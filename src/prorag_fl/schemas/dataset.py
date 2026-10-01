"""Pydantic schemas for raw manifests, feature schemas, label mappings, and split/partition manifests."""

from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RawFileEntry(BaseModel):
    """Metadata entry for an individual raw dataset file."""

    model_config = ConfigDict(extra="forbid")

    relative_path: str = Field(..., description="Relative path from data/raw/<dataset>/")
    byte_size: int = Field(..., ge=0, description="Size in bytes")
    sha256: str = Field(..., description="SHA-256 hexadecimal checksum")
    row_count: int | None = Field(default=None, description="Number of rows if tabular")
    columns: list[str] = Field(default_factory=list, description="Column names found in the file")
    source_note: str = Field(default="official_mirror", description="Acquisition source or mirror")


class RawDatasetManifest(BaseModel):
    """Immutable manifest for all raw files of a dataset."""

    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    files: list[RawFileEntry]
    total_bytes: int = Field(..., ge=0)
    total_rows: int | None = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class ColumnAudit(BaseModel):
    """Audit details for a single dataset column."""

    model_config = ConfigDict(extra="forbid")

    dtype: str
    num_missing: int = 0
    num_infinite: int = 0
    num_unique: int = 0
    is_constant: bool = False
    is_all_null: bool = False


class FeatureSchema(BaseModel):
    """Schema defining feature classifications and dropped fields."""

    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    numeric_features: list[str]
    categorical_features: list[str]
    target_column: str
    identifier_columns: list[str] = Field(default_factory=list)
    timestamp_columns: list[str] = Field(default_factory=list)
    dropped_columns: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from dropped column name to exclusion rationale (e.g. leakage, constant, identifier)",
    )
    final_feature_order: list[str] = Field(
        default_factory=list,
        description="Exact locked ordered list of input features feeding the 1D-CNN",
    )


class LabelClassInfo(BaseModel):
    """Detailed taxonomy mapping for a specific class."""

    model_config = ConfigDict(extra="forbid")

    class_id: int
    canonical_name: str
    family: str
    is_attack: bool
    is_held_out: bool = False


class LabelMapping(BaseModel):
    """Complete versioned mapping from raw dataset labels to model taxonomy."""

    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    raw_to_canonical: dict[str, str]
    canonical_to_id: dict[str, int]
    id_to_canonical: dict[int, str]
    family_mapping: dict[str, str]
    class_details: dict[str, LabelClassInfo]
    num_classes: int


class SplitManifest(BaseModel):
    """Immutable manifest capturing the exact train/validation/test split."""

    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    split_seed: int
    test_ratio: float
    val_ratio: float
    held_out_family: str | None = None
    train_count: int
    val_count: int
    test_count: int
    total_count: int
    train_indices: list[int]
    val_indices: list[int]
    test_indices: list[int]
    train_class_counts: dict[str, int]
    val_class_counts: dict[str, int]
    test_class_counts: dict[str, int]
    split_hash: str = Field(..., description="SHA-256 digest of split indices and configurations")
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class ClientPartitionInfo(BaseModel):
    """Partition assignment for a single federated client."""

    model_config = ConfigDict(extra="forbid")

    client_id: int
    num_samples: int
    sample_indices: list[int]
    class_counts: dict[str, int]


class PartitionManifest(BaseModel):
    """Immutable manifest of federated client partitions derived strictly from training data."""

    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    split_hash: str
    num_clients: int
    partition_type: Literal["iid", "dirichlet"]
    alpha: float | None = None
    seed: int
    clients: list[ClientPartitionInfo]
    summary_heterogeneity_entropy: float = Field(
        ...,
        description="Average Shannon entropy of label distributions across clients",
    )
    manifest_hash: str
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
