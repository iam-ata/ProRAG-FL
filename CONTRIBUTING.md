# Contributing to ProRAG-FL

Thank you for your interest in contributing to **ProRAG-FL**! This document provides guidelines for contributors, collaborators, and researchers extending the benchmark suite or algorithm implementations.

---

## 1. Scientific & Ethical Invariants

Because ProRAG-FL is an empirical research artifact supporting peer-reviewed scientific publications, all contributions must respect the following core research invariants:

1. **Strict Anti-Cherry-Picking Protocol**:
   - Any evaluation must execute across the 5 pre-declared frozen seeds: `[13, 37, 73, 101, 211]`.
   - Never exclude individual outlier seeds or under-performing runs from reported metrics.
   - All raw per-seed records must be preserved in master result datasets.
2. **Zero-Leakage Data Firewall**:
   - Preprocessing scalers (e.g., `StandardScaler`) must be fitted strictly on the training partition ($\mu_{train}, \sigma_{train}$).
   - Feature statistics must never be computed across validation or test splits.
   - Zero-day held-out attack families (e.g., Mirai in CICIoT2023, Malware in Edge-IIoTset) must remain strictly excluded from training and calibration datasets.
3. **Manuscript Narrative Separation**:
   - Code execution pipelines must never overwrite or modify scientific prose under `../Manuscript/`.
   - Synchronization to the manuscript directory is permitted only via explicit CLI confirmation (`prorag export sync-manuscript --execute`).
4. **Honest Scientific Claims**:
   - Do not claim "true zero-day detection" without qualifying it as *unseen held-out attack families with prior CTI intelligence*.
   - Do not claim "blockchain guarantees semantic truth"; blockchain guarantees tamper-proof immutable provenance records, not the real-world accuracy of external claims.

---

## 2. Development Setup

### Environment Installation

```bash
# 1. Clone repository
git clone https://github.com/iam-ata/ProRAG-FL.git
cd ProRAG-FL/Code

# 2. Create and activate Conda environment
conda env create -f environment.yml
conda activate prorag-fl

# 3. Install package in development mode
pip install -e . --no-deps --no-build-isolation

# 4. Verify system environment
prorag doctor
```

---

## 3. Code Style & Quality Standards

ProRAG-FL enforces modern Python 3.11 standards with strict typing and formatting:

- **Linter & Formatter**: We use [Ruff](https://astral.sh/ruff) for blazing-fast linting and code formatting:
  ```bash
  # Check for lint errors
  ruff check src tests

  # Check formatting
  ruff format --check src tests

  # Auto-format
  ruff format src tests
  ```
- **Type Annotations**: All public functions, classes, and CLI methods must feature comprehensive Python type hints (`from __future__ import annotations`).
- **Data Models**: Use Pydantic v2 schemas (`pydantic.BaseModel`) for all configuration, messaging, and reporting structures.

---

## 4. Testing & Acceptance Protocol

Before submitting any Pull Request, ensure that all tests pass with zero errors:

```bash
# 1. Run unit test regression suite (152 tests)
pytest tests/unit -v

# 2. Run master reproducibility audit
prorag audit full

# 3. Verify checklist integrity
prorag audit checklist
```

---

## 5. Submitting Pull Requests

1. **Fork and Branch**: Create a feature or fix branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: add new federated defense strategy`
   - `fix: resolve sparse BM25 token normalization issue`
   - `docs: update replication guide in README`
   - `test: add unit test for Merkle proof verification`
3. **Open Pull Request**: Submit the PR against `main` with a clear description of changes, motivation, and test verification output.
