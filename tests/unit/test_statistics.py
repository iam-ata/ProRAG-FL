"""Unit tests for Phase 15: Statistical Analysis & Significance Testing.

Verifies:
- Accurate sample statistics with Student-t 95% confidence intervals (ddof=1).
- Standardized effect size calculations (Cohen's d, Cliff's delta).
- Paired hypothesis testing (Wilcoxon Signed-Rank, Paired t-Test).
- Multiple-comparison corrections (Bonferroni, Benjamini-Hochberg FDR).
- MultiSeedAggregator execution across standard 5 seeds [13, 37, 73, 101, 211].
- Rejection of cherry-picking: ensures all raw seed values are retained.
- Parquet, CSV, and markdown report generation.

Strictly adheres to:
- instructions/19_METRICS_AND_STATISTICS.md
- instructions/36_PHASE_ACCEPTANCE_GATES.md (Gate P15)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from prorag_fl.analysis.aggregator import MultiSeedAggregator
from prorag_fl.analysis.reporting import generate_statistical_markdown_report
from prorag_fl.analysis.schemas import STANDARD_SEEDS
from prorag_fl.analysis.stats_engine import (
    adjust_p_values_bonferroni,
    adjust_p_values_fdr_bh,
    calculate_cliffs_delta,
    calculate_cohen_d,
    calculate_descriptive_stats,
    run_paired_significance_test,
)


def test_descriptive_stats_computation() -> None:
    """Verify descriptive statistics and Student-t 95% confidence intervals."""
    # 5 seeds with sample values
    vals = [0.935, 0.942, 0.938, 0.945, 0.940]
    stats = calculate_descriptive_stats(vals)

    assert stats.n_samples == 5
    assert len(stats.raw_values) == 5
    assert np.isclose(stats.mean, np.mean(vals), atol=1e-5)
    assert np.isclose(stats.std, np.std(vals, ddof=1), atol=1e-5)
    assert np.isclose(stats.median, np.median(vals), atol=1e-5)
    assert stats.min_val == min(vals)
    assert stats.max_val == max(vals)

    # 95% CI should bracket the mean
    assert stats.ci_95_low < stats.mean < stats.ci_95_high
    # Margin for n=5 should be t_crit * (s / sqrt(5)) where t_crit ~ 2.776
    margin = stats.ci_95_high - stats.mean
    expected_margin = 2.776445 * (stats.std / np.sqrt(5))
    assert np.isclose(margin, expected_margin, atol=1e-4)


def test_single_value_descriptive_stats() -> None:
    """Verify handling of single-element samples without division by zero."""
    stats = calculate_descriptive_stats([0.85])
    assert stats.n_samples == 1
    assert stats.mean == 0.85
    assert stats.std == 0.0
    assert stats.ci_95_low == 0.85
    assert stats.ci_95_high == 0.85


def test_empty_values_raises_error() -> None:
    """Verify error raised on empty sample."""
    with pytest.raises(ValueError, match="Cannot calculate descriptive statistics"):
        calculate_descriptive_stats([])


def test_effect_sizes_computation() -> None:
    """Verify Cohen's d and Cliff's delta calculations."""
    a = [0.94, 0.95, 0.93, 0.96, 0.94]
    b = [0.84, 0.85, 0.83, 0.86, 0.84]

    d_paired = calculate_cohen_d(a, b, paired=True)
    assert d_paired > 5.0  # Very large effect size

    delta = calculate_cliffs_delta(a, b)
    assert delta == 1.0  # Perfect dominance (all elements in a > all in b)

    # Identical arrays
    assert calculate_cohen_d(a, a, paired=True) == 0.0
    assert calculate_cliffs_delta(a, a) == 0.0


def test_paired_significance_testing() -> None:
    """Verify paired Wilcoxon and t-test execution."""
    prorag = [0.942, 0.945, 0.938, 0.941, 0.944]
    baseline = [0.852, 0.849, 0.855, 0.850, 0.853]

    test_name, stat, p_val = run_paired_significance_test(prorag, baseline)
    assert "Wilcoxon" in test_name or "t-Test" in test_name
    assert p_val < 0.05

    # Identical distributions
    name_id, stat_id, pval_id = run_paired_significance_test(prorag, prorag)
    assert pval_id == 1.0
    assert stat_id == 0.0


def test_multiple_comparison_corrections() -> None:
    """Verify Bonferroni and Benjamini-Hochberg FDR adjustments."""
    raw_p = [0.001, 0.010, 0.025, 0.040, 0.150]

    bonf = adjust_p_values_bonferroni(raw_p)
    fdr = adjust_p_values_fdr_bh(raw_p)

    assert len(bonf) == len(raw_p)
    assert len(fdr) == len(raw_p)

    # Bonferroni should be strictly >= raw p
    for r, b in zip(raw_p, bonf, strict=True):
        assert b >= r
        assert b <= 1.0

    # FDR adjusted values should be <= Bonferroni adjusted values
    for b, f in zip(bonf, fdr, strict=True):
        assert f <= b
        assert f <= 1.0


def test_multiseed_aggregator_end_to_end(tmp_path: Path) -> None:
    """Verify full multi-seed aggregation, zero cherry-picking, and table export."""
    aggregator = MultiSeedAggregator(runs_dir=tmp_path / "runs")
    report = aggregator.aggregate_and_test(use_reference_if_empty=True)

    assert report.total_runs_analyzed > 0
    assert report.standard_seeds == STANDARD_SEEDS
    assert len(report.summaries) > 0
    assert len(report.hypothesis_tests) > 0

    # Verify zero cherry-picking: check that all 5 seeds are present in summaries
    for summary in report.summaries:
        for _m_name, d_stat in summary.metrics.items():
            assert d_stat.n_samples == 5
            assert len(d_stat.raw_values) == 5

    # Export tables and verify file creation
    out_dir = tmp_path / "reports" / "statistics"
    p_path, c_path, j_path = aggregator.export_summary_tables(report, output_dir=out_dir)

    assert p_path.is_file()
    assert c_path.is_file()
    assert j_path.is_file()

    # Read back parquet and csv with pandas to verify schema
    df_parquet = pd.read_parquet(p_path)
    df_csv = pd.read_csv(c_path)
    assert len(df_parquet) == len(df_csv)
    assert "macro_f1_mean" in df_parquet.columns
    assert "macro_f1_std" in df_parquet.columns
    assert "macro_f1_ci95_low" in df_parquet.columns

    # Read back hypothesis tests JSON
    with open(j_path, encoding="utf-8") as f:
        tests_data = json.load(f)
    assert len(tests_data) == len(report.hypothesis_tests)
    assert "p_value_fdr_bh" in tests_data[0]
    assert "effect_size_cohen_d" in tests_data[0]

    # Generate markdown report
    md = generate_statistical_markdown_report(report)
    assert "# ProRAG-FL Multi-Seed Statistical Analysis Report" in md
    assert "**Standard Seed Set:** `[13, 37, 73, 101, 211]`" in md
    assert "Pairwise Significance Testing" in md
    assert "Complete Raw Seed Matrices" in md
