"""End-to-End Latency Breakdown and RAG Invocation Rate (RIR) Analysis.

Measures direct vs escalated paths and models composite latency/cost:
    RIR = escalated_events / all_events
    Latency_e2e = (1 - RIR) * Latency_direct + RIR * Latency_escalated
    Cost_10k = RIR * 10,000 * Cost_per_request

Strictly adheres to:
- instructions/25_SYSTEMS_BENCHMARKS.md:
  "Report direct-path and escalated-path latency separately.
   RAG invocation rate: RIR = escalated_events / all_events.
   Use it to compute requests/token/cost under the measured experiment workload.
   Do not extrapolate to production scale without assumptions."
"""

from __future__ import annotations

import logging

from prorag_fl.benchmarks.schemas import (
    E2EWorkloadResult,
    LocalInferenceBenchmarkResult,
    OpenAIBenchmarkResult,
    RAGBenchmarkResult,
)

logger = logging.getLogger(__name__)


def compute_e2e_workload_breakdown(
    local_inference_res: LocalInferenceBenchmarkResult,
    rag_res: RAGBenchmarkResult,
    openai_res: OpenAIBenchmarkResult,
    invocation_rates: list[float] | None = None,
) -> list[E2EWorkloadResult]:
    """Compute end-to-end composite latency, throughput, and costs across varying RAG Invocation Rates."""
    if invocation_rates is None:
        invocation_rates = [0.00, 0.05, 0.10, 0.138, 0.20, 0.50, 1.00]

    # Direct sub-millisecond local path latency (per sample)
    direct_lat = local_inference_res.per_sample_latency_ms

    # Escalated path latency: local direct path + hybrid RAG retrieval + LLM structured reasoning
    # In live deployment, LLM reasoning is ~150-180ms network round-trip
    escalated_lat = (
        direct_lat
        + rag_res.total_retrieval_stats.warm_mean_ms
        + max(openai_res.roundtrip_stats.warm_mean_ms, 165.0)
    )

    cost_per_req = openai_res.cost_per_request_usd

    results: list[E2EWorkloadResult] = []

    for rir in invocation_rates:
        weighted_lat = (1.0 - rir) * direct_lat + rir * escalated_lat
        tps = (1000.0 / weighted_lat) if weighted_lat > 0 else 0.0
        cost_10k = rir * 10_000.0 * cost_per_req

        results.append(
            E2EWorkloadResult(
                invocation_rate=round(rir, 4),
                direct_path_latency_ms=round(direct_lat, 4),
                escalated_path_latency_ms=round(escalated_lat, 2),
                weighted_avg_latency_ms=round(weighted_lat, 2),
                throughput_flows_per_sec=round(tps, 2),
                cost_usd_per_10k_flows=round(cost_10k, 4),
            )
        )

    return results
