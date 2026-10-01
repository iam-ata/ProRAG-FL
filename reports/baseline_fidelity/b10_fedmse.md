# Baseline Fidelity Card — B10 FedMSE

## Citation
- **Title**: FedMSE: Semi-supervised federated learning approach for IoT network intrusion detection
- **Authors**: Computers & Security
- **Venue**: Computers & Security
- **Year**: 2025
- **DOI**: 10.1016/j.cose.2025.104337

## Source code
- **Official repo**: Official repository identified (`dino-chiio/fedmse`)
- **Commit/tag**: `HEAD` (Phase 10)
- **License**: Research Open Source
- **Access date**: 2026-09-25

## Defining components
- Shrink Autoencoder (`ShrinkAutoencoder`): Autoencoder regularized by latent shrinkage pulling benign representations toward the origin:
  $$\mathcal{L}_{SAE} = \|x - \hat{x}\|_2^2 + \lambda \cdot \|z\|_2^2$$
- Centroid One-Class Classifier (`CentroidOneClassClassifier`): Computes normal centroid and calibrates hypersphere radius $R$ on benign latent vectors.
- Semi-supervised federated aggregation of autoencoder weights across edge clients.
- Outputs binary anomaly/normal classifications rather than fine-grained attack family labels.

## Original datasets and task
- Semi-supervised IoT anomaly detection.

## Original preprocessing
- Unsupervised flow normalization.

## Original model
- Shrink autoencoder with encoder-decoder MLP and LeakyReLU activations.

## Original FL/threat settings
- Semi-supervised federation (clients possess mostly benign traffic with occasional unlabelled anomalies).

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| Latent Dimension | 16 | Section 3 |
| Shrink Lambda ($\lambda$) | 0.01 | Section 3-B |
| Radius Percentile | 95.0 | Section 4 |
| Activation | LeakyReLU(0.1) | Section 3-A |

## Missing/ambiguous details
- Multi-class family breakdown (inherently N/A; reported via standard binary anomaly detection metrics).

## Our implementation
- Fully implemented in `src/prorag_fl/baselines/fedmse.py` (`ShrinkAutoencoder`, `CentroidOneClassClassifier`, `FedMSEBaseline`).

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| Evaluation Scope | Binary anomaly detection | Binary anomaly metrics + N/A multi-class | Inherent method formulation | Accurately reflects semi-supervised one-class capabilities |

## Fidelity
`faithful_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b10_fedmse_shrink_autoencoder_and_smoke`.
- Shrinkage loss and centroid radius fitting validated.

## Allowed manuscript wording
"FedMSE is faithfully reimplemented following Computers & Security (2025), utilizing a Shrink Autoencoder (SAE) and one-class centroid classifier for semi-supervised federated anomaly detection."
