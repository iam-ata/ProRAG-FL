# Anaconda / Python Environment

## Create
```bash
conda create -n prorag-fl python=3.11 -y
conda activate prorag-fl
python -m pip install --upgrade pip setuptools wheel
```

## Core/data
```bash
pip install numpy pandas scipy scikit-learn imbalanced-learn pyarrow joblib tqdm psutil
pip install pyyaml pydantic pydantic-settings python-dotenv typer rich structlog
```

## PyTorch
```bash
pip install torch torchvision torchaudio
```

Verify GPU:
```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

If CUDA compatibility requires a platform-specific PyTorch build, use the supported build for the installed driver and record the final version. Do not randomly downgrade dependencies.

## Flower
```bash
pip install "flwr[simulation]"
```

## RAG
```bash
pip install transformers sentence-transformers FlagEmbedding accelerate safetensors tokenizers
pip install qdrant-client minio
```

## OpenAI
```bash
pip install openai tiktoken
```

## Evaluation/experiments
```bash
pip install datasets ragas tensorboard mlflow matplotlib plotly
```

`ragas` is optional if a metric cannot be justified cleanly; do not force LLM-as-judge metrics.

## Crypto/network/dev
```bash
pip install cryptography pycryptodome requests httpx grpcio grpcio-tools protobuf
pip install pytest pytest-cov pytest-xdist hypothesis ruff mypy
```

## Verify
```bash
python -c "import torch, flwr, sklearn, pandas, qdrant_client, openai, minio, transformers; print('ProRAG-FL environment OK')"
```

## Freeze
From `Code/`:
```bash
conda env export --no-builds > environment.yml
pip freeze > requirements-lock.txt
```

## External services
Do not install Fabric/Qdrant server/MinIO server into Conda. Use Docker/WSL2 where required. Python consumes them through adapters.

## `.env`
```env
OPENAI_API_KEY=
OPENAI_MODEL=
QDRANT_URL=http://localhost:6333
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
ALLOW_EXTERNAL_API=false
```

Never commit `.env`.
