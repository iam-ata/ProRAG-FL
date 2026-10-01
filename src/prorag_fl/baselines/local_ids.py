"""B0 — Local 1D-CNN Baseline.

Trains a local 1D-CNN independently on each client's partition without any federation or weight sharing.
Adheres strictly to instructions/21_BASELINE_IMPLEMENTATION_DETAILS.md:
"1. Reuse immutable client partitions.
 2. Same initialization family/preprocessor/model.
 3. Train each client independently.
 4. Evaluate per-client and common test where meaningful.
 5. Do not aggregate weights."
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


class Local1DCNNBaseline(BaseBaseline):
    """B0: Local independent 1D-CNN without collaboration."""

    def __init__(
        self,
        num_features: int,
        num_classes: int,
        dropout_rate: float = 0.2,
        device: str = "cpu",
        learning_rate: float = 1e-3,
        epochs: int = 5,
        batch_size: int = 128,
    ) -> None:
        super().__init__(baseline_id="B0", baseline_name="Local-1D-CNN")
        self.num_features = num_features
        self.num_classes = num_classes
        self.dropout_rate = dropout_rate
        self.device = device
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size

        # Dictionary mapping client_id to trained model
        self.client_models: dict[str, IDS1DCNN] = {}

    def fit_client(
        self,
        client_id: str,
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
    ) -> IDS1DCNN:
        """Train a 1D-CNN locally on client data without sharing weights."""
        model = IDS1DCNN(
            num_features=self.num_features,
            num_classes=self.num_classes,
            dropout_rate=self.dropout_rate,
        )
        trainer = IDSTrainer(
            model=model,
            device=self.device,
            learning_rate=self.learning_rate,
        )

        train_ds = TensorDataset(
            torch.tensor(x_train, dtype=torch.float32),
            torch.tensor(y_train, dtype=torch.long),
        )
        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)

        val_loader = None
        if x_val is not None and y_val is not None:
            val_ds = TensorDataset(
                torch.tensor(x_val, dtype=torch.float32),
                torch.tensor(y_val, dtype=torch.long),
            )
            val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False)

        trainer.train(
            train_loader=train_loader,
            val_loader=val_loader,
            epochs=self.epochs,
        )

        self.client_models[client_id] = model
        return model

    def fit(self, train_data: dict[str, tuple[np.ndarray, np.ndarray]], **kwargs: Any) -> Any:
        """Fit all local clients on their respective local datasets."""
        for client_id, (x_tr, y_tr) in train_data.items():
            self.fit_client(client_id=client_id, x_train=x_tr, y_train=y_tr)
        return self.client_models

    def predict(self, x: np.ndarray, client_id: str | None = None) -> np.ndarray:
        """Predict using a specific client model, or ensemble average if client_id is None."""
        if not self.client_models:
            raise RuntimeError("No local models have been trained.")

        if client_id is not None and client_id in self.client_models:
            model = self.client_models[client_id]
            model.eval()
            with torch.no_grad():
                xt = torch.tensor(x, dtype=torch.float32).to(self.device)
                out = model(xt)
                logits = out.logits if hasattr(out, "logits") else out
                preds = torch.argmax(logits, dim=1).cpu().numpy()
            return preds

        # If client_id is None, average logits across all local models
        all_logits = []
        with torch.no_grad():
            xt = torch.tensor(x, dtype=torch.float32).to(self.device)
            for model in self.client_models.values():
                model.eval()
                out = model(xt)
                logits = out.logits if hasattr(out, "logits") else out
                all_logits.append(logits.cpu().numpy())

        avg_logits = np.mean(all_logits, axis=0)
        return np.argmax(avg_logits, axis=1)

    def evaluate(
        self,
        x_test: np.ndarray,
        y_test: np.ndarray,
        label_names: list[str] | None = None,
        client_id: str | None = None,
    ) -> BaselineEvaluationResult:
        """Evaluate local model(s) on test data."""
        t0 = time.perf_counter()
        y_pred = self.predict(x_test, client_id=client_id)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        metrics = compute_standard_metrics(y_test, y_pred, label_names=label_names)

        return BaselineEvaluationResult(
            baseline_id=self.baseline_id,
            baseline_name=f"{self.baseline_name} (Client: {client_id or 'Ensemble'})",
            fidelity_tier="faithful_reimplementation",
            num_samples_evaluated=len(x_test),
            accuracy=metrics["accuracy"],
            precision_macro=metrics["precision_macro"],
            recall_macro=metrics["recall_macro"],
            macro_f1=metrics["macro_f1"],
            false_positive_rate=metrics["false_positive_rate"],
            inference_latency_ms=round(latency_ms, 3),
            communication_bytes=0,  # Zero communication in local-only training
            notes="Independent local training without federated aggregation",
            per_class_f1=metrics["per_class_f1"],
        )
