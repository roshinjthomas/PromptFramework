# Sample RAGAS Evaluation Run Walkthrough

This example demonstrates a complete RAGAS evaluation run — from triggering the run to interpreting the results in the dashboard.

---

## Step 1 — Trigger the Evaluation

Via CLI:
```bash
/evaluate
```

Or via the UI:
1. Open http://localhost:3000
2. Click the **Evaluation** tab.
3. Click **Run Evaluation**.

Or directly:
```bash
python -m scripts.evaluation.ragas_runner \
  --dataset data/evaluation/test-dataset.json \
  --metrics faithfulness,answer_relevancy,context_precision,context_recall,answer_correctness
```

---

## Step 2 — Pipeline Execution

For each of the 5 test questions, the pipeline runs:
1. Retriever fetches top-5 chunks.
2. Phi-3 Mini generates an answer from the chunks.
3. RAGAS computes metrics comparing: question, answer, contexts, ground_truth.

Progress output:
```
Processing question 1/5: What is the return window for electronics?…
Processing question 2/5: Do you offer free shipping?…
Processing question 3/5: How long does standard shipping take?…
Processing question 4/5: Can I return a product without a receipt?…
Processing question 5/5: What payment methods do you accept?…
```

---

## Step 3 — Results

### Summary

```
RAGAS Evaluation — run-20260401-120000-abc123
  faithfulness:       0.84  PASS  (threshold 0.80)
  answer_relevancy:   0.91  PASS  (threshold 0.75)
  context_precision:  0.72  WARN  (threshold 0.70 — close to boundary)
  context_recall:     0.78  PASS  (threshold 0.70)
  answer_correctness: 0.83  PASS  (threshold 0.75)

Overall: PASSED (5/5 questions · 14.2s)
Results: data/evaluation/results/run-20260401-120000-abc123.json
```

### Per-Question Breakdown

| # | Question | Faith. | Relev. | Prec. | Recall | Correct. |
|---|---|---|---|---|---|---|
| 1 | Return window for electronics? | 0.90 | 0.95 | 0.80 | 0.85 | 0.88 |
| 2 | Free shipping? | 0.85 | 0.92 | 0.75 | 0.80 | 0.90 |
| 3 | Shipping time? | 0.88 | 0.90 | 0.72 | 0.78 | 0.85 |
| 4 | Return without receipt? | 0.78 | 0.89 | 0.65 | 0.70 | 0.78 |
| 5 | Payment methods? | 0.79 | 0.87 | 0.70 | 0.75 | 0.74 |

### Observations
- Question 4 ("Return without receipt?") shows lower Context Precision (0.65) — the retrieved chunks may include some less relevant paragraphs. Consider tuning `score_threshold` from 0.60 → 0.65.
- Question 5 ("Payment methods?") has Answer Correctness at 0.74, just below threshold — ensure the payment FAQ document is fully ingested.

---

## Step 4 — Dashboard View

Open the Evaluation tab in the web UI:
- **ScoreCard** shows all 5 metrics with pass/warn badges.
- **Trend Chart** shows this run vs. the previous one.
- **Failure Explorer** highlights Question 4 under "Poor Retrieval".
- **Question Table** provides expandable rows with full context and scores.
- **Config Panel** shows the RAG + SLM config active for this run.

---

## Step 5 — Action Items

Based on the results:
1. Monitor context_precision — it's above threshold but close to the boundary (0.72 vs 0.70).
2. Review Question 4 — add more specific return-without-receipt chunks to the KB.
3. Verify payment FAQ ingestion — re-run `/kb-list` and `/kb-refresh` if needed.
4. Consider increasing `top_k` from 5 to 7 to improve recall.
