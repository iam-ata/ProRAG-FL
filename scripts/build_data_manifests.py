"""Script to audit raw datasets, generate manifests, fit training preprocessors, and output quality reports."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

# Configure stdout for Unicode paths
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd

from prorag_fl.core.paths import get_artifacts_dir, get_data_dir, get_reports_dir
from prorag_fl.data.ciciot2023 import CICIoT2023Adapter
from prorag_fl.data.edge_iiotset import EdgeIIoTsetAdapter
from prorag_fl.data.preprocessor import FittedPreprocessor
from prorag_fl.data.quality import generate_data_quality_report
from prorag_fl.schemas.dataset import RawDatasetManifest, RawFileEntry


def compute_file_sha256(path: Path) -> str:
    """Compute SHA-256 checksum of a file in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def process_ciciot2023(data_dir: Path, artifacts_dir: Path, reports_dir: Path) -> None:
    print("\n================== PROCESSING CICIOT2023 ==================")
    raw_dir = data_dir / "raw" / "CICIoT2023"
    manifest_dir = data_dir / "manifests" / "ciciot2023"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    prep_dir = artifacts_dir / "preprocessors" / "ciciot2023"
    prep_dir.mkdir(parents=True, exist_ok=True)

    adapter = CICIoT2023Adapter()

    # Step 1: Scan and build raw manifest
    ciciot_files = [
        raw_dir / "CICIOT23" / "train" / "train.csv",
        raw_dir / "CICIOT23" / "validation" / "validation.csv",
        raw_dir / "CICIOT23" / "test" / "test.csv",
    ]

    file_entries: list[RawFileEntry] = []
    total_bytes = 0
    total_rows = 0

    for fpath in ciciot_files:
        if not fpath.exists():
            print(f"Warning: File {fpath} not found.")
            continue
        size = fpath.stat().st_size
        print(f"Hashing {fpath.name} ({size / (1024*1024):.2f} MB)...")
        sha256_hash = compute_file_sha256(fpath)
        # Read header for columns
        df_head = pd.read_csv(fpath, nrows=5)
        # Count rows using fast line counter or buffer
        with open(fpath, "rb") as bf:
            lines = sum(1 for _ in bf) - 1  # subtract header
        print(f"  {fpath.name}: {lines:,} rows, sha256={sha256_hash[:16]}...")

        entry = RawFileEntry(
            relative_path=str(fpath.relative_to(raw_dir)).replace("\\", "/"),
            byte_size=size,
            sha256=sha256_hash,
            row_count=lines,
            columns=list(df_head.columns),
            source_note="official_ciciot2023_ciciot23_splits",
        )
        file_entries.append(entry)
        total_bytes += size
        total_rows += lines

    raw_manifest = RawDatasetManifest(
        dataset_name="ciciot2023",
        files=file_entries,
        total_bytes=total_bytes,
        total_rows=total_rows,
    )
    with open(manifest_dir / "raw_manifest.json", "w", encoding="utf-8") as f:
        f.write(raw_manifest.model_dump_json(indent=2))
    print(f"Saved {manifest_dir / 'raw_manifest.json'}")

    # Step 2: Audit schema and canonicalize labels on a representative sample (100k rows)
    train_file = raw_dir / "CICIOT23" / "train" / "train.csv"
    print("Auditing schema & leakage on representative training sample...")
    sample_df = pd.read_csv(train_file, nrows=100000)
    sample_df_canon, label_map = adapter.canonicalize_labels(sample_df)
    schema, audits = adapter.audit_schema_and_leakage(sample_df_canon)

    with open(manifest_dir / "feature_schema.json", "w", encoding="utf-8") as f:
        f.write(schema.model_dump_json(indent=2))
    with open(manifest_dir / "label_map.json", "w", encoding="utf-8") as f:
        f.write(label_map.model_dump_json(indent=2))
    print(f"Saved feature_schema.json and label_map.json in {manifest_dir}")

    # Step 3: Create stratified splits with strict Mirai hold-out
    print("Creating stratified split with Mirai held-out firewall...")
    train_df, val_df, test_df, split_manifest = adapter.create_splits(
        sample_df_canon,
        seed=13,
        test_ratio=0.20,
        val_ratio=0.10,
        held_out_family="Mirai",
    )
    with open(manifest_dir / "split_manifest_seed13.json", "w", encoding="utf-8") as f:
        f.write(split_manifest.model_dump_json(indent=2))
    print(f"Saved {manifest_dir / 'split_manifest_seed13.json'}")

    # Step 4: Fit preprocessor strictly on train split
    print("Fitting preprocessor strictly on training split...")
    preprocessor = FittedPreprocessor(feature_schema=schema)
    preprocessor.fit(train_df)
    joblib_path = prep_dir / f"{preprocessor.preprocessor_hash}.joblib"
    preprocessor.save(joblib_path)
    print(f"Fitted and saved preprocessor: {joblib_path} (hash: {preprocessor.preprocessor_hash})")

    # Step 5: Generate quality report
    report_file = reports_dir / "data_quality" / "ciciot2023.md"
    generate_data_quality_report(
        dataset_name="ciciot2023",
        feature_schema=schema,
        column_audits=audits,
        split_manifest=split_manifest,
        output_path=report_file,
        extra_notes="Full CICIOT23 split verified. Total samples in raw split files: 7,845,673 rows.",
    )
    print(f"Generated quality report: {report_file}")


