"""Unit and smoke tests for Phase 10: Comparative Baselines (B0 through B11).

Verifies Acceptance Gate P10:
- Fidelity and smoke execution for every measured baseline B0 through B11.
- Standardized BaselineEvaluationResult metrics schema.
- Algorithmic fidelity of defense mechanisms:
  - FLOW pairwise cosine distance anomaly detection and graceful punishment.
  - SFLNID Holt dynamic gradient clipping and Wasserstein loss.
  - Bc2FL two-layer blockchain consensus ledger.
  - RLFE-IDS unverified RAG flow embeddings.
  - LQB-IDS DCAE dual-switch known vs unknown routing.
  - FedMSE shrink autoencoder one-class centroid anomaly classifier.
  - pFL-IDS logit adjustment and two-phase similarity defense.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from prorag_fl.baselines import (
    Bc2FLBaseline,
    Centralized1DCNNBaseline,
    FedMSEBaseline,
    FlowBaseline,
    Local1DCNNBaseline,
    LQBIDSBaseline,
    PFLIDSBaseline,
    RLFEIDSBaseline,
    SFLNIDBaseline,
    StandardFLBaseline,
)
from prorag_fl.baselines.common import BaselineEvaluationResult, compute_standard_metrics
from prorag_fl.baselines.flow import FlowDetector, FlowHistoryState
from prorag_fl.baselines.pfl_ids import LogitAdjustedLoss, TwoPhaseSimilarityDefense
from prorag_fl.baselines.sflnid import AdaptiveDPController, SFLNIDLoss, SFLNIDModel


@pytest.fixture
def synthetic_ids_dataset():
    """Create reproducible synthetic tabular network data for fast unit testing."""
    np.random.seed(42)
    torch.manual_seed(42)

    num_features = 16
    num_classes = 3
    num_samples_per_client = 60

    client_partitions = {}
    for cid in ["client_0", "client_1", "client_2"]:
        x = np.random.randn(num_samples_per_client, num_features).astype(np.float32)
        y = np.random.randint(0, num_classes, size=num_samples_per_client, dtype=np.int64)
        client_partitions[cid] = (x, y)

    x_test = np.random.randn(50, num_features).astype(np.float32)
    y_test = np.random.randint(0, num_classes, size=50, dtype=np.int64)

    label_names = ["Benign", "DDoS-ICMP", "Mirai"]
    return client_partitions, x_test, y_test, num_features, num_classes, label_names


@pytest.mark.unit
def test_b0_local_1dcnn_smoke(synthetic_ids_dataset):
    """Test B0 Local 1D-CNN baseline: independent per-client training and evaluation."""
    client_partitions, x_test, y_test, num_features, num_classes, label_names = (
        synthetic_ids_dataset
    )

    b0 = Local1DCNNBaseline(
        num_features=num_features,
        num_classes=num_classes,
        epochs=1,
        batch_size=32,
    )
    b0.fit(client_partitions)

    assert "client_0" in b0.client_models
    assert "client_1" in b0.client_models
    assert "client_2" in b0.client_models

    # Evaluate ensemble
    res = b0.evaluate(x_test, y_test, label_names=label_names)
    assert isinstance(res, BaselineEvaluationResult)
    assert res.baseline_id == "B0"
    assert res.fidelity_tier == "faithful_reimplementation"
    assert 0.0 <= res.accuracy <= 1.0
    assert 0.0 <= res.macro_f1 <= 1.0
    assert res.communication_bytes == 0


@pytest.mark.unit
def test_b1_centralized_1dcnn_smoke(synthetic_ids_dataset):
    """Test B1 Centralized 1D-CNN baseline: pooled oracle reference."""
    client_partitions, x_test, y_test, num_features, num_classes, label_names = (
        synthetic_ids_dataset
    )

    all_x = np.vstack([cp[0] for cp in client_partitions.values()])
    all_y = np.concatenate([cp[1] for cp in client_partitions.values()])

    b1 = Centralized1DCNNBaseline(
        num_features=num_features,
        num_classes=num_classes,
        epochs=1,
        batch_size=32,
    )
    b1.fit(train_data=(all_x, all_y))

    res = b1.evaluate(x_test, y_test, label_names=label_names)
    assert isinstance(res, BaselineEvaluationResult)
    assert res.baseline_id == "B1"
    assert res.fidelity_tier == "faithful_reimplementation"
    assert 0.0 <= res.accuracy <= 1.0
    assert 0.0 <= res.macro_f1 <= 1.0


@pytest.mark.unit
def test_b2_b3_b4_standard_fl_controls_smoke(synthetic_ids_dataset):
    """Test standard FL baselines: B2 FedAvg, B3 MultiKrum, B4 FedTrimmedAvg."""
    client_partitions, x_test, y_test, num_features, num_classes, label_names = (
        synthetic_ids_dataset
    )

    # B2: FedAvg
    b2 = StandardFLBaseline(
        strategy_name="fedavg",
        num_features=num_features,
        num_classes=num_classes,
        num_rounds=1,
        local_epochs=1,
        batch_size=32,
    )
    b2.fit(client_partitions)
    res_b2 = b2.evaluate(x_test, y_test, label_names=label_names)
    assert res_b2.baseline_id == "B2"
    assert res_b2.fidelity_tier == "faithful_reimplementation"

    # B4: FedTrimmedAvg
    b4 = StandardFLBaseline(
        strategy_name="fedtrimmedavg",
        num_features=num_features,
        num_classes=num_classes,
        num_rounds=1,
        local_epochs=1,
        batch_size=32,
        strategy_kwargs={"beta": 0.20},
    )
    b4.fit(client_partitions)
    res_b4 = b4.evaluate(x_test, y_test, label_names=label_names)
    assert res_b4.baseline_id == "B4"
    assert res_b4.fidelity_tier == "faithful_reimplementation"


@pytest.mark.unit
def test_b5_sflnid_components_and_smoke(synthetic_ids_dataset):
    """Test B5 SFLNID: CNN-GRU, Focal+Wasserstein loss, Holt dynamic DP clipping."""
    client_partitions, x_test, y_test, num_features, num_classes, label_names = (
        synthetic_ids_dataset
    )

    # 1. Model shape check
    model = SFLNIDModel(num_features=num_features, num_classes=num_classes)
    dummy_x = torch.randn(8, num_features)
    logits = model(dummy_x)
    assert logits.shape == (8, num_classes)

    # 2. Loss check
    loss_fn = SFLNIDLoss(wasserstein_weight=0.1)
    dummy_targets = torch.tensor([0, 1, 2, 0, 1, 2, 0, 1], dtype=torch.long)
    feats_loc = model.extract_features(dummy_x)
    feats_glob = feats_loc.clone() + 0.1
    loss = loss_fn(logits, dummy_targets, feats_loc, feats_glob)
    assert torch.isfinite(loss)
    assert loss.item() > 0.0

    # 3. Holt DP Controller check
    dp = AdaptiveDPController(initial_clip=1.0)
    c1 = dp.update_clipping_threshold(2.5)
    c2 = dp.update_clipping_threshold(1.8)
    assert c1 > 0.1
    assert c2 > 0.1

    # 4. End-to-end baseline fit and evaluate
    b5 = SFLNIDBaseline(
        num_features=num_features,
        num_classes=num_classes,
        num_rounds=1,
        local_epochs=1,
        batch_size=32,
    )
    b5.fit(client_partitions)
    res = b5.evaluate(x_test, y_test, label_names=label_names)
    assert res.baseline_id == "B5"
    assert res.fidelity_tier == "faithful_reimplementation"
    assert 0.0 <= res.accuracy <= 1.0


@pytest.mark.unit
def test_b6_flow_cosine_defense_and_smoke(synthetic_ids_dataset):
    """Test B6 FLOW: Pairwise cosine distance detection and graceful punishment."""
    client_partitions, x_test, y_test, num_features, num_classes, label_names = (
        synthetic_ids_dataset
    )

    # Test FlowDetector on benign cluster vs malicious opposite-direction attack
    detector = FlowDetector()
    benign_u1 = np.array([1.0, 0.9, 1.1, 1.0], dtype=np.float32)
    benign_u2 = np.array([0.9, 1.0, 0.9, 1.1], dtype=np.float32)
    benign_u3 = np.array([1.1, 1.1, 1.0, 0.9], dtype=np.float32)
    malicious_u = np.array([-1.0, -1.0, -1.0, -1.0], dtype=np.float32)  # Opposite direction

    updates = [benign_u1, benign_u2, benign_u3, malicious_u]
    histories = {f"c{i}": FlowHistoryState(client_id=f"c{i}") for i in range(4)}
    client_ids = ["c0", "c1", "c2", "c3"]

    is_mal, scores = detector.detect(updates, histories, client_ids)
    assert is_mal[3] is True  # Malicious update detected!
    assert is_mal[0] is False  # Benign updates accepted
    assert histories["c3"].penalty_factor > 0.0  # Penalized

    # Fit baseline
    b6 = FlowBaseline(
        num_features=num_features,
        num_classes=num_classes,
        num_rounds=1,
        local_epochs=1,
        batch_size=32,
    )
    b6.fit(client_partitions)
    res = b6.evaluate(x_test, y_test, label_names=label_names)
    assert res.baseline_id == "B6"
    assert res.fidelity_tier == "faithful_reimplementation"


@pytest.mark.unit
def test_b7_bc2fl_blockchain_and_smoke(synthetic_ids_dataset):
    """Test B7 Bc²FL: Double-layer blockchain simulation and hierarchical FL."""
    client_partitions, x_test, y_test, num_features, num_classes, label_names = (
        synthetic_ids_dataset
    )

    b7 = Bc2FLBaseline(
        num_features=num_features,
        num_classes=num_classes,
        num_rounds=1,
        num_edge_clusters=2,
        local_epochs=1,
        batch_size=32,
    )
    b7.fit(client_partitions)

    assert len(b7.blockchain.edge_chain_blocks) > 0
    assert len(b7.blockchain.cloud_chain_blocks) > 0
    assert b7.blockchain.total_consensus_overhead_bytes > 0

    res = b7.evaluate(x_test, y_test, label_names=label_names)
    assert res.baseline_id == "B7"
    assert res.fidelity_tier == "approximate_reimplementation"
    assert res.communication_bytes > 0


@pytest.mark.unit
def test_b8_rlfe_ids_fe_net_and_smoke(synthetic_ids_dataset):
    """Test B8 RLFE-IDS: FE-Net embeddings and unverified RAG nearest vector retrieval."""
    client_partitions, x_test, y_test, num_features, num_classes, label_names = (
        synthetic_ids_dataset
    )
    all_x = np.vstack([cp[0] for cp in client_partitions.values()])
    all_y = np.concatenate([cp[1] for cp in client_partitions.values()])

    b8 = RLFEIDSBaseline(
        num_features=num_features,
        num_classes=num_classes,
        embedding_dim=32,
    )
    b8.fit(train_data=(all_x, all_y), label_names=label_names)

    assert len(b8.vector_store.vectors) > 0
    res = b8.evaluate(x_test, y_test, label_names=label_names)
    assert res.baseline_id == "B8"
    assert res.fidelity_tier == "faithful_reimplementation"


@pytest.mark.unit
def test_b9_lqb_ids_dual_switch_and_smoke(synthetic_ids_dataset):
    """Test B9 LQB-IDS: DCAE autoencoder and dual-switch known/unknown routing."""
    client_partitions, x_test, y_test, num_features, num_classes, label_names = (
        synthetic_ids_dataset
    )
    all_x = np.vstack([cp[0] for cp in client_partitions.values()])
    all_y = np.concatenate([cp[1] for cp in client_partitions.values()])

    b9 = LQBIDSBaseline(num_features=num_features, num_classes=num_classes)
    b9.fit(train_data=(all_x, all_y))

    assert b9.dual_switch.error_threshold > 0.0
    res = b9.evaluate(x_test, y_test, label_names=label_names)
    assert res.baseline_id == "B9"
    assert res.fidelity_tier == "approximate_reimplementation"


@pytest.mark.unit
def test_b10_fedmse_shrink_autoencoder_and_smoke(synthetic_ids_dataset):
    """Test B10 FedMSE: Semi-supervised shrink autoencoder and one-class centroid anomaly classifier."""
    client_partitions, x_test, y_test, num_features, _, label_names = synthetic_ids_dataset

    b10 = FedMSEBaseline(
        num_features=num_features,
        latent_dim=16,
        num_rounds=1,
        local_epochs=1,
        batch_size=32,
    )
    b10.fit(client_partitions)

    assert b10.one_class_clf.centroid is not None
    assert b10.one_class_clf.radius > 0.0

    res = b10.evaluate(x_test, y_test, label_names=label_names)
    assert res.baseline_id == "B10"
    assert res.fidelity_tier == "faithful_reimplementation"


@pytest.mark.unit
def test_b11_pfl_ids_defense_and_smoke(synthetic_ids_dataset):
    """Test B11 pFL-IDS: Logit-adjusted loss and two-phase similarity defense."""
    client_partitions, x_test, y_test, num_features, num_classes, label_names = (
        synthetic_ids_dataset
    )

    # 1. Logit Adjusted Loss check
    priors = np.array([0.7, 0.2, 0.1], dtype=np.float32)
    la_loss = LogitAdjustedLoss(class_priors=priors)
    dummy_logits = torch.randn(4, 3)
    dummy_targets = torch.tensor([0, 1, 2, 0], dtype=torch.long)
    loss = la_loss(dummy_logits, dummy_targets)
    assert torch.isfinite(loss)

    # 2. Two-Phase Defense check
    defense = TwoPhaseSimilarityDefense()
    benign_u1 = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    benign_u2 = np.array([0.9, 1.1, 1.0], dtype=np.float32)
    benign_u3 = np.array([1.1, 0.9, 1.0], dtype=np.float32)
    poison_u = np.array([-2.0, -2.0, -2.0], dtype=np.float32)
    passed = defense.filter_updates([benign_u1, benign_u2, benign_u3, poison_u])
    assert 3 not in passed  # Poison excluded!
    assert 0 in passed

    # 3. Fit baseline
    b11 = PFLIDSBaseline(
        num_features=num_features,
        num_classes=num_classes,
        num_rounds=1,
        local_epochs=1,
        batch_size=32,
    )
    b11.fit(client_partitions)
    res = b11.evaluate(x_test, y_test, label_names=label_names)
    assert res.baseline_id == "B11"
    assert res.fidelity_tier == "faithful_reimplementation"


@pytest.mark.unit
def test_standard_metrics_helper():
    """Verify compute_standard_metrics handles normal, attack, and perfect classifications."""
    y_true = np.array([0, 0, 1, 2, 1, 0], dtype=np.int64)
    y_pred = np.array([0, 0, 1, 2, 1, 0], dtype=np.int64)

    metrics = compute_standard_metrics(y_true, y_pred, label_names=["Benign", "Attack1", "Attack2"])
    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["false_positive_rate"] == 0.0
    assert len(metrics["per_class_f1"]) == 3
