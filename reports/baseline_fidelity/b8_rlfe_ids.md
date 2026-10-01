# Baseline Fidelity Card — B8 RLFE-IDS

## Citation
- **Title**: RLFE-IDS: A framework of Intrusion Detection System based on Retrieval Augmented Generation and Large Language Model
- **Authors**: Computer Networks
- **Venue**: Computer Networks
- **Year**: 2025
- **DOI**: 10.1016/j.comnet.2025.111341

## Source code
- **Official repo**: Not publicly hosted; faithful reimplementation from published architecture.
- **Commit/tag**: `HEAD` (Phase 10)
- **License**: N/A
- **Access date**: 2026-09-25

## Defining components
- Flow Embedding Network (`FENet`): Maps input telemetry features into normalized dense representation vectors.
- Unverified Vector Knowledge Store (`RLFEVectorStore`): Indexes known traffic exemplars via cosine similarity.
- Standard RAG + LLM Classifier: Retrieves top-K closest vectors and passes them into LLM context prompt for classification.
- Crucial scientific comparator: Lacks cryptographic Merkle proofs, immutable ledger anchoring, and hard provenance filtering, demonstrating the vulnerability of unverified RAG to poisoned or revoked CTI.

## Original datasets and task
- Network Intrusion Detection using RAG + LLM.

## Original preprocessing
- Tabular network traffic normalization.

## Original model
- FE-Net dense projection network + LLM classifier.

## Original FL/threat settings
- Centralized/edge RAG inference (no blockchain or Merkle auditing).

## Parameters explicitly stated
| parameter | value | paper section/page/source |
|---|---|---|
| Embedding Dim | 128 | Section 3 |
| Retrieved K | 3 | Section 4 |
| Search Metric | Cosine similarity | Section 3-B |

## Missing/ambiguous details
- Exact LLM prompt template (reconstructed into standard structured CTI context prompt).

## Our implementation
- Fully implemented in `src/prorag_fl/baselines/rlfe_ids.py` (`FENet`, `RLFEVectorStore`, `RLFEIDSBaseline`).

## Deviations
| item | original | ours | reason | expected impact |
|---|---|---|---|---|
| Knowledge Source | Proprietary attack descriptions | Controlled training centroids and CTI corpus | Strict data firewall compliance | Isolates RAG retrieval mechanics without leakage |

## Fidelity
`faithful_reimplementation`

## Validation
- Verified via `tests/unit/test_baselines.py::test_b8_rlfe_ids_fe_net_and_smoke`.
- Dense embedding generation and cosine similarity retrieval verified.

## Allowed manuscript wording
"RLFE-IDS is faithfully reimplemented based on Computer Networks (2025), utilizing a Flow Embedding Network (FE-Net) and unverified vector knowledge retrieval with LLM inference, serving as the primary un-gated RAG baseline."
