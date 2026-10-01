# Configuration and CLI Contract

## YAML-first
All runs start from validated YAML. Example:
```yaml
experiment:
  id: e4_model_replacement

dataset:
  name: ciciot2023
  split_seed: 13
  held_out_family: null

model:
  name: ids_1dcnn
  conv_channels: [64, 128, 256]
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
  partition:
    type: dirichlet
    alpha: 0.3
  strategy:
    name: provenance_gated_trimmed_avg
    beta: 0.20

attack:
  name: model_replacement
  malicious_client_fraction: 0.20

rag:
  enabled: false

openai:
  enabled: false
```

## CLI capability target
```text
prorag doctor
prorag data inspect --dataset ...
prorag data prepare --config ...
prorag train centralized --config ...
prorag train local --config ...
prorag fl run --config ...
prorag blockchain doctor
prorag knowledge ingest --config ...
prorag rag evaluate --config ...
prorag infer --config ...
prorag experiment run --config ...
prorag experiment matrix --config ...
prorag results aggregate ...
prorag paper export ...
```
Names may vary, capabilities must remain.

## Dry-run
Long tasks validate config, enumerate runs/services/API requirements and estimate count before launch.

## Resumability
Identical completed config -> skip. Failed run -> preserve, retry only with explicit flag. Changed config -> new hash/run ID.

## Resolved config
Persist fully resolved scientific configuration with secrets redacted.
