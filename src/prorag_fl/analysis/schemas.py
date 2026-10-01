"""Pydantic schemas for Phase 15: Statistical Analysis & Significance Testing.

Strictly adheres to:
- instructions/19_METRICS_AND_STATISTICS.md:
  "Seeds: 13, 37, 73, 101, 211. Store all raw values. Main reporting is mean ± standard deviation.
   N=5 independent seeds is small. Prefer transparent per-seed values, effect sizes and descriptive uncertainty.
   If using paired tests, state test, N, pairing and multiple-comparison correction. Do not overuse 'significant'.
   Never report only best seed. Never remove a valid low-performing run."
- instructions/36_PHASE_ACCEPTANCE_GATES.md:
  "P15: five-seed raw results + honest uncertainty."
"""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

STANDARD_SEEDS: list[int] = [13, 37, 73, 101, 211]


class DescriptiveStats(BaseModel):
    """Rigorous sample distribution summary with honest uncertainty quantification."""

    model_config = ConfigDict(extra="forbid")

    mean: float = Field(..., description="Sample arithmetic mean")
    std: float = Field(..., description="Sample standard deviation (ddof=1)")
    median: float = Field(..., description="Sample median (50th percentile)")
    iqr: float = Field(..., description="Interquartile range (Q3 - Q1)")
    min_val: float = Field(..., description="Sample minimum observed value")
    max_val: float = Field(..., description="Sample maximum observed value")
    ci_95_low: float = Field(
        ..., description="Lower bound of 95% confidence interval (Student-t df=n-1)"
    )
    ci_95_high: float = Field(
        ..., description="Upper bound of 95% confidence interval (Student-t df=n-1)"
    )
    n_samples: int = Field(..., ge=1, description="Number of evaluated seeds")
    raw_values: list[float] = Field(
        default_factory=list, description="All raw values across evaluated seeds"
    )


class HypothesisTestResult(BaseModel):
    """Pairwise statistical significance test result between ProRAG-FL and a baseline."""

    model_config = ConfigDict(extra="forbid")

    metric_name: str = Field(..., description="Target evaluated metric")
    dataset: str = Field(..., description="Evaluated dataset")
    proposed_method: str = Field(default="prorag_fl", description="Target proposed method")
    baseline_method: str = Field(..., description="Comparative baseline name")
    test_name: str = Field(
        ..., description="Applied statistical test name (e.g., Wilcoxon Signed-Rank, Paired t-Test)"
    )
    statistic: float = Field(..., description="Computed test statistic")
    p_value_raw: float = Field(..., description="Uncorrected raw two-tailed p-value")
    p_value_bonferroni: float = Field(
        ..., description="Bonferroni family-wise error rate corrected p-value"
    )
    p_value_fdr_bh: float = Field(
        ..., description="Benjamini-Hochberg False Discovery Rate (FDR) corrected p-value"
    )
    effect_size_cohen_d: float = Field(
        ..., description="Cohen's d standardized mean difference effect size"
    )
    effect_size_cliffs_delta: float = Field(
        ..., description="Cliff's delta non-parametric effect size"
    )
    n_pairs: int = Field(..., ge=1, description="Number of paired seeds evaluated")
    is_significant_005: bool = Field(
        ..., description="Whether difference is statistically significant at alpha=0.05 after FDR"
    )
    is_significant_001: bool = Field(
        ..., description="Whether difference is statistically significant at alpha=0.01 after FDR"
    )


class MethodMetricSummary(BaseModel):
    """Aggregated multi-seed statistics for a method on a dataset."""

    model_config = ConfigDict(extra="forbid")

    dataset: str = Field(..., description="Dataset name: ciciot2023 or edge_iiotset")
    method: str = Field(..., description="Method name: prorag_fl or baseline identifier")
    experiment_type: str = Field(..., description="Experiment category E1-E10")
    attack_type: str = Field(default="none", description="Adversarial attack condition")
    alpha: float | None = Field(default=None, description="Dirichlet non-IID partition parameter")
    num_clients: int = Field(default=10, description="Participating client count")
    metrics: dict[str, DescriptiveStats] = Field(
        default_factory=dict, description="Mapping of metric name to descriptive statistics"
    )


class ComprehensiveStatisticalReport(BaseModel):
    """Top-level container for all aggregated multi-seed statistics and hypothesis tests."""

    model_config = ConfigDict(extra="forbid")

    generated_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )
    compliance_gate: str = Field(
        default="Acceptance Gate P15 (Five-Seed Raw Results & Honest Uncertainty)"
    )
    standard_seeds: list[int] = Field(default_factory=lambda: list(STANDARD_SEEDS))
    total_runs_analyzed: int = Field(..., ge=0)
    summaries: list[MethodMetricSummary] = Field(default_factory=list)
    hypothesis_tests: list[HypothesisTestResult] = Field(default_factory=list)
    raw_seed_records: list[dict[str, Any]] = Field(default_factory=list)
