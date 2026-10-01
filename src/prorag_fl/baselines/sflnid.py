"""B5 — SFLNID Baseline.

"Efficient and Privacy-Preserving Network Intrusion Detection Based on Federated Learning in SDN-Enabled IIoT Network"
IEEE Internet of Things Journal, 2025. DOI: 10.1109/JIOT.2025.3591598.

Implements faithful reimplementation:
- SFLNIDModel: CNN-GRU hybrid network capturing spatial and temporal traffic correlations.
- SFLNIDLoss: Focal loss combined with Wasserstein-distance local/global regularization.
- AdaptiveDPController: Dynamic gradient clipping using Holt exponential smoothing with calibrated noise.
- SFLNIDBaseline: Federated training and evaluation coordinator.

Adheres strictly to instructions/20_BASELINES_MASTER.md and 21_BASELINE_IMPLEMENTATION_DETAILS.md.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from prorag_fl.baselines.common import (
    BaseBaseline,
    BaselineEvaluationResult,
    compute_standard_metrics,
)


class SFLNIDModel(nn.Module):
    """Native CNN-GRU architecture for SFLNID."""

    def __init__(
        self,
        num_features: int,
        num_classes: int,
        conv_channels: int = 64,
        gru_hidden_size: int = 64,
        num_gru_layers: int = 1,
        dropout_rate: float = 0.2,
    ) -> None:
        super().__init__()
        self.conv1 = nn.Conv1d(1, conv_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(conv_channels)
        self.conv2 = nn.Conv1d(conv_channels, conv_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(conv_channels)
        self.pool = nn.MaxPool1d(2)

        # GRU expects [batch, seq_len, input_size]
        self.gru = nn.GRU(
            input_size=conv_channels,
            hidden_size=gru_hidden_size,
            num_layers=num_gru_layers,
            batch_first=True,
            dropout=dropout_rate if num_gru_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout_rate)
        self.fc = nn.Linear(gru_hidden_size, num_classes)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract bottleneck feature representations for Wasserstein regularization."""
        if x.dim() == 2:
            x = x.unsqueeze(1)
        h = F.relu(self.bn1(self.conv1(x)))
        h = F.relu(self.bn2(self.conv2(h)))
        h = self.pool(h)  # [batch, channels, length]
        h = h.permute(0, 2, 1)  # [batch, seq_len, channels]
        out, _ = self.gru(h)
        return out[:, -1, :]  # Last hidden state [batch, hidden_dim]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.extract_features(x)
        feat = self.dropout(feat)
        return self.fc(feat)


