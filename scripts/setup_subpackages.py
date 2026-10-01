"""Helper script to initialize all placeholder subpackages."""

import pathlib

subpkgs = [
    "data",
    "models",
    "calibration",
    "ood",
    "federated",
    "provenance",
    "blockchain",
    "knowledge",
    "rag",
    "reasoning",
    "threat_memory",
    "attacks",
    "baselines",
    "evaluation",
    "reporting",
    "utils",
]

base = pathlib.Path("src/prorag_fl")
for p in subpkgs:
    pkg_dir = base / p
    pkg_dir.mkdir(parents=True, exist_ok=True)
    init_file = pkg_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text(f'"""ProRAG-FL {p} module."""\n', encoding="utf-8")

print("All subpackages initialized successfully.")
