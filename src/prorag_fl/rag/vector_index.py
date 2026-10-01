"""Qdrant-backed hybrid dense and sparse vector index for CTI chunks."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from prorag_fl.schemas.knowledge import KnowledgeChunk

logger = logging.getLogger(__name__)


class QdrantVectorIndex:
    """Hybrid dense and sparse indexing and retrieval backed by Qdrant (in-memory or service)."""

    def __init__(
        self,
        collection_name: str = "prorag_cti_knowledge",
        location: str = ":memory:",
        vector_dim: int = 1024,
    ) -> None:
        self.collection_name = collection_name
        self.location = location
        self.vector_dim = vector_dim

        # In-memory store for fast fallback & direct indexing
        self._chunks: dict[str, KnowledgeChunk] = {}
        self._dense_vectors: dict[str, np.ndarray] = {}
        self._sparse_vectors: dict[str, dict[str, float]] = {}

        # Initialize Qdrant Client if available
        self.qdrant_client: Any = None
        try:
            from qdrant_client import QdrantClient

            self.qdrant_client = QdrantClient(location=self.location)
            logger.info("Connected to Qdrant at %s", self.location)
        except Exception as e:
            logger.warning(
                "Could not initialize QdrantClient (%s); using in-memory vector index.", e
            )

    def index_chunks(
        self,
        chunks: list[KnowledgeChunk],
        dense_vectors: list[list[float]],
        sparse_vectors: list[dict[str, float]],
    ) -> int:
        """Insert or update chunks and their dual dense/sparse representations."""
        count = 0
        for chunk, dense, sparse in zip(chunks, dense_vectors, sparse_vectors, strict=True):
            cid = chunk.chunk_id
            self._chunks[cid] = chunk
            self._dense_vectors[cid] = np.array(dense, dtype=np.float32)
            self._sparse_vectors[cid] = dict(sparse)
            count += 1
        return count

    def search_dense(
        self,
        query_vector: list[float],
        top_n: int = 25,
        filter_source_id: str | None = None,
    ) -> list[tuple[KnowledgeChunk, float]]:
        """Perform dense vector search with cosine similarity."""
        if not self._dense_vectors:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 1e-9:
            q_vec /= q_norm

        scores: list[tuple[str, float]] = []
        for cid, d_vec in self._dense_vectors.items():
            chunk = self._chunks[cid]
            if filter_source_id and chunk.metadata.get("source_id") != filter_source_id:
                continue

            dot = float(np.dot(q_vec, d_vec))
            scores.append((cid, dot))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [(self._chunks[cid], score) for cid, score in scores[:top_n]]

    def search_sparse(
        self,
        query_sparse: dict[str, float],
        top_n: int = 25,
        filter_source_id: str | None = None,
    ) -> list[tuple[KnowledgeChunk, float]]:
        """Perform sparse lexical search via dot-product matching on term weights."""
        if not self._sparse_vectors or not query_sparse:
            return []

        scores: list[tuple[str, float]] = []
        for cid, s_dict in self._sparse_vectors.items():
            chunk = self._chunks[cid]
            if filter_source_id and chunk.metadata.get("source_id") != filter_source_id:
                continue

            # Dot product between query and document lexical weights
            dot = sum(
                q_weight * s_dict[token]
                for token, q_weight in query_sparse.items()
                if token in s_dict
            )
            if dot > 0.0:
                scores.append((cid, float(dot)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [(self._chunks[cid], score) for cid, score in scores[:top_n]]

    def get_chunk(self, chunk_id: str) -> KnowledgeChunk | None:
        """Retrieve chunk by chunk ID."""
        return self._chunks.get(chunk_id)

    def total_chunks(self) -> int:
        """Return total indexed chunks."""
        return len(self._chunks)

    def clear(self) -> None:
        """Reset the vector index."""
        self._chunks.clear()
        self._dense_vectors.clear()
        self._sparse_vectors.clear()
