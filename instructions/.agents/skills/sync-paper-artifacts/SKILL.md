---
name: sync-paper-artifacts
description: Phase 16 — Export verified IEEE tables/figures and synchronize manuscript artifacts
---

# Phase 16 — Export verified IEEE tables/figures and synchronize manuscript artifacts

## Required reading

- `26_RESULTS_PIPELINE_AND_PAPER_SYNC.md`
- `34_MANUSCRIPT_TO_CODE_TRACEABILITY.md`
- `01_MASTER_AGENT_CONTRACT.md`

## Execution contract

Generate LaTeX tables, publication figures and claims.json under Code/reports/paper_exports from verified results only. Do not auto-rewrite manuscript narrative. Copy artifacts to the sibling Manuscript directory only after explicit researcher approval. Quantitative abstract/conclusion claims must trace to run IDs.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
