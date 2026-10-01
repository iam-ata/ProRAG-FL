---
name: train-local-ids
description: Phase 2 — Implement local and centralized 1D-CNN IDS
---

# Phase 2 — Implement local and centralized 1D-CNN IDS

## Required reading

- `02_LOCKED_PROPOSED_METHOD.md`
- `10_LOCAL_IDS_1DCNN.md`
- `19_METRICS_AND_STATISTICS.md`

## Execution contract

Implement the frozen PyTorch 1D-CNN exactly, returning logits and the 128-D embedding. Add train/eval/checkpoint loops, class weighting from training only, centralized and local controls, model card, tiny-batch overfit, gradient, deterministic inference and checkpoint round-trip tests. Do not start FL.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
