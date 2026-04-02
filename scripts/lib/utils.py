"""
Shared utilities: path helpers, environment loading, and logging setup.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------

def get_project_root() -> Path:
    """Return the absolute path to the project root (rag-chatbot-framework/)."""
    # Walk up from this file: scripts/lib/utils.py -> scripts/lib -> scripts -> root
    return Path(__file__).resolve().parents[2]


def get_config_path(filename: str) -> Path:
    """Return the absolute path to a config file by name."""
    return get_project_root() / "config" / filename


def get_data_path(subpath: str = "") -> Path:
    """Return an absolute path inside data/."""
    base = get_project_root() / "data"
    return base / subpath if subpath else base


def get_vector_store_path() -> Path:
    """Return path to the ChromaDB / FAISS persist directory."""
    return get_data_path("vector-store")


def get_documents_path() -> Path:
    """Return path to the source PDF documents directory."""
    return get_data_path("documents")


def get_evaluation_path(subpath: str = "") -> Path:
    """Return path inside data/evaluation/."""
    base = get_data_path("evaluation")
    return base / subpath if subpath else base


def get_feedback_path() -> Path:
    """Return path to the feedback store directory."""
    return get_data_path("feedback")


def ensure_dir(path: Path) -> Path:
    """Create directory (and parents) if it does not exist. Returns the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------

def load_env(env_file: Optional[str] = None) -> None:
    """Load .env from project root (or a custom path)."""
    if env_file:
        load_dotenv(dotenv_path=env_file, override=False)
    else:
        load_dotenv(dotenv_path=get_project_root() / ".env", override=False)


# ---------------------------------------------------------------------------
# YAML config loading
# ---------------------------------------------------------------------------

def load_yaml(path: Path) -> dict:
    """Load and return a YAML file as a dictionary."""
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_rag_config() -> dict:
    """Load config/rag.yaml."""
    return load_yaml(get_config_path("rag.yaml"))


def load_slm_config() -> dict:
    """Load config/slm.yaml."""
    return load_yaml(get_config_path("slm.yaml"))


def load_evaluation_config() -> dict:
    """Load config/evaluation.yaml."""
    return load_yaml(get_config_path("evaluation.yaml"))


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

_LOG_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure root logger with a consistent format.

    Args:
        level:    Logging level string (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional file path to also write logs to.

    Returns:
        The root logger instance.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        ensure_dir(Path(log_file).parent)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=numeric_level,
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        handlers=handlers,
        force=True,
    )
    return logging.getLogger()


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Return a named logger. Call setup_logging() first for full configuration."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------

def truncate_text(text: str, max_chars: int = 200) -> str:
    """Truncate text for logging/display purposes."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"


def sanitize_source_id(source: str) -> str:
    """Convert a file path or URL to a safe ID string for ChromaDB metadata."""
    return Path(source).name.replace(" ", "_").lower()
