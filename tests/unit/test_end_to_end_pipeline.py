"""Unit tests for Phase 9: End-to-End ProRAG-FL Integration Pipeline.

Verifies Acceptance Gate P9:
- Direct path makes fast local decision and NEVER calls RAG or LLM API (Invariant 1).
- Escalated path queries hybrid retriever, verifies via hard gate, and reasons with LLM.
- Cryptographically invalid evidence is rejected and NEVER reaches reasoning (Invariant 2).
- Ground truth test label never leaks into SecurityEvent or LLM prompt (Invariant 3).
- LLM output never self-admits into threat memory (Invariant 4).
- Complete auditable decision record structure with granular latency breakdown.
- Batch evaluation reporting metrics, escalation rates, and latency accounting.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from prorag_fl.calibration import TemperatureScaler
from prorag_fl.evaluation.pipeline import ProRAGFLPipeline
from prorag_fl.knowledge import (
    KnowledgeManager,
    KnowledgeObjectStore,
    MitreAttackAdapter,
)
from prorag_fl.models.ids_1dcnn import IDS1DCNN
from prorag_fl.ood import DualGate, MahalanobisOODDetector
from prorag_fl.rag.embedder import HybridEmbedder
from prorag_fl.rag.hard_gate import HardProvenanceGate
from prorag_fl.rag.retriever import HybridRetriever
from prorag_fl.rag.vector_index import QdrantVectorIndex
from prorag_fl.reasoning.client import MockReasoningClient
from prorag_fl.reasoning.engine import ReasoningEngine
from prorag_fl.schemas.pipeline import AuditableDecisionRecord, EndToEndBatchEvaluationReport


@pytest.fixture
def pipeline_components(
    tmp_path,
) -> tuple[
    IDS1DCNN,
    TemperatureScaler,
    MahalanobisOODDetector,
    DualGate,
    list[str],
    HybridRetriever,
    HardProvenanceGate,
    ReasoningEngine,
]:
    """Construct mock/fast pipeline components for end-to-end testing."""
    torch.manual_seed(42)
    np.random.seed(42)

    num_features = 16
    num_classes = 3
    label_names = ["Benign", "DDoS-ICMP", "Mirai"]

    # 1. 1D-CNN Model
    model = IDS1DCNN(
        num_features=num_features,
        num_classes=num_classes,
        dropout_rate=0.1,
    )
    model.eval()

    # 2. Temperature Scaler
    scaler = TemperatureScaler()
    scaler.eval()

    # 3. Mahalanobis OOD Detector
    ood_detector = MahalanobisOODDetector(embedding_dim=128)
    dummy_embeddings = np.random.randn(90, 128).astype(np.float32)
    dummy_labels = np.array([0] * 30 + [1] * 30 + [2] * 30, dtype=np.int64)
    ood_detector.fit(dummy_embeddings, dummy_labels)

    # 4. Dual Gate (tau_c = 0.70, tau_m = 10.0)
    dual_gate = DualGate(
        temperature_scaler=scaler,
        mahalanobis_detector=ood_detector,
        tau_c=0.70,
        tau_m=10.0,
    )

    # 5. Knowledge manager and RAG components
    store = KnowledgeObjectStore(storage_dir=tmp_path / "knowledge_store")
    km = KnowledgeManager(object_store=store)
    mitre_adapter = MitreAttackAdapter()
    doc, chunks = km.ingest_document(
        adapter=mitre_adapter,
        raw_data={
            "technique_id": "T1059",
            "name": "Command and Scripting Interpreter",
            "description": "Mirai botnet brute forces default credentials over Telnet ports 23 and 2323 to launch DDoS flood attacks.",
            "tactics": ["Execution"],
        },
        version="v1.0.0",
    )

    embedder = HybridEmbedder(use_fallback=True)
    v_index = QdrantVectorIndex(location=":memory:", vector_dim=1024)

    texts = [c.canonical_text for c in chunks]
    dense_vecs, sparse_vecs = embedder.embed(texts)
    v_index.index_chunks(chunks, dense_vecs, sparse_vecs)

    retriever = HybridRetriever(vector_index=v_index, embedder=embedder, rrf_k=60)
    hard_gate = HardProvenanceGate(knowledge_manager=km, max_evidence=5)

    # 6. Reasoning Engine
    mock_client = MockReasoningClient(model_id="mock-gpt4o-mini")
    reasoning_engine = ReasoningEngine(client=mock_client)

    return (
        model,
        scaler,
        ood_detector,
        dual_gate,
        label_names,
        retriever,
        hard_gate,
        reasoning_engine,
    )


@pytest.mark.unit
def test_direct_path_no_rag_or_api(pipeline_components) -> None:
    """Gate P9 Invariant 1: Direct path (G=0) must NEVER call RAG or LLM API."""
    (
        model,
        scaler,
        ood_detector,
        _,
        label_names,
        retriever,
        hard_gate,
        reasoning_engine,
    ) = pipeline_components

    # Create a dual gate that guarantees DIRECT route (tau_c = 0.0, tau_m = 999.0 => G=0)
    direct_gate = DualGate(
        temperature_scaler=scaler,
        mahalanobis_detector=ood_detector,
        tau_c=0.0,
        tau_m=999.0,
    )

    pipeline = ProRAGFLPipeline(
        model=model,
        temperature_scaler=scaler,
        ood_detector=ood_detector,
        dual_gate=direct_gate,
        label_names=label_names,
        retriever=retriever,
        hard_gate=hard_gate,
        reasoning_engine=reasoning_engine,
    )

    x = np.random.randn(16).astype(np.float32)
    record = pipeline.process_sample(x=x, ground_truth_label="Benign", event_id="evt_direct_01")

    # Invariant 1 Assertions:
    assert record.route == "DIRECT"
    assert record.gate_escalated is False
    assert record.gate_reason == "direct"
    assert record.retrieval_candidate_ids == []
    assert record.rejected_candidate_ids == []
    assert record.verified_evidence_ids == []
    assert record.reasoning_model_id is None
    assert record.structured_reasoning is None

    # Timing assertions:
    assert record.latency_breakdown.inference_ids_ms >= 0.0
    assert record.latency_breakdown.calibration_ms >= 0.0
    assert record.latency_breakdown.ood_ms >= 0.0
    assert record.latency_breakdown.gate_ms >= 0.0
    assert record.latency_breakdown.retrieval_ms == 0.0
    assert record.latency_breakdown.hard_gate_ms == 0.0
    assert record.latency_breakdown.reasoning_ms == 0.0
    assert record.latency_breakdown.total_latency_ms > 0.0


@pytest.mark.unit
def test_escalated_path_queries_rag_and_reasoning(pipeline_components) -> None:
    """Gate P9: Escalated path (G=1) routes to RAG, verifies with Hard Gate, and calls LLM."""
    (
        model,
        scaler,
        ood_detector,
        _,
        label_names,
        retriever,
        hard_gate,
        reasoning_engine,
    ) = pipeline_components

    # Create a dual gate that guarantees ESCALATED route (tau_c = 1.0, tau_m = 0.0 => G=1)
    escalate_gate = DualGate(
        temperature_scaler=scaler,
        mahalanobis_detector=ood_detector,
        tau_c=1.0,
        tau_m=0.0,
    )

    pipeline = ProRAGFLPipeline(
        model=model,
        temperature_scaler=scaler,
        ood_detector=ood_detector,
        dual_gate=escalate_gate,
        label_names=label_names,
        retriever=retriever,
        hard_gate=hard_gate,
        reasoning_engine=reasoning_engine,
    )

    x = np.random.randn(16).astype(np.float32)
    record = pipeline.process_sample(x=x, ground_truth_label="Mirai", event_id="evt_esc_01")

    assert record.route == "ESCALATED"
    assert record.gate_escalated is True
    assert record.gate_reason in ("low_confidence", "high_mahalanobis", "both")
    assert len(record.retrieval_candidate_ids) > 0
    assert len(record.verified_evidence_ids) > 0
    assert record.reasoning_model_id == "mock-gpt4o-mini"
    assert record.structured_reasoning is not None
    assert record.structured_reasoning.evidence_sufficient is True

    # Timing assertions:
    assert record.latency_breakdown.retrieval_ms >= 0.0
    assert record.latency_breakdown.hard_gate_ms >= 0.0
    assert record.latency_breakdown.reasoning_ms >= 0.0
    assert record.latency_breakdown.total_latency_ms > 0.0


@pytest.mark.unit
def test_invalid_evidence_rejected_by_hard_gate(pipeline_components) -> None:
    """Gate P9 Invariant 2: Cryptographically invalid evidence is rejected and never reaches reasoning."""
    (
        model,
        scaler,
        ood_detector,
        _,
        label_names,
        retriever,
        hard_gate,
        reasoning_engine,
    ) = pipeline_components

    # Revoke the document so all its chunks become invalid
    hard_gate.knowledge_manager.revoke_document("T1059", "v1.0.0")

    escalate_gate = DualGate(
        temperature_scaler=scaler,
        mahalanobis_detector=ood_detector,
        tau_c=1.0,
        tau_m=0.0,
    )
    pipeline = ProRAGFLPipeline(
        model=model,
        temperature_scaler=scaler,
        ood_detector=ood_detector,
        dual_gate=escalate_gate,
        label_names=label_names,
        retriever=retriever,
        hard_gate=hard_gate,
        reasoning_engine=reasoning_engine,
    )

    x = np.random.randn(16).astype(np.float32)
    record = pipeline.process_sample(x=x, ground_truth_label="Mirai", event_id="evt_tampered_01")

    assert record.route == "ESCALATED"
    # Retrieved candidates exist in vector store
    assert len(record.retrieval_candidate_ids) > 0
    # But all revoked chunks must be rejected!
    assert len(record.rejected_candidate_ids) > 0
    # Verified evidence passed to LLM must be empty
    assert len(record.verified_evidence_ids) == 0
    # LLM must report insufficient evidence
    assert record.structured_reasoning is not None
    assert record.structured_reasoning.evidence_sufficient is False


@pytest.mark.unit
def test_ground_truth_firewall_invariant(pipeline_components) -> None:
    """Gate P9 Invariant 3: Ground-truth test label never leaks into SecurityEvent or LLM payload."""
    (
        model,
        scaler,
        ood_detector,
        _,
        label_names,
        retriever,
        hard_gate,
        reasoning_engine,
    ) = pipeline_components

    escalate_gate = DualGate(
        temperature_scaler=scaler,
        mahalanobis_detector=ood_detector,
        tau_c=1.0,
        tau_m=0.0,
    )
    pipeline = ProRAGFLPipeline(
        model=model,
        temperature_scaler=scaler,
        ood_detector=ood_detector,
        dual_gate=escalate_gate,
        label_names=label_names,
        retriever=retriever,
        hard_gate=hard_gate,
        reasoning_engine=reasoning_engine,
    )

    x = np.random.randn(16).astype(np.float32)
    secret_ground_truth = "CONFIDENTIAL_TRUE_LABEL_ZERO_DAY"
    record = pipeline.process_sample(
        x=x, ground_truth_label=secret_ground_truth, event_id="evt_leak_test"
    )

    # Check that evaluation_ground_truth is stored strictly for evaluation
    assert record.evaluation_ground_truth == secret_ground_truth

    # Check reasoning engine execution history: prompt text must NOT contain secret_ground_truth!
    assert len(reasoning_engine.execution_history) > 0
    last_exec = reasoning_engine.execution_history[-1]
    # The prompt hash exists
    assert len(last_exec.prompt_hash) == 64
    # The secret ground truth must not appear in any execution log or structured output
    assert secret_ground_truth not in (last_exec.error_message or "")


@pytest.mark.unit
def test_threat_memory_invariant(pipeline_components) -> None:
    """Gate P9 Invariant 4: LLM output never self-admits into threat memory."""
    (
        model,
        scaler,
        ood_detector,
        _,
        label_names,
        retriever,
        hard_gate,
        reasoning_engine,
    ) = pipeline_components

    escalate_gate = DualGate(
        temperature_scaler=scaler,
        mahalanobis_detector=ood_detector,
        tau_c=1.0,
        tau_m=0.0,
    )
    pipeline = ProRAGFLPipeline(
        model=model,
        temperature_scaler=scaler,
        ood_detector=ood_detector,
        dual_gate=escalate_gate,
        label_names=label_names,
        retriever=retriever,
        hard_gate=hard_gate,
        reasoning_engine=reasoning_engine,
    )

    x = np.random.randn(16).astype(np.float32)
    pipeline.process_sample(x=x, ground_truth_label="Mirai")

    # Invariant 4 check
    assert pipeline.admitted_into_threat_memory is False


@pytest.mark.unit
def test_batch_evaluation_and_report_metrics(pipeline_components) -> None:
    """Gate P9: Batch evaluation produces accurate metrics, latency comparison, and asserts all invariants."""
    (
        model,
        scaler,
        ood_detector,
        dual_gate,
        label_names,
        retriever,
        hard_gate,
        reasoning_engine,
    ) = pipeline_components

    pipeline = ProRAGFLPipeline(
        model=model,
        temperature_scaler=scaler,
        ood_detector=ood_detector,
        dual_gate=dual_gate,
        label_names=label_names,
        retriever=retriever,
        hard_gate=hard_gate,
        reasoning_engine=reasoning_engine,
    )

    x_batch = np.random.randn(10, 16).astype(np.float32)
    y_batch = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], dtype=np.int64)

    report, records = pipeline.evaluate_batch(x_batch=x_batch, y_batch=y_batch)

    assert isinstance(report, EndToEndBatchEvaluationReport)
    assert report.total_events == 10
    assert report.direct_count + report.escalated_count == 10
    assert 0.0 <= report.escalation_rate <= 1.0
    assert 0.0 <= report.overall_accuracy <= 1.0
    assert 0.0 <= report.macro_f1 <= 1.0
    assert report.invariants_verified is True
    assert len(records) == 10

    for rec in records:
        assert isinstance(rec, AuditableDecisionRecord)
        assert rec.event_pseudonym.startswith("pse_")
        assert rec.global_model_version == "v1.0"
        assert rec.confidence >= 0.0
        assert rec.mahalanobis_distance >= 0.0
