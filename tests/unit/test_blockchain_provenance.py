"""Unit tests and acceptance gates for Phase 5 Blockchain Model Provenance."""

from __future__ import annotations

import concurrent.futures
import hashlib
import uuid

import pytest

from prorag_fl.blockchain.benchmark import run_blockchain_benchmark
from prorag_fl.blockchain.mock_ledger import MockProvenanceLedger
from prorag_fl.schemas.blockchain import ModelUpdateRecord


@pytest.fixture
def ledger() -> MockProvenanceLedger:
    """Fixture providing a fresh mock Hyperledger Fabric ledger."""
    instance = MockProvenanceLedger()
    instance.register_client("client_0", msp_id="Org1MSP", is_authorized=True)
    instance.register_client("client_1", msp_id="Org2MSP", is_authorized=True)
    instance.register_client("client_2", msp_id="Org3MSP", is_authorized=True)
    return instance


@pytest.mark.unit
def test_valid_current_update_accepted(ledger: MockProvenanceLedger) -> None:
    """Gate P5: Valid current update must be accepted and committed to the ledger."""
    dummy_payload = b"valid_model_update_weights_123"
    update_sha256 = hashlib.sha256(dummy_payload).hexdigest()
    nonce = f"nonce_{uuid.uuid4().hex}"

    is_valid, reason = ledger.verify_update(
        client_id="client_0",
        server_round=1,
        global_model_version="v0",
        update_sha256=update_sha256,
        nonce=nonce,
    )
    assert is_valid is True
    assert reason == "verified"

    record = ModelUpdateRecord(
        update_id="update_001",
        client_id="client_0",
        round=1,
        global_model_version="v0",
        update_sha256=update_sha256,
        nonce=f"sub_{nonce}",
        num_examples=100,
        local_loss=0.45,
        local_accuracy=0.88,
    )
    receipt = ledger.submit_update(record)
    assert receipt.status == "COMMITTED"
    assert receipt.tx_bytes > 0
    assert receipt.block_number >= 1

    queried = ledger.query_update("update_001")
    assert queried is not None
    assert queried.update_id == "update_001"
    assert queried.status == "active"


@pytest.mark.unit
def test_duplicate_nonce_replay_rejected(ledger: MockProvenanceLedger) -> None:
    """Gate P5: Duplicate nonce reuse must be rejected (replay prevention)."""
    dummy_payload = b"update_payload"
    update_sha256 = hashlib.sha256(dummy_payload).hexdigest()
    reused_nonce = "fixed_nonce_12345"

    is_valid1, reason1 = ledger.verify_update(
        client_id="client_0",
        server_round=1,
        global_model_version="v0",
        update_sha256=update_sha256,
        nonce=reused_nonce,
    )
    assert is_valid1 is True

    # Replay attempt with same nonce
    is_valid2, reason2 = ledger.verify_update(
        client_id="client_0",
        server_round=1,
        global_model_version="v0",
        update_sha256=update_sha256,
        nonce=reused_nonce,
    )
    assert is_valid2 is False
    assert "duplicate_nonce_replay" in reason2


@pytest.mark.unit
def test_unauthorized_and_unknown_identity_rejected(ledger: MockProvenanceLedger) -> None:
    """Gate P5: Unknown or unauthorized client identity must be rejected."""
    dummy_sha256 = hashlib.sha256(b"weights").hexdigest()
    nonce = f"nonce_{uuid.uuid4().hex}"

    is_valid, reason = ledger.verify_update(
        client_id="rogue_intruder_99",
        server_round=1,
        global_model_version="v0",
        update_sha256=dummy_sha256,
        nonce=nonce,
    )
    assert is_valid is False
    assert "unauthorized_identity" in reason


@pytest.mark.unit
def test_revoked_client_rejected(ledger: MockProvenanceLedger) -> None:
    """Gate P5: Revoked client must be rejected immediately."""
    ledger.revoke_client("client_1", reason="malicious_model_poisoning_detected")

    dummy_sha256 = hashlib.sha256(b"weights").hexdigest()
    nonce = f"nonce_{uuid.uuid4().hex}"

    is_valid, reason = ledger.verify_update(
        client_id="client_1",
        server_round=1,
        global_model_version="v0",
        update_sha256=dummy_sha256,
        nonce=nonce,
    )
    assert is_valid is False
    assert "client_revoked" in reason


