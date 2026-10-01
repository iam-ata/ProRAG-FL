# ProRAG-FL Full Experiment Matrix Plan & Cost Audit

**Generated:** 2026-09-25T18:20:13.958413+00:00  
**Total Runs Planned:** `2354`  

## 1. Run Count Breakdown by Experiment

| Experiment ID | Focus Area | Run Count |
|---|---|---|
| `E10_VALIDATION_SENSITIVITY` | Validation Hyperparameter Grid Search | 24 |
| `E1_SANITY` | Local 1D-CNN vs Centralized Oracle Ceiling | 20 |
| `E2_HETEROGENEITY` | FL Non-IID Dirichlet Partitioning & Heterogeneity | 300 |
| `E3_SCALABILITY` | Client Scaling (K=5, 10, 20) | 60 |
| `E4_MALICIOUS_CLIENTS` | Byzantine Update Poisoning & Backdoors (0-40%) | 960 |
| `E5_PROVENANCE_ATTACKS` | Blockchain & Provenance Layer Tampering | 60 |
| `E6_UNSEEN_TO_MODEL` | Zero-Day Unseen Family Escalation & Reasoning | 50 |
| `E7_RAG_POISONING` | Knowledge Base Poisoning & Prompt Injection | 800 |
| `E8_ABLATION` | Main Ablation Ladder (A0 through A6) | 70 |
| `E9_SYSTEMS` | End-to-End Systems Latency & Communication | 10 |

## 2. Resource Projections

| Resource Category | Estimated Metric | Notes |
|---|---|---|
| **GPU Compute** | `112.88 GPU-hours` | Based on PyTorch 1D-CNN batch processing |
| **CPU Compute** | `352.74 CPU-hours` | Including FL client aggregation & Krum distance |
| **Disk Storage** | `5885.0 MB` | Metrics, checkpoints, logs, and run manifests |
| **Fabric Transactions** | `62,240` | Provenance envelopes and block commits |
| **OpenAI API Calls** | `85,000` | Zero-day and RAG poisoning reasoning samples |
| **OpenAI Est. Cost** | `$33.1500 USD` | At GPT-4o-mini current token rates |

## 3. Strict Scientific Safeguards
- Final evaluations executed across standard seeds: `13, 37, 73, 101, 211`.
- Ground-truth labels strictly isolated from reasoning payloads (evaluation-only).
- Checkpointing and resumability enforced via immutable `DONE` markers.
- Zero data snooping: hyperparameters tuned exclusively on validation splits.
