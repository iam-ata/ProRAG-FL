"""Tests for configuration parsing and schema validation."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from prorag_fl.schemas.config import (
    ExperimentConfig,
    load_and_validate_config,
    load_yaml_config,
    validate_config,
)


@pytest.mark.unit
def test_valid_config_validates_successfully(sample_config_dict):
    """Verify that a compliant dictionary validates into ExperimentConfig."""
    cfg = validate_config(sample_config_dict)
    assert isinstance(cfg, ExperimentConfig)
    assert cfg.experiment.id == "test_exp_01"
    assert cfg.dataset.name == "ciciot2023"
    assert cfg.dataset.held_out_family == "Mirai"
    assert cfg.training.seed == 13
    assert cfg.federated.num_clients == 10
    assert cfg.federated.strategy.beta == 0.20


@pytest.mark.unit
def test_default_yaml_file_validates(tmp_path):
    """Verify that configs/experiments/default.yaml passes validation."""
    from prorag_fl.core.paths import get_configs_dir

    default_yaml = get_configs_dir() / "experiments" / "default.yaml"
    assert default_yaml.is_file()

    cfg = load_and_validate_config(default_yaml)
    assert cfg.experiment.id == "default_experiment"
    assert cfg.dataset.name == "ciciot2023"


@pytest.mark.unit
def test_unknown_field_rejected(sample_config_dict):
    """Verify that extra unvalidated fields are forbidden (preventing configuration drift)."""
    bad_cfg = deepcopy(sample_config_dict)
    bad_cfg["unknown_scientific_parameter"] = "invalid"

    with pytest.raises(ValidationError):
        validate_config(bad_cfg)


@pytest.mark.unit
def test_invalid_dataset_name_rejected(sample_config_dict):
    """Verify that only authorized datasets (ciciot2023, edge_iiotset) are accepted."""
    bad_cfg = deepcopy(sample_config_dict)
    bad_cfg["dataset"]["name"] = "kdd99"  # Forbidden dataset

    with pytest.raises(ValidationError):
        validate_config(bad_cfg)


@pytest.mark.unit
def test_edge_iiotset_valid(sample_config_dict):
    """Verify edge_iiotset is accepted as a valid dataset."""
    cfg_data = deepcopy(sample_config_dict)
    cfg_data["dataset"]["name"] = "edge_iiotset"
    cfg_data["dataset"]["held_out_family"] = "Malware"

    cfg = validate_config(cfg_data)
    assert cfg.dataset.name == "edge_iiotset"
    assert cfg.dataset.held_out_family == "Malware"


@pytest.mark.unit
def test_invalid_test_ratio_rejected(sample_config_dict):
    """Verify validation boundaries on dataset splits."""
    bad_cfg = deepcopy(sample_config_dict)
    bad_cfg["dataset"]["test_ratio"] = 0.99  # Too high

    with pytest.raises(ValidationError):
        validate_config(bad_cfg)


@pytest.mark.unit
def test_load_yaml_missing_file_raises():
    """Verify FileNotFoundError when config file is not found."""
    with pytest.raises(FileNotFoundError):
        load_yaml_config("non_existent_config_file_xyz.yaml")
