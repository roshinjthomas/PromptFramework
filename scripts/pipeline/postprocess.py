"""
Response post-processor.

- Citation injection: appends source references to the response.
- Tone check: validates professional customer service language.
- Fallback guard: replaces response when no supporting context was found.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from scripts.lib.utils import get_logger
from scripts.lib.vector_store import RetrievedChunk

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FALLBACK_RESPONSE = (
    "I don't have specific information about that in my knowledge base.\n"
    "Please contact our support team at support@example.com or call 1-800-XXX-XXXX."
)

# Words/phrases that indicate the SLM is fabricating outside the context
HALLUCINATION_SIGNALS = [
    r"\bI believe\b",
    r"\bI think\b",
    r"\bprobably\b",
    r"\bmight be\b",
    r"\bI'm not sure\b",
    r"\bI cannot confirm\b",
]

# Unprofessional phrases to flag (can be extended)
TONE_VIOLATIONS = [
    r"\bfrank(ly)?\b",
    r"\bactually\b",
    r"\bobviously\b",
    r"\bstupid\b",
    r"\bdumb\b",
]


# ---------------------------------------------------------------------------
# Citation injection
# ---------------------------------------------------------------------------

def inject_citations(response: str, chunks: list[RetrievedChunk]) -> str:
    """
    Append a formatted citation list to the response.

    Citations are de-duplicated by (source_file, page_number).

    Example output:
        ...your answer text...

        Sources:
        [1] Returns Policy Guide, p.4
        [2] Shipping FAQ, p.2
    """
    if not chunks:
        return response

    seen: set[tuple[str, int]] = set()
    citation_lines: list[str] = []
    citation_index = 1

    for chunk in chunks:
        key = (chunk.source_file, chunk.page_number)
        if key in seen:
            continue
        seen.add(key)

        label = chunk.source_file.replace(".pdf", "").replace("-", " ").replace("_", " ").title()
        line = f"[{citation_index}] {label}, p.{chunk.page_number}"
        if chunk.section_header:
            line += f' — "{chunk.section_header[:60]}"'
        citation_lines.append(line)
        citation_index += 1

    if not citation_lines:
        return response

    citations_block = "\n\nSources:\n" + "\n".join(citation_lines)
    return response.rstrip() + citations_block


# ---------------------------------------------------------------------------
# Tone check
# ---------------------------------------------------------------------------

def check_tone(response: str) -> dict[str, Any]:
    """
    Check the response for tone violations and hallucination signals.

    Returns:
        Dict with:
          - is_acceptable (bool)
          - tone_violations (list[str])
          - hallucination_signals (list[str])
          - warnings (list[str])
    """
    tone_hits = [
        phrase
        for pattern in TONE_VIOLATIONS
        for phrase in re.findall(pattern, response, flags=re.IGNORECASE)
    ]
    hallucination_hits = [
        phrase
        for pattern in HALLUCINATION_SIGNALS
        for phrase in re.findall(pattern, response, flags=re.IGNORECASE)
    ]

    warnings: list[str] = []
    if tone_hits:
        warnings.append(f"Tone violations detected: {tone_hits}")
    if hallucination_hits:
        warnings.append(f"Potential hallucination signals: {hallucination_hits}")

    return {
        "is_acceptable": not bool(tone_hits or hallucination_hits),
        "tone_violations": tone_hits,
        "hallucination_signals": hallucination_hits,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Fallback guard
# ---------------------------------------------------------------------------

def apply_fallback_guard(
    response: str,
    chunks: list[RetrievedChunk],
    *,
    fallback_message: Optional[str] = None,
) -> str:
    """
    Replace the response with the fallback message when no chunks were retrieved.

    Args:
        response:         The SLM's generated response.
        chunks:           The retrieved chunks used to generate the response.
        fallback_message: Custom fallback text (defaults to FALLBACK_RESPONSE).

    Returns:
        The original response if chunks exist, otherwise the fallback message.
    """
    if not chunks:
        logger.info("No chunks retrieved — applying fallback guard.")
        return fallback_message or FALLBACK_RESPONSE
    return response


# ---------------------------------------------------------------------------
# Main postprocess function
# ---------------------------------------------------------------------------

def postprocess(
    response: str,
    chunks: list[RetrievedChunk],
    *,
    fallback_message: Optional[str] = None,
    inject_sources: bool = True,
    tone_check: bool = True,
) -> dict[str, Any]:
    """
    Full post-processing pipeline for a generated response.

    Args:
        response:         Raw response from the SLM.
        chunks:           Retrieved chunks used to generate the response.
        fallback_message: Override fallback message.
        inject_sources:   Whether to append citation list.
        tone_check:       Whether to run tone analysis.

    Returns:
        Dict with:
          - response (str): Final processed response text.
          - citations (list[dict]): Citation objects for the UI.
          - tone (dict): Tone check results.
          - used_fallback (bool): Whether the fallback was triggered.
    """
    # 1. Fallback guard
    response = apply_fallback_guard(response, chunks, fallback_message=fallback_message)
    used_fallback = not bool(chunks)

    # 2. Inject citations
    citations: list[dict[str, Any]] = []
    if inject_sources and not used_fallback:
        seen: set[tuple[str, int]] = set()
        idx = 1
        for chunk in chunks:
            key = (chunk.source_file, chunk.page_number)
            if key not in seen:
                seen.add(key)
                label = chunk.source_file.replace(".pdf", "").replace("-", " ").replace("_", " ").title()
                citations.append(
                    {
                        "id": idx,
                        "source_file": chunk.source_file,
                        "page_number": chunk.page_number,
                        "section_header": chunk.section_header,
                        "label": label,
                        "score": round(chunk.score, 4),
                        "text_excerpt": chunk.text[:200],
                    }
                )
                idx += 1
        response = inject_citations(response, chunks)

    # 3. Tone check
    tone_result = check_tone(response) if tone_check else {"is_acceptable": True, "warnings": []}
    if tone_result.get("warnings"):
        for w in tone_result["warnings"]:
            logger.warning("Post-process tone warning: %s", w)

    return {
        "response": response,
        "citations": citations,
        "tone": tone_result,
        "used_fallback": used_fallback,
    }
