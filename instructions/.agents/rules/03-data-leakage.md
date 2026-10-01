---
trigger: model_decision
description: Applies whenever reading, splitting, transforming, balancing, partitioning or tuning on datasets.
---

# Leakage Prevention

Required sequence:

```text
raw data
→ immutable split
→ fit preprocessing on training only
→ transform validation/test
→ build FL client partitions from training only
```

Never:
- scale before split;
- encode categories using test-derived categories/statistics without a frozen unknown-category policy;
- feature-select on all data;
- oversample before split;
- tune thresholds on final test;
- use held-out Mirai/Malware examples to fit temperature or Mahalanobis statistics;
- regenerate different FL partitions for competing methods.

Persist split and partition manifests and assert non-overlap in tests.
