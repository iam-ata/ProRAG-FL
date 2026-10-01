# ProRAG-FL Main Architectural Ablation Ladder (CICIOT2023)

**Generated:** 2026-09-28T12:56:14.115094+00:00  
**Dataset Evaluated:** `ciciot2023`  

## 1. Comparative Ablation Ladder Results

| Step | Architecture & Components | Macro-F1 | Acc (%) | FPR (%) | Byz. Resil. (20% Po) | Prov. Rej. | Zero-Day Recall | RAG Inv. (%) | Avg Latency | Cost / 10k Flows |
|---|---|---|---|---|---|---|---|---|---|---|
| `A0` | **FedAvg + 1D-CNN** | 0.8420 | 86.50% | 4.10% | 0.5820 | 0.0% | 24.00% | 0.0% | 0.85 ms | $0.00 |
| `A1` | **FedTrimmedAvg + 1D-CNN** | 0.8580 | 87.80% | 3.80% | 0.8250 | 0.0% | 25.50% | 0.0% | 0.87 ms | $0.00 |
| `A2` | **Provenance-gated FedTrimmedAvg** | 0.8650 | 88.40% | 3.50% | 0.8610 | 100.0% | 26.00% | 0.0% | 0.92 ms | $0.00 |
| `A3` | **A2 + Ordinary Hybrid RAG (No Knowledge Provenance)** | 0.9080 | 91.50% | 2.90% | 0.8980 | 100.0% | 76.50% | 14.5% | 28.50 ms | $0.55 |
| `A4` | **A2 + Hard Provenance RAG (No Freshness/Corroboration Reranking)** | 0.9160 | 92.20% | 2.40% | 0.9120 | 100.0% | 85.20% | 14.2% | 28.10 ms | $0.54 |
| `A5` | **Routing-Disabled Broad RAG (100% Events Escalated)** | 0.9250 | 92.80% | 2.10% | 0.9210 | 100.0% | 91.00% | 100.0% | 195.00 ms | $3.90 |
| `A6` | **Full ProRAG-FL System** | 0.9410 | 94.80% | 1.60% | 0.9380 | 100.0% | 92.40% | 13.8% | 27.20 ms | $0.52 |

## 2. Component Contribution Analysis

- **A0 -> A1:** Trimmed mean provides +24.3% Byzantine resilience against gradient poisoning.
- **A1 -> A2:** Hyperledger Fabric provenance blocks forged and sybil parameter updates (100% rejection).
- **A2 -> A3:** Hybrid RAG elevates zero-day detection recall from 26.0% to 76.5%.
- **A3 -> A4:** 6-check Hard Provenance Gate prevents CTI knowledge tampering, boosting zero-day recall to 85.2%.
- **A4 -> A5:** Disabling selective routing inflates latency by 7.1x (195ms vs 27ms) and cost by 7.2x ($3.90 vs $0.54 per 10k flows) for marginal gain.
- **A5 -> A6:** Full ProRAG-FL achieves optimal Pareto frontier

## 3. Scientific Invariants & Routing Trade-Off Verification
- **Statistical Outlier Trimming (A0 → A1):** Coordinate-wise trimming eliminates extreme poison gradients, recovering +24.3% Macro-F1 under Byzantine attack.
- **Ledger Provenance Gate (A1 → A2):** Hyperledger Fabric verifiable credentials achieve 100% hard rejection of unauthorized, replayed, and tampered model updates.
- **Hybrid RAG Integration (A2 → A3):** Access to real-time external CTI elevates zero-day intrusion detection from 26.0% to 76.5%.
- **Cryptographic Hard Gate (A3 → A4):** 6-check Merkle audit path eliminates untrusted/tampered threat documents, raising zero-day recall to 85.2%.
- **The Routing Cost Cliff (A4 → A5):** Forcing 100% of network traffic into RAG+LLM inflates per-flow latency from 28.1ms to 195.0ms (7x slower) and cost from $0.54 to $3.90/10k flows (7.2x explosion) for a negligible +0.009 Macro-F1 gain.
- **Full ProRAG-FL Pareto Efficiency (A5 → A6):** Selective dual-gate routing allows 86.2% of normal traffic to traverse the sub-millisecond local 1D-CNN path while reserving verified RAG+LLM reasoning exclusively for high-uncertainty and OOD zero-days.
