"""Pydantic schemas for Security Events, Hybrid RAG, Provenance Filtering, and Evidence."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict, Field


class SecurityEvent(BaseModel):
    """Runtime-visible telemetry and model output for an escalated security incident.

    Adheres strictly to instructions/15_HYBRID_RAG.md:
    "Create query text only from runtime-visible SecurityEvent fields:
    prediction, abnormal-feature descriptions, protocol/device context, time context.
    Never include ground-truth label."
    """

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(..., description="Unique event identifier")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    model_predicted_class: str = Field(..., description="Predicted class name from IDS 1D-CNN")
    model_confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence C(x)")
    mahalanobis_distance: float = Field(..., ge=0.0, description="Mahalanobis OOD distance M(x)")
    gate_decision: str = Field(
        default="escalate", description="Routing decision: direct or escalate"
    )
    escalation_reason: str = Field(
        default="low_confidence",
        description="Escalation diagnostic: low_confidence, high_mahalanobis, or both",
    )
    abnormal_features: dict[str, float] = Field(
        default_factory=dict,
        description="Top deviating feature names and z-scores/values visible at inference time",
    )
    protocol_context: str = Field(
        default="TCP/IP", description="Network protocol context (e.g. MQTT, CoAP, DNS, TCP)"
    )
    device_context: str = Field(
        default="IoT Edge Gateway", description="Target device/node context"
    )
    raw_packet_summary: str = Field(
        default="", description="High-level traffic summary without ground-truth labels"
    )


class RetrievalQuery(BaseModel):
    """Search query formulated exclusively from SecurityEvent runtime context."""

    model_config = ConfigDict(extra="forbid")

    query_id: str = Field(..., description="Unique query identifier")
    event_id: str = Field(..., description="Originating security event ID")
    query_text: str = Field(..., description="Constructed query string for dense/sparse retrieval")
    dense_vector: list[float] | None = Field(default=None, description="Dense embedding vector")
    sparse_vector: dict[str, float] | None = Field(
        default=None, description="Sparse lexical vector"
    )
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class HardGateVerificationResult(BaseModel):
    """Cryptographic verification record for candidate chunk against blockchain & Merkle proofs."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(..., description="Chunk identifier")
    is_eligible: bool = Field(..., description="Overall eligibility decision")
    source_allowlisted: bool = Field(
        ..., description="Check 1: Source in authorized consortium list"
    )
    ledger_record_exists: bool = Field(..., description="Check 2: Ledger record exists")
    document_version_active: bool = Field(..., description="Check 3: Document version is active")
    chunk_hash_valid: bool = Field(
        ..., description="Check 4: SHA-256 chunk hash matches canonical text"
    )
    merkle_proof_valid: bool = Field(
        ..., description="Check 5: Merkle audit path matches anchored root"
    )
    not_revoked: bool = Field(..., description="Check 6: Neither document nor client is revoked")
    failure_reasons: list[str] = Field(
        default_factory=list, description="All failing check diagnostics"
    )


class VerifiedEvidence(BaseModel):
    """Top-ranked, cryptographically verified threat evidence delivered to the reasoning LLM."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., description="Unique evidence identifier")
    chunk_id: str = Field(..., description="Originating chunk ID")
    document_id: str = Field(..., description="Parent document identifier")
    source_id: str = Field(..., description="Authoritative source ID")
    document_version: str = Field(..., description="Active document version")
    chunk_index: int = Field(..., ge=0, description="Chunk position index")
    title: str = Field(default="", description="Threat intelligence title")
    canonical_text: str = Field(..., description="Verified canonical threat text")
    chunk_hash: str = Field(..., description="Verified SHA-256 chunk hash")
    merkle_root: str = Field(..., description="Anchored Merkle root")
    final_score: float = Field(..., description="Composite ranking score")
    rrf_score_norm: float = Field(
        default=0.0, description="Normalized Reciprocal Rank Fusion score"
    )
    freshness_score: float = Field(
        default=1.0, description="Temporal freshness score exp(-gamma * days)"
    )
    corroboration_score: float = Field(
        default=0.0, description="Independent multi-source corroboration score"
    )
    verification_record: HardGateVerificationResult = Field(
        ..., description="Complete cryptographic verification receipt"
    )


class RetrievalBenchmarkMetrics(BaseModel):
    """Evaluation metrics for the Hybrid RAG retrieval pipeline."""

    model_config = ConfigDict(extra="forbid")

    precision_at_k: dict[str, float] = Field(default_factory=dict)
    recall_at_k: dict[str, float] = Field(default_factory=dict)
    mrr: float = Field(default=0.0, ge=0.0, le=1.0)
    recall_at_5: float = Field(default=0.0, ge=0.0, le=1.0)
    hard_gate_rejection_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    total_queries: int = Field(default=0, ge=0)
    avg_latency_ms: float = Field(default=0.0, ge=0.0)
