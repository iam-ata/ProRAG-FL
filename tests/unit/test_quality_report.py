"""Unit test for data quality report generation."""

import pandas as pd
import pytest

from prorag_fl.data.ciciot2023 import CICIoT2023Adapter
from prorag_fl.data.quality import generate_data_quality_report


@pytest.mark.unit
def test_generate_data_quality_report(tmp_path):
    """Verify that quality report markdown artifact is generated with all sections."""
    df = pd.DataFrame(
        {
            "flow_duration": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
            "Rate": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0],
            "src_ip": [f"10.0.0.{i}" for i in range(10)],
            "label": [
                "BenignTraffic",
                "BenignTraffic",
                "BenignTraffic",
                "BenignTraffic",
                "DDoS-ICMP_Flood",
                "DDoS-ICMP_Flood",
                "DoS-SYN_Flood",
                "DoS-SYN_Flood",
                "Mirai-greeth_flood",
                "Mirai-udpplain",
            ],
        }
    )

    adapter = CICIoT2023Adapter()
    df_canon, _ = adapter.canonicalize_labels(df)
    schema, audits = adapter.audit_schema_and_leakage(df_canon)

    train_df, val_df, test_df, split_manifest = adapter.create_splits(
        df_canon,
        seed=13,
        test_ratio=0.20,
        val_ratio=0.20,
        held_out_family="Mirai",
    )

    out_file = tmp_path / "ciciot2023_quality.md"
    report_path = generate_data_quality_report(
        dataset_name="ciciot2023",
        feature_schema=schema,
        column_audits=audits,
        split_manifest=split_manifest,
        output_path=out_file,
    )

    assert report_path.is_file()
    content = report_path.read_text(encoding="utf-8")
    assert "Data Quality & Leakage Audit Report: CICIOT2023" in content
    assert "Held-Out Attack Family Verification" in content
    assert "Mirai" in content
    assert "PASS" in content
    assert "Dropped & Leakage Columns" in content
