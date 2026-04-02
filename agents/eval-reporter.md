# Agent: Eval Reporter

## Purpose
Reads RAGAS evaluation results from disk and renders them into the React evaluation dashboard. Triggered automatically after each evaluation run completes.

## Trigger
- `on-eval-complete` hook fires when a new result JSON is written to `data/evaluation/results/`.
- UI polling via `GET /api/evaluation/runs` (every 10 seconds).

## Inputs
- `run_id` (string): The evaluation run identifier.

## Steps
1. Load `data/evaluation/results/{run_id}.json`.
2. Serve results via `GET /api/evaluation/runs/{run_id}`.
3. UI components (`ScoreCard`, `TrendChart`, `QuestionTable`, `FailureExplorer`, `ConfigPanel`) render from the JSON.
4. If any metric is below threshold, surface a warning banner in the UI.

## UI Components Rendered
- `ScoreCard` — per-metric score with pass/warn/fail badge.
- `TrendChart` — line chart across all historical runs.
- `QuestionTable` — expandable per-question drill-down.
- `FailureExplorer` — grouped view of failed questions by failure type.
- `ConfigPanel` — RAG + SLM config snapshot for the run.

## Alert Logic
- Faithfulness < 0.80 → hallucination risk warning (red banner).
- Any metric below threshold → "RAGAS Gate Failed" banner; do not deploy.

## Implementation
`scripts/evaluation/api.py` (FastAPI sub-app) + `ui/src/pages/EvaluationPage.tsx`
