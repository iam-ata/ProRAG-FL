---
trigger: always_on
description: Prevents silent drift from the frozen ProRAG-FL method.
---

# Locked Proposed Method

Read `02_LOCKED_PROPOSED_METHOD.md` before modifying core method code.

Do not silently change:
- datasets: CICIoT2023 and Edge-IIoTset evaluated separately;
- 1D-CNN channels: 64,128,256;
- embedding dimension: 128;
- dropout: 0.30;
- AdamW default lr 1e-3, weight decay 1e-4;
- Flower FL;
- primary K=10, scalability K=5/10/20;
- 50 rounds, 2 local epochs;
- Dirichlet alpha 1.0/0.5/0.3/0.1;
- proposed aggregation: hard model-provenance gate then FedTrimmedAvg beta=0.20;
- calibration: temperature scaling;
- OOD: Mahalanobis on 128-D representation;
- RAG only when confidence/OOD gate fires;
- MinIO + Qdrant + BGE-M3 + hybrid/RRF;
- hard knowledge provenance filter;
- candidate Top-20 and final verified Top-5;
- Hyperledger Fabric target;
- Merkle-root-on-chain/chunk-proof design;
- OpenAI structured reasoning with tools disabled in controlled experiments;
- Mirai and Malware held-out protocols.

Any method change requires explicit researcher approval and a documented manuscript/code update.
