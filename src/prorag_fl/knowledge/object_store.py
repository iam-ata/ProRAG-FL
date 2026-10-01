"""Immutable, content-addressed object store for threat intelligence documents."""

from __future__ import annotations

from pathlib import Path

from prorag_fl.schemas.knowledge import KnowledgeDocument


class KnowledgeObjectStore:
    """Versioned, immutable object store for canonical knowledge documents.

    Adheres strictly to instructions/14_KNOWLEDGE_INGESTION_AND_MERKLE.md:
    Path convention: <source>/<document_id>/<version>/<content_sha256>.json
    Never overwrite historical content under the same provenance key.
    """

    def __init__(self, storage_dir: Path | str | None = None) -> None:
        self.storage_dir = Path(storage_dir) if storage_dir else None
        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._memory_store: dict[str, str] = {}

    def build_object_key(
        self,
        source_id: str,
        document_id: str,
        version: str,
        content_sha256: str,
    ) -> str:
        """Construct deterministic canonical object key."""
        clean_source = source_id.lower().strip()
        clean_doc = document_id.lower().strip()
        clean_ver = version.strip()
        clean_hash = content_sha256.lower().strip()
        return f"{clean_source}/{clean_doc}/{clean_ver}/{clean_hash}.json"

    def put_document(self, document: KnowledgeDocument) -> str:
        """Store an immutable KnowledgeDocument. Raises ValueError if key exists with different payload."""
        key = self.build_object_key(
            source_id=document.source_id,
            document_id=document.document_id,
            version=document.version,
            content_sha256=document.content_sha256,
        )
        serialized = document.model_dump_json(indent=2)

        # Check in-memory store
        if key in self._memory_store:
            existing = self._memory_store[key]
            if existing != serialized:
                raise ValueError(
                    f"Immutability violation: Object at key '{key}' already exists with different content."
                )
            return key

        self._memory_store[key] = serialized

        # Persist to disk if storage_dir configured
        if self.storage_dir:
            target_file = self.storage_dir / key
            if target_file.exists():
                existing_file_content = target_file.read_text(encoding="utf-8")
                if existing_file_content != serialized:
                    raise ValueError(
                        f"Immutability violation: File at '{target_file}' already exists with different content."
                    )
            else:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(serialized, encoding="utf-8")

        return key

    def get_document(
        self,
        source_id: str,
        document_id: str,
        version: str,
        content_sha256: str,
    ) -> KnowledgeDocument | None:
        """Retrieve a stored KnowledgeDocument by exact provenance coordinates."""
        key = self.build_object_key(source_id, document_id, version, content_sha256)

        if key in self._memory_store:
            return KnowledgeDocument.model_validate_json(self._memory_store[key])

        if self.storage_dir:
            target_file = self.storage_dir / key
            if target_file.exists():
                content = target_file.read_text(encoding="utf-8")
                return KnowledgeDocument.model_validate_json(content)

        return None

    def exists(
        self,
        source_id: str,
        document_id: str,
        version: str,
        content_sha256: str,
    ) -> bool:
        """Check if an object exists at the specified provenance key."""
        key = self.build_object_key(source_id, document_id, version, content_sha256)
        if key in self._memory_store:
            return True
        if self.storage_dir:
            return (self.storage_dir / key).exists()
        return False
