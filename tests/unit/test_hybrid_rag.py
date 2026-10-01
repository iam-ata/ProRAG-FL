"""Unit tests and acceptance gates for Phase 7 Hybrid Provenance-Aware RAG."""

from __future__ import annotations

import pytest

from prorag_fl.knowledge.adapters.cisa import CisaKevAdapter
from prorag_fl.knowledge.adapters.consortium import ConsortiumIncidentAdapter
from prorag_fl.knowledge.adapters.mitre import MitreAttackAdapter
from prorag_fl.knowledge.adapters.nvd import NvdCveAdapter
from prorag_fl.knowledge.manager import KnowledgeManager
from prorag_fl.knowledge.object_store import KnowledgeObjectStore
from prorag_fl.rag.benchmark import evaluate_retrieval_benchmark
from prorag_fl.rag.embedder import HybridEmbedder
from prorag_fl.rag.hard_gate import HardProvenanceGate
from prorag_fl.rag.query_builder import construct_retrieval_query
from prorag_fl.rag.retriever import HybridRetriever
from prorag_fl.rag.vector_index import QdrantVectorIndex
from prorag_fl.schemas.knowledge import MerkleProofStep
from prorag_fl.schemas.rag import SecurityEvent


@pytest.fixture
def knowledge_env() -> tuple[KnowledgeManager, QdrantVectorIndex, HybridEmbedder]:
    """Fixture providing initialized knowledge manager, vector index, and embedder."""
    store = KnowledgeObjectStore()
    km = KnowledgeManager(object_store=store, chunk_size=250, chunk_overlap=30)
    embedder = HybridEmbedder(use_fallback=True)
    v_index = QdrantVectorIndex(location=":memory:", vector_dim=1024)

    # Ingest baseline threat documents across all 4 authorized sources
    mitre_adapter = MitreAttackAdapter()
    km.ingest_document(
        mitre_adapter,
        raw_data={
            "technique_id": "T1059",
            "name": "Command and Scripting Interpreter",
            "description": "Adversaries may abuse command and script interpreters to execute commands.",
            "tactics": ["Execution"],
        },
        version="v1.0.0",
    )

    nvd_adapter = NvdCveAdapter()
    km.ingest_document(
        nvd_adapter,
        raw_data={
            "cve_id": "CVE-2023-4567",
            "description": "Buffer overflow in IoT smart meter telemetry gateway enabling code execution.",
            "cvss_score": 9.8,
            "severity": "CRITICAL",
        },
        version="v1.0.0",
    )

    cisa_adapter = CisaKevAdapter()
    km.ingest_document(
        cisa_adapter,
        raw_data={
            "cveID": "CVE-2023-4567",
            "vendorProject": "SmartGridCorp",
            "product": "Edge Gateway",
            "vulnerabilityName": "Remote Code Execution",
            "shortDescription": "Actively exploited in industrial IoT deployments.",
        },
        version="v1.0.0",
    )

    consortium_adapter = ConsortiumIncidentAdapter()
    km.ingest_document(
        consortium_adapter,
        raw_data={
            "incident_id": "INC-2024-MIRAI",
            "title": "Mirai IoT botnet propagation attempt",
            "target_system": "Industrial SCADA node",
            "narrative": "Mirai brute-force attempt targeting default credentials over Telnet and HTTP.",
        },
        version="v1.0.0",
    )

    # Index all active chunks in the vector index
    all_chunks = km.get_active_chunks()
    texts = [c.canonical_text for c in all_chunks]
    dense_vecs, sparse_vecs = embedder.embed(texts)
    v_index.index_chunks(all_chunks, dense_vecs, sparse_vecs)

    return km, v_index, embedder


