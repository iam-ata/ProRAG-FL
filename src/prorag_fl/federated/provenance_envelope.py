"""Provenance envelope generation, serialization, and cryptographic validation."""

from __future__ import annotations

import hashlib
import io
import uuid

import numpy as np

from prorag_fl.schemas.federated import ModelProvenanceEnvelope


def serialize_ndarrays(ndarrays: list[np.ndarray]) -> bytes:
    """Deterministically serialize a list of NumPy arrays to bytes."""
    buf = io.BytesIO()
    # Save number of arrays first
    buf.write(len(ndarrays).to_bytes(4, byteorder="big"))
    for arr in ndarrays:
        np.save(buf, np.ascontiguousarray(arr), allow_pickle=False)
    return buf.getvalue()


def compute_ndarrays_digest(ndarrays: list[np.ndarray]) -> str:
    """Compute deterministic SHA-256 digest of model parameters or update diff."""
    raw_bytes = serialize_ndarrays(ndarrays)
    return hashlib.sha256(raw_bytes).hexdigest()


def create_provenance_envelope(
    client_id: str,
    server_round: int,
    global_model_version: str,
    update_ndarrays: list[np.ndarray],
    num_examples: int,
    local_loss: float,
    local_accuracy: float,
    secret_key: str = "prorag_shared_secret",
    nonce: str | None = None,
) -> ModelProvenanceEnvelope:
    """Construct and sign a ModelProvenanceEnvelope."""
    update_digest = compute_ndarrays_digest(update_ndarrays)
    if nonce is None:
        nonce = uuid.uuid4().hex

    # Compute cryptographic provenance signature
    sig_payload = (
        f"{client_id}:{server_round}:{global_model_version}:{update_digest}:{nonce}:{secret_key}"
    )
    signature = hashlib.sha256(sig_payload.encode("utf-8")).hexdigest()

    return ModelProvenanceEnvelope(
        client_id=client_id,
        server_round=server_round,
        global_model_version=global_model_version,
        update_digest=update_digest,
        num_examples=num_examples,
        local_loss=float(local_loss),
        local_accuracy=float(local_accuracy),
        signature=signature,
        nonce=nonce,
        status="valid",
    )


class ProvenanceVerifier:
    """Verifies provenance, integrity, freshness, and anti-replay of model updates."""

    def __init__(
        self,
        authorized_client_ids: set[str] | list[str] | None = None,
        secret_key: str = "prorag_shared_secret",
    ) -> None:
        self.authorized_client_ids = (
            set(authorized_client_ids) if authorized_client_ids is not None else None
        )
        self.secret_key = secret_key
        self.seen_nonces: set[str] = set()

    def verify(
        self,
        envelope: ModelProvenanceEnvelope,
        expected_round: int,
        expected_model_version: str,
        update_ndarrays: list[np.ndarray] | None = None,
    ) -> tuple[bool, str]:
        """Validate envelope against security policies.

        Returns:
            Tuple of (is_valid: bool, reason: str).
        """
        # 1. Authorization check
        if (
            self.authorized_client_ids is not None
            and envelope.client_id not in self.authorized_client_ids
        ):
            return False, f"unauthorized_client:{envelope.client_id}"

        # 2. Lifecycle status check
        if envelope.status != "valid":
            return False, f"invalid_status:{envelope.status}"

        # 3. Round freshness check
        if envelope.server_round != expected_round:
            return False, f"stale_round:got_{envelope.server_round}_expected_{expected_round}"

        # 4. Global model version check
        if envelope.global_model_version != expected_model_version:
            return (
                False,
                f"version_mismatch:got_{envelope.global_model_version}_expected_{expected_model_version}",
            )

        # 5. Replay attack check
        if envelope.nonce in self.seen_nonces:
            return False, f"replay_nonce_detected:{envelope.nonce}"

        # 6. Update digest verification
        if update_ndarrays is not None:
            actual_digest = compute_ndarrays_digest(update_ndarrays)
            if actual_digest != envelope.update_digest:
                return (
                    False,
                    f"digest_tampered:got_{actual_digest}_expected_{envelope.update_digest}",
                )

        # 7. Signature verification
        expected_sig_payload = (
            f"{envelope.client_id}:{envelope.server_round}:{envelope.global_model_version}:"
            f"{envelope.update_digest}:{envelope.nonce}:{self.secret_key}"
        )
        expected_sig = hashlib.sha256(expected_sig_payload.encode("utf-8")).hexdigest()
        if envelope.signature != expected_sig:
            return False, "invalid_cryptographic_signature"

        # Record nonce to prevent future replay
        self.seen_nonces.add(envelope.nonce)
        return True, "verified"
