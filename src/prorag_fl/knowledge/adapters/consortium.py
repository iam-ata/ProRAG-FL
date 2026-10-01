"""Consortium Incident Memory threat intelligence adapter."""

from __future__ import annotations

from typing import Any

from prorag_fl.knowledge.adapters.base import BaseKnowledgeAdapter
from prorag_fl.knowledge.canonicalizer import canonicalize_text, compute_canonical_hash
from prorag_fl.schemas.knowledge import KnowledgeDocument


class ConsortiumIncidentAdapter(BaseKnowledgeAdapter):
    """Adapter for shared consortium incident reports, zero-day threat memory, and IoT post-mortems."""

    @property
    def source_id(self) -> str:
        return "consortium_incident_memory"

    def parse_document(
        self,
        raw_data: dict[str, Any] | str,
        version: str = "v1.0.0",
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        """Parse consortium incident report into canonical KnowledgeDocument."""
        meta = dict(metadata or {})

        if isinstance(raw_data, str):
            inc_id = meta.get("incident_id", "consortium_inc_unknown")
            title = meta.get("title", f"Consortium Incident Report {inc_id}")
            body = raw_data
            canonical_uri = meta.get("url", f"consortium://incidents/{inc_id}")
        else:
            inc_id = raw_data.get("incident_id") or raw_data.get("id", "inc_unknown")
            title = raw_data.get("title") or f"Consortium Incident Report: {inc_id}"
            target_system = raw_data.get("target_system", "IoT Edge Infrastructure")
            attack_vector = raw_data.get("attack_vector", "Network Infiltration")
            iocs = raw_data.get("indicators_of_compromise") or raw_data.get("iocs", [])
            mitigation_taken = raw_data.get("mitigation_taken", "")
            narrative = raw_data.get("narrative") or raw_data.get("description", "")

            parts = [
                f"# {title}",
                f"Incident ID: {inc_id}",
                f"Target Environment: {target_system}",
                f"Attack Vector: {attack_vector}",
                f"## Incident Summary\n{narrative}",
            ]
            if iocs:
                ioc_lines = [
                    f"- {ioc if isinstance(ioc, str) else ioc.get('value', str(ioc))}"
                    for ioc in iocs
                ]
                parts.append("## Indicators of Compromise\n" + "\n".join(ioc_lines))
            if mitigation_taken:
                parts.append(f"## Containment & Remediation\n{mitigation_taken}")

            body = "\n\n".join(parts)
            canonical_uri = f"consortium://incidents/{inc_id}"
            meta.update(
                {
                    "incident_id": inc_id,
                    "target_system": target_system,
                    "attack_vector": attack_vector,
                }
            )

        canonical_body = canonicalize_text(body)
        content_hash = compute_canonical_hash(canonical_body)
        doc_id = str(meta.get("incident_id", inc_id)).lower().replace("-", "_")

        return KnowledgeDocument(
            document_id=doc_id,
            source_id=self.source_id,
            canonical_uri=canonical_uri,
            version=version,
            title=str(title),
            content=canonical_body,
            content_sha256=content_hash,
            merkle_root="",
            total_chunks=0,
            status="active",
            object_uri=f"s3://cti-knowledge/{self.source_id}/{doc_id}/{version}/{content_hash}.json",
            metadata=meta,
        )
