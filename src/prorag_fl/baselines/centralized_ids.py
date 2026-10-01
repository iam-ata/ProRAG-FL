"""B1 — Centralized 1D-CNN Baseline (Oracle Reference).

Pools all client training partitions into a centralized dataset and trains an oracle reference model.
Adheres strictly to instructions/21_BASELINE_IMPLEMENTATION_DETAILS.md:
"1. Union global training-client indices.
 2. Same validation/test.
 3. Same architecture/preprocessor.
 4. Tune only on validation.
 5. Evaluate final frozen checkpoint."
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


class Centralized1DCNNBaseline(BaseBaseline):
    """B1: Centralized 1D-CNN oracle reference."""

    def __init__(
        self,
        num_features: int,
        num_classes: int,
        dropout_rate: float = 0.2,
        device: str = "cpu",
        learning_rate: float = 1e-3,
        epochs: int = 10,
        batch_size: int = 128,
    ) -> None:
        super().__init__(baseline_id="B1", baseline_name="Centralized-1D-CNN")
        self.num_features = num_features
        self.num_classes = num_classes
        self.dropout_rate = dropout_rate
        self.device = device
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size

        self.model = IDS1DCNN(
            num_features=self.num_features,
            num_classes=self.num_classes,
            dropout_rate=self.dropout_rate,
        )
        self.trainer = IDSTrainer(
            model=self.model,
            device=self.device,
            learning_rate=self.learning_rate,
        )

    def fit(
        self,
        train_data: tuple[np.ndarray, np.ndarray],
        val_data: tuple[np.ndarray, np.ndarray] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Train the centralized model on the pooled training dataset."""
        x_train, y_train = train_data
        train_ds = TensorDataset(
            torch.tensor(x_train, dtype=torch.float32),
            torch.tensor(y_train, dtype=torch.long),
        )
        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)

        val_loader = None
        if val_data is not None:
            x_val, y_val = val_data
            val_ds = TensorDataset(
                torch.tensor(x_val, dtype=torch.float32),
                torch.tensor(y_val, dtype=torch.long),
            )
            val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False)

        history = self.trainer.train(
            train_loader=train_loader,
            val_loader=val_loader,
            epochs=self.epochs,
        )
        return history

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Predict classes using the trained centralized model."""
        self.model.eval()
        with torch.no_grad():
            xt = torch.tensor(x, dtype=torch.float32).to(self.device)
            out = self.model(xt)
            logits = out.logits if hasattr(out, "logits") else out
            preds = torch.argmax(logits, dim=1).cpu().numpy()
        return preds

    def evaluate(
        self,
        x_test: np.ndarray,
        y_test: np.ndarray,
        label_names: list[str] | None = None,
    ) -> BaselineEvaluationResult:
        """Evaluate centralized model on test data."""
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
            communication_bytes=0,  # Centralized oracle: no federated communication rounds
            notes="Centralized oracle trained on union of all client training partitions",
            per_class_f1=metrics["per_class_f1"],
        )
