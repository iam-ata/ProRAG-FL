"""Unit tests for Phase 14: System and Overhead Benchmarks.

Strictly tests:
- instructions/25_SYSTEMS_BENCHMARKS.md
- instructions/36_PHASE_ACCEPTANCE_GATES.md (Gate P14: hardware/software and consistent timing protocol)
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from prorag_fl.benchmarks.fabric_overhead import benchmark_fabric_overhead
from prorag_fl.benchmarks.fl_overhead import benchmark_fl_overhead
from prorag_fl.benchmarks.local_inference import benchmark_local_inference
from prorag_fl.benchmarks.openai_overhead import benchmark_openai_overhead, load_pricing_config
from prorag_fl.benchmarks.rag_overhead import benchmark_rag_overhead
from prorag_fl.benchmarks.reporting import generate_benchmark_markdown
from prorag_fl.benchmarks.runner import MasterBenchmarkRunner
from prorag_fl.benchmarks.schemas import (
    ComprehensiveBenchmarkReport,
    FabricBenchmarkResult,
    FLBenchmarkResult,
    LocalInferenceBenchmarkResult,
    OpenAIBenchmarkResult,
    RAGBenchmarkResult,
    TimingStats,
)
from prorag_fl.benchmarks.timing import measure_callable


def test_timing_protocol_isolation_and_statistics() -> None:
    """Verify precision timing protocol: cold-start isolation, warmups, and distribution statistics."""
    call_counts = {"count": 0}

    def dummy_op(val: int) -> int:
        call_counts["count"] += 1
        time.sleep(0.001)  # 1ms sleep
        return val * 2

    stats, res = measure_callable(dummy_op, 5, warmup_iterations=3, benchmark_iterations=5)

    assert isinstance(stats, TimingStats)
    assert res == 10
    # Total calls = 1 cold + 3 warmup + 5 benchmark = 9
    assert call_counts["count"] == 9
    assert stats.cold_start_ms > 0.0
    assert stats.warm_mean_ms > 0.0
    assert stats.warm_median_ms > 0.0
    assert stats.warm_p95_ms >= stats.warm_median_ms
    assert stats.warm_p99_ms >= stats.warm_p95_ms
    assert stats.warm_min_ms <= stats.warm_max_ms
    assert stats.iterations == 5


def test_local_inference_benchmark() -> None:
    """Verify local IDS inference microbenchmarking across preprocessing, CNN, calibration, and OOD."""
    results = benchmark_local_inference(
        batch_sizes=[1, 4],
        num_features=46,
        num_classes=15,
        warmup_iterations=2,
        benchmark_iterations=5,
    )

    assert len(results) == 2
    b1 = results[0]
    b4 = results[1]

    assert b1.batch_size == 1
    assert b4.batch_size == 4
    assert isinstance(b1, LocalInferenceBenchmarkResult)
    assert b1.per_sample_latency_ms > 0.0
    assert b1.throughput_samples_per_sec > 0.0

    # Batch throughput scaling
    assert b4.throughput_samples_per_sec >= b1.throughput_samples_per_sec * 0.8
    # Assert all sub-components timed
    assert b1.preprocessing_stats.warm_mean_ms >= 0.0
    assert b1.forward_pass_stats.warm_mean_ms >= 0.0
    assert b1.calibration_stats.warm_mean_ms >= 0.0
    assert b1.ood_stats.warm_mean_ms >= 0.0
    assert b1.total_direct_stats.warm_mean_ms > 0.0


def test_fl_overhead_benchmark() -> None:
    """Verify Federated Learning overhead metrics: training, serialization, bandwidth, aggregation."""
    results = benchmark_fl_overhead(
        strategies=["fedavg", "fedtrimmedavg"],
        client_counts=[3],
        num_features=46,
        num_classes=15,
        batch_size=32,
        warmup_iterations=1,
        benchmark_iterations=2,
    )

    assert len(results) == 2
    for r in results:
        assert isinstance(r, FLBenchmarkResult)
        assert r.num_clients == 3
        assert r.client_training_stats.warm_mean_ms > 0.0
        assert r.serialization_stats.warm_mean_ms >= 0.0
        assert r.provenance_check_stats.warm_mean_ms >= 0.0
        assert r.aggregation_stats.warm_mean_ms >= 0.0
        assert r.total_round_stats.warm_mean_ms > 0.0
        assert r.upload_bytes_per_client > 1000
        assert r.download_bytes_per_client > 1000


def test_fabric_overhead_benchmark() -> None:
    """Verify Hyperledger Fabric blockchain provenance overhead: submission, query, verification, endorsement."""
    res = benchmark_fabric_overhead(
        num_clients=3,
        payload_size_bytes=1024,
        warmup_iterations=2,
        benchmark_iterations=5,
    )

    assert isinstance(res, FabricBenchmarkResult)
    assert res.verification_stats.warm_mean_ms > 0.0
    assert res.tx_submission_stats.warm_mean_ms > 0.0
    assert res.query_stats.warm_mean_ms >= 0.0
    assert res.endorsement_stats.warm_mean_ms >= 0.0
    assert res.peak_tps > 0.0
    assert res.ledger_growth_mb_per_100_rounds > 0.0


def test_rag_overhead_benchmark() -> None:
    """Verify Hybrid RAG retrieval pipeline breakdown across MinIO, embeddings, dense/sparse search, and Merkle checks."""
    res = benchmark_rag_overhead(
        num_knowledge_docs=10,
        top_candidates=5,
        top_verified=3,
        warmup_iterations=2,
        benchmark_iterations=5,
    )

    assert isinstance(res, RAGBenchmarkResult)
    assert res.minio_fetch_stats.warm_mean_ms >= 0.0
    assert res.embedding_stats.warm_mean_ms >= 0.0
    assert res.dense_search_stats.warm_mean_ms >= 0.0
    assert res.sparse_search_stats.warm_mean_ms >= 0.0
    assert res.rrf_fusion_stats.warm_mean_ms >= 0.0
    assert res.merkle_verification_stats.warm_mean_ms >= 0.0
    assert res.reranking_stats.warm_mean_ms >= 0.0
    assert res.total_retrieval_stats.warm_mean_ms > 0.0
    assert res.candidates_retrieved > 0
    assert res.verified_evidence_count <= 3


def test_openai_overhead_and_dynamic_pricing() -> None:
    """Verify OpenAI reasoning overhead and dynamic pricing config lookup (no hardcoded pricing in code)."""
    pricing = load_pricing_config()
    assert "models" in pricing
    assert "gpt-4o-mini" in pricing["models"]
    assert pricing["models"]["gpt-4o-mini"]["input_per_million_tokens"] > 0.0
    assert pricing["models"]["gpt-4o-mini"]["output_per_million_tokens"] > 0.0

    res = benchmark_openai_overhead(
        model="gpt-4o-mini",
        warmup_iterations=2,
        benchmark_iterations=5,
    )

    assert isinstance(res, OpenAIBenchmarkResult)
    assert res.model == "gpt-4o-mini"
    assert res.roundtrip_stats.warm_mean_ms >= 0.0
    assert res.total_tokens == res.prompt_tokens + res.completion_tokens
    assert res.cost_per_request_usd > 0.0
    assert res.cost_per_10k_requests_usd == pytest.approx(
        res.cost_per_request_usd * 10000, abs=1e-2
    )


def test_e2e_workload_breakdown_and_report_generation(tmp_path: Path) -> None:
    """Verify composite end-to-end workload model and markdown report generation."""
    runner = MasterBenchmarkRunner(warmup_iterations=2, benchmark_iterations=3)
    report = runner.run_all_benchmarks()

    assert isinstance(report, ComprehensiveBenchmarkReport)
    assert "os" in report.hardware_info
    assert "cpu" in report.hardware_info
    assert "torch" in report.software_versions
    assert len(report.local_inference) > 0
    assert len(report.federated_learning) > 0
    assert len(report.e2e_workloads) > 0
    assert len(report.summary_conclusions) > 0

    # Invariants on composite workload
    rir_zero = next(e for e in report.e2e_workloads if e.invocation_rate == 0.0)
    rir_full = next(e for e in report.e2e_workloads if e.invocation_rate == 1.0)
    assert rir_zero.cost_usd_per_10k_flows == 0.0
    assert rir_full.cost_usd_per_10k_flows > 0.0
    assert rir_full.weighted_avg_latency_ms > rir_zero.weighted_avg_latency_ms * 5.0

    # Report markdown test
    out_file = tmp_path / "system_benchmark_report.md"
    md = generate_benchmark_markdown(report, output_path=out_file)

    assert out_file.exists()
    assert "# ProRAG-FL System and Overhead Benchmarks Report" in md
    assert "Hardware & Software Telemetry" in md
    assert "Timing Protocol Specification" in md
    assert "Local IDS Inference Path Overhead" in md
    assert "Federated Learning Subsystem Overhead" in md
    assert "Hyperledger Fabric Blockchain Provenance Overhead" in md
    assert "Hybrid Provenance-Aware RAG Pipeline Breakdown" in md
    assert "OpenAI Structured CTI Reasoning & Dynamic Pricing" in md
    assert "End-to-End Latency Breakdown vs. RAG Invocation Rate" in md
