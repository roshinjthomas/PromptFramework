"""
Sentence-transformers embedding wrapper.

Default model: all-MiniLM-L6-v2 (384-dim, fast, good semantic similarity).
Supports batch embedding for efficient ingestion.
"""

from __future__ import annotations

from typing import Optional

from scripts.lib.utils import get_logger, load_rag_config

logger = get_logger(__name__)

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_DEVICE = "cpu"
DEFAULT_BATCH_SIZE = 32


class Embedder:
    """
    Wrapper around sentence-transformers SentenceTransformer.

    Usage:
        embedder = Embedder()
        vectors = embedder.embed(["Hello world", "Another sentence"])
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = DEFAULT_DEVICE,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self._model = None  # lazy-loaded

    # ------------------------------------------------------------------
    # Lazy model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            ) from exc

        logger.info("Loading embedding model '%s' on device '%s'…", self.model_name, self.device)
        self._model = SentenceTransformer(self.model_name, device=self.device)
        logger.info("Embedding model loaded. Dimension: %d", self.embedding_dim)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def embedding_dim(self) -> int:
        """Return the output embedding dimension."""
        self._load_model()
        return self._model.get_sentence_embedding_dimension()  # type: ignore[union-attr]

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of strings and return a list of float vectors.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embedding vectors (each is a list of floats).
        """
        if not texts:
            return []

        self._load_model()

        logger.debug("Embedding %d texts in batches of %d…", len(texts), self.batch_size)
        embeddings = self._model.encode(  # type: ignore[union-attr]
            texts,
            batch_size=self.batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True,
            normalize_embeddings=True,  # cosine similarity via dot product
        )

        return embeddings.tolist()

    def embed_one(self, text: str) -> list[float]:
        """Embed a single string. Convenience wrapper around embed()."""
        return self.embed([text])[0]

    def embed_query(self, query: str) -> list[float]:
        """
        Embed a query string. Identical to embed_one but semantically clearer
        at call sites in the retrieval pipeline.
        """
        return self.embed_one(query)


# ---------------------------------------------------------------------------
# Convenience factory from config
# ---------------------------------------------------------------------------

def get_embedder(config: Optional[dict] = None) -> Embedder:
    """Create an Embedder from config/rag.yaml (or an override dict)."""
    if config is None:
        config = load_rag_config()

    embedding_cfg = config.get("embedding", {})
    return Embedder(
        model_name=embedding_cfg.get("model", DEFAULT_MODEL),
        device=embedding_cfg.get("device", DEFAULT_DEVICE),
        batch_size=embedding_cfg.get("batch_size", DEFAULT_BATCH_SIZE),
    )
