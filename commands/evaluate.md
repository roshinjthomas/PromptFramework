# /evaluate

Run RAGAS evaluation on the test dataset.

## Usage
```
/evaluate
/evaluate --dataset data/evaluation/test-dataset.json
/evaluate --metrics faithfulness,answer_relevancy
```

## Arguments
| Argument | Type | Required | Description |
|---|---|---|---|
| `--dataset` | string | no | Path to test dataset JSON (default: `data/evaluation/test-dataset.json`) |
| `--metrics` | string | no | Comma-separated metric names (default: all 5) |
| `--run-id` | string | no | Custom run identifier for the results file |

## RAGAS Metrics
| Metric | Threshold | Measures |
|---|---|---|
| `faithfulness` | 0.80 | Answer grounded in context — no hallucination |
| `answer_relevancy` | 0.75 | Answer addresses the question |
| `context_precision` | 0.70 | Retrieved chunks are relevant |
| `context_recall` | 0.70 | All needed chunks were retrieved |
| `answer_correctness` | 0.75 | Answer matches ground truth |

## What Happens
1. Loads test dataset.
2. For each question: retrieves chunks, generates answer with SLM.
3. Passes question, answer, contexts, and ground truth to RAGAS.
4. Computes scores and compares to thresholds from `config/evaluation.yaml`.
5. Saves results to `data/evaluation/results/{run_id}.json`.
6. Prints pass/fail summary.

## Example Output
```
RAGAS Evaluation — run-20260401-120000-abc123
  faithfulness:       0.84  PASS (threshold 0.80)
  answer_relevancy:   0.91  PASS (threshold 0.75)
  context_precision:  0.72  WARN (threshold 0.70, close to boundary)
  context_recall:     0.78  PASS (threshold 0.70)
  answer_correctness: 0.83  PASS (threshold 0.75)

Overall: PASSED (5/5 questions · 12.4s)
```

## RAGAS Gate
If `fail_on_threshold_breach: true` and any metric fails, evaluation status is `"failed"`. Do not deploy until resolved.

## Agent
`agents/ragas-evaluator.md`

## Implementation
`scripts/evaluation/ragas_runner.py:run_evaluation()`
