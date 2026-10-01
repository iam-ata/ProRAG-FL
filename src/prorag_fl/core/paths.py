"""Repository root and directory path resolution helpers."""

from __future__ import annotations

import os
from pathlib import Path

PRORAG_ROOT_ENV = "PRORAG_PROJECT_ROOT"


def find_project_root(start_path: Path | str | None = None) -> Path:
    """Find the root directory of the ProRAG-FL Code repository.

    The root is determined in order of precedence:
    1. Explicit PRORAG_PROJECT_ROOT environment variable.
    2. Given start_path (or its parents) containing both 'pyproject.toml' and 'instructions/'.
    3. Current working directory (or its parents) containing both 'pyproject.toml' and 'instructions/'.
    4. Location of this file (or its parents) containing both 'pyproject.toml' and 'instructions/'.
    5. Fallback: closest parent having 'pyproject.toml' or 'instructions/'.
    """
    if PRORAG_ROOT_ENV in os.environ:
        root = Path(os.environ[PRORAG_ROOT_ENV]).resolve()
        if root.exists():
            return root

    search_roots: list[Path] = []
    if start_path:
        search_roots.append(Path(start_path).resolve())
    search_roots.append(Path.cwd().resolve())
    search_roots.append(Path(__file__).resolve().parent)

    for base in search_roots:
        candidates = [base, *base.parents]
        for candidate in candidates:
            if (candidate / "pyproject.toml").is_file() and (candidate / "instructions").is_dir():
                return candidate

    for base in search_roots:
        candidates = [base, *base.parents]
        for candidate in candidates:
            if (candidate / "pyproject.toml").is_file() or (candidate / "instructions").is_dir():
                return candidate

    # Ultimate fallback to repository Code folder
    return Path(__file__).resolve().parents[2]


def get_project_root() -> Path:
    """Return the resolved project root directory."""
    return find_project_root()


def get_configs_dir() -> Path:
    """Return the path to the configs/ directory."""
    path = get_project_root() / "configs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir() -> Path:
    """Return the path to the data/ directory."""
    path = get_project_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_runs_dir() -> Path:
    """Return the path to the runs/ directory."""
    path = get_project_root() / "runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_artifacts_dir() -> Path:
    """Return the path to the artifacts/ directory."""
    path = get_project_root() / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_checkpoints_dir() -> Path:
    """Return the path to the checkpoints/ directory."""
    path = get_project_root() / "checkpoints"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_reports_dir() -> Path:
    """Return the path to the reports/ directory."""
    path = get_project_root() / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path
