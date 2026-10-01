---
trigger: model_decision
description: Applies when implementing or evaluating any published baseline.
---

# Baseline Fidelity

Before coding a published baseline:
1. create a fidelity card under `Code/reports/baseline_fidelity/`;
2. identify full citation/DOI;
3. locate official code if available;
4. pin commit/tag if used;
5. inspect license;
6. extract exact method-defining equations and parameters from full paper/code;
7. list missing details and assumptions;
8. classify fidelity.

Do not implement a paper from abstract-level summaries alone.

Do not replace a baseline's defining architecture with the ProRAG-FL 1D-CNN merely for convenience.

If a baseline does not support a metric/task, report `N/A`; do not invent an equivalent.
