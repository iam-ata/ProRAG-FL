---
name: build-blockchain-provenance
description: Implements Hyperledger Fabric 2.5 model-update and knowledge provenance registries, Merkle verification, replay/version protection, and 2-of-3 incident endorsement.
---
# Fabric Provenance
Create reproducible 3-org/3-peer/3-Raft dev network and one app channel. ModelUpdateRegistry operations: register/get/status/replay/query-round. Knowledge registry: register version/revoke/get active/endorse/check admission. Blockchain stores metadata only. Python adapter has mock and Fabric backends. Integration tests: tampered hash, stale round, wrong version, duplicate nonce, unknown client, modified chunk, revoked document, insufficient endorsement, 2-of-3 success.
