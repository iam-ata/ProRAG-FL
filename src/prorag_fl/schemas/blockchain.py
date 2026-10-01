"""Pydantic schemas for Blockchain model update provenance records and transaction receipts."""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ModelUpdateRecord(BaseModel):
    """Immutable record stored on Hyperledger Fabric ledger capturing model update provenance."""

    model_config = ConfigDict(extra="forbid")

    update_id: str = Field(..., description="Unique deterministic identifier for the update record")
    client_id: str = Field(..., description="Unique client identifier (e.g. client_0)")
    round: int = Field(..., ge=0, description="Federated learning round number")
    global_model_version: str = Field(..., description="Global model version base (e.g. v0, v1)")
    update_sha256: str = Field(
        ..., description="SHA-256 digest of canonically serialized model update diff"
    )
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    nonce: str = Field(..., description="Unique single-use cryptographic nonce")
    status: str = Field(
        default="active", description="Lifecycle status: active, revoked, superseded"
    )
    submitter_identity: str = Field(
        default="Org1MSP/Peer1", description="MSP and peer identity of submitter"
    )
    signature: str = Field(default="", description="Cryptographic signature of payload")
    tx_id: str = Field(default="", description="Hyperledger Fabric transaction ID")
    block_number: int = Field(
        default=0, ge=0, description="Block height where transaction was committed"
    )
    num_examples: int = Field(default=0, ge=0, description="Number of local training samples")
    local_loss: float = Field(default=0.0, ge=0.0, description="Local training loss")
    local_accuracy: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Local training accuracy"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional provenance metadata"
    )


class ProvenanceTransactionReceipt(BaseModel):
    """Receipt returned by Hyperledger Fabric or mock ledger upon transaction commit."""

    model_config = ConfigDict(extra="forbid")

    tx_id: str = Field(..., description="Unique blockchain transaction hash")
    status: str = Field(
        ..., description="Transaction status: COMMITTED, REJECTED, DUPLICATE_NONCE, etc."
    )
    block_number: int = Field(default=0, ge=0, description="Block index")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    execution_time_ms: float = Field(
        default=0.0, ge=0.0, description="Commit and verification latency in milliseconds"
    )
    tx_bytes: int = Field(default=0, ge=0, description="Total serialized transaction size in bytes")
    details: str = Field(default="", description="Diagnostic message or rejection reason")


class ClientIdentityRecord(BaseModel):
    """Client identity and registration status in the blockchain ledger."""

    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., description="Unique client identifier")
    msp_id: str = Field(..., description="Membership Service Provider identity (e.g. Org1MSP)")
    is_authorized: bool = Field(
        default=True, description="Whether client is authorized to participate"
    )
    is_revoked: bool = Field(
        default=False, description="Whether client certificate/identity has been revoked"
    )
    revocation_reason: str = Field(default="", description="Reason for revocation if revoked")
    registered_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )


class LedgerStats(BaseModel):
    """Aggregated metrics and performance statistics for the blockchain ledger."""

    model_config = ConfigDict(extra="forbid")

    total_transactions: int = Field(default=0, ge=0)
    committed_transactions: int = Field(default=0, ge=0)
    rejected_transactions: int = Field(default=0, ge=0)
    block_height: int = Field(default=0, ge=0)
    total_ledger_bytes: int = Field(default=0, ge=0)
    avg_commit_latency_ms: float = Field(default=0.0, ge=0.0)
    avg_query_latency_ms: float = Field(default=0.0, ge=0.0)
    rejection_reasons: dict[str, int] = Field(default_factory=dict)
