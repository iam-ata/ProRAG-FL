"""B6 — FLOW Baseline.

"FLOW: A Robust Federated Learning Framework to Defend Against Model Poisoning Attacks in IoT"
IEEE Internet of Things Journal, 2024. DOI: 10.1109/JIOT.2023.3341811.

Implements faithful reimplementation:
- FlowHistoryState: Tracks historical cosine distance behavior and dynamic penalty factors.
- FlowDetector: Computes pairwise cosine distance matrix and identifies anomalous/malicious updates.
- FlowAggregator: Applies graceful punishment rather than permanent exclusion, permitting recovery.
- FlowBaseline: Complete FL baseline coordination.

Adheres strictly to instructions/20_BASELINES_MASTER.md and 21_BASELINE_IMPLEMENTATION_DETAILS.md.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from prorag_fl.baselines.common import (
    BaseBaseline,
    BaselineEvaluationResult,
    compute_standard_metrics,
)
from prorag_fl.models.ids_1dcnn import IDS1DCNN
from prorag_fl.models.trainer import IDSTrainer


class FlowHistoryState:
    """Historical behavior tracking per client for graceful punishment and recovery."""

    def __init__(
        self,
        client_id: str,
        penalty_rate: float = 0.5,
        recovery_rate: float = 0.2,
    ) -> None:
        self.client_id = client_id
        self.penalty_rate = penalty_rate
        self.recovery_rate = recovery_rate
        self.penalty_factor = 0.0  # 0.0 means full weight; 1.0 means fully suppressed
        self.consecutive_malicious_rounds = 0
        self.history_scores: list[float] = []

    def update(self, is_malicious: bool, anomaly_score: float) -> float:
        """Update client penalty factor based on current round observation."""
        self.history_scores.append(anomaly_score)
        if is_malicious:
            self.consecutive_malicious_rounds += 1
            # Graceful exponential penalty increase
            self.penalty_factor = min(1.0, self.penalty_factor + self.penalty_rate)
        else:
            self.consecutive_malicious_rounds = 0
            # Graceful linear recovery credit
            self.penalty_factor = max(0.0, self.penalty_factor - self.recovery_rate)
        return self.penalty_factor


class FlowDetector:
    """Detects malicious updates using pairwise cosine distances and historical momentum."""

    def __init__(self, distance_threshold_std: float = 1.5) -> None:
        self.distance_threshold_std = distance_threshold_std

    def compute_cosine_distances(self, update_vectors: list[np.ndarray]) -> np.ndarray:
        """Compute pairwise cosine distance matrix between flattened client updates."""
        num_clients = len(update_vectors)
        dist_matrix = np.zeros((num_clients, num_clients), dtype=np.float32)

        norms = [np.linalg.norm(v) + 1e-10 for v in update_vectors]

        for i in range(num_clients):
            for j in range(i, num_clients):
                if i == j:
                    dist_matrix[i, j] = 0.0
                else:
                    dot = float(np.dot(update_vectors[i], update_vectors[j]))
                    cos_sim = dot / (norms[i] * norms[j])
                    cos_dist = float(1.0 - cos_sim)
                    dist_matrix[i, j] = cos_dist
                    dist_matrix[j, i] = cos_dist

        return dist_matrix

    def detect(
        self,
        update_vectors: list[np.ndarray],
        client_histories: dict[str, FlowHistoryState],
        client_ids: list[str],
    ) -> tuple[list[bool], list[float]]:
        """Identify malicious clients and calculate anomaly scores."""
        num_clients = len(update_vectors)
        if num_clients <= 2:
            return [False] * num_clients, [0.0] * num_clients

        dist_matrix = self.compute_cosine_distances(update_vectors)

        # Average distance to other clients: d_i = sum_{j != i} D_{ij} / (K - 1)
        mean_distances = []
        for i in range(num_clients):
            other_dists = [dist_matrix[i, j] for j in range(num_clients) if i != j]
            mean_distances.append(float(np.mean(other_dists)))

        mean_d = float(np.mean(mean_distances))
        std_d = float(np.std(mean_distances))
        threshold = mean_d + self.distance_threshold_std * max(std_d, 1e-4)

        is_malicious_list = []
        anomaly_scores = []
        for i, cid in enumerate(client_ids):
            score = mean_distances[i]
            # Client considered malicious if its average cosine distance exceeds threshold or opposite direction
            is_mal = score > threshold or score > 1.2
            is_malicious_list.append(is_mal)
            anomaly_scores.append(score)

            if cid in client_histories:
                client_histories[cid].update(is_mal, score)

        return is_malicious_list, anomaly_scores


class FlowAggregator:
    """Robust aggregation applying FLOW dynamic penalty and weight discounting."""

    def __init__(self, detector: FlowDetector) -> None:
        self.detector = detector
        self.client_histories: dict[str, FlowHistoryState] = {}

    def aggregate(
        self,
        client_ids: list[str],
        client_weights: list[dict[str, np.ndarray]],
        base_weights: dict[str, np.ndarray],
        sample_counts: list[int],
    ) -> tuple[dict[str, np.ndarray], list[bool]]:
        """Aggregate model updates with FLOW penalty suppression."""
        for cid in client_ids:
            if cid not in self.client_histories:
                self.client_histories[cid] = FlowHistoryState(client_id=cid)

        # Flatten updates: delta_i = w_i - w_global
        flattened_updates = []
        for w in client_weights:
            flat_parts = []
            for k in sorted(w.keys()):
                diff = (w[k] - base_weights[k]).flatten()
                flat_parts.append(diff)
            flattened_updates.append(np.concatenate(flat_parts))

        # Detect
        is_malicious_list, _ = self.detector.detect(
            update_vectors=flattened_updates,
            client_histories=self.client_histories,
            client_ids=client_ids,
        )

        # Compute effective aggregation weights using sample count and penalty factor
        effective_weights = []
        for i, cid in enumerate(client_ids):
            pen = self.client_histories[cid].penalty_factor
            # If marked malicious this round, suppress completely for this round
            if is_malicious_list[i]:
                w_eff = 0.0
            else:
                w_eff = sample_counts[i] * (1.0 - pen)
            effective_weights.append(max(0.0, w_eff))

        total_weight = sum(effective_weights)
        if total_weight <= 1e-10:
            # Fallback to mean of non-penalized or uniform if all suppressed
            effective_weights = [1.0 if not m else 0.0 for m in is_malicious_list]
            total_weight = sum(effective_weights) or 1.0

        normalized_weights = [w / total_weight for w in effective_weights]

        # Aggregate parameters
        aggregated_weights = {}
        for k in base_weights.keys():
            aggregated_weights[k] = sum(
                normalized_weights[i] * client_weights[i][k] for i in range(len(client_ids))
            )

        return aggregated_weights, is_malicious_list


class FlowBaseline(BaseBaseline):
    """B6: FLOW poisoning-robust federated learning baseline."""

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
        super().__init__(baseline_id="B6", baseline_name="FLOW")
        self.num_features = num_features
        self.num_classes = num_classes
        self.num_rounds = num_rounds
        self.local_epochs = local_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.device = device

        self.global_model = IDS1DCNN(
            num_features=num_features,
            num_classes=num_classes,
        )
        self.aggregator = FlowAggregator(detector=FlowDetector())

    def fit(
        self,
        client_partitions: dict[str, tuple[np.ndarray, np.ndarray]],
        **kwargs: Any,
    ) -> IDS1DCNN:
        """Run FLOW federated learning simulation."""
        client_ids = list(client_partitions.keys())

        for _ in range(self.num_rounds):
            base_weights = {k: v.cpu().numpy() for k, v in self.global_model.state_dict().items()}
            round_weights = []
            sample_counts = []

            for cid in client_ids:
                x_cl, y_cl = client_partitions[cid]
                if len(x_cl) == 0:
                    continue

                local_model = IDS1DCNN(
                    num_features=self.num_features,
                    num_classes=self.num_classes,
                )
                local_model.load_state_dict(self.global_model.state_dict())

                trainer = IDSTrainer(
                    model=local_model,
                    device=self.device,
                    learning_rate=self.learning_rate,
                )
                train_ds = TensorDataset(
                    torch.tensor(x_cl, dtype=torch.float32),
                    torch.tensor(y_cl, dtype=torch.long),
                )
                train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)
                trainer.train(train_loader=train_loader, epochs=self.local_epochs)

                round_weights.append(
                    {k: v.cpu().numpy() for k, v in local_model.state_dict().items()}
                )
                sample_counts.append(len(x_cl))

            if round_weights:
                new_weights, _ = self.aggregator.aggregate(
                    client_ids=client_ids,
                    client_weights=round_weights,
                    base_weights=base_weights,
                    sample_counts=sample_counts,
                )
                torch_weights = {k: torch.tensor(v) for k, v in new_weights.items()}
                self.global_model.load_state_dict(torch_weights)

        return self.global_model

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Classify test instances."""
        self.global_model.eval()
        with torch.no_grad():
            xt = torch.tensor(x, dtype=torch.float32).to(self.device)
            out = self.global_model(xt)
            logits = out.logits if hasattr(out, "logits") else out
            preds = torch.argmax(logits, dim=1).cpu().numpy()
        return preds

    def evaluate(
        self,
        x_test: np.ndarray,
        y_test: np.ndarray,
        label_names: list[str] | None = None,
    ) -> BaselineEvaluationResult:
        """Evaluate FLOW baseline on test data."""
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
            notes="Faithful FLOW: Pairwise cosine distance detection, graceful historical punishment and recovery",
            per_class_f1=metrics["per_class_f1"],
        )
