"""
PDF parser using PyMuPDF as primary extractor and pdfplumber as fallback.

Returns a list of page dictionaries, each containing:
  - page_number (int, 1-based)
  - text (str)
  - tables (list[list[list[str]]])  — pdfplumber table data when detected
  - metadata (dict)                 — title, author, source_file, etc.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from scripts.lib.utils import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

PageData = dict[str, Any]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """Remove excessive whitespace, page numbers, and common header/footer noise."""
    # Collapse runs of blank lines to a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove lines that are purely page numbers (e.g., "  3  " or "Page 3 of 12")
    text = re.sub(r"(?m)^\s*(Page\s+\d+\s+of\s+\d+|\d+)\s*$", "", text)
    # Strip trailing whitespace from each line
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def _extract_section_header(text: str) -> str:
    """Heuristically detect a section header from the first non-empty line."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and len(stripped) < 120:
            return stripped
    return ""


# ---------------------------------------------------------------------------
# PyMuPDF primary parser
# ---------------------------------------------------------------------------

def _parse_with_pymupdf(pdf_path: Path) -> list[PageData]:
    """Parse a PDF with PyMuPDF (fitz). Raises on encrypted documents."""
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError("PyMuPDF (pymupdf) is not installed. Run: pip install pymupdf") from exc

    doc = fitz.open(str(pdf_path))

    if doc.is_encrypted:
        doc.close()
        raise ValueError(f"PDF is password-protected and cannot be parsed: {pdf_path.name}")

    pdf_metadata = doc.metadata or {}
    pages: list[PageData] = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        raw_text = page.get_text("text")  # type: ignore[attr-defined]
        cleaned = _clean_text(raw_text)

        pages.append(
            {
                "page_number": page_index + 1,
                "text": cleaned,
                "tables": [],
                "metadata": {
                    "source_file": pdf_path.name,
                    "source_path": str(pdf_path),
                    "title": pdf_metadata.get("title", ""),
                    "author": pdf_metadata.get("author", ""),
                    "section_header": _extract_section_header(cleaned),
                    "page_count": len(doc),
                },
            }
        )

    doc.close()
    logger.info("PyMuPDF parsed %d pages from '%s'", len(pages), pdf_path.name)
    return pages


# ---------------------------------------------------------------------------
# pdfplumber fallback parser (also handles tables)
# ---------------------------------------------------------------------------

def _parse_with_pdfplumber(pdf_path: Path) -> list[PageData]:
    """
    Parse a PDF with pdfplumber. Used as fallback when PyMuPDF yields empty
    pages (e.g., scanned/image-only PDFs) or to extract tables.
    """
    try:
        import pdfplumber
    except ImportError as exc:
        raise ImportError(
            "pdfplumber is not installed. Run: pip install pdfplumber"
        ) from exc

    pages: list[PageData] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        pdf_meta = pdf.metadata or {}
        total = len(pdf.pages)

        for page in pdf.pages:
            raw_text = page.extract_text() or ""
            cleaned = _clean_text(raw_text)

            # Extract tables
            raw_tables = page.extract_tables() or []
            tables: list[list[list[str]]] = [
                [[cell or "" for cell in row] for row in tbl]
                for tbl in raw_tables
            ]

            pages.append(
                {
                    "page_number": page.page_number,
                    "text": cleaned,
                    "tables": tables,
                    "metadata": {
                        "source_file": pdf_path.name,
                        "source_path": str(pdf_path),
                        "title": pdf_meta.get("Title", ""),
                        "author": pdf_meta.get("Author", ""),
                        "section_header": _extract_section_header(cleaned),
                        "page_count": total,
                    },
                }
            )

    logger.info("pdfplumber parsed %d pages from '%s'", len(pages), pdf_path.name)
    return pages


# ---------------------------------------------------------------------------
# OCR fallback for scanned PDFs
# ---------------------------------------------------------------------------

def _ocr_page_image(page_image: Any) -> str:
    """Run Tesseract OCR on a page image returned by pdfplumber."""
    try:
        import pytesseract
    except ImportError as exc:
        raise ImportError(
            "pytesseract is not installed. Run: pip install pytesseract"
        ) from exc

    text = pytesseract.image_to_string(page_image, lang="eng")
    return _clean_text(text)


def _parse_scanned_pdf(pdf_path: Path) -> list[PageData]:
    """Parse a scanned PDF by converting pages to images and running OCR."""
    try:
        import pdfplumber
    except ImportError as exc:
        raise ImportError("pdfplumber is required for OCR fallback.") from exc

    pages: list[PageData] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        total = len(pdf.pages)
        for page in pdf.pages:
            img = page.to_image(resolution=200).original
            ocr_text = _ocr_page_image(img)

            pages.append(
                {
                    "page_number": page.page_number,
                    "text": ocr_text,
                    "tables": [],
                    "metadata": {
                        "source_file": pdf_path.name,
                        "source_path": str(pdf_path),
                        "title": "",
                        "author": "",
                        "section_header": _extract_section_header(ocr_text),
                        "page_count": total,
                        "ocr": True,
                    },
                }
            )

    logger.info("OCR parsed %d pages from '%s'", len(pages), pdf_path.name)
    return pages


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_pdf(pdf_path: str | Path, *, ocr_fallback: bool = True) -> list[PageData]:
    """
    Parse a PDF document and return per-page data.

    Strategy:
    1. Try PyMuPDF for fast text extraction.
    2. If pages are mostly empty (likely scanned), fall back to pdfplumber.
    3. If pdfplumber also yields empty pages and ocr_fallback is True, run OCR.

    Args:
        pdf_path:    Path to the PDF file.
        ocr_fallback: Whether to attempt OCR on image-only PDFs.

    Returns:
        List of PageData dicts with keys: page_number, text, tables, metadata.

    Raises:
        ValueError: If the PDF is password-protected.
        FileNotFoundError: If the file does not exist.
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 50:
        raise ValueError(
            f"PDF exceeds 50 MB limit ({file_size_mb:.1f} MB). "
            "Please split the document before ingestion."
        )

    # --- Primary: PyMuPDF ---
    try:
        pages = _parse_with_pymupdf(pdf_path)
    except Exception as exc:
        logger.warning("PyMuPDF failed (%s), trying pdfplumber…", exc)
        pages = []

    # Check if extraction yielded meaningful text
    total_text = sum(len(p["text"]) for p in pages)
    if total_text < 50 * len(pages) if pages else True:
        logger.info(
            "PyMuPDF text sparse (avg %d chars/page), switching to pdfplumber",
            total_text // max(len(pages), 1),
        )
        try:
            pages = _parse_with_pdfplumber(pdf_path)
        except Exception as exc:
            logger.warning("pdfplumber failed (%s)", exc)
            pages = []

    # Check again — if still empty, try OCR
    total_text = sum(len(p["text"]) for p in pages)
    if total_text < 50 * len(pages) if pages else True:
        if ocr_fallback:
            logger.info("Attempting OCR fallback for '%s'", pdf_path.name)
            pages = _parse_scanned_pdf(pdf_path)
        else:
            logger.warning(
                "PDF '%s' appears to be scanned/image-only but OCR fallback is disabled.",
                pdf_path.name,
            )

    logger.info(
        "Parsed '%s': %d pages, %d total chars",
        pdf_path.name,
        len(pages),
        sum(len(p["text"]) for p in pages),
    )
    return pages
