"""B7 — Bc²FL Baseline.

"Bc²FL: Double-Layer Blockchain-Driven Federated Learning Framework for Agricultural IoT"
IEEE Internet of Things Journal, 2025. DOI: 10.1109/JIOT.2024.3485208.

Implements Mode B (Component/System Comparison):
- DoubleLayerBlockchainSimulator: Layer-1 Edge Cluster Consensus and Layer-2 Cloud Global Consensus.
- Hierarchical FL topology: Edge groups aggregate locally; cloud committee aggregates regionally with quality weighting.
- Model quality scoring: Adaptive weighting based on regional validation loss.

Adheres strictly to instructions/20_BASELINES_MASTER.md and 21_BASELINE_IMPLEMENTATION_DETAILS.md.
Marked: approximate_reimplementation (applied to network intrusion detection workload).
"""

from __future__ import annotations

import hashlib
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


class DoubleLayerBlockchainSimulator:
    """Simulates double-layer blockchain consensus and transaction records for Bc²FL."""

    def __init__(self, num_edge_clusters: int = 2) -> None:
        self.num_edge_clusters = num_edge_clusters
        self.edge_chain_blocks: list[dict[str, Any]] = []
        self.cloud_chain_blocks: list[dict[str, Any]] = []
        self.total_consensus_overhead_bytes = 0

    def commit_edge_round(
        self,
        cluster_id: int,
        round_idx: int,
        model_hash: str,
        quality_score: float,
    ) -> str:
        """Stage 1: Edge-layer PBFT/Raft block commitment."""
        prev_hash = self.edge_chain_blocks[-1]["block_hash"] if self.edge_chain_blocks else "0" * 64
        payload = f"{cluster_id}:{round_idx}:{model_hash}:{quality_score:.4f}:{prev_hash}"
        b_hash = hashlib.sha256(payload.encode()).hexdigest()

        block = {
            "layer": 1,
            "cluster_id": cluster_id,
            "round_idx": round_idx,
            "model_hash": model_hash,
            "quality_score": quality_score,
            "prev_hash": prev_hash,
            "block_hash": b_hash,
        }
        self.edge_chain_blocks.append(block)
        # Approximate PBFT message exchange overhead (~8 KB per edge round)
        self.total_consensus_overhead_bytes += 8192
        return b_hash

    def commit_cloud_round(
        self,
        round_idx: int,
        global_model_hash: str,
        contributing_edge_hashes: list[str],
    ) -> str:
        """Stage 2: Cloud-layer BFT cross-cluster block commitment."""
        prev_hash = (
            self.cloud_chain_blocks[-1]["block_hash"] if self.cloud_chain_blocks else "0" * 64
        )
        payload = f"cloud:{round_idx}:{global_model_hash}:{','.join(contributing_edge_hashes)}:{prev_hash}"
        b_hash = hashlib.sha256(payload.encode()).hexdigest()

        block = {
            "layer": 2,
            "round_idx": round_idx,
            "global_model_hash": global_model_hash,
            "contributing_edge_hashes": contributing_edge_hashes,
            "prev_hash": prev_hash,
            "block_hash": b_hash,
        }
        self.cloud_chain_blocks.append(block)
        # Cloud committee consensus overhead (~16 KB per global round)
        self.total_consensus_overhead_bytes += 16384
        return b_hash


