"""Core statistical computational engine for Phase 15.

Calculates descriptive statistics, sample dispersion with honest confidence intervals,
standardized effect sizes (Cohen's d, Cliff's delta), and multiple-comparison corrected
hypothesis tests (Wilcoxon signed-rank, paired t-test, Bonferroni, Benjamini-Hochberg FDR).

Strictly adheres to:
- instructions/19_METRICS_AND_STATISTICS.md:
  "N=5 independent seeds is small. Prefer transparent per-seed values, effect sizes
   and descriptive uncertainty. If using paired tests, state test, N, pairing and
   multiple-comparison correction. Do not overuse 'significant'."
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import numpy as np
import scipy.stats as stats

from prorag_fl.analysis.schemas import DescriptiveStats

logger = logging.getLogger(__name__)


def calculate_descriptive_stats(values: Sequence[float] | np.ndarray) -> DescriptiveStats:
    """Calculate sample distribution statistics with Student-t 95% confidence intervals."""
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        raise ValueError("Cannot calculate descriptive statistics for empty sequence.")

    n = int(arr.size)
    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))

    if n > 1:
        q75, q25 = np.percentile(arr, [75, 25])
        iqr_val = float(q75 - q25)
        std_val = float(np.std(arr, ddof=1))

        # Student's t critical value for df = n - 1 at alpha = 0.05 (two-tailed)
        t_crit = float(stats.t.ppf(0.975, df=n - 1))
        stderr = std_val / np.sqrt(n)
        ci_low = float(mean_val - t_crit * stderr)
        ci_high = float(mean_val + t_crit * stderr)
    else:
        iqr_val = 0.0
        std_val = 0.0
        ci_low = mean_val
        ci_high = mean_val

    return DescriptiveStats(
        mean=round(mean_val, 6),
        std=round(std_val, 6),
        median=round(median_val, 6),
        iqr=round(iqr_val, 6),
        min_val=round(min_val, 6),
        max_val=round(max_val, 6),
        ci_95_low=round(ci_low, 6),
        ci_95_high=round(ci_high, 6),
        n_samples=n,
        raw_values=[round(float(v), 6) for v in arr.tolist()],
    )


def calculate_cohen_d(
    a: Sequence[float] | np.ndarray,
    b: Sequence[float] | np.ndarray,
    paired: bool = True,
) -> float:
    """Compute Cohen's d standardized effect size.

    For paired measurements across identical seeds: d = mean(diff) / std(diff, ddof=1).
    For independent samples: d = (mean(a) - mean(b)) / s_pooled.
    """
    arr_a = np.asarray(a, dtype=np.float64)
    arr_b = np.asarray(b, dtype=np.float64)

    if arr_a.shape != arr_b.shape:
        raise ValueError(
            f"Arrays must have identical shapes for comparison: {arr_a.shape} vs {arr_b.shape}"
        )

    if paired:
        diff = arr_a - arr_b
        std_diff = np.std(diff, ddof=1)
        if std_diff > 1e-12:
            return float(np.mean(diff) / std_diff)
        # If paired difference has zero variance (constant shift), use pooled standard deviation
        s_pooled = np.sqrt((np.var(arr_a, ddof=1) + np.var(arr_b, ddof=1)) / 2.0)
        if s_pooled > 1e-12:
            return float(np.mean(diff) / s_pooled)
        return 0.0

    # Independent samples pooled standard deviation
    n_a, n_b = arr_a.size, arr_b.size
    var_a = np.var(arr_a, ddof=1) if n_a > 1 else 0.0
    var_b = np.var(arr_b, ddof=1) if n_b > 1 else 0.0
    s_pooled = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / max(n_a + n_b - 2, 1))
    if s_pooled <= 1e-12:
        return 0.0
    return float((np.mean(arr_a) - np.mean(arr_b)) / s_pooled)


def calculate_cliffs_delta(
    a: Sequence[float] | np.ndarray,
    b: Sequence[float] | np.ndarray,
) -> float:
    """Compute Cliff's delta non-parametric effect size in [-1.0, 1.0]."""
    arr_a = np.asarray(a, dtype=np.float64)
    arr_b = np.asarray(b, dtype=np.float64)

    if arr_a.size == 0 or arr_b.size == 0:
        return 0.0

    greater = 0
    less = 0
    for x in arr_a:
        for y in arr_b:
            if x > y:
                greater += 1
            elif x < y:
                less += 1

    total_comparisons = arr_a.size * arr_b.size
    return float((greater - less) / total_comparisons)


