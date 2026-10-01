"""System, hardware, runtime, and package environment capture with secret redaction."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from typing import Any

import psutil
import torch

from prorag_fl.core.logging import SENSITIVE_KEY_PATTERNS


def get_git_info() -> dict[str, Any]:
    """Capture current Git commit hash, branch, and dirty status safely."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        is_dirty = bool(status)
        return {"commit": commit, "branch": branch, "dirty": is_dirty}
    except Exception:
        return {
            "commit": "unknown",
            "branch": "unknown",
            "dirty": False,
            "note": "git unavailable or not a repo",
        }


def get_hardware_info() -> dict[str, Any]:
    """Capture CPU, memory, and GPU specifications."""
    mem = psutil.virtual_memory()
    info: dict[str, Any] = {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "cpu": {
            "processor": platform.processor(),
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
        },
        "ram": {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
        },
        "gpu": {
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
            "devices": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
            if torch.cuda.is_available()
            else [],
            "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
            "cudnn_version": torch.backends.cudnn.version() if torch.cuda.is_available() else None,
        },
    }
    return info


def get_package_versions() -> dict[str, str]:
    """Capture versions of primary research dependencies."""
    packages = [
        "torch",
        "flwr",
        "scikit-learn",
        "pandas",
        "numpy",
        "scipy",
        "pydantic",
        "pyyaml",
        "typer",
        "structlog",
        "transformers",
        "openai",
        "minio",
        "qdrant_client",
        "pytest",
        "ruff",
    ]
    versions: dict[str, str] = {}
    for pkg in packages:
        try:
            import importlib.metadata

            ver = importlib.metadata.version(pkg)
            versions[pkg] = ver
        except Exception:
            # Fallback to direct import attribute check
            mod_name = pkg.replace("-", "_")
            try:
                mod = __import__(mod_name)
                versions[pkg] = getattr(mod, "__version__", "installed (unknown version)")
            except Exception:
                versions[pkg] = "not_installed"
    return versions


def get_redacted_env_vars() -> dict[str, str]:
    """Capture environment variables while strictly redacting sensitive keys."""
    redacted: dict[str, str] = {}
    for key, val in os.environ.items():
        key_lower = key.lower()
        if any(pat in key_lower for pat in SENSITIVE_KEY_PATTERNS):
            redacted[key] = "[REDACTED]"
        else:
            redacted[key] = val
    return redacted


def capture_environment() -> dict[str, Any]:
    """Capture comprehensive reproducible environment snapshot."""
    return {
        "python": {
            "version": sys.version,
            "executable": sys.executable,
        },
        "hardware": get_hardware_info(),
        "git": get_git_info(),
        "packages": get_package_versions(),
        "environment_variables": get_redacted_env_vars(),
    }
