# Phase 4 — Federated Learning

Framework: Flower.

## Client workflow
1. receive global model + model version + round;
2. load immutable client partition;
3. train 2 local epochs;
4. compute update;
5. record sample count/local metrics;
6. deterministically serialize update for digest;
7. create metadata/provenance envelope;
8. return update reference + metadata.

## Final settings
- primary K=10;
- scalability K=5,10,20;
- 50 rounds;
- IID + Dirichlet alpha 1.0/0.5/0.3/0.1.

## Strategies
### FedAvg
Sample-count weighted averaging.

### MultiKrum
Use a canonical/Flower-compatible implementation. Record Byzantine-count assumption, number selected, update-vs-weight convention, distance definition, and K constraints. Never tune Byzantine count on final test performance.

### FedTrimmedAvg
Coordinate-wise trimmed mean. Primary beta=0.20. Verify exactly how the chosen library converts beta to trimmed-client count for each K.

### ProvenanceGatedFedTrimmedAvg
1. verify each candidate's identity/hash/round/version/nonce/status;
2. log accept/reject + reason;
3. pass only accepted updates to the identical FedTrimmedAvg implementation.

No silent fallback to FedAvg if too few updates remain. Emit `INSUFFICIENT_ELIGIBLE_CLIENTS` and handle per experiment protocol.

## Versioning
Create deterministic global model/version identifiers bound to dataset/model/config/round.

## Communication accounting
Measure actual serialized bytes for model/update and metadata separately.

## Per-round log
participants, rejected/accepted, reasons, local metrics, aggregation time, global validation metric, bytes, checkpoint hash.

## Smoke
K=3, two rounds, tiny fixture for every strategy using mock provenance first.

## Fairness
Same split, partition, initial weights, participation schedule, local optimizer and evaluation pipeline unless a published baseline's defining method requires otherwise.
