# Agent: Document Ingestion

## Purpose
Orchestrates the full PDF-to-vector-store pipeline. Accepts a PDF path, parses it, chunks the text, generates embeddings, and stores the chunks in ChromaDB.

## Trigger
Invoked by the `/ingest` command or the `on-ingest` hook after a file upload.

## Inputs
- `pdf_path` (string, required): Absolute path to the PDF file.
- `label` (string, optional): Human-readable document name.
- `replace_existing` (bool, default false): If true, delete existing chunks for this source before re-ingesting.

## Steps
1. **Validate** — Check file exists, is a PDF, does not exceed 50 MB limit.
2. **Parse** — Call `scripts/lib/pdf_parser.py:parse_pdf()`. Use PyMuPDF primary; pdfplumber fallback; OCR for scanned pages.
3. **Chunk** — Call `scripts/lib/chunker.py:get_chunker().chunk_pages()` with parameters from `config/rag.yaml` (chunk_size=512, overlap=64).
4. **Embed** — Call `scripts/lib/embedder.py:get_embedder().embed()` in batches of 32.
5. **Store** — Call `scripts/lib/vector_store.py:VectorStore.add_chunks()` with embeddings.
6. **Report** — Return stats dict: pages_parsed, chunks_created, embed_time_s, total_chunks_in_store.

## Outputs
```json
{
  "source_file": "returns-policy.pdf",
  "pages_parsed": 12,
  "chunks_created": 28,
  "embed_time_s": 1.4,
  "ingest_time_s": 3.2,
  "total_chunks_in_store": 215,
  "status": "success"
}
```

## Error Handling
- Password-protected PDF: raise `ValueError` with clear message, do not partially ingest.
- File > 50 MB: raise `ValueError`; instruct user to split the document.
- Empty document (0 chunks after chunking): return status `"empty"` with a warning.

## Config
Reads from `config/rag.yaml` (chunk_size, overlap, min_chunk_size, embedding model).

## Implementation
`scripts/pipeline/ingest.py:ingest_pdf()`
