"""Unit tests and acceptance gates for Phase 6 Knowledge Ingestion and Merkle Provenance."""

from __future__ import annotations

import hashlib
import tempfile

import pytest

from prorag_fl.knowledge.adapters.cisa import CisaKevAdapter
from prorag_fl.knowledge.adapters.consortium import ConsortiumIncidentAdapter
from prorag_fl.knowledge.adapters.mitre import MitreAttackAdapter
from prorag_fl.knowledge.adapters.nvd import NvdCveAdapter
from prorag_fl.knowledge.canonicalizer import canonicalize_text, compute_canonical_hash
from prorag_fl.knowledge.chunker import DeterministicChunker
from prorag_fl.knowledge.manager import KnowledgeManager
from prorag_fl.knowledge.merkle import MerkleTree, hash_internal, verify_merkle_proof
from prorag_fl.knowledge.object_store import KnowledgeObjectStore
from prorag_fl.schemas.knowledge import MerkleProofStep


@pytest.mark.unit
def test_canonicalizer_determinism_and_normalization() -> None:
    """Verify Unicode NFC, line endings, and whitespace cleanup produce deterministic hashes."""
    text1 = "Line 1   \r\nLine 2\r\n\r\n\r\nLine 3 \t "
    text2 = "Line 1\nLine 2\n\nLine 3"

    canon1 = canonicalize_text(text1)
    canon2 = canonicalize_text(text2)

    assert canon1 == canon2
    assert compute_canonical_hash(text1) == compute_canonical_hash(text2)


@pytest.mark.unit
def test_merkle_tree_fixed_vectors_and_odd_leaf_handling() -> None:
    """Verify Merkle tree construction with odd leaves, proof generation, and verification."""
    leaf_a = hashlib.sha256(b"chunk_A").hexdigest()
    leaf_b = hashlib.sha256(b"chunk_B").hexdigest()
    leaf_c = hashlib.sha256(b"chunk_C").hexdigest()

    # 3 leaves (odd count): leaf_c should duplicate itself at level 0
    tree = MerkleTree([leaf_a, leaf_b, leaf_c])

    parent_ab = hash_internal(leaf_a, leaf_b)
    parent_cc = hash_internal(leaf_c, leaf_c)
    expected_root = hash_internal(parent_ab, parent_cc)

    assert tree.root == expected_root

    # Verify proofs for each leaf
    for idx in range(3):
        proof = tree.get_proof(idx)
        assert len(proof) == 2
        leaf_hash = [leaf_a, leaf_b, leaf_c][idx]
        assert verify_merkle_proof(leaf_hash, proof, expected_root) is True


@pytest.mark.unit
def test_deterministic_chunking_reproducibility() -> None:
    """Verify chunker produces bit-identical chunk counts, offsets, and hashes across runs."""
    doc_text = (
        "Adversaries may use PowerShell commands and scripts for execution. "
        "PowerShell is a powerful interactive command-line interface and scripting environment. "
        "It can be used to execute arbitrary code, download malicious payloads, "
        "and establish persistence within Cloud and IoT enterprise nodes. "
    ) * 10

    chunker = DeterministicChunker(chunk_size=200, chunk_overlap=30)
    chunks1 = chunker.chunk_document("doc_01", "v1.0.0", doc_text)
    chunks2 = chunker.chunk_document("doc_01", "v1.0.0", doc_text)

    assert len(chunks1) > 1
    assert len(chunks1) == len(chunks2)

    for c1, c2 in zip(chunks1, chunks2, strict=True):
        assert c1.chunk_id == c2.chunk_id
        assert c1.chunk_hash == c2.chunk_hash
        assert c1.canonical_text == c2.canonical_text
        assert c1.start_char_offset == c2.start_char_offset
        assert c1.end_char_offset == c2.end_char_offset


@pytest.mark.unit
def test_all_source_adapters_parsing() -> None:
    """Verify modular adapters parse MITRE ATT&CK, NVD CVE, CISA KEV, and Consortium memory."""
    # 1. MITRE ATT&CK
    mitre_adapter = MitreAttackAdapter()
    mitre_doc = mitre_adapter.parse_document(
        raw_data={
            "technique_id": "T1059.001",
            "name": "PowerShell",
            "description": "Adversaries may abuse PowerShell commands for execution.",
            "tactics": ["Execution"],
        }
    )
    assert mitre_doc.source_id == "mitre_attack"
    assert mitre_doc.document_id == "t1059_001"
    assert "PowerShell" in mitre_doc.title

    # 2. NVD CVE
    nvd_adapter = NvdCveAdapter()
    nvd_doc = nvd_adapter.parse_document(
        raw_data={
            "cve_id": "CVE-2023-12345",
            "description": "Buffer overflow in IoT firmware gateway.",
            "cvss_score": 9.8,
            "severity": "CRITICAL",
        }
    )
    assert nvd_doc.source_id == "nvd_cve"
    assert nvd_doc.document_id == "cve_2023_12345"
    assert "CRITICAL" in nvd_doc.title

    # 3. CISA KEV
    cisa_adapter = CisaKevAdapter()
    cisa_doc = cisa_adapter.parse_document(
        raw_data={
            "cveID": "CVE-2022-9999",
            "vendorProject": "EdgeRouter",
            "product": "Firmware OS",
            "vulnerabilityName": "Remote Code Execution",
            "shortDescription": "Actively exploited in the wild against industrial systems.",
        }
    )
    assert cisa_doc.source_id == "cisa_kev"
    assert "EdgeRouter" in cisa_doc.title

    # 4. Consortium Incident Memory
    consortium_adapter = ConsortiumIncidentAdapter()
    consortium_doc = consortium_adapter.parse_document(
        raw_data={
            "incident_id": "INC-2024-001",
            "title": "Mirai botnet brute-force surge on telemetry nodes",
            "target_system": "Industrial IoT MQTT broker",
            "narrative": "Coordinated Mirai brute force attempts detected from compromised sensors.",
        }
    )
    assert consortium_doc.source_id == "consortium_incident_memory"
    assert consortium_doc.document_id == "inc_2024_001"


