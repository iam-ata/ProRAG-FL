"""Tests for environment capture and secret redaction."""

import pytest

from prorag_fl.core.environment import capture_environment, get_redacted_env_vars
from prorag_fl.core.logging import _redact_dict


@pytest.mark.unit
def test_environment_capture_structure():
    """Verify capture_environment returns all required system, hardware, and package fields."""
    env = capture_environment()
    assert "python" in env
    assert "version" in env["python"]
    assert "executable" in env["python"]

    assert "hardware" in env
    assert "cpu" in env["hardware"]
    assert "ram" in env["hardware"]
    assert "gpu" in env["hardware"]

    assert "packages" in env
    assert "torch" in env["packages"]
    assert "flwr" in env["packages"]

    assert "environment_variables" in env


@pytest.mark.unit
def test_environment_capture_redacts_sensitive_keys(monkeypatch):
    """Verify that any environment variable containing sensitive patterns is masked with [REDACTED]."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-supersecretkey12345")
    monkeypatch.setenv("MINIO_SECRET_KEY", "verysecretpassword999")
    monkeypatch.setenv("DATABASE_PASSWORD", "mypassword123")
    monkeypatch.setenv("PRORAG_SAFE_CONFIG_PATH", "configs/experiments/default.yaml")

    redacted = get_redacted_env_vars()

    assert redacted["OPENAI_API_KEY"] == "[REDACTED]"
    assert redacted["MINIO_SECRET_KEY"] == "[REDACTED]"
    assert redacted["DATABASE_PASSWORD"] == "[REDACTED]"
    assert redacted["PRORAG_SAFE_CONFIG_PATH"] == "configs/experiments/default.yaml"


@pytest.mark.unit
def test_redact_nested_dictionary():
    """Verify recursive secret redaction in nested data structures."""
    data = {
        "user": "researcher",
        "nested": {
            "api_key": "topsecret_token",
            "safe_field": 42,
            "deep": {
                "private_key": "-----BEGIN RSA PRIVATE KEY-----",
                "normal": "value",
            },
        },
        "list_items": [
            {"token": "xyz123"},
            {"public": "abc"},
        ],
    }
    redacted = _redact_dict(data)

    assert redacted["user"] == "researcher"
    assert redacted["nested"]["api_key"] == "[REDACTED]"
    assert redacted["nested"]["safe_field"] == 42
    assert redacted["nested"]["deep"]["private_key"] == "[REDACTED]"
    assert redacted["nested"]["deep"]["normal"] == "value"
    assert redacted["list_items"][0]["token"] == "[REDACTED]"
    assert redacted["list_items"][1]["public"] == "abc"
