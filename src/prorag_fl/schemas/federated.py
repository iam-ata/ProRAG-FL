"""Pydantic schemas for Federated Learning envelopes, per-round audit logs, and simulation results."""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ModelProvenanceEnvelope(BaseModel):
    """Cryptographic provenance envelope accompanying client model updates."""

    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., description="Unique client identifier")
    server_round: int = Field(..., ge=0, description="FL round index")
    global_model_version: str = Field(
        ..., description="Identifier of the global model trained upon"
    )
    update_digest: str = Field(..., description="SHA-256 digest of serialized model parameter diff")
    num_examples: int = Field(..., gt=0, description="Local training sample count")
    local_loss: float = Field(..., ge=0.0, description="Training loss achieved locally")
    local_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Training accuracy achieved locally"
    )
    signature: str = Field(default="mock_sig", description="Cryptographic signature of envelope")
    nonce: str = Field(..., description="Unique single-use nonce for replay prevention")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    status: str = Field(default="valid", description="Lifecycle validity status")


class RoundAuditLog(BaseModel):
    """Per-round audit record capturing provenance, metrics, bytes, and aggregation state."""

    model_config = ConfigDict(extra="forbid")

    server_round: int
    global_model_version: str
    strategy_name: str
    num_participating: int
    num_accepted: int
    num_rejected: int
    accepted_clients: list[str] = Field(default_factory=list)
    rejections: dict[str, str] = Field(
        default_factory=dict, description="client_id -> rejection reason"
    )
    local_metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    aggregation_time_seconds: float = 0.0
    global_val_loss: float | None = None
    global_val_accuracy: float | None = None
    global_val_macro_f1: float | None = None
    model_bytes_sent: int = Field(default=0, ge=0)
    update_bytes_received: int = Field(default=0, ge=0)
    metadata_bytes_received: int = Field(default=0, ge=0)
    checkpoint_hash: str = ""
    insufficient_clients: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class FLSimulationResult(BaseModel):
    """Immutable audit record for a completed federated learning run."""

    model_config = ConfigDict(extra="forbid")

    strategy_name: str
    dataset_name: str
    num_clients: int
    num_rounds: int
    local_epochs: int = 2
    partition_type: str = "iid"
    dirichlet_alpha: float | None = None
    seed: int = 13
    round_logs: list[RoundAuditLog]
    total_model_bytes: int = Field(default=0, ge=0)
    total_metadata_bytes: int = Field(default=0, ge=0)
    final_global_val_accuracy: float = 0.0
    final_global_val_loss: float = 0.0
    final_checkpoint_path: str = ""
    final_checkpoint_digest: str = ""
    extra_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
