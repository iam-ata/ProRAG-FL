# Run Artifact Schema

Every final experiment has its own immutable directory:

```text
runs/<run_id>/
├── config.resolved.yaml
├── environment.json
├── dataset_manifest_ref.json
├── split_manifest_ref.json
├── client_partition_ref.json        # FL when applicable
├── corpus_manifest_ref.json         # RAG when applicable
├── metrics.json
├── metrics_per_class.csv
├── timings.json
├── communication.json               # FL when applicable
├── provenance_events.jsonl          # provenance experiments
├── retrieval_events.jsonl           # RAG experiments
├── reasoning_events.jsonl           # sanitized metadata only
├── stdout.log
├── stderr.log
├── artifact_manifest.json
└── DONE | FAILED
```

## `metrics.json`
Use a versioned schema. Include metric definitions/version, not only values.

## Event logs
Event logs must use pseudonymous IDs and avoid raw secrets/payloads. Separate ground-truth evaluation labels from data sent to reasoning.

## Artifact manifest
List produced artifacts with SHA-256, byte size and semantic role.

## DONE marker
Create only after all expected outputs validate. A process exit code of zero alone is not enough.

## FAILED marker
Include structured failure stage/reason. Never delete automatically.

## Aggregation eligibility
The results aggregator consumes only runs with valid DONE marker, matching schema version and complete manifest. Failed/incomplete runs appear in a missing-run report.
