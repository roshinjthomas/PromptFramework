"""
Evaluation router.

GET  /api/evaluation/runs          - List all RAGAS evaluation runs
GET  /api/evaluation/runs/:run_id  - Full results for a specific run
GET  /api/evaluation/runs/:run_id/status - Status of a run
POST /api/evaluation/start         - Trigger a new RAGAS evaluation run
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

# Re-use the sub-app router from scripts/evaluation/api.py
from scripts.evaluation.api import router as _eval_sub_router

# Mount under /api/evaluation in main.py — here we just re-export it
router = APIRouter()
router.include_router(_eval_sub_router)
