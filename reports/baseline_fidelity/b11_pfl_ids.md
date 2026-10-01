# Baseline Fidelity Card — B11 pFL-IDS

## Citation
- **Title**: Personalized federated learning-based intrusion detection system: Poisoning attack and defense
- **Authors**: Thein et al.
- **Venue**: Future Generation Computer Systems
- **Year**: 2024
- **DOI**: 10.1016/j.future.2023.10.005

## Source code
- **Official repo**: Not publicly hosted; faithful reimplementation from published equations and defense protocol.
- **Commit/tag**: `HEAD` (Phase 10)
- **License**: N/A
- **Access date**: 2026-09-25

## Defining components
- Mini-batch Logit-Adjusted Loss (`LogitAdjustedLoss`): Counters Non-IID client label distribution shifts by adjusting logits with class prior probabilities $\pi_y$:
  $$\mathcal{L}_{LA}(y, f(x)) = -\log \frac{\exp(f_y(x) + \tau \log \pi_y)}{\sum_j \exp(f_j(x) + \tau \log \pi_j)}$$
- Two-Phase Similarity Defense (`TwoPhaseSimilarityDefense`):
  - Phase 1: Directional Cosine Similarity filtering against consensus update direction (discards updates with negative cosine similarity).
  - Phase 2: Benign Centroid Distance defense (filters updates deviating significantly from the median absolute deviation of passed updates).
- Personalized Client Models: Keeps personalized local models for client-specific evaluation alongside global aggregation.

## Original datasets and task
- Personalized intrusion detection under non-IID partitions and targeted poisoning attacks.

## Original preprocessing
- Empirical class prior estimation and standard feature normalization.

## Original model
- Deep neural network for NIDS (our locked IDS 1D-CNN).

## Original FL/threat settings
- Non-IID Dirichlet distribution ($\alpha=0.3, 0.1$) with label-flipping and model replacement poisoning attacks.

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| Tau ($\tau$) | 1.0 | Section 3-B |
| Phase 1 threshold | 0.0 (non-negative cosine similarity) | Section 4-A |
| Phase 2 factor | 1.5 * MAD | Section 4-B |

## Missing/ambiguous details
- Exact construction of initial precomputed consensus direction (initialized using median update vector).

## Our implementation
- Fully implemented in `src/prorag_fl/baselines/pfl_ids.py` (`LogitAdjustedLoss`, `TwoPhaseSimilarityDefense`, `PFLIDSBaseline`).

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| Model Architecture | 4-layer MLP | Standard IDS 1D-CNN | Benchmark model consistency | Isolates logit-adjustment and defense mechanisms |

## Fidelity
`faithful_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b11_pfl_ids_defense_and_smoke`.
- Logit-adjustment loss computation and two-phase poison rejection validated.

## Allowed manuscript wording
"pFL-IDS is faithfully reimplemented based on Thein et al. (FGCS, 2024), featuring logit-adjusted loss for Non-IID class imbalance and a two-phase cosine-similarity/benign centroid defense against model poisoning."