class SFLNIDLoss(nn.Module):
    """Focal loss with Wasserstein regularization between local and global representations."""

    def __init__(
        self,
        gamma: float = 2.0,
        alpha: float | None = None,
        wasserstein_weight: float = 0.05,
    ) -> None:
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha
        self.wasserstein_weight = wasserstein_weight

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
        local_features: torch.Tensor | None = None,
        global_features: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute composite SFLNID loss."""
        # 1. Focal Loss
        ce_loss = F.cross_entropy(logits, targets, reduction="none")
        pt = torch.exp(-ce_loss)
        focal_loss = ((1.0 - pt) ** self.gamma) * ce_loss
        if self.alpha is not None:
            focal_loss = self.alpha * focal_loss
        total_loss = focal_loss.mean()

        # 2. Wasserstein distance approximation between local and global feature distributions
        if (
            self.wasserstein_weight > 0.0
            and local_features is not None
            and global_features is not None
            and len(local_features) > 1
            and len(global_features) > 1
        ):
            mu_local = local_features.mean(dim=0)
            mu_global = global_features.mean(dim=0)
            mean_dist = torch.norm(mu_local - mu_global, p=2)

            std_local = local_features.std(dim=0)
            std_global = global_features.std(dim=0)
            std_dist = torch.norm(std_local - std_global, p=2)

            w_dist = mean_dist + std_dist
            total_loss = total_loss + self.wasserstein_weight * w_dist

        return total_loss


class AdaptiveDPController:
    """Dynamic gradient clipping using Holt exponential smoothing with calibrated noise."""

    def __init__(
        self,
        alpha_holt: float = 0.3,
        beta_holt: float = 0.1,
        initial_clip: float = 1.0,
        noise_multiplier: float = 0.01,
    ) -> None:
        self.alpha = alpha_holt
        self.beta = beta_holt
        self.noise_multiplier = noise_multiplier

        self.s_t = initial_clip
        self.b_t = 0.0
        self.current_clip = initial_clip

    def update_clipping_threshold(self, observed_norm: float) -> float:
        """Update Holt smoothing state and determine next dynamic clipping threshold."""
        prev_s = self.s_t
        self.s_t = self.alpha * observed_norm + (1.0 - self.alpha) * (self.s_t + self.b_t)
        self.b_t = self.beta * (self.s_t - prev_s) + (1.0 - self.beta) * self.b_t
        self.current_clip = max(0.1, float(self.s_t + self.b_t))
        return self.current_clip

    def clip_and_add_noise(self, model: nn.Module) -> float:
        """Clip gradients dynamically and add differential privacy noise."""
        total_norm = 0.0
        for p in model.parameters():
            if p.grad is not None:
                param_norm = p.grad.data.norm(2)
                total_norm += param_norm.item() ** 2
        total_norm = float(np.sqrt(total_norm))

        clip_c = self.update_clipping_threshold(total_norm)

        # Clip
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=clip_c)

        # Add DP noise
        if self.noise_multiplier > 0.0:
            sigma = self.noise_multiplier * clip_c
            for p in model.parameters():
                if p.grad is not None:
                    noise = torch.randn_like(p.grad.data) * sigma
                    p.grad.data.add_(noise)

        return total_norm


class SFLNIDBaseline(BaseBaseline):
    """B5: SFLNID federated intrusion detection baseline."""

    def __init__(
        self,
        num_features: int,
        num_classes: int,
        num_rounds: int = 5,
        local_epochs: int = 2,
        batch_size: int = 128,
        learning_rate: float = 1e-3,
        wasserstein_weight: float = 0.05,
        dp_noise_multiplier: float = 0.01,
        device: str = "cpu",
    ) -> None:
        super().__init__(baseline_id="B5", baseline_name="SFLNID")
        self.num_features = num_features
        self.num_classes = num_classes
        self.num_rounds = num_rounds
        self.local_epochs = local_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.wasserstein_weight = wasserstein_weight
        self.dp_noise_multiplier = dp_noise_multiplier
        self.device = device

        self.global_model = SFLNIDModel(
            num_features=num_features,
            num_classes=num_classes,
        ).to(device)

        self.dp_controller = AdaptiveDPController(
            noise_multiplier=dp_noise_multiplier,
        )

    def fit(
        self,
        client_partitions: dict[str, tuple[np.ndarray, np.ndarray]],
        **kwargs: Any,
    ) -> SFLNIDModel:
        """Run SFLNID federated training across clients."""
        loss_fn = SFLNIDLoss(wasserstein_weight=self.wasserstein_weight)

        for _ in range(self.num_rounds):
            local_weights: list[dict[str, torch.Tensor]] = []
            sample_counts: list[int] = []

            # Global reference features
            global_ref_feats = None
            sample_client = next(iter(client_partitions.values()))
            with torch.no_grad():
                self.global_model.eval()
                sample_x = torch.tensor(
                    sample_client[0][: min(64, len(sample_client[0]))], dtype=torch.float32
                ).to(self.device)
                global_ref_feats = self.global_model.extract_features(sample_x)

            for _, (x_cl, y_cl) in client_partitions.items():
                if len(x_cl) == 0:
                    continue

                local_model = SFLNIDModel(
                    num_features=self.num_features,
                    num_classes=self.num_classes,
                ).to(self.device)
                local_model.load_state_dict(self.global_model.state_dict())
                local_model.train()

                optimizer = torch.optim.Adam(local_model.parameters(), lr=self.learning_rate)
                dataset = TensorDataset(
                    torch.tensor(x_cl, dtype=torch.float32),
                    torch.tensor(y_cl, dtype=torch.long),
                )
                loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

                for _ in range(self.local_epochs):
                    for bx, by in loader:
                        bx, by = bx.to(self.device), by.to(self.device)
                        optimizer.zero_grad()
                        feats = local_model.extract_features(bx)
                        logits = local_model.fc(local_model.dropout(feats))
                        loss = loss_fn(
                            logits=logits,
                            targets=by,
                            local_features=feats,
                            global_features=global_ref_feats,
                        )
                        loss.backward()

                        # Dynamic Holt clipping & DP noise
                        self.dp_controller.clip_and_add_noise(local_model)
                        optimizer.step()

                local_weights.append({k: v.cpu() for k, v in local_model.state_dict().items()})
                sample_counts.append(len(x_cl))

            # Aggregate
            if local_weights:
                total_samples = sum(sample_counts)
                agg_dict = {}
                for k in local_weights[0].keys():
                    agg_dict[k] = sum(
                        (w[k] * (sample_counts[i] / total_samples))
                        for i, w in enumerate(local_weights)
                    )
                self.global_model.load_state_dict(agg_dict)

        return self.global_model

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Classify test instances."""
        self.global_model.eval()
        with torch.no_grad():
            xt = torch.tensor(x, dtype=torch.float32).to(self.device)
            logits = self.global_model(xt)
            preds = torch.argmax(logits, dim=1).cpu().numpy()
        return preds

    def evaluate(
        self,
        x_test: np.ndarray,
        y_test: np.ndarray,
        label_names: list[str] | None = None,
    ) -> BaselineEvaluationResult:
        """Evaluate SFLNID baseline model."""
        t0 = time.perf_counter()
        y_pred = self.predict(x_test)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        metrics = compute_standard_metrics(y_test, y_pred, label_names=label_names)

        return BaselineEvaluationResult(
            baseline_id=self.baseline_id,
            baseline_name=self.baseline_name,
            fidelity_tier="faithful_reimplementation",
            num_samples_evaluated=len(x_test),
            accuracy=metrics["accuracy"],
            precision_macro=metrics["precision_macro"],
            recall_macro=metrics["recall_macro"],
            macro_f1=metrics["macro_f1"],
            false_positive_rate=metrics["false_positive_rate"],
            inference_latency_ms=round(latency_ms, 3),
            communication_bytes=0,
            notes="Faithful SFLNID: CNN-GRU, Focal Loss + Wasserstein regularization, Holt dynamic clipping DP",
            per_class_f1=metrics["per_class_f1"],
        )
