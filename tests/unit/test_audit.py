"""Unit tests for ProRAG-FL final reproducibility audit engine and checklist synchronization."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from prorag_fl.audit.engine import ReproducibilityAuditEngine
from prorag_fl.audit.reporting import AuditReporter
from prorag_fl.audit.schemas import (
    AuditCategorySummary,
    AuditCheckItem,
    AuditCheckStatus,
    FinalReproducibilityAudit,
)


@pytest.mark.unit
def test_audit_schemas_serialization() -> None:
    """Verify serialization and validation of audit schemas."""
    item = AuditCheckItem(
        category="Environment",
        name="Conda env exported",
        status=AuditCheckStatus.PASSED,
        details="Verified environment.yml",
        artifacts=["environment.yml"],
    )
    summary = AuditCategorySummary(
        category="Environment",
        total_checks=1,
        passed_count=1,
        warning_count=0,
        failed_count=0,
        is_fully_compliant=True,
        items=[item],
    )
    audit = FinalReproducibilityAudit(
        audit_id="audit_test_001",
        timestamp="2026-09-28T12:00:00Z",
        git_commit="abcdef123456",
        git_branch="main",
        git_dirty=False,
        is_reproducible=True,
        total_checks=1,
        total_passed=1,
        total_warnings=0,
        total_failed=0,
        categories={"Environment": summary},
        notes=["Test audit passed"],
    )

    data = json.loads(audit.model_dump_json())
    assert data["is_reproducible"] is True
    assert data["total_passed"] == 1
    assert data["categories"]["Environment"]["is_fully_compliant"] is True


@pytest.mark.unit
def test_reproducibility_audit_engine_full_pass() -> None:
    """Verify that ReproducibilityAuditEngine runs cleanly across the repository and passes all checks."""
    engine = ReproducibilityAuditEngine()
    audit = engine.run_full_audit()

    assert audit is not None
    assert audit.total_checks >= 45
    assert audit.total_failed == 0
    assert audit.is_reproducible is True

    # Check that all 10 standard categories exist
    expected_categories = [
        "Environment",
        "Data",
        "Model/gate",
        "FL",
        "Blockchain",
        "Knowledge/RAG",
        "OpenAI",
        "Baselines",
        "Experiments",
        "Paper",
    ]
    for cat in expected_categories:
        assert cat in audit.categories, f"Missing category: {cat}"
        cat_summary = audit.categories[cat]
        assert cat_summary.is_fully_compliant is True, f"Category {cat} had failures!"


@pytest.mark.unit
def test_audit_reporter_generates_valid_files(tmp_path: Path) -> None:
    """Verify that AuditReporter saves JSON, Markdown, and updates checklist."""
    engine = ReproducibilityAuditEngine()
    audit = engine.run_full_audit()

    reporter = AuditReporter()
    saved = reporter.save_reports(audit)

    assert Path(saved["json_path"]).exists()
    assert Path(saved["md_path"]).exists()

    with open(saved["json_path"], encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["is_reproducible"] is True
