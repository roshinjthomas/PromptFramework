# Rule: RAG Standards

## Chunk Size Limits
- `chunk_size` MUST be between **128 and 1024 tokens**.
- Values outside this range require documented justification in a comment in `config/rag.yaml`.
- Default: 512 tokens.

## Overlap Rules
- `chunk_overlap` MUST be less than `chunk_size`.
- Recommended range: 10–20% of chunk_size (default: 64 tokens with chunk_size=512).
- Zero overlap is permitted for structured data (tables, FAQs) only.

## Top-K Bounds
- `top_k` MUST be between **1 and 20**.
- Values above 10 significantly increase prompt length and inference latency.
- Default: 5.

## Score Threshold
- `score_threshold` MUST be **≥ 0.5**.
- Values below 0.5 include too many irrelevant chunks and increase hallucination risk.
- Default: 0.6.

## Paragraph Respect
- `respect_paragraphs: true` is the default and SHOULD NOT be disabled without reason.
- Splitting mid-paragraph degrades retrieval quality.

## Reranking
- Cross-encoder reranking is optional but SHOULD be enabled for production deployments handling complex multi-sentence queries.
- Set `retrieval.rerank: true` in `config/rag.yaml`.

## Config Change Policy
- Any change to `config/rag.yaml` MUST trigger a RAGAS evaluation run before deployment.
- This is enforced by the `on-config-change` hook.
