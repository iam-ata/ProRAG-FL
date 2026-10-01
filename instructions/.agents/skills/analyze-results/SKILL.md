---
name: analyze-results
description: Phase 15 — Aggregate immutable runs and perform statistical analysis
---

# Phase 15 — Aggregate immutable runs and perform statistical analysis

## Required reading

- `19_METRICS_AND_STATISTICS.md`
- `26_RESULTS_PIPELINE_AND_PAPER_SYNC.md`
- `40_RUN_ARTIFACT_SCHEMA.md`

## Execution contract

Aggregate only DONE artifacts into master CSV/Parquet. Retain per-seed values, produce mean±SD and appropriate uncertainty/effect-size analysis, show failed/missing runs, generate plots/tables by script, and never hand-edit metrics. Avoid overclaiming significance with N=5.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
