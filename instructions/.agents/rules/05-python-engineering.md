---
trigger: glob
globs: "*.py,**/*.py,pyproject.toml"
description: Python engineering conventions for ProRAG-FL.
---

# Python Engineering

- Python 3.11 in Conda environment `prorag-fl`.
- Source layout under `Code/src/prorag_fl/`.
- Type hints for public functions/classes.
- `pathlib.Path`, no hard-coded absolute paths.
- Pydantic/dataclasses for configs and records.
- Explicit RNG/seed parameters.
- Structured logging.
- YAML-driven experiments.
- pytest + Ruff.
- No notebook-only research logic.
- No broad exception swallowing.
- Fail loudly on invalid schemas, NaNs, stale model versions, invalid proofs and missing artifacts.
- Long jobs support dry-run/config validation and resumable run IDs.
