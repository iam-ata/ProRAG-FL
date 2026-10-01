---
name: prepare-datasets
description: Phase 1 — Prepare CICIoT2023 and Edge-IIoTset without leakage
---

# Phase 1 — Prepare CICIoT2023 and Edge-IIoTset without leakage

## Required reading

- `08_DATASETS_AND_PREPROCESSING.md`
- `09_CLIENT_PARTITIONING.md`
- `03-data-leakage` rule
- `40_RUN_ARTIFACT_SCHEMA.md`

## Execution contract

Implement a common DatasetAdapter. Inspect the actual supplied dataset schema rather than assuming columns. Build raw SHA-256 manifests, label maps, immutable train/validation/test splits, train-only preprocessing, data-quality reports, IID and Dirichlet FL partitions, and held-out-family manifests. Do CICIoT2023 first, pass all checks, then Edge-IIoTset.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
