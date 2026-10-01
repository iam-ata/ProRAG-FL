"""Threat knowledge ingestion, canonicalization, Merkle provenance, and CTI adapters."""

from prorag_fl.knowledge.adapters import (
    BaseKnowledgeAdapter,
    CisaKevAdapter,
    ConsortiumIncidentAdapter,
    MitreAttackAdapter,
    NvdCveAdapter,
)
from prorag_fl.knowledge.canonicalizer import canonicalize_text, compute_canonical_hash
from prorag_fl.knowledge.chunker import DeterministicChunker
from prorag_fl.knowledge.manager import KnowledgeManager
from prorag_fl.knowledge.merkle import MerkleTree, verify_merkle_proof
from prorag_fl.knowledge.object_store import KnowledgeObjectStore

__all__ = [
    "canonicalize_text",
    "compute_canonical_hash",
    "MerkleTree",
    "verify_merkle_proof",
    "DeterministicChunker",
    "KnowledgeObjectStore",
    "KnowledgeManager",
    "BaseKnowledgeAdapter",
    "MitreAttackAdapter",
    "NvdCveAdapter",
    "CisaKevAdapter",
    "ConsortiumIncidentAdapter",
]
