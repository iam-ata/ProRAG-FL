"""Unit tests for Phase 12: Frozen Experiment Matrix & Runner.

Verifies Acceptance Gate P12:
- Matrix expansion and principled run-count bounding (no combinatorial explosion).
- Resource projections: GPU-hours, CPU-hours, disk growth, Fabric TX, OpenAI token costs.
- Run artifact schema compliance adhering strictly to instructions/40_RUN_ARTIFACT_SCHEMA.md.
- Checkpointing, resumability, and skipping runs with valid DONE marker.
- Failure handling: structured FAILED marker diagnostics.
- Smoke matrix end-to-end execution across all experiment types E1 through E10.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from prorag_fl.experiments.planner import (
    compute_resource_estimates,
    expand_matrix_plan,
    generate_planning_markdown,
)
from prorag_fl.experiments.runner import ExperimentRunner
from prorag_fl.experiments.schemas import (
    ExperimentDescriptor,
    ExperimentType,
    MatrixPlanSummary,
    RunStatus,
)
from prorag_fl.experiments.smoke import run_smoke_matrix


@pytest.mark.unit
def test_matrix_expansion_and_counting():
    """Verify matrix expansion covers E1-E10 without unconstrained explosion."""
    descriptors = expand_matrix_plan(datasets=["ciciot2023"], seeds=[13])
    assert len(descriptors) > 0

    exp_types = {d.experiment_type for d in descriptors}
    assert exp_types == set(ExperimentType)

    # Full 5-seed matrix verification
    full_descriptors = expand_matrix_plan()
    assert len(full_descriptors) == 2354

    # Verify seed isolation
    seeds_seen = {d.seed for d in full_descriptors}
    assert seeds_seen == {13, 37, 73, 101, 211}


@pytest.mark.unit
def test_resource_and_cost_estimation(tmp_path: Path):
    """Verify resource formulas produce finite, realistic estimates."""
    descriptors = expand_matrix_plan()
    summary = compute_resource_estimates(descriptors)

    assert isinstance(summary, MatrixPlanSummary)
    assert summary.total_runs == 2354
    assert summary.estimated_gpu_hours > 0.0
    assert summary.estimated_cpu_hours > 0.0
    assert summary.estimated_disk_mb > 0.0
    assert summary.estimated_fabric_tx_count > 0
    assert summary.estimated_openai_requests > 0
    assert summary.estimated_openai_cost_usd > 0.0

    report_path = tmp_path / "matrix_plan.md"
    content = generate_planning_markdown(summary, output_path=report_path)
    assert report_path.is_file()
    assert "# ProRAG-FL Full Experiment Matrix Plan & Cost Audit" in content
    assert "E1_SANITY" in content
    assert "OpenAI Est. Cost" in content


@pytest.mark.unit
def test_run_artifact_schema_compliance(tmp_path: Path):
    """Verify runner generates all required artifacts conforming to 40_RUN_ARTIFACT_SCHEMA.md."""
    runner = ExperimentRunner(runs_root=tmp_path / "runs")

    desc = ExperimentDescriptor(
        run_id="test_run_e1_compliance",
        experiment_type=ExperimentType.E1_SANITY,
        dataset="ciciot2023",
        method="b1_centralized",
        seed=13,
        num_clients=1,
        global_rounds=1,
        local_epochs=1,
    )

    status, res = runner.run_descriptor(descriptor=desc, force_rerun=True)
    assert status == RunStatus.COMPLETED

    run_dir = runner.runs_root / desc.run_id
    assert run_dir.is_dir()

    # Required files from 40_RUN_ARTIFACT_SCHEMA.md
    expected_files = [
        "config.resolved.yaml",
        "environment.json",
        "dataset_manifest_ref.json",
        "split_manifest_ref.json",
        "metrics.json",
        "metrics_per_class.csv",
        "timings.json",
        "stdout.log",
        "stderr.log",
        "artifact_manifest.json",
        "DONE",
    ]

    for fname in expected_files:
        p = run_dir / fname
        assert p.is_file(), f"Missing required artifact: {fname}"

    # Verify manifest integrity
    manifest_data = json.loads((run_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert manifest_data["run_id"] == desc.run_id
    assert manifest_data["schema_version"] == "1.0.0"
    assert len(manifest_data["artifacts"]) >= len(expected_files) - 2

    # Verify DONE marker
    done_data = json.loads((run_dir / "DONE").read_text(encoding="utf-8"))
    assert done_data["status"] == "COMPLETED"
    assert done_data["duration_sec"] >= 0.0


@pytest.mark.unit
def test_run_resumability_skips_done(tmp_path: Path):
    """Verify that runner skips runs with an existing valid DONE marker."""
    runner = ExperimentRunner(runs_root=tmp_path / "runs")

    desc = ExperimentDescriptor(
        run_id="test_run_resumable",
        experiment_type=ExperimentType.E1_SANITY,
        dataset="ciciot2023",
        method="b0_local",
        seed=13,
        num_clients=1,
        global_rounds=1,
        local_epochs=1,
    )

    status1, _ = runner.run_descriptor(descriptor=desc, force_rerun=False)
    assert status1 == RunStatus.COMPLETED

    # Second invocation without force_rerun must return SKIPPED
    status2, res2 = runner.run_descriptor(descriptor=desc, force_rerun=False)
    assert status2 == RunStatus.SKIPPED
    assert res2["status"] == "SKIPPED"


@pytest.mark.unit
def test_run_failure_records_failed_marker(tmp_path: Path):
    """Verify that an execution error properly writes FAILED marker with diagnostic record."""
    runner = ExperimentRunner(runs_root=tmp_path / "runs")

    desc = ExperimentDescriptor(
        run_id="test_run_failure",
        experiment_type=ExperimentType.E1_SANITY,
        dataset="ciciot2023",
        method="b1_centralized",
        seed=13,
        num_clients=1,
        global_rounds=1,
        local_epochs=1,
    )

    # Patch _execute_experiment to raise a simulated runtime error
    with patch.object(
        runner,
        "_execute_experiment",
        side_effect=RuntimeError("Simulated infrastructure CUDA memory failure"),
    ):
        with pytest.raises(RuntimeError, match="Simulated infrastructure"):
            runner.run_descriptor(descriptor=desc, force_rerun=True)

    run_dir = runner.runs_root / desc.run_id
    assert (run_dir / "FAILED").is_file()
    assert not (run_dir / "DONE").is_file()

    fail_data = json.loads((run_dir / "FAILED").read_text(encoding="utf-8"))
    assert fail_data["error_type"] == "RuntimeError"
    assert "Simulated infrastructure" in fail_data["error_message"]
    assert "Traceback" in fail_data["traceback"]


@pytest.mark.unit
def test_smoke_matrix_all_pass(tmp_path: Path):
    """Acceptance Gate P12: Verify smoke matrix executes all 10 experiment types E1-E10."""
    smoke_root = tmp_path / "smoke_runs"
    summary = run_smoke_matrix(runs_root=smoke_root, force_rerun=True)

    assert summary["all_passed"] is True
    assert summary["total_runs"] == 10
    assert summary["passed_runs"] == 10

    # Ensure all 10 types are represented
    tested_types = {r["experiment_type"] for r in summary["results"]}
    assert len(tested_types) == 10
    for exp_t in ExperimentType:
        assert exp_t.value in tested_types
