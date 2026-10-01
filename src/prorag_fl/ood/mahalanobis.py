"""Class-conditional Mahalanobis OOD detector conforming to 11_CALIBRATION_AND_OOD.md."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.covariance import LedoitWolf

from prorag_fl.schemas.calibration import MahalanobisResult


class MahalanobisOODDetector:
    """Class-conditional Mahalanobis Out-of-Distribution detector.

    Computes distance in the 128-D latent embedding space:
        M(x) = min_c sqrt((h(x) - mu_c)^T Sigma^-1 (h(x) - mu_c))

    Uses Ledoit-Wolf optimal shrinkage estimation for the pooled covariance
    to guarantee numerical stability, positive definiteness, and well-conditioned precision.
    """

    def __init__(self, embedding_dim: int = 128) -> None:
        self.embedding_dim = embedding_dim
        self.class_means: dict[int, np.ndarray] = {}
        self.precision: np.ndarray | None = None
        self.covariance: np.ndarray | None = None
        self.tau_m: float = 10.0
        self.shrinkage_intensity: float = 0.0
        self.condition_number: float = 1.0
        self.is_fitted: bool = False
        self.last_result: MahalanobisResult | None = None

    def fit(
        self,
        train_embeddings: np.ndarray | torch.Tensor,
        train_labels: np.ndarray | torch.Tensor,
        shrinkage_method: str = "ledoit_wolf",
    ) -> MahalanobisResult:
        """Fit class-conditional means and pooled regularized precision matrix.

        Strict Rules:
            - Must be trained EXCLUSIVELY on training-known embeddings.
            - Never expose held-out classes during fitting.
        """
        if isinstance(train_embeddings, torch.Tensor):
            H = train_embeddings.detach().cpu().numpy().astype(np.float64)
        else:
            H = np.asarray(train_embeddings, dtype=np.float64)

        if isinstance(train_labels, torch.Tensor):
            Y = train_labels.detach().cpu().numpy().astype(np.int64)
        else:
            Y = np.asarray(train_labels, dtype=np.int64)

        if H.ndim != 2:
            raise ValueError(f"Expected 2D train_embeddings [N, D], got shape {H.shape}")
        if Y.ndim != 1:
            raise ValueError(f"Expected 1D train_labels [N], got shape {Y.shape}")
        if len(H) != len(Y):
            raise ValueError(f"Sample count mismatch: {len(H)} embeddings vs {len(Y)} labels")

        n_samples, d = H.shape
        self.embedding_dim = d

        # Step 1: Compute class-conditional means
        classes = np.unique(Y)
        self.class_means.clear()
        centered_embeddings = np.zeros_like(H)

        for c in classes:
            mask = Y == c
            c_samples = H[mask]
            mu_c = np.mean(c_samples, axis=0)
            self.class_means[int(c)] = mu_c
            centered_embeddings[mask] = c_samples - mu_c

        # Step 2: Estimate pooled regularized covariance using Ledoit-Wolf
        if shrinkage_method == "ledoit_wolf":
            lw = LedoitWolf(assume_centered=True)
            lw.fit(centered_embeddings)
            self.covariance = lw.covariance_
            self.precision = lw.precision_
            self.shrinkage_intensity = float(lw.shrinkage_)
        else:
            # Empirical covariance with trace shrinkage fallback
            emp_cov = np.dot(centered_embeddings.T, centered_embeddings) / n_samples
            alpha = 0.05
            reg_cov = (1.0 - alpha) * emp_cov + alpha * (np.trace(emp_cov) / d) * np.eye(d)
            self.covariance = reg_cov
            self.precision = np.linalg.pinv(reg_cov)
            self.shrinkage_intensity = alpha

        # Step 3: Check condition number and finiteness
        eigvals = np.linalg.eigvalsh(self.covariance)
        min_eig = max(float(eigvals[0]), 1e-12)
        max_eig = float(eigvals[-1])
        self.condition_number = max_eig / min_eig

        assert np.isfinite(self.precision).all(), "Non-finite precision matrix computed!"
        assert self.precision.shape == (d, d), f"Invalid precision shape: {self.precision.shape}"

        self.is_fitted = True

        result = MahalanobisResult(
            embedding_dimension=d,
            num_classes=len(classes),
            tau_m=self.tau_m,
            validation_quantile=0.95,
            shrinkage_method=shrinkage_method,
            shrinkage_intensity=self.shrinkage_intensity,
            covariance_condition_number=self.condition_number,
            num_train_samples=n_samples,
            num_val_samples=0,
        )
        self.last_result = result
        return result

    def compute_distance(self, embeddings: np.ndarray | torch.Tensor) -> np.ndarray:
        """Compute class-conditional Mahalanobis distance M(x) = min_c d(x, mu_c).

        Args:
            embeddings: Query latent embeddings [N, D].

        Returns:
            1D NumPy array of length N containing min Mahalanobis distance.
        """
        if not self.is_fitted or self.precision is None:
            raise RuntimeError("MahalanobisOODDetector must be fitted before computing distances.")

        if isinstance(embeddings, torch.Tensor):
            H = embeddings.detach().cpu().numpy().astype(np.float64)
        else:
            H = np.asarray(embeddings, dtype=np.float64)

        if H.ndim == 1:
            H = H.reshape(1, -1)

        N = H.shape[0]
        num_classes = len(self.class_means)
        all_class_distances = np.zeros((N, num_classes), dtype=np.float64)

        # Vectorized distance computation per class
        for idx, (_, mu_c) in enumerate(self.class_means.items()):
            delta = H - mu_c  # [N, D]
            # (delta @ precision) * delta summed over features
            dist_sq = np.sum(np.dot(delta, self.precision) * delta, axis=1)
            # Clip negative zeros from float inaccuracy
            dist_sq = np.maximum(dist_sq, 0.0)
            all_class_distances[:, idx] = np.sqrt(dist_sq)

        # Return minimum distance across all training classes
        min_distances = np.min(all_class_distances, axis=1)
        return min_distances

    def select_threshold(
        self,
        val_embeddings: np.ndarray | torch.Tensor,
        quantile: float = 0.95,
    ) -> float:
        """Select distance threshold tau_m strictly from validation-known embeddings.

        Never tune with held-out zero-day attack families.
        """
        distances = self.compute_distance(val_embeddings)
        self.tau_m = float(np.quantile(distances, quantile))
        if self.last_result is not None:
            self.last_result.tau_m = self.tau_m
            self.last_result.num_val_samples = len(distances)
            self.last_result.validation_quantile = quantile
        return self.tau_m

    def save(self, filepath: Path | str) -> Path:
        """Save fitted detector parameters to JSON."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload: dict[str, Any] = {
            "embedding_dim": self.embedding_dim,
            "tau_m": float(self.tau_m),
            "shrinkage_intensity": float(self.shrinkage_intensity),
            "condition_number": float(self.condition_number),
            "is_fitted": self.is_fitted,
            "class_means": {str(k): v.tolist() for k, v in self.class_means.items()},
            "precision": self.precision.tolist() if self.precision is not None else None,
            "covariance": self.covariance.tolist() if self.covariance is not None else None,
            "last_result": self.last_result.model_dump() if self.last_result else None,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def load(self, filepath: Path | str) -> MahalanobisOODDetector:
        """Load detector parameters from JSON."""
        path = Path(filepath)
        data = json.loads(path.read_text(encoding="utf-8"))

        self.embedding_dim = int(data["embedding_dim"])
        self.tau_m = float(data["tau_m"])
        self.shrinkage_intensity = float(data["shrinkage_intensity"])
        self.condition_number = float(data["condition_number"])
        self.is_fitted = bool(data.get("is_fitted", True))

        self.class_means = {
            int(k): np.array(v, dtype=np.float64) for k, v in data["class_means"].items()
        }
        self.precision = (
            np.array(data["precision"], dtype=np.float64) if data.get("precision") else None
        )
        self.covariance = (
            np.array(data["covariance"], dtype=np.float64) if data.get("covariance") else None
        )

        if data.get("last_result"):
            self.last_result = MahalanobisResult.model_validate(data["last_result"])

        return self
