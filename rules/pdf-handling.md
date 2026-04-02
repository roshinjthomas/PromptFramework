# Rule: PDF Handling

## File Size Limit
- Maximum **50 MB** per PDF document.
- Documents exceeding this limit MUST be split before ingestion.
- The ingestion pipeline MUST reject oversized files with a clear error message.

## Password Protection
- Password-protected PDFs MUST be rejected at the parse step.
- Do not attempt to guess or bypass passwords.
- Error message: "This PDF is password-protected and cannot be ingested. Please provide an unlocked version."

## Supported PDF Types
| Type | Handler | Notes |
|---|---|---|
| Text-based PDF | PyMuPDF (primary) | Fast, preserves structure |
| Scanned PDF (image) | pdfplumber + Tesseract OCR | Slower; requires Tesseract installed |
| PDF with tables | pdfplumber table extractor | Tables converted to text representation |
| Password-protected | Rejected | Clear error returned |

## OCR Requirements
- OCR is only triggered when both PyMuPDF and pdfplumber yield < 50 characters per page on average.
- Tesseract MUST be installed (`pip install pytesseract` + system Tesseract binary).
- OCR resolution: 200 DPI minimum for acceptable accuracy.
- OCR language: `eng` by default; configurable via environment variable `TESSERACT_LANG`.

## Metadata Extraction
Every parsed page MUST include:
- `source_file` — the PDF filename.
- `page_number` — 1-based page index.
- `section_header` — detected from the first non-empty line of the page.
- `page_count` — total pages in the document.

## Cleaning Requirements
Before chunking, the parser MUST:
- Remove excessive blank lines (3+ consecutive → 1 blank line).
- Remove lines that are purely page numbers (e.g., "Page 3 of 12" or standalone "3").
- Strip trailing whitespace from each line.
- Preserve paragraph structure for the chunker.

## Logging
Log the following per document:
- File name and size.
- Parser used (PyMuPDF, pdfplumber, or OCR).
- Pages parsed and total character count.
- Whether any PII was redacted.
