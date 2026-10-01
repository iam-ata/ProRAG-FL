"""Flower NumPyClient implementation for local 1D-CNN IDS training with provenance envelopes."""

from __future__ import annotations

import flwr as fl
import numpy as np
import torch
import torch.nn as nn
from flwr.common import Scalar
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader

from prorag_fl.federated.provenance_envelope import (
    create_provenance_envelope,
    serialize_ndarrays,
)
from prorag_fl.models.ids_1dcnn import IDS1DCNN


class FlowerIDSClient(fl.client.NumPyClient):
    """Flower client executing local 1D-CNN IDS training adhering to 12_FEDERATED_LEARNING.md."""

    def __init__(
        self,
        client_id: str,
        model: IDS1DCNN,
        train_loader: DataLoader,
        val_loader: DataLoader,
        class_weights: torch.Tensor | None = None,
        local_epochs: int = 2,
        lr: float = 0.001,
        weight_decay: float = 0.0001,
        device: torch.device | str | None = None,
        secret_key: str = "prorag_shared_secret",
    ) -> None:
        self.client_id = client_id
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        elif isinstance(device, str):
            self.device = torch.device(device)
        else:
            self.device = device

        self.model = model.to(self.device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.class_weights = class_weights.to(self.device) if class_weights is not None else None
        self.local_epochs = local_epochs
        self.lr = lr
        self.weight_decay = weight_decay
        self.secret_key = secret_key

    def get_parameters(self, config: dict[str, Scalar]) -> list[np.ndarray]:
        """Return current model parameters as list of NumPy arrays."""
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters: list[np.ndarray]) -> None:
        """Set model parameters from list of NumPy arrays."""
        state_dict = dict(
            zip(
                self.model.state_dict().keys(),
                [torch.from_numpy(p) for p in parameters],
                strict=True,
            )
        )
        self.model.load_state_dict(state_dict, strict=True)

    def fit(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Scalar],
    ) -> tuple[list[np.ndarray], int, dict[str, Scalar]]:
        """Train model locally, record sample metrics, sign provenance envelope, and return updates."""
        # 1. Receive global model + version + round
        self.set_parameters(parameters)
        server_round = int(config.get("server_round", 1))
        global_model_version = str(config.get("global_model_version", "v1.0.0"))
        epochs = int(config.get("local_epochs", self.local_epochs))

        # 2. Local optimizer and criterion
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.lr,
            weight_decay=self.weight_decay,
        )
        criterion = nn.CrossEntropyLoss(weight=self.class_weights)

        # 3. Train local epochs
        self.model.train()
        total_loss = 0.0
        correct = 0
        total_samples = 0

        for _ in range(epochs):
            for x, y in self.train_loader:
                x = x.to(self.device)
                y = y.to(self.device)

                optimizer.zero_grad()
                out = self.model(x)
                loss = criterion(out.logits, y)
                loss.backward()
                optimizer.step()

                bs = x.size(0)
                total_loss += loss.item() * bs
                preds = torch.argmax(out.logits, dim=1)
                correct += (preds == y).sum().item()
                total_samples += bs

        num_examples = len(self.train_loader.dataset)
        avg_loss = total_loss / max(total_samples, 1)
        avg_acc = correct / max(total_samples, 1)

        # 4. Extract updated parameters and compute update diff / weights
        updated_parameters = self.get_parameters(config={})

        # 5. Create signed provenance envelope
        envelope = create_provenance_envelope(
            client_id=self.client_id,
            server_round=server_round,
            global_model_version=global_model_version,
            update_ndarrays=updated_parameters,
            num_examples=num_examples,
            local_loss=avg_loss,
            local_accuracy=avg_acc,
            secret_key=self.secret_key,
        )

        # 6. Communication accounting: measure actual bytes
        update_bytes = len(serialize_ndarrays(updated_parameters))
        metadata_bytes = len(envelope.model_dump_json().encode("utf-8"))

        metrics: dict[str, Scalar] = {
            "client_id": self.client_id,
            "train_loss": float(avg_loss),
            "train_acc": float(avg_acc),
            "update_bytes": int(update_bytes),
            "metadata_bytes": int(metadata_bytes),
            "provenance_envelope_json": envelope.model_dump_json(),
        }

        return updated_parameters, num_examples, metrics

    def evaluate(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Scalar],
    ) -> tuple[float, int, dict[str, Scalar]]:
        """Evaluate parameters on local validation partition."""
        self.set_parameters(parameters)
        criterion = nn.CrossEntropyLoss(weight=self.class_weights)
        self.model.eval()

        total_loss = 0.0
        correct = 0
        total_samples = 0
        all_preds: list[int] = []
        all_targets: list[int] = []

        with torch.no_grad():
            for x, y in self.val_loader:
                x = x.to(self.device)
                y = y.to(self.device)

                out = self.model(x)
                loss = criterion(out.logits, y)

                bs = x.size(0)
                total_loss += loss.item() * bs
                preds = torch.argmax(out.logits, dim=1)
                correct += (preds == y).sum().item()
                total_samples += bs

                all_preds.extend(preds.cpu().numpy().tolist())
                all_targets.extend(y.cpu().numpy().tolist())

        val_loss = total_loss / max(total_samples, 1)
        val_acc = correct / max(total_samples, 1)
        val_macro_f1 = float(f1_score(all_targets, all_preds, average="macro", zero_division=0))

        metrics: dict[str, Scalar] = {
            "val_acc": float(val_acc),
            "val_macro_f1": float(val_macro_f1),
        }
        return float(val_loss), total_samples, metrics
