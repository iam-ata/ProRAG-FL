---
name: final-reproducibility-audit
description: Phase 17 — Perform final research reproducibility and traceability audit
---

# Phase 17 — Perform final research reproducibility and traceability audit

## Required reading

- `27_TESTING_QA_AND_ACCEPTANCE.md`
- `30_FINAL_REPRODUCIBILITY_CHECKLIST.md`
- `34_MANUSCRIPT_TO_CODE_TRACEABILITY.md`
- `36_PHASE_ACCEPTANCE_GATES.md`

## Execution contract

Run the complete unit/integration/smoke/regression suite, verify environment/data/config/checkpoint/result hashes, verify every manuscript method component maps to code/tests/results, confirm baseline fidelity cards, inspect result traceability and ensure no forbidden claims or test leakage remain. Produce a final audit report rather than silently fixing scientific discrepancies.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
