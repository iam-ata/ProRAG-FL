"""Tests for deterministic seed utilities across Python, NumPy, and PyTorch."""

import random

import numpy as np
import pytest
import torch

from prorag_fl.core.seeding import PRIMARY_SEEDS, get_primary_seeds, is_primary_seed, set_seed


@pytest.mark.unit
def test_primary_seeds_contents():
    """Verify primary research seeds match the contract specification: 13, 37, 73, 101, 211."""
    assert PRIMARY_SEEDS == (13, 37, 73, 101, 211)
    assert get_primary_seeds() == (13, 37, 73, 101, 211)
    for s in (13, 37, 73, 101, 211):
        assert is_primary_seed(s)
    assert not is_primary_seed(42)
    assert not is_primary_seed(999)


@pytest.mark.unit
def test_seed_reproduces_random():
    """Verify python random generator is reproducible with set_seed."""
    set_seed(13)
    val1 = [random.random() for _ in range(5)]

    set_seed(13)
    val2 = [random.random() for _ in range(5)]

    assert val1 == val2

    # Different seed should give different values
    set_seed(37)
    val3 = [random.random() for _ in range(5)]
    assert val1 != val3


@pytest.mark.unit
def test_seed_reproduces_numpy():
    """Verify NumPy random generator is reproducible with set_seed."""
    set_seed(73)
    arr1 = np.random.randn(10)

    set_seed(73)
    arr2 = np.random.randn(10)

    np.testing.assert_allclose(arr1, arr2)

    set_seed(101)
    arr3 = np.random.randn(10)
    assert not np.allclose(arr1, arr3)


@pytest.mark.unit
def test_seed_reproduces_torch():
    """Verify PyTorch CPU random tensor generator is reproducible with set_seed."""
    set_seed(211)
    t1 = torch.randn(4, 4)

    set_seed(211)
    t2 = torch.randn(4, 4)

    assert torch.equal(t1, t2)

    set_seed(13)
    t3 = torch.randn(4, 4)
    assert not torch.equal(t1, t3)
