---
trigger: always_on
description: Research integrity, result provenance, and anti-fabrication rules for all ProRAG-FL work.
---

# Research Integrity

- Never fabricate metrics, logs, latency, cost, dataset values, attack results, or baseline outcomes.
- Every paper-facing number must trace to a saved run ID.
- Preserve per-seed raw values before aggregation.
- Never cherry-pick the best seed.
- Never discard a legitimate bad result.
- Do not claim a baseline is reproduced unless its fidelity card supports that statement.
- Distinguish `official`, `faithful_reimplementation`, and `approximate_reimplementation`.
- Do not use final test data for tuning.
- Do not describe held-out known CTI as globally unknown zero-day knowledge.
- Blockchain proves provenance/integrity under the threat model; it does not prove factual truth.
- LLM-generated text is not automatically trusted threat intelligence.
- If a run fails due to infrastructure, preserve the failed artifact and retry under an explicit retry record.
