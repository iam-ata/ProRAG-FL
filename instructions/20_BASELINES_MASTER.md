# Phase 10 — Baselines Master Protocol

Published methods often differ in task, architecture, privacy assumptions, client count, blockchain design and dataset. Separate **method-faithful reproduction** from **controlled component comparison**.

## Simple controls
### B0 Local 1D-CNN
No collaboration.
### B1 Centralized 1D-CNN
Union of training data; oracle centralized reference.
### B2 FedAvg + 1D-CNN
Plain FL.
### B3 MultiKrum + 1D-CNN
Byzantine-robust aggregation control.
### B4 FedTrimmedAvg + 1D-CNN
Robust aggregation without blockchain provenance.

These controls share the same model/splits whenever possible.

## B5 SFLNID
**Efficient and Privacy-Preserving Network Intrusion Detection Based on Federated Learning in SDN-Enabled IIoT Network**  
IEEE Internet of Things Journal, 2025. DOI `10.1109/JIOT.2025.3591598`.

Verified defining ideas: Focal loss, Wasserstein-distance local/global regularization, adaptive differential privacy with dynamic gradient clipping using Holt exponential smoothing, custom CNN-GRU, non-IID/imbalance focus. Use for FL IDS heterogeneity/privacy-efficiency comparison where reproducible.

## B6 FLOW
**FLOW: A Robust Federated Learning Framework to Defend Against Model Poisoning Attacks in IoT**  
IEEE Internet of Things Journal, 2024. DOI `10.1109/JIOT.2023.3341811`.

Verified defining ideas: cosine-distance behavior among local updates, current + historical information, current-round malicious update elimination, graceful punishment rather than permanent exclusion. Use for poisoning robustness.

## B7 Bc²FL
**Bc²FL: Double-Layer Blockchain-Driven Federated Learning Framework for Agricultural IoT**  
IEEE Internet of Things Journal, 2025. DOI `10.1109/JIOT.2024.3485208`.

Verified defining ideas: double-layer blockchain, two-stage consensus, hierarchical FL, adaptive model aggregation/noise based on model quality. Use as blockchain-FL architectural/system comparator; do not imply agricultural task equivalence to IDS.

## B8 RLFE-IDS
**RLFE-IDS: A framework of Intrusion Detection System based on Retrieval Augmented Generation and Large Language Model**  
Computer Networks, 2025. DOI `10.1016/j.comnet.2025.111341`.

Verified defining ideas: RAG, FE-Net network-traffic embedding, vector database, LLM API classification. Use as primary RAG/LLM IDS comparator.

## B9 LQB-IDS (Huang et al.)
**An adaptive intrusion detection system for the internet of things using large language models and post-quantum-secure blockchain**  
Computer Networks, 2026. DOI `10.1016/j.comnet.2025.111819`.

Verified defining ideas: lightweight known-attack path, LLM unknown-attack analyzer, dual-switch/adaptive learning, LLM-maintained post-quantum-secure blockchain DB, credit-scoring/adaptation. Use as closest high-level LLM+blockchain IDS comparator.

## B10 FedMSE
**FedMSE: Semi-supervised federated learning approach for IoT network intrusion detection**  
Computers & Security, 2025. DOI `10.1016/j.cose.2025.104337`.

Official public repository identified: `dino-chiio/fedmse`. Defining ideas: shrink autoencoder, centroid one-class classifier, semi-supervised FL, unknown/anomaly focus. Particularly relevant to held-out/anomaly comparison.

## B11 pFL-IDS — Thein et al.
**Personalized federated learning-based intrusion detection system: Poisoning attack and defense**  
Future Generation Computer Systems, 2024. DOI `10.1016/j.future.2023.10.005`.

Verified defining ideas: personalized FL, mini-batch logit adjustment, two-phase client cosine-similarity/benign-centroid poisoning defense. Use under non-IID + poisoning.

## Rule
Before final implementation, obtain defining equations/parameters from official code/full paper/supplement. Abstract-level descriptions are not permission to invent details. If details remain missing, mark `approximate_reimplementation` and document assumptions.
