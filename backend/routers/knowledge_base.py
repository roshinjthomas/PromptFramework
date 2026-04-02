"""
Knowledge base router.

GET    /api/kb              - List all ingested documents
POST   /api/kb/ingest       - Upload and ingest a PDF
DELETE /api/kb/:doc_id      - Remove a document from the KB
POST   /api/kb/refresh      - Re-ingest an updated document
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from scripts.lib.utils import get_documents_path, get_logger, ensure_dir, load_rag_config
from scripts.lib.vector_store import get_vector_store
from scripts.pipeline.ingest import ingest_pdf

logger = get_logger(__name__)

router = APIRouter(prefix="/api/kb", tags=["knowledge_base"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class KBDocument(BaseModel):
    source_file: str
    chunk_count: int


class IngestResponse(BaseModel):
    source_file: str
    pages_parsed: int
    chunks_created: int
    embed_time_s: float
    ingest_time_s: float
    total_chunks_in_store: int
    label: str
    status: str


class DeleteResponse(BaseModel):
    source_file: str
    chunks_deleted: int
    message: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("")
async def list_documents() -> list[KBDocument]:
    """List all documents currently in the knowledge base."""
    try:
        cfg = load_rag_config()
        vs = get_vector_store(cfg)
        sources = vs.list_sources()
        return [KBDocument(**s) for s in sources]
    except Exception as exc:
        logger.error("Failed to list KB documents: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(..., description="PDF file to ingest"),
    label: str = Form(default="", description="Optional human-readable label"),
    replace: bool = Form(default=False, description="Replace existing chunks for this document"),
) -> IngestResponse:
    """Upload and ingest a PDF into the knowledge base."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Save to documents directory
    docs_dir = get_documents_path()
    ensure_dir(docs_dir)
    dest_path = docs_dir / file.filename

    try:
        with open(dest_path, "wb") as fh:
            content = await file.read()
            fh.write(content)

        stats = ingest_pdf(
            dest_path,
            label=label or None,
            replace_existing=replace,
        )
        return IngestResponse(**stats)

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Ingestion failed for '%s': %s", file.filename, exc)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")


@router.delete("/{doc_id}", response_model=DeleteResponse)
async def remove_document(doc_id: str) -> DeleteResponse:
    """
    Remove a document and all its chunks from the knowledge base.

    :param doc_id: The source filename (e.g., returns-policy.pdf).
    """
    try:
        cfg = load_rag_config()
        vs = get_vector_store(cfg)
        deleted = vs.delete_by_source(doc_id)

        if deleted == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{doc_id}' not found in knowledge base.",
            )

        # Also remove the file from documents directory if present
        docs_path = get_documents_path() / doc_id
        if docs_path.exists():
            docs_path.unlink()

        return DeleteResponse(
            source_file=doc_id,
            chunks_deleted=deleted,
            message=f"Successfully removed '{doc_id}' and {deleted} chunks.",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to remove document '%s': %s", doc_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/refresh", response_model=IngestResponse)
async def refresh_document(
    file: UploadFile = File(..., description="Updated PDF file"),
    replace: str = Form(..., description="Filename of the document to replace"),
    label: str = Form(default="", description="Optional label"),
) -> IngestResponse:
    """Re-ingest an updated version of an existing document."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    docs_dir = get_documents_path()
    ensure_dir(docs_dir)
    dest_path = docs_dir / file.filename

    try:
        # Delete old document chunks
        cfg = load_rag_config()
        vs = get_vector_store(cfg)
        vs.delete_by_source(replace)

        # Remove old file
        old_path = docs_dir / replace
        if old_path.exists():
            old_path.unlink()

        # Save new file
        with open(dest_path, "wb") as fh:
            content = await file.read()
            fh.write(content)

        stats = ingest_pdf(dest_path, label=label or None)
        return IngestResponse(**stats)

    except Exception as exc:
        logger.error("Refresh failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
