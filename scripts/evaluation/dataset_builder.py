"""
Evaluation dataset builder.

Generates Q&A pairs from the knowledge base for use in RAGAS evaluation.
Can be used to bootstrap a test-dataset.json when no labeled data exists.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Optional

from scripts.lib.utils import (
    get_evaluation_path,
    get_logger,
    load_rag_config,
    load_slm_config,
    ensure_dir,
)
from scripts.lib.vector_store import get_vector_store
from scripts.pipeline.inference import generate_response

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Question generation prompt
# ---------------------------------------------------------------------------

QUESTION_GEN_PROMPT_TEMPLATE = """You are generating evaluation questions for a customer service chatbot.
Based on the following document excerpt, generate {n_questions} distinct customer service questions
that can be answered using ONLY this text. Return the questions as a numbered list.

Document excerpt:
{chunk_text}

Generate exactly {n_questions} questions:"""


# ---------------------------------------------------------------------------
# Dataset builder
# ---------------------------------------------------------------------------

def _generate_questions_from_chunk(
    chunk_text: str,
    source_file: str,
    n_questions: int = 2,
    slm_config: Optional[dict] = None,
) -> list[str]:
    """Use the SLM to generate questions from a chunk."""
    prompt = QUESTION_GEN_PROMPT_TEMPLATE.format(
        chunk_text=chunk_text[:1000],
        n_questions=n_questions,
    )
    try:
        result = generate_response(prompt, "", config=slm_config)
        raw = result["response"]
        # Parse numbered list
        lines = [
            re.sub(r"^\d+[\.\)]\s*", "", line).strip()
            for line in raw.splitlines()
            if re.match(r"^\d+", line.strip())
        ]
        return [q for q in lines if q][:n_questions]
    except Exception as exc:
        logger.warning("Question generation failed for chunk from '%s': %s", source_file, exc)
        return []


def _generate_answer_for_question(
    question: str,
    chunk_text: str,
    slm_config: Optional[dict] = None,
) -> str:
    """Use the SLM to generate a ground-truth answer from the chunk."""
    try:
        result = generate_response(question, chunk_text, config=slm_config)
        return result["response"].strip()
    except Exception as exc:
        logger.warning("Answer generation failed: %s", exc)
        return ""


def build_dataset(
    *,
    questions_per_chunk: int = 2,
    max_chunks: int = 50,
    output_path: Optional[str | Path] = None,
    rag_config: Optional[dict] = None,
    slm_config: Optional[dict] = None,
) -> list[dict[str, Any]]:
    """
    Build an evaluation Q&A dataset from the knowledge base.

    Samples chunks from ChromaDB, generates questions using the SLM,
    then generates reference answers. Results are saved to test-dataset.json.

    Args:
        questions_per_chunk: Number of Q&A pairs to generate per chunk.
        max_chunks:          Maximum number of chunks to sample.
        output_path:         Where to save the JSON file.
        rag_config:          RAG config override.
        slm_config:          SLM config override.

    Returns:
        List of Q&A pair dicts.
    """
    rag_cfg = rag_config or load_rag_config()
    slm_cfg = slm_config or load_slm_config()

    # Retrieve sample chunks from the vector store
    vector_store = get_vector_store(rag_cfg)
    all_data = vector_store._get_collection().get(
        include=["documents", "metadatas"],
        limit=max_chunks,
    )
    documents = all_data.get("documents") or []
    metadatas = all_data.get("metadatas") or []

    if not documents:
        logger.warning("Knowledge base is empty — cannot build dataset.")
        return []

    logger.info("Building dataset from %d chunks…", len(documents))

    qa_pairs: list[dict[str, Any]] = []

    for doc_text, meta in zip(documents, metadatas):
        source_file = meta.get("source_file", "unknown")
        page_number = meta.get("page_number", 0)

        questions = _generate_questions_from_chunk(
            doc_text, source_file, n_questions=questions_per_chunk, slm_config=slm_cfg
        )

        for question in questions:
            if not question:
                continue
            ground_truth = _generate_answer_for_question(question, doc_text, slm_config=slm_cfg)
            if ground_truth:
                qa_pairs.append(
                    {
                        "question": question,
                        "ground_truth": ground_truth,
                        "source_document": source_file,
                        "source_page": page_number,
                    }
                )

        time.sleep(0.1)  # Avoid overwhelming the model

    # Save output
    out_path = Path(output_path) if output_path else get_evaluation_path("test-dataset.json")
    ensure_dir(out_path.parent)

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(qa_pairs, fh, indent=2, ensure_ascii=False)

    logger.info("Saved %d Q&A pairs to '%s'", len(qa_pairs), out_path)
    return qa_pairs


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build RAGAS evaluation dataset from KB.")
    parser.add_argument("--questions-per-chunk", type=int, default=2)
    parser.add_argument("--max-chunks", type=int, default=50)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    pairs = build_dataset(
        questions_per_chunk=args.questions_per_chunk,
        max_chunks=args.max_chunks,
        output_path=args.output,
    )
    print(f"Built {len(pairs)} Q&A pairs.")
