# Master Agent Contract

## Research integrity
Never fabricate dataset statistics, model scores, attack success, RAG scores, blockchain timing, API cost, baseline results, logs, citations, or hardware measurements. Every manuscript number must trace to a stored run artifact.

## Test-set firewall
The final test split is evaluation-only. Never use it to fit preprocessing, feature selection, class weights, architecture, hyperparameters, calibration, confidence/OOD thresholds, retrieval weights, Top-K, defense thresholds, prompts, or baseline parameters.

## Proposed-method fidelity
`02_LOCKED_PROPOSED_METHOD.md` is authoritative. Do not silently replace the model, aggregator, provenance semantics, OOD gate, RAG design, datasets, blockchain boundary, knowledge admission, or terminology.

## Baseline fidelity
Before coding a published baseline:
1. identify paper/DOI;
2. locate official code/supplement if available;
3. pin commit/version if used;
4. extract equations/architecture/hyperparameters;
5. write a fidelity card;
6. classify `official`, `faithful_reimplementation`, or `approximate_reimplementation`.

If details are missing, do not invent them. Record the ambiguity and stop or mark the implementation approximate.

## Reproducibility
Primary seeds: `13, 37, 73, 101, 211`.

Every substantive run stores:
- run ID/time;
- Git commit;
- resolved config + config hash;
- dataset/split manifest hashes;
- seed;
- Python/PyTorch/CUDA and package snapshot;
- CPU/GPU/RAM;
- stdout/stderr;
- raw metrics and timings;
- checkpoint/artifact references;
- DONE/FAILED state.

Do not overwrite prior runs.

## Source of truth

```text
raw data → immutable manifests → configs → run artifacts → aggregated analysis → generated LaTeX/figures → manuscript
```

The manuscript is not a source of experiment values.

## Code quality
- Python 3.11 in Conda;
- typed public interfaces;
- Pydantic/dataclasses for records;
- `pathlib`;
- YAML-driven configuration;
- structured logging;
- pytest + Ruff;
- no notebook-only scientific logic;
- no absolute paths;
- no secret values in code.

## Infrastructure boundary
Python/ML uses Anaconda. Hyperledger Fabric, Qdrant, and MinIO run as external/containerized services. The Python core depends on typed adapters, not infrastructure-specific code everywhere.

## Phase work loop
1. Read phase instructions.
2. Inspect current repository state.
3. State implementation plan.
4. Implement smallest complete slice.
5. Add unit tests.
6. Add integration/smoke test.
7. Run checks.
8. Save artifacts.
9. Evaluate acceptance criteria.
10. Update `31_STATUS.md`.
11. Stop unless explicitly told to continue.

## Scientific wording
Never claim:
- blockchain proves semantic truth;
- held-out-family evaluation is true zero-day detection;
- an approximate baseline is an exact reproduction;
- an LLM self-confidence field is a calibrated probability;
- a result is statistically significant without a declared test.
