"""Smoke Matrix Execution Engine for Acceptance Gate P12.

Executes a minimal, representative smoke batch spanning all experiment types
E1 through E10 to verify end-to-end execution, schema compliance, and artifact manifests.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from prorag_fl.experiments.runner import ExperimentRunner
from prorag_fl.experiments.schemas import (
    ExperimentDescriptor,
    ExperimentType,
    RunStatus,
)

logger = logging.getLogger(__name__)


def generate_smoke_descriptors() -> list[ExperimentDescriptor]:
    """Generate exactly 1 representative fast descriptor per experiment type E1-E10."""
    return [
        # E1: Local/Centralized Sanity
        ExperimentDescriptor(
            run_id="smoke_e1_sanity_b1_centralized",
            experiment_type=ExperimentType.E1_SANITY,
            dataset="ciciot2023",
            method="b1_centralized",
            seed=13,
            num_clients=1,
            global_rounds=1,
            local_epochs=1,
        ),
        # E2: FL Heterogeneity
        ExperimentDescriptor(
            run_id="smoke_e2_hetero_fedavg_a03",
            experiment_type=ExperimentType.E2_HETEROGENEITY,
            dataset="ciciot2023",
            method="fedavg",
            seed=13,
            num_clients=3,
            alpha=0.3,
            global_rounds=2,
            local_epochs=1,
        ),
        # E3: Scalability
        ExperimentDescriptor(
            run_id="smoke_e3_scale_k5",
            experiment_type=ExperimentType.E3_SCALABILITY,
            dataset="ciciot2023",
            method="fedtrimmedavg",
            seed=13,
            num_clients=5,
            alpha=0.3,
            global_rounds=2,
            local_epochs=1,
        ),
        # E4: Malicious Clients
        ExperimentDescriptor(
            run_id="smoke_e4_mal_label_flip_f20",
            experiment_type=ExperimentType.E4_MALICIOUS_CLIENTS,
            dataset="ciciot2023",
            method="fedtrimmedavg",
            seed=13,
            num_clients=5,
            attack_type="label_flip",
            malicious_fraction=0.20,
            global_rounds=2,
            local_epochs=1,
        ),
        # E5: Provenance Attacks
        ExperimentDescriptor(
            run_id="smoke_e5_prov_tamper",
            experiment_type=ExperimentType.E5_PROVENANCE_ATTACKS,
            dataset="ciciot2023",
            method="prorag_fl",
            seed=13,
            num_clients=3,
            attack_type="digest_tamper",
            malicious_fraction=0.33,
            global_rounds=2,
            local_epochs=1,
        ),
        # E6: Unseen-to-Model
        ExperimentDescriptor(
            run_id="smoke_e6_unseen_mirai",
            experiment_type=ExperimentType.E6_UNSEEN_TO_MODEL,
            dataset="ciciot2023",
            method="prorag_fl",
            seed=13,
            num_clients=3,
            parameters={"held_out_family": "Mirai"},
            global_rounds=2,
            local_epochs=1,
        ),
        # E7: RAG Poisoning
        ExperimentDescriptor(
            run_id="smoke_e7_rag_poison_prompt_inj",
            experiment_type=ExperimentType.E7_RAG_POISONING,
            dataset="ciciot2023",
            method="prorag_fl",
            seed=13,
            num_clients=3,
            attack_type="prompt_injection",
            rag_poison_fraction=0.10,
            global_rounds=2,
            local_epochs=1,
        ),
        # E8: Ablation Ladder
        ExperimentDescriptor(
            run_id="smoke_e8_ablation_a2",
            experiment_type=ExperimentType.E8_ABLATION,
            dataset="ciciot2023",
            method="ablation",
            ablation_id="A2",
            seed=13,
            num_clients=3,
            alpha=0.3,
            global_rounds=2,
            local_epochs=1,
        ),
        # E9: Systems Benchmarking
        ExperimentDescriptor(
            run_id="smoke_e9_systems_overhead",
            experiment_type=ExperimentType.E9_SYSTEMS,
            dataset="ciciot2023",
            method="prorag_fl",
            seed=13,
            num_clients=3,
            global_rounds=2,
            local_epochs=1,
        ),
        # E10: Validation Sensitivity
        ExperimentDescriptor(
            run_id="smoke_e10_sens_beta_tc",
            experiment_type=ExperimentType.E10_VALIDATION_SENSITIVITY,
            dataset="ciciot2023",
            method="prorag_fl",
            seed=13,
            num_clients=3,
            parameters={"beta": 0.20, "tau_c": 0.80},
            global_rounds=2,
            local_epochs=1,
        ),
    ]


def run_smoke_matrix(
    runs_root: Path | None = None,
    force_rerun: bool = True,
) -> dict[str, Any]:
    """Execute all 10 smoke descriptors and verify compliance with 40_RUN_ARTIFACT_SCHEMA.md."""
    runner = ExperimentRunner(runs_root=runs_root)
    descriptors = generate_smoke_descriptors()

    results: list[dict[str, Any]] = []
    all_passed = True

    for desc in descriptors:
        status, res = runner.run_descriptor(descriptor=desc, force_rerun=force_rerun)
        run_dir = runner.runs_root / desc.run_id

        # Verify critical artifacts exist
        required_files = [
            "config.resolved.yaml",
            "environment.json",
            "dataset_manifest_ref.json",
            "split_manifest_ref.json",
            "metrics.json",
            "timings.json",
            "artifact_manifest.json",
            "DONE",
        ]
        missing_files = [f for f in required_files if not (run_dir / f).is_file()]

        passed = (status in [RunStatus.COMPLETED, RunStatus.SKIPPED]) and len(missing_files) == 0
        if not passed:
            all_passed = False

        results.append(
            {
                "run_id": desc.run_id,
                "experiment_type": desc.experiment_type.value,
                "status": status.value,
                "passed": passed,
                "missing_files": missing_files,
            }
        )

    return {
        "all_passed": all_passed,
        "total_runs": len(results),
        "passed_runs": sum(1 for r in results if r["passed"]),
        "results": results,
    }
