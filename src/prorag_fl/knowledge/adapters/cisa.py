"""CISA Known Exploited Vulnerabilities (KEV) threat intelligence adapter."""

from __future__ import annotations

from typing import Any

from prorag_fl.knowledge.adapters.base import BaseKnowledgeAdapter
from prorag_fl.knowledge.canonicalizer import canonicalize_text, compute_canonical_hash
from prorag_fl.schemas.knowledge import KnowledgeDocument


class CisaKevAdapter(BaseKnowledgeAdapter):
    """Adapter for CISA Known Exploited Vulnerabilities (KEV) Catalog entries."""

    @property
    def source_id(self) -> str:
        return "cisa_kev"

    def parse_document(
        self,
        raw_data: dict[str, Any] | str,
        version: str = "v1.0.0",
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        """Parse CISA KEV JSON or text into canonical KnowledgeDocument."""
        meta = dict(metadata or {})

        if isinstance(raw_data, str):
            cve_id = meta.get("cve_id", "cisa_advisory")
            title = f"CISA Advisory {cve_id}"
            body = raw_data
            canonical_uri = meta.get(
                "url", "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
            )
        else:
            cveID = raw_data.get("cveID") or raw_data.get("cve_id", "cve_unknown")
            vendorProject = raw_data.get("vendorProject", "Unknown Vendor")
            product = raw_data.get("product", "Unknown Product")
            vulnerabilityName = raw_data.get("vulnerabilityName", "Active Exploit in the Wild")
            shortDescription = raw_data.get("shortDescription") or raw_data.get("description", "")
            requiredAction = raw_data.get("requiredAction", "Apply vendor updates immediately.")
            dueDate = raw_data.get("dueDate", "")
            knownRansomware = raw_data.get("knownRansomwareCampaignUse", "Unknown")

            title = f"CISA KEV: {cveID} ({vendorProject} {product})"
            parts = [
                f"# {title}",
                f"Vulnerability: {vulnerabilityName}",
                f"Vendor/Product: {vendorProject} - {product}",
                f"Known Ransomware Campaign Use: {knownRansomware}",
                f"Remediation Due Date: {dueDate}" if dueDate else "",
                f"## Short Description\n{shortDescription}",
                f"## Required Action\n{requiredAction}",
            ]
            body = "\n\n".join(p for p in parts if p)
            canonical_uri = (
                f"https://www.cisa.gov/known-exploited-vulnerabilities-catalog?search={cveID}"
            )
            meta.update(
                {
                    "cve_id": cveID,
                    "vendor": vendorProject,
                    "product": product,
                    "ransomware_use": knownRansomware,
                }
            )

        canonical_body = canonicalize_text(body)
        content_hash = compute_canonical_hash(canonical_body)
        doc_id = str(meta.get("cve_id", "cisa_kev")).lower().replace("-", "_")

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
