# Baseline Fidelity Card — B6 FLOW

## Citation
- **Title**: FLOW: A Robust Federated Learning Framework to Defend Against Model Poisoning Attacks in IoT
- **Authors**: IEEE Internet of Things Journal
- **Venue**: IEEE Internet of Things Journal
- **Year**: 2024
- **DOI**: 10.1109/JIOT.2023.3341811

## Source code
- **Official repo**: Not publicly hosted; faithful reimplementation from published equations and algorithm.
- **Commit/tag**: `HEAD` (Phase 10)
- **License**: N/A
- **Access date**: 2026-09-25

## Defining components
- Pairwise cosine-distance matrix computation across flattened client model update vectors:
  $$D_{ij} = 1 - \frac{u_i \cdot u_j}{\|u_i\|_2 \|u_j\|_2}, \quad \bar{D}_i = \frac{1}{K-1} \sum_{j \neq i} D_{ij}$$
- Dynamic anomaly detection thresholding identifying malicious/poisonous updates.
- Historical client state tracking (`FlowHistoryState`) with graceful punishment rather than permanent exclusion:
  - If malicious: increases penalty factor $p_i \leftarrow \min(1.0, p_i + \text{rate})$.
  - If benign: grants linear recovery credit $p_i \leftarrow \max(0.0, p_i - \text{recovery})$.
- Adaptive aggregation discount: $w_i \propto n_i \cdot (1 - p_i)$.

## Original datasets and task
- IoT network traffic classification under targeted model poisoning attacks.

## Original preprocessing
- Model parameter vector flattening and L2 normalization.

## Original model
- Applied to generic IoT neural network classifiers (our IDS 1D-CNN).

## Original FL/threat settings
- Model poisoning, sign-flipping, and targeted backdoor attacks.

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| Metric | Pairwise cosine distance | Section IV-A |
| Anomaly threshold | Mean + 1.5 Std | Section IV-B |
| Penalty rate | 0.5 per malicious round | Section IV-C |
| Recovery rate | 0.2 per benign round | Section IV-C |

## Missing/ambiguous details
- Exact cluster linkage algorithm (centroid vs mean pairwise distance; mean distance used for robust symmetry).

## Our implementation
- Fully implemented in `src/prorag_fl/baselines/flow.py` (`FlowHistoryState`, `FlowDetector`, `FlowAggregator`, `FlowBaseline`).

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| Architecture | Multi-layer IoT perceptron | Standard IDS 1D-CNN | Experimental control fairness | Direct comparison of poisoning defense efficacy |

## Fidelity
`faithful_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b6_flow_cosine_defense_and_smoke`.
- Opposite-direction sign flipping attack detected and suppressed.
- Graceful recovery mechanism validated.

## Allowed manuscript wording
"FLOW is faithfully reimplemented from its defining protocol (IEEE JIOT, 2024), utilizing pairwise cosine-distance update analysis and graceful historical punishment to mitigate model poisoning attacks."