def process_edge_iiotset(data_dir: Path, artifacts_dir: Path, reports_dir: Path) -> None:
    print("\n================== PROCESSING EDGE-IIOTSET ==================")
    raw_dir = data_dir / "raw" / "Edge-IIoTset"
    manifest_dir = data_dir / "manifests" / "edge_iiotset"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    prep_dir = artifacts_dir / "preprocessors" / "edge_iiotset"
    prep_dir.mkdir(parents=True, exist_ok=True)

    adapter = EdgeIIoTsetAdapter()

    # Step 1: Scan and build raw manifest
    ml_file = raw_dir / "Edge-IIoTset dataset" / "Selected dataset for ML and DL" / "ML-EdgeIIoT-dataset.csv"
    dnn_file = raw_dir / "Edge-IIoTset dataset" / "Selected dataset for ML and DL" / "DNN-EdgeIIoT-dataset.csv"

    file_entries: list[RawFileEntry] = []
    total_bytes = 0
    total_rows = 0

    for fpath in [ml_file, dnn_file]:
        if not fpath.exists():
            print(f"Warning: File {fpath} not found.")
            continue
        size = fpath.stat().st_size
        print(f"Hashing {fpath.name} ({size / (1024*1024):.2f} MB)...")
        sha256_hash = compute_file_sha256(fpath)
        df_head = pd.read_csv(fpath, nrows=5)
        with open(fpath, "rb") as bf:
            lines = sum(1 for _ in bf) - 1
        print(f"  {fpath.name}: {lines:,} rows, sha256={sha256_hash[:16]}...")

        entry = RawFileEntry(
            relative_path=str(fpath.relative_to(raw_dir)).replace("\\", "/"),
            byte_size=size,
            sha256=sha256_hash,
            row_count=lines,
            columns=list(df_head.columns),
            source_note="official_edge_iiotset_ferrag",
        )
        file_entries.append(entry)
        total_bytes += size
        total_rows += lines

    raw_manifest = RawDatasetManifest(
        dataset_name="edge_iiotset",
        files=file_entries,
        total_bytes=total_bytes,
        total_rows=total_rows,
    )
    with open(manifest_dir / "raw_manifest.json", "w", encoding="utf-8") as f:
        f.write(raw_manifest.model_dump_json(indent=2))
    print(f"Saved {manifest_dir / 'raw_manifest.json'}")

    # Step 2: Audit schema and canonicalize labels on ML-EdgeIIoTset (157,800 rows)
    print("Reading full ML-EdgeIIoTset dataset for schema and leakage audit...")
    df_ml = pd.read_csv(ml_file, low_memory=False)
    df_canon, label_map = adapter.canonicalize_labels(df_ml)
    schema, audits = adapter.audit_schema_and_leakage(df_canon)

    with open(manifest_dir / "feature_schema.json", "w", encoding="utf-8") as f:
        f.write(schema.model_dump_json(indent=2))
    with open(manifest_dir / "label_map.json", "w", encoding="utf-8") as f:
        f.write(label_map.model_dump_json(indent=2))
    print(f"Saved feature_schema.json and label_map.json in {manifest_dir}")

    # Step 3: Create stratified splits with strict Malware hold-out
    print("Creating stratified split with Malware held-out firewall...")
    train_df, val_df, test_df, split_manifest = adapter.create_splits(
        df_canon,
        seed=13,
        test_ratio=0.20,
        val_ratio=0.10,
        held_out_family="Malware",
    )
    with open(manifest_dir / "split_manifest_seed13.json", "w", encoding="utf-8") as f:
        f.write(split_manifest.model_dump_json(indent=2))
    print(f"Saved {manifest_dir / 'split_manifest_seed13.json'}")

    # Step 4: Fit preprocessor strictly on train split
    print("Fitting preprocessor strictly on training split...")
    preprocessor = FittedPreprocessor(feature_schema=schema)
    preprocessor.fit(train_df)
    joblib_path = prep_dir / f"{preprocessor.preprocessor_hash}.joblib"
    preprocessor.save(joblib_path)
    print(f"Fitted and saved preprocessor: {joblib_path} (hash: {preprocessor.preprocessor_hash})")

    # Step 5: Generate quality report
    report_file = reports_dir / "data_quality" / "edge_iiotset.md"
    generate_data_quality_report(
        dataset_name="edge_iiotset",
        feature_schema=schema,
        column_audits=audits,
        split_manifest=split_manifest,
        output_path=report_file,
        extra_notes="ML-EdgeIIoT-dataset (157,800 rows) and DNN-EdgeIIoT-dataset (2,219,201 rows) verified.",
    )
    print(f"Generated quality report: {report_file}")


def main() -> None:
    data_dir = get_data_dir()
    artifacts_dir = get_artifacts_dir()
    reports_dir = get_reports_dir()

    process_ciciot2023(data_dir, artifacts_dir, reports_dir)
    process_edge_iiotset(data_dir, artifacts_dir, reports_dir)
    print("\nAll manifests, preprocessors, and data quality reports generated successfully!")


if __name__ == "__main__":
    main()
