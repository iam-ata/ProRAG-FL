---
name: benchmark-systems
description: Phase 14 — Benchmark communication, blockchain, RAG and API overhead
---

# Phase 14 — Benchmark communication, blockchain, RAG and API overhead

## Required reading

- `25_SYSTEMS_BENCHMARKS.md`
- `38_DOCKER_AND_INFRASTRUCTURE_SETUP.md`
- `40_RUN_ARTIFACT_SCHEMA.md`

## Execution contract

Measure direct and escalated paths separately with documented warm-up/timing protocol. Record FL bytes/time, Fabric submit/query/verify/throughput/ledger growth, embedding/retrieval/Merkle times, API tokens/latency/cost, RAG invocation rate and end-to-end latency. Record pricing date/source instead of hard-coding permanent API prices.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.
