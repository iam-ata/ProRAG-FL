# Baseline Source Notes

These are verified high-level method facts used to shape implementation planning. They are **not** a substitute for the full paper/code before final reproduction.

## SFLNID
DOI `10.1109/JIOT.2025.3591598`. High-level verified: Focal loss, Wasserstein local/global regularization, adaptive DP, dynamic gradient clipping with Holt exponential smoothing, CNN-GRU; evaluated on ToN-IoT, RT-IoT and Edge-IIoT.

## FLOW
DOI `10.1109/JIOT.2023.3341811`. High-level verified: cosine distances among local updates, current/historical training behavior, current-round malicious update elimination, graceful punishment rather than permanent exclusion; targeted/untargeted/adaptive poisoning focus.

## Bc²FL
DOI `10.1109/JIOT.2024.3485208`. High-level verified: double-layer blockchain, two-stage consensus, hierarchical FL, adaptive aggregation/noise tied to model quality; Agricultural IoT domain.

## RLFE-IDS
DOI `10.1016/j.comnet.2025.111341`. High-level verified: RAG, FE-Net traffic embedding, vector knowledge DB, API LLM classification, multiple benchmark datasets/real-network deployment.

## LQB-IDS
DOI `10.1016/j.comnet.2025.111819`. High-level verified: lightweight known-attack detector, LLM unknown-attack analyzer, adaptive/dual-switch learning, post-quantum-secure blockchain DB and credit-scoring/adaptation.

## FedMSE
DOI `10.1016/j.cose.2025.104337`. High-level verified: semi-supervised FL, Shrink Autoencoder, centroid one-class classifier; public repo identified as `dino-chiio/fedmse`.

## pFL-IDS
DOI `10.1016/j.future.2023.10.005`. High-level verified: personalized FL IDS, mini-batch logit adjustment, two-phase cosine-similarity/benign-centroid poisoning defense.

## Mandatory rule
The IDE agent must inspect official code/full paper for exact equations, layer sizes, thresholds and hyperparameters before final baseline runs. Never convert these summaries into invented implementation details.
