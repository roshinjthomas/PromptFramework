"""
Pydantic models for RAGAS evaluation results.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class MetricScore(BaseModel):
    """Score for a single RAGAS metric."""
    score: float = Field(..., ge=0.0, le=1.0, description="Metric score between 0 and 1.")
    threshold: float = Field(..., description="Minimum passing threshold.")
    passed: bool = Field(..., description="True if score >= threshold.")


class RAGConfig(BaseModel):
    """RAG configuration snapshot used during a run."""
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    top_k: Optional[int] = None
    score_threshold: Optional[float] = None
    embedding_model: Optional[str] = None


class SLMConfig(BaseModel):
    """SLM configuration snapshot used during a run."""
    model_id: Optional[str] = None
    quantization: Optional[str] = None
    temperature: Optional[float] = None
    max_new_tokens: Optional[int] = None


class ConfigSnapshot(BaseModel):
    """Full config snapshot for a run."""
    rag: Optional[RAGConfig] = None
    slm: Optional[SLMConfig] = None


class PerQuestionResult(BaseModel):
    """Per-question score breakdown."""
    question: str
    answer: str
    ground_truth: str
    contexts: list[str] = Field(default_factory=list)
    source_document: Optional[str] = None
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    answer_correctness: Optional[float] = None


class EvalRun(BaseModel):
    """Full result for a single RAGAS evaluation run."""
    run_id: str
    timestamp: str
    duration_s: float
    question_count: int
    status: str = Field(..., description="'passed' or 'failed'")
    metrics: dict[str, MetricScore]
    per_question: list[dict[str, Any]] = Field(default_factory=list)
    config_snapshot: Optional[ConfigSnapshot] = None
    fail_on_threshold_breach: bool = True


class EvalRunSummary(BaseModel):
    """Lightweight summary of an evaluation run for listing."""
    run_id: str
    timestamp: str
    status: str
    question_count: int
    duration_s: float
    metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Flat map of metric_name -> score for quick display.",
    )
