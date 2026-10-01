"""Utility helpers for IDS model training, class weighting, and dataset loaders."""

from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset


class TabularIDSDataset(Dataset):
    """PyTorch Dataset for preprocessed intrusion detection tabular data."""

    def __init__(
        self, features: np.ndarray | torch.Tensor, targets: np.ndarray | torch.Tensor
    ) -> None:
        if isinstance(features, np.ndarray):
            self.features = torch.from_numpy(features.astype(np.float32))
        else:
            self.features = features.float()

        if isinstance(targets, np.ndarray):
            self.targets = torch.from_numpy(targets.astype(np.int64))
        else:
            self.targets = targets.long()

        if len(self.features) != len(self.targets):
            raise ValueError(
                f"Features count ({len(self.features)}) does not match targets count ({len(self.targets)})"
            )

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.features[idx], self.targets[idx]


def compute_class_weights(
    labels: np.ndarray | torch.Tensor,
    num_classes: int,
    norm: bool = True,
) -> torch.Tensor:
    """Compute balanced class weights exclusively from training labels.

    Formula:
        w_c = N / (C * N_c)
    where N is total samples, C is number of active classes, and N_c is count of class c.

    Args:
        labels: 1D array of integer class labels.
        num_classes: Total number of classes.
        norm: Whether to normalize weights such that mean(weights) == 1.0.

    Returns:
        torch.FloatTensor of length num_classes.
    """
    if isinstance(labels, torch.Tensor):
        labels_arr = labels.cpu().numpy()
    else:
        labels_arr = np.asarray(labels)

    total_samples = len(labels_arr)
    weights = np.ones(num_classes, dtype=np.float32)

    unique, counts = np.unique(labels_arr, return_counts=True)
    count_dict = dict(zip(unique, counts, strict=True))

    active_classes = len(count_dict)
    if active_classes == 0 or total_samples == 0:
        return torch.ones(num_classes, dtype=torch.float32)

    for c in range(num_classes):
        c_count = count_dict.get(c, 0)
        if c_count > 0:
            weights[c] = total_samples / (active_classes * c_count)
        else:
            weights[c] = 0.0  # Zero weight for absent / held-out classes

    if norm and weights.sum() > 0:
        # Normalize non-zero weights
        non_zero_mask = weights > 0
        weights[non_zero_mask] = weights[non_zero_mask] / weights[non_zero_mask].mean()

    return torch.from_numpy(weights.astype(np.float32))


def create_ids_data_loader(
    features: np.ndarray | torch.Tensor,
    targets: np.ndarray | torch.Tensor,
    batch_size: int = 256,
    shuffle: bool = True,
    generator: torch.Generator | None = None,
    num_workers: int = 0,
) -> DataLoader:
    """Create a deterministic DataLoader for IDS training or evaluation."""
    dataset = TabularIDSDataset(features=features, targets=targets)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )
