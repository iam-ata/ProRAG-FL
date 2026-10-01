# Master Execution Plan

## Phase 0 — Bootstrap
Package skeleton, config loader, logging, seed utilities, run manager, gitignore, env example, lint/tests, doctor CLI.
Exit: pytest/lint/doctor pass.

## Phase 1 — Data
CICIoT2023 first, then Edge-IIoTset via a common adapter. Build checksums, schemas, leakage-safe split/preprocess, FL partitions, held-out-family manifests.
Exit: automated leakage report passes.

## Phase 2 — IDS
Implement frozen 1D-CNN, centralized/local baselines, calibration, 128-D embeddings, Mahalanobis OOD.
Exit: tiny-batch overfit, checkpoint round-trip, deterministic smoke training.

## Phase 3 — FL
Flower + FedAvg/MultiKrum/FedTrimmedAvg + provenance-gated strategy using mock provenance first.
Exit: K=3, two-round deterministic smoke runs for all strategies.

## Phase 4 — Blockchain
3-org Fabric dev network, model-update registry, knowledge registry, Merkle utilities, replay/version checks, 2-of-3 incident admission.
Exit: tamper/replay/stale/version/Merkle/endorsement integration tests pass.

## Phase 5 — RAG
CTI adapters, MinIO, BGE-M3 dense+sparse, Qdrant, RRF, hard provenance filter, Top-20→Top-5, retrieval benchmark.
Exit: expected evidence retrieved; corrupted chunk never eligible.

## Phase 6 — OpenAI
Sanitized SecurityEvent, Responses API adapter, Structured Output schema, mock tests, explicit real-API gate, token/cost/latency logging.
Exit: forbidden fields cannot reach API payload.

## Phase 7 — Baselines
Controls first, then SFLNID, FLOW, Bc²FL, RLFE-IDS, Huang et al., FedMSE, Thein et al. Create fidelity card before code.
Exit: every baseline has CLI/config, smoke test, metric schema, fidelity classification.

## Phase 8 — Attacks
FL poisoning/backdoor/replay and RAG tampering/insertion/replay/prompt injection/authorized-malicious-source plus trigger amplification.
Exit: each attack demonstrably affects an unprotected control where feasible.

## Phase 9 — Full matrix
Run core IDS → heterogeneity → scalability → malicious clients → provenance attacks → unseen-to-model → RAG poisoning → ablations → systems → validation-only sensitivity.
Exit: immutable complete run manifests.

## Phase 10 — Analysis
Generate master results, plots, tables, failure analysis, statistical summaries. No manual metric entry.

## Phase 11 — Paper sync
Export LaTeX tables/figures/setup tables and machine-readable claim support from verified runs only.
