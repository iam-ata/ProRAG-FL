# Troubleshooting and Stop Conditions

## Dataset mismatch
Print actual schema and stop if mapping ambiguity affects labels/features. Never invent missing columns.

## CUDA OOM
For smoke/debug, reducing batch size is allowed and must be logged. Do not silently change model architecture. Final resource settings must be documented consistently.

## Flower/Windows issue
Use a supported local mode, WSL2 or compatible environment. Do not switch the scientific framework without approval.

## Fabric failure
Isolate Docker/network vs chaincode vs adapter. Mock backend may keep unit development moving, but mock results are never reported as blockchain performance.

## Qdrant/MinIO unavailable
In-memory/filesystem adapters are allowed for unit tests only. Final architecture/system experiments require real services or explicitly approved equivalent.

## OpenAI failure
Do not silently switch models. Preserve failed run and retry under policy.

## Missing baseline detail
Record in fidelity card; obtain full paper/official code. If unresolved, mark approximate and request approval.

## Poor test result
Do not retune on test. Investigate only genuine bugs. Negative scientific results remain valid.

## Run inconsistency
Compare split/config hashes, seeds, checkpoint, environment and dependency versions. Never aggregate incomparable runs.
