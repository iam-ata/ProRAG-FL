"""Phase 14: System and Overhead Benchmarks.

Provides:
- Precision timing protocol and hardware/software telemetry
- Component microbenchmarks (Local IDS, FL, Hyperledger Fabric, Hybrid RAG, OpenAI Reasoning)
- End-to-end composite workload breakdown across RAG Invocation Rates
- Comprehensive audit report generation for Gate P14
"""

from __future__ import annotations

from prorag_fl.benchmarks.e2e_breakdown import compute_e2e_workload_breakdown
from prorag_fl.benchmarks.fabric_overhead import benchmark_fabric_overhead
from prorag_fl.benchmarks.fl_overhead import benchmark_fl_overhead
from prorag_fl.benchmarks.local_inference import benchmark_local_inference
from prorag_fl.benchmarks.openai_overhead import benchmark_openai_overhead
from prorag_fl.benchmarks.rag_overhead import benchmark_rag_overhead
from prorag_fl.benchmarks.reporting import generate_benchmark_markdown
from prorag_fl.benchmarks.runner import MasterBenchmarkRunner
from prorag_fl.benchmarks.schemas import (
    ComprehensiveBenchmarkReport,
    E2EWorkloadResult,
    FabricBenchmarkResult,
    FLBenchmarkResult,
    LocalInferenceBenchmarkResult,
    OpenAIBenchmarkResult,
    RAGBenchmarkResult,
    TimingStats,
)
from prorag_fl.benchmarks.timing import measure_callable

__all__ = [
    "ComprehensiveBenchmarkReport",
    "E2EWorkloadResult",
    "FLBenchmarkResult",
    "FabricBenchmarkResult",
    "LocalInferenceBenchmarkResult",
    "MasterBenchmarkRunner",
    "OpenAIBenchmarkResult",
    "RAGBenchmarkResult",
    "TimingStats",
    "benchmark_fabric_overhead",
    "benchmark_fl_overhead",
    "benchmark_local_inference",
    "benchmark_openai_overhead",
    "benchmark_rag_overhead",
    "compute_e2e_workload_breakdown",
    "generate_benchmark_markdown",
    "measure_callable",
]
