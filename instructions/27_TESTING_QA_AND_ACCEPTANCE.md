# Testing, QA, and Acceptance

## Unit tests
Cover config, seeds, splits, transforms, model shapes, calibration, Mahalanobis, aggregators, update hashing, replay logic, Merkle tree/proof, RRF, hard filtering, sanitizer, structured parser and metrics.

## Integration tests
- processed batch -> model training;
- 3-client FL/2 rounds;
- mock + real Fabric provenance;
- MinIO -> chunk -> root -> Qdrant -> retrieve -> verify;
- verified retrieval -> mock reasoning;
- full direct/escalated path.

## Regression fixtures
Keep small deterministic fixtures for label map, feature order, config hash, Merkle root, RRF ranking and metric calculations.

## Required gates
### Data
No overlap/leakage; complete manifests.
### Model
Tiny-batch overfit; checkpoint/determinism.
### FL
All control strategies smoke.
### Blockchain
Tamper/replay/version/identity tests.
### RAG
Invalid evidence cannot reach final Top-5.
### Reasoning
Forbidden fields cannot serialize; invalid outputs fail validation.
### Baselines
Fidelity card exists before final run.
### Final matrix
Fixed seeds/configs; immutable artifacts.

## CI
Fast unit/smoke/lint on each meaningful commit. Mark heavy GPU/Fabric/service tests separately.
