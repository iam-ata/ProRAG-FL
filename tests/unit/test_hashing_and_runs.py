"""Tests for canonical hashing, run ID generation, and overwrite protection."""

import datetime
from copy import deepcopy

import pytest

from prorag_fl.core.hashing import (
    compute_config_hash,
    create_run_directory,
    generate_run_id,
    mark_run_completed,
)


@pytest.mark.unit
def test_same_config_produces_identical_hash(sample_config_dict):
    """Verify that identical configurations produce identical hashes regardless of key order."""
    cfg1 = deepcopy(sample_config_dict)
    # Reverse key ordering in a shallow copy
    cfg2 = {k: cfg1[k] for k in reversed(list(cfg1.keys()))}

    h1 = compute_config_hash(cfg1)
    h2 = compute_config_hash(cfg2)
    assert h1 == h2
    assert len(h1) == 12


@pytest.mark.unit
def test_different_config_produces_different_hash(sample_config_dict):
    """Verify that changing any scientific parameter changes the config hash."""
    cfg1 = deepcopy(sample_config_dict)
    cfg2 = deepcopy(sample_config_dict)
    cfg2["training"]["lr"] = 0.005

    h1 = compute_config_hash(cfg1)
    h2 = compute_config_hash(cfg2)
    assert h1 != h2

    # Different seed also produces different hash
    cfg3 = deepcopy(sample_config_dict)
    cfg3["training"]["seed"] = 37
    h3 = compute_config_hash(cfg3)
    assert h1 != h3


@pytest.mark.unit
def test_generate_run_id_format():
    """Verify generated run ID conforms to <exp>_<timestamp>_<shorthash>_seed<seed>."""
    fixed_ts = datetime.datetime(2026, 9, 25, 12, 0, 0, tzinfo=datetime.UTC)
    run_id = generate_run_id("test_exp", "b225b535aca7", 13, timestamp=fixed_ts)
    assert run_id == "test_exp_20260925_120000_b225b535_seed13"


@pytest.mark.unit
def test_create_run_directory_creates_subdirs(tmp_path):
    """Verify create_run_directory creates runs folder and checkpoints/logs/metrics subdirs."""
    run_id = "exp_sample_seed13"
    run_dir = create_run_directory(tmp_path, run_id)
    assert run_dir.exists()
    assert (run_dir / "checkpoints").is_dir()
    assert (run_dir / "logs").is_dir()
    assert (run_dir / "metrics").is_dir()


@pytest.mark.unit
def test_create_run_directory_prevents_silent_overwrite_of_completed_run(tmp_path):
    """Verify that attempting to create an already completed run directory raises FileExistsError."""
    run_id = "exp_completed_seed13"
    run_dir = create_run_directory(tmp_path, run_id)
    mark_run_completed(run_dir, {"status": "SUCCESS"})

    # Attempting to recreate the same run directory without resume must raise FileExistsError
    with pytest.raises(FileExistsError) as exc_info:
        create_run_directory(tmp_path, run_id, allow_resume=False)

    assert "COMPLETED marker" in str(exc_info.value)

    # But with allow_resume=True it should succeed
    resumed_dir = create_run_directory(tmp_path, run_id, allow_resume=True)
    assert resumed_dir == run_dir
