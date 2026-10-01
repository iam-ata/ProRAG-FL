# Phase Acceptance Gates — Quick Sheet

- **P0:** package imports; pytest/Ruff/doctor; secrets redacted.
- **P1:** raw hashes; split manifests; no overlap/leakage; train-only preprocessing; held-out proof.
- **P2:** shape/gradient/tiny-overfit/checkpoint/determinism/local-central smoke.
- **P3:** calibration/OOD finite; validation-only thresholds; serialization.
- **P4:** 3-client/2-round smoke all control strategies; shared partition/init; bytes logged.
- **P5:** valid accept; tamper/replay/stale/version/identity reject.
- **P6:** deterministic chunks/root; tampered proof fails; version/revocation works.
- **P7:** dense+sparse/RRF/hard gate/verified Top-5 + retrieval benchmark.
- **P8:** mock/schema/forbidden-field/evidence-ID tests; real API behind flag.
- **P9:** direct path no API; escalated only verified evidence; audit record.
- **P10:** fidelity card and smoke for every measured baseline.
- **P11:** attacks have positive controls and frozen configs.
- **P12:** smoke matrix, run-count review, immutable final outputs.
- **P13:** all ablations reproducible; parameters frozen.
- **P14:** hardware/software and consistent timing protocol.
- **P15:** five-seed raw results + honest uncertainty.
- **P16:** generated tables/figures; claims trace to runs.
- **P17:** environment/data/code/result/manuscript traceability passes.
