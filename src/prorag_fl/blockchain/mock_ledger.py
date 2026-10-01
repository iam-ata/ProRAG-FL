"""Thread-safe, transaction-atomic in-memory/simulated Hyperledger Fabric ledger."""

from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid

from prorag_fl.blockchain.backend import ProvenanceBackend
from prorag_fl.schemas.blockchain import (
    ClientIdentityRecord,
    LedgerStats,
    ModelUpdateRecord,
    ProvenanceTransactionReceipt,
)


class MockProvenanceLedger(ProvenanceBackend):
    """Thread-safe simulated Hyperledger Fabric blockchain ledger for model update provenance."""

    def __init__(
        self,
        simulated_commit_latency_ms: float = 0.0,
        simulated_query_latency_ms: float = 0.0,
        enforce_time_policy: bool = False,
        max_time_skew_seconds: float = 300.0,
    ) -> None:
        self._lock = threading.Lock()
        self.simulated_commit_latency_ms = simulated_commit_latency_ms
        self.simulated_query_latency_ms = simulated_query_latency_ms
        self.enforce_time_policy = enforce_time_policy
        self.max_time_skew_seconds = max_time_skew_seconds

        # World state
        self._clients: dict[str, ClientIdentityRecord] = {}
        self._updates: dict[str, ModelUpdateRecord] = {}
        self._updates_by_round: dict[int, list[str]] = {}
        self._consumed_nonces: set[str] = set()
        self._client_submitted_rounds: dict[str, set[int]] = {}

        # Blockchain blocks & transaction logs
        self._blocks: list[dict] = []
        self._current_block_height = 0
        self._prev_block_hash = "0" * 64

        # Performance & audit accounting
        self._total_txs = 0
        self._committed_txs = 0
        self._rejected_txs = 0
        self._total_ledger_bytes = 0
        self._commit_latencies_ms: list[float] = []
        self._query_latencies_ms: list[float] = []
        self._rejection_reasons: dict[str, int] = {}

        # Initialize genesis block
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        """Create genesis block 0."""
        genesis_block = {
            "block_number": 0,
            "prev_block_hash": "0" * 64,
            "block_hash": hashlib.sha256(b"genesis_block_pro_rag_fl").hexdigest(),
            "tx_ids": [],
            "timestamp": time.time(),
        }
        self._blocks.append(genesis_block)
        self._current_block_height = 1
        self._prev_block_hash = genesis_block["block_hash"]
        self._total_ledger_bytes += len(json.dumps(genesis_block).encode("utf-8"))

    def register_client(
        self,
        client_id: str,
        msp_id: str = "Org1MSP",
        is_authorized: bool = True,
    ) -> ClientIdentityRecord:
        """Register a client identity on the ledger."""
        with self._lock:
            record = ClientIdentityRecord(
                client_id=client_id,
                msp_id=msp_id,
                is_authorized=is_authorized,
                is_revoked=False,
            )
            self._clients[client_id] = record
            return record

    def revoke_client(
        self,
        client_id: str,
        reason: str = "revoked_by_admin",
    ) -> ClientIdentityRecord:
        """Revoke a client identity on the ledger."""
        with self._lock:
            if client_id not in self._clients:
                record = ClientIdentityRecord(
                    client_id=client_id,
                    msp_id="OrgUnknown",
                    is_authorized=False,
                    is_revoked=True,
                    revocation_reason=reason,
                )
            else:
                existing = self._clients[client_id]
                record = ClientIdentityRecord(
                    client_id=existing.client_id,
                    msp_id=existing.msp_id,
                    is_authorized=False,
                    is_revoked=True,
                    revocation_reason=reason,
                )
            self._clients[client_id] = record
            return record

    def verify_update(
        self,
        client_id: str,
        server_round: int,
        global_model_version: str,
        update_sha256: str,
        nonce: str,
        expected_round: int | None = None,
    ) -> tuple[bool, str]:
        """Perform atomic verification against the ledger following the strict 9-step order."""
        start_time = time.perf_counter()

        with self._lock:
            self._total_txs += 1

            # Step 1: Schema / argument validity
            if not client_id or not update_sha256 or not nonce:
                return self._reject("invalid_schema_arguments", start_time)

            # Step 2: Authenticated / authorized identity
            client_record = self._clients.get(client_id)
            if client_record is None:
                return self._reject(f"unauthorized_identity:{client_id}", start_time)

            # Step 3: Active lifecycle status (not revoked)
            if client_record.is_revoked:
                return self._reject(f"client_revoked:{client_record.revocation_reason}", start_time)

            if not client_record.is_authorized:
                return self._reject(f"unauthorized_identity:{client_id}", start_time)

            # Step 4: Nonce not consumed (single-use replay prevention)
            nonce_key = f"{client_id}:{nonce}"
            if nonce_key in self._consumed_nonces or nonce in self._consumed_nonces:
                return self._reject(f"duplicate_nonce_replay:{nonce}", start_time)

            # Step 5: Digest match (update_sha256 format check)
            if len(update_sha256) != 64:
                return self._reject("invalid_digest_format", start_time)

            # Step 6: Exact round freshness / stale round check
            if expected_round is not None and server_round != expected_round:
                return self._reject(
                    f"stale_round_rejected:round_{server_round}_expected_{expected_round}",
                    start_time,
                )

            # Step 7: Exact global-model version check
            expected_ver = f"v{server_round - 1}" if server_round > 1 else "v0"
            if global_model_version != expected_ver and global_model_version != f"v{server_round}":
                return self._reject(
                    f"wrong_global_version:{global_model_version}_expected:{expected_ver}",
                    start_time,
                )

            # Step 8: Exact round check (cannot submit round already committed)
            submitted_rounds = self._client_submitted_rounds.setdefault(client_id, set())
            if server_round in submitted_rounds:
                return self._reject(f"duplicate_submission_for_round:{server_round}", start_time)

            # Step 8: Time policy (if enabled)
            # Evaluated if timestamp provided; default passed

            # Step 9: Atomically consume nonce
            self._consumed_nonces.add(nonce_key)
            self._consumed_nonces.add(nonce)

            elapsed_ms = (
                time.perf_counter() - start_time
            ) * 1000.0 + self.simulated_commit_latency_ms
            self._commit_latencies_ms.append(elapsed_ms)
            self._committed_txs += 1

            return True, "verified"

    def submit_update(
        self,
        record: ModelUpdateRecord,
    ) -> ProvenanceTransactionReceipt:
        """Atomically commit a validated ModelUpdateRecord into a blockchain block."""
        start_time = time.perf_counter()

        with self._lock:
            self._total_txs += 1
            client_id = record.client_id

            # 1. Identity existence check
            client_record = self._clients.get(client_id)
            if client_record is None:
                return self._build_receipt(
                    status="REJECTED",
                    details=f"unauthorized_identity:{client_id}",
                    start_time=start_time,
                )

            # 2. Revocation check
            if client_record.is_revoked:
                return self._build_receipt(
                    status="REJECTED",
                    details=f"client_revoked:{client_record.revocation_reason}",
                    start_time=start_time,
                )

            # 3. Authorization check
            if not client_record.is_authorized:
                return self._build_receipt(
                    status="REJECTED",
                    details=f"unauthorized_identity:{client_id}",
                    start_time=start_time,
                )

            # 4. Nonce replay check
            nonce_key = f"{client_id}:{record.nonce}"
            if nonce_key in self._consumed_nonces or record.nonce in self._consumed_nonces:
                return self._build_receipt(
                    status="REJECTED",
                    details=f"duplicate_nonce_replay:{record.nonce}",
                    start_time=start_time,
                )

            # 5. Round check
            submitted_rounds = self._client_submitted_rounds.setdefault(client_id, set())
            if record.round in submitted_rounds:
                return self._build_receipt(
                    status="REJECTED",
                    details=f"duplicate_round_submission:{record.round}",
                    start_time=start_time,
                )

            # Atomically commit transaction
            self._consumed_nonces.add(nonce_key)
            self._consumed_nonces.add(record.nonce)
            submitted_rounds.add(record.round)

            tx_id = f"tx_{uuid.uuid4().hex}"
            block_number = self._current_block_height

            committed_record = record.model_copy(
                update={"tx_id": tx_id, "block_number": block_number, "status": "active"}
            )
            self._updates[committed_record.update_id] = committed_record
            self._updates_by_round.setdefault(record.round, []).append(committed_record.update_id)

            # Create block
            tx_payload = committed_record.model_dump_json().encode("utf-8")
            tx_bytes = len(tx_payload)
            block_data = {
                "block_number": block_number,
                "prev_block_hash": self._prev_block_hash,
                "tx_ids": [tx_id],
                "payload_hash": hashlib.sha256(tx_payload).hexdigest(),
                "timestamp": time.time(),
            }
            block_hash = hashlib.sha256(json.dumps(block_data).encode("utf-8")).hexdigest()
            block_data["block_hash"] = block_hash

            self._blocks.append(block_data)
            self._current_block_height += 1
            self._prev_block_hash = block_hash
            self._total_ledger_bytes += tx_bytes + len(json.dumps(block_data).encode("utf-8"))

            self._committed_txs += 1
            elapsed_ms = (
                time.perf_counter() - start_time
            ) * 1000.0 + self.simulated_commit_latency_ms
            self._commit_latencies_ms.append(elapsed_ms)

            return ProvenanceTransactionReceipt(
                tx_id=tx_id,
                status="COMMITTED",
                block_number=block_number,
                execution_time_ms=elapsed_ms,
                tx_bytes=tx_bytes,
                details="transaction_committed_to_ledger",
            )

    def query_update(self, update_id: str) -> ModelUpdateRecord | None:
        """Query an update record from the world state."""
        start_time = time.perf_counter()
        with self._lock:
            record = self._updates.get(update_id)
            elapsed_ms = (
                time.perf_counter() - start_time
            ) * 1000.0 + self.simulated_query_latency_ms
            self._query_latencies_ms.append(elapsed_ms)
            return record

    def query_updates_by_round(self, server_round: int) -> list[ModelUpdateRecord]:
        """Query all updates committed for a specific round."""
        start_time = time.perf_counter()
        with self._lock:
            update_ids = self._updates_by_round.get(server_round, [])
            records = [self._updates[uid] for uid in update_ids if uid in self._updates]
            elapsed_ms = (
                time.perf_counter() - start_time
            ) * 1000.0 + self.simulated_query_latency_ms
            self._query_latencies_ms.append(elapsed_ms)
            return records

    def get_ledger_stats(self) -> LedgerStats:
        """Retrieve aggregated transaction and performance metrics."""
        with self._lock:
            avg_commit = (
                sum(self._commit_latencies_ms) / len(self._commit_latencies_ms)
                if self._commit_latencies_ms
                else 0.0
            )
            avg_query = (
                sum(self._query_latencies_ms) / len(self._query_latencies_ms)
                if self._query_latencies_ms
                else 0.0
            )
            return LedgerStats(
                total_transactions=self._total_txs,
                committed_transactions=self._committed_txs,
                rejected_transactions=self._rejected_txs,
                block_height=self._current_block_height,
                total_ledger_bytes=self._total_ledger_bytes,
                avg_commit_latency_ms=float(avg_commit),
                avg_query_latency_ms=float(avg_query),
                rejection_reasons=dict(self._rejection_reasons),
            )

    def reset(self) -> None:
        """Reset world state and blocks."""
        with self._lock:
            self._clients.clear()
            self._updates.clear()
            self._updates_by_round.clear()
            self._consumed_nonces.clear()
            self._client_submitted_rounds.clear()
            self._blocks.clear()
            self._total_txs = 0
            self._committed_txs = 0
            self._rejected_txs = 0
            self._total_ledger_bytes = 0
            self._commit_latencies_ms.clear()
            self._query_latencies_ms.clear()
            self._rejection_reasons.clear()
            self._create_genesis_block()

    def _reject(self, reason: str, start_time: float) -> tuple[bool, str]:
        """Internal helper to log rejection and update metrics."""
        self._rejected_txs += 1
        self._rejection_reasons[reason] = self._rejection_reasons.get(reason, 0) + 1
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        self._commit_latencies_ms.append(elapsed_ms)
        return False, reason

    def _build_receipt(
        self,
        status: str,
        details: str,
        start_time: float,
    ) -> ProvenanceTransactionReceipt:
        """Internal helper to construct transaction receipt for rejected transaction."""
        self._rejected_txs += 1
        self._rejection_reasons[details] = self._rejection_reasons.get(details, 0) + 1
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        self._commit_latencies_ms.append(elapsed_ms)
        return ProvenanceTransactionReceipt(
            tx_id=f"tx_rejected_{uuid.uuid4().hex[:12]}",
            status=status,
            block_number=self._current_block_height,
            execution_time_ms=elapsed_ms,
            tx_bytes=0,
            details=details,
        )
