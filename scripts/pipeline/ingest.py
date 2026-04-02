"""
End-to-end PDF ingestion pipeline.

PDF → parse → chunk → embed → store

Returns an ingestion stats dict on completion.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

from scripts.lib.chunker import get_chunker
from scripts.lib.embedder import get_embedder
from scripts.lib.pdf_parser import parse_pdf
from scripts.lib.utils import (
    get_logger,
    load_rag_config,
    ensure_dir,
    get_data_path,
)
from scripts.lib.vector_store import get_vector_store

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Public ingestion entry point
# ---------------------------------------------------------------------------

def ingest_pdf(
    pdf_path: str | Path,
    *,
    label: Optional[str] = None,
    config: Optional[dict] = None,
    replace_existing: bool = False,
) -> dict[str, Any]:
    """
    Run the full PDF ingestion pipeline.

    Steps:
      1. Parse PDF → per-page text + metadata
      2. Chunk pages → sliding-window chunks
      3. Embed chunks → float vectors
      4. Store in ChromaDB vector store

    Args:
        pdf_path:         Absolute or relative path to the PDF.
        label:            Optional human-readable label for the document.
        config:           Override config dict (defaults to config/rag.yaml).
        replace_existing: If True, delete existing chunks for the same source first.

    Returns:
        Stats dict with keys:
          source_file, pages_parsed, chunks_created, embed_time_s,
          ingest_time_s, total_chunks_in_store, label
    """
    start_time = time.time()
    pdf_path = Path(pdf_path)
    cfg = config or load_rag_config()

    logger.info("=== Ingestion started: %s ===", pdf_path.name)

    # 1. Parse ---------------------------------------------------------------
    t0 = time.time()
    pages = parse_pdf(pdf_path)
    parse_time = time.time() - t0
    logger.info("Parsed %d pages in %.2fs", len(pages), parse_time)

    # 2. Chunk ---------------------------------------------------------------
    chunker = get_chunker(cfg)
    chunks = chunker.chunk_pages(pages)
    logger.info("Created %d chunks", len(chunks))

    if not chunks:
        logger.warning("No chunks produced — document may be empty or below min_chunk_size.")
        return {
            "source_file": pdf_path.name,
            "pages_parsed": len(pages),
            "chunks_created": 0,
            "embed_time_s": 0.0,
            "ingest_time_s": time.time() - start_time,
            "total_chunks_in_store": 0,
            "label": label or pdf_path.stem,
            "status": "empty",
        }

    # 3. Embed ---------------------------------------------------------------
    embedder = get_embedder(cfg)
    texts = [c.text for c in chunks]

    t0 = time.time()
    embeddings = embedder.embed(texts)
    embed_time = time.time() - t0
    logger.info("Embedded %d chunks in %.2fs", len(embeddings), embed_time)

    # 4. Store ---------------------------------------------------------------
    vector_store = get_vector_store(cfg)

    if replace_existing:
        deleted = vector_store.delete_by_source(pdf_path.name)
        logger.info("Removed %d existing chunks for '%s'", deleted, pdf_path.name)

    chunk_dicts = [c.to_dict() for c in chunks]
    # Inject label into metadata if provided
    if label:
        for cd in chunk_dicts:
            cd["label"] = label

    vector_store.add_chunks(chunk_dicts, embeddings)
    total = vector_store.count()

    ingest_time = time.time() - start_time

    stats: dict[str, Any] = {
        "source_file": pdf_path.name,
        "pages_parsed": len(pages),
        "chunks_created": len(chunks),
        "embed_time_s": round(embed_time, 3),
        "ingest_time_s": round(ingest_time, 3),
        "total_chunks_in_store": total,
        "label": label or pdf_path.stem,
        "status": "success",
    }

    logger.info(
        "=== Ingestion complete: %d pages, %d chunks, %.2fs total ===",
        stats["pages_parsed"],
        stats["chunks_created"],
        stats["ingest_time_s"],
    )
    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Ingest a PDF into the knowledge base.")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("--label", default=None, help="Human-readable document label")
    parser.add_argument(
        "--replace", action="store_true", help="Replace existing chunks for this source"
    )
    args = parser.parse_args()

    stats = ingest_pdf(args.pdf, label=args.label, replace_existing=args.replace)
    print(json.dumps(stats, indent=2))
