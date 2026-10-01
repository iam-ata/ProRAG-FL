"""B9 — LQB-IDS Baseline.

"An adaptive intrusion detection system for the internet of things using large language models and post-quantum-secure blockchain"
Computer Networks, 2026. DOI: 10.1016/j.comnet.2025.111819.

Implements approximate reimplementation:
- DCAEModel: Deep Convolutional Autoencoder for reconstruction error computation.
- DualSwitchController: Known-attack vs unknown-anomaly routing mechanism.
- CreditScoreManager: Adaptive credit scoring for edge participating nodes.
- LQBIDSBaseline: Adaptive dual-path detector.

Adheres strictly to instructions/20_BASELINES_MASTER.md and 21_BASELINE_IMPLEMENTATION_DETAILS.md.
Marked: approximate_reimplementation (literature comparator).
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from prorag_fl.baselines.common import (
    BaseBaseline,
    BaselineEvaluationResult,
    compute_standard_metrics,
)


class DCAEModel(nn.Module):
    """Deep Convolutional Autoencoder for reconstruction error baseline in LQB-IDS."""

    def __init__(self, num_features: int, bottleneck_dim: int = 16) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(num_features, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Linear(64, bottleneck_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Linear(64, num_features),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z = self.encoder(x)
        rec = self.decoder(z)
        return rec, z

    def compute_reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        rec, _ = self.forward(x)
        return torch.mean((x - rec) ** 2, dim=1)


class DualSwitchController:
    """Adaptive switch determining whether an event is a known pattern or unknown zero-day."""

    def __init__(self, error_threshold: float = 0.5) -> None:
        self.error_threshold = error_threshold

    def route(self, reconstruction_errors: np.ndarray) -> np.ndarray:
        """Returns boolean mask: True = Unknown anomaly (switch to LLM/expert), False = Known pattern."""
        return reconstruction_errors > self.error_threshold


class CreditScoreManager:
    """Maintains participant credit scores based on verification accuracy."""

    def __init__(self, initial_credit: float = 100.0, max_credit: float = 200.0) -> None:
        self.credit_scores: dict[str, float] = {}
        self.initial_credit = initial_credit
        self.max_credit = max_credit

    def get_credit(self, node_id: str) -> float:
        return self.credit_scores.get(node_id, self.initial_credit)

    def update_credit(self, node_id: str, is_accurate: bool) -> float:
        current = self.get_credit(node_id)
        if is_accurate:
            new_credit = min(self.max_credit, current + 1.0)
        else:
            new_credit = max(0.0, current - 5.0)
        self.credit_scores[node_id] = new_credit
        return new_credit


class LQBIDSBaseline(BaseBaseline):
    """B9: LQB-IDS adaptive dual-switch intrusion detection baseline."""

    def __init__(
        self,
        num_features: int,
        num_classes: int,
        reconstruction_threshold: float = 0.5,
        device: str = "cpu",
    ) -> None:
        super().__init__(baseline_id="B9", baseline_name="LQB-IDS")
        self.num_features = num_features
        self.num_classes = num_classes
        self.device = device

        self.dcae = DCAEModel(num_features=num_features).to(device)
        self.known_classifier = nn.Linear(num_features, num_classes).to(device)
        self.dual_switch = DualSwitchController(error_threshold=reconstruction_threshold)
        self.credit_manager = CreditScoreManager()

    def fit(self, train_data: tuple[np.ndarray, np.ndarray], **kwargs: Any) -> None:
        """Fit DCAE autoencoder and known pattern classifier."""
        x_tr, y_tr = train_data
        optimizer_ae = torch.optim.Adam(self.dcae.parameters(), lr=1e-3)
        optimizer_clf = torch.optim.Adam(self.known_classifier.parameters(), lr=1e-3)

        ds = torch.utils.data.TensorDataset(
            torch.tensor(x_tr, dtype=torch.float32),
            torch.tensor(y_tr, dtype=torch.long),
        )
        loader = torch.utils.data.DataLoader(ds, batch_size=128, shuffle=True)

        self.dcae.train()
        self.known_classifier.train()

        for _ in range(3):
            for bx, by in loader:
                bx, by = bx.to(self.device), by.to(self.device)

                # 1. Train DCAE
                optimizer_ae.zero_grad()
                rec, _ = self.dcae(bx)
                loss_ae = F.mse_loss(rec, bx)
                loss_ae.backward()
                optimizer_ae.step()

                # 2. Train Known Classifier
                optimizer_clf.zero_grad()
                logits = self.known_classifier(bx)
                loss_clf = F.cross_entropy(logits, by)
                loss_clf.backward()
                optimizer_clf.step()

        # Calibrate switch threshold on benign train reconstruction error (95th percentile)
        self.dcae.eval()
        with torch.no_grad():
            benign_x = x_tr[y_tr == 0][: min(500, np.sum(y_tr == 0))]
            if len(benign_x) > 0:
                bx_t = torch.tensor(benign_x, dtype=torch.float32).to(self.device)
                errs = self.dcae.compute_reconstruction_error(bx_t).cpu().numpy()
                self.dual_switch.error_threshold = float(np.percentile(errs, 95))

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Dual-switch prediction."""
        self.dcae.eval()
        self.known_classifier.eval()

        with torch.no_grad():
            xt = torch.tensor(x, dtype=torch.float32).to(self.device)
            errs = self.dcae.compute_reconstruction_error(xt).cpu().numpy()
            logits = self.known_classifier(xt)
            known_preds = torch.argmax(logits, dim=1).cpu().numpy()

        unknown_mask = self.dual_switch.route(errs)
        preds = np.copy(known_preds)
        # For unknown anomalies where error is huge and known classifier predicted benign (0),
        # LQB-IDS flags as anomaly/attack (default attack class index 1)
        for i in range(len(preds)):
            if unknown_mask[i] and preds[i] == 0:
                preds[i] = 1

        return preds

    def evaluate(
        self,
        x_test: np.ndarray,
        y_test: np.ndarray,
        label_names: list[str] | None = None,
    ) -> BaselineEvaluationResult:
        """Evaluate LQB-IDS baseline."""
        t0 = time.perf_counter()
        y_pred = self.predict(x_test)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        metrics = compute_standard_metrics(y_test, y_pred, label_names=label_names)

        return BaselineEvaluationResult(
            baseline_id=self.baseline_id,
            baseline_name=self.baseline_name,
            fidelity_tier="approximate_reimplementation",
            num_samples_evaluated=len(x_test),
            accuracy=metrics["accuracy"],
            precision_macro=metrics["precision_macro"],
            recall_macro=metrics["recall_macro"],
            macro_f1=metrics["macro_f1"],
            false_positive_rate=metrics["false_positive_rate"],
            inference_latency_ms=round(latency_ms, 3),
            communication_bytes=0,
            notes="Approximate LQB-IDS: DCAE dual-switch routing between known classifier and anomaly path",
            per_class_f1=metrics["per_class_f1"],
        )
