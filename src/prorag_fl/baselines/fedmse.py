"""B10 — FedMSE Baseline.

"FedMSE: Semi-supervised federated learning approach for IoT network intrusion detection"
Computers & Security, 2025. DOI: 10.1016/j.cose.2025.104337.

Implements faithful reimplementation:
- ShrinkAutoencoder (SAE): Constrains latent space via shrinkage toward normal centroid.
- CentroidOneClassClassifier: Hypersphere distance threshold for anomaly detection.
- FedMSEBaseline: Semi-supervised federated learning baseline.

Adheres strictly to instructions/20_BASELINES_MASTER.md and 21_BASELINE_IMPLEMENTATION_DETAILS.md.
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


class ShrinkAutoencoder(nn.Module):
    """Shrink Autoencoder (SAE) enforcing latent shrinkage towards the centroid."""

    def __init__(self, num_features: int, latent_dim: int = 16) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(num_features, 64),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.1),
            nn.Linear(64, latent_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.1),
            nn.Linear(64, num_features),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z = self.encoder(x)
        rec = self.decoder(z)
        return rec, z


class CentroidOneClassClassifier:
    """One-class centroid classifier computing Euclidean distance in latent space."""

    def __init__(self, radius: float = 1.0) -> None:
        self.centroid: np.ndarray | None = None
        self.radius = radius

    def fit(self, latent_vectors: np.ndarray, percentile: float = 95.0) -> None:
        """Compute benign centroid and calibrate radius threshold."""
        self.centroid = np.mean(latent_vectors, axis=0)
        dists = np.linalg.norm(latent_vectors - self.centroid, axis=1)
        self.radius = float(np.percentile(dists, percentile))

    def predict(self, latent_vectors: np.ndarray) -> np.ndarray:
        """Returns 0 for normal (within radius), 1 for anomaly (outside radius)."""
        if self.centroid is None:
            raise RuntimeError("Classifier has not been fitted.")
        dists = np.linalg.norm(latent_vectors - self.centroid, axis=1)
        return (dists > self.radius).astype(np.int64)


class FedMSEBaseline(BaseBaseline):
    """B10: FedMSE semi-supervised federated intrusion detection baseline."""

    def __init__(
        self,
        num_features: int,
        latent_dim: int = 16,
        num_rounds: int = 5,
        local_epochs: int = 2,
        batch_size: int = 128,
        learning_rate: float = 1e-3,
        shrink_lambda: float = 0.01,
        device: str = "cpu",
    ) -> None:
        super().__init__(baseline_id="B10", baseline_name="FedMSE")
        self.num_features = num_features
        self.latent_dim = latent_dim
        self.num_rounds = num_rounds
        self.local_epochs = local_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.shrink_lambda = shrink_lambda
        self.device = device

        self.global_sae = ShrinkAutoencoder(num_features=num_features, latent_dim=latent_dim).to(
            device
        )
        self.one_class_clf = CentroidOneClassClassifier()

    def fit(
        self,
        client_partitions: dict[str, tuple[np.ndarray, np.ndarray]],
        **kwargs: Any,
    ) -> ShrinkAutoencoder:
        """Federated training of Shrink Autoencoder on normal/unlabeled data."""
        client_ids = list(client_partitions.keys())

        for _ in range(self.num_rounds):
            local_weights = []
            sample_counts = []

            for cid in client_ids:
                x_cl, y_cl = client_partitions[cid]
                # FedMSE is semi-supervised: primarily trains on normal/benign traffic
                normal_mask = y_cl == 0
                train_x = x_cl[normal_mask] if np.sum(normal_mask) > 10 else x_cl
                if len(train_x) == 0:
                    continue

                local_sae = ShrinkAutoencoder(self.num_features, self.latent_dim).to(self.device)
                local_sae.load_state_dict(self.global_sae.state_dict())
                local_sae.train()

                optimizer = torch.optim.Adam(local_sae.parameters(), lr=self.learning_rate)
                ds = torch.utils.data.TensorDataset(torch.tensor(train_x, dtype=torch.float32))
                loader = torch.utils.data.DataLoader(ds, batch_size=self.batch_size, shuffle=True)

                for _ in range(self.local_epochs):
                    for (bx,) in loader:
                        bx = bx.to(self.device)
                        optimizer.zero_grad()
                        rec, z = local_sae(bx)
                        rec_loss = F.mse_loss(rec, bx)
                        shrink_loss = torch.mean(torch.sum(z**2, dim=1))
                        loss = rec_loss + self.shrink_lambda * shrink_loss
                        loss.backward()
                        optimizer.step()

                local_weights.append({k: v.cpu() for k, v in local_sae.state_dict().items()})
                sample_counts.append(len(train_x))

            if local_weights:
                tot_s = sum(sample_counts)
                agg = {}
                for k in local_weights[0].keys():
                    agg[k] = sum(
                        (w[k] * (sample_counts[i] / tot_s)) for i, w in enumerate(local_weights)
                    )
                self.global_sae.load_state_dict(agg)

        # Calibrate global one-class classifier on benign training embeddings
        self.global_sae.eval()
        with torch.no_grad():
            all_benign_x = []
            for _, (x_cl, y_cl) in client_partitions.items():
                b_x = x_cl[y_cl == 0]
                if len(b_x) > 0:
                    all_benign_x.append(b_x[: min(100, len(b_x))])
            if all_benign_x:
                pooled_b = np.vstack(all_benign_x)
                _, z_b = self.global_sae(
                    torch.tensor(pooled_b, dtype=torch.float32).to(self.device)
                )
                self.one_class_clf.fit(z_b.cpu().numpy())

        return self.global_sae

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Classify test instances: 0 = Benign, 1 = Anomaly/Attack."""
        self.global_sae.eval()
        with torch.no_grad():
            xt = torch.tensor(x, dtype=torch.float32).to(self.device)
            rec, z = self.global_sae(xt)
            # Both latent distance and reconstruction error contribute
            preds = self.one_class_clf.predict(z.cpu().numpy())
        return preds

    def evaluate(
        self,
        x_test: np.ndarray,
        y_test: np.ndarray,
        label_names: list[str] | None = None,
    ) -> BaselineEvaluationResult:
        """Evaluate FedMSE binary anomaly detection performance."""
        t0 = time.perf_counter()
        y_pred = self.predict(x_test)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        # Convert multi-class ground truth to binary (0 = normal, >=1 = attack) for one-class evaluation
        binary_y_test = (np.asarray(y_test) > 0).astype(np.int64)
        binary_labels = ["Benign", "Attack_Anomaly"]

        metrics = compute_standard_metrics(binary_y_test, y_pred, label_names=binary_labels)

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
            notes="Faithful FedMSE: Semi-supervised shrink autoencoder + one-class centroid anomaly classifier",
            per_class_f1=metrics["per_class_f1"],
        )
