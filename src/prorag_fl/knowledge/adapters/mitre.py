"""MITRE ATT&CK threat intelligence source adapter."""

from __future__ import annotations

from typing import Any

from prorag_fl.knowledge.adapters.base import BaseKnowledgeAdapter
from prorag_fl.knowledge.canonicalizer import canonicalize_text, compute_canonical_hash
from prorag_fl.schemas.knowledge import KnowledgeDocument


class MitreAttackAdapter(BaseKnowledgeAdapter):
    """Adapter for MITRE ATT&CK techniques, tactics, and mitigation procedures."""

    @property
    def source_id(self) -> str:
        return "mitre_attack"

    def parse_document(
        self,
        raw_data: dict[str, Any] | str,
        version: str = "v1.0.0",
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        """Parse MITRE ATT&CK JSON or text payload into canonical KnowledgeDocument."""
        meta = dict(metadata or {})

        if isinstance(raw_data, str):
            doc_id = meta.get("technique_id", "mitre_attack_doc")
            title = meta.get("name", doc_id)
            body = raw_data
            canonical_uri = meta.get("url", f"https://attack.mitre.org/techniques/{doc_id.upper()}")
        else:
            doc_id = raw_data.get("id") or raw_data.get("technique_id") or "mitre_technique"
            title = raw_data.get("name") or raw_data.get("title") or doc_id
            description = raw_data.get("description", "")
            mitigations = raw_data.get("mitigations", "")
            detection = raw_data.get("detection", "")
            tactics = raw_data.get("tactics", [])

            parts = [f"# MITRE ATT&CK {doc_id}: {title}", description]
            if tactics:
                parts.append(
                    f"Tactics: {', '.join(tactics) if isinstance(tactics, list) else tactics}"
                )
            if mitigations:
                parts.append(f"## Mitigations\n{mitigations}")
            if detection:
                parts.append(f"## Detection\n{detection}")

            body = "\n\n".join(parts)
            canonical_uri = raw_data.get(
                "url", f"https://attack.mitre.org/techniques/{str(doc_id).replace('.', '/')}"
            )
            meta.update({k: v for k, v in raw_data.items() if k not in ("description",)})

        canonical_body = canonicalize_text(body)
        content_hash = compute_canonical_hash(canonical_body)

        return KnowledgeDocument(
            document_id=str(doc_id).lower().replace(".", "_").replace(" ", "_"),
            source_id=self.source_id,
            canonical_uri=canonical_uri,
            version=version,
            title=str(title),
            content=canonical_body,
            content_sha256=content_hash,
            merkle_root="",  # Computed upon chunking
            total_chunks=0,
            status="active",
            object_uri=f"s3://cti-knowledge/{self.source_id}/{doc_id}/{version}/{content_hash}.json",
            metadata=meta,
        )
