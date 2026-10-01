---
name: build-knowledge-provenance
description: Phase 6 — Build threat-knowledge ingestion and Merkle provenance
---

# Phase 6 — Build threat-knowledge ingestion and Merkle provenance

## Required reading

- `14_KNOWLEDGE_INGESTION_AND_MERKLE.md`
- `39_CTI_SOURCE_ACQUISITION.md`
- `13_BLOCKCHAIN_AND_MODEL_PROVENANCE.md`

## Execution contract

Create common KnowledgeDocument/KnowledgeChunk schemas, deterministic canonicalization/chunking, SHA-256 Merkle trees and proofs, MinIO versioned canonical storage, knowledge ledger records, version/revocation semantics, and source adapters. Implement one authorized source end-to-end first. A modified chunk must fail verification.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
