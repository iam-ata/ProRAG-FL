"""Pytest shared fixtures for ProRAG-FL test suite."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def sample_config_dict() -> dict[str, Any]:
    """Return a valid minimal experiment configuration dictionary."""
    return {
        "experiment": {
            "id": "test_exp_01",
            "description": "Unit testing experiment",
        },
        "dataset": {
            "name": "ciciot2023",
            "split_seed": 13,
            "held_out_family": "Mirai",
            "test_ratio": 0.20,
            "val_ratio": 0.10,
        },
        "model": {
            "name": "ids_1dcnn",
            "conv_channels": [64, 128, 256],
            "embedding_dim": 128,
            "dropout": 0.30,
        },
        "training": {
            "optimizer": "adamw",
            "lr": 0.001,
            "weight_decay": 0.0001,
            "batch_size": 256,
            "local_epochs": 2,
            "global_rounds": 50,
            "seed": 13,
        },
        "federated": {
            "num_clients": 10,
            "fraction_fit": 1.0,
            "partition": {
                "type": "dirichlet",
                "alpha": 0.3,
            },
            "strategy": {
                "name": "provenance_gated_trimmed_avg",
                "beta": 0.20,
            },
        },
        "attack": {
            "name": "none",
            "malicious_client_fraction": 0.0,
            "poison_budget": 0.0,
        },
        "rag": {
            "enabled": False,
            "embedding_model": "BAAI/bge-m3",
            "qdrant_url": "http://localhost:6333",
            "top_candidates": 20,
            "top_verified": 5,
            "require_merkle_proof": True,
        },
        "openai": {
            "enabled": False,
            "model": "gpt-4o-mini",
            "max_tokens": 1000,
            "temperature": 0.0,
        },
    }
