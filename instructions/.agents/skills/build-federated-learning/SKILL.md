---
name: build-federated-learning
description: Phase 4 — Implement Flower FL and robust aggregation controls
---

# Phase 4 — Implement Flower FL and robust aggregation controls

## Required reading

- `12_FEDERATED_LEARNING.md`
- `09_CLIENT_PARTITIONING.md`
- `02_LOCKED_PROPOSED_METHOD.md`

## Execution contract

Implement Flower clients/server and FedAvg, MultiKrum, FedTrimmedAvg(beta=0.20), plus the proposed provenance-gated FedTrimmedAvg using a mock ProvenanceBackend first. Ensure fair shared initial weights/client manifests and log per-round communication/aggregation metrics. Complete K=3, 2-round smoke tests before blockchain integration.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
