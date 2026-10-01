"""Hybrid dense and sparse retriever with Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

from prorag_fl.rag.embedder import HybridEmbedder
from prorag_fl.rag.vector_index import QdrantVectorIndex
from prorag_fl.schemas.knowledge import KnowledgeChunk
from prorag_fl.schemas.rag import RetrievalQuery


class HybridRetriever:
    """Combines dense semantic and sparse lexical retrieval using Reciprocal Rank Fusion (RRF).

    Adheres strictly to instructions/15_HYBRID_RAG.md:
    1. dense Top-N
    2. sparse Top-N
    3. RRF fusion: RRF(d) = sum_over_rankers 1 / (k + rank_r(d))
    4. retain approximately Top-20 fused candidates.
    """

    def __init__(
        self,
        vector_index: QdrantVectorIndex,
        embedder: HybridEmbedder | None = None,
        top_k_dense: int = 30,
        top_k_sparse: int = 30,
        rrf_k: int = 60,
        top_fused_candidates: int = 20,
    ) -> None:
        self.vector_index = vector_index
        self.embedder = embedder or HybridEmbedder()
        self.top_k_dense = top_k_dense
        self.top_k_sparse = top_k_sparse
        self.rrf_k = rrf_k
        self.top_fused_candidates = top_fused_candidates

    def retrieve(
        self,
        query: RetrievalQuery | str,
        filter_source_id: str | None = None,
    ) -> list[tuple[KnowledgeChunk, float]]:
        """Execute hybrid search and return fused candidates ordered by RRF score."""
        query_text = query.query_text if isinstance(query, RetrievalQuery) else query

        # 1. Embed query
        dense_vecs, sparse_vecs = self.embedder.embed([query_text])
        dense_query = dense_vecs[0]
        sparse_query = sparse_vecs[0]

        # 2. Retrieve Top-N dense and Top-N sparse
        dense_results = self.vector_index.search_dense(
            dense_query, top_n=self.top_k_dense, filter_source_id=filter_source_id
        )
        sparse_results = self.vector_index.search_sparse(
            sparse_query, top_n=self.top_k_sparse, filter_source_id=filter_source_id
        )

        # 3. Compute Reciprocal Rank Fusion scores
        # candidate_id -> (chunk, rrf_score)
        fused_candidates: dict[str, tuple[KnowledgeChunk, float]] = {}

        # Dense rank contributions
        for rank_0, (chunk, _) in enumerate(dense_results):
            cid = chunk.chunk_id
            rank = rank_0 + 1  # 1-indexed
            rrf_contrib = 1.0 / (self.rrf_k + rank)
            _, current_score = fused_candidates.get(cid, (chunk, 0.0))
            fused_candidates[cid] = (chunk, current_score + rrf_contrib)

        # Sparse rank contributions
        for rank_0, (chunk, _) in enumerate(sparse_results):
            cid = chunk.chunk_id
            rank = rank_0 + 1  # 1-indexed
            rrf_contrib = 1.0 / (self.rrf_k + rank)
            _, current_score = fused_candidates.get(cid, (chunk, 0.0))
            fused_candidates[cid] = (chunk, current_score + rrf_contrib)

        # 4. Sort and retain approximately Top-20 fused candidates
        sorted_fused = sorted(fused_candidates.values(), key=lambda x: x[1], reverse=True)
        return sorted_fused[: self.top_fused_candidates]
