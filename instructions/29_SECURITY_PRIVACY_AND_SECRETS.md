# Security, Privacy, and Secrets

## Ignore at minimum
```gitignore
.env
data/raw/
data/interim/
data/processed/
runs/
artifacts/
checkpoints/
*.pt
*.pth
*.ckpt
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
mlruns/
services/**/data/
services/fabric/**/crypto-config/
services/fabric/**/organizations/
```

## OpenAI allowlist
`SecurityEvent` external serialization must use an allowlist of approved fields. A blacklist is insufficient because newly added fields could leak unintentionally.

## Pseudonymization
External event IDs should be experiment-safe pseudonyms, not raw device/IP identity.

## Logs
Separate scientific metrics from infrastructure/debug logs. Redact secrets and private key material.

## Fabric identities
Keep private keys inside controlled Fabric volumes/identity stores. Core research code receives identity references/config, not embedded secret strings.

## CTI licensing
Record source and relevant redistribution terms. Public artifact should prefer reproducible fetch/build scripts and manifests rather than redistributing restricted corpora.
