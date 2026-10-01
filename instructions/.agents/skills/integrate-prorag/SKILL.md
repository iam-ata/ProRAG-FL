---
name: integrate-prorag
description: Phase 9 — Integrate the complete ProRAG-FL runtime pipeline
---

# Phase 9 — Integrate the complete ProRAG-FL runtime pipeline

## Required reading

- `17_END_TO_END_PIPELINE.md`
- `03_SYSTEM_ARCHITECTURE.md`
- `34_MANUSCRIPT_TO_CODE_TRACEABILITY.md`

## Execution contract

Connect classifier, calibration, OOD gate, direct path, sanitizer, retrieval/provenance, Top-5 evidence and reasoning. Also integrate FL update provenance before FedTrimmedAvg. Build auditable decision records. Prove direct high-confidence events do not call RAG/API and provenance-invalid evidence never reaches reasoning.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
