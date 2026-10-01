# Phase 16 — Results Pipeline and Manuscript Synchronization

## Source of truth
Consume only completed immutable run artifacts. Never read numerical values back from manuscript prose/screenshots/manual spreadsheets.

## Master outputs
Generate:
```text
reports/results_master.parquet
reports/results_master.csv
```
Each record should identify run ID, dataset, seed, method, partition, attack, ratios, metrics and system measurements.

## Generated paper artifacts
Scripts generate, not hand-type:
```text
reports/paper_exports/
├── table_setup.tex
├── table_main_ids.tex
├── table_fl_poisoning.tex
├── table_unseen_attack.tex
├── table_rag_poisoning.tex
├── table_ablation.tex
├── table_overhead.tex
├── figures/
└── claims.json
```

## Claims traceability
`claims.json` maps every quantitative statement to run IDs, metric and aggregation. Example:
```json
{
  "claim_id": "RQ2_C01",
  "metric": "macro_f1",
  "comparison": ["ProRAG-FL", "FLOW"],
  "source_runs": [],
  "aggregation": "mean_of_fixed_5_seeds"
}
```

## Manuscript boundary
Manuscript is `../Manuscript/`. Generate artifacts under Code first. Only an explicit synchronization command, after researcher approval, copies tables/figures to the manuscript.

Do not auto-rewrite scientific narrative without review.

## Abstract/conclusion
Quantitative values enter only after final five-seed runs and analysis. Do not use preliminary/smoke values.

## Wording guardrails
Do not write:
- true zero-day for held-out known CTI;
- blockchain guarantees truth;
- statistically significant without a test;
- real-time without defined measured latency criterion;
- privacy-preserving beyond actual implemented guarantees.
