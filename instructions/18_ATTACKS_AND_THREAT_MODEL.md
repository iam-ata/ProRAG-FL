# Phase 11 — Threat Model and Adversarial Scenarios

## Actors
### Malicious FL client
Can poison local labels/training/update but cannot forge another valid organization identity under the base model.

### Replay/network adversary
Can replay previously valid signed artifacts/stale versions.

### Knowledge-store adversary
Can modify off-chain content or attempt unauthorized insertion.

### Prompt-injection author
Can insert malicious natural-language instructions into knowledge.

### Authorized malicious source
Has valid provenance but provides misleading semantic content. This is a residual risk: provenance != truth.

# FL attacks

## Label flipping
Implement config-driven targeted and untargeted variants. Untargeted replaces a configured fraction with deterministic non-original labels; targeted maps source -> target. Record clients, poison fraction, mapping, seed.

## Untargeted update poisoning
Use a clearly named perturbation (e.g. sign-flip/scaled sign-flip) with fixed equation/strength in config. Do not call an arbitrary noise function “the poisoning attack.”

## Model replacement
Implement according to a cited standard formulation. Extract the scaling equation before final runs and freeze it; never adjust after seeing defense results.

## Backdoor
For tabular traffic, define a deterministic trigger on selected modifiable features using training-distribution quantiles/domain rationale. Poison only malicious-client training samples and target a configured class. Create a triggered copy of eligible clean test samples. Report clean performance + ASR + trigger/target definition.

# Provenance attacks
- changed update after hash registration;
- duplicate nonce;
- stale round;
- wrong global version;
- unauthorized identity;
- revoked status.
Expected: reject before aggregation.

# Knowledge attacks
## Post-ingestion tampering
Change chunk bytes after anchoring; Merkle verification must fail.

## Unauthorized insertion
High-similarity content without valid allowlisted provenance must fail hard gate.

## Stale replay
Old document version when newer active version exists must fail version/status eligibility.

## Prompt injection
Embedded instructions attempt to override system policy, force label, leak data, or call tools.

## Authorized malicious source
Cryptographically valid but semantically harmful evidence tests limitation/corroboration.

# RAG-trigger amplification
Construct bounded stress traffic that raises low-confidence/OOD routing. Measure invocation rate, queue/API latency, requests and cost. Do not generalize a synthetic stress test into a universal DoS claim.

# Attack validation
Every attack requires:
1. transformation unit test;
2. positive control demonstrating attack effect where feasible;
3. defense test;
4. immutable attack config;
5. saved malicious-client/item manifest.
