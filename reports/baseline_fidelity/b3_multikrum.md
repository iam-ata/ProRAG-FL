# Baseline Fidelity Card — B3 MultiKrum

## Citation
- **Title**: Machine Learning with Adversaries: Byzantine Tolerant Gradient Descent
- **Authors**: Peva Blanchard, El Mahdi El Mhamdi, Rachid Guerraoui, Julien Stainer
- **Venue**: NeurIPS
- **Year**: 2017
- **DOI**: arXiv:1703.02757 / NeurIPS 2017

## Source code
- **Official repo**: Standard Flower `flwr.server.strategy.Krum` with `num_to_keep > 1`
- **Commit/tag**: Flower 1.38.0
- **License**: Apache-2.0
- **Access date**: 2026-09-25

## Defining components
- Pairwise Euclidean distance computation across client updates:
  $$s(i) = \sum_{j \in \mathcal{N}_{n - f - 2}(i)} \|w_i - w_j\|_2^2$$
- Selects the $m$ updates with lowest distance sum scores and computes their coordinate-wise arithmetic average.
- Byzantine fault tolerance bound: $2f + 2 < n$.

## Original datasets and task
- Distributed SGD benchmark tasks.

## Original preprocessing
- Standard coordinate flattening.

## Original model
- Applied to arbitrary feedforward / convolutional network parameters.

## Original FL/threat settings
- Byzantine adversary model: malicious clients may send arbitrarily corrupted model weights.

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| num_byzantine ($f$) | 1 (in smoke) / $\lfloor 0.2 \cdot K \rfloor$ (in scale) | Section 3 |
| num_to_keep ($m$) | $K - f$ | Section 4 |
| Metric | Squared Euclidean $L_2$ distance | Equation 1 |

## Missing/ambiguous details
- MultiKrum scoring evaluates parameter updates $\Delta w$ relative to previous global round.

## Our implementation
- Implemented in `src/prorag_fl/baselines/fl_controls.py` via `prorag_fl.federated.strategies.create_multikrum_strategy`.

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| Domain | Image classification | Tabular NIDS | Application domain | Standard benchmark comparator |

## Fidelity
`faithful_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b2_b3_b4_standard_fl_controls_smoke` and `test_federated_learning.py`.

## Allowed manuscript wording
"MultiKrum represents canonical Byzantine-robust aggregation (Blanchard et al., 2017) selecting the subset of client model updates that minimize Euclidean distance sums to nearest neighbors."
