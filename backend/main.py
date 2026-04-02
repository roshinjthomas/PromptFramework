"""
FastAPI application entry point.

Mounts all routers, configures CORS, and serves the React UI build.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routers.chat import router as chat_router
from backend.routers.evaluation import router as evaluation_router
from backend.routers.knowledge_base import router as kb_router
from scripts.lib.utils import get_logger, load_env

# Load .env from project root
load_env()
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

async def _prewarm() -> None:
    """Pre-load embedder and vector store at startup to eliminate first-request delay."""
    try:
        from scripts.pipeline.retrieve import _get_shared_embedder, _get_shared_vector_store
        _get_shared_embedder()
        _get_shared_vector_store()
        logger.info("Pipeline pre-warmed: embedder and vector store ready.")
    except Exception as exc:
        logger.warning("Pre-warm skipped: %s", exc)


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Customer Service Chatbot",
        description=(
            "A RAG-based customer service chatbot framework backed by Phi-3 Mini, "
            "ChromaDB, and RAGAS evaluation."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — allow the Vite dev server and any production origin
    allowed_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in allowed_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup():
        await _prewarm()

    # API routers
    app.include_router(chat_router)
    app.include_router(evaluation_router, prefix="/api")
    app.include_router(kb_router)

    # Serve React build from ui/dist (only in production)
    ui_dist = Path(__file__).resolve().parents[1] / "ui" / "dist"
    if ui_dist.exists():
        app.mount("/assets", StaticFiles(directory=str(ui_dist / "assets")), name="assets")

        @app.get("/", include_in_schema=False)
        async def serve_ui() -> FileResponse:
            return FileResponse(str(ui_dist / "index.html"))

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str) -> FileResponse:
            """Catch-all route to support React Router client-side routing."""
            file_path = ui_dist / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(ui_dist / "index.html"))
    else:
        @app.get("/", include_in_schema=False)
        async def root():
            return {
                "message": "RAG Chatbot API is running.",
                "docs": "/docs",
                "ui": "Build the React app with `cd ui && npm run build` then restart.",
            }

    logger.info("FastAPI app created. Navigate to http://localhost:8000/docs for the API docs.")
    return app


app = create_app()


# ---------------------------------------------------------------------------
# Run directly with: python -m backend.main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=True,
        log_level="info",
    )
