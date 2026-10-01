# Full Matrix Planning and Cost Control

Before launching final experiments the agent must expand the configuration matrix and report its size.

## Count runs
Break down by:
- dataset;
- method;
- partition/alpha;
- K;
- attack;
- malicious fraction;
- RAG poison fraction;
- ablation;
- seed.

Avoid accidental combinatorial explosions by running only combinations justified in `23_EXPERIMENT_MATRIX.md`.

## Compute estimate
After one-seed pilots, estimate:
- GPU-hours;
- CPU-hours;
- disk growth;
- Fabric transaction count;
- embedding/index time;
- OpenAI requests/tokens/cost.

This is planning only; do not replace measured final values with estimates.

## OpenAI cost control
Final RAG experiments should cache deterministic retrieval inputs but not fake API outputs. If repeated reasoning on the exact same frozen payload is scientifically intended to measure model nondeterminism, treat it as repeated samples; otherwise avoid accidental duplicate requests.

Before a large API batch:
1. enumerate request count;
2. estimate input/output tokens from pilot;
3. load current pricing into a dated config;
4. show estimated cost;
5. wait for researcher approval.

## Checkpointing/resume
Long matrices must be safely resumable without changing run IDs. Completed runs are not repeated unless an explicit replication design requires it.
