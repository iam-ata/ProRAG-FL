# Baseline Fidelity Card — B7 Bc²FL

## Citation
- **Title**: Bc²FL: Double-Layer Blockchain-Driven Federated Learning Framework for Agricultural IoT
- **Authors**: IEEE Internet of Things Journal
- **Venue**: IEEE Internet of Things Journal
- **Year**: 2025
- **DOI**: 10.1109/JIOT.2024.3485208

## Source code
- **Official repo**: Not publicly hosted; reimplemented as an architectural/system comparator.
- **Commit/tag**: `HEAD` (Phase 10)
- **License**: N/A
- **Access date**: 2026-09-25

## Defining components
- Double-layer blockchain architecture:
  - Layer 1: Edge Cluster Consensus recording intra-cluster model aggregations.
  - Layer 2: Cloud Global Consensus anchoring cross-cluster checkpoints.
- Two-stage consensus message passing simulation.
- Adaptive model quality aggregation: weights regional models according to validation quality score $Q_r = \exp(-\text{Loss}_r)$.

## Original datasets and task
- Agricultural IoT sensory classification.

## Original preprocessing
- Domain sensory normalization.

## Original model
- Domain-specific IoT neural network.

## Original FL/threat settings
- Hierarchical double-chain federated learning.

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| Edge Clusters | 2 (in benchmark) / configurable | Section III |
| Quality function | Exponential inverse validation loss | Section IV-B |
| Layer Structure | 2-tier (Edge + Cloud) | Section III-A |

## Missing/ambiguous details
- Specific blockchain VM smart contract bytecode (simulated via cryptographic SHA-256 state transitions and PBFT/BFT message byte accounting).

## Our implementation
- Implemented in `src/prorag_fl/baselines/bc2fl.py` under Mode B (component/system comparison).

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| Workload | Agricultural IoT | Network Intrusion Detection (NIDS) | Unified benchmark evaluation | Direct comparison of double-chain overhead on IDS |

## Fidelity
`approximate_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b7_bc2fl_blockchain_and_smoke`.
- Stage 1 edge block commits and Stage 2 cloud block hashes validated with consensus byte overhead accounting.

## Allowed manuscript wording
"Bc²FL is evaluated as an approximate architectural comparator (Mode B, IEEE JIOT, 2025) to measure the consensus and communication overhead of a hierarchical double-layer blockchain control plane under our standard IDS workload."
