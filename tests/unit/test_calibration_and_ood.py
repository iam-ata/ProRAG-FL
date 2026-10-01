"""Unit tests for Phase 3 Confidence Calibration, Mahalanobis OOD, and Dual Escalation Gate."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

from prorag_fl.calibration.temperature_scaling import (
    TemperatureScaler,
)
from prorag_fl.core.seeding import set_seed
from prorag_fl.ood.dual_gate import DualGate
from prorag_fl.ood.mahalanobis import MahalanobisOODDetector


@pytest.fixture
def mock_validation_data() -> tuple[torch.Tensor, torch.Tensor]:
    """Synthetic validation logits and labels for calibration tests."""
    set_seed(42)
    n_samples = 200
    n_classes = 5

    # Generate synthetic uncalibrated logits
    logits = torch.randn(n_samples, n_classes) * 2.5
    # True labels loosely correlated with argmax
    labels = torch.argmax(logits + torch.randn_like(logits) * 0.5, dim=1)
    return logits, labels


@pytest.fixture
def mock_embedding_data() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Synthetic training and validation embeddings with distinct class clusters."""
    set_seed(42)
    rng = np.random.default_rng(42)
    n_train_per_class = 60
    n_val_per_class = 20
    n_classes = 4
    dim = 128

    train_h_list, train_y_list = [], []
    val_h_list, val_y_list = [], []

    # Create separated class centers in 128-D space
    centers = rng.standard_normal((n_classes, dim)) * 5.0

    for c in range(n_classes):
        train_samples = centers[c] + rng.standard_normal((n_train_per_class, dim)) * 0.8
        val_samples = centers[c] + rng.standard_normal((n_val_per_class, dim)) * 0.8

        train_h_list.append(train_samples)
        train_y_list.extend([c] * n_train_per_class)

        val_h_list.append(val_samples)
        val_y_list.extend([c] * n_val_per_class)

    return (
        np.vstack(train_h_list).astype(np.float32),
        np.array(train_y_list, dtype=np.int64),
        np.vstack(val_h_list).astype(np.float32),
        np.array(val_y_list, dtype=np.int64),
    )


@pytest.mark.unit
def test_temperature_scaling_positive_and_normalized(
    mock_validation_data: tuple[torch.Tensor, torch.Tensor],
) -> None:
    """Requirement 1: Verify temperature is strictly positive and probabilities sum to 1.0."""
    logits, _ = mock_validation_data
    scaler = TemperatureScaler()

    # Even with an extreme negative parameter, temperature must remain strictly positive
    with torch.no_grad():
        scaler.raw_temperature.copy_(torch.tensor([-100.0]))
    assert scaler.temperature.item() > 0.0, "Temperature must be strictly positive!"

    # Probabilities must sum to 1.0
    probs = scaler.predict_proba(logits)
    sums = probs.sum(dim=-1)
    assert torch.allclose(sums, torch.ones_like(sums), atol=1e-5), (
        "Probabilities do not sum to 1.0!"
    )


@pytest.mark.unit
def test_temperature_scaling_optimization_improves_metrics(
    mock_validation_data: tuple[torch.Tensor, torch.Tensor],
) -> None:
    """Requirement 2: Verify temperature fitting reduces NLL or ECE on validation logits."""
    logits, labels = mock_validation_data
    scaler = TemperatureScaler()

    result = scaler.fit(val_logits=logits, val_labels=labels, target_recall=0.90)

    assert result.temperature > 0.0
    assert result.nll_after <= result.nll_before + 1e-4, "Calibration increased NLL!"
    assert 0.0 <= result.tau_c <= 1.0, f"Invalid tau_c: {result.tau_c}"
    assert scaler.is_fitted is True


@pytest.mark.unit
def test_mahalanobis_covariance_stability_and_finite_distances(
    mock_embedding_data: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
) -> None:
    """Requirement 3: Verify regularized covariance is well-conditioned and distances are finite."""
    train_h, train_y, val_h, _ = mock_embedding_data
    detector = MahalanobisOODDetector(embedding_dim=128)

    result = detector.fit(train_h, train_y, shrinkage_method="ledoit_wolf")

    assert detector.is_fitted is True
    assert detector.precision is not None
    assert np.isfinite(detector.precision).all(), "Precision matrix contains non-finite entries!"
    assert result.covariance_condition_number >= 1.0

    # Compute distances on validation
    val_distances = detector.compute_distance(val_h)
    assert np.isfinite(val_distances).all(), "Mahalanobis distances are not finite!"
    assert (val_distances >= 0.0).all(), "Distances cannot be negative!"

    # Outlier vector (very far from any center) must have significantly larger distance
    far_vector = np.ones((5, 128), dtype=np.float32) * 50.0
    far_distances = detector.compute_distance(far_vector)
    assert np.min(far_distances) > np.max(val_distances), (
        "Outliers did not produce higher distances!"
    )


