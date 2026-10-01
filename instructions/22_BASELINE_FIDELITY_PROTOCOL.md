# Baseline Fidelity Protocol

Before final run create `reports/baseline_fidelity/<name>.md` with:

```markdown
# Baseline Fidelity Card — NAME
## Citation
Title / authors / venue / year / DOI
## Source code
Official repo / commit/tag / license / access date
## Defining components
## Original datasets and task
## Original preprocessing
## Original model
## Original FL/threat settings
## Parameters explicitly stated
| parameter | value | paper section/page/source |
## Missing/ambiguous details
## Our implementation
## Deviations
| item | original | ours | reason | expected impact |
## Fidelity
official | faithful_reimplementation | approximate_reimplementation
## Validation
smoke/tests/qualitative reproduction
## Allowed manuscript wording
```

### Official
Authors' official code, pinned, with only transparent adapters/patches.

### Faithful reimplementation
No official code but defining method sufficiently specified and recreated.

### Approximate
Material algorithm/system details missing or infeasible to reproduce exactly.

Forbidden: calling an approximate version “official,” “exact,” or comparing our result directly with authors' reported number as if settings were identical.
