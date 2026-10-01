# Start Here
Copy `AGENTS.md`, `.agents/`, and `docs/` into the root of the coding repository.

First Antigravity prompt:
> Read AGENTS.md and docs/01_MASTER_EXECUTION_PLAN.md. Do not write research code yet. Invoke /bootstrap-prorag, show the plan and acceptance checks, execute Phase 0 only, and stop after its gate passes.

Then use skills in order:
`/bootstrap-prorag` → `/prepare-datasets` → `/train-centralized-ids` → `/build-federated-learning` → `/build-blockchain-provenance` → `/build-rag-pipeline` → `/build-openai-reasoning` → `/implement-baselines` → `/run-adversarial-tests` → `/run-experiment-matrix` → `/analyze-results` → `/sync-paper-artifacts`.

At each phase ask for a plan before edits and a verification report before moving forward.
