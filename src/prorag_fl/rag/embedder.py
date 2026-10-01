"""Dense and sparse text embedding pipeline for Hybrid RAG using BGE-M3 or fast deterministic fallback."""

from __future__ import annotations

import hashlib
import logging
import math
import re
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

BGE_M3_MODEL_ID = "BAAI/bge-m3"
EMBEDDING_DIM = 1024


class HybridEmbedder:
    """Computes dual dense (1024-D) and sparse lexical representations for Hybrid RAG.

    Supports BAAI/bge-m3 or deterministic high-speed fallback for offline reproducibility.
    """

    def __init__(
        self,
        model_name_or_path: str = BGE_M3_MODEL_ID,
        use_fallback: bool = True,
        embedding_dim: int = EMBEDDING_DIM,
    ) -> None:
        self.model_name = model_name_or_path
        self.use_fallback = use_fallback
        self.embedding_dim = embedding_dim
        self._model: Any = None

        if not self.use_fallback:
            try:
                from FlagEmbedding import BGEM3FlagModel

                self._model = BGEM3FlagModel(self.model_name, use_fp16=True)
                logger.info("Loaded BGE-M3 FlagEmbedding model %s", self.model_name)
            except Exception as e:
                logger.warning(
                    "FlagEmbedding BGE-M3 not available (%s); using deterministic fallback embedder.",
                    e,
                )
                self.use_fallback = True

    def embed_dense(self, texts: list[str]) -> list[list[float]]:
        """Compute normalized 1024-D dense embeddings for texts."""
        if not texts:
            return []

        if not self.use_fallback and self._model is not None:
            output = self._model.encode(texts, return_dense=True, return_sparse=False)
            dense_vecs = output["dense_vecs"]
            return [v.tolist() for v in dense_vecs]

        # Fast deterministic fallback: feature-hashed character/word n-gram embedding
        embeddings: list[list[float]] = []
        for text in texts:
            vec = np.zeros(self.embedding_dim, dtype=np.float32)
            words = re.findall(r"\w+", text.lower())
            for w in words:
                # Deterministic hash to dimension
                h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
                idx = h % self.embedding_dim
                sign = 1.0 if (h // self.embedding_dim) % 2 == 0 else -1.0
                vec[idx] += sign

            norm = np.linalg.norm(vec)
            if norm > 1e-9:
                vec /= norm
            embeddings.append(vec.tolist())

        return embeddings

    def embed_sparse(self, texts: list[str]) -> list[dict[str, float]]:
        """Compute sparse lexical token weightings (BM25 / lexical weights)."""
        if not texts:
            return []

        if not self.use_fallback and self._model is not None:
            output = self._model.encode(texts, return_dense=False, return_sparse=True)
            sparse_vecs = output["lexical_weights"]
            return [{str(k): float(v) for k, v in sv.items()} for sv in sparse_vecs]

        # Fast deterministic fallback: term-frequency sublinear weighting
        sparse_list: list[dict[str, float]] = []
        for text in texts:
            words = re.findall(r"\w+", text.lower())
            counts: dict[str, int] = {}
            for w in words:
                counts[w] = counts.get(w, 0) + 1

            lexical_weights: dict[str, float] = {}
            for w, count in counts.items():
                # Sublinear term frequency scaling: 1 + ln(count)
                lexical_weights[w] = round(1.0 + math.log(count), 4)

            sparse_list.append(lexical_weights)

        return sparse_list

    def embed(
        self,
        texts: list[str],
    ) -> tuple[list[list[float]], list[dict[str, float]]]:
        """Compute both dense and sparse representations concurrently."""
        dense_vecs = self.embed_dense(texts)
        sparse_vecs = self.embed_sparse(texts)
        return dense_vecs, sparse_vecs