class Bc2FLBaseline(BaseBaseline):
    """B7: Bc²FL double-layer blockchain federated learning baseline."""

    def __init__(
        self,
        num_features: int,
        num_classes: int,
        num_rounds: int = 5,
        num_edge_clusters: int = 2,
        local_epochs: int = 2,
        batch_size: int = 128,
        learning_rate: float = 1e-3,
        device: str = "cpu",
    ) -> None:
        super().__init__(baseline_id="B7", baseline_name="Bc2FL")
        self.num_features = num_features
        self.num_classes = num_classes
        self.num_rounds = num_rounds
        self.num_edge_clusters = num_edge_clusters
        self.local_epochs = local_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.device = device

        self.global_model = IDS1DCNN(
            num_features=num_features,
            num_classes=num_classes,
        )
        self.blockchain = DoubleLayerBlockchainSimulator(num_edge_clusters=num_edge_clusters)

    def fit(
        self,
        client_partitions: dict[str, tuple[np.ndarray, np.ndarray]],
        val_data: tuple[np.ndarray, np.ndarray] | None = None,
        **kwargs: Any,
    ) -> IDS1DCNN:
        """Execute hierarchical double-layer blockchain FL."""
        cids = list(client_partitions.keys())
        # Split clients into edge clusters
        clusters: list[list[str]] = [[] for _ in range(self.num_edge_clusters)]
        for idx, cid in enumerate(cids):
            clusters[idx % self.num_edge_clusters].append(cid)

        for rnd in range(self.num_rounds):
            edge_models: list[dict[str, np.ndarray]] = []
            edge_qualities: list[float] = []
            edge_hashes: list[str] = []

            # 1. Edge-Layer Local Training & Aggregation
            for c_idx, cluster_clients in enumerate(clusters):
                cluster_weights = []
                cluster_samples = []

                for cid in cluster_clients:
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
                    loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)
                    trainer.train(train_loader=loader, epochs=self.local_epochs)

                    cluster_weights.append(
                        {k: v.cpu().numpy() for k, v in local_model.state_dict().items()}
                    )
                    cluster_samples.append(len(x_cl))

                if cluster_weights:
                    # Intra-cluster FedAvg
                    tot_s = sum(cluster_samples)
                    edge_agg = {}
                    for k in cluster_weights[0].keys():
                        edge_agg[k] = sum(
                            (w[k] * (cluster_samples[i] / tot_s))
                            for i, w in enumerate(cluster_weights)
                        )
                    edge_models.append(edge_agg)

                    # Compute quality score Q = exp(-val_loss)
                    q_score = 1.0
                    if val_data is not None:
                        vx, vy = val_data
                        val_m = IDS1DCNN(self.num_features, self.num_classes)
                        val_m.load_state_dict({k: torch.tensor(v) for k, v in edge_agg.items()})
                        val_m.eval()
                        with torch.no_grad():
                            v_out = val_m(
                                torch.tensor(vx[: min(100, len(vx))], dtype=torch.float32)
                            )
                            v_logits = v_out.logits if hasattr(v_out, "logits") else v_out
                            v_loss = torch.nn.functional.cross_entropy(
                                v_logits, torch.tensor(vy[: min(100, len(vy))], dtype=torch.long)
                            ).item()
                        q_score = float(np.exp(-min(v_loss, 5.0)))
                    edge_qualities.append(q_score)

                    # Commit to Stage 1 Edge Blockchain
                    m_hash = hashlib.sha256(str(sorted(edge_agg.keys())).encode()).hexdigest()
                    b_hash = self.blockchain.commit_edge_round(
                        cluster_id=c_idx,
                        round_idx=rnd,
                        model_hash=m_hash,
                        quality_score=q_score,
                    )
                    edge_hashes.append(b_hash)

            # 2. Cloud-Layer Adaptive Quality Aggregation
            if edge_models:
                tot_q = sum(edge_qualities) or 1.0
                q_weights = [q / tot_q for q in edge_qualities]

                cloud_agg = {}
                for k in edge_models[0].keys():
                    cloud_agg[k] = sum(
                        q_weights[i] * edge_models[i][k] for i in range(len(edge_models))
                    )

                self.global_model.load_state_dict(
                    {k: torch.tensor(v) for k, v in cloud_agg.items()}
                )

                # Commit to Stage 2 Cloud Blockchain
                global_hash = hashlib.sha256(str(sorted(cloud_agg.keys())).encode()).hexdigest()
                self.blockchain.commit_cloud_round(
                    round_idx=rnd,
                    global_model_hash=global_hash,
                    contributing_edge_hashes=edge_hashes,
                )

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
        """Evaluate Bc²FL baseline."""
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
            communication_bytes=self.blockchain.total_consensus_overhead_bytes,
            notes="Approximate Bc2FL: Mode B double-layer blockchain hierarchy and quality aggregation",
            per_class_f1=metrics["per_class_f1"],
        )
