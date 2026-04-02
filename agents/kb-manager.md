# Agent: KB Manager

## Purpose
Manages the knowledge base: adds new documents, removes outdated ones, refreshes updated versions, and lists current contents.

## Trigger
Invoked by `/kb-list`, `/kb-remove`, `/kb-refresh` commands, or the `POST /api/kb/ingest` API endpoint.

## Operations

### List (`/kb-list`)
- Call `VectorStore.list_sources()`.
- Return: source_file, chunk_count for each document.

### Add (`/ingest`)
- Validate file (PDF, ≤ 50 MB).
- Run Document Ingestion agent pipeline.
- Report chunk count and index size on completion.

### Remove (`/kb-remove <filename>`)
- Call `VectorStore.delete_by_source(filename)`.
- Optionally remove the source PDF from `data/documents/`.
- Report how many chunks were deleted.

### Refresh (`/kb-refresh <new-file> --replace <old-file>`)
- Delete old document chunks (`delete_by_source`).
- Ingest new document with `replace_existing=True`.
- Report old chunk count removed + new chunk count added.

## Rules
- Never ingest a password-protected PDF — reject with clear error.
- Never ingest a file >50 MB — prompt user to split it.
- After any add/remove/refresh, log the new total chunk count.

## Implementation
- `backend/routers/knowledge_base.py`
- `scripts/pipeline/ingest.py`
- `scripts/lib/vector_store.py`
