"""Temperature scaling calibration module conforming to 11_CALIBRATION_AND_OOD.md."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from prorag_fl.schemas.calibration import CalibrationResult


def compute_ece(probs: torch.Tensor, labels: torch.Tensor, n_bins: int = 15) -> float:
    """Compute Expected Calibration Error (ECE) with equal-width confidence bins.

    Formula:
        ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    if probs.numel() == 0 or labels.numel() == 0:
        return 0.0

    confidences, predictions = torch.max(probs, dim=1)
    accuracies = predictions.eq(labels)

    bin_boundaries = torch.linspace(0, 1, n_bins + 1, device=probs.device)
    ece = torch.zeros(1, device=probs.device)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        if i == n_bins - 1:
            in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
        else:
            in_bin = (confidences >= bin_lower) & (confidences < bin_upper)

        bin_size = in_bin.sum().item()
        if bin_size > 0:
            bin_acc = accuracies[in_bin].float().mean()
            bin_conf = confidences[in_bin].mean()
            ece += (bin_size / len(labels)) * torch.abs(bin_acc - bin_conf)

    return float(ece.item())


def compute_brier_score(probs: torch.Tensor, labels: torch.Tensor) -> float:
    """Compute multi-class Brier score: mean squared difference from one-hot target."""
    num_classes = probs.size(1)
    one_hot = F.one_hot(labels, num_classes=num_classes).float()
    return float(torch.mean(torch.sum((probs - one_hot) ** 2, dim=1)).item())


def compute_nll(logits: torch.Tensor, labels: torch.Tensor) -> float:
    """Compute Negative Log-Likelihood (cross-entropy) on given logits."""
    return float(F.cross_entropy(logits, labels).item())


class TemperatureScaler(nn.Module):
    """Post-hoc confidence calibration via scalar Temperature Scaling.

    Freezes the underlying IDS model and optimizes a strictly positive scalar T:
        P_T(y|x) = softmax(z(x) / T)
        C(x) = max_y P_T(y|x)

    Positive Parameterization:
        T = softplus(raw_temperature) + eps
    guaranteeing T > 0 unconditionally.
    """

    def __init__(self, eps: float = 1e-4) -> None:
        super().__init__()
        self.eps = eps
        # Initialize raw_temperature such that softplus(0.5413) + 1e-4 ≈ 1.000
        self.raw_temperature = nn.Parameter(torch.tensor([0.5413], dtype=torch.float32))
        self.tau_c: float = 0.50
        self.is_fitted: bool = False
        self.last_result: CalibrationResult | None = None

    @property
    def temperature(self) -> torch.Tensor:
        """Strictly positive scalar temperature T > 0."""
        return F.softplus(self.raw_temperature) + self.eps

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        """Scale logits by temperature."""
        return logits / self.temperature

    def predict_proba(self, logits: torch.Tensor) -> torch.Tensor:
        """Return calibrated, normalized probabilities."""
        scaled = self.forward(logits)
        return F.softmax(scaled, dim=-1)

    def predict_confidence(self, logits: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Return max calibrated confidence C(x) and predicted class ID."""
        probs = self.predict_proba(logits)
        return torch.max(probs, dim=-1)

    def fit(
        self,
        val_logits: torch.Tensor,
        val_labels: torch.Tensor,
        max_iter: int = 50,
        lr: float = 0.05,
        target_recall: float = 0.95,
    ) -> CalibrationResult:
        """Fit temperature T strictly on validation logits and labels.

        Args:
            val_logits: Logits from the validation split [N, C].
            val_labels: True class labels from the validation split [N].
            max_iter: Max optimization iterations.
            lr: Learning rate for L-BFGS.
            target_recall: Target recall for selecting tau_c from validation.
        """
        if val_logits.dim() != 2:
            raise ValueError(f"Expected 2D val_logits [N, C], got {list(val_logits.shape)}")
        if val_labels.dim() != 1:
            raise ValueError(f"Expected 1D val_labels [N], got {list(val_labels.shape)}")
        if len(val_logits) != len(val_labels):
            raise ValueError(
                f"Sample count mismatch: {len(val_logits)} logits vs {len(val_labels)} labels"
            )

        device = val_logits.device
        self.to(device)

        # Baseline uncalibrated metrics
        with torch.no_grad():
            nll_before = compute_nll(val_logits, val_labels)
            probs_before = F.softmax(val_logits, dim=-1)
            ece_before = compute_ece(probs_before, val_labels)
            brier_before = compute_brier_score(probs_before, val_labels)

        # Optimize temperature using L-BFGS
        nll_criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.LBFGS([self.raw_temperature], lr=lr, max_iter=max_iter)

        def eval_loss() -> torch.Tensor:
            optimizer.zero_grad()
            scaled = val_logits / self.temperature
            loss = nll_criterion(scaled, val_labels)
            loss.backward()
            return loss

        optimizer.step(eval_loss)

        # Calibrated metrics
        with torch.no_grad():
            scaled_logits = self.forward(val_logits)
            nll_after = compute_nll(scaled_logits, val_labels)
            probs_after = self.predict_proba(val_logits)
            ece_after = compute_ece(probs_after, val_labels)
            brier_after = compute_brier_score(probs_after, val_labels)

            # Select tau_c from validation correct predictions
            confs_after, preds_after = torch.max(probs_after, dim=-1)
            correct_mask = preds_after.eq(val_labels)

            if correct_mask.sum() > 0:
                correct_confs = confs_after[correct_mask].cpu().numpy()
                tau_c_val = float(np.quantile(correct_confs, max(0.0, 1.0 - target_recall)))
            else:
                tau_c_val = 0.50

            self.tau_c = tau_c_val
            self.is_fitted = True

        result = CalibrationResult(
            temperature=float(self.temperature.item()),
            nll_before=float(nll_before),
            nll_after=float(nll_after),
            ece_before=float(ece_before),
            ece_after=float(ece_after),
            brier_before=float(brier_before),
            brier_after=float(brier_after),
            tau_c=float(self.tau_c),
            target_recall=float(target_recall),
            num_val_samples=len(val_labels),
            optimizer="L-BFGS",
        )
        self.last_result = result
        return result

    def save(self, filepath: Path | str) -> Path:
        """Save calibrated parameters and metadata to JSON."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload: dict[str, Any] = {
            "raw_temperature": float(self.raw_temperature.item()),
            "temperature": float(self.temperature.item()),
            "tau_c": float(self.tau_c),
            "is_fitted": self.is_fitted,
            "calibration_result": self.last_result.model_dump() if self.last_result else None,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def load(self, filepath: Path | str) -> TemperatureScaler:
        """Load calibrated parameters and threshold from JSON."""
        path = Path(filepath)
        data = json.loads(path.read_text(encoding="utf-8"))

        with torch.no_grad():
            self.raw_temperature.copy_(torch.tensor([data["raw_temperature"]], dtype=torch.float32))
        self.tau_c = float(data["tau_c"])
        self.is_fitted = bool(data.get("is_fitted", True))
        if data.get("calibration_result"):
            self.last_result = CalibrationResult.model_validate(data["calibration_result"])

        return self
