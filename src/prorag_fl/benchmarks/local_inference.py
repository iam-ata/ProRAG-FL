"""Local Inference Path Benchmarking Suite.

Measures latency and throughput across:
- Preprocessing (Standardization + Reshaping)
- 1D-CNN Forward Pass (128-D embeddings + logits)
- Temperature Scaling Probability Calibration
- Mahalanobis OOD Latent Distance Computation
- Total Sub-Millisecond Direct Path Execution

Strictly adheres to:
- instructions/25_SYSTEMS_BENCHMARKS.md:
  "Measure preprocessing, CNN forward, calibration, OOD, direct total."
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import torch
from sklearn.preprocessing import StandardScaler

from prorag_fl.benchmarks.schemas import LocalInferenceBenchmarkResult
from prorag_fl.benchmarks.timing import measure_callable
from prorag_fl.calibration.temperature_scaling import TemperatureScaler
from prorag_fl.models.ids_1dcnn import IDS1DCNN
from prorag_fl.ood.mahalanobis import MahalanobisOODDetector

logger = logging.getLogger(__name__)


def benchmark_local_inference(
    batch_sizes: list[int] | None = None,
    num_features: int = 46,
    num_classes: int = 15,
    warmup_iterations: int = 10,
    benchmark_iterations: int = 50,
) -> list[LocalInferenceBenchmarkResult]:
    """Execute rigorous local inference benchmarks across specified batch sizes."""
    if batch_sizes is None:
        batch_sizes = [1, 32, 64]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Local inference benchmarking using device: %s", device)

    # 1. Initialize models and calibrators
    model = IDS1DCNN(num_features=num_features, num_classes=num_classes).to(device)
    model.eval()

    scaler = TemperatureScaler().to(device)
    scaler.eval()

    ood_detector = MahalanobisOODDetector(embedding_dim=128)
    # Fit OOD detector with synthetic background representations
    rng = np.random.default_rng(42)
    synthetic_h = rng.normal(0.0, 1.0, size=(300, 128))
    synthetic_y = rng.integers(0, num_classes, size=(300,))
    ood_detector.fit(synthetic_h, synthetic_y)

    preproc_scaler = StandardScaler()
    preproc_scaler.fit(rng.normal(0.0, 1.0, size=(100, num_features)))

    results: list[LocalInferenceBenchmarkResult] = []

    for b in batch_sizes:
        raw_features = rng.normal(0.0, 1.0, size=(b, num_features)).astype(np.float32)

        # A. Preprocessing benchmark
        def run_preproc(data: np.ndarray) -> torch.Tensor:
            scaled = preproc_scaler.transform(data)
            tensor = torch.from_numpy(scaled).float().unsqueeze(1).to(device)
            return tensor

        preproc_stats, preproc_tensor = measure_callable(
            run_preproc,
            raw_features,
            warmup_iterations=warmup_iterations,
            benchmark_iterations=benchmark_iterations,
        )

        # B. 1D-CNN Forward pass benchmark
        @torch.no_grad()
        def run_forward(x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
            logits, embeddings = model(x)
            return logits, embeddings

        forward_stats, (logits, embeddings) = measure_callable(
            run_forward,
            preproc_tensor,
            warmup_iterations=warmup_iterations,
            benchmark_iterations=benchmark_iterations,
        )

        # C. Temperature scaling calibration benchmark
        @torch.no_grad()
        def run_calibration(lg: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
            conf, pred = scaler.predict_confidence(lg)
            return conf, pred

        cal_stats, _ = measure_callable(
            run_calibration,
            logits,
            warmup_iterations=warmup_iterations,
            benchmark_iterations=benchmark_iterations,
        )

        # D. Mahalanobis OOD benchmark
        emb_np = embeddings.detach().cpu().numpy().astype(np.float64)

        def run_ood(h: np.ndarray) -> np.ndarray:
            dist = ood_detector.compute_distance(h)
            return dist

        ood_stats, _ = measure_callable(
            run_ood,
            emb_np,
            warmup_iterations=warmup_iterations,
            benchmark_iterations=benchmark_iterations,
        )

        # E. Total direct path execution
        @torch.no_grad()
        def run_total_direct_path(data: np.ndarray) -> dict[str, Any]:
            x = torch.from_numpy(preproc_scaler.transform(data)).float().unsqueeze(1).to(device)
            lg, emb = model(x)
            conf, _ = scaler.predict_confidence(lg)
            dists = ood_detector.compute_distance(emb.detach().cpu().numpy().astype(np.float64))
            return {"confidence": conf, "mahalanobis": dists}

        total_stats, _ = measure_callable(
            run_total_direct_path,
            raw_features,
            warmup_iterations=warmup_iterations,
            benchmark_iterations=benchmark_iterations,
        )

        per_sample_lat = total_stats.warm_mean_ms / b
        throughput = (
            (1000.0 / total_stats.warm_mean_ms) * b if total_stats.warm_mean_ms > 0 else 0.0
        )

        results.append(
            LocalInferenceBenchmarkResult(
                batch_size=b,
                preprocessing_stats=preproc_stats,
                forward_pass_stats=forward_stats,
                calibration_stats=cal_stats,
                ood_stats=ood_stats,
                total_direct_stats=total_stats,
                per_sample_latency_ms=round(per_sample_lat, 4),
                throughput_samples_per_sec=round(throughput, 2),
            )
        )

    return results
