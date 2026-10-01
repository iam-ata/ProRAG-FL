"""Structured logging setup with secret redaction and configurable output formats."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import structlog

# Keys that may contain secrets and must be redacted from logs
SENSITIVE_KEY_PATTERNS = {
    "api_key",
    "apikey",
    "secret",
    "secret_key",
    "password",
    "passwd",
    "token",
    "private_key",
    "privatekey",
    "authorization",
    "bearer",
}


def redact_sensitive_data(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor that recursively redacts sensitive information in event dictionaries."""
    return _redact_dict(event_dict)


def _redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, val in data.items():
        key_lower = str(key).lower()
        if any(pat in key_lower for pat in SENSITIVE_KEY_PATTERNS):
            redacted[key] = "[REDACTED]"
        elif isinstance(val, dict):
            redacted[key] = _redact_dict(val)
        elif isinstance(val, list):
            redacted[key] = [_redact_dict(item) if isinstance(item, dict) else item for item in val]
        else:
            redacted[key] = val
    return redacted


def configure_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Path | str | None = None,
) -> None:
    """Configure structured logging for ProRAG-FL.

    Args:
        level: Log level string ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        json_format: Whether to output log events as JSON lines.
        log_file: Optional file path to append logs to.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        redact_sensitive_data,
    ]

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(str(file_path), encoding="utf-8"))

    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=handlers,
        force=True,
    )

    if json_format:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    for handler in handlers:
        handler.setFormatter(formatter)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a configured structlog logger instance."""
    return structlog.get_logger(name or "prorag_fl")
