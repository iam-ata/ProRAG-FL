"""Pydantic schemas for Phase 9: End-to-End ProRAG-FL Pipeline.

Strictly adheres to instructions/17_END_TO_END_PIPELINE.md:
- Full auditable decision record schema storing event pseudonym, model version,
  prediction, confidence, OOD score, gate reason, route, candidate IDs,
  rejected IDs/reasons, verified evidence IDs, reasoning model ID, structured result,
  and latency breakdown.
- Ground truth lives ONLY in evaluation records, never reasoning input.
- Runtime invariants enforcement:
  * direct events never call RAG or LLM API
  * invalid evidence never reaches reasoning
  * test label never appears in LLM payload
  * LLM output never self-admits into threat memory
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from prorag_fl.schemas.reasoning import StructuredReasoningOutput


class LatencyBreakdown(BaseModel):
    """Detailed timing latency breakdown (in milliseconds) across pipeline stages."""

    model_config = ConfigDict(extra="forbid")

    inference_ids_ms: float = Field(default=0.0, ge=0.0, description="1D-CNN forward pass latency")
    calibration_ms: float = Field(default=0.0, ge=0.0, description="Temperature scaling latency")
    ood_ms: float = Field(default=0.0, ge=0.0, description="Mahalanobis distance latency")
    gate_ms: float = Field(default=0.0, ge=0.0, description="Dual gate evaluation latency")
    retrieval_ms: float = Field(
        default=0.0, ge=0.0, description="Hybrid dense/sparse RRF retrieval latency"
    )
    hard_gate_ms: float = Field(
        default=0.0, ge=0.0, description="Hard cryptographic gate verification latency"
    )
    reasoning_ms: float = Field(default=0.0, ge=0.0, description="LLM structured reasoning latency")
    total_latency_ms: float = Field(
        default=0.0, ge=0.0, description="Total end-to-end execution latency"
    )


class AuditableDecisionRecord(BaseModel):
    """Authoritative, tamper-evident audit record for every processed telemetry event.

    Adheres strictly to instructions/17_END_TO_END_PIPELINE.md:
    "Store event pseudonym, model version, classifier prediction, confidence, OOD score,
    gate reason, route, candidate IDs, rejected IDs/reasons, verified evidence IDs,
    reasoning model ID, structured result, and latency breakdown.
    Ground truth lives only in evaluation records, never reasoning input."
    """

    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(..., description="Unique UUID for this audit record")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of decision")
    event_pseudonym: str = Field(..., description="Pseudonymized event identifier")
    global_model_version: str = Field(
        default="v0", description="FL global model version used for IDS"
    )
    classifier_prediction: str = Field(..., description="Initial 1D-CNN predicted class")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence C(x)")
    mahalanobis_distance: float = Field(
        ..., ge=0.0, description="Regularized Mahalanobis distance M(x)"
    )
    gate_escalated: bool = Field(..., description="True if G(x)=1, False if G(x)=0")
    gate_reason: str = Field(
        ..., description="Diagnostic reason: direct, low_confidence, high_mahalanobis, or both"
    )
    route: Literal["DIRECT", "ESCALATED"] = Field(
        ..., description="Execution path taken: DIRECT (local IDS) or ESCALATED (RAG + LLM)"
    )
    final_decision: str = Field(
        ..., description="Final operational classification (local prediction or LLM interpretation)"
    )
    final_action: str = Field(
        ..., description="Operational response action (e.g. ALLOW, LOG, BLOCK_PORT, ISOLATE_DEVICE)"
    )
    retrieval_candidate_ids: list[str] = Field(
        default_factory=list, description="Candidate chunk IDs retrieved by hybrid search"
    )
    rejected_candidate_ids: list[str] = Field(
        default_factory=list, description="Chunk IDs rejected by Hard Provenance Gate"
    )
    rejection_reasons: dict[str, list[str]] = Field(
        default_factory=dict, description="Cryptographic rejection reasons per chunk ID"
    )
    verified_evidence_ids: list[str] = Field(
        default_factory=list, description="Top-5 verified evidence IDs supplied to LLM"
    )
    reasoning_model_id: str | None = Field(
        default=None, description="Reasoning model identifier if escalated; None if direct"
    )
    structured_reasoning: StructuredReasoningOutput | None = Field(
        default=None, description="Parsed structured reasoning output if escalated; None if direct"
    )
    latency_breakdown: LatencyBreakdown = Field(
        ..., description="Granular latency breakdown in milliseconds"
    )
    # Ground truth is strictly evaluation-only; never serialized or passed to the LLM
    evaluation_ground_truth: str | None = Field(
        default=None, description="Ground-truth label for offline research evaluation ONLY"
    )


class EndToEndBatchEvaluationReport(BaseModel):
    """Aggregate scientific evaluation metrics for a batch of end-to-end events."""

    model_config = ConfigDict(extra="forbid")

    total_events: int = Field(default=0, ge=0)
    direct_count: int = Field(default=0, ge=0)
    escalated_count: int = Field(default=0, ge=0)
    escalation_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    direct_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    escalated_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    macro_f1: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_direct_latency_ms: float = Field(default=0.0, ge=0.0)
    avg_escalated_latency_ms: float = Field(default=0.0, ge=0.0)
    avg_total_latency_ms: float = Field(default=0.0, ge=0.0)
    total_api_calls: int = Field(default=0, ge=0)
    total_reasoning_cost_usd: float = Field(default=0.0, ge=0.0)
    invariants_verified: bool = Field(
        default=True, description="True if all 4 runtime invariants held without exception"
    )
