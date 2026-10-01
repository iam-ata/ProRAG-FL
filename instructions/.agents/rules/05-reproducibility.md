---
trigger: model_decision
description: "Apply to model training, experiments, baselines, attacks, metrics, timings, and result aggregation."
---
# Reproducibility
Every run saves: run_id, git commit, timestamp, OS/Python/CUDA/GPU/CPU/RAM, dependency snapshot, dataset-manifest hash, resolved config, config hash, seed, logs, raw metrics, timings, checkpoint refs, artifact manifest.
Use seeds 13, 37, 73, 101, 211. Aggregate only intended completed seeds or explicitly documented failures.
Report per-seed values plus mean/std. Do not cherry-pick.
Time preprocessing, retrieval, provenance, API, parsing, and total latency separately.
