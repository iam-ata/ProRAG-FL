# Phase 3 — Confidence Calibration and OOD Gate

## Temperature scaling
Freeze classifier. Collect validation logits/labels and optimize scalar positive T minimizing validation negative log-likelihood:
```text
P_T = softmax(logits/T)
```
Use positive parameterization such as `softplus(raw_T)+eps`.

Save T, NLL before/after, ECE before/after, and fitting config.

## Calibrated confidence
```text
C(x)=max(P_T(y|x))
```
Select `tau_C` from validation only using a predeclared routing objective, such as maintaining a target known-class direct-route recall while controlling unnecessary escalation.

## Mahalanobis OOD
Extract 128-D **training-known** embeddings. Compute class means and a pooled regularized covariance. If covariance is unstable, use a documented shrinkage estimator rather than an arbitrary pseudoinverse.

```text
M(x)=min_c sqrt((h(x)-mu_c)^T Sigma^-1 (h(x)-mu_c))
```

Select `tau_M` through validation only. Never tune with the final held-out family.

## Gate
```python
escalate = confidence < tau_C or mahalanobis > tau_M
```

## Gate evaluation
Known traffic:
- direct-route rate;
- false escalation rate;
- accuracy/F1 of direct decisions.

Held-out experiment:
- escalation recall;
- OOD AUROC/AUPR where valid;
- downstream retrieval/reasoning success.

## Tests
- T positive;
- probabilities normalized;
- fitters cannot consume test split;
- covariance stable/finite;
- scores finite;
- serialized thresholds reproduce identical decisions.
