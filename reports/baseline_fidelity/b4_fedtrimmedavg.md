# Baseline Fidelity Card — B4 FedTrimmedAvg

## Citation
- **Title**: Byzantine-Robust Distributed Learning: Towards Optimal Statistical Rates
- **Authors**: Dong Yin, Yudong Chen, Ramchandran Kannan, Peter L. Bartlett
- **Venue**: ICML
- **Year**: 2018
- **DOI**: arXiv:1803.01498 / PMLR 80:5650-5659

## Source code
- **Official repo**: Custom exact implementation in `prorag_fl.federated.strategies.FedTrimmedAvg`
- **Commit/tag**: `HEAD` (Phase 4)
- **License**: MIT
- **Access date**: 2026-09-25

## Defining components
- Coordinate-wise trimmed average across client model update vectors.
- For each parameter index $j$, sort values $\{w_{k, j}\}_{k=1}^K$, remove the $\lfloor \beta K \rfloor$ lowest and highest values, and average the remainder:
  $$\text{TrimmedMean}_j = \frac{1}{K - 2\lfloor \beta K \rfloor} \sum_{k = \lfloor \beta K \rfloor + 1}^{K - \lfloor \beta K \rfloor} w_{(k), j}$$
- Primary trimming fraction: $\beta = 0.20$.
- Operates strictly without blockchain identity checks or cryptographic provenance envelopes.

## Original datasets and task
- Theoretical and empirical distributed learning bounds.

## Original preprocessing
- Coordinate-wise sorting and trimming.

## Original model
- Applied to all learnable weight and bias parameters of the model.

## Original FL/threat settings
- Tolerates up to $\beta < 0.5$ Byzantine client fraction.

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| Trimming parameter $\beta$ | 0.20 | Section 2 |
| Feasibility condition | $K - 2\lfloor \beta K \rfloor \ge 1$ | Section 2 |
| Coordinate treatment | Element-wise independent sorting | Equation 2 |

## Missing/ambiguous details
- Handling of ties: Standard stable sort.

## Our implementation
- Fully implemented in `src/prorag_fl/federated/strategies.py` and wrapped in `src/prorag_fl/baselines/fl_controls.py`.

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| Provenance Gating | None | None | Baseline control definition | Isolates the exact benefit of blockchain gating |

## Fidelity
`faithful_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b2_b3_b4_standard_fl_controls_smoke` and `test_federated_learning.py`.

## Allowed manuscript wording
"FedTrimmedAvg implements coordinate-wise trimmed mean aggregation (Yin et al., 2018) with trimming fraction beta=0.20, serving as an un-gated statistical robustness control."
