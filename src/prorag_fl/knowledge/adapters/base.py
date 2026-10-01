"""Base interface for authorized threat intelligence source adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from prorag_fl.schemas.knowledge import KnowledgeDocument


class BaseKnowledgeAdapter(ABC):
    """Abstract base class for modular threat intelligence source adapters."""

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Return unique source identifier (e.g. mitre_attack, nvd_cve, cisa_kev)."""
        ...

    @abstractmethod
    def parse_document(
        self,
        raw_data: dict[str, Any] | str,
        version: str = "v1.0.0",
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        """Parse raw upstream threat intelligence into a standardized KnowledgeDocument."""
        ...
