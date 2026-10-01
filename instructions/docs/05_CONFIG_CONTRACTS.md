# Config Contracts
Use YAML; resolved configs are saved per run. Example:
```yaml
dataset:
  name: ciciot2023
  split_seed: 13
  held_out_family: null
model:
  name: ids_1dcnn
  conv_channels: [64,128,256]
  embedding_dim: 128
  dropout: 0.30
training:
  optimizer: adamw
  lr: 0.001
  weight_decay: 0.0001
  batch_size: 256
  local_epochs: 2
  global_rounds: 50
  seed: 13
federated:
  num_clients: 10
  partition: {type: dirichlet, alpha: 0.3}
  strategy: {name: fedtrimmedavg, beta: 0.20}
  provenance_gate: {enabled: true}
rag:
  embedding_model: BAAI/bge-m3
  vector_db: qdrant
  candidate_k: 20
  final_k: 5
  hybrid_fusion: rrf
  provenance_required: true
openai:
  enabled: false
  model: ${OPENAI_MODEL}
  allow_external_api: false
  structured_output: true
  tools_enabled: false
attack:
  name: none
  malicious_client_fraction: 0.0
```
Never persist resolved secrets.
