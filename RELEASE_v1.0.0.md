# 🚀 ProRAG-FL v1.0.0 — Official Research Release & Reproducibility Suite

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1%2Bcu130-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Tests](https://img.shields.io/badge/Tests-152%2F152%20Passing-brightgreen.svg?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Audit](https://img.shields.io/badge/Reproducibility%20Audit-48%2F48%20Passed-success.svg)](reports/audit/reproducibility_audit_report.md)
[![DOI](https://zenodo.org/badge/1400577850.svg)](https://doi.org/10.5281/zenodo.23089427)

---

## 📌 Overview

We are proud to announce the **v1.0.0 official research release** of **ProRAG-FL**, the accompanying codebase and experimental evaluation framework for our paper:

> **"ProRAG-FL: Blockchain-Anchored Provenance-Aware Retrieval-Augmented Federated Intrusion Detection for Cloud-IoT Systems"**  
> *Submitted to IEEE Internet of Things Journal (2026)*

**Authors:**  
Ata Mohammadi$^1$, Nahideh Derakhshanfard$^1$ (Corresponding Author), Ali Asghar Pour Haji Kazem$^2$, Neda Dadashkhani$^3$, Wael Anabousi$^4$, Parisa Khoshvaght$^5$, and Mehdi Hosseinzadeh$^6$ (Corresponding Author)

$^1$ Department of Computer Engineering, Ta.C., Islamic Azad University, Tabriz, Iran  
$^2$ Department of Software Engineering, Faculty of Engineering and Natural Sciences, Istinye University, Istanbul, Turkey  
$^3$ Computer Programming Program, Vocational School, Istinye University, Istanbul, Turkey  
$^4$ e-Learning department, Al-Ahliyya Amman University, Amman, Jordan  
   *(E-mail: `w.anbousi@ammanu.edu.jo`, ORCID: [0009-0004-3913-939X](https://orcid.org/0009-0004-3913-939X))*  
$^5$ Institute of Research and Development, Duy Tan University, Da Nang, Vietnam  
   *(E-mail: `parisakhoshvaght@duytan.edu.vn`)*  
$^6$ School of Engineering & Technology, Duy Tan University, Da Nang, Vietnam  

**Corresponding Contacts:**  
- Nahideh Derakhshanfard: `N.derakhshan@iau.ac.ir`  
- Mehdi Hosseinzadeh: `mehdihosseinzadeh@duytan.edu.vn`

---

## 🌟 What's New in v1.0.0

This production research release features the complete, frozen, and mathematically audited implementation of ProRAG-FL, spanning:
- **12 Competitive Baselines (B0–B11)** fully implemented, benchmarked, and cataloged with transparent fidelity cards (`reports/baseline_fidelity/`).
- **5 Threat Models & Adversarial Attacks**: Untargeted label-flipping, sign-inversion, gradient replacement, tabular backdoor watermarking, and CTI knowledge poisoning.
- **48-Check Automated Reproducibility Audit**: Deterministic verification passing 100% of mathematical integrity, zero-leakage, and report synchronization checks.
- **Publication-Ready Artifact Generator**: Automated CLI generating 7 camera-ready LaTeX tables and 6 vector figures (`.pdf`, `.png`, `.svg`).
- **Full Authorship & Citation Metadata**: Synchronized across `CITATION.cff`, `.zenodo.json`, `pyproject.toml`, and documentation.

---

## 🏛️ Tripartite Architecture Highlights

ProRAG-FL resolves the **tripartite trust dilemma** in collaborative Cloud-IoT security:

```
[ Tier 1: Model Trust ]  ──► Hyperledger Fabric 2.5 + Coordinate-wise FedTrimmedAvg (β=0.20)
[ Tier 2: Knowledge Trust ] ──► SHA-256 Merkle CTI Registry + 6-Point Hard Provenance Filter
[ Tier 3: Decision Trust ] ──► Platt Calibration (T*=1.428) + Mahalanobis OOD + LLM Escalation
```

1. **Tier 1 (Model Trust)**:
   - Hyperledger Fabric smart contract validates client identity, gradient digests, and aggregation proofs.
   - Robust coordinate-wise trimmed mean completely neutralizes up to **40% Byzantine client compromise**.
2. **Tier 2 (Knowledge Trust)**:
   - Structured ingestion from MITRE ATT&CK Enterprise v14.1, NVD CVE 2.0, CISA KEV, and security advisories.
   - Deterministic Merkle tree leaf verification preventing knowledge-base poisoning or tampering.
   - Hybrid dense (`BGE-M3`) + sparse (`BM25`) reciprocal rank fusion.
3. **Tier 3 (Decision Trust)**:
   - Line-rate **1D-CNN backbone** classifies standard traffic with **sub-millisecond latency** ($P_{99} = 0.18\text{ ms}$).
   - Platt temperature scaling and class-conditional Mahalanobis distance ($\text{AUROC} = 0.965$) escalate only zero-day or ambiguous anomalies to structured reasoning.

---

## 📊 Key Experimental Findings (CICIoT2023, $N=5$ Frozen Seeds)

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
- At **20% Byzantine compromise**:
  - FedAvg collapses to $0.7022$ Macro-F1 (Attack Success Rate: $42.20\%$).
  - MultiKrum drops to $0.7012$ Macro-F1 (ASR: $36.98\%$).
  - **ProRAG-FL maintains $0.9125 \pm 0.0036$ attacked Macro-F1 with only $7.17\%$ ASR** ($p = 0.00005$, Cohen's $d = +32.11$).
- Under severe **40% Byzantine saturation**, ProRAG-FL sustains $0.8710$ Macro-F1 (FedAvg falls to $0.5100$).

### 3. Latency & Operational Economics (RQ4)
- At operational invocation rate ($\text{RIR} = 13.8\%$), composite end-to-end latency is **$25.36\text{ ms}$ at $\$0.30$ per $10,000$ flows**.
- Compared to non-selective broad RAG ($\text{RIR} = 100\%$, $168.67\text{ ms}$, $\$2.18 / 10\text{k}$ flows), selective escalation achieves a **$6.6\times$ latency reduction and $7.2\times$ cost savings**.

---

## 🛠️ Quick Start & Reproduction

### 1. Installation
```bash
git clone https://github.com/iam-ata/ProRAG-FL.git
cd ProRAG-FL

# Set up Conda environment
conda env create -f environment.yml
conda activate prorag-fl

# Install CLI in editable mode
pip install -e . --no-deps --no-build-isolation
```

### 2. Verify System & Environment
```bash
prorag doctor
```

### 3. Run Test Suite (152 unit and integration tests)
```bash
pytest tests/ -v
```

### 4. Run 48-Check Reproducibility Audit
```bash
prorag audit --strict
```

### 5. Re-generate All Camera-Ready Tables & Figures
```bash
prorag export build-all
```
Outputs are exported immediately to `reports/paper_exports/tables/` and `reports/paper_exports/figures/`.

---

## 📦 Repository Structure

```
ProRAG-FL/
├── src/prorag_fl/          # Core architecture modules
│   ├── attacks/            # 5 adversarial threat implementations
│   ├── audit/              # 48-check deterministic audit engine
│   ├── baselines/          # 12 baseline IDS algorithms (B0–B11)
│   ├── blockchain/         # Hyperledger Fabric chaincode & ledger
│   ├── cti/                # Merkle CTI trees & Hard Provenance Filter
│   ├── export/             # LaTeX table and figure export pipeline
│   ├── models/             # 1D-CNN backbone, calibration & OOD
│   └── rag/                # Hybrid dense/sparse retrieval & reasoning
├── tests/                  # 152 automated pytest test cases
├── configs/                # Frozen experiment configs & seed lists
├── reports/
│   ├── audit/              # Full audit report log
│   ├── baseline_fidelity/  # Mathematical comparison cards for baselines
│   └── paper_exports/      # Generated LaTeX tables and vector figures
├── CITATION.cff            # Academic citation metadata (CFF v1.2.0)
├── .zenodo.json            # Zenodo archive metadata
├── pyproject.toml          # Python package specification
└── README.md               # Primary documentation
```

---

## 📄 Citation

```bibtex
@article{mohammadi2026proragfl,
  author    = {Mohammadi, Ata and Derakhshanfard, Nahideh and Pour Haji Kazem, Ali Asghar and Dadashkhani, Neda and Anabousi, Wael and Khoshvaght, Parisa and Hosseinzadeh, Mehdi},
  title     = {ProRAG-FL: Blockchain-Anchored Provenance-Aware Retrieval-Augmented Federated Intrusion Detection for Cloud-IoT Systems},
  journal   = {IEEE Internet of Things Journal},
  year      = {2026},
  note      = {Submitted for publication}
}
```

```bibtex
@software{mohammadi_2026_proragfl_code,
  author       = {Mohammadi, Ata and Derakhshanfard, Nahideh and Pour Haji Kazem, Ali Asghar and Dadashkhani, Neda and Anabousi, Wael and Khoshvaght, Parisa and Hosseinzadeh, Mehdi},
  title        = {ProRAG-FL: Reproducible Research Benchmark and Implementation Artifact},
  month        = sep,
  year         = 2026,
  publisher    = {Zenodo},
  version      = {v1.0.0},
  doi          = {10.5281/zenodo.23089427},
  url          = {https://github.com/iam-ata/ProRAG-FL}
}
```

---

## ⚖️ License
This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.
