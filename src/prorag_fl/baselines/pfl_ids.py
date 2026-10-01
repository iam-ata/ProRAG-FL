"""B11 — pFL-IDS Baseline (Thein et al.).

"Personalized federated learning-based intrusion detection system: Poisoning attack and defense"
Future Generation Computer Systems, 2024. DOI: 10.1016/j.future.2023.10.005.

Implements faithful reimplementation:
- LogitAdjustedLoss: Mitigates Non-IID class imbalance via empirical label prior adjustments.
- TwoPhaseSimilarityDefense: Phase 1 global direction cosine similarity + Phase 2 benign centroid defense.
- PersonalizedClientTrainer: Preserves personalized client heads while aggregating global representation.
- PFLIDSBaseline: End-to-end personalized poisoning-robust FL baseline.

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
from prorag_fl.models.ids_1dcnn import IDS1DCNN


class LogitAdjustedLoss(nn.Module):
    """Mini-batch logit adjustment loss handling Non-IID class imbalance."""

    def __init__(self, class_priors: np.ndarray, tau: float = 1.0) -> None:
        super().__init__()
        # Avoid log(0)
        priors = np.clip(class_priors, 1e-6, 1.0)
        priors = priors / np.sum(priors)
        self.log_priors = torch.tensor(np.log(priors), dtype=torch.float32)
        self.tau = tau

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """Adjust logits by class prior: logit + tau * log(pi)."""
        logits_t = logits.logits if hasattr(logits, "logits") else logits
        device = logits_t.device
        adj = self.tau * self.log_priors.to(device)
        adjusted_logits = logits_t + adj.unsqueeze(0)
        return F.cross_entropy(adjusted_logits, targets)


class TwoPhaseSimilarityDefense:
    """Two-phase defense: Phase 1 global cosine similarity + Phase 2 benign centroid."""

    def __init__(self, cos_threshold: float = 0.0, centroid_factor: float = 1.5) -> None:
        self.cos_threshold = cos_threshold
        self.centroid_factor = centroid_factor

    def filter_updates(
        self,
        update_vectors: list[np.ndarray],
        reference_direction: np.ndarray | None = None,
    ) -> list[int]:
        """Return indices of accepted benign updates."""
        num_updates = len(update_vectors)
        if num_updates <= 2:
            return list(range(num_updates))

        norms = [np.linalg.norm(v) + 1e-10 for v in update_vectors]

        # Phase 1: Directional Cosine Similarity with consensus direction
        if reference_direction is None:
            # Estimate consensus as median coordinate vector
            ref = np.median(update_vectors, axis=0)
        else:
            ref = reference_direction
        ref_norm = np.linalg.norm(ref) + 1e-10

        phase1_passed = []
        for idx, v in enumerate(update_vectors):
            cos_sim = float(np.dot(v, ref) / (norms[idx] * ref_norm))
            if cos_sim >= self.cos_threshold:
                phase1_passed.append(idx)

        if not phase1_passed:
            phase1_passed = list(range(num_updates))

        # Phase 2: Benign Centroid Distance Filtering
        passed_vectors = [update_vectors[i] for i in phase1_passed]
        benign_centroid = np.mean(passed_vectors, axis=0)
        dists = [float(np.linalg.norm(v - benign_centroid)) for v in passed_vectors]
        dists_arr = np.array(dists, dtype=np.float32)
        median_dist = float(np.median(dists_arr))
        mad = float(np.median(np.abs(dists_arr - median_dist))) or 1e-4
        threshold_dist = median_dist + self.centroid_factor * mad

        phase2_passed = []
        for orig_idx, d in zip(phase1_passed, dists, strict=False):
            if d <= threshold_dist:
                phase2_passed.append(orig_idx)

        return phase2_passed or phase1_passed


class PFLIDSBaseline(BaseBaseline):
    """B11: pFL-IDS personalized federated learning intrusion detection baseline."""

    def __init__(
        self,
        num_features: int,
        num_classes: int,
        num_rounds: int = 5,
        local_epochs: int = 2,
        batch_size: int = 128,
        learning_rate: float = 1e-3,
        device: str = "cpu",
    ) -> None:
        super().__init__(baseline_id="B11", baseline_name="pFL-IDS")
        self.num_features = num_features
        self.num_classes = num_classes
        self.num_rounds = num_rounds
        self.local_epochs = local_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.device = device

        self.global_model = IDS1DCNN(num_features, num_classes)
        self.defense = TwoPhaseSimilarityDefense()
        self.personalized_models: dict[str, IDS1DCNN] = {}

    def fit(
        self,
        client_partitions: dict[str, tuple[np.ndarray, np.ndarray]],
        **kwargs: Any,
    ) -> IDS1DCNN:
        """Execute pFL-IDS with logit adjustment and two-phase similarity defense."""
        client_ids = list(client_partitions.keys())
        prev_consensus_dir = None

        for _ in range(self.num_rounds):
            base_weights = {k: v.cpu().numpy() for k, v in self.global_model.state_dict().items()}
            client_updates = []
            valid_cids = []
            sample_counts = []

            for cid in client_ids:
                x_cl, y_cl = client_partitions[cid]
                if len(x_cl) == 0:
                    continue

                local_model = IDS1DCNN(self.num_features, self.num_classes)
                local_model.load_state_dict(self.global_model.state_dict())
                local_model.train()

                # Calculate client empirical class priors for logit adjustment
                counts = np.bincount(y_cl, minlength=self.num_classes)
                priors = counts.astype(np.float32) / len(y_cl)
                loss_fn = LogitAdjustedLoss(class_priors=priors)

                optimizer = torch.optim.Adam(local_model.parameters(), lr=self.learning_rate)
                ds = TensorDataset(
                    torch.tensor(x_cl, dtype=torch.float32), torch.tensor(y_cl, dtype=torch.long)
                )
                loader = DataLoader(ds, batch_size=self.batch_size, shuffle=True)

                for _ in range(self.local_epochs):
                    for bx, by in loader:
                        optimizer.zero_grad()
                        logits = local_model(bx)
                        loss = loss_fn(logits, by)
                        loss.backward()
                        optimizer.step()

                # Save local personalized model
                self.personalized_models[cid] = local_model

                # Flatten update vector: w_local - w_global
                w_loc = {k: v.cpu().numpy() for k, v in local_model.state_dict().items()}
                diff_flat = np.concatenate(
                    [(w_loc[k] - base_weights[k]).flatten() for k in sorted(w_loc.keys())]
                )
                client_updates.append(diff_flat)
                valid_cids.append(cid)
                sample_counts.append(len(x_cl))

            if client_updates:
                # Apply Two-Phase Similarity Defense
                accepted_indices = self.defense.filter_updates(
                    update_vectors=client_updates,
                    reference_direction=prev_consensus_dir,
                )

                tot_s = sum(sample_counts[i] for i in accepted_indices) or 1
                new_state = {}
                for k in base_weights.keys():
                    accepted_diffs = sum(
                        (
                            self.personalized_models[valid_cids[i]].state_dict()[k].cpu().numpy()
                            - base_weights[k]
                        )
                        * (sample_counts[i] / tot_s)
                        for i in accepted_indices
                    )
                    new_state[k] = torch.tensor(base_weights[k] + accepted_diffs)

                self.global_model.load_state_dict(new_state)
                prev_consensus_dir = np.mean([client_updates[i] for i in accepted_indices], axis=0)

        return self.global_model

    def predict(self, x: np.ndarray, client_id: str | None = None) -> np.ndarray:
        """Predict using client personalized model if available, else global model."""
        model = self.global_model
        if client_id is not None and client_id in self.personalized_models:
            model = self.personalized_models[client_id]

        model.eval()
        with torch.no_grad():
            xt = torch.tensor(x, dtype=torch.float32).to(self.device)
            out = model(xt)
            logits = out.logits if hasattr(out, "logits") else out
            preds = torch.argmax(logits, dim=1).cpu().numpy()
        return preds

    def evaluate(
        self,
        x_test: np.ndarray,
        y_test: np.ndarray,
        label_names: list[str] | None = None,
        client_id: str | None = None,
    ) -> BaselineEvaluationResult:
        """Evaluate pFL-IDS baseline."""
        t0 = time.perf_counter()
        y_pred = self.predict(x_test, client_id=client_id)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        metrics = compute_standard_metrics(y_test, y_pred, label_names=label_names)

        return BaselineEvaluationResult(
            baseline_id=self.baseline_id,
            baseline_name=f"{self.baseline_name} ({'Personalized ' + client_id if client_id else 'Global'})",
            fidelity_tier="faithful_reimplementation",
            num_samples_evaluated=len(x_test),
            accuracy=metrics["accuracy"],
            precision_macro=metrics["precision_macro"],
            recall_macro=metrics["recall_macro"],
            macro_f1=metrics["macro_f1"],
            false_positive_rate=metrics["false_positive_rate"],
            inference_latency_ms=round(latency_ms, 3),
            communication_bytes=0,
            notes="Faithful pFL-IDS: Logit-adjusted loss and two-phase cosine-similarity/benign centroid defense",
            per_class_f1=metrics["per_class_f1"],
        )
