# Agent: RAGAS Evaluator

## Purpose
Runs RAGAS evaluation metrics on a labeled test dataset to measure chatbot quality across five dimensions: Faithfulness, Answer Relevancy, Context Precision, Context Recall, and Answer Correctness.

## Trigger
- Invoked by `/evaluate` command.
- Automatically triggered by `on-config-change` hook when `config/rag.yaml` or `config/slm.yaml` is saved.
- Triggered by `on-ingest` hook for spot-checks after new documents are added.

## Inputs
- `dataset_path` (string, optional): Path to test-dataset.json (default: `data/evaluation/test-dataset.json`).
- `metrics` (list[str], optional): Subset of metrics to run.
- `run_id` (string, optional): Custom run identifier.

## Evaluation Flow
1. Load test dataset (list of question/ground_truth/source_document triples).
2. For each question: run Retriever → SLM Inference to generate answer and contexts.
3. Build HuggingFace Dataset with: question, answer, contexts, ground_truth.
4. Call `ragas.evaluate()` with selected metrics.
5. Apply thresholds from `config/evaluation.yaml`.
6. Save results JSON to `data/evaluation/results/{run_id}.json`.

## RAGAS Metrics
| Metric | Measures |
|---|---|
| Faithfulness | Answer grounded in context (0=hallucination, 1=faithful) |
| Answer Relevancy | Answer addresses the question |
| Context Precision | Retrieved chunks are relevant |
| Context Recall | All needed chunks were retrieved |
| Answer Correctness | Answer matches ground truth |

## Thresholds (from `config/evaluation.yaml`)
- faithfulness ≥ 0.80
- answer_relevancy ≥ 0.75
- context_precision ≥ 0.70
- context_recall ≥ 0.70
- answer_correctness ≥ 0.75

## Outputs
Saves `{run_id}.json` to `data/evaluation/results/`. Returns summary dict with per-metric scores and pass/fail status.

## RAGAS Gate
If `fail_on_threshold_breach: true` and any metric is below threshold, logs a warning and the result status is set to `"failed"`. Block deployment until resolved.

## Implementation
`scripts/evaluation/ragas_runner.py:run_evaluation()`
