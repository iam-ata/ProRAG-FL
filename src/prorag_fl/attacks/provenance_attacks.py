"""Provenance and Blockchain-Layer Adversarial Attacks.

Simulates adversarial tampering with federated model provenance records:
- Payload hash tampering after registration.
- Duplicate nonce replay attacks.
- Stale round update submission.
- Wrong global model version training.
- Unauthorized / Sybil client identity injection.
- Revoked client certificate exploitation.

Adheres strictly to instructions/18_ATTACKS_AND_THREAT_MODEL.md.
"""

from __future__ import annotations

import hashlib
import uuid

from prorag_fl.attacks.schemas import AttackManifest
from prorag_fl.schemas.federated import ModelProvenanceEnvelope


class ProvenanceAttacker:
    """Generates adversarial provenance envelopes testing blockchain ledger verification."""

    @staticmethod
    def create_tampered_payload_envelope(
        valid_envelope: ModelProvenanceEnvelope,
    ) -> tuple[ModelProvenanceEnvelope, AttackManifest]:
        """Tamper with the parameter update digest after signature/ledger registration."""
        tampered = valid_envelope.model_copy(
            update={"update_digest": hashlib.sha256(b"tampered_weights_payload").hexdigest()}
        )
        manifest = AttackManifest(
            attack_id=f"atk_prov_tamp_{uuid.uuid4().hex[:8]}",
            attack_type="provenance_tampering",
            malicious_client_ids=[valid_envelope.client_id],
            config_hash=hashlib.sha256(b"provenance_tampering").hexdigest()[:16],
            parameters={"target_field": "update_digest"},
        )
        return tampered, manifest

    @staticmethod
    def create_replay_nonce_envelope(
        valid_envelope: ModelProvenanceEnvelope,
        replayed_nonce: str,
    ) -> tuple[ModelProvenanceEnvelope, AttackManifest]:
        """Replay an already consumed nonce to test replay protection."""
        replayed = valid_envelope.model_copy(update={"nonce": replayed_nonce})
        manifest = AttackManifest(
            attack_id=f"atk_prov_rep_{uuid.uuid4().hex[:8]}",
            attack_type="replay_nonce",
            malicious_client_ids=[valid_envelope.client_id],
            config_hash=hashlib.sha256(b"replay_nonce").hexdigest()[:16],
            parameters={"replayed_nonce": replayed_nonce},
        )
        return replayed, manifest

    @staticmethod
    def create_stale_round_envelope(
        valid_envelope: ModelProvenanceEnvelope,
        stale_round: int = 0,
    ) -> tuple[ModelProvenanceEnvelope, AttackManifest]:
        """Submit an update with a stale/obsolete server round index."""
        stale = valid_envelope.model_copy(update={"server_round": stale_round})
        manifest = AttackManifest(
            attack_id=f"atk_prov_stale_{uuid.uuid4().hex[:8]}",
            attack_type="stale_round",
            malicious_client_ids=[valid_envelope.client_id],
            config_hash=hashlib.sha256(b"stale_round").hexdigest()[:16],
            parameters={"stale_round": stale_round},
        )
        return stale, manifest

    @staticmethod
    def create_unauthorized_client_envelope(
        valid_envelope: ModelProvenanceEnvelope,
        fake_client_id: str = "sybil_adversary_node_999",
    ) -> tuple[ModelProvenanceEnvelope, AttackManifest]:
        """Submit an update with an unauthorized / unregistered client identifier."""
        unauth = valid_envelope.model_copy(update={"client_id": fake_client_id})
        manifest = AttackManifest(
            attack_id=f"atk_prov_unauth_{uuid.uuid4().hex[:8]}",
            attack_type="unauthorized_identity",
            malicious_client_ids=[fake_client_id],
            config_hash=hashlib.sha256(b"unauthorized_identity").hexdigest()[:16],
            parameters={"fake_client_id": fake_client_id},
        )
        return unauth, manifest
