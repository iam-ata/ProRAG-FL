"""Unit tests for FittedPreprocessor."""

import numpy as np
import pandas as pd
import pytest

from prorag_fl.data.preprocessor import FittedPreprocessor
from prorag_fl.schemas.dataset import FeatureSchema


@pytest.fixture
def dummy_schema() -> FeatureSchema:
    return FeatureSchema(
        dataset_name="dummy",
        numeric_features=["num_a", "num_b"],
        categorical_features=["cat_c"],
        target_column="target",
        final_feature_order=["num_a", "cat_c", "num_b"],
    )


@pytest.mark.unit
def test_preprocessor_fit_and_transform(dummy_schema, tmp_path):
    """Verify that preprocessing standardizes numeric data and encodes categoricals."""
    train_df = pd.DataFrame(
        {
            "num_a": [10.0, 20.0, 30.0, 40.0, 50.0],
            "num_b": [1.0, 2.0, np.nan, 4.0, 5.0],  # Has NaN
            "cat_c": ["TCP", "UDP", "TCP", "ICMP", "TCP"],
            "target": [0, 0, 1, 1, 0],
        }
    )

    test_df = pd.DataFrame(
        {
            "num_a": [15.0, 25.0],
            "num_b": [2.5, np.inf],  # Has Inf
            "cat_c": ["UDP", "UNKNOWN_PROTOCOL"],  # Has unseen category
            "target": [0, 1],
        }
    )

    prep = FittedPreprocessor(dummy_schema)
    prep.fit(train_df)

    # Check fitted values
    assert prep.is_fitted
    assert prep.numeric_medians["num_b"] == 3.0  # Median of [1, 2, 4, 5] is (2 + 4) / 2 = 3.0
    assert "TCP" in prep.categorical_vocab["cat_c"]
    assert "<UNK>" in prep.categorical_vocab["cat_c"]

    # Transform train and test
    X_train = prep.transform(train_df)
    X_test = prep.transform(test_df)

    assert X_train.shape == (5, 3)
    assert X_test.shape == (2, 3)
    assert X_train.dtype == np.float32
    assert X_test.dtype == np.float32

    # Verify zero NaNs and zero Infs
    assert not np.isnan(X_train).any()
    assert not np.isnan(X_test).any()
    assert not np.isinf(X_train).any()
    assert not np.isinf(X_test).any()

    # Serialization test
    saved_path = prep.save(tmp_path / "preprocessor.joblib")
    loaded = FittedPreprocessor.load(saved_path)
    X_test_loaded = loaded.transform(test_df)
    np.testing.assert_allclose(X_test, X_test_loaded)
