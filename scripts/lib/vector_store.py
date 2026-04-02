"""
ChromaDB vector store interface.

Provides: add_chunks, query, delete_by_source, list_sources.
All data is persisted to data/vector-store/.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Optional

from scripts.lib.utils import (
    get_logger,
    get_vector_store_path,
    load_rag_config,
    ensure_dir,
    sanitize_source_id,
)

logger = get_logger(__name__)

DEFAULT_COLLECTION = "customer-kb"
DEFAULT_PERSIST_PATH = "data/vector-store"


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# VectorStore class
# ---------------------------------------------------------------------------

class VectorStore:
    """
    ChromaDB-backed vector store for RAG chunks.

    Constructor args:
        persist_path:     Directory to persist the ChromaDB data.
        collection_name:  ChromaDB collection name.
    """

    def __init__(
        self,
        persist_path: Optional[str | Path] = None,
        collection_name: str = DEFAULT_COLLECTION,
    ) -> None:
        self.persist_path = Path(persist_path) if persist_path else get_vector_store_path()
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    # ------------------------------------------------------------------
    # Lazy initialisation
    # ------------------------------------------------------------------

    def _get_collection(self):
        if self._collection is not None:
            return self._collection

        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError as exc:
            raise ImportError(
                "chromadb is not installed. Run: pip install chromadb"
            ) from exc

        ensure_dir(self.persist_path)

        self._client = chromadb.PersistentClient(
            path=str(self.persist_path),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB collection '%s' opened at '%s' (%d existing chunks)",
            self.collection_name,
            self.persist_path,
            self._collection.count(),
        )
        return self._collection

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_chunks(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> int:
        """
        Add chunks with pre-computed embeddings to the collection.

        Args:
            chunks:     List of chunk dicts (from Chunk.to_dict()).
            embeddings: Parallel list of embedding vectors.

        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0

        collection = self._get_collection()

        ids: list[str] = []
        docs: list[str] = []
        metas: list[dict] = []
        embeds: list[list[float]] = []

        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            docs.append(chunk["text"])
            embeds.append(embedding)
            metas.append(
                {
                    "source_file": str(chunk.get("source_file", "")),
                    "page_number": int(chunk.get("page_number", 0)),
                    "section_header": str(chunk.get("section_header", "")),
                    "chunk_index": int(chunk.get("chunk_index", 0)),
                    "token_count": int(chunk.get("token_count", 0)),
                }
            )

        collection.add(ids=ids, documents=docs, embeddings=embeds, metadatas=metas)
        logger.info("Added %d chunks to collection '%s'", len(ids), self.collection_name)
        return len(ids)

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        score_threshold: float = 0.0,
        where: Optional[dict] = None,
    ) -> list[RetrievedChunk]:
        """
        Query the vector store for the top-K most similar chunks.

        Args:
            query_embedding: Embedded query vector.
            top_k:           Maximum number of results to return.
            score_threshold: Minimum cosine similarity score (0–1) to include.
            where:           Optional ChromaDB metadata filter dict.

        Returns:
            List of RetrievedChunk objects, sorted by descending score.
        """
        collection = self._get_collection()

        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, max(collection.count(), 1)),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = collection.query(**kwargs)

        retrieved: list[RetrievedChunk] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, distance in zip(documents, metadatas, distances):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score in [0, 1]
            score = 1.0 - (distance / 2.0)
            if score < score_threshold:
                continue

            retrieved.append(
                RetrievedChunk(
                    text=doc,
                    score=score,
                    source_file=meta.get("source_file", ""),
                    page_number=int(meta.get("page_number", 0)),
                    section_header=meta.get("section_header", ""),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    metadata=meta,
                )
            )

        logger.debug(
            "Query returned %d chunks (before threshold: %d)", len(retrieved), len(documents)
        )
        return retrieved

    def delete_by_source(self, source_file: str) -> int:
        """
        Delete all chunks belonging to a specific source document.

        Args:
            source_file: The source_file metadata value to match (filename, not full path).

        Returns:
            Number of chunks deleted.
        """
        collection = self._get_collection()

        results = collection.get(
            where={"source_file": source_file},
            include=["metadatas"],
        )
        ids_to_delete = results.get("ids", [])

        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info(
                "Deleted %d chunks for source '%s'", len(ids_to_delete), source_file
            )
        else:
            logger.warning("No chunks found for source '%s'", source_file)

        return len(ids_to_delete)

    def list_sources(self) -> list[dict[str, Any]]:
        """
        List all unique source documents in the collection.

        Returns:
            List of dicts with source_file, chunk_count, and sample page_number.
        """
        collection = self._get_collection()
        all_meta = collection.get(include=["metadatas"])
        metadatas = all_meta.get("metadatas") or []

        counts: dict[str, dict[str, Any]] = {}
        for meta in metadatas:
            src = meta.get("source_file", "unknown")
            if src not in counts:
                counts[src] = {"source_file": src, "chunk_count": 0}
            counts[src]["chunk_count"] += 1

        return list(counts.values())

    def count(self) -> int:
        """Return total number of chunks in the collection."""
        return self._get_collection().count()

    def reset(self) -> None:
        """Delete and recreate the collection (destructive — use with caution)."""
        if self._client is not None:
            self._client.delete_collection(self.collection_name)
            self._collection = None
            logger.warning("Collection '%s' has been reset.", self.collection_name)


# ---------------------------------------------------------------------------
# Convenience factory from config
# ---------------------------------------------------------------------------

def get_vector_store(config: Optional[dict] = None) -> VectorStore:
    """Create a VectorStore from config/rag.yaml (or an override dict)."""
    if config is None:
        config = load_rag_config()

    vs_cfg = config.get("vector_store", {})
    persist = vs_cfg.get("persist_path", DEFAULT_PERSIST_PATH)
    collection = vs_cfg.get("collection_name", DEFAULT_COLLECTION)

    return VectorStore(persist_path=persist, collection_name=collection)
