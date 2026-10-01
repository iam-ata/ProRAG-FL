"""Hybrid Provenance-Aware RAG Overhead Benchmarking Suite.

Measures latency across every stage of the knowledge retrieval pipeline:
- Object Store (MinIO) Document Fetch
- BGE Dense Vector Embedding
- Qdrant Dense Vector Search
- BM25 Sparse Lexical Search
- Reciprocal Rank Fusion (RRF k=60)
- Hard Provenance Gate (6-Check Cryptographic Merkle Audit Path Verification)
- Multi-Factor Reranking (RRF + Temporal Freshness + Source Corroboration)
- Total End-to-End Retrieval Pipeline (Top-20 Candidates -> Top-5 Verified)

Strictly adheres to:
- instructions/25_SYSTEMS_BENCHMARKS.md:
  "MinIO fetch, BGE embedding/query, Qdrant dense/sparse, RRF, Merkle checks, reranking, final retrieval total."
"""

from __future__ import annotations

import logging
from typing import Any

from prorag_fl.benchmarks.schemas import RAGBenchmarkResult
from prorag_fl.benchmarks.timing import measure_callable
from prorag_fl.knowledge.adapters.mitre import MitreAttackAdapter
from prorag_fl.knowledge.adapters.nvd import NvdCveAdapter
from prorag_fl.knowledge.manager import KnowledgeManager
from prorag_fl.knowledge.object_store import KnowledgeObjectStore
from prorag_fl.rag.embedder import HybridEmbedder
from prorag_fl.rag.hard_gate import HardProvenanceGate
from prorag_fl.rag.retriever import HybridRetriever
from prorag_fl.rag.vector_index import QdrantVectorIndex
from prorag_fl.schemas.knowledge import KnowledgeChunk, KnowledgeDocument
from prorag_fl.schemas.rag import RetrievalQuery

logger = logging.getLogger(__name__)


