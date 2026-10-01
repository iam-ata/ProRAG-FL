# Baseline-by-Baseline Implementation Instructions

This file describes the implementation route. Exact paper equations override high-level summaries.

# B0 — Local 1D-CNN
1. Reuse immutable client partitions.
2. Same initialization family/preprocessor/model.
3. Train each client independently.
4. Evaluate per-client and common test where meaningful.
5. Do not aggregate weights.

# B1 — Centralized 1D-CNN
1. Union global training-client indices.
2. Same validation/test.
3. Same architecture/preprocessor.
4. Tune only on validation.
5. Evaluate final frozen checkpoint.

# B2 — FedAvg
1. Same partitions and initialization as proposed method.
2. 2 local epochs.
3. sample-count weighted average.
4. no provenance filtering.
5. same 50 rounds and evaluation.

# B3 — MultiKrum
Before final runs verify from canonical implementation/paper:
- Byzantine-count parameter;
- whether scoring uses updates or full weights;
- selected model count;
- minimum K constraints;
- exact distance and aggregation behavior.

Conceptually flatten update vectors, compute pairwise squared Euclidean distances, score each update using nearest-neighbor distances under Byzantine assumption, select/aggregate according to MultiKrum. Freeze threat parameter before test.

# B4 — FedTrimmedAvg
For each parameter coordinate collect client values, sort, remove lower/upper tails according to library's beta definition, average remainder. Primary beta=0.20. Record exact integer trim count for K=5/10/20 and reject infeasible configurations rather than silently changing beta.

# B5 — SFLNID
## Before coding
Extract from full paper:
- CNN-GRU layer dimensions;
- Focal loss alpha/gamma;
- Wasserstein regularization equation/coefficient;
- DP clipping/noise equations;
- Holt smoothing initialization/coefficients;
- privacy accountant/epsilon/delta;
- FL participation/local epochs/optimizer.

## Modules
- `SFLNIDModel` — native CNN-GRU, not our 1D-CNN.
- `SFLNIDLoss` — exact Focal + Wasserstein term from paper.
- `AdaptiveDPController` — dynamic clipping and noise using paper's Holt mechanism.
- FL trainer/orchestrator matching paper settings where possible.

## Fair use on our datasets
Keep defining algorithm intact; adapt only dataset-specific input/class dimensions. Tune only permitted optimization values on validation and document deviations.

If DP or Wasserstein components are omitted, do **not** call the result full SFLNID; call it `SFLNID-inspired` and do not present it as exact reproduction.

# B6 — FLOW
## Before coding
Extract exact:
- local-update representation;
- cosine-distance matrix;
- current-round malicious decision rule;
- threshold/cluster rule;
- history state update;
- penalty/weight rule;
- recovery rule;
- adaptive-attack setup.

## Suggested classes
- `FlowHistoryState` per client;
- `FlowDetector(current_updates, history)` -> scores/mask;
- `FlowAggregator` applies current rejection/penalty and updates history.

## Sanity test
Synthetic benign vectors cluster; a strong opposite-direction malicious update should produce suspicious behavior under the reproduced criterion. This is a qualitative unit check, not proof of paper-level accuracy.

Do not tune FLOW decision threshold on test ASR.

# B7 — Bc²FL
Bc²FL is Agricultural-IoT oriented. Use one of two explicitly labeled modes:

## Mode A — architecture/system reproduction
Reproduce the double-chain/hierarchical FL control plane and use IDS as workload.

## Mode B — component/system comparison
Compare applicable ledger/coordination/aggregation overhead without claiming complete Bc²FL reproduction.

Before implementation extract:
- responsibilities of each blockchain layer;
- two-stage consensus;
- hierarchy topology;
- adaptive aggregation equation;
- model-quality scoring;
- noise/privacy adaptation;
- chain parameters.

Keep it isolated in baseline namespace. If only one chain or subset is implemented, mark approximate and say exactly what is missing.

# B8 — RLFE-IDS
## Defining components
FE-Net + vector knowledge database + retrieval + LLM classification.

## Before coding
Extract:
- FE-Net architecture/objective;
- network-feature representation;
- similarity/search method;
- retrieved K;
- prompt format;
- LLM settings;
- dataset preprocessing and knowledge population rules.

## Preferred faithful implementation
Implement FE-Net and an independent RLFE index. Populate only with training/allowed knowledge—never final test rows.

## Controlled component comparison
Separately compare `standard hybrid RAG without provenance` using our corpus. Do not label that controlled ablation RLFE-IDS unless it actually matches RLFE.

# B9 — LQB-IDS
Before coding extract:
- lightweight detector/DCAE architecture;
- known/unknown switch rule;
- dual-switch/adaptation loop;
- knowledge distillation;
- LLM input/prompt;
- post-quantum blockchain mechanism;
- credit score;
- adaptive update procedure.

Because LQB-IDS is not the same FL task, compare only supported dimensions. Use `N/A` for unsupported FL metrics rather than forcing artificial equivalents.

If post-quantum blockchain cannot be faithfully reproduced, the paper may remain an architectural literature comparator rather than a measured baseline. Do not fabricate a “simplified LQB-IDS” result without clear approximate labeling.

# B10 — FedMSE
## Preferred route
Use official repository if license permits. Pin commit and record dependencies/config/data preparation.

Public repo structure has included Data/Notebook/src with checkpoint, configuration, data loader, evaluator, model, trainer and utilities. Inspect the pinned version rather than relying on memory.

## Integration
1. vendor/submodule official source if appropriate;
2. keep vendor changes explicit/patch-based;
3. create wrapper converting our train split into expected input;
4. run native SAE/centroid one-class method;
5. parse output into common metrics.

FedMSE may output anomaly/normal rather than attack-family labels. Report `N/A` for unsupported family-identification metrics. It is especially useful for held-out anomaly detection.

# B11 — pFL-IDS (Thein et al.)
Before final implementation extract exact:
- mini-batch logit-adjustment equation and priors;
- personalization mechanism;
- precomputed-global-model construction;
- first/second cosine-similarity phases;
- benign centroid;
- malicious threshold;
- aggregation restriction.

Suggested modules:
- `LogitAdjustedLoss`;
- `PersonalizedClientTrainer`;
- `TwoPhaseSimilarityDefense`;
- `PFLIDSAggregator`.

Use particularly for alpha=0.3/0.1 poisoning experiments. Report global/personalized metrics exactly as supported by the method.

# Universal baseline completion
Each baseline requires:
- fidelity card;
- smoke test;
- common metrics adapter;
- immutable config;
- source/version record;
- documented deviations;
- no test-driven tuning.
