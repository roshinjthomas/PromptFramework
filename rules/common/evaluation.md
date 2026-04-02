# Rule: Evaluation Requirements

## RAGAS Gate
**No retrieval config or SLM config change ships without a passing RAGAS evaluation.**

This is enforced by:
1. The `on-config-change` hook automatically triggering evaluation when `config/rag.yaml` or `config/slm.yaml` is saved.
2. Setting `fail_on_threshold_breach: true` in `config/evaluation.yaml`.

## Thresholds (Mandatory Minimums)
| Metric | Minimum Score | Consequence of Breach |
|---|---|---|
| faithfulness | 0.80 | Hallucination risk — block deployment |
| answer_relevancy | 0.75 | SLM misunderstanding queries |
| context_precision | 0.70 | Retrieval quality degraded |
| context_recall | 0.70 | Missing knowledge in retrieval |
| answer_correctness | 0.75 | Incorrect answers being served |

## Test Dataset Requirements
- The test dataset MUST have at least **20 questions** before production deployment.
- Questions MUST cover all ingested documents (at least 2 questions per document).
- Ground truth answers MUST be manually verified by a subject matter expert.
- Dataset MUST be updated whenever new documents are added to the KB.

## Evaluation Frequency
- Run evaluation: after every document ingestion (spot-check, 5 questions).
- Run evaluation: after any config change to `rag.yaml` or `slm.yaml`.
- Run evaluation: before each production deployment.
- Run evaluation: weekly in production for drift monitoring.

## Results Storage
- All evaluation results MUST be saved to `data/evaluation/results/`.
- Results MUST NOT be deleted — they form the audit trail.
- The evaluation dashboard (`/eval-ui`) MUST show the trend across all runs.
