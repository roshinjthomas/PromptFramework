"""
TF-IDF + LSA embedding wrapper (pure Python, no torch/onnxruntime required).

Produces 384-dim dense vectors via TfidfVectorizer + TruncatedSVD.
The model is fit on the first batch of documents and persisted to disk
so that query embeddings stay in the same vector space.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Normalizer

from scripts.lib.utils import get_logger, load_rag_config

logger = get_logger(__name__)

DEFAULT_MODEL = "tfidf-lsa-384"
DEFAULT_BATCH_SIZE = 32
EMBEDDING_DIM = 384
MODEL_CACHE_PATH = Path("data/vector-store/embedder.pkl")


class Embedder:
    """
    TF-IDF + Truncated SVD (LSA) embedding.

    On first use the pipeline is fit to the corpus and cached to disk.
    Subsequent calls load the cached model so that query vectors are
    consistent with document vectors.

    Usage:
        embedder = Embedder()
        vectors = embedder.embed(["Hello world", "Another sentence"])
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        batch_size: int = DEFAULT_BATCH_SIZE,
        n_components: int = EMBEDDING_DIM,
        **kwargs,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.n_components = n_components
        self._pipeline: Optional[Pipeline] = None
        self._corpus: list[str] = []  # accumulated for fitting

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _cache_path(self) -> Path:
        return MODEL_CACHE_PATH

    def _save(self) -> None:
        path = self._cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self._pipeline, f)
        logger.info("Embedder pipeline saved to %s", path)

    def _load_cached(self) -> bool:
        path = self._cache_path()
        if path.exists():
            with open(path, "rb") as f:
                self._pipeline = pickle.load(f)
            logger.info("Loaded cached embedder from %s", path)
            return True
        return False

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    def _build_pipeline(self, texts: list[str]) -> None:
        """Fit TF-IDF + SVD on the provided texts."""
        n = min(self.n_components, len(texts) - 1)
        if n < 2:
            n = 2
        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                max_features=50_000,
                ngram_range=(1, 2),
                sublinear_tf=True,
                min_df=1,
            )),
            ("svd", TruncatedSVD(n_components=n, random_state=42)),
            ("norm", Normalizer(copy=False)),
        ])
        self._pipeline.fit(texts)
        self._save()
        logger.info("Embedder pipeline fit on %d texts, dim=%d", len(texts), n)

    def _ensure_pipeline(self, texts: list[str]) -> None:
        """Load cached pipeline or fit a new one."""
        if self._pipeline is not None:
            return
        if self._load_cached():
            return
        self._build_pipeline(texts)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def embedding_dim(self) -> int:
        if self._pipeline is None:
            self._load_cached()
        if self._pipeline is not None:
            return self._pipeline.named_steps["svd"].n_components
        return self.n_components

    def fit(self, texts: list[str]) -> None:
        """Explicitly fit the pipeline on a corpus (called during ingestion)."""
        self._build_pipeline(texts)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of strings and return float vectors.
        If no pipeline exists yet, fits on the provided texts.
        """
        if not texts:
            return []

        self._ensure_pipeline(texts)

        logger.debug("Embedding %d texts…", len(texts))
        matrix = self._pipeline.transform(texts)  # type: ignore[union-attr]

        # Pad to EMBEDDING_DIM if SVD produced fewer components
        current_dim = matrix.shape[1]
        if current_dim < EMBEDDING_DIM:
            padding = np.zeros((matrix.shape[0], EMBEDDING_DIM - current_dim))
            matrix = np.hstack([matrix, padding])

        return matrix.tolist()

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_one(query)


# ---------------------------------------------------------------------------
# Convenience factory from config
# ---------------------------------------------------------------------------

def get_embedder(config: Optional[dict] = None) -> Embedder:
    if config is None:
        config = load_rag_config()

    embedding_cfg = config.get("embedding", {})
    return Embedder(
        model_name=embedding_cfg.get("model", DEFAULT_MODEL),
        batch_size=embedding_cfg.get("batch_size", DEFAULT_BATCH_SIZE),
    )
