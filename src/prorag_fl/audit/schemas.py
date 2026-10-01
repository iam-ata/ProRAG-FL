"""Pydantic schemas for ProRAG-FL final reproducibility and audit verification."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AuditCheckStatus(StrEnum):
    """Execution status for an audit check."""

    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"


class AuditCheckItem(BaseModel):
    """Individual verification check item."""

    category: str = Field(description="Checklist section (e.g., Environment, Data, Model, etc.)")
    name: str = Field(description="Identifier or name of the specific check")
    status: AuditCheckStatus = Field(description="Verification outcome")
    details: str = Field(description="Detailed explanation or diagnostic note")
    artifacts: list[str] = Field(
        default_factory=list, description="Associated file paths or references"
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Structured verification evidence"
    )


class AuditCategorySummary(BaseModel):
    """Summary of audit checks within a specific checklist category."""

    category: str
    total_checks: int
    passed_count: int
    warning_count: int
    failed_count: int
    is_fully_compliant: bool
    items: list[AuditCheckItem] = Field(default_factory=list)


class FinalReproducibilityAudit(BaseModel):
    """Master document summarizing end-to-end reproducibility and scientific audit."""

    audit_id: str = Field(description="Unique deterministic ID for this audit pass")
    timestamp: str = Field(description="ISO-8601 audit timestamp")
    git_commit: str = Field(description="Git commit hash")
    git_branch: str = Field(description="Git branch")
    git_dirty: bool = Field(description="Whether uncommitted changes exist")
    is_reproducible: bool = Field(description="Overall reproducibility pass/fail verdict")
    total_checks: int
    total_passed: int
    total_warnings: int
    total_failed: int
    categories: dict[str, AuditCategorySummary] = Field(default_factory=dict)
    reproducibility_checklist_path: str = Field(
        default="instructions/30_FINAL_REPRODUCIBILITY_CHECKLIST.md"
    )
    notes: list[str] = Field(default_factory=list)