@pytest.mark.unit
def test_query_construction_firewall_and_formatting() -> None:
    """Verify construct_retrieval_query uses only runtime visible fields and forbids ground-truth label."""
    event = SecurityEvent(
        event_id="evt_test_101",
        model_predicted_class="DDoS-UDP_Flood",
        model_confidence=0.54,
        mahalanobis_distance=18.42,
        gate_decision="escalate",
        escalation_reason="high_mahalanobis",
        abnormal_features={"flow_duration": 142.5, "rate": 8920.1, "syn_count": 0.0},
        protocol_context="UDP / Port 53 / DNS",
        device_context="IoT Edge Gateway Model-X",
        raw_packet_summary="Abnormal surge in high-frequency UDP datagrams without payload",
    )

    query = construct_retrieval_query(event)

    assert query.event_id == "evt_test_101"
    assert "DDoS-UDP_Flood" in query.query_text
    assert "IoT Edge Gateway Model-X" in query.query_text
    assert "high_mahalanobis" in query.query_text
    assert "flow_duration" in query.query_text
    # Verify no ground-truth label attribute exists on SecurityEvent schema
    assert not hasattr(event, "ground_truth")
    assert not hasattr(event, "true_label")


@pytest.mark.unit
def test_hybrid_retriever_rrf_scoring(
    knowledge_env: tuple[KnowledgeManager, QdrantVectorIndex, HybridEmbedder],
) -> None:
    """Verify hybrid retrieval combines dense and sparse rankings using Reciprocal Rank Fusion."""
    _, v_index, embedder = knowledge_env
    retriever = HybridRetriever(
        vector_index=v_index,
        embedder=embedder,
        top_k_dense=10,
        top_k_sparse=10,
        rrf_k=60,
        top_fused_candidates=10,
    )

    query_str = "IoT buffer overflow code execution vulnerability in gateway"
    fused_results = retriever.retrieve(query_str)

    assert len(fused_results) > 0
    # Highest score must be first
    scores = [score for _, score in fused_results]
    assert scores == sorted(scores, reverse=True)
    for score in scores:
        assert score > 0.0


@pytest.mark.unit
def test_hard_provenance_gate_six_checks(
    knowledge_env: tuple[KnowledgeManager, QdrantVectorIndex, HybridEmbedder],
) -> None:
    """Gate P7: Verify all 6 hard cryptographic and lifecycle checks reject invalid candidates."""
    km, _, _ = knowledge_env
    gate = HardProvenanceGate(knowledge_manager=km)

    active_chunks = km.get_active_chunks()
    assert len(active_chunks) > 0
    valid_chunk = active_chunks[0]

    # 1. Valid chunk must pass
    res_valid = gate.verify_candidate(valid_chunk)
    assert res_valid.is_eligible is True
    assert len(res_valid.failure_reasons) == 0

    # 2. Check 1: Non-allowlisted source rejected
    gate_restricted = HardProvenanceGate(
        knowledge_manager=km, allowed_sources={"only_mitre_attack"}
    )
    res_unauth = gate_restricted.verify_candidate(valid_chunk)
    assert res_unauth.is_eligible is False
    assert any("source_not_allowlisted" in r for r in res_unauth.failure_reasons)

    # 3. Check 2: Missing ledger record rejected
    chunk_no_ledger = valid_chunk.model_copy(update={"document_id": "nonexistent_doc_id"})
    res_no_ledger = gate.verify_candidate(chunk_no_ledger)
    assert res_no_ledger.is_eligible is False
    assert "ledger_record_missing" in res_no_ledger.failure_reasons

    # 4. Check 3: Stale / inactive version rejected
    chunk_stale_ver = valid_chunk.model_copy(update={"document_version": "v0.0.1_stale"})
    res_stale = gate.verify_candidate(chunk_stale_ver)
    assert res_stale.is_eligible is False
    assert any("document_version_inactive" in r for r in res_stale.failure_reasons)

    # 5. Check 4: Tampered chunk text rejected
    chunk_tampered_text = valid_chunk.model_copy(
        update={"canonical_text": valid_chunk.canonical_text + " [INJECTED_TAMPER]"}
    )
    res_tampered_text = gate.verify_candidate(chunk_tampered_text)
    assert res_tampered_text.is_eligible is False
    assert "chunk_hash_mismatch" in res_tampered_text.failure_reasons

    # 6. Check 5: Tampered Merkle proof rejected
    corrupt_proof = [MerkleProofStep(position="left", sibling_hash="f" * 64)]
    chunk_corrupt_proof = valid_chunk.model_copy(update={"merkle_proof": corrupt_proof})
    res_corrupt_proof = gate.verify_candidate(chunk_corrupt_proof)
    assert res_corrupt_proof.is_eligible is False
    assert "merkle_proof_invalid" in res_corrupt_proof.failure_reasons

    # 7. Check 6: Revoked document rejected
    km.revoke_document("t1059", "v1.0.0")
    t1059_chunks = [c for c in active_chunks if c.document_id == "t1059"]
    if t1059_chunks:
        res_revoked = gate.verify_candidate(t1059_chunks[0])
        assert res_revoked.is_eligible is False
        assert any(
            "document_revoked" in r or "document_version_inactive" in r
            for r in res_revoked.failure_reasons
        )


