"""Schemas and manifests for adversarial attacks and threat model evaluation.

Adheres strictly to instructions/18_ATTACKS_AND_THREAT_MODEL.md:
"Every attack requires:
 1. transformation unit test;
 2. positive control demonstrating attack effect where feasible;
 3. defense test;
 4. immutable attack config;
 5. saved malicious-client/item manifest."
"""

from __future__ import annotations

import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AttackManifest(BaseModel):
    """Immutable audit manifest for a configured adversarial attack instantiation."""

    model_config = ConfigDict(extra="forbid")

    attack_id: str = Field(..., description="Unique attack run identifier")
    attack_type: Literal[
        "targeted_label_flipping",
        "untargeted_label_flipping",
        "sign_flipping",
        "model_replacement",
        "tabular_backdoor",
        "provenance_tampering",
        "replay_nonce",
        "stale_round",
        "unauthorized_identity",
        "knowledge_tampering",
        "unauthorized_knowledge_insertion",
        "prompt_injection",
        "dos_rag_amplification",
    ] = Field(..., description="Categorical threat model classification")
    source_class: int | None = Field(
        default=None, description="Source class index for targeted attacks"
    )
    target_class: int | None = Field(
        default=None, description="Target class index for targeted attacks"
    )
    poison_fraction: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Fraction of samples or clients poisoned"
    )
    malicious_client_ids: list[str] = Field(
        default_factory=list, description="IDs of adversarial clients"
    )
    total_poisoned_samples: int = Field(
        default=0, ge=0, description="Total number of modified data points"
    )
    config_hash: str = Field(..., description="SHA-256 digest of immutable attack parameters")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Attack-specific configuration parameters"
    )
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class AttackEvaluationReport(BaseModel):
    """Standardized metrics reporting attack impact and defense efficacy."""

    model_config = ConfigDict(extra="forbid")

    attack_id: str
    attack_type: str
    defense_strategy: str
    clean_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Accuracy on unperturbed clean test set"
    )
    attacked_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Overall accuracy under attack"
    )
    attack_success_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="ASR: Fraction of targeted samples misclassified to target class",
    )
    attack_mitigated: bool = Field(
        ..., description="Whether defense successfully thwarted the attack"
    )
    num_samples_evaluated: int = Field(..., ge=0)
    latency_overhead_ms: float = Field(default=0.0, ge=0.0)
    extra_metrics: dict[str, Any] = Field(default_factory=dict)
    notes: str = Field(default="")
