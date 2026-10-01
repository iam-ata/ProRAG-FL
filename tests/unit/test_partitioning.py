"""Unit tests for federated client partitioning (IID and Dirichlet non-IID)."""

import numpy as np
import pytest

from prorag_fl.data.partitioning import partition_dirichlet, partition_iid


@pytest.fixture
def dummy_train_data():
    """Create synthetic training indices and labels for 1000 samples across 5 classes."""
    np.random.seed(13)
    n_samples = 1000
    classes = ["Benign", "DDoS", "DoS", "Recon", "Web"]
    labels = np.random.choice(classes, size=n_samples, p=[0.4, 0.25, 0.15, 0.1, 0.1]).tolist()
    indices = list(range(n_samples))
    return indices, labels


@pytest.mark.unit
def test_iid_partition_completeness_and_balance(dummy_train_data):
    """Verify that IID partition assigns every sample once without duplicates."""
    indices, labels = dummy_train_data
    manifest = partition_iid(
        train_indices=indices,
        train_labels=labels,
        num_clients=10,
        seed=13,
        dataset_name="ciciot2023",
        split_hash="mock_hash_123",
    )

    assert len(manifest.clients) == 10
    assigned_indices = []
    for client in manifest.clients:
        assert client.num_samples == len(client.sample_indices)
        assigned_indices.extend(client.sample_indices)

    # Every sample assigned exactly once
    assert len(assigned_indices) == len(indices)
    assert set(assigned_indices) == set(indices)
    assert len(set(assigned_indices)) == len(assigned_indices)


@pytest.mark.unit
@pytest.mark.parametrize("alpha", [1.0, 0.5, 0.3, 0.1])
def test_dirichlet_partition_invariants(dummy_train_data, alpha):
    """Verify Dirichlet partition satisfies sample conservation and minimum size across all alphas."""
    indices, labels = dummy_train_data
    min_samples = 10
    manifest = partition_dirichlet(
        train_indices=indices,
        train_labels=labels,
        num_clients=10,
        alpha=alpha,
        seed=13,
        dataset_name="ciciot2023",
        split_hash="mock_hash_123",
        min_samples_per_client=min_samples,
    )

    assert len(manifest.clients) == 10
    assigned_indices = []
    for client in manifest.clients:
        assert client.num_samples >= min_samples
        assert client.num_samples == len(client.sample_indices)
        assigned_indices.extend(client.sample_indices)

    # Sample conservation
    assert len(assigned_indices) == len(indices)
    assert set(assigned_indices) == set(indices)


@pytest.mark.unit
def test_dirichlet_alpha_heterogeneity_entropy(dummy_train_data):
    """Verify that smaller alpha (more non-IID) yields lower label entropy on average."""
    indices, labels = dummy_train_data

    m_high = partition_dirichlet(
        train_indices=indices,
        train_labels=labels,
        num_clients=5,
        alpha=1.0,
        seed=13,
        dataset_name="ciciot2023",
        split_hash="mock_hash_123",
    )

    m_low = partition_dirichlet(
        train_indices=indices,
        train_labels=labels,
        num_clients=5,
        alpha=0.1,
        seed=13,
        dataset_name="ciciot2023",
        split_hash="mock_hash_123",
    )

    # Lower alpha produces more class skew, hence lower entropy
    assert m_low.summary_heterogeneity_entropy < m_high.summary_heterogeneity_entropy


@pytest.mark.unit
def test_partition_deterministic_reproducibility(dummy_train_data):
    """Verify that running partitioning with the same seed reproduces the exact manifest hash."""
    indices, labels = dummy_train_data

    m1 = partition_dirichlet(
        train_indices=indices,
        train_labels=labels,
        num_clients=10,
        alpha=0.3,
        seed=73,
        dataset_name="ciciot2023",
        split_hash="mock_hash_123",
    )

    m2 = partition_dirichlet(
        train_indices=indices,
        train_labels=labels,
        num_clients=10,
        alpha=0.3,
        seed=73,
        dataset_name="ciciot2023",
        split_hash="mock_hash_123",
    )

    assert m1.manifest_hash == m2.manifest_hash

    # Different seed yields different hash
    m3 = partition_dirichlet(
        train_indices=indices,
        train_labels=labels,
        num_clients=10,
        alpha=0.3,
        seed=101,
        dataset_name="ciciot2023",
        split_hash="mock_hash_123",
    )
    assert m1.manifest_hash != m3.manifest_hash
