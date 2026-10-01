"""NVD / CVE threat intelligence source adapter."""

from __future__ import annotations

from typing import Any

from prorag_fl.knowledge.adapters.base import BaseKnowledgeAdapter
from prorag_fl.knowledge.canonicalizer import canonicalize_text, compute_canonical_hash
from prorag_fl.schemas.knowledge import KnowledgeDocument


class NvdCveAdapter(BaseKnowledgeAdapter):
    """Adapter for National Vulnerability Database (NVD) CVE advisories and CVSS metrics."""

    @property
    def source_id(self) -> str:
        return "nvd_cve"

    def parse_document(
        self,
        raw_data: dict[str, Any] | str,
        version: str = "v1.0.0",
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        """Parse NVD CVE dictionary or text payload into canonical KnowledgeDocument."""
        meta = dict(metadata or {})

        if isinstance(raw_data, str):
            cve_id = meta.get("cve_id", "cve_unknown")
            title = f"Vulnerability {cve_id.upper()}"
            body = raw_data
            canonical_uri = meta.get("url", f"https://nvd.nist.gov/vuln/detail/{cve_id.upper()}")
        else:
            cve_id = (
                raw_data.get("cve_id")
                or raw_data.get("id")
                or raw_data.get("cve", {}).get("id", "cve_unknown")
            )
            description = (
                raw_data.get("description")
                or raw_data.get("summary")
                or (
                    raw_data.get("descriptions", [{}])[0].get("value", "")
                    if isinstance(raw_data.get("descriptions"), list)
                    else ""
                )
            )
            cvss_score = raw_data.get("cvss_score") or raw_data.get("cvss")
            severity = raw_data.get("severity", "UNKNOWN")
            cwe_id = raw_data.get("cwe_id") or raw_data.get("weaknesses", "")

            title = f"{cve_id.upper()}: {severity} Severity Vulnerability"
            parts = [
                f"# {cve_id.upper()}",
                f"Severity: {severity} (CVSS: {cvss_score})"
                if cvss_score
                else f"Severity: {severity}",
                f"Weakness: {cwe_id}" if cwe_id else "",
                f"## Description\n{description}",
            ]
            references = raw_data.get("references", [])
            if references:
                ref_links = [
                    f"- {r.get('url', r) if isinstance(r, dict) else r}" for r in references[:5]
                ]
                parts.append("## References\n" + "\n".join(ref_links))

            body = "\n\n".join(p for p in parts if p)
            canonical_uri = f"https://nvd.nist.gov/vuln/detail/{cve_id.upper()}"
            meta.update(
                {
                    "cve_id": cve_id.upper(),
                    "severity": severity,
                    "cvss_score": cvss_score,
                }
            )

        canonical_body = canonicalize_text(body)
        content_hash = compute_canonical_hash(canonical_body)
        doc_id = str(cve_id).lower().replace("-", "_")

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
