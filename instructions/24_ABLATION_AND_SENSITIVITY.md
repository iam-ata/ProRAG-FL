# Phase 13 — Ablation and Sensitivity

## Main ladder
- **A0** FedAvg + 1D-CNN.
- **A1** FedTrimmedAvg + 1D-CNN.
- **A2** blockchain/provenance-gated FedTrimmedAvg.
- **A3** A2 + ordinary hybrid RAG without knowledge provenance.
- **A4** A2 + hard provenance RAG without freshness/corroboration reranking.
- **A5** full provenance/retrieval but disable selective OOD/confidence routing (broad/all-event RAG according to a fixed policy) to quantify cost/latency and routing value.
- **A6** full ProRAG-FL.

A5 is a routing/cost ablation, not a claim that invoking RAG everywhere is desirable.

## Sensitivity
Validation-only grids:
- beta around 0.20, e.g. 0.10/0.15/0.20/0.25 where K permits;
- confidence threshold across validation confidence distribution;
- Mahalanobis threshold/quantiles;
- retrieval candidate/final K;
- rerank weights on a simplex/grid.

## Freeze
Write selected values to `artifacts/frozen_parameters/<dataset>/<hash>.yaml`. Final test code must refuse tuning flags.

## Reporting
Show performance, attack resilience, RAG invocation and latency where relevant. Do not choose settings on a single favorable metric without declaring the objective.
