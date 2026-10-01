"""Phase 15: Statistical Analysis & Significance Testing module."""

from __future__ import annotations

from prorag_fl.analysis.aggregator import MultiSeedAggregator
from prorag_fl.analysis.reporting import generate_statistical_markdown_report
from prorag_fl.analysis.schemas import (
    STANDARD_SEEDS,
    ComprehensiveStatisticalReport,
    DescriptiveStats,
    HypothesisTestResult,
    MethodMetricSummary,
)
from prorag_fl.analysis.stats_engine import (
    adjust_p_values_bonferroni,
    adjust_p_values_fdr_bh,
    calculate_cliffs_delta,
    calculate_cohen_d,
    calculate_descriptive_stats,
    run_paired_significance_test,
)

__all__ = [
    "STANDARD_SEEDS",
    "ComprehensiveStatisticalReport",
    "DescriptiveStats",
    "HypothesisTestResult",
    "MethodMetricSummary",
    "MultiSeedAggregator",
    "adjust_p_values_bonferroni",
    "adjust_p_values_fdr_bh",
    "calculate_cliffs_delta",
    "calculate_cohen_d",
    "calculate_descriptive_stats",
    "generate_statistical_markdown_report",
    "run_paired_significance_test",
]
