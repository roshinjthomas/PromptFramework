"""
Feedback collector.

Stores thumbs up/down ratings linked to query + response pairs.
Feedback is persisted as a JSON file per session in data/feedback/.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from scripts.lib.utils import get_feedback_path, get_logger, ensure_dir

logger = get_logger(__name__)

Rating = Literal["thumbs_up", "thumbs_down"]

# Single feedback store file (append-style)
FEEDBACK_FILE = "feedback_store.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_store_path() -> Path:
    store_dir = get_feedback_path()
    ensure_dir(store_dir)
    return store_dir / FEEDBACK_FILE


def _load_store() -> list[dict[str, Any]]:
    path = _get_store_path()
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            logger.warning("Feedback store is corrupted — starting fresh.")
            return []


def _save_store(records: list[dict[str, Any]]) -> None:
    path = _get_store_path()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def store_feedback(
    query: str,
    response: str,
    rating: Rating,
    *,
    session_id: Optional[str] = None,
    citations: Optional[list[dict[str, Any]]] = None,
    comment: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """
    Record a thumbs feedback entry.

    Args:
        query:      The user's question.
        response:   The chatbot's response.
        rating:     "thumbs_up" or "thumbs_down".
        session_id: Optional chat session identifier.
        citations:  List of citation dicts from the response.
        comment:    Optional free-text user comment.
        metadata:   Any additional metadata to store.

    Returns:
        The unique feedback entry ID.
    """
    entry_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    record: dict[str, Any] = {
        "id": entry_id,
        "timestamp": timestamp,
        "session_id": session_id,
        "rating": rating,
        "query": query,
        "response": response,
        "citations": citations or [],
        "comment": comment,
        "metadata": metadata or {},
    }

    records = _load_store()
    records.append(record)
    _save_store(records)

    logger.info("Feedback stored: %s for query '%s…'", rating, query[:60])
    return entry_id


def get_feedback(
    *,
    rating_filter: Optional[Rating] = None,
    session_id: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict[str, Any]]:
    """
    Retrieve stored feedback entries, optionally filtered.

    Args:
        rating_filter: Only return entries with this rating.
        session_id:    Only return entries for this session.
        limit:         Maximum number of entries to return (most recent first).

    Returns:
        List of feedback records.
    """
    records = _load_store()

    # Apply filters
    if rating_filter:
        records = [r for r in records if r.get("rating") == rating_filter]
    if session_id:
        records = [r for r in records if r.get("session_id") == session_id]

    # Most recent first
    records = list(reversed(records))

    if limit:
        records = records[:limit]

    return records


def get_feedback_stats() -> dict[str, Any]:
    """Return aggregate statistics about stored feedback."""
    records = _load_store()
    thumbs_up = sum(1 for r in records if r.get("rating") == "thumbs_up")
    thumbs_down = sum(1 for r in records if r.get("rating") == "thumbs_down")
    total = len(records)

    return {
        "total": total,
        "thumbs_up": thumbs_up,
        "thumbs_down": thumbs_down,
        "satisfaction_rate": round(thumbs_up / total, 4) if total > 0 else None,
    }
