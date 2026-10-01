"""Unit tests for Phase 13: Architectural Ablation Ladder & Parameter Sensitivity.

Strictly tests:
- instructions/24_ABLATION_AND_SENSITIVITY.md
- instructions/02_LOCKED_PROPOSED_METHOD.md
- instructions/36_PHASE_ACCEPTANCE_GATES.md (Gate P13: all ablations reproducible; parameters frozen)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from prorag_fl.ablations.ladder import (
    AblationLadderRunner,
    get_ladder_config,
)
from prorag_fl.ablations.reporting import (
    generate_ladder_markdown,
    generate_sensitivity_markdown,
)
from prorag_fl.ablations.schemas import (
    AblationLadderReport,
    AblationStepConfig,
    AblationStepResult,
    FrozenParametersRecord,
    LadderStep,
)
from prorag_fl.ablations.sensitivity import (
    SensitivityEvaluator,
    assert_parameters_frozen,
    load_frozen_parameters,
)


def test_ladder_step_configs_completeness() -> None:
    """Verify that all 7 canonical ablation ladder steps A0 through A6 are well-defined."""
    steps = [
        LadderStep.A0,
        LadderStep.A1,
        LadderStep.A2,
        LadderStep.A3,
        LadderStep.A4,
        LadderStep.A5,
        LadderStep.A6,
    ]
    assert len(steps) == 7

    for step in steps:
        cfg = get_ladder_config(step)
        assert isinstance(cfg, AblationStepConfig)
        assert cfg.step == step
        assert len(cfg.name) > 0
        assert len(cfg.description) > 0

    # Specific architectural invariant assertions
    a0 = get_ladder_config(LadderStep.A0)
    assert a0.fl_aggregation == "fedavg"
    assert not a0.model_provenance_enabled
    assert not a0.hybrid_rag_enabled

    a1 = get_ladder_config(LadderStep.A1)
    assert a1.fl_aggregation == "fedtrimmedavg"
    assert not a1.model_provenance_enabled

    a2 = get_ladder_config(LadderStep.A2)
    assert a2.fl_aggregation == "provenance_gated"
    assert a2.model_provenance_enabled
    assert not a2.hybrid_rag_enabled

    a3 = get_ladder_config(LadderStep.A3)
    assert a3.hybrid_rag_enabled
    assert not a3.knowledge_provenance_enabled

    a4 = get_ladder_config(LadderStep.A4)
    assert a4.knowledge_provenance_enabled
    assert not a4.multifactor_reranking_enabled

    a5 = get_ladder_config(LadderStep.A5)
    assert a5.force_all_events_escalated
    assert not a5.dual_gate_routing_enabled

    a6 = get_ladder_config(LadderStep.A6)
    assert a6.dual_gate_routing_enabled
    assert not a6.force_all_events_escalated
    assert a6.knowledge_provenance_enabled
    assert a6.multifactor_reranking_enabled


def test_ladder_execution_and_scientific_invariants() -> None:
    """Run full ablation ladder and assert expected scientific progressions and invariants."""
    runner = AblationLadderRunner(dataset="ciciot2023", seed=13)
    report = runner.run_full_ladder()

    assert isinstance(report, AblationLadderReport)
    assert report.dataset == "ciciot2023"
    assert len(report.steps) == 7

    step_results: dict[LadderStep, AblationStepResult] = {s.step: s for s in report.steps}

    # 1. Byzantine resilience recovery from A0 to A1
    a0 = step_results[LadderStep.A0]
    a1 = step_results[LadderStep.A1]
    assert a1.byzantine_resilience_f1 > a0.byzantine_resilience_f1 + 0.20

    # 2. Blockchain provenance verification rejection rate
    a2 = step_results[LadderStep.A2]
    assert a2.provenance_tamper_rejection_rate == 1.0

    # 3. Zero-day recall elevation through RAG (A2 -> A3) and Hard Provenance Gate (A3 -> A4)
    a3 = step_results[LadderStep.A3]
    a4 = step_results[LadderStep.A4]
    assert a3.zero_day_detection_recall > a2.zero_day_detection_recall + 0.40
    assert a4.zero_day_detection_recall > a3.zero_day_detection_recall

    # 4. The Routing Cost Cliff invariant (A4 -> A5 vs A6)
    a5 = step_results[LadderStep.A5]
    a6 = step_results[LadderStep.A6]
    assert a5.rag_invocation_rate == 1.0  # 100% events escalated
    assert a6.rag_invocation_rate < 0.20  # Selective routing keeps >80% on local path
    assert a5.avg_latency_ms > 5.0 * a6.avg_latency_ms  # Extreme latency inflation
    assert (
        a5.estimated_cost_usd_per_10k > 5.0 * a6.estimated_cost_usd_per_10k
    )  # Extreme cost explosion
    assert a6.macro_f1 >= a5.macro_f1  # Full ProRAG-FL achieves superior or equal performance


def test_markdown_report_generation(tmp_path: Path) -> None:
    """Verify markdown output generation for ablation ladder and sensitivity report."""
    runner = AblationLadderRunner(dataset="ciciot2023")
    report = runner.run_full_ladder()

    out_file = tmp_path / "ladder_test.md"
    md = generate_ladder_markdown(report, output_path=out_file)

    assert out_file.exists()
    assert "# ProRAG-FL Main Architectural Ablation Ladder" in md
    assert "A0" in md and "A6" in md
    assert "Routing Cost Cliff" in md

    # Sensitivity markdown
    evaluator = SensitivityEvaluator(dataset="ciciot2023")
    sens_report = evaluator.run_full_sensitivity_suite()
    sens_out_file = tmp_path / "sensitivity_test.md"
    sens_md = generate_sensitivity_markdown(sens_report, output_path=sens_out_file)

    assert sens_out_file.exists()
    assert "Beta Trimming Fraction Sweep" in sens_md
    assert "Confidence Escalation Threshold (tau_c) Sweep" in sens_md
    assert "Mahalanobis Distance Threshold (tau_m) Sweep" in sens_md


def test_sensitivity_sweeps_and_objective_scoring() -> None:
    """Verify validation-only sensitivity sweeps and multi-objective score function."""
    evaluator = SensitivityEvaluator(dataset="ciciot2023")

    # Objective formula test
    score = evaluator.compute_objective_score(
        macro_f1=0.94, operational_fpr=0.02, rag_invocation_rate=0.10
    )
    # Expected: 0.94 - 0.5*0.02 - 0.1*0.10 = 0.94 - 0.01 - 0.01 = 0.92
    assert score == pytest.approx(0.92, abs=1e-3)

    report = evaluator.run_full_sensitivity_suite()
    assert len(report.beta_sweep) == 4
    assert len(report.tau_c_sweep) == 6
    assert len(report.tau_m_sweep) == 5
    assert len(report.top_k_sweep) == 4
    assert len(report.rerank_weights_sweep) == 5

    opt = report.selected_optimal_config
    assert "beta" in opt
    assert "tau_c" in opt
    assert "tau_m" in opt
    assert opt["beta"] == 0.20
    assert opt["tau_c"] == 0.80
    assert opt["tau_m"] == 5.0


def test_parameter_freezing_and_evaluation_invariant(tmp_path: Path) -> None:
    """Verify Gate P13: write frozen parameters and strictly refuse tuning flags in test mode."""
    evaluator = SensitivityEvaluator(dataset="ciciot2023")
    report = evaluator.run_full_sensitivity_suite()

    # Freeze to isolated temporary directory
    record, file_path = evaluator.freeze_optimal_parameters(report, target_dir=tmp_path)

    assert file_path.exists()
    assert file_path.suffix == ".yaml"
    assert file_path.name == f"{record.config_hash}.yaml"
    assert isinstance(record, FrozenParametersRecord)
    assert record.dataset == "ciciot2023"
    assert record.beta == 0.20
    assert record.tau_c == 0.80
    assert record.tau_m == 5.0

    # Test loading frozen parameters
    loaded = load_frozen_parameters(dataset="ciciot2023", target_dir=tmp_path)
    assert loaded.config_hash == record.config_hash
    assert loaded.beta == record.beta

    # Test evaluation mode: pass without tuning overrides
    verified_record = assert_parameters_frozen(
        dataset="ciciot2023", requested_overrides=None, target_dir=tmp_path
    )
    assert verified_record.config_hash == record.config_hash

    # Test evaluation mode: pass with non-tuning override
    verified_record_2 = assert_parameters_frozen(
        dataset="ciciot2023", requested_overrides={"batch_size": 64}, target_dir=tmp_path
    )
    assert verified_record_2.config_hash == record.config_hash

    # Test evaluation mode: STRICT REFUSAL of hyperparameter tuning flags
    for forbidden_param in [
        "beta",
        "tau_c",
        "tau_m",
        "top_candidates",
        "top_verified",
        "lambda_rrf",
        "lambda_freshness",
        "lambda_corroboration",
    ]:
        with pytest.raises(ValueError, match="Evaluation mode violation"):
            assert_parameters_frozen(
                dataset="ciciot2023",
                requested_overrides={forbidden_param: 0.99},
                target_dir=tmp_path,
            )
