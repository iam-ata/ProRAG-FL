"""Unit tests and acceptance smoke tests for Phase 4 Federated Learning."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from flwr.common import (
    Code,
    FitRes,
    Status,
    ndarrays_to_parameters,
)

from prorag_fl.core.seeding import set_seed
from prorag_fl.federated.client import FlowerIDSClient
from prorag_fl.federated.provenance_envelope import (
    ProvenanceVerifier,
    create_provenance_envelope,
)
from prorag_fl.federated.simulation import run_fl_simulation
from prorag_fl.federated.strategies import (
    ProvenanceGatedFedTrimmedAvg,
)
from prorag_fl.models.ids_1dcnn import IDS1DCNN
from prorag_fl.models.utils import create_ids_data_loader


@pytest.fixture
def mock_ndarrays() -> list[np.ndarray]:
    """Mock model weights."""
    return [
        np.ones((64, 1, 3), dtype=np.float32) * 0.1,
        np.zeros(64, dtype=np.float32),
        np.ones((8, 128), dtype=np.float32) * 0.05,
    ]


@pytest.fixture
def mock_client_data() -> tuple[
    dict[int, tuple[np.ndarray, np.ndarray]],
    dict[int, tuple[np.ndarray, np.ndarray]],
    tuple[np.ndarray, np.ndarray],
]:
    """Synthetic partitioned dataset for 3 clients."""
    rng = np.random.default_rng(42)
    num_features = 16
    num_classes = 4

    train_data = {}
    val_data = {}

    for i in range(3):
        x_tr = rng.standard_normal((60, num_features)).astype(np.float32)
        y_tr = rng.integers(0, num_classes, size=60).astype(np.int64)
        x_va = rng.standard_normal((20, num_features)).astype(np.float32)
        y_va = rng.integers(0, num_classes, size=20).astype(np.int64)
        train_data[i] = (x_tr, y_tr)
        val_data[i] = (x_va, y_va)

    global_x = rng.standard_normal((50, num_features)).astype(np.float32)
    global_y = rng.integers(0, num_classes, size=50).astype(np.int64)

    return train_data, val_data, (global_x, global_y)


@pytest.mark.unit
def test_provenance_envelope_verification(mock_ndarrays: list[np.ndarray]) -> None:
    """Verify cryptographic provenance envelope creation, digest matching, and security checks."""
    verifier = ProvenanceVerifier(authorized_client_ids=["client_0", "client_1"])

    # 1. Valid envelope
    envelope = create_provenance_envelope(
        client_id="client_0",
        server_round=1,
        global_model_version="v0",
        update_ndarrays=mock_ndarrays,
        num_examples=100,
        local_loss=0.45,
        local_accuracy=0.88,
        nonce="nonce_unique_1",
    )
    is_valid, reason = verifier.verify(
        envelope=envelope,
        expected_round=1,
        expected_model_version="v0",
        update_ndarrays=mock_ndarrays,
    )
    assert is_valid is True
    assert reason == "verified"

    # 2. Replay attack rejection (same nonce reused)
    is_valid_replay, reason_replay = verifier.verify(
        envelope=envelope,
        expected_round=1,
        expected_model_version="v0",
        update_ndarrays=mock_ndarrays,
    )
    assert is_valid_replay is False
    assert "replay_nonce_detected" in reason_replay

    # 3. Unauthorized client rejection
    unauth_env = create_provenance_envelope(
        client_id="rogue_client_99",
        server_round=1,
        global_model_version="v0",
        update_ndarrays=mock_ndarrays,
        num_examples=100,
        local_loss=0.5,
        local_accuracy=0.8,
        nonce="nonce_unique_2",
    )
    is_valid_unauth, reason_unauth = verifier.verify(
        envelope=unauth_env,
        expected_round=1,
        expected_model_version="v0",
        update_ndarrays=mock_ndarrays,
    )
    assert is_valid_unauth is False
    assert "unauthorized_client" in reason_unauth

    # 4. Tampered update digest rejection
    tampered_ndarrays = [arr * 2.0 for arr in mock_ndarrays]
    is_valid_tampered, reason_tampered = verifier.verify(
        envelope=create_provenance_envelope(
            client_id="client_1",
            server_round=1,
            global_model_version="v0",
            update_ndarrays=mock_ndarrays,
            num_examples=100,
            local_loss=0.5,
            local_accuracy=0.8,
            nonce="nonce_unique_3",
        ),
        expected_round=1,
        expected_model_version="v0",
        update_ndarrays=tampered_ndarrays,
    )
    assert is_valid_tampered is False
    assert "digest_tampered" in reason_tampered


@pytest.mark.unit
def test_flower_client_local_training() -> None:
    """Verify FlowerIDSClient fits local parameters, tracks communication bytes, and signs envelope."""
    set_seed(13)
    num_features = 16
    num_classes = 4

    x_tr = np.random.randn(40, num_features).astype(np.float32)
    y_tr = np.random.randint(0, num_classes, size=40).astype(np.int64)
    x_va = np.random.randn(20, num_features).astype(np.float32)
    y_va = np.random.randint(0, num_classes, size=20).astype(np.int64)

    tr_loader = create_ids_data_loader(x_tr, y_tr, batch_size=16)
    va_loader = create_ids_data_loader(x_va, y_va, batch_size=16)

    model = IDS1DCNN(num_features=num_features, num_classes=num_classes)
    client = FlowerIDSClient(
        client_id="client_test",
        model=model,
        train_loader=tr_loader,
        val_loader=va_loader,
        local_epochs=1,
    )

    init_params = client.get_parameters(config={})
    updated_params, num_samples, metrics = client.fit(
        parameters=init_params,
        config={"server_round": 1, "global_model_version": "v0"},
    )

    assert len(updated_params) == len(init_params)
    assert num_samples == 40
    assert metrics["update_bytes"] > 0
    assert metrics["metadata_bytes"] > 0
    assert "provenance_envelope_json" in metrics

    loss, count, eval_metrics = client.evaluate(updated_params, config={})
    assert loss > 0.0
    assert count == 20
    assert "val_acc" in eval_metrics


@pytest.mark.unit
def test_provenance_gated_strategy_rejection_and_insufficient_clients(
    mock_ndarrays: list[np.ndarray],
) -> None:
    """Verify ProvenanceGatedFedTrimmedAvg rejects invalid updates and refuses silent FedAvg fallback."""
    verifier = ProvenanceVerifier(authorized_client_ids=["client_0", "client_1"])
    strategy = ProvenanceGatedFedTrimmedAvg(
        verifier=verifier,
        beta=0.20,
        min_accepted_clients=2,
    )

    client_proxy_0 = MagicMock()
    client_proxy_0.cid = "client_0"
    client_proxy_1 = MagicMock()
    client_proxy_1.cid = "client_1"

    # Client 0 sends valid update
    env_0 = create_provenance_envelope(
        client_id="client_0",
        server_round=1,
        global_model_version="v0",
        update_ndarrays=mock_ndarrays,
        num_examples=100,
        local_loss=0.5,
        local_accuracy=0.8,
        nonce="nonce_test_0",
    )
    fit_res_0 = FitRes(
        status=Status(code=Code.OK, message="Success"),
        parameters=ndarrays_to_parameters(mock_ndarrays),
        num_examples=100,
        metrics={"client_id": "client_0", "provenance_envelope_json": env_0.model_dump_json()},
    )

    # Client 1 sends stale round update (round 99 instead of 1)
    env_1 = create_provenance_envelope(
        client_id="client_1",
        server_round=99,
        global_model_version="v0",
        update_ndarrays=mock_ndarrays,
        num_examples=100,
        local_loss=0.5,
        local_accuracy=0.8,
        nonce="nonce_test_1",
    )
    fit_res_1 = FitRes(
        status=Status(code=Code.OK, message="Success"),
        parameters=ndarrays_to_parameters(mock_ndarrays),
        num_examples=100,
        metrics={"client_id": "client_1", "provenance_envelope_json": env_1.model_dump_json()},
    )

    results = [(client_proxy_0, fit_res_0), (client_proxy_1, fit_res_1)]
    aggregated_params, metrics = strategy.aggregate_fit(
        server_round=1,
        results=results,
        failures=[],
    )

    # Since only 1 client passed and min_accepted_clients=2:
    # Must emit INSUFFICIENT_ELIGIBLE_CLIENTS and NOT silently aggregate
    assert metrics["status"] == "INSUFFICIENT_ELIGIBLE_CLIENTS"
    assert metrics["num_accepted"] == 1
    assert metrics["num_rejected"] == 1
    assert aggregated_params is None


@pytest.mark.unit
@pytest.mark.parametrize("strat_name", ["fedavg", "fedtrimmedavg", "multikrum", "provenance_gated"])
def test_3_client_2_round_smoke_simulation_all_strategies(
    strat_name: str,
    mock_client_data: tuple[
        dict[int, tuple[np.ndarray, np.ndarray]],
        dict[int, tuple[np.ndarray, np.ndarray]],
        tuple[np.ndarray, np.ndarray],
    ],
) -> None:
    """Acceptance Gate P4: 3-client, 2-round smoke simulation for all control strategies."""
    train_data, val_data, global_val = mock_client_data
    num_features = 16
    num_classes = 4

    with tempfile.TemporaryDirectory() as tmp_dir:
        result = run_fl_simulation(
            strategy_name=strat_name,
            dataset_name="smoke_test_ds",
            num_clients=3,
            num_rounds=2,
            client_train_data=train_data,
            client_val_data=val_data,
            global_val_data=global_val,
            num_features=num_features,
            num_classes=num_classes,
            local_epochs=1,
            seed=13,
            checkpoint_dir=tmp_dir,
        )

        assert result.strategy_name == strat_name
        assert result.num_clients == 3
        assert result.num_rounds == 2
        assert len(result.round_logs) == 2
        assert result.total_model_bytes > 0
        assert result.final_checkpoint_path != ""
        assert Path(result.final_checkpoint_path).exists()
