"""Leakage-safe tabular preprocessor fitted exclusively on training data."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from prorag_fl.schemas.dataset import FeatureSchema


class FittedPreprocessor:
    """Preprocessor fitted exclusively on training data.

    Enforces:
    - Fixed feature order;
    - Median imputation for numerical features;
    - Standard scaling (mean and standard deviation computed strictly on train);
    - Frozen categorical mapping with fallback for unseen categories;
    - Output validation (zero NaNs, zero Infs, float32 array).
    """

    def __init__(self, feature_schema: FeatureSchema) -> None:
        self.feature_schema = feature_schema
        self.numeric_features = list(feature_schema.numeric_features)
        self.categorical_features = list(feature_schema.categorical_features)
        self.feature_order = list(feature_schema.final_feature_order)

        # Fitted statistics (empty until fit() is called)
        self.numeric_medians: dict[str, float] = {}
        self.numeric_means: dict[str, float] = {}
        self.numeric_stds: dict[str, float] = {}
        self.categorical_vocab: dict[str, dict[str, int]] = {}
        self.is_fitted: bool = False
        self.preprocessor_hash: str = ""

    def fit(self, train_df: pd.DataFrame) -> FittedPreprocessor:
        """Compute all normalization and imputation statistics exclusively from train_df."""
        # Numerical features
        for col in self.numeric_features:
            if col not in train_df.columns:
                raise ValueError(f"Numeric column '{col}' missing from training dataframe.")
            series = pd.to_numeric(train_df[col], errors="coerce").replace(
                [np.inf, -np.inf], np.nan
            )
            median_val = float(series.median())
            if np.isnan(median_val):
                median_val = 0.0
            self.numeric_medians[col] = median_val

            imputed = series.fillna(median_val)
            mean_val = float(imputed.mean())
            std_val = float(imputed.std(ddof=0))
            if std_val < 1e-7 or np.isnan(std_val):
                std_val = 1.0  # Constant column fallback

            self.numeric_means[col] = mean_val
            self.numeric_stds[col] = std_val

        # Categorical features
        for col in self.categorical_features:
            if col not in train_df.columns:
                raise ValueError(f"Categorical column '{col}' missing from training dataframe.")
            unique_vals = train_df[col].astype(str).unique().tolist()
            # Map index 0 to <UNK>, subsequent to known categories
            vocab = {"<UNK>": 0}
            for idx, val in enumerate(sorted(unique_vals), start=1):
                vocab[val] = idx
            self.categorical_vocab[col] = vocab

        self.is_fitted = True
        self.preprocessor_hash = self._compute_hash()
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform input dataframe into standardized float32 array using fitted statistics."""
        if not self.is_fitted:
            raise RuntimeError("Cannot transform before calling fit() on training split.")

        num_samples = len(df)
        num_features = len(self.feature_order)
        result = np.zeros((num_samples, num_features), dtype=np.float32)

        for out_idx, col in enumerate(self.feature_order):
            if col not in df.columns:
                raise ValueError(f"Required feature '{col}' missing in input dataframe.")

            if col in self.numeric_features:
                series = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
                median_val = self.numeric_medians[col]
                mean_val = self.numeric_means[col]
                std_val = self.numeric_stds[col]

                # Impute missing values with training median and scale
                imputed = series.fillna(median_val).to_numpy(dtype=np.float64)
                scaled = (imputed - mean_val) / std_val
                result[:, out_idx] = scaled.astype(np.float32)

            elif col in self.categorical_features:
                vocab = self.categorical_vocab[col]
                mapped = (
                    df[col]
                    .astype(str)
                    .map(lambda x, v=vocab: v.get(x, 0))
                    .to_numpy(dtype=np.float32)
                )
                result[:, out_idx] = mapped

            else:
                raise ValueError(
                    f"Feature '{col}' in feature_order is neither numeric nor categorical."
                )

        # Strict validation checks
        if np.isnan(result).any():
            raise AssertionError(f"Transformed features contain NaN values in {col}!")
        if np.isinf(result).any():
            raise AssertionError(f"Transformed features contain Infinite values in {col}!")

        return result

    def _compute_hash(self) -> str:
        """Compute deterministic SHA-256 hash of all fitted statistics."""
        summary: dict[str, Any] = {
            "dataset_name": self.feature_schema.dataset_name,
            "feature_order": self.feature_order,
            "numeric_means": {k: round(v, 6) for k, v in self.numeric_means.items()},
            "numeric_stds": {k: round(v, 6) for k, v in self.numeric_stds.items()},
            "numeric_medians": {k: round(v, 6) for k, v in self.numeric_medians.items()},
            "categorical_vocab": self.categorical_vocab,
        }
        raw_bytes = json.dumps(summary, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()

    def save(self, output_path: Path | str) -> Path:
        """Serialize fitted preprocessor to disk using joblib."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, file_path: Path | str) -> FittedPreprocessor:
        """Load fitted preprocessor from disk."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Preprocessor file not found: {path}")
        instance = joblib.load(path)
        if not isinstance(instance, FittedPreprocessor):
            raise TypeError(f"Loaded object from {path} is not a FittedPreprocessor.")
        return instance
