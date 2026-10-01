# Frozen Scientific Decisions — Quick Reference

| Item | Decision |
|---|---|
| Datasets | CICIoT2023 + Edge-IIoTset, separate |
| Local model | PyTorch 1D-CNN |
| Channels | 64,128,256 |
| Embedding | 128-D |
| Dropout | 0.30 |
| Optimizer | AdamW |
| LR | 1e-3 |
| Weight decay | 1e-4 |
| Batch | 256 |
| FL | Flower |
| Primary K | 10 |
| Scalability K | 5,10,20 |
| Rounds | 50 |
| Local epochs | 2 |
| non-IID | Dirichlet 1.0,0.5,0.3,0.1 |
| Seeds | 13,37,73,101,211 |
| Proposed aggregator | FedTrimmedAvg |
| beta | 0.20 |
| FL trust | hard provenance before aggregation |
| Blockchain | Hyperledger Fabric 2.5 LTS-compatible target |
| Consortium | 3 orgs / 3 peers |
| Ordering | 3-node Raft |
| Incident admission | 2-of-3 endorsements |
| Canonical knowledge | MinIO |
| Vector store | Qdrant |
| Retrieval | BGE-M3 dense+sparse + RRF |
| Initial candidates | Top-20 |
| Final evidence | verified Top-5 |
| Knowledge proof | Merkle root on-chain + chunk proofs |
| RAG trigger | calibrated confidence OR Mahalanobis OOD |
| OpenAI | env-configured structured reasoning |
| Tools in controlled LLM run | disabled |
| CICIoT hold-out | Mirai |
| Edge-IIoT hold-out | Malware |
| Malicious clients | 0,10,20,30,40% |
| RAG poison | 0,5,10,20,30% |
| FL attacks | label flip, untargeted, replacement, backdoor |
| RAG attacks | tamper, unauthorized, stale, prompt injection, malicious authorized source |
| Claim | unseen-to-model, not zero-day |
