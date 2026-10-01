"""Common interfaces and evaluation data models for baseline intrusion detection systems.

Adheres strictly to instructions/20_BASELINES_MASTER.md, 21_BASELINE_IMPLEMENTATION_DETAILS.md,
and 22_BASELINE_FIDELITY_PROTOCOL.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


class BaselineEvaluationResult(BaseModel):
    """Standardized evaluation report across all baseline architectures."""

    model_config = ConfigDict(extra="forbid")

    baseline_id: str = Field(..., description="Unique baseline identifier (e.g. B0, B1, B5)")
    baseline_name: str = Field(..., description="Human-readable baseline name")
    fidelity_tier: Literal[
        "official", "faithful_reimplementation", "approximate_reimplementation"
    ] = Field(
        ..., description="Fidelity tier according to instructions/22_BASELINE_FIDELITY_PROTOCOL.md"
    )
    num_samples_evaluated: int = Field(..., ge=0)
    accuracy: float = Field(..., ge=0.0, le=1.0)
    precision_macro: float = Field(..., ge=0.0, le=1.0)
    recall_macro: float = Field(..., ge=0.0, le=1.0)
    macro_f1: float = Field(..., ge=0.0, le=1.0)
    false_positive_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    inference_latency_ms: float = Field(default=0.0, ge=0.0)
    communication_bytes: int = Field(default=0, ge=0)
    notes: str = Field(default="", description="Implementation details or documented deviations")
    per_class_f1: dict[str, float] = Field(default_factory=dict)


def compute_standard_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    label_names: list[str] | None = None,
    benign_class_idx: int = 0,
) -> dict[str, Any]:
    """Compute standardized classification metrics across all baselines.

    Args:
        y_true: Ground truth integer labels
        y_pred: Predicted integer labels
        label_names: Optional mapping from index to class name
        benign_class_idx: Class index corresponding to normal/benign traffic

    Returns:
        Dictionary with accuracy, precision_macro, recall_macro, macro_f1, false_positive_rate, and per_class_f1
    """
    y_t = np.asarray(y_true, dtype=np.int64)
    y_p = np.asarray(y_pred, dtype=np.int64)

    acc = float(accuracy_score(y_t, y_p))
    prec = float(precision_score(y_t, y_p, average="macro", zero_division=0))
    rec = float(recall_score(y_t, y_p, average="macro", zero_division=0))
    f1 = float(f1_score(y_t, y_p, average="macro", zero_division=0))

    # Compute False Positive Rate: Benign classified as Attack / Total Benign
    benign_mask = y_t == benign_class_idx
    total_benign = int(np.sum(benign_mask))
    if total_benign > 0:
        false_positives = int(np.sum((y_t == benign_class_idx) & (y_p != benign_class_idx)))
        fpr = float(false_positives / total_benign)
    else:
        fpr = 0.0

    # Per-class F1
    unique_classes = np.unique(np.concatenate([y_t, y_p]))
    per_class_scores = f1_score(y_t, y_p, average=None, zero_division=0)
    per_class_f1: dict[str, float] = {}
    for idx, c in enumerate(unique_classes):
        c_name = label_names[int(c)] if label_names and int(c) < len(label_names) else f"class_{c}"
        per_class_f1[c_name] = round(float(per_class_scores[idx]), 4)

    return {
        "accuracy": round(acc, 4),
        "precision_macro": round(prec, 4),
        "recall_macro": round(rec, 4),
        "macro_f1": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "per_class_f1": per_class_f1,
    }


class BaseBaseline(ABC):
    """Abstract base class for all benchmark baselines."""

    def __init__(self, baseline_id: str, baseline_name: str) -> None:
        self.baseline_id = baseline_id
        self.baseline_name = baseline_name

    @abstractmethod
    def fit(self, train_data: Any, **kwargs: Any) -> Any:
        """Train or fit baseline model."""
        pass

    @abstractmethod
    def predict(self, x: np.ndarray) -> np.ndarray:
        """Generate class predictions for input samples."""
        pass

    @abstractmethod
    def evaluate(
        self,
        x_test: np.ndarray,
        y_test: np.ndarray,
        label_names: list[str] | None = None,
    ) -> BaselineEvaluationResult:
        """Evaluate baseline on test dataset and return standardized metrics."""
        pass
