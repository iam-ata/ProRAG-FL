---
trigger: model_decision
description: Applies to experiment orchestration and generated results.
---

# Run Immutability

A resolved run config is immutable.

If any parameter changes, generate a new config hash/run ID.

Never edit metrics.json after completion to “correct” a number manually.

Corrections require rerunning the experiment or creating a derived analysis artifact with explicit provenance.

Failed runs remain visible. Retrying requires a new attempt record.
