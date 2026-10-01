# Phase 12 — Frozen Experiment Matrix

Final seeds: `13,37,73,101,211`. Datasets run independently.

## E1 Local/centralized sanity
Local 1D-CNN and centralized 1D-CNN. Establish clean pipeline and performance reference.

## E2 FL heterogeneity
K=10; IID and alpha 1.0/0.5/0.3/0.1. Methods: FedAvg, MultiKrum where meaningful, FedTrimmedAvg, ProRAG-FL FL path, SFLNID, relevant pFL comparator. Report detection, convergence and communication.

## E3 Scalability
K=5,10,20 under representative IID/non-IID settings. Report model quality, round time, bytes, aggregation/provenance overhead.

## E4 Malicious clients
Fractions 0/10/20/30/40%. Attacks: label flip, untargeted update poisoning, model replacement, backdoor. Methods: FedAvg, MultiKrum, FedTrimmedAvg, FLOW, pFL-IDS where supported, proposed FL path. Report clean/attacked Macro-F1, ASR, malicious acceptance, benign false rejection, convergence.

## E5 Provenance attacks
Digest tamper, nonce replay, stale round, wrong version, unauthorized identity, revoked status. Expected hard rejection before aggregation. Measure correctness and latency.

## E6 Unseen-to-model
CICIoT2023 Mirai; Edge-IIoTset Malware. Compare classifier only, FedMSE anomaly comparator, standard RAG without provenance, RLFE-IDS if faithful, full ProRAG-FL. Report escalation recall, OOD metrics, Recall@5, MRR, final family identification, evidence correctness, latency.

## E7 RAG poisoning
Corpus fractions 0/5/10/20/30%. Tamper, unauthorized insertion, stale replay, prompt injection, authorized malicious source. Compare ordinary hybrid RAG, hard provenance RAG, provenance+freshness/corroboration, full system, RLFE where compatible.

## E8 Ablation
Use `24_ABLATION_AND_SENSITIVITY.md`.

## E9 Systems
Communication, training, Fabric, retrieval, API and end-to-end path measurements.

## E10 Validation sensitivity
Tune beta, tau_C, tau_M, Top-K and retrieval weights on validation only, then freeze.

## Execution staging
1. unit/integration tests;
2. smoke matrix;
3. one-seed pilot for implementation bugs only;
4. freeze final configs;
5. five-seed final matrix.

After config freeze, final test outcomes are not a reason to retune.