@pytest.mark.unit
def test_stale_round_and_wrong_version_rejected(ledger: MockProvenanceLedger) -> None:
    """Gate P5: Stale round or mismatched global model version must be rejected."""
    dummy_sha256 = hashlib.sha256(b"weights").hexdigest()

    # Wrong global model version
    is_valid_ver, reason_ver = ledger.verify_update(
        client_id="client_0",
        server_round=2,
        global_model_version="v99_incompatible",
        update_sha256=dummy_sha256,
        nonce=f"nonce_{uuid.uuid4().hex}",
    )
    assert is_valid_ver is False
    assert "wrong_global_version" in reason_ver

    # Stale round check: round t-1 (round 1) submitted at round t (round 2)
    nonce_stale = f"nonce_{uuid.uuid4().hex}"
    is_valid_stale, reason_stale = ledger.verify_update(
        client_id="client_0",
        server_round=1,
        global_model_version="v0",
        update_sha256=dummy_sha256,
        nonce=nonce_stale,
        expected_round=2,
    )
    assert is_valid_stale is False
    assert "stale_round_rejected" in reason_stale

    # Valid submission for round 1
    nonce1 = f"nonce_{uuid.uuid4().hex}"
    is_valid1, _ = ledger.verify_update(
        client_id="client_0",
        server_round=1,
        global_model_version="v0",
        update_sha256=dummy_sha256,
        nonce=nonce1,
    )
    assert is_valid1 is True

    # Commit round 1
    record = ModelUpdateRecord(
        update_id="up_client_0_r1",
        client_id="client_0",
        round=1,
        global_model_version="v0",
        update_sha256=dummy_sha256,
        nonce=f"sub_{nonce1}",
    )
    receipt = ledger.submit_update(record)
    assert receipt.status == "COMMITTED"

    # Same client attempts submitting round 1 again
    nonce2 = f"nonce_{uuid.uuid4().hex}"
    is_valid2, reason2 = ledger.verify_update(
        client_id="client_0",
        server_round=1,
        global_model_version="v0",
        update_sha256=dummy_sha256,
        nonce=nonce2,
    )
    assert is_valid2 is False
    assert "duplicate_submission_for_round" in reason2


@pytest.mark.unit
def test_atomic_concurrent_nonce_safety(ledger: MockProvenanceLedger) -> None:
    """Gate P5: Concurrent race condition with duplicate nonce must be atomic (no double-spend)."""
    dummy_sha256 = hashlib.sha256(b"weights").hexdigest()
    target_nonce = "concurrent_race_nonce_xyz"

    def try_verify(client_suffix: str) -> tuple[bool, str]:
        return ledger.verify_update(
            client_id="client_2",
            server_round=1,
            global_model_version="v0",
            update_sha256=dummy_sha256,
            nonce=target_nonce,
        )

    # Launch 10 concurrent threads trying to consume the EXACT same nonce simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(try_verify, str(i)) for i in range(10)]
        results = [f.result() for f in futures]

    accepted_count = sum(1 for is_valid, _ in results if is_valid)
    rejected_count = sum(1 for is_valid, _ in results if not is_valid)

    # Exactly ONE thread must succeed; all other 9 must be rejected
    assert accepted_count == 1
    assert rejected_count == 9


@pytest.mark.unit
def test_blockchain_benchmark_metrics(ledger: MockProvenanceLedger) -> None:
    """Gate P5: Benchmark transaction submit/query/verification latency, throughput, bytes."""
    metrics = run_blockchain_benchmark(
        backend=ledger,
        num_clients=5,
        num_rounds=3,
        payload_size_bytes=2048,
    )

    assert metrics["num_clients"] == 5
    assert metrics["num_rounds"] == 3
    assert metrics["total_transactions"] == 15
    assert metrics["throughput_tx_per_sec"] > 0.0
    assert metrics["submit_latency_ms"]["mean"] >= 0.0
    assert metrics["verify_latency_ms"]["mean"] >= 0.0
    assert metrics["query_latency_ms"]["mean"] >= 0.0
    assert metrics["total_tx_bytes"] > 0
    assert metrics["ledger_block_height"] > 1
