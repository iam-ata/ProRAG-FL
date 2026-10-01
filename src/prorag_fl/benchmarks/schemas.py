"""Pydantic schemas for Phase 14: System and Overhead Benchmarks.

Strictly adheres to:
- instructions/25_SYSTEMS_BENCHMARKS.md
- instructions/36_PHASE_ACCEPTANCE_GATES.md (P14: hardware/software and consistent timing protocol)
"""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TimingStats(BaseModel):
    """Rigorous timing statistics strictly separating cold-start and warm-path measurements."""

    model_config = ConfigDict(extra="forbid")

    cold_start_ms: float = Field(
        ..., description="Latency of the very first execution before cache/GPU warmup"
    )
    warm_mean_ms: float = Field(..., description="Mean latency over warm repeated iterations")
    warm_median_ms: float = Field(..., description="Median latency over warm repeated iterations")
    warm_p95_ms: float = Field(..., description="95th percentile latency")
    warm_p99_ms: float = Field(..., description="99th percentile latency")
    warm_std_ms: float = Field(..., description="Standard deviation over warm iterations")
    warm_min_ms: float = Field(..., description="Minimum measured warm latency")
    warm_max_ms: float = Field(..., description="Maximum measured warm latency")
    iterations: int = Field(..., description="Number of warm benchmark iterations executed")


class LocalInferenceBenchmarkResult(BaseModel):
    """Benchmarking metrics for the direct sub-millisecond local IDS inference path."""

    model_config = ConfigDict(extra="forbid")

    batch_size: int
    preprocessing_stats: TimingStats
    forward_pass_stats: TimingStats
    calibration_stats: TimingStats
    ood_stats: TimingStats
    total_direct_stats: TimingStats
    per_sample_latency_ms: float = Field(
        ..., description="Effective latency per single network flow"
    )
    throughput_samples_per_sec: float = Field(
        ..., description="Processed network flows per second under this batch size"
    )


class FLBenchmarkResult(BaseModel):
    """Benchmarking metrics for Federated Learning client training, communication, and aggregation."""

    model_config = ConfigDict(extra="forbid")

    strategy: str = Field(
        ..., description="FL Strategy: fedavg, fedtrimmedavg, or provenance_gated"
    )
    num_clients: int
    client_training_stats: TimingStats
    serialization_stats: TimingStats
    provenance_check_stats: TimingStats
    aggregation_stats: TimingStats
    total_round_stats: TimingStats
    upload_bytes_per_client: int = Field(
        ..., description="Payload size uploaded per client per round"
    )
    download_bytes_per_client: int = Field(
        ..., description="Payload size downloaded per client per round"
    )


class FabricBenchmarkResult(BaseModel):
    """Benchmarking metrics for Hyperledger Fabric blockchain model provenance verification."""

    model_config = ConfigDict(extra="forbid")

    tx_submission_stats: TimingStats
    query_stats: TimingStats
    verification_stats: TimingStats
    endorsement_stats: TimingStats
    peak_tps: float = Field(..., description="Transactions processed per second under saturation")
    payload_bytes: int = Field(..., description="Serialized model update envelope size in bytes")
    ledger_growth_mb_per_100_rounds: float = Field(
        ..., description="Projected state database growth in MB per 100 federated rounds"
    )


class RAGBenchmarkResult(BaseModel):
    """Benchmarking metrics for Hybrid RAG retrieval, Hard Gate verification, and multi-factor reranking."""

    model_config = ConfigDict(extra="forbid")

    minio_fetch_stats: TimingStats
    embedding_stats: TimingStats
    dense_search_stats: TimingStats
    sparse_search_stats: TimingStats
    rrf_fusion_stats: TimingStats
    merkle_verification_stats: TimingStats
    reranking_stats: TimingStats
    total_retrieval_stats: TimingStats
    candidates_retrieved: int
    verified_evidence_count: int


class OpenAIBenchmarkResult(BaseModel):
    """Benchmarking metrics and cost calculation for OpenAI structured CTI reasoning."""

    model_config = ConfigDict(extra="forbid")

    model: str
    roundtrip_stats: TimingStats
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_per_request_usd: float
    cost_per_10k_requests_usd: float
    pricing_source: str
    pricing_effective_date: str


class E2EWorkloadResult(BaseModel):
    """Latency and cost projections under varying RAG Invocation Rates (RIR)."""

    model_config = ConfigDict(extra="forbid")

    invocation_rate: float = Field(..., ge=0.0, le=1.0, description="RIR: escalated / all flows")
    direct_path_latency_ms: float
    escalated_path_latency_ms: float
    weighted_avg_latency_ms: float
    throughput_flows_per_sec: float
    cost_usd_per_10k_flows: float


class ComprehensiveBenchmarkReport(BaseModel):
    """Complete system-level execution, timing, and resource overhead report."""

    model_config = ConfigDict(extra="forbid")

    generated_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )
    hardware_info: dict[str, Any]
    software_versions: dict[str, Any]
    local_inference: list[LocalInferenceBenchmarkResult]
    federated_learning: list[FLBenchmarkResult]
    fabric_ledger: FabricBenchmarkResult
    hybrid_rag: RAGBenchmarkResult
    openai_reasoning: OpenAIBenchmarkResult
    e2e_workloads: list[E2EWorkloadResult]
    summary_conclusions: list[str] = Field(default_factory=list)
