"""
RAG retrieval pipeline.

Query → embed → top-K chunks from ChromaDB with score filtering.
"""

from __future__ import annotations

from typing import Any, Optional

from scripts.lib.embedder import get_embedder
from scripts.lib.utils import get_logger, load_rag_config
from scripts.lib.vector_store import RetrievedChunk, get_vector_store

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Retrieval function
# ---------------------------------------------------------------------------

def retrieve(
    query: str,
    *,
    top_k: Optional[int] = None,
    score_threshold: Optional[float] = None,
    source_filter: Optional[str] = None,
    config: Optional[dict] = None,
) -> list[RetrievedChunk]:
    """
    Retrieve the top-K most relevant chunks for a query.

    Args:
        query:           The user's natural language question.
        top_k:           Number of chunks to retrieve (overrides config).
        score_threshold: Minimum similarity score to include (overrides config).
        source_filter:   Optional source_file name to restrict retrieval.
        config:          Override config dict (defaults to config/rag.yaml).

    Returns:
        List of RetrievedChunk objects sorted by descending similarity score.
    """
    cfg = config or load_rag_config()
    retrieval_cfg = cfg.get("retrieval", {})

    effective_top_k = top_k if top_k is not None else retrieval_cfg.get("top_k", 5)
    effective_threshold = (
        score_threshold if score_threshold is not None
        else retrieval_cfg.get("score_threshold", 0.6)
    )

    if not query.strip():
        logger.warning("Empty query — returning no results.")
        return []

    # Embed the query
    embedder = get_embedder(cfg)
    query_vector = embedder.embed_query(query)

    # Build optional metadata filter
    where: Optional[dict] = None
    if source_filter:
        where = {"source_file": source_filter}

    # Query the vector store
    vector_store = get_vector_store(cfg)
    chunks = vector_store.query(
        query_embedding=query_vector,
        top_k=effective_top_k,
        score_threshold=effective_threshold,
        where=where,
    )

    logger.info(
        "Retrieved %d chunks for query '%s…' (top_k=%d, threshold=%.2f)",
        len(chunks),
        query[:60],
        effective_top_k,
        effective_threshold,
    )

    # Optional cross-encoder reranking
    if retrieval_cfg.get("rerank", False) and chunks:
        chunks = _rerank(query, chunks)

    return chunks


# ---------------------------------------------------------------------------
# Optional reranking (cross-encoder)
# ---------------------------------------------------------------------------

def _rerank(query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """
    Rerank chunks using a cross-encoder model.
    Requires: pip install sentence-transformers (cross-encoder support).
    """
    try:
        from sentence_transformers import CrossEncoder
    except ImportError:
        logger.warning("CrossEncoder not available — skipping rerank.")
        return chunks

    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    pairs = [(query, c.text) for c in chunks]
    scores = model.predict(pairs)

    for chunk, score in zip(chunks, scores):
        chunk.score = float(score)

    chunks.sort(key=lambda c: c.score, reverse=True)
    logger.info("Reranked %d chunks with cross-encoder.", len(chunks))
    return chunks


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_context(chunks: list[RetrievedChunk], *, max_chunks: Optional[int] = None) -> str:
    """
    Format retrieved chunks into a context block for the SLM prompt.

    Each chunk is labeled with its source and page number.
    """
    if max_chunks:
        chunks = chunks[:max_chunks]

    parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        header = f"[{i}] {chunk.source_file}, p.{chunk.page_number}"
        if chunk.section_header:
            header += f" — {chunk.section_header}"
        parts.append(f"{header}\n{chunk.text}")

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Retrieve relevant chunks for a query.")
    parser.add_argument("query", help="The search query")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--source", default=None)
    args = parser.parse_args()

    results = retrieve(
        args.query,
        top_k=args.top_k,
        score_threshold=args.threshold,
        source_filter=args.source,
    )
    output = [c.to_dict() for c in results]
    print(json.dumps(output, indent=2))
