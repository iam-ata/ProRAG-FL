# Baseline Fidelity Card — B0 Local 1D-CNN

## Citation
- **Title**: Local Independent 1D-CNN Baseline Control (No Collaboration)
- **Authors**: Antigravity Research Team / Standard NIDS Control
- **Venue**: Internal Control Benchmark
- **Year**: 2026
- **DOI**: N/A (Standard Baseline Control)

## Source code
- **Official repo**: Internal project repository (`prorag_fl.baselines.local_ids`)
- **Commit/tag**: `HEAD` (Phase 10)
- **License**: MIT
- **Access date**: 2026-09-25

## Defining components
- Independent local training on immutable client partitions.
- No model parameter aggregation, consensus, or federated exchange.
- Serves as the lower-bound isolation baseline evaluating the benefit of collaborative federation.

## Original datasets and task
- Task: Multi-class and binary Network Intrusion Detection (NIDS).
- Datasets: Edge-IIoTset (15-class), CIC-IoT-2023 (8-class).

## Original preprocessing
- Train-only fitted `TabularPreprocessor` (Z-score standard scaling + robust quantile clipping).

## Original model
- Architecture: 3-block 1D-CNN with Conv1D, BatchNorm1d, ReLU, Dropout (0.2), GlobalAveragePooling1d, 128-D bottleneck representation, and linear classification head.

## Original FL/threat settings
- Zero collaboration, zero communication bytes, no threat defense mechanisms required.

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| Model Architecture | IDS1DCNN (Conv1D 64->128->256) | Section IV-B |
| Optimizer | AdamW | Section IV-B |
| Learning Rate | 0.001 | Section IV-B |
| Weight Decay | 0.0001 | Section IV-B |
| Local Epochs | 5 | Section IV-B |
| Batch Size | 128 | Section IV-B |

## Missing/ambiguous details
- None.

## Our implementation
- Fully implemented in `src/prorag_fl/baselines/local_ids.py` (`Local1DCNNBaseline`).

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| Aggregation | None | None | Consistent control definition | No deviation |

## Fidelity
`faithful_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b0_local_1dcnn_smoke`.
- Zero communication bytes asserted.
- Independent per-client model state verified.

## Allowed manuscript wording
"Local 1D-CNN represents an isolated baseline where each edge client trains an identical 1D-CNN architecture strictly on its local partition without parameter sharing or cross-node collaboration."
