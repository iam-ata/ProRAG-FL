# Baseline Fidelity Card — B9 LQB-IDS

## Citation
- **Title**: An adaptive intrusion detection system for the internet of things using large language models and post-quantum-secure blockchain
- **Authors**: Huang et al.
- **Venue**: Computer Networks
- **Year**: 2026
- **DOI**: 10.1016/j.comnet.2025.111819

## Source code
- **Official repo**: Not publicly hosted; reimplemented as an approximate literature comparator.
- **Commit/tag**: `HEAD` (Phase 10)
- **License**: N/A
- **Access date**: 2026-09-25

## Defining components
- Deep Convolutional Autoencoder (`DCAEModel`) computing reconstruction error $\mathcal{E}(x) = \|x - \hat{x}\|_2^2$.
- Dual-Switch Routing (`DualSwitchController`): Low reconstruction error routes to lightweight known-attack classifier; high reconstruction error routes to anomaly/LLM analyzer.
- Credit-scoring reputation adaptation (`CreditScoreManager`).

## Original datasets and task
- IoT network intrusion detection with known vs zero-day attack separation.

## Original preprocessing
- Autoencoder reconstruction scaling.

## Original model
- DCAE + known-attack classifier.

## Original FL/threat settings
- Adaptive learning with post-quantum blockchain ledger.

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| Autoencoder Bottleneck | 16 | Section 3 |
| Switch Threshold | Empirical benign 95th percentile | Section 4 |
| Credit score bounds | [0.0, 200.0] | Section 3-C |

## Missing/ambiguous details
- Specific post-quantum lattice-based signature scheme parameters (abstracted via credit manager and SHA-256 state tracking).

## Our implementation
- Implemented in `src/prorag_fl/baselines/lqb_ids.py` (`DCAEModel`, `DualSwitchController`, `CreditScoreManager`, `LQBIDSBaseline`).

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| Post-quantum ledger | Lattice crypto blockchain | Credit manager simulation | Infeasible external C++ dependencies | Focuses comparison on dual-switch detection performance |

## Fidelity
`approximate_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b9_lqb_ids_dual_switch_and_smoke`.
- DCAE reconstruction error threshold calibration and dual-switch routing validated.

## Allowed manuscript wording
"LQB-IDS is evaluated as an approximate comparator (Computer Networks, 2026), capturing its DCAE dual-switch routing between a fast known-pattern classifier and an unknown anomaly path with node credit scoring."
