# Skill: RAG Pipeline

## What This Skill Teaches
Chunking strategies, embedding model trade-offs, and retrieval patterns for production RAG systems.

## Chunking Strategies

### Sliding Window (default)
- Best for: continuous prose, FAQs, policy documents.
- chunk_size=512, overlap=64 gives good retrieval with manageable prompt size.
- Set `respect_paragraphs: true` to avoid splitting mid-sentence.

### Fixed-Size (no overlap)
- Best for: structured data like tables or line-item lists.
- Use when paragraph boundaries are not meaningful.

### Sentence-Level
- Best for: short, precise factual documents.
- Use chunk_size=128–256 with minimal overlap.

## Embedding Model Trade-offs
| Model | Dim | Speed | Quality | Best For |
|---|---|---|---|---|
| all-MiniLM-L6-v2 | 384 | Fast | Good | Default — best speed/quality |
| all-mpnet-base-v2 | 768 | Medium | Better | Higher quality, more RAM |
| bge-large-en-v1.5 | 1024 | Slow | Best | Production precision-critical |

## Retrieval Patterns

### Top-K with Score Threshold
- Retrieve top-K chunks, discard below threshold.
- Threshold 0.6: balanced recall vs. noise.
- Threshold 0.75+: high precision, may miss relevant content.

### Cross-Encoder Reranking
- Add a cross-encoder (ms-marco-MiniLM-L-6-v2) after initial retrieval.
- Improves precision at the cost of ~2x latency.
- Enable with `retrieval.rerank: true`.

### Hybrid Search (future)
- Combine dense (embedding) + sparse (BM25) retrieval for better coverage.
- Especially useful for documents with specific product codes or SKUs.
