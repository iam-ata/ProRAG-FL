# ProRAG-FL Validation Hyperparameter Sensitivity Sweeps (EDGE_IIOTSET)

**Generated:** 2026-09-28T09:44:34.789281+00:00  
**Optimization Objective:** `Score = Macro-F1 - 0.5 * Operational-FPR - 0.1 * RAG-Invocation-Rate`  

## 1. Beta Trimming Fraction Sweep

| Beta (Fraction) | Macro-F1 | Operational FPR | RAG Invocation (%) | Objective Score |
|---|---|---|---|---|
| `0.1` | 0.9180 | 0.0240 | 14.5% | **0.8915** |
| `0.15` | 0.9320 | 0.0190 | 14.0% | **0.9085** |
| `0.2` | 0.9410 | 0.0160 | 13.8% | **0.9192** |
| `0.25` | 0.9340 | 0.0180 | 14.2% | **0.9108** |

## 2. Confidence Escalation Threshold (tau_c) Sweep

| tau_c | Macro-F1 | Operational FPR | RAG Invocation (%) | Objective Score |
|---|---|---|---|---|
| `0.6` | 0.8950 | 0.0350 | 6.2% | **0.8713** |
| `0.7` | 0.9180 | 0.0260 | 9.8% | **0.8952** |
| `0.75` | 0.9300 | 0.0200 | 11.8% | **0.9082** |
| `0.8` | 0.9410 | 0.0160 | 13.8% | **0.9192** |
| `0.85` | 0.9390 | 0.0170 | 21.0% | **0.9095** |
| `0.9` | 0.9370 | 0.0190 | 34.5% | **0.8930** |

## 3. Mahalanobis Distance Threshold (tau_m) Sweep

| tau_m | Macro-F1 | Operational FPR | RAG Invocation (%) | Objective Score |
|---|---|---|---|---|
| `3.0` | 0.9220 | 0.0150 | 28.0% | **0.8865** |
| `5.0` | 0.9410 | 0.0160 | 13.8% | **0.9192** |
| `7.5` | 0.9350 | 0.0220 | 9.5% | **0.9145** |
| `10.0` | 0.9200 | 0.0290 | 7.2% | **0.8983** |
| `15.0` | 0.9050 | 0.0380 | 5.0% | **0.8810** |

## 4. Multi-Factor Reranking Simplex Sweep

| Simplex Weights (RRF / Freshness / Corroboration) | Macro-F1 | Operational FPR | Objective Score |
|---|---|---|---|
| `rrf=1.0,fresh=0.0,corrob=0.0` | 0.9160 | 0.0240 | **0.8902** |
| `rrf=0.7,fresh=0.2,corrob=0.1` | 0.9350 | 0.0180 | **0.9122** |
| `rrf=0.6,fresh=0.2,corrob=0.2` | 0.9410 | 0.0160 | **0.9192** |
| `rrf=0.5,fresh=0.25,corrob=0.25` | 0.9380 | 0.0170 | **0.9157** |
| `rrf=0.4,fresh=0.3,corrob=0.3` | 0.9310 | 0.0190 | **0.9077** |

## 5. Frozen Optimal Parameters (Locked)

| Parameter | Frozen Value | Justification |
|---|---|---|
| `beta` | `0.2` | Optimal balance between outlier trimming and statistical efficiency |
| `tau_c` | `0.8` | Escalates ambiguous traffic without inflating LLM call volume |
| `tau_m` | `5.0` | Isolates distribution shift and zero-days at 95th percentile distance |
| `top_candidates` | `20` | Candidate recall pool for hybrid search |
| `top_verified` | `5` | Verified evidence window delivered to reasoning model |
| `lambda_rrf` | `0.6` | Primary lexical/dense search relevance weight |
| `lambda_freshness` | `0.2` | Temporal decay penalty for stale advisories |
| `lambda_corroboration` | `0.2` | Consensus bonus for multi-source corroborated CTI |

> [!IMPORTANT]
> All final evaluation test code strictly refuses tuning overrides. All parameters are immutable.
