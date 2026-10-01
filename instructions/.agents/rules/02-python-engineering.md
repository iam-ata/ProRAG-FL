---
trigger: glob
globs: "*.py, **/*.py, pyproject.toml"
description: "Python coding and testing standards for the ProRAG-FL repository."
---
# Python Engineering
- No hard-coded absolute paths.
- Use `pathlib.Path`, typed public interfaces, and structured exceptions.
- Pass seeds/RNGs explicitly; do not hide randomness.
- Fail on schema mismatch, NaN/Inf, stale model version, invalid provenance, or missing required fields.
- Use typed schemas for configs, SecurityEvent, provenance records, RAG evidence, and model responses.
- Tests required for split logic, transforms, metrics, attacks, provenance, serialization, and API sanitization.
- Every CLI supports `--help`; long runs support smoke mode.
- Every artifact has run ID and config hash.
