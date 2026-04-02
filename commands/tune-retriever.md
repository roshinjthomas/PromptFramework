# /tune-retriever

Adjust retrieval configuration and automatically re-run RAGAS evaluation to measure impact.

## Usage
```
/tune-retriever --chunk-size 256 --top-k 8
/tune-retriever --overlap 128
/tune-retriever --threshold 0.7
/tune-retriever --rerank true
```

## Arguments
| Argument | Type | Required | Description |
|---|---|---|---|
| `--chunk-size` | int | no | New chunk size in tokens (must be 128–1024) |
| `--overlap` | int | no | New chunk overlap in tokens |
| `--top-k` | int | no | New top-K retrieval count (1–20) |
| `--threshold` | float | no | New similarity score threshold (≥ 0.5) |
| `--rerank` | bool | no | Enable/disable cross-encoder reranking |

## What Happens
1. Validates new values against rules (chunk_size: 128–1024; threshold: ≥ 0.5).
2. Updates `config/rag.yaml` with new values.
3. **If chunk-size or overlap changed**: re-runs full ingestion pipeline on all documents (required because chunk boundaries change).
4. Automatically triggers a RAGAS evaluation run to measure the impact.
5. Shows before/after metric comparison.

## Example Output
```
Tuning retriever: chunk_size 512→256, top_k 5→8

Re-ingesting 3 documents...
  product-manual.pdf: 142→267 chunks
  returns-policy.pdf: 28→54 chunks
  shipping-faq.pdf: 45→88 chunks

Running RAGAS evaluation...
  Before: faithfulness=0.84, context_precision=0.72
  After:  faithfulness=0.87, context_precision=0.79 (+0.07)

Result: IMPROVEMENT — new config is active.
```

## Safety Gate
If the RAGAS evaluation after tuning shows any metric below threshold, the new config is reverted and the old values are restored.

## Agent
`agents/ragas-evaluator.md`, `agents/document-ingestion.md`
