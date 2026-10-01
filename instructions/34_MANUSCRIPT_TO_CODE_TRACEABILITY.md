# Manuscript-to-Code Traceability

| Method concept | Code area | Evidence artifact |
|---|---|---|
| 1D-CNN | `models/` | model cards/checkpoints |
| FL | `federated/` | round logs |
| update provenance | `provenance/` | verification events |
| Fabric | `blockchain/` + services | transaction logs |
| calibration | `calibration/` | T/ECE report |
| OOD | `ood/` | means/cov/threshold |
| sanitized event | `schemas/`/`reasoning/` | payload schema |
| CTI ingest | `knowledge/` | source manifests |
| Merkle | `provenance/` | roots/proofs/tests |
| BGE/Qdrant | `rag/` | index/retrieval logs |
| hard evidence gate | `rag/` + `provenance/` | reject reasons |
| OpenAI | `reasoning/` | structured outputs |
| threat memory | `threat_memory/` | endorsements/admission |
| FL attacks | `attacks/fl/` | attack configs |
| RAG attacks | `attacks/rag/` | poison manifests |
| metrics | `evaluation/` | `metrics.json` |
| paper outputs | `reporting/` | generated exports |

Before submission, map each important method equation/algorithm to concrete code path, test and result artifact where applicable.
