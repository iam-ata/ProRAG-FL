"""Experiment Matrix Planner and Cost Control.

Strictly adheres to:
- instructions/23_EXPERIMENT_MATRIX.md
- instructions/41_FULL_MATRIX_PLANNING_AND_COST_CONTROL.md
"""

from __future__ import annotations

from pathlib import Path

from prorag_fl.experiments.schemas import (
    ExperimentDescriptor,
    ExperimentType,
    MatrixPlanSummary,
)

STANDARD_SEEDS = [13, 37, 73, 101, 211]
DEFAULT_DATASETS = ["ciciot2023", "edge_iiotset"]


def expand_matrix_plan(
    datasets: list[str] | None = None,
    seeds: list[int] | None = None,
    include_experiments: list[ExperimentType] | None = None,
) -> list[ExperimentDescriptor]:
    """Deterministically expand the complete frozen experiment matrix.

    Generates only principled, non-combinatorial runs specified in
    instructions/23_EXPERIMENT_MATRIX.md.
    """
    target_datasets = datasets or DEFAULT_DATASETS
    target_seeds = seeds or STANDARD_SEEDS
    exp_filter = set(include_experiments) if include_experiments else set(ExperimentType)

    descriptors: list[ExperimentDescriptor] = []

    # -------------------------------------------------------------
    # E1: Local / Centralized Sanity
    # -------------------------------------------------------------
    if ExperimentType.E1_SANITY in exp_filter:
        for ds in target_datasets:
            for seed in target_seeds:
                for method in ["b0_local", "b1_centralized"]:
                    run_id = f"e1_sanity_{ds}_{method}_seed{seed}"
                    descriptors.append(
                        ExperimentDescriptor(
                            run_id=run_id,
                            experiment_type=ExperimentType.E1_SANITY,
                            dataset=ds,  # type: ignore[arg-type]
                            method=method,
                            seed=seed,
                            num_clients=10 if method == "b0_local" else 1,
                            global_rounds=1,
                            local_epochs=5,
                        )
                    )

    # -------------------------------------------------------------
    # E2: FL Heterogeneity (K=10; IID + alphas 1.0, 0.5, 0.3, 0.1)
    # -------------------------------------------------------------
    if ExperimentType.E2_HETEROGENEITY in exp_filter:
        alphas = [None, 1.0, 0.5, 0.3, 0.1]
        e2_methods = [
            "fedavg",
            "multikrum",
            "fedtrimmedavg",
            "sflnid",
            "pfl_ids",
            "prorag_fl",
        ]
        for ds in target_datasets:
            for alpha in alphas:
                alpha_str = f"a{alpha}" if alpha is not None else "iid"
                for method in e2_methods:
                    for seed in target_seeds:
                        run_id = f"e2_hetero_{ds}_{alpha_str}_{method}_seed{seed}"
                        descriptors.append(
                            ExperimentDescriptor(
                                run_id=run_id,
                                experiment_type=ExperimentType.E2_HETEROGENEITY,
                                dataset=ds,  # type: ignore[arg-type]
                                method=method,
                                seed=seed,
                                num_clients=10,
                                alpha=alpha,
                                global_rounds=20,
                                local_epochs=2,
                            )
                        )

    # -------------------------------------------------------------
    # E3: Scalability (K in [5, 10, 20])
    # -------------------------------------------------------------
    if ExperimentType.E3_SCALABILITY in exp_filter:
        client_scales = [5, 10, 20]
        e3_methods = ["fedtrimmedavg", "prorag_fl"]
        for ds in target_datasets:
            for k in client_scales:
                for method in e3_methods:
                    for seed in target_seeds:
                        run_id = f"e3_scale_{ds}_k{k}_{method}_seed{seed}"
                        descriptors.append(
                            ExperimentDescriptor(
                                run_id=run_id,
                                experiment_type=ExperimentType.E3_SCALABILITY,
                                dataset=ds,  # type: ignore[arg-type]
                                method=method,
                                seed=seed,
                                num_clients=k,
                                alpha=0.3,
                                global_rounds=15,
                                local_epochs=2,
                            )
                        )

    # -------------------------------------------------------------
    # E4: Malicious Clients (fractions 10%, 20%, 30%, 40%)
    # -------------------------------------------------------------
    if ExperimentType.E4_MALICIOUS_CLIENTS in exp_filter:
        mal_fractions = [0.10, 0.20, 0.30, 0.40]
        attacks = ["label_flip", "sign_flip", "model_replacement", "backdoor"]
        e4_methods = [
            "fedavg",
            "multikrum",
            "fedtrimmedavg",
            "flow",
            "pfl_ids",
            "prorag_fl",
        ]
        for ds in target_datasets:
            for mal_f in mal_fractions:
                pct = int(mal_f * 100)
                for atk in attacks:
                    for method in e4_methods:
                        for seed in target_seeds:
                            run_id = f"e4_mal_{ds}_{atk}_f{pct}_{method}_seed{seed}"
                            descriptors.append(
                                ExperimentDescriptor(
                                    run_id=run_id,
                                    experiment_type=ExperimentType.E4_MALICIOUS_CLIENTS,
                                    dataset=ds,  # type: ignore[arg-type]
                                    method=method,
                                    seed=seed,
                                    num_clients=10,
                                    alpha=0.3,
                                    attack_type=atk,
                                    malicious_fraction=mal_f,
                                    global_rounds=15,
                                    local_epochs=2,
                                )
                            )

    # -------------------------------------------------------------
    # E5: Provenance Attacks (digest, replay, stale, version, sybil)
    # -------------------------------------------------------------
    if ExperimentType.E5_PROVENANCE_ATTACKS in exp_filter:
        prov_attacks = [
            "digest_tamper",
            "nonce_replay",
            "stale_round",
            "wrong_version",
            "unauthorized_identity",
            "revoked_status",
        ]
        for ds in target_datasets:
            for atk in prov_attacks:
                for seed in target_seeds:
                    run_id = f"e5_prov_{ds}_{atk}_seed{seed}"
                    descriptors.append(
                        ExperimentDescriptor(
                            run_id=run_id,
                            experiment_type=ExperimentType.E5_PROVENANCE_ATTACKS,
                            dataset=ds,  # type: ignore[arg-type]
                            method="prorag_fl",
                            seed=seed,
                            num_clients=10,
                            attack_type=atk,
                            malicious_fraction=0.20,
                            global_rounds=5,
                            local_epochs=1,
                        )
                    )

    # -------------------------------------------------------------
    # E6: Unseen-to-Model (Held-out zero-day evaluation)
    # -------------------------------------------------------------
    if ExperimentType.E6_UNSEEN_TO_MODEL in exp_filter:
        e6_methods = ["ids_only", "fedmse", "standard_rag", "rlfe_ids", "prorag_fl"]
        for ds in target_datasets:
            held_out = "Mirai" if ds == "ciciot2023" else "Malware"
            for method in e6_methods:
                for seed in target_seeds:
                    run_id = f"e6_unseen_{ds}_{held_out}_{method}_seed{seed}"
                    descriptors.append(
                        ExperimentDescriptor(
                            run_id=run_id,
                            experiment_type=ExperimentType.E6_UNSEEN_TO_MODEL,
                            dataset=ds,  # type: ignore[arg-type]
                            method=method,
                            seed=seed,
                            num_clients=10,
                            parameters={"held_out_family": held_out},
                            global_rounds=10,
                            local_epochs=2,
                        )
                    )

    # -------------------------------------------------------------
    # E7: RAG Poisoning (Corpus fractions 5%, 10%, 20%, 30%)
    # -------------------------------------------------------------
    if ExperimentType.E7_RAG_POISONING in exp_filter:
        rag_fractions = [0.05, 0.10, 0.20, 0.30]
        rag_attacks = [
            "knowledge_tampering",
            "unauthorized_insertion",
            "stale_replay",
            "prompt_injection",
            "malicious_source",
        ]
        rag_methods = [
            "standard_rag",
            "hard_gate_rag",
            "provenance_freshness_rag",
            "prorag_fl",
        ]
        for ds in target_datasets:
            for p_frac in rag_fractions:
                p_pct = int(p_frac * 100)
                for atk in rag_attacks:
                    for method in rag_methods:
                        for seed in target_seeds:
                            run_id = f"e7_rag_poison_{ds}_{atk}_p{p_pct}_{method}_seed{seed}"
                            descriptors.append(
                                ExperimentDescriptor(
                                    run_id=run_id,
                                    experiment_type=ExperimentType.E7_RAG_POISONING,
                                    dataset=ds,  # type: ignore[arg-type]
                                    method=method,
                                    seed=seed,
                                    attack_type=atk,
                                    rag_poison_fraction=p_frac,
                                    global_rounds=5,
                                    local_epochs=1,
                                )
                            )

    # -------------------------------------------------------------
    # E8: Ablation Ladder (A0 to A6)
    # -------------------------------------------------------------
    if ExperimentType.E8_ABLATION in exp_filter:
        ablation_ladder = ["A0", "A1", "A2", "A3", "A4", "A5", "A6"]
        for ds in target_datasets:
            for abl in ablation_ladder:
                for seed in target_seeds:
                    run_id = f"e8_ablation_{ds}_{abl}_seed{seed}"
                    descriptors.append(
                        ExperimentDescriptor(
                            run_id=run_id,
                            experiment_type=ExperimentType.E8_ABLATION,
                            dataset=ds,  # type: ignore[arg-type]
                            method="ablation",
                            ablation_id=abl,
                            seed=seed,
                            num_clients=10,
                            alpha=0.3,
                            global_rounds=15,
                            local_epochs=2,
                        )
                    )

    # -------------------------------------------------------------
    # E9: Systems Benchmarking (Overhead measurements)
    # -------------------------------------------------------------
    if ExperimentType.E9_SYSTEMS in exp_filter:
        for ds in target_datasets:
            for seed in target_seeds:
                run_id = f"e9_systems_{ds}_seed{seed}"
                descriptors.append(
                    ExperimentDescriptor(
                        run_id=run_id,
                        experiment_type=ExperimentType.E9_SYSTEMS,
                        dataset=ds,  # type: ignore[arg-type]
                        method="prorag_fl",
                        seed=seed,
                        num_clients=10,
                        global_rounds=10,
                        local_epochs=2,
                    )
                )

    # -------------------------------------------------------------
    # E10: Validation Sensitivity (Validation splits only)
    # -------------------------------------------------------------
    if ExperimentType.E10_VALIDATION_SENSITIVITY in exp_filter:
        betas = [0.10, 0.15, 0.20, 0.25]
        tau_cs = [0.60, 0.75, 0.90]
        for ds in target_datasets:
            for beta in betas:
                for tc in tau_cs:
                    run_id = f"e10_sens_{ds}_b{int(beta * 100)}_tc{int(tc * 100)}"
                    descriptors.append(
                        ExperimentDescriptor(
                            run_id=run_id,
                            experiment_type=ExperimentType.E10_VALIDATION_SENSITIVITY,
                            dataset=ds,  # type: ignore[arg-type]
                            method="prorag_fl",
                            seed=13,  # Validation tuning on single standard seed
                            num_clients=10,
                            parameters={"beta": beta, "tau_c": tc},
                            global_rounds=10,
                            local_epochs=1,
                        )
                    )

    return descriptors


