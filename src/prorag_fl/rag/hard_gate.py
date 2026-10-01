"""Hard Provenance Filter and Verified Reranking for CTI Evidence."""

from __future__ import annotations

import datetime
import math
import uuid

from prorag_fl.knowledge.canonicalizer import canonicalize_text, compute_canonical_hash
from prorag_fl.knowledge.manager import KnowledgeManager
from prorag_fl.knowledge.merkle import verify_merkle_proof
from prorag_fl.schemas.knowledge import KnowledgeChunk
from prorag_fl.schemas.rag import HardGateVerificationResult, VerifiedEvidence

DEFAULT_ALLOWED_SOURCES = {
    "mitre_attack",
    "nvd_cve",
    "cisa_kev",
    "consortium_incident_memory",
}


class HardProvenanceGate:
    """Enforces strict, non-bypassable cryptographic gating and multi-factor verified reranking.

    Adheres strictly to instructions/15_HYBRID_RAG.md:
    "For every candidate verify:
    1. source allowlisted;
    2. ledger record exists;
    3. document version active/current;
    4. chunk hash valid;
    5. Merkle proof valid;
    6. not revoked.
    Failure on any required check => candidate ineligible. Never let semantic similarity override failure."
    """

    def __init__(
        self,
        knowledge_manager: KnowledgeManager,
        allowed_sources: set[str] | None = None,
        lambda_rrf: float = 0.60,
        lambda_freshness: float = 0.20,
        lambda_corroboration: float = 0.20,
        gamma_decay: float = 0.005,
        max_evidence: int = 5,
    ) -> None:
        self.knowledge_manager = knowledge_manager
        self.allowed_sources = allowed_sources or set(DEFAULT_ALLOWED_SOURCES)
        self.lambda_rrf = lambda_rrf
        self.lambda_freshness = lambda_freshness
        self.lambda_corroboration = lambda_corroboration
        self.gamma_decay = gamma_decay
        self.max_evidence = max_evidence

    def verify_candidate(self, chunk: KnowledgeChunk) -> HardGateVerificationResult:
        """Evaluate all 6 hard cryptographic and lifecycle checks for a candidate chunk."""
        failures: list[str] = []

        # 1. Source allowlisted
        ledger_key = (chunk.document_id, chunk.document_version)
        ledger_record = self.knowledge_manager._ledger_records.get(ledger_key)
        source_id = (
            ledger_record.source_id if ledger_record else chunk.metadata.get("source_id", "")
        )
        source_ok = source_id in self.allowed_sources
        if not source_ok:
            failures.append(f"source_not_allowlisted:{source_id}")

        # 2. Ledger record exists
        ledger_ok = ledger_record is not None
        if not ledger_ok:
            failures.append("ledger_record_missing")

        # 3. Document version active / current
        active_ver = self.knowledge_manager._active_versions.get(chunk.document_id)
        version_active = active_ver is not None and active_ver == chunk.document_version
        if not version_active:
            failures.append(
                f"document_version_inactive:active_{active_ver}_vs_chunk_{chunk.document_version}"
            )

        # 4. Chunk hash valid against canonical text
        canonical_str = canonicalize_text(chunk.canonical_text)
        recomputed_hash = compute_canonical_hash(canonical_str)
        hash_ok = recomputed_hash == chunk.chunk_hash
        if not hash_ok:
            failures.append("chunk_hash_mismatch")

        # 5. Merkle proof valid against anchored root
        proof_ok = False
        if ledger_record and chunk.merkle_root == ledger_record.merkle_root:
            proof_ok = verify_merkle_proof(
                leaf_hash=chunk.chunk_hash,
                proof=chunk.merkle_proof,
                expected_root=chunk.merkle_root,
            )
        if not proof_ok:
            failures.append("merkle_proof_invalid")

        # 6. Not revoked
        not_revoked = True
        if ledger_record and ledger_record.status == "revoked":
            not_revoked = False
            failures.append("document_revoked")

        is_eligible = (
            source_ok and ledger_ok and version_active and hash_ok and proof_ok and not_revoked
        )

        return HardGateVerificationResult(
            chunk_id=chunk.chunk_id,
            is_eligible=is_eligible,
            source_allowlisted=source_ok,
            ledger_record_exists=ledger_ok,
            document_version_active=version_active,
            chunk_hash_valid=hash_ok,
            merkle_proof_valid=proof_ok,
            not_revoked=not_revoked,
            failure_reasons=failures,
        )

    def filter_and_rerank(
        self,
        candidates: list[tuple[KnowledgeChunk, float]],
        reference_time: datetime.datetime | None = None,
    ) -> list[VerifiedEvidence]:
        """Filter candidate pool with hard gate and rerank eligible evidence using multi-factor scoring."""
        if not candidates:
            return []

        now = reference_time or datetime.datetime.now(datetime.UTC)

        # Step 1: Hard Gate Filtering
        eligible_candidates: list[tuple[KnowledgeChunk, float, HardGateVerificationResult]] = []
        for chunk, rrf_score in candidates:
            ver_result = self.verify_candidate(chunk)
            if ver_result.is_eligible:
                eligible_candidates.append((chunk, rrf_score, ver_result))

        if not eligible_candidates:
            return []

        # Step 2: Multi-source corroboration counting
        # Count distinct authoritative organizations/sources in the pool
        unique_sources = {
            res.failure_reasons
            and "unknown"
            or (
                self.knowledge_manager._ledger_records.get(
                    (chk.document_id, chk.document_version)
                ).source_id
            )
            for chk, _, res in eligible_candidates
            if (chk.document_id, chk.document_version) in self.knowledge_manager._ledger_records
        }
        total_unique_sources = max(len(unique_sources), 1)

        max_rrf = max(score for _, score, _ in eligible_candidates) or 1.0

        # Step 3: Verified Reranking
        scored_evidence: list[VerifiedEvidence] = []
        for chunk, rrf_score, ver_res in eligible_candidates:
            # 1. Normalized RRF
            rrf_norm = rrf_score / max_rrf

            # 2. Freshness decay: exp(-gamma * days)
            ledger_record = self.knowledge_manager._ledger_records.get(
                (chunk.document_id, chunk.document_version)
            )
            age_days = 0.0
            if ledger_record and ledger_record.timestamp:
                try:
                    ts = datetime.datetime.fromisoformat(ledger_record.timestamp)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=datetime.UTC)
                    age_days = max(0.0, (now - ts).total_seconds() / 86400.0)
                except Exception:
                    age_days = 0.0

            freshness = math.exp(-self.gamma_decay * age_days)

            # 3. Independent corroboration
            # Does this document's threat topic appear in other independent sources?
            doc_source = (
                ledger_record.source_id if ledger_record else chunk.metadata.get("source_id", "")
            )
            other_sources = len(unique_sources - {doc_source})
            corroboration = (
                min(1.0, other_sources / max(1, total_unique_sources - 1))
                if total_unique_sources > 1
                else 0.5
            )

            # Composite verified score
            final_score = (
                self.lambda_rrf * rrf_norm
                + self.lambda_freshness * freshness
                + self.lambda_corroboration * corroboration
            )

            # Retrieve parent document for human-readable title
            parent_doc = self.knowledge_manager.get_active_document(chunk.document_id)
            doc_title = parent_doc.title if parent_doc else chunk.document_id

            evidence = VerifiedEvidence(
                evidence_id=f"evi_{uuid.uuid4().hex[:12]}",
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                source_id=doc_source,
                document_version=chunk.document_version,
                chunk_index=chunk.chunk_index,
                title=doc_title,
                canonical_text=chunk.canonical_text,
                chunk_hash=chunk.chunk_hash,
                merkle_root=chunk.merkle_root,
                final_score=float(final_score),
                rrf_score_norm=float(rrf_norm),
                freshness_score=float(freshness),
                corroboration_score=float(corroboration),
                verification_record=ver_res,
            )
            scored_evidence.append(evidence)

        # Step 4: Sort by final verified score and return top-5
        scored_evidence.sort(key=lambda e: e.final_score, reverse=True)
        return scored_evidence[: self.max_evidence]
