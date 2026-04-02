# Agent: Retriever

## Purpose
Embeds a user query and retrieves the top-K most relevant chunks from ChromaDB, filtered by a minimum similarity score threshold.

## Trigger
Called as the first step of every chat request, before SLM inference.

## Inputs
- `query` (string, required): The user's natural language question.
- `top_k` (int, optional): Override the configured top-K (default: 5).
- `score_threshold` (float, optional): Override minimum similarity score (default: 0.6).
- `source_filter` (string, optional): Restrict retrieval to a specific source document.

## Steps
1. **Embed query** — Call `embedder.embed_query(query)` with the same model used during ingestion (`all-MiniLM-L6-v2`).
2. **Query ChromaDB** — Call `VectorStore.query(query_vector, top_k, score_threshold)`.
3. **Filter** — Discard chunks below `score_threshold`.
4. **Rerank** (optional) — If `config/rag.yaml: retrieval.rerank: true`, apply cross-encoder reranking.
5. **Return** — List of `RetrievedChunk` objects sorted by descending similarity score.

## Outputs
List of chunk objects:
```json
[
  {
    "text": "Returns must be made within 30 days with original receipt...",
    "score": 0.87,
    "source_file": "returns-policy.pdf",
    "page_number": 4,
    "section_header": "Return Conditions",
    "chunk_index": 12
  }
]
```

## Fallback
If no chunks pass the threshold, returns an empty list. The downstream post-processor will trigger the fallback response.

## Implementation
`scripts/pipeline/retrieve.py:retrieve()`
