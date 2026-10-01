"""Evaluation and benchmarking utilities for Hybrid Provenance-Aware RAG."""

from __future__ import annotations

import time

from prorag_fl.rag.hard_gate import HardProvenanceGate
from prorag_fl.rag.retriever import HybridRetriever
from prorag_fl.schemas.rag import RetrievalBenchmarkMetrics, RetrievalQuery


def evaluate_retrieval_benchmark(
    retriever: HybridRetriever,
    hard_gate: HardProvenanceGate,
    query_ground_truth_pairs: list[tuple[RetrievalQuery, set[str]]],
    k_values: tuple[int, ...] = (1, 3, 5),
) -> RetrievalBenchmarkMetrics:
    """Evaluate Precision@K, Recall@K, MRR, and hard-gate rejection metrics.

    Adheres strictly to instructions/15_HYBRID_RAG.md:
    "Report Precision@K, Recall@K, MRR and Recall@5/support-hit rate."
    """
    total_queries = len(query_ground_truth_pairs)
    if total_queries == 0:
        return RetrievalBenchmarkMetrics()

    precisions: dict[int, list[float]] = {k: [] for k in k_values}
    recalls: dict[int, list[float]] = {k: [] for k in k_values}
    reciprocal_ranks: list[float] = []
    latencies_ms: list[float] = []

    total_candidates_examined = 0
    total_candidates_rejected = 0

    for query, relevant_doc_ids in query_ground_truth_pairs:
        start_t = time.perf_counter()

        # 1. Hybrid retrieval
        candidates = retriever.retrieve(query)
        total_candidates_examined += len(candidates)

        # 2. Hard Gate filtering & reranking
        verified_evidence = hard_gate.filter_and_rerank(candidates)
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        latencies_ms.append(elapsed_ms)

        retrieved_doc_ids = [e.document_id for e in verified_evidence]
        total_candidates_rejected += len(candidates) - len(verified_evidence)

        # Reciprocal Rank (first relevant document position)
        rr = 0.0
        for rank_0, doc_id in enumerate(retrieved_doc_ids):
            if doc_id in relevant_doc_ids:
                rr = 1.0 / (rank_0 + 1)
                break
        reciprocal_ranks.append(rr)

        # Precision@K and Recall@K
        for k in k_values:
            top_k_docs = retrieved_doc_ids[:k]
            hits = len(set(top_k_docs) & relevant_doc_ids)
            p_k = hits / k if k > 0 else 0.0
            r_k = hits / len(relevant_doc_ids) if relevant_doc_ids else 0.0
            precisions[k].append(p_k)
            recalls[k].append(r_k)

    mrr = float(sum(reciprocal_ranks) / total_queries)
    recall_at_5 = float(sum(recalls[5]) / total_queries) if 5 in recalls else 0.0
    rejection_rate = (
        total_candidates_rejected / total_candidates_examined
        if total_candidates_examined > 0
        else 0.0
    )

    avg_latency = float(sum(latencies_ms) / len(latencies_ms)) if latencies_ms else 0.0

    return RetrievalBenchmarkMetrics(
        precision_at_k={
            f"P@{k}": round(float(sum(precisions[k]) / total_queries), 4) for k in k_values
        },
        recall_at_k={f"R@{k}": round(float(sum(recalls[k]) / total_queries), 4) for k in k_values},
        mrr=round(mrr, 4),
        recall_at_5=round(recall_at_5, 4),
        hard_gate_rejection_rate=round(rejection_rate, 4),
        total_queries=total_queries,
        avg_latency_ms=round(avg_latency, 2),
    )
