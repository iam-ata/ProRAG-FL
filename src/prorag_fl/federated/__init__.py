"""Federated learning module for ProRAG-FL using Flower."""

from prorag_fl.federated.client import FlowerIDSClient
from prorag_fl.federated.provenance_envelope import (
    ProvenanceVerifier,
    compute_ndarrays_digest,
    create_provenance_envelope,
    serialize_ndarrays,
)
from prorag_fl.federated.simulation import run_fl_simulation
from prorag_fl.federated.strategies import (
    ProvenanceGatedFedTrimmedAvg,
    create_fedavg_strategy,
    create_fedtrimmedavg_strategy,
    create_multikrum_strategy,
)

__all__ = [
    "FlowerIDSClient",
    "create_provenance_envelope",
    "ProvenanceVerifier",
    "serialize_ndarrays",
    "compute_ndarrays_digest",
    "create_fedavg_strategy",
    "create_multikrum_strategy",
    "create_fedtrimmedavg_strategy",
    "ProvenanceGatedFedTrimmedAvg",
    "run_fl_simulation",
]
