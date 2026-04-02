"""
Pydantic models for chat request and response.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A single source citation extracted from a RAG response."""
    id: int = Field(..., description="Citation index number (1-based).")
    source_file: str = Field(..., description="Source PDF filename.")
    page_number: int = Field(..., description="Page number within the source document.")
    section_header: str = Field(default="", description="Section heading of the chunk.")
    label: str = Field(..., description="Human-readable document label.")
    score: float = Field(..., description="Cosine similarity score (0–1).")
    text_excerpt: str = Field(default="", description="Short excerpt from the chunk.")


class ChatRequest(BaseModel):
    """Incoming chat request from the UI."""
    query: str = Field(..., min_length=1, max_length=2000, description="The customer's question.")
    session_id: Optional[str] = Field(default=None, description="Optional session identifier for multi-turn context.")
    company_name: str = Field(default="our company", description="Company name injected into the system prompt.")
    top_k: Optional[int] = Field(default=None, ge=1, le=20, description="Override retrieval top-K.")
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Override similarity threshold.")
    stream: bool = Field(default=True, description="If True, use SSE streaming.")


class ChatResponse(BaseModel):
    """Complete (non-streaming) chat response."""
    response: str = Field(..., description="The generated customer service response.")
    citations: list[Citation] = Field(default_factory=list, description="Source references.")
    used_fallback: bool = Field(default=False, description="True if no context was retrieved.")
    session_id: Optional[str] = Field(default=None)
    generation_time_s: float = Field(default=0.0)
    model_id: str = Field(default="")


class FeedbackRequest(BaseModel):
    """Thumbs up/down feedback from the user."""
    session_id: Optional[str] = None
    query: str
    response: str
    rating: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")
    comment: Optional[str] = None
    citations: Optional[list[Citation]] = None


class FeedbackResponse(BaseModel):
    """Feedback submission acknowledgement."""
    feedback_id: str
    message: str = "Feedback recorded. Thank you!"
