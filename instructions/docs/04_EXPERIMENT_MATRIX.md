# Frozen Experiment Matrix
Seeds: `13,37,73,101,211`. Datasets run independently.

E1 Local/central sanity: Local 1D-CNN, Centralized 1D-CNN. Metrics: macro-F1, balanced accuracy, precision, recall, FPR, AUROC where valid, per-class recall.

E2 FL heterogeneity: FedAvg, MultiKrum, FedTrimmedAvg, proposed FL path, selected FL baselines. K=10. IID + alpha={1.0,0.5,0.3,0.1}.

E3 Scalability: K={5,10,20}; report macro-F1, round time, communication, convergence, provenance overhead.

E4 Malicious clients: ratio={0,10,20,30,40%}; attacks label flipping, untargeted poisoning, model replacement, backdoor. Compare FedAvg, MultiKrum, FedTrimmedAvg, FLOW, proposed path, Thein where compatible. Metrics clean macro-F1, ASR/backdoor-ASR, malicious-update acceptance, rejection, convergence.

E5 Provenance attacks: tampered update, replay, stale round, wrong model version, invalid signature, duplicate nonce. Expected hard rejection.

E6 Unseen-to-model: CICIoT2023 hold out Mirai; Edge-IIoTset hold out Malware. Measure escalation recall → retrieval Recall@5/MRR → evidence correctness → final family identification → latency. Compare FL-only, FedMSE, standard RAG, RLFE-IDS, full ProRAG-FL.

E7 RAG poisoning: malicious corpus ratio={0,5,10,20,30%}; post-ingestion modification, unauthorized insertion, stale replay, prompt injection, authorized-malicious source. Compare standard hybrid RAG, hard provenance RAG, full provenance+freshness/corroboration, RLFE-IDS where compatible.

E8 Ablation: A0 FedAvg; A1 FedTrimmedAvg; A2 blockchain-gated FedTrimmedAvg; A3 FL+standard hybrid RAG; A4 hard provenance RAG without freshness/corroboration; A5 full without OOD gate; A6 full.

E9 Systems: FL bytes/time, provenance verify, Fabric transaction latency/throughput/ledger growth, MinIO, embedding, retrieval, Merkle, API tokens/latency/cost, RAG invocation rate, total latency.

E10 Sensitivity uses validation only: beta, confidence threshold, Mahalanobis threshold, Top-K, retrieval weights. Freeze before test evaluation.
