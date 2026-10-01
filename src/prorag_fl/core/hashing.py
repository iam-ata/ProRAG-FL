"""Canonical hashing, run ID generation, and collision-safe run directory creation."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json_bytes(data: dict[str, Any]) -> bytes:
    """Serialize dictionary to canonical JSON bytes with sorted keys and normalized separators."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def compute_config_hash(config_data: dict[str, Any], length: int = 12) -> str:
    """Compute a deterministic SHA-256 hash of a configuration dictionary.

    Args:
        config_data: Dictionary representing the resolved scientific configuration.
        length: Number of leading hexadecimal characters to return (default 12).
    """
    raw_bytes = canonical_json_bytes(config_data)
    digest = hashlib.sha256(raw_bytes).hexdigest()
    return digest[:length]


def generate_run_id(
    experiment_id: str,
    config_hash: str,
    seed: int,
    timestamp: datetime.datetime | None = None,
) -> str:
    """Generate canonical Run ID matching the specification:

    <experiment>_<timestamp>_<short-config-hash>_seed<seed>
    """
    ts = (timestamp or datetime.datetime.now(datetime.UTC)).strftime("%Y%m%d_%H%M%S")
    clean_exp = experiment_id.strip().replace(" ", "_")
    short_hash = config_hash[:8]
    return f"{clean_exp}_{ts}_{short_hash}_seed{seed}"


def create_run_directory(
    runs_root: Path | str,
    run_id: str,
    allow_resume: bool = False,
) -> Path:
    """Create an isolated directory for a run.

    Raises FileExistsError if the run already exists and has a completion marker,
    enforcing the test-set and experiment immutability rule.
    """
    run_dir = Path(runs_root) / run_id
    completion_marker = run_dir / "COMPLETED"

    if run_dir.exists():
        if completion_marker.exists() and not allow_resume:
            raise FileExistsError(
                f"Run directory '{run_dir}' already exists and contains a COMPLETED marker. "
                "Silent overwrite of completed runs is forbidden by Master Agent Contract."
            )

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "checkpoints").mkdir(exist_ok=True)
    (run_dir / "logs").mkdir(exist_ok=True)
    (run_dir / "metrics").mkdir(exist_ok=True)
    return run_dir


def mark_run_completed(run_dir: Path | str, metadata: dict[str, Any] | None = None) -> None:
    """Write an immutable completion marker to the run directory."""
    marker = Path(run_dir) / "COMPLETED"
    content = metadata or {"completed_at": datetime.datetime.now(datetime.UTC).isoformat()}
    marker.write_text(json.dumps(content, indent=2), encoding="utf-8")