def benchmark_rag_overhead(
    num_knowledge_docs: int = 10,
    top_candidates: int = 20,
    top_verified: int = 5,
    warmup_iterations: int = 10,
    benchmark_iterations: int = 50,
) -> RAGBenchmarkResult:
    """Execute rigorous benchmarking of every component of the RAG retrieval pipeline."""
    # 1. Initialize storage, knowledge manager, embedder, and vector index
    store = KnowledgeObjectStore()
    km = KnowledgeManager(object_store=store, chunk_size=250, chunk_overlap=30)
    embedder = HybridEmbedder(use_fallback=True)
    v_index = QdrantVectorIndex(location=":memory:", vector_dim=1024)

    mitre_adapter = MitreAttackAdapter()
    nvd_adapter = NvdCveAdapter()

    all_chunks: list[KnowledgeChunk] = []
    sample_doc: KnowledgeDocument | None = None

    # Ingest representative threat documents
    for i in range(num_knowledge_docs):
        d1, c1 = km.ingest_document(
            mitre_adapter,
            raw_data={
                "technique_id": f"T10{i:02d}",
                "name": f"Industrial Exploit Technique {i}",
                "description": f"Adversaries abuse industrial protocols with buffer overflow and unauthorized commands #{i}.",
                "tactics": ["Execution"],
            },
            version="v1.0.0",
        )
        if sample_doc is None:
            sample_doc = d1
        _, c2 = km.ingest_document(
            nvd_adapter,
            raw_data={
                "cve_id": f"CVE-2024-{1000 + i}",
                "description": f"Buffer overflow vulnerability in telemetry gateway #{i} enabling remote code execution.",
                "cvss_score": 9.8,
                "severity": "CRITICAL",
            },
            version="v1.0.0",
        )
        all_chunks.extend(c1)
        all_chunks.extend(c2)

    chunk_texts = [c.canonical_text for c in all_chunks]
    dense_vecs, sparse_vecs = embedder.embed(chunk_texts)
    v_index.index_chunks(all_chunks, dense_vecs, sparse_vecs)

    retriever = HybridRetriever(
        vector_index=v_index,
        embedder=embedder,
        top_k_dense=top_candidates,
        top_k_sparse=top_candidates,
        top_fused_candidates=top_candidates,
    )
    hard_gate = HardProvenanceGate(knowledge_manager=km, max_evidence=top_verified)

    sample_query = RetrievalQuery(
        query_id="query_bench_001",
        event_id="event_bench_001",
        query_text="buffer overflow vulnerability in telemetry gateway",
    )

    # A. MinIO / Object Store Fetch benchmark
    assert sample_doc is not None

    def run_minio_fetch() -> Any:
        return store.get_document(
            sample_doc.source_id,
            sample_doc.document_id,
            sample_doc.version,
            sample_doc.content_sha256,
        )

    minio_stats, _ = measure_callable(
        run_minio_fetch,
        warmup_iterations=warmup_iterations,
        benchmark_iterations=benchmark_iterations,
    )

    # B. Dense Vector Embedding benchmark
    def run_embedding() -> list[float]:
        dense, _ = embedder.embed([sample_query.query_text])
        return dense[0]

    embedding_stats, query_dense_vec = measure_callable(
        run_embedding,
        warmup_iterations=warmup_iterations,
        benchmark_iterations=benchmark_iterations,
    )

    # C. Qdrant Dense Vector Search benchmark
    def run_dense_search() -> list[tuple[KnowledgeChunk, float]]:
        return v_index.search_dense(query_dense_vec, top_n=top_candidates)

    dense_stats, _ = measure_callable(
        run_dense_search,
        warmup_iterations=warmup_iterations,
        benchmark_iterations=benchmark_iterations,
    )

    # D. BM25 Sparse Lexical Search benchmark
    _, query_sparse_vec = embedder.embed([sample_query.query_text])

    def run_sparse_search() -> list[tuple[KnowledgeChunk, float]]:
        return v_index.search_sparse(query_sparse_vec[0], top_n=top_candidates)

    sparse_stats, _ = measure_callable(
        run_sparse_search,
        warmup_iterations=warmup_iterations,
        benchmark_iterations=benchmark_iterations,
    )

    # E. RRF (Reciprocal Rank Fusion) benchmark
    dense_hits = v_index.search_dense(query_dense_vec, top_n=top_candidates)
    sparse_hits = v_index.search_sparse(query_sparse_vec[0], top_n=top_candidates)

    def run_rrf() -> list[tuple[KnowledgeChunk, float]]:
        fused: dict[str, tuple[KnowledgeChunk, float]] = {}
        for rank, (chunk, _) in enumerate(dense_hits):
            fused[chunk.chunk_id] = (chunk, 1.0 / (60 + rank + 1))
        for rank, (chunk, _) in enumerate(sparse_hits):
            score = 1.0 / (60 + rank + 1)
            if chunk.chunk_id in fused:
                existing_chunk, existing_score = fused[chunk.chunk_id]
                fused[chunk.chunk_id] = (existing_chunk, existing_score + score)
            else:
                fused[chunk.chunk_id] = (chunk, score)
        return sorted(fused.values(), key=lambda x: x[1], reverse=True)[:top_candidates]

    rrf_stats, candidate_fused = measure_callable(
        run_rrf,
        warmup_iterations=warmup_iterations,
        benchmark_iterations=benchmark_iterations,
    )

    # F. Hard Provenance Gate Merkle Verification benchmark
    sample_chunk = candidate_fused[0][0] if candidate_fused else all_chunks[0]

    def run_merkle_check() -> Any:
        return hard_gate.verify_candidate(sample_chunk)

    merkle_stats, _ = measure_callable(
        run_merkle_check,
        warmup_iterations=warmup_iterations,
        benchmark_iterations=benchmark_iterations,
    )

    # G. Multi-Factor Reranking benchmark
    def run_reranking() -> Any:
        return hard_gate.filter_and_rerank(candidate_fused)

    rerank_stats, verified_evidence = measure_callable(
        run_reranking,
        warmup_iterations=warmup_iterations,
        benchmark_iterations=benchmark_iterations,
    )

    # H. Total End-to-End Retrieval Pipeline benchmark
    def run_total_retrieval() -> Any:
        fused = retriever.retrieve(sample_query)
        return hard_gate.filter_and_rerank(fused)

    total_stats, final_verified = measure_callable(
        run_total_retrieval,
        warmup_iterations=warmup_iterations,
        benchmark_iterations=benchmark_iterations,
    )

    return RAGBenchmarkResult(
        minio_fetch_stats=minio_stats,
        embedding_stats=embedding_stats,
        dense_search_stats=dense_stats,
        sparse_search_stats=sparse_stats,
        rrf_fusion_stats=rrf_stats,
        merkle_verification_stats=merkle_stats,
        reranking_stats=rerank_stats,
        total_retrieval_stats=total_stats,
        candidates_retrieved=len(candidate_fused),
        verified_evidence_count=len(final_verified),
    )
