"""
FastAPI sub-application for evaluation endpoints.

Provides:
  GET  /runs           - List all evaluation runs
  GET  /runs/{run_id}  - Full results for a specific run
  POST /start          - Trigger a new RAGAS evaluation run
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from scripts.lib.utils import get_evaluation_path, get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


# ---------------------------------------------------------------------------
# Helper — results directory
# ---------------------------------------------------------------------------

def _results_dir() -> Path:
    return get_evaluation_path("results")


def _load_run(run_id: str) -> dict[str, Any]:
    path = _results_dir() / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _list_runs() -> list[dict[str, Any]]:
    results_dir = _results_dir()
    if not results_dir.exists():
        return []

    runs: list[dict[str, Any]] = []
    for path in sorted(results_dir.glob("*.json"), reverse=True):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # Return summary only (skip per_question for listing)
            runs.append(
                {
                    "run_id": data.get("run_id", path.stem),
                    "timestamp": data.get("timestamp", ""),
                    "status": data.get("status", "unknown"),
                    "question_count": data.get("question_count", 0),
                    "duration_s": data.get("duration_s", 0),
                    "metrics": {
                        k: v.get("score") for k, v in data.get("metrics", {}).items()
                    },
                }
            )
        except Exception as exc:
            logger.warning("Failed to read run file '%s': %s", path, exc)

    return runs


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class StartEvalRequest(BaseModel):
    dataset_path: Optional[str] = None
    metrics: Optional[list[str]] = None
    run_id: Optional[str] = None


class StartEvalResponse(BaseModel):
    run_id: str
    message: str


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------

_active_runs: dict[str, str] = {}  # run_id -> status


def _run_evaluation_task(run_id: str, dataset_path: Optional[str], metrics: Optional[list[str]]) -> None:
    """Background task to run RAGAS evaluation."""
    _active_runs[run_id] = "running"
    try:
        from scripts.evaluation.ragas_runner import run_evaluation
        run_evaluation(dataset_path=dataset_path, metrics=metrics, run_id=run_id)
        _active_runs[run_id] = "completed"
    except Exception as exc:
        logger.error("Evaluation run '%s' failed: %s", run_id, exc)
        _active_runs[run_id] = "failed"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/runs")
async def list_runs() -> list[dict[str, Any]]:
    """List all completed evaluation runs (summary only)."""
    return _list_runs()


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    """Return full results for a specific evaluation run."""
    return _load_run(run_id)


@router.post("/start", response_model=StartEvalResponse)
async def start_evaluation(
    request: StartEvalRequest, background_tasks: BackgroundTasks
) -> StartEvalResponse:
    """Trigger a new RAGAS evaluation run asynchronously."""
    import uuid
    from datetime import datetime, timezone

    run_id = request.run_id or f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"

    background_tasks.add_task(
        _run_evaluation_task,
        run_id,
        request.dataset_path,
        request.metrics,
    )

    _active_runs[run_id] = "queued"
    logger.info("Evaluation run '%s' queued.", run_id)

    return StartEvalResponse(
        run_id=run_id,
        message=f"Evaluation run '{run_id}' started. Poll GET /evaluation/runs/{run_id} for status.",
    )


@router.get("/runs/{run_id}/status")
async def get_run_status(run_id: str) -> dict[str, str]:
    """Return the current status of an in-progress or completed run."""
    if run_id in _active_runs:
        return {"run_id": run_id, "status": _active_runs[run_id]}
    # Check if result file exists (completed in a previous session)
    results_path = _results_dir() / f"{run_id}.json"
    if results_path.exists():
        return {"run_id": run_id, "status": "completed"}
    raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
