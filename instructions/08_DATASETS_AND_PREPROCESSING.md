# Phase 1 — Datasets and Leakage-Safe Preprocessing

## Datasets
- CICIoT2023
- Edge-IIoTset

Process/evaluate independently.

## Common interface
Create a `DatasetAdapter` with methods such as:
```text
scan_raw()
validate_schema()
build_raw_manifest()
load_raw()
canonicalize_labels()
create_split()
fit_preprocessor(train)
transform(split)
save_processed()
build_quality_report()
```

## Step 1 — raw manifest
For every raw file store relative path, byte size, SHA-256, row count where readable, columns, and source/acquisition note.

## Step 2 — inspect actual schema
Report numeric/categorical/target/identifier/timestamp columns, constants, all-null fields, NaN/inf, duplicates, and class counts. Never assume a mirror has the same columns as another release.

## Step 3 — leakage audit
Check for scenario IDs, capture IDs, filenames, timestamps, source identifiers, or near-duplicate rows that trivially encode attack labels. Document every dropped/excluded column and why.

## Step 4 — split before fitting transforms
Required order:
```text
canonical raw rows
→ train/validation/test indices
→ fit transforms on train
→ transform train
→ transform validation
→ transform test
```

If flow/session groups exist and random row splits create duplicate leakage, use group-aware splitting and save the group definition.

## Step 5 — preprocessing
Use training-derived only:
- imputation;
- categorical encoding;
- numerical scaling;
- feature ordering;
- any feature selection.

Persist the fitted transformer and hash.

## Step 6 — balancing
Default: class-weighted loss. Never SMOTE before splitting. A baseline-specific resampling method may operate only inside training and must be documented.

## Step 7 — labels
Maintain original label, canonical class, family, binary/multiclass mappings. Save as versioned JSON/YAML.

## Step 8 — held-out protocol
For held-out runs:
- remove entire family from classifier training;
- exclude it from class weights;
- exclude it from calibration fit;
- exclude it from Mahalanobis class statistics;
- keep it in final test evaluation.

Primary hold-outs:
- CICIoT2023: Mirai;
- Edge-IIoTset: Malware.

## Assertions
- no sample ID overlap among splits;
- same feature order across splits;
- no test-derived fitted statistic;
- no unexpected NaN/inf after transforms;
- stable label IDs;
- held-out family absent from forbidden partitions.

## Artifacts
```text
data/manifests/<dataset>/raw_manifest.json
data/manifests/<dataset>/split_manifest_seed*.json
data/manifests/<dataset>/feature_schema.json
data/manifests/<dataset>/label_map.json
artifacts/preprocessors/<dataset>/<hash>.joblib
reports/data_quality/<dataset>.md
```
