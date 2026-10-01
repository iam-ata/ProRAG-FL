# Phase 0 — Repository Bootstrap

## Goal
Create a reproducible research repository without implementing the scientific method yet.

## Steps
1. Inspect current files, active Conda env, Python, Git, GPU.
2. Confirm environment is `prorag-fl`.
3. Create `src/prorag_fl/` package and the repository tree from `04_REPOSITORY_STRUCTURE.md`.
4. Create `pyproject.toml` with package metadata, pytest, Ruff, and mypy configuration.
5. Implement repository-root/path helper using `pathlib`.
6. Implement YAML loader + Pydantic configuration validation.
7. Implement deterministic seed helper for Python, NumPy, PyTorch CPU/CUDA.
8. Implement structured logging.
9. Implement run ID and config-hash generation.
10. Implement environment capture with secret redaction.
11. Create `.gitignore` and `.env.example`.
12. Add CLI commands:
   - `doctor`
   - `validate-config`
   - `show-env`
13. Add unit tests.
14. Run lint/tests/doctor.
15. Update `31_STATUS.md`.

## Run ID
Suggested:
```text
<experiment>_<timestamp>_<short-config-hash>_seed<seed>
```

## Required tests
- same config -> same config hash;
- different scientific config -> different hash;
- run directory never silently overwrites an existing completed run;
- seed helper reproduces NumPy/PyTorch random sequences;
- environment output redacts secrets;
- project root resolves independent of current working directory.

## Acceptance gate
Phase 0 passes only when:
- package imports;
- pytest passes;
- Ruff passes;
- doctor reports environment correctly;
- no secrets are printed;
- config validation works;
- status file is updated.