@pytest.mark.unit
def test_verified_reranking_returns_top5_evidence(
    knowledge_env: tuple[KnowledgeManager, QdrantVectorIndex, HybridEmbedder],
) -> None:
    """Gate P7: Multi-factor reranking must return at most verified Top-5 evidence."""
    km, v_index, embedder = knowledge_env
    retriever = HybridRetriever(vector_index=v_index, embedder=embedder)
    gate = HardProvenanceGate(knowledge_manager=km, max_evidence=5)

    candidates = retriever.retrieve("IoT smart meter vulnerability buffer overflow")
    verified_evidence = gate.filter_and_rerank(candidates)

    assert len(verified_evidence) <= 5
    for ev in verified_evidence:
        assert ev.evidence_id.startswith("evi_")
        assert ev.verification_record.is_eligible is True
        assert len(ev.verification_record.failure_reasons) == 0
        assert ev.final_score > 0.0
        assert ev.canonical_text != ""


@pytest.mark.unit
def test_acceptance_gate_p7_retrieval_benchmark(
    knowledge_env: tuple[KnowledgeManager, QdrantVectorIndex, HybridEmbedder],
) -> None:
    """Acceptance Gate P7: Dense+sparse/RRF/hard gate/verified Top-5 + retrieval benchmark."""
    km, v_index, embedder = knowledge_env
    retriever = HybridRetriever(vector_index=v_index, embedder=embedder)
    gate = HardProvenanceGate(knowledge_manager=km, max_evidence=5)

    # Construct test query / support pairs
    q1 = construct_retrieval_query(
        SecurityEvent(
            event_id="q1",
            model_predicted_class="Buffer_Overflow",
            model_confidence=0.6,
            mahalanobis_distance=15.0,
            escalation_reason="high_mahalanobis",
            abnormal_features={"packet_len": 1500.0},
            protocol_context="TCP / Port 8080",
            device_context="Smart meter IoT gateway",
            raw_packet_summary="Buffer overflow attempt targeting SmartGridCorp edge gateway",
        )
    )
    support1 = {"cve_2023_4567"}

    q2 = construct_retrieval_query(
        SecurityEvent(
            event_id="q2",
            model_predicted_class="Mirai-greeth_flood",
            model_confidence=0.5,
            mahalanobis_distance=20.0,
            escalation_reason="both",
            abnormal_features={"rate": 10000.0},
            protocol_context="Telnet / HTTP",
            device_context="Industrial SCADA node",
            raw_packet_summary="Mirai brute-force attempt targeting default credentials",
        )
    )
    support2 = {"inc_2024_mirai"}

    query_pairs = [(q1, support1), (q2, support2)]

    metrics = evaluate_retrieval_benchmark(
        retriever=retriever,
        hard_gate=gate,
        query_ground_truth_pairs=query_pairs,
        k_values=(1, 3, 5),
    )

    assert metrics.total_queries == 2
    assert metrics.mrr > 0.0
    assert metrics.recall_at_5 > 0.0
    assert "P@1" in metrics.precision_at_k
    assert "R@5" in metrics.recall_at_k
    assert metrics.avg_latency_ms >= 0.0
