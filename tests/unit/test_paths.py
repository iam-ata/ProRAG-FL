"""Tests for paths and directory structure resolution."""

from pathlib import Path

import pytest

from prorag_fl.core.paths import (
    PRORAG_ROOT_ENV,
    find_project_root,
    get_artifacts_dir,
    get_checkpoints_dir,
    get_configs_dir,
    get_data_dir,
    get_project_root,
    get_reports_dir,
    get_runs_dir,
)


@pytest.mark.unit
def test_find_project_root_locates_code_dir() -> None:
    """Verify that find_project_root resolves the repository root containing pyproject.toml."""
    root = get_project_root()
    assert root.exists(), f"Resolved root {root} does not exist"
    assert (root / "pyproject.toml").is_file(), "pyproject.toml must exist at project root"
    assert (root / "instructions").is_dir(), "instructions/ directory must exist at project root"


@pytest.mark.unit
def test_find_project_root_independent_of_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify project root resolution remains accurate even when CWD is changed."""
    expected_root = get_project_root()
    # Change current working directory to a temporary folder
    monkeypatch.chdir(tmp_path)
    # When PRORAG_PROJECT_ROOT is set, it directly returns it
    monkeypatch.setenv(PRORAG_ROOT_ENV, str(expected_root))
    assert find_project_root() == expected_root


@pytest.mark.unit
def test_directory_helpers_exist_and_are_directories() -> None:
    """Verify standard repository directories are resolved properly."""
    dirs = [
        get_configs_dir(),
        get_data_dir(),
        get_runs_dir(),
        get_artifacts_dir(),
        get_checkpoints_dir(),
        get_reports_dir(),
    ]
    for d in dirs:
        assert isinstance(d, Path)
        assert d.is_dir()
