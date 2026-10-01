# Complete Execution Roadmap

| Phase | File(s) | Output gate |
|---|---|---|
| 0 Bootstrap | `07_PHASE_0_BOOTSTRAP.md` | package/config/tests/doctor |
| 1 Data | `08_DATASETS_AND_PREPROCESSING.md`, `09_CLIENT_PARTITIONING.md` | leakage-safe manifests |
| 2 IDS | `10_LOCAL_IDS_1DCNN.md` | stable local/central model |
| 3 Gate | `11_CALIBRATION_AND_OOD.md` | frozen validation thresholds |
| 4 FL | `12_FEDERATED_LEARNING.md` | strategy smoke tests |
| 5 Model provenance | `13_BLOCKCHAIN_AND_MODEL_PROVENANCE.md` | attack/replay tests |
| 6 Knowledge provenance | `14_KNOWLEDGE_INGESTION_AND_MERKLE.md` | deterministic roots/proofs |
| 7 RAG | `15_HYBRID_RAG.md` | verified Top-5 retrieval |
| 8 OpenAI | `16_OPENAI_REASONING.md` | sanitized structured reasoning |
| 9 Integration | `17_END_TO_END_PIPELINE.md` | direct + escalated paths |
| 10 Baselines | `20`–`22` | fidelity cards + runs |
| 11 Attacks | `18_ATTACKS_AND_THREAT_MODEL.md` | positive/defense controls |
| 12 Matrix | `23_EXPERIMENT_MATRIX.md` | immutable final runs |
| 13 Ablation | `24_ABLATION_AND_SENSITIVITY.md` | component evidence |
| 14 Systems | `25_SYSTEMS_BENCHMARKS.md` | latency/overhead |
| 15 Analysis | `19_METRICS_AND_STATISTICS.md` | fixed-seed aggregation |
| 16 Paper export | `26_RESULTS_PIPELINE_AND_PAPER_SYNC.md` | generated TeX/figures |
| 17 Audit | `27`, `30`, `36` | reproducibility checklist |

Never launch the full final experiment matrix before component smoke tests and a one-seed pilot are green.
