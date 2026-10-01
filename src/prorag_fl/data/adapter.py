"""Abstract Base Class for leakage-safe Dataset Adapters."""

from __future__ import annotations

import abc
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

from prorag_fl.data.preprocessor import FittedPreprocessor
from prorag_fl.schemas.dataset import (
    ColumnAudit,
    FeatureSchema,
    LabelMapping,
    RawDatasetManifest,
    RawFileEntry,
    SplitManifest,
)


class DatasetAdapter(abc.ABC):
    """Abstract Base Class defining the standard lifecycle for research dataset ingestion."""

    def __init__(self, dataset_name: str) -> None:
        self.dataset_name = dataset_name

    def compute_file_sha256(self, file_path: Path, chunk_size: int = 1024 * 1024) -> str:
        """Compute SHA-256 checksum of a file efficiently in 1MB chunks."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()

    def scan_raw(self, raw_dir: Path) -> list[RawFileEntry]:
        """Scan raw directory, compute file checksums, sizes, and schema info."""
        if not raw_dir.is_dir():
            raise FileNotFoundError(f"Raw directory does not exist: {raw_dir}")

        entries: list[RawFileEntry] = []
        valid_extensions = {".csv", ".parquet", ".gz"}

        for p in sorted(raw_dir.glob("**/*")):
            if not p.is_file() or p.name.startswith(".") or p.name == ".gitkeep":
                continue
            if p.suffix.lower() not in valid_extensions and not any(
                p.name.endswith(ext) for ext in [".csv.gz", ".tar.gz"]
            ):
                continue

            rel_path = str(p.relative_to(raw_dir)).replace("\\", "/")
            byte_size = p.stat().st_size
            sha256_hash = self.compute_file_sha256(p)

            # Read first few lines for header if CSV
            columns: list[str] = []
            row_count: int | None = None
            try:
                if p.name.endswith(".parquet"):
                    df_sample = pd.read_parquet(p)
                    columns = list(df_sample.columns)
                    row_count = len(df_sample)
                elif p.name.endswith(".csv") or p.name.endswith(".csv.gz"):
                    # Sample header
                    df_sample = pd.read_csv(p, nrows=5)
                    columns = list(df_sample.columns)
            except Exception:
                pass

            entries.append(
                RawFileEntry(
                    relative_path=rel_path,
                    byte_size=byte_size,
                    sha256=sha256_hash,
                    row_count=row_count,
                    columns=columns,
                    source_note="verified_scan",
                )
            )
        return entries

    def build_raw_manifest(
        self, raw_dir: Path, output_file: Path | None = None
    ) -> RawDatasetManifest:
        """Build and optionally persist an immutable raw files manifest."""
        entries = self.scan_raw(raw_dir)
        total_bytes = sum(e.byte_size for e in entries)
        total_rows = sum(e.row_count for e in entries if e.row_count is not None) if entries else 0

        manifest = RawDatasetManifest(
            dataset_name=self.dataset_name,
            files=entries,
            total_bytes=total_bytes,
            total_rows=total_rows if total_rows > 0 else None,
        )

        if output_file:
            out_p = Path(output_file)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

        return manifest

    @abc.abstractmethod
    def audit_schema_and_leakage(
        self, df: pd.DataFrame
    ) -> tuple[FeatureSchema, dict[str, ColumnAudit]]:
        """Identify feature types, constant columns, leakage identifiers, and return locked FeatureSchema."""
        pass

    @abc.abstractmethod
    def canonicalize_labels(self, df: pd.DataFrame) -> tuple[pd.DataFrame, LabelMapping]:
        """Normalize dataset labels into canonical classes, attack families, and integer target IDs."""
        pass

    def create_splits(
        self,
        df: pd.DataFrame,
        seed: int,
        test_ratio: float = 0.20,
        val_ratio: float = 0.10,
        held_out_family: str | None = None,
        family_col: str = "family",
        target_col: str = "target_id",
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, SplitManifest]:
        """Strictly partition rows into train/validation/test sets.

        Held-out attack family samples are placed EXCLUSIVELY into the test set,
        ensuring they never leak into classifier training, calibration, or OOD statistics.
        """
        if test_ratio <= 0.0 or val_ratio <= 0.0 or (test_ratio + val_ratio) >= 1.0:
            raise ValueError(f"Invalid split ratios: test={test_ratio}, val={val_ratio}")

        total_rows = len(df)
        df_work = df.copy().reset_index(drop=True)

        held_out_indices: list[int] = []
        regular_indices: list[int] = []

        if held_out_family and family_col in df_work.columns:
            held_mask = df_work[family_col].astype(str).str.lower() == held_out_family.lower()
            held_out_indices = df_work[held_mask].index.tolist()
            regular_indices = df_work[~held_mask].index.tolist()
        else:
            regular_indices = list(range(total_rows))

        # Stratified split on non-held-out data
        regular_df = df_work.iloc[regular_indices]
        strat_labels = regular_df[target_col].to_numpy()

        # First split into train vs (val + test)
        val_test_ratio = test_ratio + val_ratio
        _, class_counts1 = np.unique(strat_labels, return_counts=True)
        if np.min(class_counts1) >= 2:
            splitter1 = StratifiedShuffleSplit(
                n_splits=1, test_size=val_test_ratio, random_state=seed
            )
            train_rel_idx, val_test_rel_idx = next(splitter1.split(regular_indices, strat_labels))
        else:
            from sklearn.model_selection import ShuffleSplit

            splitter1 = ShuffleSplit(n_splits=1, test_size=val_test_ratio, random_state=seed)
            train_rel_idx, val_test_rel_idx = next(splitter1.split(regular_indices))

        train_idx = [regular_indices[i] for i in train_rel_idx]
        val_test_sub_indices = [regular_indices[i] for i in val_test_rel_idx]
        val_test_sub_labels = regular_df.iloc[val_test_rel_idx][target_col].to_numpy()

        # Then split remaining into val and test
        val_proportion_of_remainder = val_ratio / val_test_ratio
        _, class_counts2 = np.unique(val_test_sub_labels, return_counts=True)
        if np.min(class_counts2) >= 2:
            splitter2 = StratifiedShuffleSplit(
                n_splits=1, test_size=1.0 - val_proportion_of_remainder, random_state=seed
            )
            val_rel_idx, test_rel_idx = next(
                splitter2.split(val_test_sub_indices, val_test_sub_labels)
            )
        else:
            from sklearn.model_selection import ShuffleSplit

            splitter2 = ShuffleSplit(
                n_splits=1, test_size=1.0 - val_proportion_of_remainder, random_state=seed
            )
            val_rel_idx, test_rel_idx = next(splitter2.split(val_test_sub_indices))

        val_idx = [val_test_sub_indices[i] for i in val_rel_idx]
        test_regular_idx = [val_test_sub_indices[i] for i in test_rel_idx]

        # Combine regular test indices with all held-out family indices
        test_idx = sorted([*test_regular_idx, *held_out_indices])

        # Strict firewall assertions
        train_set, val_set, test_set = set(train_idx), set(val_idx), set(test_idx)
        assert len(train_set.intersection(val_set)) == 0, (
            "Leakage detected: train and val share indices!"
        )
        assert len(train_set.intersection(test_set)) == 0, (
            "Leakage detected: train and test share indices!"
        )
        assert len(val_set.intersection(test_set)) == 0, (
            "Leakage detected: val and test share indices!"
        )
        assert len(train_set) + len(val_set) + len(test_set) == total_rows, (
            "Split does not partition all samples!"
        )

        if held_out_family:
            train_families = set(df_work.iloc[train_idx][family_col].astype(str).str.lower())
            val_families = set(df_work.iloc[val_idx][family_col].astype(str).str.lower())
            assert held_out_family.lower() not in train_families, (
                f"Held-out family {held_out_family} found in training!"
            )
            assert held_out_family.lower() not in val_families, (
                f"Held-out family {held_out_family} found in validation!"
            )

        train_df = df_work.iloc[train_idx].copy().reset_index(drop=True)
        val_df = df_work.iloc[val_idx].copy().reset_index(drop=True)
        test_df = df_work.iloc[test_idx].copy().reset_index(drop=True)

        # Build split hash
        split_summary: dict[str, Any] = {
            "dataset": self.dataset_name,
            "seed": seed,
            "train_len": len(train_idx),
            "val_len": len(val_idx),
            "test_len": len(test_idx),
            "held_out_family": held_out_family,
            "train_first_10": train_idx[:10],
            "val_first_10": val_idx[:10],
            "test_first_10": test_idx[:10],
        }
        split_hash = hashlib.sha256(str(split_summary).encode("utf-8")).hexdigest()[:16]

        manifest = SplitManifest(
            dataset_name=self.dataset_name,
            split_seed=seed,
            test_ratio=test_ratio,
            val_ratio=val_ratio,
            held_out_family=held_out_family,
            train_count=len(train_idx),
            val_count=len(val_idx),
            test_count=len(test_idx),
            total_count=total_rows,
            train_indices=train_idx,
            val_indices=val_idx,
            test_indices=test_idx,
            train_class_counts=train_df[family_col].value_counts().to_dict(),
            val_class_counts=val_df[family_col].value_counts().to_dict(),
            test_class_counts=test_df[family_col].value_counts().to_dict(),
            split_hash=split_hash,
        )

        return train_df, val_df, test_df, manifest

    def fit_and_transform_splits(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        feature_schema: FeatureSchema,
    ) -> tuple[FittedPreprocessor, np.ndarray, np.ndarray, np.ndarray]:
        """Fit preprocessor strictly on training data, then transform all splits."""
        preprocessor = FittedPreprocessor(feature_schema=feature_schema)
        preprocessor.fit(train_df)

        X_train = preprocessor.transform(train_df)
        X_val = preprocessor.transform(val_df)
        X_test = preprocessor.transform(test_df)

        return preprocessor, X_train, X_val, X_test
