# Ready-to-Paste Antigravity Prompts

## Start
> The project has `Code/` and `Manuscript/`. All research instruction Markdown files intentionally stay under `Code/instructions/`; do not move them. Work inside `Code/`. Read the master/method/environment/roadmap/Phase-0 files. Inspect first, show the Phase 0 plan and acceptance criteria, execute Phase 0 only, update `instructions/31_STATUS.md`, and stop.

## Data
> Read `08_DATASETS_AND_PREPROCESSING.md`, `09_CLIENT_PARTITIONING.md`, and the master contract. Implement CICIoT2023 using the actual files I provide; do not assume columns. Produce raw/split manifests and leakage tests. Stop after CICIoT2023 passes before Edge-IIoTset.

## IDS
> Read `10_LOCAL_IDS_1DCNN.md`. Implement the locked network exactly, including the 128-D embedding. Complete tiny-batch overfit, gradient, checkpoint and determinism tests. Establish local/centralized smoke runs. Do not start FL.

## Calibration/OOD
> Read `11_CALIBRATION_AND_OOD.md`. Fit temperature scaling and Mahalanobis using training/validation only. Prove final held-out test data never enters threshold fitting. Save frozen thresholds.

## FL
> Read `12_FEDERATED_LEARNING.md`. Implement FedAvg, MultiKrum, FedTrimmedAvg and provenance-gated FedTrimmedAvg with a mock provenance backend first. Run K=3/two-round smoke. Do not start Fabric until green.

## Blockchain
> Read `13_BLOCKCHAIN_AND_MODEL_PROVENANCE.md`. Build the target-compatible Fabric provenance layer and prove valid acceptance plus tamper, replay, stale round, wrong version and invalid identity rejection. Do not report mock timings as blockchain timings.

## Knowledge provenance
> Read `14_KNOWLEDGE_INGESTION_AND_MERKLE.md`. Build one authoritative source end-to-end first and prove modified chunks fail the old Merkle proof. Then generalize adapters.

## RAG
> Read `15_HYBRID_RAG.md`. Implement BGE-M3 dense+sparse retrieval, Qdrant, RRF, hard provenance filtering and verified Top-5. Build retrieval benchmark. Do not call OpenAI yet.

## OpenAI
> Read `16_OPENAI_REASONING.md` and security instructions. Implement mock first. Show exact sanitized payload/schema tests. Do not make a real API call unless external API is explicitly enabled and credentials are configured.

## Integration
> Read `17_END_TO_END_PIPELINE.md`. Prove direct events never call RAG/API and invalid evidence never reaches reasoning. Ground truth must remain evaluation-only.

## Baselines
> Read `20_BASELINES_MASTER.md`, `21_BASELINE_IMPLEMENTATION_DETAILS.md`, `22_BASELINE_FIDELITY_PROTOCOL.md`, and `37_BASELINE_SOURCE_NOTES.md`. Implement simple controls first. Before each published baseline create its fidelity card, locate official code/full paper, and do not invent missing parameters.

## Attacks
> Read `18_ATTACKS_AND_THREAT_MODEL.md`. Implement every attack with an immutable config, positive control and defense test. Do not tune attack strength after seeing final defense results.

## Final experiments
> Read `23_EXPERIMENT_MATRIX.md`, `19_METRICS_AND_STATISTICS.md`, and `28_CONFIG_AND_CLI_CONTRACT.md`. Expand the planned matrix and report total runs, estimated compute/storage/API requests first. Execute smoke tier only. Wait for approval before full matrix.

## Analysis/paper
> Aggregate only immutable DONE runs. Generate all tables/figures by script. Use fixed five-seed summaries. Export to `Code/reports/paper_exports/` first and copy to `../Manuscript/` only after approval.
