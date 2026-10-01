# Metrics and Statistical Analysis

## IDS
Primary: Macro-F1, balanced accuracy, macro precision, macro recall, FPR, per-class recall. AUROC/AUPR only with explicit binary/multiclass definition.

FPR must be defined. For multiclass distinguish one-vs-rest macro FPR from operational benign-vs-attack FPR.

## FL robustness
Clean/attacked Macro-F1, attack success, backdoor ASR, malicious-update acceptance/rejection, benign false rejection, convergence.

## Calibration/OOD
NLL, ECE, optional Brier score, OOD AUROC/AUPR where valid, escalation recall, false escalation, RAG invocation rate.

## Retrieval
Precision@K, Recall@K, MRR, Recall@5/support hit, poisoned retrieval, provenance rejection.

## LLM reasoning
Structured family accuracy/recall, evidence-ID validity, unsupported-reference rate, evidence-sufficiency correctness when labeled, prompt-injection success. Use “faithfulness” only with a fully specified evaluator.

## Systems
Bytes, training/aggregation time, blockchain latency/throughput/ledger growth, embedding/retrieval/Merkle latency, API tokens/latency/cost, end-to-end direct and escalated latency.

## Seeds
`13, 37, 73, 101, 211`. Store all raw values. Main reporting is mean ± standard deviation.

## Statistical caution
N=5 independent seeds is small. Prefer transparent per-seed values, effect sizes and descriptive uncertainty. If using paired tests, state test, N, pairing and multiple-comparison correction. Do not overuse “significant.”

## No cherry-picking
Never report only best seed. Never remove a valid low-performing run. Rerun only genuine infrastructure failures under a documented retry policy.
