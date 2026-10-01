---
trigger: model_decision
description: Applies to training, experiments, attacks, benchmarks, metrics and result generation.
---

# Reproducibility

Primary seeds: `13,37,73,101,211`.

Every run stores:
- run ID;
- Git commit;
- resolved config + hash;
- dataset/split/partition manifest hashes;
- seed;
- environment snapshot;
- hardware;
- logs;
- metrics;
- timings;
- artifact manifest;
- DONE/FAILED state.

Do not overwrite runs.

Use a common metrics implementation across methods when definitions permit.

Aggregate only completed immutable runs.

Report mean ± standard deviation over fixed seeds, with per-seed raw values retained.
