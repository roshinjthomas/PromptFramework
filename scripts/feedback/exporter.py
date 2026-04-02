"""
Feedback exporter.

Converts stored thumbs feedback into JSONL format suitable for SLM fine-tuning.
Supports filtering by rating so only high-quality (thumbs-up) pairs are exported.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from scripts.feedback.collector import get_feedback
from scripts.lib.utils import get_data_path, get_logger, ensure_dir

logger = get_logger(__name__)

Rating = Literal["thumbs_up", "thumbs_down"]

# ---------------------------------------------------------------------------
# JSONL format builders
# ---------------------------------------------------------------------------

def _to_chat_format(record: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a feedback record to OpenAI chat fine-tuning format.

    Format:
      {"messages": [
          {"role": "user", "content": "<query>"},
          {"role": "assistant", "content": "<response>"}
      ]}
    """
    return {
        "messages": [
            {"role": "user", "content": record["query"]},
            {"role": "assistant", "content": record["response"]},
        ],
        "_meta": {
            "id": record["id"],
            "rating": record["rating"],
            "timestamp": record["timestamp"],
            "session_id": record.get("session_id"),
        },
    }


def _to_instruction_format(record: dict[str, Any]) -> dict[str, Any]:
    """
    Convert to instruction-following format (Alpaca-style).

    Format:
      {"instruction": "<query>", "input": "", "output": "<response>"}
    """
    return {
        "instruction": record["query"],
        "input": "",
        "output": record["response"],
        "_meta": {
            "id": record["id"],
            "rating": record["rating"],
            "timestamp": record["timestamp"],
        },
    }


# ---------------------------------------------------------------------------
# Export function
# ---------------------------------------------------------------------------

def export_dataset(
    *,
    output_path: Optional[str | Path] = None,
    min_rating: Rating = "thumbs_up",
    format: Literal["chat", "instruction"] = "chat",
    session_id: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict[str, Any]:
    """
    Export feedback records as a JSONL fine-tuning dataset.

    Args:
        output_path: Where to write the JSONL file (defaults to data/finetune-dataset.jsonl).
        min_rating:  Only include entries with this rating ("thumbs_up" recommended).
        format:      JSONL format: "chat" (OpenAI) or "instruction" (Alpaca).
        session_id:  Filter to a specific session.
        limit:       Maximum number of examples to export.

    Returns:
        Dict with output_path, count, format, timestamp.
    """
    records = get_feedback(rating_filter=min_rating, session_id=session_id, limit=limit)

    if not records:
        logger.warning(
            "No feedback records found with rating='%s'. Dataset will be empty.", min_rating
        )

    # Convert to chosen format
    converter = _to_chat_format if format == "chat" else _to_instruction_format
    examples = [converter(r) for r in records]

    # Resolve output path
    if output_path is None:
        out_dir = get_data_path()
        ensure_dir(out_dir)
        output_path = out_dir / "finetune-dataset.jsonl"
    output_path = Path(output_path)
    ensure_dir(output_path.parent)

    # Write JSONL
    with open(output_path, "w", encoding="utf-8") as fh:
        for example in examples:
            fh.write(json.dumps(example, ensure_ascii=False) + "\n")

    result = {
        "output_path": str(output_path),
        "count": len(examples),
        "format": format,
        "min_rating": min_rating,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Exported %d examples (%s format) to '%s'",
        len(examples),
        format,
        output_path,
    )
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export feedback as fine-tuning JSONL.")
    parser.add_argument("--output", default=None, help="Output JSONL file path")
    parser.add_argument(
        "--min-rating",
        default="thumbs_up",
        choices=["thumbs_up", "thumbs_down"],
        help="Minimum rating to include",
    )
    parser.add_argument(
        "--format",
        default="chat",
        choices=["chat", "instruction"],
        help="JSONL format",
    )
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    result = export_dataset(
        output_path=args.output,
        min_rating=args.min_rating,
        format=args.format,
        limit=args.limit,
    )
    print(json.dumps(result, indent=2))