def compute_resource_estimates(
    descriptors: list[ExperimentDescriptor],
) -> MatrixPlanSummary:
    """Compute empirical run counts and resource estimates.

    Strictly adheres to instructions/41_FULL_MATRIX_PLANNING_AND_COST_CONTROL.md.
    """
    total = len(descriptors)
    by_exp: dict[str, int] = {}
    by_ds: dict[str, int] = {}
    by_meth: dict[str, int] = {}
    by_sd: dict[str, int] = {}

    total_rounds = 0
    total_clients_steps = 0
    total_fabric_tx = 0
    total_openai_requests = 0

    for d in descriptors:
        by_exp[d.experiment_type.value] = by_exp.get(d.experiment_type.value, 0) + 1
        by_ds[d.dataset] = by_ds.get(d.dataset, 0) + 1
        by_meth[d.method] = by_meth.get(d.method, 0) + 1
        by_sd[str(d.seed)] = by_sd.get(str(d.seed), 0) + 1

        rounds = d.global_rounds
        clients = d.num_clients
        epochs = d.local_epochs

        total_rounds += rounds
        total_clients_steps += rounds * clients * epochs

        # Fabric TX: Each client update + 1 aggregation block per round
        if "prorag" in d.method or d.experiment_type in [
            ExperimentType.E5_PROVENANCE_ATTACKS,
            ExperimentType.E9_SYSTEMS,
        ]:
            total_fabric_tx += rounds * (clients + 1)

        # OpenAI reasoning requests: Evaluated in E6, E7, and ProRAG-FL escalated events
        if d.experiment_type in [
            ExperimentType.E6_UNSEEN_TO_MODEL,
            ExperimentType.E7_RAG_POISONING,
        ]:
            # Estimated ~100 escalated samples per evaluation split in zero-day/tampered regimes
            total_openai_requests += 100

    # Resource formulas:
    # 1 client step (1 epoch on ~2560 flows) ≈ 0.8 seconds GPU / 2.5 seconds CPU
    estimated_gpu_hours = (total_clients_steps * 0.8) / 3600.0
    estimated_cpu_hours = (total_clients_steps * 2.5) / 3600.0

    # Disk growth: ~2.5 MB per run (checkpoints, metrics, logs, envelopes)
    estimated_disk_mb = total * 2.5

    # OpenAI Pricing (GPT-4o-mini: $0.15/1M input tokens, $0.60/1M output tokens)
    # Average ~1,200 input tokens (evidence + prompt) + ~350 output tokens per reasoning call
    input_tokens = total_openai_requests * 1200
    output_tokens = total_openai_requests * 350
    estimated_cost_usd = (input_tokens / 1_000_000 * 0.15) + (output_tokens / 1_000_000 * 0.60)

    return MatrixPlanSummary(
        total_runs=total,
        runs_by_experiment=by_exp,
        runs_by_dataset=by_ds,
        runs_by_method=by_meth,
        runs_by_seed=by_sd,
        estimated_gpu_hours=round(estimated_gpu_hours, 2),
        estimated_cpu_hours=round(estimated_cpu_hours, 2),
        estimated_disk_mb=round(estimated_disk_mb, 1),
        estimated_fabric_tx_count=total_fabric_tx,
        estimated_openai_requests=total_openai_requests,
        estimated_openai_cost_usd=round(estimated_cost_usd, 4),
    )


