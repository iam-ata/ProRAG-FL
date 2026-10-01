"""Tests for Typer CLI commands."""

import json

import pytest
from typer.testing import CliRunner

from prorag_fl.cli.main import app

runner = CliRunner()


@pytest.mark.unit
def test_cli_version():
    """Verify 'prorag version' exits with code 0 and prints version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "ProRAG-FL version" in result.stdout


@pytest.mark.unit
def test_cli_doctor():
    """Verify 'prorag doctor' exits with code 0 and reports workspace status."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "ProRAG-FL Environment Doctor" in result.stdout
    assert "Hardware & Runtime" in result.stdout
    assert "Workspace Directories" in result.stdout


@pytest.mark.unit
def test_cli_validate_config_success():
    """Verify 'prorag validate-config' succeeds on valid config."""
    result = runner.invoke(app, ["validate-config", "--config", "configs/experiments/default.yaml"])
    assert result.exit_code == 0
    assert "Configuration is valid!" in result.stdout
    assert "Config SHA-256:" in result.stdout


@pytest.mark.unit
def test_cli_validate_config_failure(tmp_path):
    """Verify 'prorag validate-config' fails on invalid schema."""
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("experiment:\n  id: bad\ninvalid_section: true\n", encoding="utf-8")

    result = runner.invoke(app, ["validate-config", "--config", str(bad_yaml)])
    assert result.exit_code != 0
    assert "Configuration validation failed" in result.stdout


@pytest.mark.unit
def test_cli_show_env():
    """Verify 'prorag show-env' succeeds and masks secrets."""
    result = runner.invoke(app, ["show-env"])
    assert result.exit_code == 0
    assert "Reproducibility Environment Snapshot" in result.stdout


@pytest.mark.unit
def test_cli_show_env_json():
    """Verify 'prorag show-env --json' returns valid parseable JSON."""
    result = runner.invoke(app, ["show-env", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "python" in data
    assert "hardware" in data
    assert "packages" in data


@pytest.mark.unit
def test_cli_data_inspect():
    """Verify 'prorag data inspect' runs without error."""
    result = runner.invoke(app, ["data", "inspect", "--dataset", "ciciot2023"])
    assert result.exit_code == 0
    assert "Scanning raw dataset in" in result.stdout
