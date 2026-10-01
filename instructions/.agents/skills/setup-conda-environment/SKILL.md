---
name: setup-conda-environment
description: Environment setup — Create and validate the Anaconda environment
---

# Environment setup — Create and validate the Anaconda environment

## Required reading

- `05_ANACONDA_ENVIRONMENT.md`
- `29_SECURITY_PRIVACY_AND_SECRETS.md`

## Execution contract

Use Anaconda/Conda environment `prorag-fl` with Python 3.11. Install the required core, PyTorch, Flower, RAG, OpenAI, crypto, experiment and development dependencies. Verify imports and CUDA availability. Export environment.yml and requirements-lock.txt after the environment is stable. Do not install Fabric/Qdrant/MinIO servers inside Conda.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
