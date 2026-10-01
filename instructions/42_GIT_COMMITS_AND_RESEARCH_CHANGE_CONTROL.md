# Git, Commits, and Research Change Control

## Why
A paper result must be traceable to the exact code/config that created it.

## Branch discipline
Use understandable branches, e.g.:
- `phase/data`;
- `phase/fl`;
- `phase/rag`;
- `experiment/final-v1`.

The researcher may choose another workflow; traceability is the requirement.

## Commit before final matrix
Before final experiments:
1. tests green;
2. configs frozen;
3. commit code;
4. record commit hash in every run.

Do not run a final five-seed matrix from a dirty working tree unless there is a documented reason. Prefer refusing final mode when uncommitted scientific-code changes exist.

## Research-impacting change
Any change to preprocessing, model, attack, aggregation, thresholds, retrieval, prompt, metric or baseline implementation after final runs invalidates affected runs and requires new run IDs.

Cosmetic reporting changes that do not alter values do not invalidate runs.

## Tags
Consider tagging frozen milestones such as:
- `v0-data-freeze`;
- `v0-method-freeze`;
- `v1-final-experiments`.

## Manifest
Paper-export metadata should include the final Git commit/tag used for each table/figure.
