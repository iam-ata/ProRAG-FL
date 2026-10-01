# Phase 9 — End-to-End ProRAG-FL

## Training path
```text
training data
→ client partitions
→ local train
→ update artifact + digest
→ provenance verification
→ eligible updates
→ FedTrimmedAvg(beta=0.20)
→ new global model/version
```

## Inference path
```text
processed event
→ 1D-CNN logits + 128D embedding
→ temperature calibration
→ confidence C
→ Mahalanobis M
→ gate G
```

If G=0: direct IDS decision.  
If G=1:
```text
sanitized SecurityEvent
→ query
→ BGE-M3/Qdrant hybrid retrieval
→ provenance/Merkle filter
→ verified Top-5
→ OpenAI structured reasoning
→ escalated decision
```

## Auditable decision record
Store event pseudonym, model version, classifier prediction, confidence, OOD score, gate reason, route, candidate IDs, rejected IDs/reasons, verified evidence IDs, reasoning model ID, structured result, and latency breakdown. Ground truth lives only in evaluation records, never reasoning input.

## Integration progression
1. all mocks;
2. real model;
3. real Qdrant;
4. real MinIO;
5. real Fabric;
6. real OpenAI only after explicit permission.

## Runtime invariants
- direct high-confidence events do not call RAG/API;
- invalid FL update never reaches aggregator;
- provenance-invalid knowledge never reaches reasoning;
- test label never appears in LLM payload;
- LLM output never self-admits into threat memory.
