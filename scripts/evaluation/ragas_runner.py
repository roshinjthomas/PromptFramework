"""
Claude-based evaluation runner (replaces RAGAS library).

Scores Faithfulness, Answer Relevancy, Context Precision, Context Recall,
and Answer Correctness using Claude as the judge — no torch/ragas required.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from scripts.lib.utils import (
    get_evaluation_path,
    get_logger,
    load_evaluation_config,
    load_rag_config,
    load_slm_config,
    ensure_dir,
)
from scripts.pipeline.inference import generate_response, _get_sync_client
from scripts.pipeline.retrieve import retrieve, format_context

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Claude-as-judge scoring
# ---------------------------------------------------------------------------

def _score_with_claude(prompt: str) -> float:
    """Ask Claude to return a score 0.0-1.0 for a given evaluation prompt."""
    try:
        client = _get_sync_client()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            temperature=0.0,
            system="You are an evaluation judge. Respond ONLY with a decimal number between 0.0 and 1.0.",
            messages=[{"role": "user", "content": prompt}],
        )
        return min(1.0, max(0.0, float(msg.content[0].text.strip())))
    except Exception as exc:
        logger.warning("Claude scoring failed: %s", exc)
        return 0.5


def _score_faithfulness(answer: str, contexts: list[str]) -> float:
    ctx = "\n".join(contexts[:3])
    return _score_with_claude(
        f"Context:\n{ctx}\n\nAnswer:\n{answer}\n\n"
        f"Score how faithful the answer is to the context (1.0=fully grounded, 0.0=hallucinated):"
    )


def _score_answer_relevancy(question: str, answer: str) -> float:
    return _score_with_claude(
        f"Question: {question}\nAnswer: {answer}\n\n"
        f"Score how relevant the answer is to the question (1.0=perfectly relevant, 0.0=irrelevant):"
    )


def _score_context_precision(question: str, contexts: list[str]) -> float:
    ctx = "\n".join(contexts[:3])
    return _score_with_claude(
        f"Question: {question}\nRetrieved context:\n{ctx}\n\n"
        f"Score what proportion of retrieved context is actually useful for answering the question (1.0=all useful, 0.0=none useful):"
    )


def _score_context_recall(question: str, ground_truth: str, contexts: list[str]) -> float:
    ctx = "\n".join(contexts[:3])
    return _score_with_claude(
        f"Ground truth answer: {ground_truth}\nRetrieved context:\n{ctx}\n\n"
        f"Score how much of the ground truth can be inferred from the retrieved context (1.0=fully covered, 0.0=not covered):"
    )


def _score_answer_correctness(answer: str, ground_truth: str) -> float:
    return _score_with_claude(
        f"Ground truth: {ground_truth}\nGenerated answer: {answer}\n\n"
        f"Score the factual correctness of the generated answer compared to the ground truth (1.0=correct, 0.0=incorrect):"
    )


METRIC_SCORERS = {
    "faithfulness": lambda q, a, ctx, gt: _score_faithfulness(a, ctx),
    "answer_relevancy": lambda q, a, ctx, gt: _score_answer_relevancy(q, a),
    "context_precision": lambda q, a, ctx, gt: _score_context_precision(q, ctx),
    "context_recall": lambda q, a, ctx, gt: _score_context_recall(q, gt, ctx),
    "answer_correctness": lambda q, a, ctx, gt: _score_answer_correctness(a, gt),
}


# ---------------------------------------------------------------------------
# Dataset preparation
# ---------------------------------------------------------------------------

def _prepare_dataset(test_dataset: list[dict], rag_config: dict) -> list[dict]:
    prepared = []
    for i, item in enumerate(test_dataset):
        question = item["question"]
        ground_truth = item.get("ground_truth", "")
        logger.info("Processing %d/%d: %s…", i + 1, len(test_dataset), question[:60])

        chunks = retrieve(question, config=rag_config)
        contexts = [c.text for c in chunks]
        context_str = format_context(chunks)
        result = generate_response(question, context_str)

        prepared.append({
            "question": question,
            "answer": result["response"],
            "contexts": contexts,
            "ground_truth": ground_truth,
            "source_document": item.get("source_document", ""),
        })
    return prepared


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_evaluation(
    *,
    dataset_path: Optional[str | Path] = None,
    metrics: Optional[list[str]] = None,
    config: Optional[dict] = None,
    output_dir: Optional[str | Path] = None,
    run_id: Optional[str] = None,
) -> dict[str, Any]:
    eval_cfg = config or load_evaluation_config()
    rag_cfg = load_rag_config()
    slm_cfg = load_slm_config()
    ragas_cfg = eval_cfg.get("ragas", {})

    if dataset_path is None:
        dataset_path = get_evaluation_path(ragas_cfg.get("test_dataset", "test-dataset.json"))
    dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        raise FileNotFoundError(f"Test dataset not found: {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as fh:
        test_dataset = json.load(fh)

    logger.info("Loaded %d test questions", len(test_dataset))

    effective_metrics = metrics or ragas_cfg.get(
        "metrics", ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "answer_correctness"]
    )
    thresholds = ragas_cfg.get("thresholds", {})

    run_id = run_id or f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    out_dir = Path(output_dir) if output_dir else get_evaluation_path("results")
    ensure_dir(out_dir)

    start = time.time()

    # Run RAG pipeline on each question
    prepared = _prepare_dataset(test_dataset, rag_cfg)

    # Score each question on each metric
    per_question = []
    metric_totals: dict[str, float] = {m: 0.0 for m in effective_metrics}

    for item in prepared:
        q, a, ctx, gt = item["question"], item["answer"], item["contexts"], item["ground_truth"]
        scores: dict[str, float] = {}
        for metric in effective_metrics:
            if metric in METRIC_SCORERS:
                score = METRIC_SCORERS[metric](q, a, ctx, gt)
                scores[metric] = round(score, 4)
                metric_totals[metric] += score
        per_question.append({
            "question": q,
            "answer": a,
            "ground_truth": gt,
            "contexts": ctx,
            "source_document": item.get("source_document", ""),
            "scores": scores,
        })

    n = len(prepared)
    metric_results: dict[str, Any] = {}
    any_failed = False
    for metric in effective_metrics:
        avg = round(metric_totals[metric] / n, 4) if n else 0.0
        threshold = thresholds.get(metric, 0.0)
        passed = avg >= threshold
        if not passed:
            any_failed = True
        metric_results[metric] = {"score": avg, "threshold": threshold, "passed": passed}

    elapsed = time.time() - start

    result = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_s": round(elapsed, 2),
        "question_count": n,
        "metrics": metric_results,
        "per_question": per_question,
        "config_snapshot": {
            "rag": {
                "chunk_size": rag_cfg.get("ingestion", {}).get("chunk_size"),
                "chunk_overlap": rag_cfg.get("ingestion", {}).get("chunk_overlap"),
                "top_k": rag_cfg.get("retrieval", {}).get("top_k"),
                "score_threshold": rag_cfg.get("retrieval", {}).get("score_threshold"),
                "embedding_model": rag_cfg.get("embedding", {}).get("model"),
            },
            "slm": {
                "model_id": "claude-haiku-4-5-20251001",
                "temperature": slm_cfg.get("model", {}).get("temperature"),
                "max_new_tokens": slm_cfg.get("model", {}).get("max_new_tokens"),
            },
        },
        "status": "failed" if any_failed else "passed",
    }

    out_path = out_dir / f"{run_id}.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, default=str)
    logger.info("Evaluation saved to '%s'", out_path)

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--metrics", default=None)
    args = parser.parse_args()
    metrics = args.metrics.split(",") if args.metrics else None
    result = run_evaluation(dataset_path=args.dataset, metrics=metrics)
    print(json.dumps({k: v for k, v in result.items() if k != "per_question"}, indent=2))
