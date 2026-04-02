# /ingest

Add a PDF document to the knowledge base.

## Usage
```
/ingest path/to/product-manual.pdf
/ingest path/to/returns-policy.pdf --label "Returns Policy"
/ingest path/to/shipping-faq.pdf --replace
```

## Arguments
| Argument | Type | Required | Description |
|---|---|---|---|
| `path` | string | yes | Path to the PDF file (absolute or relative to project root) |
| `--label` | string | no | Human-readable document name shown in KB list and citations |
| `--replace` | flag | no | Delete existing chunks for this document before re-ingesting |

## What Happens
1. Validates the PDF (exists, not password-protected, ≤ 50 MB).
2. Parses text and metadata from all pages.
3. Splits into 512-token chunks with 64-token overlap.
4. Embeds chunks using `all-MiniLM-L6-v2`.
5. Stores in ChromaDB at `data/vector-store/`.
6. Reports: pages parsed, chunks created, total index size.

## Example Output
```
Ingestion complete!
  Source:  returns-policy.pdf
  Pages:   12
  Chunks:  28
  Time:    3.2s
  Total chunks in store: 215
```

## Errors
- Password-protected PDF: rejected with clear message.
- File > 50 MB: rejected; split first.
- Empty/unreadable PDF: reports "empty" status with warning.

## Agent
`agents/document-ingestion.md`

## Implementation
`scripts/pipeline/ingest.py:ingest_pdf()`
