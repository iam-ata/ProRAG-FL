# Antigravity Rules and Skills

This folder provides the operational layer for the detailed ProRAG-FL instructions.

## Rules

Rules are persistent constraints for research integrity, method fidelity, leakage prevention, baseline fidelity, engineering, secrets, reproducibility, manuscript boundaries and run immutability.

## Skills

Skills map directly to the project phases. Each skill points back to the detailed numbered Markdown files; the numbered files remain the authoritative explanation.

Suggested order:

```text
/setup-conda-environment
/bootstrap-prorag
/prepare-datasets
/train-local-ids
/calibrate-ood
/build-federated-learning
/build-model-provenance
/build-knowledge-provenance
/build-rag-pipeline
/build-openai-reasoning
/integrate-prorag
/implement-baselines
/run-adversarial-tests
/run-experiment-matrix
/run-ablation-sensitivity
/benchmark-systems
/analyze-results
/sync-paper-artifacts
/final-reproducibility-audit
```

Because the researcher keeps this entire control pack inside `Code/instructions/`, do not relocate it automatically.
