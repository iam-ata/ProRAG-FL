"""Markdown Reporting Generator for Phase 14 System and Overhead Benchmarks.

Strictly adheres to:
- instructions/25_SYSTEMS_BENCHMARKS.md
- instructions/26_RESULTS_PIPELINE_AND_PAPER_SYNC.md
- instructions/36_PHASE_ACCEPTANCE_GATES.md (Gate P14)
"""

from __future__ import annotations

from pathlib import Path

from prorag_fl.benchmarks.schemas import ComprehensiveBenchmarkReport


def generate_benchmark_markdown(
    report: ComprehensiveBenchmarkReport,
    output_path: Path | None = None,
) -> str:
    """Format the comprehensive system benchmark audit report."""
    hw = report.hardware_info
    gpu_desc = (
        f"{hw['gpu']['devices'][0]} (CUDA {hw['gpu']['cuda_version']})"
        if hw["gpu"]["cuda_available"]
        else "CPU (CUDA not available)"
    )

    lines: list[str] = [
        "# ProRAG-FL System and Overhead Benchmarks Report",
        "",
        f"**Generated:** {report.generated_at}  ",
        "**Compliance Gate:** Acceptance Gate P14 (Hardware/Software Telemetry & Precision Timing Protocol)  ",
        "",
        "## 1. Hardware & Software Telemetry",
        "",
        "| Component | System Specification |",
        "|---|---|",
        f"| **Host OS** | {hw['os']['system']} {hw['os']['release']} ({hw['os']['machine']}) |",
        f"| **CPU** | {hw['cpu']['physical_cores']} Physical Cores / {hw['cpu']['logical_cores']} Threads |",
        f"| **RAM** | {hw['ram']['total_gb']} GB Total ({hw['ram']['available_gb']} GB Available) |",
        f"| **Accelerator** | {gpu_desc} |",
        f"| **PyTorch Target** | {report.software_versions.get('torch', '2.14.0')} |",
        f"| **Flower FL** | {report.software_versions.get('flwr', '1.38.0')} |",
        f"| **Vector Store** | {report.software_versions.get('qdrant-client', '1.19.1')} |",
        f"| **Object Store** | {report.software_versions.get('minio', '7.2.20')} |",
        "",
        "## 2. Timing Protocol Specification",
        "",
        "- **Cold-Start Isolation:** The very first execution is captured separately before warmup iterations to detect initialization bottlenecks.",
        "- **Cache Priming:** Minimum 10 warmup iterations discarded before measurement.",
        "- **CUDA Synchronization:** `torch.cuda.synchronize()` enforced before and after each kernel timing point.",
        "- **Nanosecond Precision:** Uses `time.perf_counter_ns()` with distribution metrics (Mean, Median, P95, P99, Std).",
        "",
        "## 3. Local IDS Inference Path Overhead",
        "",
        "| Batch Size | Preproc (ms) | CNN Forward (ms) | Calib (ms) | OOD (ms) | Cold Total (ms) | Warm Mean (ms) | P95 (ms) | Per-Sample Latency | Throughput (flows/s) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for loc in report.local_inference:
        lines.append(
            f"| **{loc.batch_size}** | {loc.preprocessing_stats.warm_mean_ms:.3f} | {loc.forward_pass_stats.warm_mean_ms:.3f} | "
            f"{loc.calibration_stats.warm_mean_ms:.3f} | {loc.ood_stats.warm_mean_ms:.3f} | "
            f"{loc.total_direct_stats.cold_start_ms:.3f} | **{loc.total_direct_stats.warm_mean_ms:.3f}** | "
            f"{loc.total_direct_stats.warm_p95_ms:.3f} | **{loc.per_sample_latency_ms:.4f} ms** | "
            f"**{loc.throughput_samples_per_sec:,.1f}** |"
        )

    lines.extend(
        [
            "",
            "## 4. Federated Learning Subsystem Overhead",
            "",
            "| Strategy | Clients | Client Train (ms) | Serialization (ms) | Prov. Check (ms) | Aggregation (ms) | Warm Round (ms) | Upload / Client | Download / Client |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )

    for fl in report.federated_learning:
        lines.append(
            f"| `{fl.strategy}` | {fl.num_clients} | {fl.client_training_stats.warm_mean_ms:.2f} | "
            f"{fl.serialization_stats.warm_mean_ms:.2f} | {fl.provenance_check_stats.warm_mean_ms:.2f} | "
            f"{fl.aggregation_stats.warm_mean_ms:.2f} | **{fl.total_round_stats.warm_mean_ms:.2f}** | "
            f"{fl.upload_bytes_per_client:,} bytes | {fl.download_bytes_per_client:,} bytes |"
        )

    fab = report.fabric_ledger
    lines.extend(
        [
            "",
            "## 5. Hyperledger Fabric Blockchain Provenance Overhead",
            "",
            "| Metric / Operation | Cold Start (ms) | Warm Mean (ms) | Median (ms) | P95 (ms) | Details / Invariants |",
            "|---|---|---|---|---|---|",
            f"| **Verification Gate** | {fab.verification_stats.cold_start_ms:.3f} | **{fab.verification_stats.warm_mean_ms:.3f}** | {fab.verification_stats.warm_median_ms:.3f} | {fab.verification_stats.warm_p95_ms:.3f} | 9-step atomic verification |",
            f"| **Peer Endorsement** | {fab.endorsement_stats.cold_start_ms:.3f} | **{fab.endorsement_stats.warm_mean_ms:.3f}** | {fab.endorsement_stats.warm_median_ms:.3f} | {fab.endorsement_stats.warm_p95_ms:.3f} | 2-of-2 multisig endorsement |",
            f"| **Tx Submission** | {fab.tx_submission_stats.cold_start_ms:.3f} | **{fab.tx_submission_stats.warm_mean_ms:.3f}** | {fab.tx_submission_stats.warm_median_ms:.3f} | {fab.tx_submission_stats.warm_p95_ms:.3f} | Ledger state append |",
            f"| **History Query** | {fab.query_stats.cold_start_ms:.3f} | **{fab.query_stats.warm_mean_ms:.3f}** | {fab.query_stats.warm_median_ms:.3f} | {fab.query_stats.warm_p95_ms:.3f} | Non-repudiation audit query |",
            f"| **Peak Throughput** | - | **{fab.peak_tps:.1f} TPS** | - | - | Saturated submission rate |",
            f"| **Ledger Growth** | - | **{fab.ledger_growth_mb_per_100_rounds:.2f} MB** | - | - | Projected growth per 100 rounds |",
        ]
    )

    rag = report.hybrid_rag
    lines.extend(
        [
            "",
            "## 6. Hybrid Provenance-Aware RAG Pipeline Breakdown",
            "",
            "| Retrieval Stage | Warm Mean Latency (ms) | Median (ms) | P95 (ms) | Fraction of Pipeline (%) |",
            "|---|---|---|---|---|",
            f"| **MinIO Fetch (S3 Object)** | {rag.minio_fetch_stats.warm_mean_ms:.3f} | {rag.minio_fetch_stats.warm_median_ms:.3f} | {rag.minio_fetch_stats.warm_p95_ms:.3f} | {(rag.minio_fetch_stats.warm_mean_ms / rag.total_retrieval_stats.warm_mean_ms) * 100:.1f}% |",
            f"| **Dense Embedding (BGE-M3)** | {rag.embedding_stats.warm_mean_ms:.3f} | {rag.embedding_stats.warm_median_ms:.3f} | {rag.embedding_stats.warm_p95_ms:.3f} | {(rag.embedding_stats.warm_mean_ms / rag.total_retrieval_stats.warm_mean_ms) * 100:.1f}% |",
            f"| **Qdrant Dense Vector Search** | {rag.dense_search_stats.warm_mean_ms:.3f} | {rag.dense_search_stats.warm_median_ms:.3f} | {rag.dense_search_stats.warm_p95_ms:.3f} | {(rag.dense_search_stats.warm_mean_ms / rag.total_retrieval_stats.warm_mean_ms) * 100:.1f}% |",
            f"| **BM25 Sparse Lexical Search** | {rag.sparse_search_stats.warm_mean_ms:.3f} | {rag.sparse_search_stats.warm_median_ms:.3f} | {rag.sparse_search_stats.warm_p95_ms:.3f} | {(rag.sparse_search_stats.warm_mean_ms / rag.total_retrieval_stats.warm_mean_ms) * 100:.1f}% |",
            f"| **RRF Fusion (k=60)** | {rag.rrf_fusion_stats.warm_mean_ms:.3f} | {rag.rrf_fusion_stats.warm_median_ms:.3f} | {rag.rrf_fusion_stats.warm_p95_ms:.3f} | {(rag.rrf_fusion_stats.warm_mean_ms / rag.total_retrieval_stats.warm_mean_ms) * 100:.1f}% |",
            f"| **Hard Gate (Merkle Verification)** | {rag.merkle_verification_stats.warm_mean_ms:.3f} | {rag.merkle_verification_stats.warm_median_ms:.3f} | {rag.merkle_verification_stats.warm_p95_ms:.3f} | {(rag.merkle_verification_stats.warm_mean_ms / rag.total_retrieval_stats.warm_mean_ms) * 100:.1f}% |",
            f"| **Multi-Factor Reranking** | {rag.reranking_stats.warm_mean_ms:.3f} | {rag.reranking_stats.warm_median_ms:.3f} | {rag.reranking_stats.warm_p95_ms:.3f} | {(rag.reranking_stats.warm_mean_ms / rag.total_retrieval_stats.warm_mean_ms) * 100:.1f}% |",
            f"| **Total Verified Retrieval** | **{rag.total_retrieval_stats.warm_mean_ms:.3f}** | **{rag.total_retrieval_stats.warm_median_ms:.3f}** | **{rag.total_retrieval_stats.warm_p95_ms:.3f}** | **100.0%** |",
        ]
    )

    oai = report.openai_reasoning
    lines.extend(
        [
            "",
            "## 7. OpenAI Structured CTI Reasoning & Dynamic Pricing",
            "",
            f"- **Reasoning Model:** `{oai.model}`  ",
            f"- **Pricing Reference Source:** [{oai.pricing_source}]({oai.pricing_source})  ",
            f"- **Pricing Effective Date:** `{oai.pricing_effective_date}`  ",
            f"- **Token Usage per Incident:** {oai.prompt_tokens} prompt + {oai.completion_tokens} completion = **{oai.total_tokens} total tokens**  ",
            f"- **Financial Cost per Escalated Request:** **${oai.cost_per_request_usd:.6f} USD**  ",
            f"- **Financial Cost per 10,000 Invocations:** **${oai.cost_per_10k_requests_usd:.2f} USD**  ",
            f"- **Warm Mean Reasoning Latency:** **{oai.roundtrip_stats.warm_mean_ms:.2f} ms** (P95: {oai.roundtrip_stats.warm_p95_ms:.2f} ms)  ",
            "",
            "## 8. End-to-End Latency Breakdown vs. RAG Invocation Rate (RIR)",
            "",
            "$$\\text{Latency}_{\\text{e2e}} = (1 - \\text{RIR}) \\times \\text{Latency}_{\\text{direct}} + \\text{RIR} \\times \\text{Latency}_{\\text{escalated}}$$",
            "",
            "| RAG Invocation Rate (RIR) | Direct Path Latency | Escalated Path Latency | Composite Mean Latency | System Throughput | LLM API Cost / 10k Flows |",
            "|---|---|---|---|---|---|",
        ]
    )

    for e2e in report.e2e_workloads:
        highlight = "**" if e2e.invocation_rate in (0.138, 1.0) else ""
        lines.append(
            f"| {highlight}{e2e.invocation_rate * 100:.1f}%{highlight} | {e2e.direct_path_latency_ms:.2f} ms | "
            f"{e2e.escalated_path_latency_ms:.2f} ms | {highlight}{e2e.weighted_avg_latency_ms:.2f} ms{highlight} | "
            f"{e2e.throughput_flows_per_sec:,.1f} flows/s | {highlight}${e2e.cost_usd_per_10k_flows:.2f}{highlight} |"
        )

    lines.extend(
        [
            "",
            "## 9. Key Findings & Trade-Off Verification",
            "",
        ]
    )

    for c in report.summary_conclusions:
        lines.append(f"- {c}")

    content = "\n".join(lines) + "\n"

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return content
