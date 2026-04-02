# Skill: PDF Parsing

## PyMuPDF vs pdfplumber

### PyMuPDF (fitz)
- **Speed**: Very fast (C-based).
- **Best for**: Text-based PDFs with standard formatting.
- **Limitations**: Poor table extraction; limited OCR support.
- **Usage**: Primary parser in this framework.

### pdfplumber
- **Speed**: Slower (Python-based).
- **Best for**: PDFs with tables; complex layouts.
- **Strengths**: `page.extract_table()` returns structured list-of-lists.
- **Usage**: Fallback when PyMuPDF yields sparse text; always used for table extraction.

## Detecting Scanned PDFs
A PDF is likely scanned (image-only) if the average character count per page is < 50 after PyMuPDF extraction. Trigger OCR in this case.

## Tesseract OCR Setup
```bash
# Windows
choco install tesseract

# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Python binding
pip install pytesseract
```

## Table Extraction
pdfplumber tables come back as `list[list[str | None]]`. Convert to text:
```python
rows = [[cell or "" for cell in row] for row in table]
text = "\n".join("\t".join(row) for row in rows)
```

## Metadata Preservation
Always extract and attach to each chunk:
- `source_file` — filename (not full path, for privacy)
- `page_number` — 1-based
- `section_header` — first non-empty line of the page
- `page_count` — total pages

## Common Issues
- **Ligatures**: fi, fl, ffi ligatures may appear as single characters. PyMuPDF handles these better than pdfplumber.
- **Rotated pages**: pdfplumber handles rotation automatically; PyMuPDF may need `page.set_rotation(0)`.
- **Multi-column layouts**: Both parsers may merge columns incorrectly. Post-process with column detection heuristics if needed.
