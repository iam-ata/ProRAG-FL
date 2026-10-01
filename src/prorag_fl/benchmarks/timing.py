"""Precision Timing Protocol and Measurement Harness.

Strictly adheres to:
- instructions/25_SYSTEMS_BENCHMARKS.md:
  "Use warm-ups and repeated measurements. Synchronize GPU timing when needed.
   Report mean plus median/p95 where informative. Never mix cold-start and warm-path values without labels."
"""

from __future__ import annotations

import statistics
import time
from collections.abc import Callable
from typing import Any

import numpy as np
import torch

from prorag_fl.benchmarks.schemas import TimingStats


def synchronize_gpu() -> None:
    """Synchronize CUDA GPU pipeline if CUDA is available."""
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def measure_callable(
    fn: Callable[..., Any],
    *args: Any,
    warmup_iterations: int = 10,
    benchmark_iterations: int = 50,
    **kwargs: Any,
) -> tuple[TimingStats, Any]:
    """Execute a callable with rigorous timing protocol, returning TimingStats and last output.

    Protocol:
    1. Measures cold-start execution on the very first call.
    2. Runs warmup_iterations to prime caches and JIT paths.
    3. Runs benchmark_iterations, synchronizing GPU timing if CUDA is active.
    4. Computes distribution statistics (mean, median, p95, p99, std, min, max).
    """
    # 1. Cold start measurement
    synchronize_gpu()
    t0_cold = time.perf_counter_ns()
    cold_res = fn(*args, **kwargs)
    synchronize_gpu()
    t1_cold = time.perf_counter_ns()
    cold_start_ms = (t1_cold - t0_cold) / 1_000_000.0

    # 2. Warmup iterations (discarded)
    for _ in range(warmup_iterations):
        synchronize_gpu()
        _ = fn(*args, **kwargs)
        synchronize_gpu()

    # 3. Repeated benchmark measurements
    latencies_ms: list[float] = []
    last_res = cold_res
    for _ in range(benchmark_iterations):
        synchronize_gpu()
        t0 = time.perf_counter_ns()
        last_res = fn(*args, **kwargs)
        synchronize_gpu()
        t1 = time.perf_counter_ns()
        latencies_ms.append((t1 - t0) / 1_000_000.0)

    # 4. Statistical computation
    arr = np.array(latencies_ms, dtype=np.float64)
    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    p95_val = float(np.percentile(arr, 95))
    p99_val = float(np.percentile(arr, 99))
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))
    std_val = float(statistics.stdev(latencies_ms)) if len(latencies_ms) > 1 else 0.0

    stats = TimingStats(
        cold_start_ms=round(cold_start_ms, 4),
        warm_mean_ms=round(mean_val, 4),
        warm_median_ms=round(median_val, 4),
        warm_p95_ms=round(p95_val, 4),
        warm_p99_ms=round(p99_val, 4),
        warm_std_ms=round(std_val, 4),
        warm_min_ms=round(min_val, 4),
        warm_max_ms=round(max_val, 4),
        iterations=benchmark_iterations,
    )
    return stats, last_res
