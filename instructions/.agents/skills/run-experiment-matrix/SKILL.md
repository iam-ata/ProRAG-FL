---
name: run-experiment-matrix
description: Phase 12 — Execute the frozen experiment matrix reproducibly
---

# Phase 12 — Execute the frozen experiment matrix reproducibly

## Required reading

- `23_EXPERIMENT_MATRIX.md`
- `28_CONFIG_AND_CLI_CONTRACT.md`
- `40_RUN_ARTIFACT_SCHEMA.md`
- `41_FULL_MATRIX_PLANNING_AND_COST_CONTROL.md`

## Execution contract

Expand YAML matrices into immutable run configs. Before full execution, report run count, service requirements, expected GPU/storage/API use, then run smoke and one-seed pilot tiers. Freeze configs before five-seed final runs. Support resume/skip-complete/retry-failed without overwriting artifacts.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
