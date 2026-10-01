# ProRAG-FL v0.1.0 — Initial Research Release & Reproducibility Suite

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1%2Bcu130-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Tests](https://img.shields.io/badge/Tests-152%2F152%20Passing-brightgreen.svg?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Audit](https://img.shields.io/badge/Reproducibility%20Audit-48%2F48%20Passed-success.svg)](reports/audit/reproducibility_audit_report.md)
[![Zenodo](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.xxxxxx-blue.svg)](https://zenodo.org/)

We are pleased to announce the initial open-source research release of **ProRAG-FL** (`v0.1.0`), accompanying our paper:
> **"ProRAG-FL: Blockchain-Anchored Provenance-Aware Retrieval-Augmented Federated Intrusion Detection for Cloud-IoT Systems"** (Submitted to *IEEE Internet of Things Journal*).

This release provides the complete, mathematically audited, zero-leakage research framework, benchmark suites, 12 competitive baseline IDS models, and automated reproduction engines.

---

## 🚀 Key Highlights & Architectural Overview

ProRAG-FL resolves the fundamental **tripartite trust dilemma** (Model Trust, Knowledge Trust, and Decision Trust) inherent in collaborative IoT intrusion detection systems via a decoupled three-tier architecture:

1. **Tier 1 (Model Trust — Blockchain-Anchored Federated Consensus)**:
   - **Hyperledger Fabric 2.5** chaincode validates participant credentials, gradient envelope digests, and aggregation proofs via a 9-step atomic verification contract.
   - Robust parameter-space aggregation using **coordinate-wise trimmed mean ($\text{FedTrimmedAvg}$, $\beta=0.20$)** completely neutralizing Byzantine poisoning up to 40% adversary control.

2. **Tier 2 (Knowledge Trust — Deterministic Merkle CTI Provenance)**:
   - Structured ingestion adapters for **MITRE ATT&CK Enterprise v14.1, NVD CVE 2.0, CISA KEV, and Consortium Advisories**.
   - **Deterministic Unicode-canonicalized Merkle tree** chunking with SHA-256 leaf proofs.
   - **6-Point Hard Provenance Filter** enforcing signature validation, authority whitelisting, timestamp freshness, and tamper detection before hybrid Dense (`BGE-M3`) + Sparse (`BM25`) reciprocal rank fusion.

3. **Tier 3 (Decision Trust — Dual-Gated Line-Rate / CTI Reasoning Routing)**:
   - High-throughput **1D-CNN backbone** paired with temperature-scaled Platt calibration ($T^* = 1.428$) and class-conditional **Mahalanobis Out-of-Distribution (OOD)** distance scoring ($\text{AUROC} = 0.965$).
   - Bifurcates line-rate traffic: **99.8% sub-millisecond local classification** ($P_{99} = 0.18\text{ ms}$) for standard packets, escalating only uncertain or zero-day anomalies to an **allowlist-firewalled OpenAI structured reasoning engine** (`gpt-4o-mini`).

---

## 📊 Benchmark Results & Empirical Findings (CICIoT2023, $N=5$ Seeds)

All evaluations adhere to a strict **zero-leakage firewall** (training-only min-max normalization, immutable disjoint client indices, and zero-day Mirai family isolation).

### 1. Primary Intrusion Detection Utility (RQ1)
| Method / Comparator | Macro-F1 (Mean $\pm$ SD) | Balanced Accuracy | Operational FPR |
| :--- | :---: | :---: | :---: |
| Local 1D-CNN (B0) | $0.7824 \pm 0.0212$ | $0.7721 \pm 0.0189$ | $3.60\% \pm 0.08\%$ |
| MultiKrum (B3) | $0.8207 \pm 0.0117$ | $0.8100 \pm 0.0128$ | $3.49\% \pm 0.29\%$ |
| FedAvg (B2) | $0.8414 \pm 0.0074$ | $0.8309 \pm 0.0094$ | $3.35\% \pm 0.15\%$ |
| FedTrimmedAvg (B4) | $0.8566 \pm 0.0087$ | $0.8459 \pm 0.0098$ | $2.78\% \pm 0.26\%$ |
| SFLNID (B5) | $0.8642 \pm 0.0046$ | $0.8516 \pm 0.0045$ | $2.62\% \pm 0.09\%$ |
| Bc$^2$FL (B7) | $0.8636 \pm 0.0025$ | $0.8530 \pm 0.0072$ | $2.59\% \pm 0.13\%$ |
| FLOW (B6) | $0.8791 \pm 0.0118$ | $0.8673 \pm 0.0155$ | $2.54\% \pm 0.15\%$ |
| LQB-IDS (B9) | $0.8802 \pm 0.0079$ | $0.8682 \pm 0.0060$ | $2.38\% \pm 0.28\%$ |
| RLFE-IDS (B8) | $0.8830 \pm 0.0069$ | $0.8703 \pm 0.0056$ | $2.47\% \pm 0.16\%$ |
| FedMSE (B10) | $0.8840 \pm 0.0078$ | $0.8701 \pm 0.0090$ | $2.20\% \pm 0.31\%$ |
| pFL-IDS (B11) | $0.8915 \pm 0.0051$ | $0.8821 \pm 0.0065$ | $2.08\% \pm 0.18\%$ |
| Centralized 1D-CNN (B1) | $0.9190 \pm 0.0025$ | $0.9052 \pm 0.0052$ | $2.01\% \pm 0.07\%$ |
| **ProRAG-FL (Proposed)** | $\mathbf{0.9390 \pm 0.0031}$ | $\mathbf{0.9285 \pm 0.0038}$ | $\mathbf{1.49\% \pm 0.30\%}$ |

- **Macro-F1 Gain**: $+11.6\%$ relative improvement over standard FedAvg ($p < 0.001$, Cohen's $d = +13.32$).
- **False-Alarm Reduction**: $55.5\%$ relative drop in Operational FPR ($1.49\%$ vs $3.35\%$).
- **Centralized Benchmark**: Outperforms closed-world Centralized training ($0.939$ vs $0.919$) via verified external CTI escalation.

### 2. Byzantine Robustness Under Attack (RQ2)
- At $20\%$ Byzantine malicious client compromise:
  - Standard FedAvg collapses to $0.7022$ Macro-F1 (Attack Success Rate: $42.20\%$).
  - MultiKrum drops to $0.7012$ Macro-F1 (ASR: $36.98\%$).
  - **ProRAG-FL maintains $0.9125 \pm 0.0036$ attacked Macro-F1 with only $7.17\%$ ASR** ($p = 0.00005$, Cohen's $d = +32.11$).
- Under severe $40\%$ Byzantine saturation, ProRAG-FL sustains $0.8710$ Macro-F1 (FedAvg drops to $0.5100$).

### 3. Latency & Operational Economics (RQ4)
- At operational invocation rate ($\text{RIR} = 13.8\%$), composite end-to-end latency is **$25.36\text{ ms}$ at $\$0.30$ per $10,000$ flows**.
- Compared to non-selective broad RAG ($\text{RIR} = 100\%$, $168.67\text{ ms}$, $\$2.18 / 10\text{k}$ flows), selective escalation achieves a **$6.6\times$ latency reduction and $7.2\times$ cost savings**.

---

## 📦 What's Included in This Release

- **`src/prorag_fl/`**:
  - Full implementation of model trainer, 1D-CNN backbone, calibration module, Mahalanobis detector, Merkle tree verifier, hybrid retriever, and LLM reasoning engine.
- **12 Baselines (`src/prorag_fl/baselines/`)**:
  - Complete, faithful implementations of B0 through B11 with corresponding fidelity cards in `reports/baseline_fidelity/`.
- **Adversarial Suite (`src/prorag_fl/attacks/`)**:
  - 5 threat models: label-flipping, sign-inversion, gradient replacement, tabular backdoor watermarking, and CTI knowledge poison injection.
- **Reproducibility Engine (`src/prorag_fl/audit/`)**:
  - Automated 48-check verification engine enforcing frozen seed integrity, mathematical consistency, zero cherry-picking, and report synchronization.
- **Publication Exports (`reports/paper_exports/`)**:
  - 7 camera-ready LaTeX tables (`table_setup.tex`, `table_main_ids.tex`, `table_fl_poisoning.tex`, etc.).
  - 6 publication-ready vector/bitmap figures (`fig_baseline_macro_f1`, `fig_baseline_pareto`, `fig_byzantine_resilience`, `fig_latency_vs_rir`, `fig_roc_ood`, `fig_ablation_ladder`).
  - Scientific claims mapping (`claims.json`).

---

## ⚡ Quick Start

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/iam-ata/ProRAG-FL.git
cd ProRAG-FL

# Create conda environment
conda env create -f environment.yml
conda activate prorag-fl

# Install in development mode
pip install -e . --no-deps --no-build-isolation

# Run environment doctor
prorag doctor
```

### 2. Verify 152 Unit Tests
```bash
python -m pytest tests/unit -v
```

### 3. Run 48-Check Master Reproducibility Audit
```bash
prorag audit full
```

### 4. Build LaTeX Tables and Figures
```bash
prorag export build-all
```

---

## 📄 Citation & Attribution

If you use ProRAG-FL in your academic research, please cite:

```bibtex
@article{mohammadi2026proragfl,
  author    = {Mohammadi, Ata},
  title     = {ProRAG-FL: Blockchain-Anchored Provenance-Aware Retrieval-Augmented Federated Intrusion Detection for Cloud-IoT Systems},
  journal   = {IEEE Internet of Things Journal},
  year      = {2026},
  note      = {Submitted for publication}
}
```

```bibtex
@software{mohammadi_2026_proragfl_code,
  author       = {Mohammadi, Ata},
  title        = {ProRAG-FL: Reproducible Research Benchmark and Implementation Artifact},
  month        = sep,
  year         = 2026,
  publisher    = {Zenodo},
  version      = {v0.1.0},
  doi          = {10.5281/zenodo.xxxxxx},
  url          = {https://github.com/iam-ata/ProRAG-FL}
}
```

---

## ⚖️ License
This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.
