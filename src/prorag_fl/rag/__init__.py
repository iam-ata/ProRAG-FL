"""Hybrid Provenance-Aware RAG module: Query building, embeddings, Qdrant index, RRF, hard gating, and benchmark."""

from prorag_fl.rag.benchmark import evaluate_retrieval_benchmark
from prorag_fl.rag.embedder import HybridEmbedder
from prorag_fl.rag.hard_gate import HardProvenanceGate
from prorag_fl.rag.query_builder import construct_retrieval_query
from prorag_fl.rag.retriever import HybridRetriever
from prorag_fl.rag.vector_index import QdrantVectorIndex

__all__ = [
    "construct_retrieval_query",
    "HybridEmbedder",
    "QdrantVectorIndex",
    "HybridRetriever",
    "HardProvenanceGate",
    "evaluate_retrieval_benchmark",
]
