# ProRAG-FL — Final Antigravity Instruction Pack

## Project identity
**Paper:** ProRAG-FL: Blockchain-Anchored Provenance-Aware Retrieval-Augmented Federated Intrusion Detection for Cloud–IoT Systems  
**Target:** IEEE Internet of Things Journal

The researcher has fixed this layout:

```text
ProRAG-FL/
├── Code/
│   └── instructions/   # ALL instruction Markdown files stay here
└── Manuscript/         # LaTeX manuscript, bibliography, figures and tables
```

Do not move the instruction files. Work under `Code/`; the paper is a sibling at `../Manuscript/`.

## First IDE prompt

> Work inside `Code/`. All project instructions are intentionally stored in `instructions/`; do not move them. Read `instructions/00_READ_ME_FIRST.md`, `01_MASTER_AGENT_CONTRACT.md`, `02_LOCKED_PROPOSED_METHOD.md`, `03_SYSTEM_ARCHITECTURE.md`, `04_REPOSITORY_STRUCTURE.md`, `05_ANACONDA_ENVIRONMENT.md`, and `06_EXECUTION_ROADMAP.md`. Inspect the workspace, show the Phase 0 plan and acceptance criteria, execute Phase 0 only, update `instructions/31_STATUS.md`, and stop.

## Phase order

```text
0  Bootstrap and reproducibility foundation
1  Dataset ingestion/preprocessing
2  Local + centralized IDS
3  Calibration + OOD routing
4  Federated learning
5  Blockchain/model-update provenance
6  Threat-knowledge ingestion + Merkle provenance
7  Hybrid RAG
8  OpenAI structured reasoning
9  End-to-end ProRAG-FL integration
10 Published/simple baselines
11 Adversarial scenarios
12 Final experiment matrix
13 Ablations + sensitivity
14 System/overhead benchmarks
15 Statistics and analysis
16 IEEE table/figure export
17 Final reproducibility audit
```

## Completion rule
A phase is complete only when implementation, tests, artifacts, acceptance checks, and status documentation all pass. “It runs” is not enough.

---

# Antigravity control layer

This final pack also contains:

```text
instructions/AGENTS.md
instructions/.agents/rules/
instructions/.agents/skills/
```

`AGENTS.md` is the operational master contract and the numbered files are the detailed scientific specifications.

The `.agents/skills/` directory contains one skill for each implementation phase plus Conda environment setup.

The `.agents/rules/` directory contains persistent research-integrity, leakage, method-lock, baseline-fidelity, security and reproducibility rules.

Keep these files inside `instructions/` as specified by the researcher.