def generate_planning_markdown(summary: MatrixPlanSummary, output_path: Path | None = None) -> str:
    """Format a comprehensive Markdown audit report for the experiment matrix."""
    lines: list[str] = [
        "# ProRAG-FL Full Experiment Matrix Plan & Cost Audit",
        "",
        f"**Generated:** {summary.generated_at}  ",
        f"**Total Runs Planned:** `{summary.total_runs}`  ",
        "",
        "## 1. Run Count Breakdown by Experiment",
        "",
        "| Experiment ID | Focus Area | Run Count |",
        "|---|---|---|",
    ]

    exp_labels = {
        "E1_SANITY": "Local 1D-CNN vs Centralized Oracle Ceiling",
        "E2_HETEROGENEITY": "FL Non-IID Dirichlet Partitioning & Heterogeneity",
        "E3_SCALABILITY": "Client Scaling (K=5, 10, 20)",
        "E4_MALICIOUS_CLIENTS": "Byzantine Update Poisoning & Backdoors (0-40%)",
        "E5_PROVENANCE_ATTACKS": "Blockchain & Provenance Layer Tampering",
        "E6_UNSEEN_TO_MODEL": "Zero-Day Unseen Family Escalation & Reasoning",
        "E7_RAG_POISONING": "Knowledge Base Poisoning & Prompt Injection",
        "E8_ABLATION": "Main Ablation Ladder (A0 through A6)",
        "E9_SYSTEMS": "End-to-End Systems Latency & Communication",
        "E10_VALIDATION_SENSITIVITY": "Validation Hyperparameter Grid Search",
    }

    for exp_id, count in sorted(summary.runs_by_experiment.items()):
        label = exp_labels.get(exp_id, exp_id)
        lines.append(f"| `{exp_id}` | {label} | {count} |")

    lines.extend(
        [
            "",
            "## 2. Resource Projections",
            "",
            "| Resource Category | Estimated Metric | Notes |",
            "|---|---|---|",
            f"| **GPU Compute** | `{summary.estimated_gpu_hours:.2f} GPU-hours` | Based on PyTorch 1D-CNN batch processing |",
            f"| **CPU Compute** | `{summary.estimated_cpu_hours:.2f} CPU-hours` | Including FL client aggregation & Krum distance |",
            f"| **Disk Storage** | `{summary.estimated_disk_mb:.1f} MB` | Metrics, checkpoints, logs, and run manifests |",
            f"| **Fabric Transactions** | `{summary.estimated_fabric_tx_count:,}` | Provenance envelopes and block commits |",
            f"| **OpenAI API Calls** | `{summary.estimated_openai_requests:,}` | Zero-day and RAG poisoning reasoning samples |",
            f"| **OpenAI Est. Cost** | `${summary.estimated_openai_cost_usd:.4f} USD` | At GPT-4o-mini current token rates |",
            "",
            "## 3. Strict Scientific Safeguards",
            "- Final evaluations executed across standard seeds: `13, 37, 73, 101, 211`.",
            "- Ground-truth labels strictly isolated from reasoning payloads (evaluation-only).",
            "- Checkpointing and resumability enforced via immutable `DONE` markers.",
            "- Zero data snooping: hyperparameters tuned exclusively on validation splits.",
        ]
    )

    content = "\n".join(lines) + "\n"

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return content
