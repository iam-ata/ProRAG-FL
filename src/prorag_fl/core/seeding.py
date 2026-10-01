"""Deterministic seeding utilities for Python, NumPy, and PyTorch."""

from __future__ import annotations

import os
import random

import numpy as np
import torch

# Standard seeds specified across the research protocol
PRIMARY_SEEDS: tuple[int, ...] = (13, 37, 73, 101, 211)


def set_seed(seed: int, deterministic: bool = True) -> None:
    """Set random seed for Python, NumPy, and PyTorch across CPU and GPU.

    Args:
        seed: Integer seed value.
        deterministic: If True, configure PyTorch and cuDNN for deterministic operations.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        # Set deterministic algorithms with warn_only=True to prevent crashes on non-implemented ops
        try:
            torch.use_deterministic_algorithms(True, warn_only=True)
        except Exception:
            pass


def is_primary_seed(seed: int) -> bool:
    """Check if seed is in the primary evaluation seed set."""
    return seed in PRIMARY_SEEDS


def get_primary_seeds() -> tuple[int, ...]:
    """Return the frozen tuple of primary research seeds."""
    return PRIMARY_SEEDS
