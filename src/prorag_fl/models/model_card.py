"""Model card schema and generator for 1D-CNN IDS models conforming to 10_LOCAL_IDS_1DCNN.md."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from prorag_fl.core.environment import capture_environment
from prorag_fl.models.ids_1dcnn import IDS1DCNN


class ModelCard(BaseModel):
    """Immutable model card documenting architecture, training parameters, and lineage."""

    model_config = ConfigDict(extra="forbid")

    model_name: str = "IDS-1DCNN"
    dataset_name: str
    run_id: str
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())

    # Architecture
    num_features: int
    num_classes: int
    architecture_summary: str
    total_parameters: int
    trainable_parameters: int

    # Training & Loss
    optimizer: str = "AdamW"
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    batch_size: int = 256
    loss_function: str = "Class-Weighted CrossEntropyLoss"
    class_weights: list[float] | None = None
    classes: list[str]

    # Reproducibility & Lineage
    preprocessor_hash: str
    checkpoint_path: str
    checkpoint_digest: str
    seed: int

    # Performance & History
    best_epoch: int
    best_val_loss: float
    training_history: dict[str, list[float] | list[int]]

    # Hardware & Environment
    environment_snapshot: dict[str, Any] = Field(default_factory=dict)


def generate_model_card(
    model: IDS1DCNN,
    dataset_name: str,
    run_id: str,
    classes: list[str],
    preprocessor_hash: str,
    checkpoint_path: Path | str,
    checkpoint_digest: str,
    seed: int,
    training_history: dict[str, list[float] | list[int]],
    best_epoch: int,
    best_val_loss: float,
    class_weights: list[float] | None = None,
    output_path: Path | str | None = None,
) -> ModelCard:
    """Construct and optionally serialize an authoritative ModelCard."""
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    arch_summary = (
        "Conv1d(1,64,k=3,p=1)->BN->ReLU -> "
        "Conv1d(64,128,k=3,p=1)->BN->ReLU->MaxPool(2) -> "
        "Conv1d(128,256,k=3,p=1)->ReLU->AdaptiveAvgPool(1) -> "
        "Flatten->Linear(256,128)->ReLU->Dropout(0.30)->Linear(128,num_classes)"
    )

    env_snapshot = capture_environment()

    card = ModelCard(
        model_name="IDS-1DCNN",
        dataset_name=dataset_name,
        run_id=run_id,
        num_features=model.num_features,
        num_classes=model.num_classes,
        architecture_summary=arch_summary,
        total_parameters=total_params,
        trainable_parameters=trainable_params,
        classes=classes,
        class_weights=class_weights,
        preprocessor_hash=preprocessor_hash,
        checkpoint_path=str(checkpoint_path).replace("\\", "/"),
        checkpoint_digest=checkpoint_digest,
        seed=seed,
        best_epoch=best_epoch,
        best_val_loss=best_val_loss,
        training_history=training_history,
        environment_snapshot=env_snapshot,
    )

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(card.model_dump_json(indent=2), encoding="utf-8")

    return card
