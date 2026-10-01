"""Benchmarking suite for Blockchain Model-Update Provenance overheads."""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any

from prorag_fl.blockchain.backend import ProvenanceBackend
from prorag_fl.schemas.blockchain import ModelUpdateRecord


def run_blockchain_benchmark(
    backend: ProvenanceBackend,
    num_clients: int = 10,
    num_rounds: int = 5,
    payload_size_bytes: int = 4096,
) -> dict[str, Any]:
    """Benchmark transaction submit/query/verification latency, throughput, and ledger growth.

    Adheres strictly to instructions/13_BLOCKCHAIN_AND_MODEL_PROVENANCE.md:
    "Transaction submit/query/verification latency, throughput, transaction bytes, ledger growth.
    Keep blockchain time separate from ML aggregation time."
    """
    backend.reset()

    # 1. Register clients
    client_ids = [f"client_{i}" for i in range(num_clients)]
    for cid in client_ids:
        backend.register_client(client_id=cid, msp_id="Org1MSP", is_authorized=True)

    submit_latencies_ms: list[float] = []
    verify_latencies_ms: list[float] = []
    query_latencies_ms: list[float] = []
    total_tx_bytes = 0

    total_start = time.perf_counter()

    for r in range(1, num_rounds + 1):
        global_version = f"v{r - 1}" if r > 1 else "v0"

        for cid in client_ids:
            # Generate deterministic synthetic update payload digest
            dummy_payload = f"model_update_{cid}_round_{r}".encode() + b"0" * (
                payload_size_bytes - 32
            )
            update_digest = hashlib.sha256(dummy_payload).hexdigest()
            nonce = f"nonce_{cid}_r{r}_{uuid.uuid4().hex[:8]}"

            # Verification timing
            v_start = time.perf_counter()
            is_valid, reason = backend.verify_update(
                client_id=cid,
                server_round=r,
                global_model_version=global_version,
                update_sha256=update_digest,
                nonce=nonce,
            )
            v_elapsed = (time.perf_counter() - v_start) * 1000.0
            verify_latencies_ms.append(v_elapsed)
            assert is_valid, f"Verification failed unexpectedly for {cid}: {reason}"

            # Submission / commit timing
            record = ModelUpdateRecord(
                update_id=f"up_{cid}_r{r}",
                client_id=cid,
                round=r,
                global_model_version=global_version,
                update_sha256=update_digest,
                nonce=f"sub_{nonce}",
                num_examples=256,
                local_loss=0.35,
                local_accuracy=0.92,
            )
            s_start = time.perf_counter()
            receipt = backend.submit_update(record)
            s_elapsed = (time.perf_counter() - s_start) * 1000.0
            submit_latencies_ms.append(s_elapsed)
            total_tx_bytes += receipt.tx_bytes

            # Query timing
            q_start = time.perf_counter()
            retrieved = backend.query_update(record.update_id)
            q_elapsed = (time.perf_counter() - q_start) * 1000.0
            query_latencies_ms.append(q_elapsed)
            assert retrieved is not None, f"Query failed to find update {record.update_id}"

    total_wall_time = time.perf_counter() - total_start
    total_tx_count = num_clients * num_rounds
    throughput_tps = total_tx_count / max(total_wall_time, 1e-6)

    stats = backend.get_ledger_stats()

    return {
        "num_clients": num_clients,
        "num_rounds": num_rounds,
        "total_transactions": total_tx_count,
        "throughput_tx_per_sec": round(throughput_tps, 2),
        "total_wall_time_seconds": round(total_wall_time, 4),
        "submit_latency_ms": {
            "mean": round(float(sum(submit_latencies_ms) / len(submit_latencies_ms)), 3),
            "min": round(float(min(submit_latencies_ms)), 3),
            "max": round(float(max(submit_latencies_ms)), 3),
        },
        "verify_latency_ms": {
            "mean": round(float(sum(verify_latencies_ms) / len(verify_latencies_ms)), 3),
            "min": round(float(min(verify_latencies_ms)), 3),
            "max": round(float(max(verify_latencies_ms)), 3),
        },
        "query_latency_ms": {
            "mean": round(float(sum(query_latencies_ms) / len(query_latencies_ms)), 3),
            "min": round(float(min(query_latencies_ms)), 3),
            "max": round(float(max(query_latencies_ms)), 3),
        },
        "total_tx_bytes": total_tx_bytes,
        "avg_bytes_per_tx": round(total_tx_bytes / max(total_tx_count, 1), 2),
        "ledger_block_height": stats.block_height,
        "total_ledger_bytes": stats.total_ledger_bytes,
    }