@pytest.mark.unit
def test_object_store_immutability() -> None:
    """Verify object store rejects overwrite with different payload under same provenance key."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = KnowledgeObjectStore(storage_dir=tmp_dir)

        adapter = MitreAttackAdapter()
        doc = adapter.parse_document("Initial payload text", version="v1.0.0")
        key = store.put_document(doc)
        assert store.exists(doc.source_id, doc.document_id, doc.version, doc.content_sha256) is True

        # Retrieving object
        retrieved = store.get_document(
            doc.source_id, doc.document_id, doc.version, doc.content_sha256
        )
        assert retrieved is not None
        assert retrieved.content == doc.content

        # Attempting overwrite with same content succeeds idempotently
        key_again = store.put_document(doc)
        assert key_again == key

        # Attempting overwrite with different content raises ValueError
        tampered_doc = doc.model_copy(update={"title": "Tampered Title"})
        with pytest.raises(ValueError, match="Immutability violation"):
            store.put_document(tampered_doc)


@pytest.mark.unit
def test_acceptance_gate_p6_tamper_detection_and_lifecycle() -> None:
    """Acceptance Gate P6: Deterministic chunks/root, tampered proof fails, version/revocation works."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = KnowledgeObjectStore(storage_dir=tmp_dir)
        manager = KnowledgeManager(object_store=store, chunk_size=150, chunk_overlap=20)
        adapter = MitreAttackAdapter()

        # 1. Ingest initial version 1
        raw_v1 = {
            "technique_id": "T1046",
            "name": "Network Service Discovery",
            "description": (
                "Adversaries may attempt to get a listing of services running on remote hosts, "
                "including IoT sensor gateways and edge nodes. Methods include port scans and ping sweeps. "
            )
            * 3,
        }
        doc_v1, chunks_v1 = manager.ingest_document(adapter, raw_v1, version="v1.0.0")

        assert len(chunks_v1) >= 2
        assert len(doc_v1.merkle_root) == 64
        assert doc_v1.status == "active"

        # 2. Valid chunk verification passes
        valid_chunk = chunks_v1[0]
        is_valid, reason = manager.verify_chunk(valid_chunk)
        assert is_valid is True
        assert reason == "verified"

        # 3. Tamper test 1: Modify 1 byte/character in chunk text
        tampered_text_chunk = valid_chunk.model_copy(
            update={"canonical_text": valid_chunk.canonical_text + "X"}
        )
        is_valid_t1, reason_t1 = manager.verify_chunk(tampered_text_chunk)
        assert is_valid_t1 is False
        assert "chunk_content_tampered" in reason_t1

        # 4. Tamper test 2: Modify sibling hash in Merkle proof
        tampered_proof = [
            MerkleProofStep(position=step.position, sibling_hash="0" * 64)
            for step in valid_chunk.merkle_proof
        ]
        tampered_proof_chunk = valid_chunk.model_copy(update={"merkle_proof": tampered_proof})
        is_valid_t2, reason_t2 = manager.verify_chunk(tampered_proof_chunk)
        assert is_valid_t2 is False
        assert "merkle_proof_verification_failed" in reason_t2

        # 5. Version update: Ingest version 2
        raw_v2 = {
            "technique_id": "T1046",
            "name": "Network Service Discovery Updated",
            "description": "Updated adversary procedures for IoT network scanning.",
        }
        doc_v2, chunks_v2 = manager.ingest_document(adapter, raw_v2, version="v2.0.0")

        assert doc_v2.status == "active"
        assert doc_v2.previous_version == "v1.0.0"

        # Chunks from active version 2 pass
        is_valid_v2, _ = manager.verify_chunk(chunks_v2[0])
        assert is_valid_v2 is True

        # Chunks from superseded version 1 are rejected when active version enforced
        is_valid_old, reason_old = manager.verify_chunk(valid_chunk, enforce_active_version=True)
        assert is_valid_old is False
        assert "stale_version_rejected" in reason_old

        # 6. Revocation: Revoke version 2
        revoked = manager.revoke_document("t1046", "v2.0.0")
        assert revoked is True
        is_valid_rev, reason_rev = manager.verify_chunk(chunks_v2[0])
        assert is_valid_rev is False
        assert "document_version_revoked" in reason_rev
