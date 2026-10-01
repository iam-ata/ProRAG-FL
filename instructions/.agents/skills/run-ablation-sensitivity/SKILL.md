---
name: run-ablation-sensitivity
description: Phase 13 — Run the frozen ablation ladder and validation-only sensitivity analysis
---

# Phase 13 — Run the frozen ablation ladder and validation-only sensitivity analysis

## Required reading

- `24_ABLATION_AND_SENSITIVITY.md`
- `02_LOCKED_PROPOSED_METHOD.md`
- `19_METRICS_AND_STATISTICS.md`

## Execution contract

Implement A0–A6 exactly and run sensitivity sweeps for beta, confidence threshold, Mahalanobis threshold, Top-K and retrieval weights using validation only. Persist a frozen-parameters artifact and make final-test scripts reject tuning options.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
