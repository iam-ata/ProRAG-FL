"""Unit tests for EdgeIIoTsetAdapter and Malware family held-out firewall."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from prorag_fl.data.edge_iiotset import (
    EdgeIIoTsetAdapter,
)


@pytest.fixture
def mock_edge_df() -> pd.DataFrame:
    """Create synthetic DataFrame matching Edge-IIoTset schema."""
    rng = np.random.default_rng(42)
    n_samples = 300

    labels = [
        "Normal",
        "DDoS_UDP",
        "DDoS_ICMP",
        "SQL_injection",
        "Port_Scanning",
        "MITM",
        "Backdoor",  # Malware (held-out)
        "Ransomware",  # Malware (held-out)
        "Uploading",  # Malware (held-out)
    ]

    assigned_labels = rng.choice(labels, size=n_samples)

    data: dict[str, list[object] | np.ndarray] = {
        # Leakage/metadata columns
        "frame.time": [f"2021-09-01 10:{i % 60:02d}:00" for i in range(n_samples)],
        "ip.src_host": [f"192.168.1.{i % 10}" for i in range(n_samples)],
        "ip.dst_host": ["192.168.1.100"] * n_samples,
        "arp.src.proto_ipv4": ["192.168.1.1"] * n_samples,
        "arp.dst.proto_ipv4": ["192.168.1.100"] * n_samples,
        "http.file_data": ["none"] * n_samples,
        "http.request.full_uri": ["http://example.com/test"] * n_samples,
        "http.referer": ["http://example.com"] * n_samples,
        "http.request.version": ["HTTP/1.1"] * n_samples,
        "dns.qry.name": ["dns.example.com"] * n_samples,
        "tcp.payload": ["001122"] * n_samples,
        "tcp.options": ["opt"] * n_samples,
        "tcp.srcport": [str(rng.integers(1024, 65535)) for _ in range(n_samples)],
        "mqtt.msg": ["msg"] * n_samples,
        # Constant column
        "icmp.unused": np.zeros(n_samples),
        # Valid numerical features
        "arp.opcode": rng.integers(0, 3, size=n_samples).astype(float),
        "arp.hw.size": rng.integers(0, 7, size=n_samples).astype(float),
        "icmp.checksum": rng.uniform(0, 65535, size=n_samples),
        "tcp.len": rng.uniform(0, 1500, size=n_samples),
        "tcp.ack": rng.uniform(0, 100000, size=n_samples),
        "udp.port": rng.integers(0, 100, size=n_samples).astype(float),
        # Targets
        "Attack_label": [0 if lab == "Normal" else 1 for lab in assigned_labels],
        "Attack_type": assigned_labels,
    }

    return pd.DataFrame(data)


@pytest.mark.unit
def test_edge_schema_and_leakage_audit(mock_edge_df: pd.DataFrame) -> None:
    """Verify that leakage, constant, and identifier columns are flagged and excluded."""
    adapter = EdgeIIoTsetAdapter()
    schema, audits = adapter.audit_schema_and_leakage(mock_edge_df)

    assert "frame.time" in schema.dropped_columns
    assert "ip.src_host" in schema.dropped_columns
    assert "ip.dst_host" in schema.dropped_columns
    assert "http.request.full_uri" in schema.dropped_columns
    assert "tcp.payload" in schema.dropped_columns
    assert "icmp.unused" in schema.dropped_columns
    assert "Attack_type" in schema.dropped_columns or schema.target_column == "Attack_type"

    # Numeric features must include valid measurements
    assert "tcp.len" in schema.numeric_features
    assert "icmp.checksum" in schema.numeric_features
    assert "arp.opcode" in schema.numeric_features


@pytest.mark.unit
def test_edge_canonicalize_labels(mock_edge_df: pd.DataFrame) -> None:
    """Verify label canonicalization and Malware held-out tagging."""
    adapter = EdgeIIoTsetAdapter()
    df_canon, mapping = adapter.canonicalize_labels(mock_edge_df)

    assert "canonical_label" in df_canon.columns
    assert "family" in df_canon.columns
    assert "target_id" in df_canon.columns
    assert "is_attack" in df_canon.columns

    # Check mapping details
    malware_info = mapping.class_details["Malware"]
    assert malware_info.is_held_out is True
    assert malware_info.is_attack is True

    benign_info = mapping.class_details["Benign"]
    assert benign_info.is_held_out is False
    assert benign_info.is_attack is False


@pytest.mark.unit
def test_edge_split_strict_malware_firewall(mock_edge_df: pd.DataFrame) -> None:
    """Verify that Malware family is strictly firewalled: 0 in train, 0 in val, present in test."""
    adapter = EdgeIIoTsetAdapter()
    df_canon, _ = adapter.canonicalize_labels(mock_edge_df)

    train_df, val_df, test_df, manifest = adapter.create_splits(
        df_canon,
        seed=13,
        test_ratio=0.15,
        val_ratio=0.15,
        held_out_family="Malware",
    )

    train_families = set(train_df["family"].str.lower())
    val_families = set(val_df["family"].str.lower())
    test_families = set(test_df["family"].str.lower())

    assert "malware" not in train_families, "Leakage: Malware found in training split!"
    assert "malware" not in val_families, "Leakage: Malware found in validation split!"
    assert "malware" in test_families, "Malware must be evaluated in test split!"

    # Ensure zero index overlap
    train_ids = set(manifest.train_indices)
    val_ids = set(manifest.val_indices)
    test_ids = set(manifest.test_indices)

    assert len(train_ids.intersection(val_ids)) == 0
    assert len(train_ids.intersection(test_ids)) == 0
    assert len(val_ids.intersection(test_ids)) == 0
