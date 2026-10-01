"""Pydantic schemas for Phase 12: Experiment Matrix & Runner.

Strictly adheres to:
- instructions/23_EXPERIMENT_MATRIX.md
- instructions/40_RUN_ARTIFACT_SCHEMA.md
- instructions/41_FULL_MATRIX_PLANNING_AND_COST_CONTROL.md
"""

from __future__ import annotations

import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ExperimentType(StrEnum):
    """Categorization of scientific experiments E1 through E10."""

    E1_SANITY = "E1_SANITY"
    E2_HETEROGENEITY = "E2_HETEROGENEITY"
    E3_SCALABILITY = "E3_SCALABILITY"
    E4_MALICIOUS_CLIENTS = "E4_MALICIOUS_CLIENTS"
    E5_PROVENANCE_ATTACKS = "E5_PROVENANCE_ATTACKS"
    E6_UNSEEN_TO_MODEL = "E6_UNSEEN_TO_MODEL"
    E7_RAG_POISONING = "E7_RAG_POISONING"
    E8_ABLATION = "E8_ABLATION"
    E9_SYSTEMS = "E9_SYSTEMS"
    E10_VALIDATION_SENSITIVITY = "E10_VALIDATION_SENSITIVITY"


class RunStatus(StrEnum):
    """Execution status of an individual experiment run."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ExperimentDescriptor(BaseModel):
    """Deterministic configuration defining a single scientific experiment run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., description="Unique deterministic run identifier")
    experiment_type: ExperimentType = Field(..., description="E1 through E10 classification")
    dataset: Literal["ciciot2023", "edge_iiotset"] = Field(..., description="Dataset evaluated")
    method: str = Field(
        ...,
        description="Target method: b0_local, b1_centralized, fedavg, multikrum, fedtrimmedavg, sflnid, flow, bc2fl, rlfe_ids, lqb_ids, fedmse, pfl_ids, prorag_fl",
    )
    seed: int = Field(default=13, description="RNG seed from standard set [13, 37, 73, 101, 211]")
    num_clients: int = Field(
        default=10, ge=1, description="Number of participating federated clients"
    )
    alpha: float | None = Field(
        default=0.3, description="Dirichlet non-IID parameter, or None for IID"
    )
    attack_type: str = Field(default="none", description="Adversarial attack type if evaluated")
    malicious_fraction: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Fraction of malicious clients"
    )
    rag_poison_fraction: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Fraction of poisoned knowledge corpus"
    )
    ablation_id: str | None = Field(
        default=None, description="Ablation ladder identifier: A0 to A6"
    )
    global_rounds: int = Field(default=10, ge=1, description="Number of global federated rounds")
    local_epochs: int = Field(default=2, ge=1, description="Local training epochs per client round")
    batch_size: int = Field(default=128, ge=1, description="Batch size for training")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Fine-grained hyperparameter overrides"
    )
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class ArtifactEntry(BaseModel):
    """Metadata record for a single produced run artifact."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., description="Relative file path within runs/<run_id>/")
    sha256: str = Field(..., description="SHA-256 cryptographic digest")
    byte_size: int = Field(..., ge=0, description="File size in bytes")
    semantic_role: str = Field(
        ...,
        description="Semantic purpose: config, metrics, timing, communication, provenance, log, marker",
    )


class RunArtifactManifest(BaseModel):
    """Manifest tracking all artifacts generated during an experiment run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0.0")
    run_id: str = Field(..., description="Run identifier")
    experiment_type: ExperimentType
    completed_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )
    artifacts: list[ArtifactEntry] = Field(default_factory=list)
    total_byte_size: int = Field(default=0, ge=0)


class RunFailureRecord(BaseModel):
    """Structured failure diagnosis recorded in FAILED marker."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    stage: str = Field(..., description="Execution stage where error occurred")
    error_type: str = Field(..., description="Python exception class name")
    error_message: str = Field(..., description="Exception text description")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    traceback: str = Field(default="", description="Full stack traceback")


class MatrixPlanSummary(BaseModel):
    """Full experiment matrix run-count review and resource projection."""

    model_config = ConfigDict(extra="forbid")

    plan_name: str = Field(default="ProRAG-FL Frozen Experiment Matrix")
    generated_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )
    total_runs: int = Field(default=0, ge=0)
    runs_by_experiment: dict[str, int] = Field(default_factory=dict)
    runs_by_dataset: dict[str, int] = Field(default_factory=dict)
    runs_by_method: dict[str, int] = Field(default_factory=dict)
    runs_by_seed: dict[str, int] = Field(default_factory=dict)
    estimated_gpu_hours: float = Field(default=0.0, ge=0.0)
    estimated_cpu_hours: float = Field(default=0.0, ge=0.0)
    estimated_disk_mb: float = Field(default=0.0, ge=0.0)
    estimated_fabric_tx_count: int = Field(default=0, ge=0)
    estimated_openai_requests: int = Field(default=0, ge=0)
    estimated_openai_cost_usd: float = Field(default=0.0, ge=0.0)
