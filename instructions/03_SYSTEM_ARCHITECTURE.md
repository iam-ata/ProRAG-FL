# System Architecture and Module Boundaries

## Data plane
`DatasetAdapter → split manifest → train-only preprocessor → tensors → 1D-CNN`.

## FL plane
`local training → serialized update → digest → provenance envelope → verifier → eligible set → robust aggregation → new model/version`.

Blockchain never carries model tensors.

## Direct inference
`event → CNN → logits+128D embedding → calibration → Mahalanobis → gate → direct decision`.

## Escalated inference
`gate=1 → SecurityEvent → query → BGE-M3/Qdrant hybrid retrieval → RRF → hard provenance/Merkle verification → verified Top-5 → OpenAI structured reasoning`.

## Knowledge ingestion
`source adapter → normalize/canonicalize → deterministic chunking → Merkle tree → MinIO → ledger root → BGE-M3 → Qdrant`.

## Threat-memory admission
`incident → sanitize → verify support → 2-of-3 endorsement → canonical version → Merkle anchor → index`.

## Required abstractions

### DatasetAdapter
Implementations: CICIoT2023, Edge-IIoTset.

### ProvenanceBackend
Methods include register/verify update, register/get/revoke document version, endorsements/admission. Implement mock and Fabric backends.

### ObjectStore
Local test + MinIO.

### VectorStore
In-memory test + Qdrant.

### ReasoningClient
Mock + OpenAI.

### FLStrategy
FedAvg, MultiKrum, FedTrimmedAvg, ProvenanceGatedFedTrimmedAvg.

## Dependency direction
Core schemas should not import infrastructure SDKs. Prefer:

```text
schemas ← domain services ← infrastructure adapters ← CLI/orchestration
```

This keeps tests independent of Fabric/Qdrant/OpenAI availability.
