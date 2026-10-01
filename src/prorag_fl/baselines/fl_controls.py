"""B2, B3, B4 — Standard Federated Learning Baseline Controls.

Implements standard federated learning aggregation baselines without blockchain or provenance filtering:
- B2: Plain FedAvg (McMahan et al.)
- B3: MultiKrum (Blanchard et al.)
- B4: FedTrimmedAvg (Yin et al., beta=0.20)

Adheres strictly to instructions/20_BASELINES_MASTER.md and 21_BASELINE_IMPLEMENTATION_DETAILS.md.
"""

from __future__ import annotations

import time
from typing import Any, Literal

import numpy as np
import torch

from prorag_fl.baselines.common import (
    BaseBaseline,
    BaselineEvaluationResult,
    compute_standard_metrics,
)
from prorag_fl.federated.simulation import run_fl_simulation
from prorag_fl.models.ids_1dcnn import IDS1DCNN
from prorag_fl.schemas.federated import FLSimulationResult


class StandardFLBaseline(BaseBaseline):
    """Unified wrapper for standard federated learning baselines (B2, B3, B4)."""

    def __init__(
        self,
        strategy_name: Literal["fedavg", "multikrum", "fedtrimmedavg"],
        num_features: int,
        num_classes: int,
        num_rounds: int = 5,
        num_clients: int = 5,
        fraction_fit: float = 1.0,
        local_epochs: int = 2,
        batch_size: int = 128,
        learning_rate: float = 1e-3,
        device: str = "cpu",
        strategy_kwargs: dict[str, Any] | None = None,
    ) -> None:
        name_map = {
            "fedavg": ("B2", "FedAvg-1D-CNN"),
            "multikrum": ("B3", "MultiKrum-1D-CNN"),
            "fedtrimmedavg": ("B4", "FedTrimmedAvg-1D-CNN"),
        }
        b_id, b_name = name_map[strategy_name]
        super().__init__(baseline_id=b_id, baseline_name=b_name)

        self.strategy_name = strategy_name
        self.num_features = num_features
        self.num_classes = num_classes
        self.num_rounds = num_rounds
        self.num_clients = num_clients
        self.fraction_fit = fraction_fit
        self.local_epochs = local_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.device = device
        self.strategy_kwargs = strategy_kwargs or {}

        self.global_model = IDS1DCNN(
            num_features=self.num_features,
            num_classes=self.num_classes,
        )
        self.simulation_result: FLSimulationResult | None = None

    def fit(
        self,
        client_partitions: dict[str, tuple[np.ndarray, np.ndarray]],
        val_data: tuple[np.ndarray, np.ndarray] | None = None,
        **kwargs: Any,
    ) -> FLSimulationResult:
        """Execute federated simulation across the immutable client partitions."""
        client_train_data: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        client_val_data: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        all_val_x, all_val_y = [], []

        for idx, (_, (x_c, y_c)) in enumerate(client_partitions.items()):
            n_samples = len(x_c)
            split_pt = max(1, int(n_samples * 0.8))
            if split_pt < n_samples:
                client_train_data[idx] = (x_c[:split_pt], y_c[:split_pt])
                client_val_data[idx] = (x_c[split_pt:], y_c[split_pt:])
                all_val_x.append(x_c[split_pt:])
                all_val_y.append(y_c[split_pt:])
            else:
                client_train_data[idx] = (x_c, y_c)
                client_val_data[idx] = (x_c, y_c)
                all_val_x.append(x_c)
                all_val_y.append(y_c)

        if val_data is not None:
            g_val = val_data
        else:
            g_val = (np.vstack(all_val_x), np.concatenate(all_val_y))

        import tempfile
        from pathlib import Path

        ckpt_dir = kwargs.get("checkpoint_dir") or tempfile.mkdtemp()
        sim_res = run_fl_simulation(
            strategy_name=self.strategy_name,
            dataset_name="ids_dataset",
            num_clients=len(client_train_data),
            num_rounds=self.num_rounds,
            client_train_data=client_train_data,
            client_val_data=client_val_data,
            global_val_data=g_val,
            num_features=self.num_features,
            num_classes=self.num_classes,
            local_epochs=self.local_epochs,
            checkpoint_dir=ckpt_dir,
        )
        self.simulation_result = sim_res

        # Set final global model weights from saved checkpoint
        if sim_res.final_checkpoint_path and Path(sim_res.final_checkpoint_path).exists():
            state_dict = torch.load(sim_res.final_checkpoint_path)
            self.global_model.load_state_dict(state_dict)

        return sim_res

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Classify test instances using the aggregated global model."""
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
        """Evaluate aggregated global model against the common test dataset."""
        t0 = time.perf_counter()
        y_pred = self.predict(x_test)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        metrics = compute_standard_metrics(y_test, y_pred, label_names=label_names)
        comm_bytes = (
            (self.simulation_result.total_model_bytes + self.simulation_result.total_metadata_bytes)
            if self.simulation_result
            else 0
        )

        notes_map = {
            "fedavg": "Standard FedAvg with sample-count weighting, no provenance checks",
            "multikrum": "MultiKrum Byzantine-robust update distance scoring without blockchain",
            "fedtrimmedavg": "Coordinate-wise trimmed average (beta=0.20) without blockchain provenance",
        }

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
            communication_bytes=comm_bytes,
            notes=notes_map[self.strategy_name],
            per_class_f1=metrics["per_class_f1"],
        )
