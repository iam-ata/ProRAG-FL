# Docker and Infrastructure Setup

The Python research environment is Conda. Infrastructure is external/containerized.

## Prerequisites on Windows
- Docker Desktop with WSL2 backend recommended;
- Git;
- enough disk space for images/volumes;
- ports available or configurable.

Do not install Qdrant/MinIO/Fabric server packages into the Conda environment.

## Qdrant
Target local service:
- HTTP `6333`;
- gRPC `6334` if used;
- persistent Docker volume under a gitignored service-data directory.

Create `services/qdrant/docker-compose.yml` during implementation. Add a health-check script and CLI `prorag service qdrant doctor` or equivalent.

Acceptance:
- create collection;
- insert test dense+sparse point;
- query it;
- delete/reset test collection;
- persistence survives container restart.

## MinIO
Target local object-store service with separate API and console ports. Credentials come from `.env`; never embed defaults in committed production configs.

Create buckets for:
- canonical CTI;
- optional experiment artifacts if used.

Acceptance:
- upload versioned object;
- retrieve and verify SHA-256;
- confirm immutable/versioned key policy;
- unauthorized/no-credential access fails.

## Hyperledger Fabric
Prefer official Fabric binaries/images/test-network tooling matching the targeted 2.5 LTS family. On Windows use WSL2/Linux tooling if the native workflow is unreliable.

Create `services/fabric/` containing:
- documented bootstrap script;
- start/stop/reset;
- chaincode source;
- gateway bridge if required;
- test identities/config;
- integration-test helpers.

Final target topology is 3 orgs/3 peers and 3 Raft orderers. A reduced network is allowed only for developer smoke and must be labeled.

## Service profiles
Support at least:
- `mock`: no external services;
- `dev`: local Qdrant/MinIO + optional reduced Fabric;
- `integration`: real target-compatible services;
- `final`: frozen experiment topology.

## Health command
`prorag doctor` should report Python/GPU plus Qdrant, MinIO and Fabric connectivity separately, without exposing secrets.
