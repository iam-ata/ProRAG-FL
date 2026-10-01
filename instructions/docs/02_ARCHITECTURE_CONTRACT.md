# Architecture Contract
Fast path: `traffic → preprocessing → 1D-CNN → calibrated confidence + Mahalanobis OOD`. High confidence/in-distribution returns direct IDS result. Otherwise build sanitized event and invoke RAG.

FL path: `local train → signed update → hard provenance gate → eligible updates → FedTrimmedAvg → global model`.
Provenance checks identity/signature/hash/round/model version/nonce/status; it does not determine statistical benignness.

Knowledge path: `source → canonical MinIO object → chunks → Merkle tree → root on-chain → BGE-M3/Qdrant index`.
Retrieval: dense+sparse Top-20 → RRF → source/status/version/Merkle validation → hard exclusion of invalid chunks → freshness/corroboration rerank → Top-5.

Reasoning input: sanitized event + verified Top-5 only. Output fields: attack_family, mitre_techniques, evidence_ids, evidence_sufficient, reasoning_summary, recommended_action. No web/file/tools in controlled experiments.

Threat-memory admission: authoritative allowlist OR sanitized incident + verified evidence + 2-of-3 org endorsement. LLM output alone never suffices.
