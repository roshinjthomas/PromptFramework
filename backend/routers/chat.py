"""
Chat router — POST /api/chat

Runs the full RAG pipeline and streams the response via Server-Sent Events.
"""

from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from backend.models.chat import ChatRequest, ChatResponse, FeedbackRequest, FeedbackResponse
from scripts.lib.utils import get_logger, load_rag_config
from scripts.pipeline.retrieve import retrieve, format_context
from scripts.pipeline.inference import generate_response, astream_response
from scripts.pipeline.postprocess import postprocess

_executor = ThreadPoolExecutor(max_workers=4)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Non-streaming endpoint helper
# ---------------------------------------------------------------------------

def _run_rag_pipeline(request: ChatRequest) -> dict:
    """Run the full RAG pipeline synchronously and return a result dict."""
    cfg = load_rag_config()

    # 1. Retrieve
    chunks = retrieve(
        request.query,
        top_k=request.top_k,
        score_threshold=request.score_threshold,
        config=cfg,
    )
    context = format_context(chunks)

    # 2. Generate
    gen_result = generate_response(
        request.query,
        context,
        company_name=request.company_name,
    )

    # 3. Post-process
    post_result = postprocess(gen_result["response"], chunks)

    return {
        "response": post_result["response"],
        "citations": post_result["citations"],
        "used_fallback": post_result["used_fallback"],
        "session_id": request.session_id or str(uuid.uuid4()),
        "generation_time_s": gen_result["generation_time_s"],
        "model_id": gen_result["model_id"],
    }


# ---------------------------------------------------------------------------
# SSE streaming generator
# ---------------------------------------------------------------------------

async def _sse_stream(request: ChatRequest) -> AsyncGenerator[str, None]:
    """
    Async SSE generator that streams RAG pipeline output.

    Events emitted:
      - type: "chunk"  — token text
      - type: "sources" — citation list (JSON)
      - type: "done"   — signals end of stream
      - type: "error"  — error message
    """
    try:
        cfg = load_rag_config()

        # Retrieve (sync — fast enough for SSE prelude)
        chunks = retrieve(
            request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            config=cfg,
        )
        context = format_context(chunks)

        # Send sources immediately so the UI can render them while tokens stream
        post_meta = postprocess("", chunks, inject_sources=False, tone_check=False)
        sources_payload = json.dumps(
            {
                "citations": post_meta["citations"],
                "used_fallback": not bool(chunks),
            }
        )
        yield f"event: sources\ndata: {sources_payload}\n\n"

        if not chunks:
            from scripts.pipeline.postprocess import FALLBACK_RESPONSE
            for word in FALLBACK_RESPONSE.split(" "):
                yield f"event: chunk\ndata: {json.dumps(word + ' ')}\n\n"
        else:
            # Stream tokens asynchronously — no event loop blocking
            async for token in astream_response(
                request.query,
                context,
                company_name=request.company_name,
            ):
                if token:
                    yield f"event: chunk\ndata: {json.dumps(token)}\n\n"

        yield f"event: done\ndata: {json.dumps({'session_id': request.session_id or str(uuid.uuid4())})}\n\n"

    except Exception as exc:
        logger.error("SSE stream error: %s", exc)
        yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("")
async def chat(request: ChatRequest):
    """
    Run the RAG pipeline for the given query.

    - If `stream=True` (default): returns Server-Sent Events stream.
    - If `stream=False`: returns a complete JSON response.
    """
    if request.stream:
        return EventSourceResponse(_sse_stream(request))

    # Run blocking pipeline in thread pool to avoid blocking the event loop
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(_executor, _run_rag_pipeline, request)
    return ChatResponse(**result)


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """Record thumbs up/down feedback for a chat response."""
    from scripts.feedback.collector import store_feedback

    feedback_id = store_feedback(
        query=request.query,
        response=request.response,
        rating=request.rating,  # type: ignore[arg-type]
        session_id=request.session_id,
        citations=[c.dict() for c in request.citations] if request.citations else None,
        comment=request.comment,
    )

    return FeedbackResponse(feedback_id=feedback_id)
