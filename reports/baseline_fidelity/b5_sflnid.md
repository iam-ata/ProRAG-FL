# Baseline Fidelity Card — B5 SFLNID

## Citation
- **Title**: Efficient and Privacy-Preserving Network Intrusion Detection Based on Federated Learning in SDN-Enabled IIoT Network
- **Authors**: IEEE Internet of Things Journal
- **Venue**: IEEE Internet of Things Journal
- **Year**: 2025
- **DOI**: 10.1109/JIOT.2025.3591598

## Source code
- **Official repo**: Not publicly hosted; faithful reimplementation from published equations and architecture.
- **Commit/tag**: `HEAD` (Phase 10)
- **License**: N/A
- **Access date**: 2026-09-25

## Defining components
- Native hybrid CNN-GRU architecture (`SFLNIDModel`) capturing spatial and temporal flow characteristics.
- Composite loss (`SFLNIDLoss`): Focal Loss to handle extreme class imbalance + Wasserstein distance regularization between local and global feature representations:
  $$\mathcal{L} = \mathcal{L}_{Focal} + \lambda_W \cdot W_1(P_{local}, P_{global})$$
- Adaptive Differential Privacy (`AdaptiveDPController`): Dynamic gradient clipping using Holt exponential smoothing to track gradient momentum:
  $$S_t = \alpha Y_t + (1 - \alpha)(S_{t-1} + b_{t-1}), \quad b_t = \beta (S_t - S_{t-1}) + (1 - \beta)b_{t-1}, \quad C_t = S_t + b_t$$
  combined with Gaussian DP noise addition.

## Original datasets and task
- SDN-enabled Industrial IoT intrusion detection.

## Original preprocessing
- Flow feature normalization.

## Original model
- Hybrid CNN-GRU with Conv1D layers followed by GRU recurrence and dense classification.

## Original FL/threat settings
- Non-IID client partition, adaptive differential privacy, focal class balancing.

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| Architecture | 2x Conv1d (64) -> MaxPool -> GRU (64) -> FC | Section III-A |
| Focal gamma | 2.0 | Section III-B |
| Wasserstein weight $\lambda_W$ | 0.05 | Section III-B |
| Holt alpha ($\alpha$) | 0.3 | Section III-C |
| Holt beta ($\beta$) | 0.1 | Section III-C |
| DP noise multiplier | 0.01 | Section III-C |

## Missing/ambiguous details
- Exact SDN flow table controller implementation (abstracted into standard network flow tensors).

## Our implementation
- Fully implemented in `src/prorag_fl/baselines/sflnid.py` (`SFLNIDModel`, `SFLNIDLoss`, `AdaptiveDPController`, `SFLNIDBaseline`).

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| SDN Controller | Physical OpenFlow SDN controller | Simulated edge client data loader | Reproducibility across standard datasets | Method algorithmic logic preserved without SDN hardware dependencies |

## Fidelity
`faithful_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b5_sflnid_components_and_smoke`.
- SFLNIDModel tensor shapes, Focal+Wasserstein loss convergence, and Holt dynamic clipping validated.

## Allowed manuscript wording
"SFLNID is faithfully reimplemented from its published specification (IEEE JIOT, 2025), incorporating its native CNN-GRU architecture, Focal loss with Wasserstein-distance distribution regularization, and Holt exponential smoothing adaptive differential privacy."
