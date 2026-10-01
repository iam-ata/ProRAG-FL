# Baseline Fidelity Card — B2 FedAvg

## Citation
- **Title**: Communication-Efficient Learning of Deep Networks from Decentralized Data
- **Authors**: H. Brendan McMahan, Eider Moore, Daniel Ramage, Seth Hampson, Blaise Agüera y Arcas
- **Venue**: AISTATS
- **Year**: 2017
- **DOI**: arXiv:1602.05629 / PMLR 54:1273-1282

## Source code
- **Official repo**: Standard Flower `flwr.server.strategy.FedAvg`
- **Commit/tag**: Flower 1.38.0
- **License**: Apache-2.0
- **Access date**: 2026-09-25

## Defining components
- Plain Federated Averaging using sample-count weighted parameter averaging:
  $$w_{t+1} = \sum_{k=1}^K \frac{n_k}{N} w_{t+1}^k$$
- No cryptographic provenance validation, no outlier trimming, and no byzantine filtering.

## Original datasets and task
- MNIST, CIFAR-10, Shakespeare (adapted to Network Intrusion Detection).

## Original preprocessing
- Dataset-specific (Z-score standard scaling on our tabular NIDS).

## Original model
- Multi-layer CNN / 1D-CNN.

## Original FL/threat settings
- Non-adversarial assumption (no defense against model poisoning or sybil attacks).

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| Local Epochs | 2 | Section 3 |
| Client Fraction | 1.0 (Full participation) | Section 3 |
| Aggregation | Weighted by sample count $n_k$ | Equation 1 |
| Base Optimizer | AdamW / SGD | Section 3 |

## Missing/ambiguous details
- None. Standard textbook algorithm.

## Our implementation
- Implemented in `src/prorag_fl/baselines/fl_controls.py` via `prorag_fl.federated.strategies.create_fedavg_strategy`.

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| Domain | Vision / Text | IIoT Telemetry Flows | Research target application | Evaluates vulnerability of plain FedAvg on NIDS |

## Fidelity
`faithful_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b2_b3_b4_standard_fl_controls_smoke` and `test_federated_learning.py`.

## Allowed manuscript wording
"FedAvg corresponds to canonical federated averaging (McMahan et al., 2017) without model update provenance verification or Byzantine-robust aggregation."
