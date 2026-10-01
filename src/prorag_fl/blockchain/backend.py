"""Abstract base interface for Blockchain Model-Update Provenance backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from prorag_fl.schemas.blockchain import (
    ClientIdentityRecord,
    LedgerStats,
    ModelUpdateRecord,
    ProvenanceTransactionReceipt,
)


class ProvenanceBackend(ABC):
    """Abstract interface defining the ledger contract for model update provenance."""

    @abstractmethod
    def register_client(
        self,
        client_id: str,
        msp_id: str = "Org1MSP",
        is_authorized: bool = True,
    ) -> ClientIdentityRecord:
        """Register a client identity on the blockchain ledger."""
        ...

    @abstractmethod
    def revoke_client(
        self,
        client_id: str,
        reason: str = "revoked_by_admin",
    ) -> ClientIdentityRecord:
        """Revoke a client identity on the blockchain ledger."""
        ...

    @abstractmethod
    def submit_update(
        self,
        record: ModelUpdateRecord,
    ) -> ProvenanceTransactionReceipt:
        """Submit a model update provenance record to be atomically committed to the ledger."""
        ...

    @abstractmethod
    def verify_update(
        self,
        client_id: str,
        server_round: int,
        global_model_version: str,
        update_sha256: str,
        nonce: str,
        expected_round: int | None = None,
    ) -> tuple[bool, str]:
        """Perform on-chain or ledger verification of candidate update against current round state.

        Returns (is_valid, reason) following the exact 9-step verification order:
        1. schema
        2. authenticated/authorized identity
        3. active lifecycle status (not revoked)
        4. digest match
        5. exact round
        6. exact global-model version
        7. nonce not consumed
        8. time policy (if enabled)
        9. atomically consume nonce upon acceptance
        """
        ...

    @abstractmethod
    def query_update(self, update_id: str) -> ModelUpdateRecord | None:
        """Query a committed model update record by update ID."""
        ...

    @abstractmethod
    def query_updates_by_round(self, server_round: int) -> list[ModelUpdateRecord]:
        """Query all committed updates for a specific federated round."""
        ...

    @abstractmethod
    def get_ledger_stats(self) -> LedgerStats:
        """Retrieve aggregated ledger performance statistics and transaction metrics."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset the ledger state (for test isolation and reproducible benchmarking)."""
        ...
