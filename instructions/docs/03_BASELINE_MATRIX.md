# Baseline Matrix and Reproduction Rules
Create `reports/baseline_fidelity/<baseline>.md` before implementing each published method. Record paper/DOI, official code and commit if available, original architecture, our configuration, missing details, deviations, fidelity class, and reason.

## Controls
B0 Local 1D-CNN — no collaboration.
B1 Centralized 1D-CNN — oracle centralized reference.
B2 FedAvg + same 1D-CNN — base FL control.
B3 MultiKrum + same 1D-CNN — robust aggregation.
B4 FedTrimmedAvg + same 1D-CNN — isolates provenance contribution.

## Primary research baselines
B5 SFLNID — federated IIoT IDS; use for IID/non-IID IDS and comparable overhead.
B6 FLOW — poisoning-resilient IoT FL; use for malicious-client/poisoning experiments.
B7 Bc²FL — blockchain-driven FL; use for blockchain/FL system and overhead comparisons; do not import agricultural assumptions unnecessarily.
B8 RLFE-IDS — RAG+LLM IDS; primary standard-RAG comparator using the same evidence corpus where possible.
B9 Huang et al. adaptive LLM+blockchain IoT IDS — closest architectural comparator.

## Secondary
B10 FedMSE — semi-supervised/unknown anomaly comparator.
B11 Thein et al. personalized FL poisoning defense — non-IID+poisoning comparator.

Fairness: identical splits/seeds/preprocessing when scientifically compatible. Preserve a baseline's native architecture if required. Never silently guess missing hyperparameters; mark assumptions and never tune them on test results.
