"""Pydantic schemas for Phase 3 confidence calibration, Mahalanobis OOD, and dual escalation gate."""

from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CalibrationResult(BaseModel):
    """Immutable audit artifact for temperature scaling calibration."""

    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(..., gt=0.0, description="Optimal scalar temperature T > 0")
    nll_before: float = Field(
        ..., ge=0.0, description="Validation negative log-likelihood before scaling"
    )
    nll_after: float = Field(
        ..., ge=0.0, description="Validation negative log-likelihood after scaling"
    )
    ece_before: float = Field(
        ..., ge=0.0, le=1.0, description="Expected calibration error before scaling"
    )
    ece_after: float = Field(
        ..., ge=0.0, le=1.0, description="Expected calibration error after scaling"
    )
    brier_before: float = Field(..., ge=0.0, description="Brier score before scaling")
    brier_after: float = Field(..., ge=0.0, description="Brier score after scaling")
    tau_c: float = Field(
        ..., ge=0.0, le=1.0, description="Calibrated confidence threshold selected from validation"
    )
    target_recall: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Target validation known-class direct recall"
    )
    num_val_samples: int = Field(..., gt=0)
    optimizer: str = Field(default="L-BFGS")
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class MahalanobisResult(BaseModel):
    """Immutable audit artifact for class-conditional Mahalanobis OOD detector."""

    model_config = ConfigDict(extra="forbid")

    embedding_dimension: int = Field(default=128, description="Latent embedding dimension")
    num_classes: int = Field(..., gt=0, description="Number of known training classes")
    tau_m: float = Field(
        ..., ge=0.0, description="Mahalanobis distance threshold selected from validation"
    )
    validation_quantile: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Quantile of validation known samples"
    )
    shrinkage_method: str = Field(default="ledoit_wolf", description="Covariance shrinkage method")
    shrinkage_intensity: float = Field(
        ..., ge=0.0, le=1.0, description="Estimated shrinkage parameter"
    )
    covariance_condition_number: float = Field(
        ..., ge=1.0, description="Condition number of regularized covariance"
    )
    num_train_samples: int = Field(..., gt=0)
    num_val_samples: int = Field(default=0, ge=0)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class GateThresholds(BaseModel):
    """Serialized dual gate routing thresholds."""

    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    tau_c: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence threshold (escalate if C < tau_c)"
    )
    tau_m: float = Field(
        ..., ge=0.0, description="Mahalanobis distance threshold (escalate if M > tau_m)"
    )
    temperature: float = Field(..., gt=0.0)
    target_direct_recall: float = 0.95
    model_checkpoint_digest: str = ""
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class GateDecision(BaseModel):
    """Routing decision for an individual network flow event."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default="")
    escalate: bool = Field(
        ..., description="True -> invoke RAG/LLM path; False -> direct IDS decision"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Calibrated max softmax probability C(x)"
    )
    mahalanobis_distance: float = Field(
        ..., ge=0.0, description="Distance to closest training class center M(x)"
    )
    predicted_class_id: int = Field(..., ge=0)
    predicted_class_name: str
    reason: Literal["direct", "low_confidence", "high_mahalanobis", "both"] = Field(...)


class GateEvaluationMetrics(BaseModel):
    """Comprehensive performance metrics evaluating the escalation gate."""

    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    num_known_samples: int = Field(..., ge=0)
    num_held_out_samples: int = Field(..., ge=0)

    # Known traffic performance
    direct_route_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of known samples routed directly (G=0)"
    )
    false_escalation_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of known samples escalated (G=1)"
    )
    direct_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Accuracy of decisions routed directly"
    )
    direct_macro_f1: float = Field(
        ..., ge=0.0, le=1.0, description="Macro F1 on directly routed decisions"
    )

    # Held-out zero-day performance
    held_out_escalation_recall: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of held-out zero-day attacks escalated (G=1)"
    )

    # Discrimination metrics
    mahalanobis_auroc: float | None = Field(
        default=None, description="AUROC using Mahalanobis distance as anomaly score"
    )
    mahalanobis_aupr: float | None = Field(
        default=None, description="AUPR using Mahalanobis distance as anomaly score"
    )
    confidence_auroc: float | None = Field(
        default=None, description="AUROC using (1 - Confidence) as anomaly score"
    )
