"""
Pure-Python / NumPy vector store.

Stores embeddings in a .npy file and metadata in a JSON file.
Uses cosine similarity for retrieval. No native C extensions required.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Optional

import numpy as np

from scripts.lib.utils import get_logger, get_vector_store_path, load_rag_config, ensure_dir

logger = get_logger(__name__)

DEFAULT_COLLECTION = "customer-kb"
DEFAULT_PERSIST_PATH = "data/vector-store"


class RetrievedChunk:
    """A chunk returned by a similarity query."""

    def __init__(
        self,
        text: str,
        score: float,
        source_file: str,
        page_number: int,
        section_header: str,
        chunk_index: int,
        metadata: dict[str, Any],
    ) -> None:
        self.text = text
        self.score = score
        self.source_file = source_file
        self.page_number = page_number
        self.section_header = section_header
        self.chunk_index = chunk_index
        self.metadata = metadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "score": self.score,
            "source_file": self.source_file,
            "page_number": self.page_number,
            "section_header": self.section_header,
            "chunk_index": self.chunk_index,
        }


class VectorStore:
    """
    NumPy-backed vector store for RAG chunks.

    Persists:
      {persist_path}/{collection_name}_embeddings.npy  — float32 matrix (N x D)
      {persist_path}/{collection_name}_metadata.json   — list of chunk dicts
    """

    def __init__(
        self,
        persist_path: Optional[str | Path] = None,
        collection_name: str = DEFAULT_COLLECTION,
    ) -> None:
        self.persist_path = Path(persist_path) if persist_path else get_vector_store_path()
        self.collection_name = collection_name
        self._embeddings: Optional[np.ndarray] = None  # shape (N, D)
        self._metadata: list[dict[str, Any]] = []
        self._loaded = False

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------

    @property
    def _emb_path(self) -> Path:
        return self.persist_path / f"{self.collection_name}_embeddings.npy"

    @property
    def _meta_path(self) -> Path:
        return self.persist_path / f"{self.collection_name}_metadata.json"

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._loaded:
            return
        ensure_dir(self.persist_path)
        if self._emb_path.exists() and self._meta_path.exists():
            self._embeddings = np.load(str(self._emb_path))
            with open(self._meta_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)
            logger.info(
                "Loaded vector store '%s': %d chunks", self.collection_name, len(self._metadata)
            )
        else:
            self._embeddings = np.empty((0, 0), dtype=np.float32)
            self._metadata = []
            logger.info("New vector store '%s'", self.collection_name)
        self._loaded = True

    def _save(self) -> None:
        ensure_dir(self.persist_path)
        if self._embeddings is not None and self._embeddings.size > 0:
            np.save(str(self._emb_path), self._embeddings.astype(np.float32))
        with open(self._meta_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_chunks(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> int:
        if not chunks:
            return 0

        self._load()

        new_emb = np.array(embeddings, dtype=np.float32)

        if self._embeddings is None or self._embeddings.size == 0:
            self._embeddings = new_emb
        else:
            # Pad/trim to matching dimensions
            d_existing = self._embeddings.shape[1]
            d_new = new_emb.shape[1]
            if d_new < d_existing:
                padding = np.zeros((new_emb.shape[0], d_existing - d_new), dtype=np.float32)
                new_emb = np.hstack([new_emb, padding])
            elif d_new > d_existing:
                padding = np.zeros((self._embeddings.shape[0], d_new - d_existing), dtype=np.float32)
                self._embeddings = np.hstack([self._embeddings, padding])
            self._embeddings = np.vstack([self._embeddings, new_emb])

        for chunk in chunks:
            self._metadata.append({
                "id": str(uuid.uuid4()),
                "text": chunk.get("text", ""),
                "source_file": str(chunk.get("source_file", "")),
                "page_number": int(chunk.get("page_number", 0)),
                "section_header": str(chunk.get("section_header", "")),
                "chunk_index": int(chunk.get("chunk_index", 0)),
                "token_count": int(chunk.get("token_count", 0)),
            })

        self._save()
        logger.info("Added %d chunks (total: %d)", len(chunks), len(self._metadata))
        return len(chunks)

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        score_threshold: float = 0.0,
        where: Optional[dict] = None,
    ) -> list[RetrievedChunk]:
        self._load()

        if self._embeddings is None or self._embeddings.size == 0:
            return []

        q = np.array(query_embedding, dtype=np.float32)

        # Pad query vector if dimensions differ
        d_store = self._embeddings.shape[1]
        if len(q) < d_store:
            q = np.concatenate([q, np.zeros(d_store - len(q), dtype=np.float32)])
        elif len(q) > d_store:
            q = q[:d_store]

        # Cosine similarity
        norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True) + 1e-10
        normed = self._embeddings / norms
        q_norm = q / (np.linalg.norm(q) + 1e-10)
        scores = normed @ q_norm

        # Apply source filter
        if where and "source_file" in where:
            src_filter = where["source_file"]
            mask = np.array([
                m.get("source_file") == src_filter for m in self._metadata
            ])
            scores = np.where(mask, scores, -1.0)

        top_indices = np.argsort(scores)[::-1][:top_k]

        results: list[RetrievedChunk] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score < score_threshold:
                continue
            meta = self._metadata[idx]
            results.append(RetrievedChunk(
                text=meta["text"],
                score=score,
                source_file=meta.get("source_file", ""),
                page_number=int(meta.get("page_number", 0)),
                section_header=meta.get("section_header", ""),
                chunk_index=int(meta.get("chunk_index", 0)),
                metadata=meta,
            ))

        logger.debug("Query returned %d chunks above threshold %.2f", len(results), score_threshold)
        return results

    def delete_by_source(self, source_file: str) -> int:
        self._load()

        keep_indices = [
            i for i, m in enumerate(self._metadata)
            if m.get("source_file") != source_file
        ]
        deleted = len(self._metadata) - len(keep_indices)

        if deleted > 0:
            self._metadata = [self._metadata[i] for i in keep_indices]
            if self._embeddings is not None and self._embeddings.size > 0:
                self._embeddings = self._embeddings[keep_indices]
            self._save()
            logger.info("Deleted %d chunks for source '%s'", deleted, source_file)
        else:
            logger.warning("No chunks found for source '%s'", source_file)

        return deleted

    def list_sources(self) -> list[dict[str, Any]]:
        self._load()
        counts: dict[str, int] = {}
        for meta in self._metadata:
            src = meta.get("source_file", "unknown")
            counts[src] = counts.get(src, 0) + 1
        return [{"source_file": src, "chunk_count": n} for src, n in counts.items()]

    def count(self) -> int:
        self._load()
        return len(self._metadata)

    def reset(self) -> None:
        self._embeddings = np.empty((0, 0), dtype=np.float32)
        self._metadata = []
        self._save()
        logger.warning("Vector store '%s' has been reset.", self.collection_name)


def get_vector_store(config: Optional[dict] = None) -> VectorStore:
    if config is None:
        config = load_rag_config()
    vs_cfg = config.get("vector_store", {})
    return VectorStore(
        persist_path=vs_cfg.get("persist_path", DEFAULT_PERSIST_PATH),
        collection_name=vs_cfg.get("collection_name", DEFAULT_COLLECTION),
    )
