"""Unit tests for dataset manifest and schema models."""

import pytest

from prorag_fl.schemas.dataset import (
    FeatureSchema,
    RawDatasetManifest,
    RawFileEntry,
    SplitManifest,
)


@pytest.mark.unit
def test_raw_file_entry_and_manifest():
    """Verify RawFileEntry and RawDatasetManifest serialization."""
    entry = RawFileEntry(
        relative_path="part1.csv",
        byte_size=10240,
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        row_count=100,
        columns=["f1", "f2", "label"],
    )
    manifest = RawDatasetManifest(
        dataset_name="ciciot2023",
        files=[entry],
        total_bytes=10240,
        total_rows=100,
    )
    assert manifest.dataset_name == "ciciot2023"
    assert len(manifest.files) == 1
    assert manifest.total_bytes == 10240


@pytest.mark.unit
def test_feature_schema_and_column_audit():
    """Verify FeatureSchema captures dropped and active columns."""
    schema = FeatureSchema(
        dataset_name="ciciot2023",
        numeric_features=["flow_duration", "rate"],
        categorical_features=["protocol"],
        target_column="label",
        dropped_columns={"src_ip": "Direct IP leakage", "timestamp": "Timestamp leakage"},
        final_feature_order=["flow_duration", "protocol", "rate"],
    )
    assert len(schema.final_feature_order) == 3
    assert "src_ip" in schema.dropped_columns


@pytest.mark.unit
def test_split_manifest_model():
    """Verify SplitManifest model validation."""
    split = SplitManifest(
        dataset_name="ciciot2023",
        split_seed=13,
        test_ratio=0.20,
        val_ratio=0.10,
        held_out_family="Mirai",
        train_count=700,
        val_count=100,
        test_count=200,
        total_count=1000,
        train_indices=list(range(700)),
        val_indices=list(range(700, 800)),
        test_indices=list(range(800, 1000)),
        train_class_counts={"Benign": 500, "DDoS": 200},
        val_class_counts={"Benign": 70, "DDoS": 30},
        test_class_counts={"Benign": 100, "DDoS": 50, "Mirai": 50},
        split_hash="a1b2c3d4e5f67890",
    )
    assert split.held_out_family == "Mirai"
    assert split.total_count == 1000
    assert "Mirai" not in split.train_class_counts
