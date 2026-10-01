# Repository Structure

Keep the researcher's top-level layout exactly:

```text
ProRAG-FL/
├── Code/
│   └── instructions/
└── Manuscript/
```

Phase 0 should expand `Code/` to:

```text
Code/
├── instructions/
├── pyproject.toml
├── environment.yml
├── requirements-lock.txt
├── .env
├── .env.example
├── .gitignore
├── configs/
│   ├── datasets/
│   ├── models/
│   ├── federated/
│   ├── blockchain/
│   ├── rag/
│   ├── openai/
│   ├── attacks/
│   ├── baselines/
│   └── experiments/
├── data/
│   ├── raw/CICIoT2023/
│   ├── raw/EdgeIIoTset/
│   ├── interim/
│   ├── processed/
│   └── manifests/
├── src/prorag_fl/
│   ├── schemas/
│   ├── data/
│   ├── models/
│   ├── calibration/
│   ├── ood/
│   ├── federated/
│   ├── provenance/
│   ├── blockchain/
│   ├── knowledge/
│   ├── rag/
│   ├── reasoning/
│   ├── threat_memory/
│   ├── attacks/
│   ├── baselines/
│   ├── evaluation/
│   ├── reporting/
│   └── utils/
├── services/
│   ├── fabric/
│   ├── qdrant/
│   └── minio/
├── scripts/
├── tests/{unit,integration,smoke,regression}/
├── runs/
├── artifacts/
├── checkpoints/
└── reports/{data_quality,baseline_fidelity,tables,figures,statistics,paper_exports}/
```

## Manuscript boundary
Normal coding phases do not edit `../Manuscript/`. Phase 16 exports verified artifacts only after explicit approval.

## Git policy
Track code/config/tests/small manifests. Ignore raw/interim/processed datasets, `.env`, checkpoints, runs, large artifacts, Qdrant/MinIO data, and Fabric crypto material.
