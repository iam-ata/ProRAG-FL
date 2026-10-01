"""Core acceptance tests proving leakage-safe data splitting and preprocessing."""

import numpy as np
import pandas as pd
import pytest

from prorag_fl.data.ciciot2023 import CICIoT2023Adapter


@pytest.fixture
def synthetic_ciciot_dataset() -> pd.DataFrame:
    """Generate a synthetic multi-class flow dataset with Benign, DDoS, DoS, Recon, and Mirai."""
    np.random.seed(42)
    n_samples = 400

    classes = (
        ["BenignTraffic"] * 150
        + ["DDoS-ICMP_Flood"] * 100
        + ["DoS-TCP_Flood"] * 70
        + ["Recon-PortScan"] * 40
        + ["Mirai-greeth_flood"] * 40  # 40 Mirai samples to hold out
    )

    df = pd.DataFrame(
        {
            "flow_duration": np.random.uniform(1.0, 1000.0, size=n_samples),
            "Rate": np.random.exponential(500.0, size=n_samples),
            "fin_flag_number": np.random.binomial(1, 0.2, size=n_samples),
            "syn_flag_number": np.random.binomial(1, 0.4, size=n_samples),
            "timestamp": [f"2023-07-01 {i:04d}" for i in range(n_samples)],
            "src_ip": [f"192.168.1.{i % 50}" for i in range(n_samples)],
            "label": classes,
        }
    )
    return df


@pytest.mark.unit
def test_leakage_firewall_zero_index_overlap(synthetic_ciciot_dataset):
    """Verify train, val, and test splits have strict 0 index intersection."""
    adapter = CICIoT2023Adapter()
    df_canon, _ = adapter.canonicalize_labels(synthetic_ciciot_dataset)

    train_df, val_df, test_df, manifest = adapter.create_splits(
        df_canon,
        seed=13,
        test_ratio=0.20,
        val_ratio=0.10,
        held_out_family="Mirai",
    )

    train_set = set(manifest.train_indices)
    val_set = set(manifest.val_indices)
    test_set = set(manifest.test_indices)

    assert len(train_set.intersection(val_set)) == 0, "Train and Val share sample indices!"
    assert len(train_set.intersection(test_set)) == 0, "Train and Test share sample indices!"
    assert len(val_set.intersection(test_set)) == 0, "Val and Test share sample indices!"
    assert len(train_set) + len(val_set) + len(test_set) == len(synthetic_ciciot_dataset)


@pytest.mark.unit
def test_held_out_mirai_strictly_absent_from_train_and_val(synthetic_ciciot_dataset):
    """Verify that held-out attack family (Mirai) is completely absent from train and val."""
    adapter = CICIoT2023Adapter()
    df_canon, _ = adapter.canonicalize_labels(synthetic_ciciot_dataset)

    train_df, val_df, test_df, manifest = adapter.create_splits(
        df_canon,
        seed=13,
        test_ratio=0.20,
        val_ratio=0.10,
        held_out_family="Mirai",
    )

    # Check dataframe contents
    assert "Mirai" not in train_df["family"].values, "Mirai leaked into train dataframe!"
    assert "Mirai" not in val_df["family"].values, "Mirai leaked into validation dataframe!"

    # Check manifest counts
    assert manifest.train_class_counts.get("Mirai", 0) == 0
    assert manifest.val_class_counts.get("Mirai", 0) == 0

    # All Mirai samples must be in test set
    assert manifest.test_class_counts.get("Mirai", 0) == 40
    assert (test_df["family"] == "Mirai").sum() == 40


@pytest.mark.unit
def test_preprocessing_fitted_exclusively_on_train(synthetic_ciciot_dataset):
    """Verify that preprocessor statistics are derived strictly from train_df."""
    adapter = CICIoT2023Adapter()
    df_canon, _ = adapter.canonicalize_labels(synthetic_ciciot_dataset)
    schema, _ = adapter.audit_schema_and_leakage(df_canon)

    train_df, val_df, test_df, _ = adapter.create_splits(
        df_canon,
        seed=13,
        test_ratio=0.20,
        val_ratio=0.10,
        held_out_family="Mirai",
    )

    prep, X_train, X_val, X_test = adapter.fit_and_transform_splits(
        train_df, val_df, test_df, schema
    )

    # Check shapes
    num_features = len(schema.final_feature_order)
    assert X_train.shape == (len(train_df), num_features)
    assert X_val.shape == (len(val_df), num_features)
    assert X_test.shape == (len(test_df), num_features)

    # Verify train mean is near 0 and std is near 1
    np.testing.assert_allclose(X_train.mean(axis=0), 0.0, atol=1e-5)
    np.testing.assert_allclose(X_train.std(axis=0), 1.0, atol=1e-5)

    # Verify that test distribution does NOT force mean=0 (it is scaled by train stats)
    # This proves test data was NOT used in fitting!
    test_means = X_test.mean(axis=0)
    assert not np.allclose(test_means, 0.0, atol=1e-4)
