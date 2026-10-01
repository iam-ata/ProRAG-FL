---
name: calibrate-ood
description: Phase 3 — Implement temperature calibration and Mahalanobis OOD gating
---

# Phase 3 — Implement temperature calibration and Mahalanobis OOD gating

## Required reading

- `11_CALIBRATION_AND_OOD.md`
- `02_LOCKED_PROPOSED_METHOD.md`
- `19_METRICS_AND_STATISTICS.md`

## Execution contract

Freeze classifier weights, fit temperature on validation logits only, compute ECE/NLL, fit class-conditional Mahalanobis statistics from known training embeddings only, select validation-only thresholds, serialize the gate, and prove held-out test families never enter fitting.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
