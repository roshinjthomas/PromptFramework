"""
Sliding-window text chunker.

Splits document text into overlapping chunks respecting paragraph boundaries.
Default: chunk_size=512 tokens, overlap=64 tokens.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from scripts.lib.utils import get_logger, load_rag_config

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Simple tokeniser (whitespace-based, good enough for chunk sizing)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Split text into whitespace tokens."""
    return text.split()


def _token_len(text: str) -> int:
    return len(_tokenize(text))


# ---------------------------------------------------------------------------
# Data class for a single chunk
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    text: str
    chunk_index: int
    source_file: str
    page_number: int
    section_header: str
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "chunk_index": self.chunk_index,
            "source_file": self.source_file,
            "page_number": self.page_number,
            "section_header": self.section_header,
            "token_count": self.token_count,
            **self.metadata,
        }


# ---------------------------------------------------------------------------
# Paragraph splitter
# ---------------------------------------------------------------------------

def _split_into_paragraphs(text: str) -> list[str]:
    """Split text on blank lines, returning non-empty paragraphs."""
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


# ---------------------------------------------------------------------------
# Core chunker
# ---------------------------------------------------------------------------

class SlidingWindowChunker:
    """
    Chunks a list of page texts using a sliding window strategy.

    The chunker:
    1. Splits each page into paragraphs (respects paragraph boundaries).
    2. Accumulates paragraphs until the token budget is reached.
    3. Slides forward by (chunk_size - overlap) tokens.
    4. Discards chunks smaller than min_chunk_size.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        min_chunk_size: int = 100,
        respect_paragraphs: bool = True,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.respect_paragraphs = respect_paragraphs

    # ------------------------------------------------------------------
    # Public method
    # ------------------------------------------------------------------

    def chunk_pages(self, pages: list[dict[str, Any]]) -> list[Chunk]:
        """
        Chunk a list of page dicts (as returned by pdf_parser.parse_pdf).

        Returns:
            List of Chunk objects with full metadata.
        """
        all_chunks: list[Chunk] = []
        global_index = 0

        for page_data in pages:
            page_text: str = page_data.get("text", "")
            page_num: int = page_data.get("page_number", 0)
            meta: dict = page_data.get("metadata", {})
            source_file: str = meta.get("source_file", "unknown")
            section_header: str = meta.get("section_header", "")

            if not page_text.strip():
                continue

            page_chunks = self._chunk_text(
                text=page_text,
                source_file=source_file,
                page_number=page_num,
                section_header=section_header,
                start_index=global_index,
            )
            all_chunks.extend(page_chunks)
            global_index += len(page_chunks)

        logger.info(
            "Chunker produced %d chunks from %d pages",
            len(all_chunks),
            len(pages),
        )
        return all_chunks

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _chunk_text(
        self,
        text: str,
        source_file: str,
        page_number: int,
        section_header: str,
        start_index: int,
    ) -> list[Chunk]:
        """Chunk a single page's text into overlapping windows."""
        if self.respect_paragraphs:
            units = _split_into_paragraphs(text)
        else:
            # Fall back to sentences if paragraphs disabled
            units = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

        if not units:
            return []

        chunks: list[Chunk] = []
        buffer: list[str] = []
        buffer_tokens = 0
        chunk_idx = start_index

        for unit in units:
            unit_tokens = _token_len(unit)

            # If a single unit exceeds chunk_size, split it by tokens
            if unit_tokens > self.chunk_size:
                # Flush current buffer first
                if buffer_tokens >= self.min_chunk_size:
                    chunk_text = " ".join(buffer)
                    chunks.append(
                        self._make_chunk(
                            chunk_text, chunk_idx, source_file, page_number, section_header
                        )
                    )
                    chunk_idx += 1
                    buffer, buffer_tokens = self._apply_overlap(buffer)

                # Split the oversized unit
                words = _tokenize(unit)
                for sub_chunk in self._split_tokens(words):
                    if _token_len(sub_chunk) >= self.min_chunk_size:
                        chunks.append(
                            self._make_chunk(
                                sub_chunk, chunk_idx, source_file, page_number, section_header
                            )
                        )
                        chunk_idx += 1
                continue

            # Would adding this unit overflow the chunk?
            if buffer_tokens + unit_tokens > self.chunk_size and buffer:
                if buffer_tokens >= self.min_chunk_size:
                    chunk_text = " ".join(buffer)
                    chunks.append(
                        self._make_chunk(
                            chunk_text, chunk_idx, source_file, page_number, section_header
                        )
                    )
                    chunk_idx += 1
                buffer, buffer_tokens = self._apply_overlap(buffer)

            buffer.append(unit)
            buffer_tokens += unit_tokens

        # Flush remaining buffer
        if buffer and buffer_tokens >= self.min_chunk_size:
            chunk_text = " ".join(buffer)
            chunks.append(
                self._make_chunk(
                    chunk_text, chunk_idx, source_file, page_number, section_header
                )
            )

        return chunks

    def _make_chunk(
        self,
        text: str,
        index: int,
        source_file: str,
        page_number: int,
        section_header: str,
    ) -> Chunk:
        return Chunk(
            text=text,
            chunk_index=index,
            source_file=source_file,
            page_number=page_number,
            section_header=section_header,
            token_count=_token_len(text),
        )

    def _apply_overlap(self, buffer: list[str]) -> tuple[list[str], int]:
        """
        Retain the last `overlap` tokens from the current buffer to seed the next chunk.
        """
        all_text = " ".join(buffer)
        all_words = _tokenize(all_text)

        overlap_words = all_words[-self.chunk_overlap :] if len(all_words) > self.chunk_overlap else all_words
        overlap_text = " ".join(overlap_words)
        return [overlap_text], len(overlap_words)

    def _split_tokens(self, words: list[str]) -> list[str]:
        """Split a token list into chunk_size chunks with overlap."""
        step = max(self.chunk_size - self.chunk_overlap, 1)
        results: list[str] = []
        i = 0
        while i < len(words):
            segment = words[i : i + self.chunk_size]
            results.append(" ".join(segment))
            i += step
        return results


# ---------------------------------------------------------------------------
# Convenience factory from config
# ---------------------------------------------------------------------------

def get_chunker(config: Optional[dict] = None) -> SlidingWindowChunker:
    """Create a SlidingWindowChunker from config/rag.yaml (or override dict)."""
    if config is None:
        config = load_rag_config()

    ingestion = config.get("ingestion", {})
    return SlidingWindowChunker(
        chunk_size=ingestion.get("chunk_size", 512),
        chunk_overlap=ingestion.get("chunk_overlap", 64),
        min_chunk_size=ingestion.get("min_chunk_size", 100),
        respect_paragraphs=ingestion.get("respect_paragraphs", True),
    )