def run_paired_significance_test(
    proposed: Sequence[float] | np.ndarray,
    baseline: Sequence[float] | np.ndarray,
) -> tuple[str, float, float]:
    """Run paired hypothesis test between proposed method and baseline across matching seeds.

    For small sample size N <= 5, uses Paired Student's t-Test because Wilcoxon signed-rank
    test cannot achieve p < 0.05 (minimum two-tailed p-value for N=5 is 2/32 = 0.0625).
    For N > 5, applies Wilcoxon Signed-Rank Test first with fallback to Paired t-Test.

    Returns:
        (test_name, test_statistic, two_tailed_p_value)
    """
    arr_p = np.asarray(proposed, dtype=np.float64)
    arr_b = np.asarray(baseline, dtype=np.float64)

    if arr_p.shape != arr_b.shape:
        raise ValueError(f"Paired test requires identical lengths: {arr_p.shape} vs {arr_b.shape}")

    diff = arr_p - arr_b
    if np.allclose(diff, 0.0, atol=1e-9):
        # Samples are identical
        return "Paired Identical (Null Difference)", 0.0, 1.0

    # For N <= 5, Wilcoxon signed-rank minimum possible two-tailed p-value is 2 / 2^N = 0.0625 (> 0.05).
    # We use Paired Student's t-Test for small N, and Wilcoxon when N > 5.
    if arr_p.size <= 5:
        try:
            t_res = stats.ttest_rel(arr_p, arr_b, alternative="two-sided")
            stat = float(t_res.statistic) if not np.isnan(t_res.statistic) else 0.0
            pval = float(t_res.pvalue) if not np.isnan(t_res.pvalue) else 1.0
            return "Paired Student's t-Test", stat, pval
        except Exception as e:
            logger.warning("Paired t-test fallback failed: %s", e)

    # Try Wilcoxon Signed-Rank Test for N > 5
    try:
        w_res = stats.wilcoxon(arr_p, arr_b, zero_method="pratt", alternative="two-sided")
        return "Wilcoxon Signed-Rank Test", float(w_res.statistic), float(w_res.pvalue)
    except (ValueError, ZeroDivisionError):
        pass

    # Fallback to Paired Student's t-Test
    try:
        t_res = stats.ttest_rel(arr_p, arr_b, alternative="two-sided")
        stat = float(t_res.statistic) if not np.isnan(t_res.statistic) else 0.0
        pval = float(t_res.pvalue) if not np.isnan(t_res.pvalue) else 1.0
        return "Paired Student's t-Test", stat, pval
    except Exception as e:
        logger.warning("Paired test fallback failed: %s", e)
        return "Paired Test Error", 0.0, 1.0


def adjust_p_values_bonferroni(p_values: Sequence[float]) -> list[float]:
    """Bonferroni FWER multiple-comparison correction: min(p * m, 1.0)."""
    m = len(p_values)
    return [min(float(p) * m, 1.0) for p in p_values]


def adjust_p_values_fdr_bh(p_values: Sequence[float]) -> list[float]:
    """Benjamini-Hochberg False Discovery Rate (FDR) step-up procedure."""
    p_arr = np.asarray(p_values, dtype=np.float64)
    m = len(p_arr)
    if m == 0:
        return []

    # Rank p-values in ascending order
    sorted_indices = np.argsort(p_arr)
    sorted_p = p_arr[sorted_indices]

    adjusted = np.empty(m, dtype=np.float64)
    min_adjusted = 1.0

    # Step-down from largest rank m down to 1
    for i in range(m - 1, -1, -1):
        rank = i + 1
        adj_p = (sorted_p[i] * m) / rank
        min_adjusted = min(min_adjusted, adj_p)
        adjusted[i] = min(min_adjusted, 1.0)

    # Invert sorting to restore original order
    result = np.empty(m, dtype=np.float64)
    result[sorted_indices] = adjusted
    return [float(x) for x in result.tolist()]
