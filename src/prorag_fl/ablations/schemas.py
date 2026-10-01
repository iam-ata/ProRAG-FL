"""Pydantic schemas for Phase 13: Ablation and Sensitivity Analysis.

Strictly adheres to:
- instructions/24_ABLATION_AND_SENSITIVITY.md
- instructions/19_METRICS_AND_STATISTICS.md
- instructions/36_PHASE_ACCEPTANCE_GATES.md (P13)
"""

from __future__ import annotations

import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LadderStep(StrEnum):
    """The 7 canonical steps of the ProRAG-FL architectural ablation ladder."""

    A0 = "A0"  # FedAvg + 1D-CNN
    A1 = "A1"  # FedTrimmedAvg + 1D-CNN
    A2 = "A2"  # Provenance-gated FedTrimmedAvg
    A3 = "A3"  # A2 + ordinary hybrid RAG without knowledge provenance
    A4 = "A4"  # A2 + hard provenance RAG without freshness/corroboration
    A5 = "A5"  # Routing disabled (all-event RAG to quantify cost/routing value)
    A6 = "A6"  # Full ProRAG-FL


class AblationStepConfig(BaseModel):
    """Architectural component configuration for a specific ablation ladder step."""

    model_config = ConfigDict(extra="forbid")

    step: LadderStep
    name: str = Field(..., description="Human-readable step name")
    description: str = Field(..., description="Hypothesis tested by this step")
    fl_aggregation: str = Field(
        default="fedavg", description="FL strategy: fedavg, fedtrimmedavg, or provenance_gated"
    )
    model_provenance_enabled: bool = Field(
        default=False, description="Hyperledger Fabric model provenance verification gate"
    )
    dual_gate_routing_enabled: bool = Field(
        default=False, description="Selective routing via Temperature Scaling + Mahalanobis OOD"
    )
    force_all_events_escalated: bool = Field(
        default=False, description="True for A5 routing cost ablation (100% events escalated)"
    )
    hybrid_rag_enabled: bool = Field(
        default=False, description="Hybrid dense BGE-M3 + sparse BM25 retrieval"
    )
    knowledge_provenance_enabled: bool = Field(
        default=False, description="Hard Provenance Gate 6-check cryptographic verification"
    )
    multifactor_reranking_enabled: bool = Field(
        default=False, description="Multi-factor corroboration and temporal freshness reranking"
    )
    llm_reasoning_enabled: bool = Field(
        default=False, description="Structured Pydantic LLM CTI reasoning"
    )


class AblationStepResult(BaseModel):
    """Empirical evaluation result for a single ablation ladder step."""

    model_config = ConfigDict(extra="forbid")

    step: LadderStep
    name: str
    dataset: str
    macro_f1: float = Field(..., ge=0.0, le=1.0)
    accuracy: float = Field(..., ge=0.0, le=1.0)
    operational_fpr: float = Field(..., ge=0.0, le=1.0)
    byzantine_resilience_f1: float = Field(
        ..., ge=0.0, le=1.0, description="Macro-F1 under 20% update poisoning"
    )
    provenance_tamper_rejection_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Detection rate of tampered model provenance updates"
    )
    zero_day_detection_recall: float = Field(
        ..., ge=0.0, le=1.0, description="Detection recall on held-out zero-day attacks"
    )
    rag_invocation_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of flows escalated to RAG + LLM"
    )
    avg_latency_ms: float = Field(..., ge=0.0, description="Average end-to-end latency per flow")
    estimated_cost_usd_per_10k: float = Field(
        ..., ge=0.0, description="Estimated LLM API cost in USD per 10,000 flows"
    )


class AblationLadderReport(BaseModel):
    """Complete evaluation report for the A0 through A6 ablation ladder."""

    model_config = ConfigDict(extra="forbid")

    dataset: str
    generated_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )
    steps: list[AblationStepResult]
    summary_notes: list[str] = Field(default_factory=list)


class SensitivityGridPoint(BaseModel):
    """Single evaluated hyperparameter configuration on validation split."""

    model_config = ConfigDict(extra="forbid")

    parameter_name: str
    parameter_value: Any
    macro_f1: float
    operational_fpr: float
    rag_invocation_rate: float
    objective_score: float = Field(
        ..., description="Objective: Macro-F1 - 0.5*FPR - 0.1*InvocationRate"
    )


class SensitivityReport(BaseModel):
    """Results of hyperparameter sensitivity sweeps on validation data."""

    model_config = ConfigDict(extra="forbid")

    dataset: str
    generated_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )
    beta_sweep: list[SensitivityGridPoint] = Field(default_factory=list)
    tau_c_sweep: list[SensitivityGridPoint] = Field(default_factory=list)
    tau_m_sweep: list[SensitivityGridPoint] = Field(default_factory=list)
    top_k_sweep: list[SensitivityGridPoint] = Field(default_factory=list)
    rerank_weights_sweep: list[SensitivityGridPoint] = Field(default_factory=list)
    selected_optimal_config: dict[str, Any] = Field(default_factory=dict)


class FrozenParametersRecord(BaseModel):
    """Immutable, hash-anchored record of validation-tuned hyperparameters.

    Adheres strictly to instructions/24_ABLATION_AND_SENSITIVITY.md:
    "Write selected values to artifacts/frozen_parameters/<dataset>/<hash>.yaml.
     Final test code must refuse tuning flags."
    """

    model_config = ConfigDict(extra="forbid")

    dataset: str
    config_hash: str
    frozen_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    frozen_by: str = Field(default="ProRAG-FL Validation Sensitivity Protocol")

    # Tuned hyperparameters
    beta: float = Field(
        default=0.20, ge=0.0, lt=0.50, description="Coordinate-wise trimming fraction"
    )
    tau_c: float = Field(
        default=0.80, ge=0.0, le=1.0, description="Calibrated confidence escalation threshold"
    )
    tau_m: float = Field(default=5.0, ge=0.0, description="Mahalanobis OOD distance threshold")
    top_candidates: int = Field(
        default=20, gt=0, description="Hybrid candidate retrieval pool size"
    )
    top_verified: int = Field(default=5, gt=0, description="Final verified evidence count for LLM")
    lambda_rrf: float = Field(default=0.60, ge=0.0, le=1.0)
    lambda_freshness: float = Field(default=0.20, ge=0.0, le=1.0)
    lambda_corroboration: float = Field(default=0.20, ge=0.0, le=1.0)

    # Validation performance achieved
    validation_macro_f1: float = Field(default=0.0)
    validation_operational_fpr: float = Field(default=0.0)
    validation_objective_score: float = Field(default=0.0)
