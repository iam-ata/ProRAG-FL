"""Pydantic configuration models and YAML validation for ProRAG-FL."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExperimentMetaConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., description="Unique experiment or baseline run identifier")
    description: str | None = Field(
        default=None, description="Optional description of the experiment"
    )


class DatasetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Literal["ciciot2023", "edge_iiotset"] = Field(..., description="Target dataset name")
    split_seed: int = Field(default=13, description="Seed used for train/val/test data splits")
    held_out_family: str | None = Field(
        default=None,
        description="Unseen-to-model attack family to hold out (e.g. Mirai for CICIoT2023, Malware for Edge-IIoTset)",
    )
    test_ratio: float = Field(default=0.20, ge=0.05, le=0.50)
    val_ratio: float = Field(default=0.10, ge=0.05, le=0.30)


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(default="ids_1dcnn")
    conv_channels: list[int] = Field(default=[64, 128, 256])
    embedding_dim: int = Field(default=128)
    dropout: float = Field(default=0.30, ge=0.0, le=0.9)


class TrainingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    optimizer: Literal["adamw", "adam", "sgd"] = Field(default="adamw")
    lr: float = Field(default=0.001, gt=0.0)
    weight_decay: float = Field(default=0.0001, ge=0.0)
    batch_size: int = Field(default=256, gt=0)
    local_epochs: int = Field(default=2, gt=0)
    global_rounds: int = Field(default=50, gt=0)
    seed: int = Field(default=13)

    @field_validator("seed")
    @classmethod
    def warn_if_not_primary_seed(cls, v: int) -> int:
        # We allow arbitrary seeds for testing/ablation, but primary evaluations use standard seeds
        return v


class PartitionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["iid", "dirichlet"] = Field(default="dirichlet")
    alpha: float | None = Field(default=0.3, gt=0.0)


class StrategyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(default="provenance_gated_trimmed_avg")
    beta: float = Field(default=0.20, ge=0.0, lt=0.50)


class FederatedConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    num_clients: int = Field(default=10, gt=0)
    fraction_fit: float = Field(default=1.0, gt=0.0, le=1.0)
    partition: PartitionConfig = Field(default_factory=PartitionConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)


class AttackConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(default="none")
    malicious_client_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    poison_budget: float = Field(default=0.0, ge=0.0, le=1.0)


class RAGConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = Field(default=False)
    embedding_model: str = Field(default="BAAI/bge-m3")
    qdrant_url: str = Field(default="http://localhost:6333")
    top_candidates: int = Field(default=20, gt=0)
    top_verified: int = Field(default=5, gt=0)
    require_merkle_proof: bool = Field(default=True)


class OpenAIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = Field(default=False)
    mock: bool = Field(
        default=True, description="When True, uses deterministic MockReasoningClient"
    )
    model: str = Field(default="gpt-4o-mini")
    max_tokens: int = Field(default=1000, gt=0)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_retries: int = Field(default=3, ge=0)
    timeout_seconds: float = Field(default=30.0, gt=0.0)


class ExperimentConfig(BaseModel):
    """Authoritative scientific experiment configuration model."""

    model_config = ConfigDict(extra="forbid")

    experiment: ExperimentMetaConfig
    dataset: DatasetConfig
    model: ModelConfig = Field(default_factory=ModelConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    federated: FederatedConfig = Field(default_factory=FederatedConfig)
    attack: AttackConfig = Field(default_factory=AttackConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)


def load_yaml_config(file_path: Path | str) -> dict[str, Any]:
    """Load a raw YAML configuration file into a dictionary."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"YAML configuration in {path} must be a dictionary/mapping.")
    return data


def validate_config(config_dict: dict[str, Any]) -> ExperimentConfig:
    """Validate a configuration dictionary against the ExperimentConfig Pydantic model."""
    return ExperimentConfig.model_validate(config_dict)


def load_and_validate_config(file_path: Path | str) -> ExperimentConfig:
    """Convenience function to load a YAML file and validate it."""
    raw = load_yaml_config(file_path)
    return validate_config(raw)
