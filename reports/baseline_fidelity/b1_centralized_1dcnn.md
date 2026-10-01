# Baseline Fidelity Card — B1 Centralized 1D-CNN

## Citation
- **Title**: Centralized 1D-CNN Oracle Reference
- **Authors**: Antigravity Research Team / Standard Centralized Oracle
- **Venue**: Internal Control Benchmark
- **Year**: 2026
- **DOI**: N/A (Standard Oracle Reference)

## Source code
- **Official repo**: Internal project repository (`prorag_fl.baselines.centralized_ids`)
- **Commit/tag**: `HEAD` (Phase 10)
- **License**: MIT
- **Access date**: 2026-09-25

## Defining components
- Pooled training on the union of all client training partitions.
- Serves as the oracle upper-bound reference evaluating performance when data centralization is unconstrained by privacy boundaries.
- Uses identical architecture, preprocessor, and validation/test splits.

## Original datasets and task
- Task: Multi-class Network Intrusion Detection (NIDS).
- Datasets: Edge-IIoTset, CIC-IoT-2023.

## Original preprocessing
- Train-only fitted `TabularPreprocessor`.

## Original model
- Locked 1D-CNN (`IDS1DCNN`).

## Original FL/threat settings
- Centralized server training. Zero federated communication overhead.

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| Model Architecture | IDS1DCNN (Conv1D 64->128->256) | Section IV-B |
| Optimizer | AdamW | Section IV-B |
| Learning Rate | 0.001 | Section IV-B |
| Weight Decay | 0.0001 | Section IV-B |
| Epochs | 10 | Section IV-B |
| Batch Size | 128 | Section IV-B |

## Missing/ambiguous details
- None.

## Our implementation
- Implemented in `src/prorag_fl/baselines/centralized_ids.py` (`Centralized1DCNNBaseline`).

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| Data Pooling | Union of clients | Union of clients | Oracle definition | True centralized empirical ceiling |

## Fidelity
`faithful_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b1_centralized_1dcnn_smoke`.
- Zero communication bytes asserted.

## Allowed manuscript wording
"Centralized 1D-CNN provides an empirical upper bound (oracle performance ceiling) by training on the unpartitioned pooled union of all client training datasets under the identical model architecture and feature preprocessing pipeline."
