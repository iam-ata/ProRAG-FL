---
name: build-rag-pipeline
description: Phase 7 — Implement BGE-M3/Qdrant hybrid provenance-aware RAG
---

# Phase 7 — Implement BGE-M3/Qdrant hybrid provenance-aware RAG

## Required reading

- `15_HYBRID_RAG.md`
- `14_KNOWLEDGE_INGESTION_AND_MERKLE.md`
- `19_METRICS_AND_STATISTICS.md`

## Execution contract

Implement runtime-visible query construction, BGE-M3 dense+sparse representations, Qdrant indexing, dense/sparse candidate retrieval, RRF fusion, hard source/version/status/Merkle eligibility checks, validation-frozen reranking and verified Top-5 output. Build a retrieval benchmark and measure Precision@K/Recall@K/MRR/Recall@5. Do not call OpenAI yet.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
