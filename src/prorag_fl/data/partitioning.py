"""Federated client partitioning for training splits (IID and Dirichlet non-IID)."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence

import numpy as np

from prorag_fl.schemas.dataset import ClientPartitionInfo, PartitionManifest


def compute_label_entropy(class_counts: dict[str, int]) -> float:
    """Compute Shannon entropy (in bits) of a class distribution."""
    total = sum(class_counts.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in class_counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return float(entropy)


def partition_iid(
    train_indices: Sequence[int],
    train_labels: Sequence[str | int],
    num_clients: int,
    seed: int,
    dataset_name: str,
    split_hash: str,
) -> PartitionManifest:
    """Deterministically partition training indices into K near-equal IID subsets."""
    if num_clients <= 0:
        raise ValueError(f"num_clients must be positive, got {num_clients}")

    n_samples = len(train_indices)
    if n_samples < num_clients:
        raise ValueError(f"Cannot partition {n_samples} samples among {num_clients} clients")

    rng = np.random.default_rng(seed)
    shuffled_order = rng.permutation(n_samples)

    client_splits = np.array_split(shuffled_order, num_clients)
    clients: list[ClientPartitionInfo] = []
    entropies: list[float] = []

    for c_id, split in enumerate(client_splits):
        client_sample_indices = [train_indices[i] for i in split]
        counts: dict[str, int] = {}
        for i in split:
            lbl = str(train_labels[i])
            counts[lbl] = counts.get(lbl, 0) + 1

        clients.append(
            ClientPartitionInfo(
                client_id=c_id,
                num_samples=len(client_sample_indices),
                sample_indices=client_sample_indices,
                class_counts=counts,
            )
        )
        entropies.append(compute_label_entropy(counts))

    avg_entropy = float(np.mean(entropies))
    manifest_data = {
        "dataset": dataset_name,
        "split_hash": split_hash,
        "type": "iid",
        "num_clients": num_clients,
        "seed": seed,
        "client_sizes": [c.num_samples for c in clients],
    }
    manifest_hash = hashlib.sha256(
        json.dumps(manifest_data, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]

    return PartitionManifest(
        dataset_name=dataset_name,
        split_hash=split_hash,
        num_clients=num_clients,
        partition_type="iid",
        alpha=None,
        seed=seed,
        clients=clients,
        summary_heterogeneity_entropy=round(avg_entropy, 4),
        manifest_hash=manifest_hash,
    )


def partition_dirichlet(
    train_indices: Sequence[int],
    train_labels: Sequence[str | int],
    num_clients: int,
    alpha: float,
    seed: int,
    dataset_name: str,
    split_hash: str,
    min_samples_per_client: int = 5,
    max_retries: int = 100,
) -> PartitionManifest:
    """Partition training indices using Dirichlet non-IID distribution with deterministic retry."""
    if num_clients <= 0:
        raise ValueError(f"num_clients must be positive, got {num_clients}")
    if alpha <= 0.0:
        raise ValueError(f"alpha must be positive, got {alpha}")

    unique_labels = sorted({str(lbl) for lbl in train_labels})

    # Group sample positions by class label
    label_to_positions: dict[str, list[int]] = {lbl: [] for lbl in unique_labels}
    for pos, lbl in enumerate(train_labels):
        label_to_positions[str(lbl)].append(pos)

    # Deterministic retry loop
    for attempt in range(max_retries):
        current_seed = seed + attempt * 10007
        rng = np.random.default_rng(current_seed)

        client_assigned_positions: list[list[int]] = [[] for _ in range(num_clients)]

        for _lbl, positions in label_to_positions.items():
            n_class_samples = len(positions)
            if n_class_samples == 0:
                continue

            shuffled_pos = rng.permutation(positions).tolist()

            # Sample client proportions from Dirichlet(alpha * ones(K))
            proportions = rng.dirichlet(np.repeat(alpha, num_clients))

            # Convert proportions into discrete sample counts
            counts = (proportions * n_class_samples).astype(int)
            remainder = n_class_samples - counts.sum()
            # Distribute remainder to clients with largest fractional remainder
            if remainder > 0:
                fractional = (proportions * n_class_samples) - counts
                top_clients = np.argsort(-fractional)[:remainder]
                for c in top_clients:
                    counts[c] += 1

            # Slice and assign class samples
            start = 0
            for c_id in range(num_clients):
                c_count = counts[c_id]
                if c_count > 0:
                    client_assigned_positions[c_id].extend(shuffled_pos[start : start + c_count])
                    start += c_count

        # Check minimum samples condition
        client_sizes = [len(pos_list) for pos_list in client_assigned_positions]
        if min(client_sizes) >= min_samples_per_client:
            # Succeeded! Build manifest
            clients: list[ClientPartitionInfo] = []
            entropies: list[float] = []

            for c_id in range(num_clients):
                c_positions = client_assigned_positions[c_id]
                client_sample_indices = [train_indices[p] for p in c_positions]

                class_counts: dict[str, int] = {}
                for p in c_positions:
                    lbl = str(train_labels[p])
                    class_counts[lbl] = class_counts.get(lbl, 0) + 1

                clients.append(
                    ClientPartitionInfo(
                        client_id=c_id,
                        num_samples=len(client_sample_indices),
                        sample_indices=client_sample_indices,
                        class_counts=class_counts,
                    )
                )
                entropies.append(compute_label_entropy(class_counts))

            avg_entropy = float(np.mean(entropies))
            manifest_data = {
                "dataset": dataset_name,
                "split_hash": split_hash,
                "type": "dirichlet",
                "alpha": alpha,
                "num_clients": num_clients,
                "seed": seed,
                "attempt": attempt,
                "client_sizes": client_sizes,
            }
            manifest_hash = hashlib.sha256(
                json.dumps(manifest_data, sort_keys=True).encode("utf-8")
            ).hexdigest()[:16]

            return PartitionManifest(
                dataset_name=dataset_name,
                split_hash=split_hash,
                num_clients=num_clients,
                partition_type="dirichlet",
                alpha=alpha,
                seed=seed,
                clients=clients,
                summary_heterogeneity_entropy=round(avg_entropy, 4),
                manifest_hash=manifest_hash,
            )

    raise RuntimeError(
        f"Failed to find valid Dirichlet partition satisfying min_samples_per_client={min_samples_per_client} "
        f"after {max_retries} deterministic attempts."
    )
