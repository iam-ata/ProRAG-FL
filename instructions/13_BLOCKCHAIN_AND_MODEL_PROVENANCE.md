# Phase 5 — Hyperledger Fabric and Model-Update Provenance

## Scope
Fabric stores compact provenance/audit metadata, never tensors/raw traffic/full CTI.

## Target topology
- Org1/Peer1;
- Org2/Peer2;
- Org3/Peer3;
- three Raft orderers;
- application channel;
- MSP/CA identity management as appropriate.

A reduced dev network may be used for smoke only and must never supply final topology-overhead numbers.

## ModelUpdateRegistry record
Suggested fields:
```text
update_id
client_id
round
global_model_version
update_sha256
timestamp
nonce
status
submitter_identity
```

## Verification order
1. schema;
2. authenticated/authorized identity;
3. active lifecycle status;
4. digest match;
5. exact round;
6. exact global-model version;
7. nonce not consumed;
8. time policy if enabled;
9. atomically consume/record replay state.

Replay check must be transaction-safe; avoid a non-atomic check-then-write race.

## Integration architecture
Core Python depends on `ProvenanceBackend`. Implement mock and Fabric backends. If the best-supported Fabric Gateway SDK is not Python-native, use a small containerized gateway service with a typed Python HTTP/gRPC client rather than choosing an abandoned SDK solely for Python purity.

## Digest
Hash exact canonical serialized update artifact. Store the full update off-chain under a content-addressed reference.

## Required integration attacks
| Scenario | Result |
|---|---|
| valid current update | accept |
| bytes changed after registration | reject |
| duplicate nonce | reject |
| round t-1 submitted at t | reject |
| wrong global version | reject |
| unknown/unauthorized identity | reject |
| revoked client | reject |

## Benchmark separately
Transaction submit/query/verification latency, throughput, transaction bytes, ledger growth. Keep blockchain time separate from ML aggregation time.
