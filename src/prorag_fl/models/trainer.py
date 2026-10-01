"""Deterministic trainer for local and centralized 1D-CNN IDS models."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader

from prorag_fl.models.ids_1dcnn import IDS1DCNN


class TrainingHistory:
    """Records per-epoch training and validation metrics."""

    def __init__(self) -> None:
        self.epochs: list[int] = []
        self.train_loss: list[float] = []
        self.train_acc: list[float] = []
        self.val_loss: list[float] = []
        self.val_acc: list[float] = []
        self.val_macro_f1: list[float] = []

    def record(
        self,
        epoch: int,
        train_loss: float,
        train_acc: float,
        val_loss: float,
        val_acc: float,
        val_macro_f1: float,
    ) -> None:
        self.epochs.append(epoch)
        self.train_loss.append(float(train_loss))
        self.train_acc.append(float(train_acc))
        self.val_loss.append(float(val_loss))
        self.val_acc.append(float(val_acc))
        self.val_macro_f1.append(float(val_macro_f1))

    def to_dict(self) -> dict[str, list[float] | list[int]]:
        return {
            "epochs": self.epochs,
            "train_loss": self.train_loss,
            "train_acc": self.train_acc,
            "val_loss": self.val_loss,
            "val_acc": self.val_acc,
            "val_macro_f1": self.val_macro_f1,
        }


class IDSTrainer:
    """Trainer for 1D-CNN IDS with AdamW, class-weighted CE, and validation early stopping."""

    def __init__(
        self,
        model: IDS1DCNN,
        class_weights: torch.Tensor | None = None,
        lr: float = 0.001,
        weight_decay: float = 0.0001,
        device: torch.device | str | None = None,
        learning_rate: float | None = None,
    ) -> None:
        if learning_rate is not None:
            lr = learning_rate
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        elif isinstance(device, str):
            self.device = torch.device(device)
        else:
            self.device = device

        self.model = model.to(self.device)
        self.class_weights = class_weights.to(self.device) if class_weights is not None else None

        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=lr,
            weight_decay=weight_decay,
        )

        self.criterion = nn.CrossEntropyLoss(weight=self.class_weights)
        self.history = TrainingHistory()
        self.best_model_state: dict[str, Any] | None = None
        self.best_val_loss: float = float("inf")
        self.best_epoch: int = -1

    def train_epoch(self, train_loader: DataLoader) -> tuple[float, float]:
        """Train the model for one epoch.

        Args:
            train_loader: Training DataLoader.

        Returns:
            Tuple of (average_loss, accuracy).
        """
        self.model.train()
        total_loss = 0.0
        correct = 0
        total_samples = 0

        for x, y in train_loader:
            x = x.to(self.device)
            y = y.to(self.device)

            self.optimizer.zero_grad()
            output = self.model(x)
            loss = self.criterion(output.logits, y)
            loss.backward()
            self.optimizer.step()

            batch_size = x.size(0)
            total_loss += loss.item() * batch_size
            preds = torch.argmax(output.logits, dim=1)
            correct += (preds == y).sum().item()
            total_samples += batch_size

        avg_loss = total_loss / max(total_samples, 1)
        acc = correct / max(total_samples, 1)
        return avg_loss, acc

    @torch.no_grad()
    def evaluate(self, val_loader: DataLoader) -> tuple[float, float, float]:
        """Evaluate model on validation data.

        Returns:
            Tuple of (loss, accuracy, macro_f1).
        """
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total_samples = 0

        all_preds: list[int] = []
        all_targets: list[int] = []

        for x, y in val_loader:
            x = x.to(self.device)
            y = y.to(self.device)

            output = self.model(x)
            loss = self.criterion(output.logits, y)

            batch_size = x.size(0)
            total_loss += loss.item() * batch_size
            preds = torch.argmax(output.logits, dim=1)
            correct += (preds == y).sum().item()
            total_samples += batch_size

            all_preds.extend(preds.cpu().numpy().tolist())
            all_targets.extend(y.cpu().numpy().tolist())

        avg_loss = total_loss / max(total_samples, 1)
        acc = correct / max(total_samples, 1)
        macro_f1 = float(f1_score(all_targets, all_preds, average="macro", zero_division=0))
        return avg_loss, acc, macro_f1

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        max_epochs: int = 50,
        patience: int = 5,
        test_loader: Any = None,  # Defense parameter to enforce test firewall
    ) -> TrainingHistory:
        """Fit model with validation early stopping.

        Strict Assertion:
            test_loader MUST be None. Trainers are firewalled from ever touching test data.
        """
        if test_loader is not None:
            raise ValueError(
                "TEST FIREWALL BREACH: A test DataLoader was passed to IDSTrainer.fit()! "
                "Training must NEVER touch the test set."
            )

        patience_counter = 0

        for epoch in range(1, max_epochs + 1):
            train_loss, train_acc = self.train_epoch(train_loader)
            val_loss, val_acc, val_f1 = self.evaluate(val_loader)

            self.history.record(
                epoch=epoch,
                train_loss=train_loss,
                train_acc=train_acc,
                val_loss=val_loss,
                val_acc=val_acc,
                val_macro_f1=val_f1,
            )

            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.best_epoch = epoch
                self.best_model_state = copy.deepcopy(self.model.state_dict())
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    # Early stopping triggered based solely on validation
                    break

        # Restore best model state
        if self.best_model_state is not None:
            self.model.load_state_dict(self.best_model_state)

        return self.history

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader | None = None,
        epochs: int = 5,
    ) -> TrainingHistory:
        """Convenience multi-epoch trainer without requiring early stopping."""
        for epoch in range(1, epochs + 1):
            train_loss, train_acc = self.train_epoch(train_loader)
            if val_loader is not None:
                val_loss, val_acc, val_f1 = self.evaluate(val_loader)
            else:
                val_loss, val_acc, val_f1 = train_loss, train_acc, 0.0
            self.history.record(
                epoch=epoch,
                train_loss=train_loss,
                train_acc=train_acc,
                val_loss=val_loss,
                val_acc=val_acc,
                val_macro_f1=val_f1,
            )
        return self.history

    def save_checkpoint(
        self,
        filepath: Path | str,
        extra_metadata: dict[str, Any] | None = None,
    ) -> tuple[Path, str]:
        """Save model checkpoint and compute its SHA-256 digest."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint: dict[str, Any] = {
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "best_val_loss": self.best_val_loss,
            "best_epoch": self.best_epoch,
            "num_features": self.model.num_features,
            "num_classes": self.model.num_classes,
            "class_weights": self.class_weights.cpu().numpy().tolist()
            if self.class_weights is not None
            else None,
            "training_history": self.history.to_dict(),
            "metadata": extra_metadata or {},
        }

        torch.save(checkpoint, path)

        # Compute SHA-256 digest of saved file
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        digest = h.hexdigest()

        return path, digest

    def load_checkpoint(self, filepath: Path | str) -> dict[str, Any]:
        """Load checkpoint into the model."""
        path = Path(filepath)
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.best_val_loss = checkpoint.get("best_val_loss", float("inf"))
        self.best_epoch = checkpoint.get("best_epoch", -1)
        return checkpoint
