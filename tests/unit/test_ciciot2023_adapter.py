"""Unit tests for CICIoT2023Adapter."""

import pandas as pd
import pytest

from prorag_fl.data.ciciot2023 import CICIoT2023Adapter


@pytest.fixture
def mock_ciciot_df() -> pd.DataFrame:
    """Return a mock dataframe representing CICIoT2023 raw flow data."""
    return pd.DataFrame(
        {
            "src_ip": ["192.168.1.10", "192.168.1.11", "10.0.0.5", "10.0.0.6", "172.16.0.2"],
            "timestamp": [
                "2023-07-01 10:00:00",
                "2023-07-01 10:00:01",
                "2023-07-01 10:00:02",
                "2023-07-01 10:00:03",
                "2023-07-01 10:00:04",
            ],
            "flow_duration": [120.5, 45.0, 300.2, 10.0, 50.0],
            "Rate": [1500.0, 200.0, 5000.0, 100.0, 800.0],
            "constant_col": [1, 1, 1, 1, 1],  # Constant column to drop
            "label": [
                "BenignTraffic",
                "Mirai-greeth_flood",
                "DDoS-ICMP_Flood",
                "DoS-SYN_Flood",
                "Recon-PortScan",
            ],
        }
    )


@pytest.mark.unit
def test_ciciot2023_audit_schema_and_leakage(mock_ciciot_df):
    """Verify that adapter identifies leakage identifiers and constant columns."""
    adapter = CICIoT2023Adapter()
    schema, audits = adapter.audit_schema_and_leakage(mock_ciciot_df)

    # Identifiers and timestamps must be dropped
    assert "src_ip" in schema.dropped_columns
    assert "timestamp" in schema.dropped_columns
    assert "constant_col" in schema.dropped_columns

    # Active features
    assert "flow_duration" in schema.numeric_features
    assert "Rate" in schema.numeric_features
    assert "label" not in schema.numeric_features


@pytest.mark.unit
def test_ciciot2023_canonicalize_labels(mock_ciciot_df):
    """Verify raw label mapping to canonical families."""
    adapter = CICIoT2023Adapter()
    df_canon, mapping = adapter.canonicalize_labels(mock_ciciot_df)

    assert "family" in df_canon.columns
    assert "target_id" in df_canon.columns
    assert "is_attack" in df_canon.columns

    # Check family assignments
    families = df_canon["family"].tolist()
    assert families == ["Benign", "Mirai", "DDoS", "DoS", "Recon"]

    # Mirai must be marked held-out
    assert mapping.class_details["Mirai"].is_held_out is True
    assert mapping.class_details["DDoS"].is_held_out is False