@pytest.mark.unit
def test_dual_gate_routing_logic(
    mock_validation_data: tuple[torch.Tensor, torch.Tensor],
    mock_embedding_data: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
) -> None:
    """Requirement 4: Verify dual escalation gate logic G(x) = (C(x) < tau_c or M(x) > tau_m)."""
    logits, labels = mock_validation_data
    train_h, train_y, val_h, _ = mock_embedding_data

    scaler = TemperatureScaler()
    scaler.fit(logits, labels)

    detector = MahalanobisOODDetector()
    detector.fit(train_h, train_y)
    detector.select_threshold(val_h, quantile=0.95)

    gate = DualGate(
        temperature_scaler=scaler,
        mahalanobis_detector=detector,
        tau_c=0.70,
        tau_m=detector.tau_m,
    )

    # Synthetic test inputs
    test_logits = torch.tensor(
        [
            [10.0, 0.0, 0.0, 0.0, 0.0],  # High confidence
            [0.1, 0.1, 0.1, 0.1, 0.1],  # Low confidence
        ]
    )
    # Near cluster center vs far outlier
    center_emb = train_h[0:1]
    far_emb = np.ones((1, 128), dtype=np.float32) * 50.0
    test_emb = np.vstack([center_emb, far_emb])

    decisions = gate.route_batch(test_logits, test_emb)
    assert len(decisions) == 2

    # First sample: high confidence + near center -> direct route
    assert decisions[0].escalate is False
    assert decisions[0].reason == "direct"

    # Second sample: low confidence + far outlier -> both
    assert decisions[1].escalate is True
    assert decisions[1].reason in ("both", "low_confidence", "high_mahalanobis")


@pytest.mark.unit
def test_dual_gate_evaluation_metrics() -> None:
    """Requirement 5: Verify gate evaluation metrics for known vs held-out zero-day attack samples."""
    # Mock decisions: 10 known samples (8 direct, 2 false escalation), 5 held-out samples (5 escalated)
    decisions = []
    # 8 correct direct known samples
    for _ in range(8):
        decisions.append(
            gate_decision_factory(escalate=False, pred=0, conf=0.95, dist=3.0, reason="direct")
        )
    # 2 falsely escalated known samples
    for _ in range(2):
        decisions.append(
            gate_decision_factory(
                escalate=True, pred=0, conf=0.40, dist=15.0, reason="low_confidence"
            )
        )
    # 5 correctly escalated held-out samples
    for _ in range(5):
        decisions.append(
            gate_decision_factory(
                escalate=True, pred=1, conf=0.30, dist=35.0, reason="high_mahalanobis"
            )
        )

    labels = [0] * 10 + [7] * 5  # Class 7 is held out
    is_held_out = [False] * 10 + [True] * 5

    scaler = TemperatureScaler()
    detector = MahalanobisOODDetector()
    gate = DualGate(temperature_scaler=scaler, mahalanobis_detector=detector, tau_c=0.5, tau_m=10.0)

    metrics = gate.evaluate(decisions, labels, is_held_out, dataset_name="mock_test")

    assert metrics.num_known_samples == 10
    assert metrics.num_held_out_samples == 5
    assert metrics.direct_route_rate == 0.80  # 8 / 10
    assert metrics.false_escalation_rate == 0.20  # 2 / 10
    assert metrics.direct_accuracy == 1.0  # All 8 direct decisions were correct
    assert metrics.held_out_escalation_recall == 1.0  # All 5 held-out samples escalated
    assert metrics.mahalanobis_auroc is not None
    assert metrics.mahalanobis_auroc > 0.90


@pytest.mark.unit
def test_serialization_and_exact_decision_reproducibility(
    mock_validation_data: tuple[torch.Tensor, torch.Tensor],
    mock_embedding_data: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
) -> None:
    """Requirement 6: Saved scaler, detector, and gate thresholds reproduce bit-exact decisions."""
    logits, labels = mock_validation_data
    train_h, train_y, val_h, _ = mock_embedding_data

    scaler = TemperatureScaler()
    scaler.fit(logits, labels)

    detector = MahalanobisOODDetector()
    detector.fit(train_h, train_y)
    detector.select_threshold(val_h, quantile=0.95)

    gate = DualGate(scaler, detector)

    with tempfile.TemporaryDirectory() as tmp_dir:
        scaler_file = Path(tmp_dir) / "scaler.json"
        detector_file = Path(tmp_dir) / "detector.json"
        gate_file = Path(tmp_dir) / "gate.json"

        scaler.save(scaler_file)
        detector.save(detector_file)
        gate.save_thresholds(
            gate_file, dataset_name="test_ds", model_checkpoint_digest="abc123digest"
        )

        # Load into new instances
        scaler_loaded = TemperatureScaler().load(scaler_file)
        detector_loaded = MahalanobisOODDetector().load(detector_file)
        gate_loaded = DualGate(scaler_loaded, detector_loaded).load_thresholds(gate_file)

        # Test decisions on validation data
        decisions_orig = gate.route_batch(logits[:20], val_h[:20])
        decisions_loaded = gate_loaded.route_batch(logits[:20], val_h[:20])

        assert len(decisions_orig) == len(decisions_loaded)
        for d1, d2 in zip(decisions_orig, decisions_loaded, strict=True):
            assert d1.escalate == d2.escalate
            assert d1.reason == d2.reason
            assert abs(d1.confidence - d2.confidence) < 1e-5
            assert abs(d1.mahalanobis_distance - d2.mahalanobis_distance) < 1e-5


def gate_decision_factory(
    escalate: bool,
    pred: int,
    conf: float,
    dist: float,
    reason: str,
):
    from prorag_fl.schemas.calibration import GateDecision

    return GateDecision(
        event_id="test",
        escalate=escalate,
        confidence=conf,
        mahalanobis_distance=dist,
        predicted_class_id=pred,
        predicted_class_name=f"Class_{pred}",
        reason=reason,
    )
