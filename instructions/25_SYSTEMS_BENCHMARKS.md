# Phase 14 — System and Overhead Benchmarks

Record hardware/software versions with every systems run.

## Timing protocol
Use warm-ups and repeated measurements. Synchronize GPU timing when needed. Report mean plus median/p95 where informative. Never mix cold-start and warm-path values without labels.

## Local inference
Measure preprocessing, CNN forward, calibration, OOD, direct total.

## FL
Client train, serialization, communication bytes, provenance verification, aggregation and round time.

## Fabric
Transaction submission, query, verification, endorsement, throughput, payload size, ledger growth.

## RAG
MinIO fetch, BGE embedding/query, Qdrant dense/sparse, RRF, Merkle checks, reranking, final retrieval total.

## OpenAI
Request round-trip, tokens, retries, cost.

Pricing changes. Store pricing input/source/date in config used for cost calculation rather than hardcoding an eternal price in scientific code.

## End-to-end
Report direct-path and escalated-path latency separately.

## RAG invocation rate
```text
RIR = escalated_events / all_events
```
Use it to compute requests/token/cost under the measured experiment workload. Do not extrapolate to production scale without assumptions.
