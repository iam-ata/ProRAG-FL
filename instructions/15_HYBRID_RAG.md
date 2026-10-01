# Phase 7 — Hybrid Provenance-Aware RAG

## Goal
Retrieve relevant threat evidence while guaranteeing that only eligible, cryptographically verifiable, active knowledge reaches the LLM.

## Query construction
Create query text only from runtime-visible `SecurityEvent` fields: prediction, abnormal-feature descriptions, protocol/device context, time context. Never include ground-truth label.

## BGE-M3
Use a maintained BGE-M3 implementation such as FlagEmbedding for dense and sparse representations. Record exact model identifier/revision and preprocessing settings.

## Qdrant
Index chunk vectors and compact metadata sufficient to filter/verify by source, document ID, version, status and chunk ID. Canonical source-of-truth document remains the versioned object store.

## Hybrid retrieval
1. dense Top-N;
2. sparse Top-N;
3. RRF fusion;
4. retain approximately Top-20 fused candidates.

RRF:
```text
RRF(d) = sum_over_rankers 1/(k + rank_r(d))
```
Store `k` in config.

## Hard provenance filter
For every candidate verify:
1. source allowlisted;
2. ledger record exists;
3. document version active/current;
4. chunk hash valid;
5. Merkle proof valid;
6. not revoked.

Failure on any required check => candidate ineligible. Never let semantic similarity override failure.

## Verified reranking
Only eligible candidates enter reranking. Allowed components after validation tuning:
- normalized RRF;
- freshness;
- independent corroboration.

Example:
```text
Score = lambda1*RRF_norm + lambda2*freshness + lambda3*corroboration
```
Weights are chosen on retrieval validation queries and frozen before final test.

Freshness can use a documented decay such as `exp(-gamma*age_days)`. Corroboration counts independent organizations, not duplicate records from one source.

## Final evidence
Return at most verified Top-5, each carrying evidence ID, source/document/version/chunk, scores, verification record, and text.

## Retrieval benchmark
Build human-reviewed query/support pairs from authoritative CTI. Report Precision@K, Recall@K, MRR and Recall@5/support-hit rate.

## Poisoning tests
Corpus fractions 0/5/10/20/30% for tampering, unauthorized insertion, stale replay, prompt injection, authorized malicious source.

Important limitation: provenance can reject unauthorized/tampered/stale evidence; it cannot prove that a valid authorized source is semantically truthful. Measure that residual risk rather than hiding it.
