---
name: implement-baselines
description: Phase 10 — Implement all controls and published baselines with fidelity tracking
---

# Phase 10 — Implement all controls and published baselines with fidelity tracking

## Required reading

- `20_BASELINES_MASTER.md`
- `21_BASELINE_IMPLEMENTATION_DETAILS.md`
- `22_BASELINE_FIDELITY_PROTOCOL.md`
- `37_BASELINE_SOURCE_NOTES.md`

## Execution contract

Implement B0–B4 controls first. For SFLNID, FLOW, Bc²FL, RLFE-IDS, LQB-IDS, FedMSE and pFL-IDS, create a fidelity card before code, inspect full paper and official repository where available, pin versions, preserve defining architecture/algorithm, document deviations, and expose all methods through the common experiment/metric interface. If details are insufficient, mark approximate and stop rather than inventing formulas.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
