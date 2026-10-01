# ProRAG-FL — Antigravity Master Agent Instructions

You are implementing the research system described in this folder for the IEEE Internet of Things Journal manuscript:

**ProRAG-FL: Blockchain-Anchored Provenance-Aware Retrieval-Augmented Federated Intrusion Detection for Cloud–IoT Systems**

This file is the operational entry point. The detailed scientific specification remains in the numbered Markdown files in this same `instructions/` directory.

## Project layout is fixed

```text
ProRAG-FL/
├── Code/
│   └── instructions/
│       ├── AGENTS.md
│       ├── .agents/
│       │   ├── rules/
│       │   └── skills/
│       └── numbered specification files
└── Manuscript/
```

Do not move the instruction pack unless the researcher explicitly asks.

Actual source code, datasets, configs, tests, services, runs and reports are created as siblings of `instructions/` under `Code/`, according to `04_REPOSITORY_STRUCTURE.md`.

## Required reading order before any implementation

Read:

1. `00_READ_ME_FIRST.md`
2. `01_MASTER_AGENT_CONTRACT.md`
3. `02_LOCKED_PROPOSED_METHOD.md`
4. `03_SYSTEM_ARCHITECTURE.md`
5. `04_REPOSITORY_STRUCTURE.md`
6. `05_ANACONDA_ENVIRONMENT.md`
7. `06_EXECUTION_ROADMAP.md`
8. the phase-specific instruction file(s)
9. the relevant rule files under `.agents/rules/`

## Scientific contract

The proposed method is frozen unless the researcher approves a deviation.

Core method:

```text
CICIoT2023 / Edge-IIoTset
        ↓
Leakage-safe preprocessing
        ↓
1D-CNN IDS (64→128→256, 128-D embedding)
        ↓
Temperature calibration + Mahalanobis OOD
        ↓
Selective direct/RAG gate
```

Federated path:

```text
Flower clients
→ signed/versioned model update
→ hard blockchain provenance gate
→ FedTrimmedAvg(beta=0.20)
→ new global model
```

Knowledge path:

```text
Authorized CTI / endorsed incident
→ MinIO canonical object
→ deterministic chunks
→ Merkle tree
→ root anchored in Hyperledger Fabric
→ BGE-M3 dense+sparse representations
→ Qdrant
→ RRF Top-20
→ hard provenance/Merkle/version/status filter
→ verified Top-5
→ OpenAI structured reasoning
```

Never reinterpret blockchain provenance as semantic truth.

Never call held-out-family evaluation true zero-day detection. Use **unseen-to-model attack identification**.

## Environment

The researcher uses **Anaconda/Conda** with environment name:

```text
prorag-fl
```

Target Python: **3.11**.

Read `05_ANACONDA_ENVIRONMENT.md` before installing or changing dependencies.

Do not create a repository-local venv unless explicitly requested.

## Experiment integrity

Never fabricate numbers or manually write experimental results.

Every result must trace to an immutable run artifact.

Never tune on final test data.

Never use held-out attack samples to fit classifier calibration or OOD statistics.

Never substitute a failed baseline implementation with an invented approximation without documenting it.

## Baseline rules

Before implementing published baselines, read:

- `20_BASELINES_MASTER.md`
- `21_BASELINE_IMPLEMENTATION_DETAILS.md`
- `22_BASELINE_FIDELITY_PROTOCOL.md`
- `37_BASELINE_SOURCE_NOTES.md`

Required controls:

- Local 1D-CNN
- Centralized 1D-CNN
- FedAvg
- MultiKrum
- FedTrimmedAvg

Primary published baselines:

- SFLNID
- FLOW
- Bc²FL
- RLFE-IDS
- LQB-IDS / Huang et al.

Secondary:

- FedMSE
- pFL-IDS / Thein et al.

Before final implementation of a published baseline, inspect its full paper and official code when available. Create a fidelity card first.

## Phase execution rule

Every phase follows:

1. inspect current state;
2. read the matching skill and detailed MD files;
3. state a short plan;
4. implement the smallest complete slice;
5. add tests;
6. run tests;
7. create required artifacts;
8. verify acceptance gate;
9. update `31_STATUS.md`;
10. stop unless the researcher requests the next phase.

Do not jump directly to the full experiment matrix.

## Fixed seeds

```text
13, 37, 73, 101, 211
```

## Manuscript boundary

The LaTeX manuscript is stored in:

```text
../../Manuscript/
```

relative to this instructions folder.

Normal coding phases must not modify it.

Only the paper-export/sync phase may copy generated tables or figures after results are verified.

## Required status report after every substantive task

Report:

- files created/changed;
- commands executed;
- tests passed/failed;
- artifacts produced;
- assumptions/deviations;
- unresolved blockers;
- next exact step.

If an important scientific detail is uncertain, stop and document the uncertainty instead of guessing.
