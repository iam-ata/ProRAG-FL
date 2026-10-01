"""High-level Knowledge Management: Ingestion, Merkle anchoring, and verification."""

from __future__ import annotations

import logging
from typing import Any

from prorag_fl.knowledge.adapters.base import BaseKnowledgeAdapter
from prorag_fl.knowledge.canonicalizer import canonicalize_text, compute_canonical_hash
from prorag_fl.knowledge.chunker import DeterministicChunker
from prorag_fl.knowledge.merkle import MerkleTree, verify_merkle_proof
from prorag_fl.knowledge.object_store import KnowledgeObjectStore
from prorag_fl.schemas.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeLedgerRecord,
)

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """End-to-end knowledge ingestion, Merkle provenance anchoring, and proof verification."""

    def __init__(
        self,
        object_store: KnowledgeObjectStore | None = None,
        chunk_size: int = 500,
        chunk_overlap: int = 60,
    ) -> None:
        self.object_store = object_store or KnowledgeObjectStore()
        self.chunker = DeterministicChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # In-memory document repository: doc_id -> list of versions
        self._documents: dict[str, dict[str, KnowledgeDocument]] = {}
        # Active version pointer: doc_id -> active version string
        self._active_versions: dict[str, str] = {}
        # All indexed chunks: chunk_id -> KnowledgeChunk
        self._chunks: dict[str, KnowledgeChunk] = {}
        # Ledger anchor records: (doc_id, version) -> KnowledgeLedgerRecord
        self._ledger_records: dict[tuple[str, str], KnowledgeLedgerRecord] = {}

    def ingest_document(
        self,
        adapter: BaseKnowledgeAdapter,
        raw_data: dict[str, Any] | str,
        version: str = "v1.0.0",
        metadata: dict[str, Any] | None = None,
    ) -> tuple[KnowledgeDocument, list[KnowledgeChunk]]:
        """Ingest raw threat intelligence, generate chunks, construct Merkle tree, and anchor record."""
        # 1. Parse document with adapter
        doc = adapter.parse_document(raw_data=raw_data, version=version, metadata=metadata)
        doc_id = doc.document_id

        # 2. Check previous version for lifecycle updating
        prev_version = self._active_versions.get(doc_id)
        if prev_version and prev_version != version:
            prev_doc = self._documents[doc_id].get(prev_version)
            if prev_doc:
                # Mark previous document as superseded
                superseded_doc = prev_doc.model_copy(update={"status": "superseded"})
                self._documents[doc_id][prev_version] = superseded_doc
                if (doc_id, prev_version) in self._ledger_records:
                    self._ledger_records[(doc_id, prev_version)].status = "superseded"
            doc.previous_version = prev_version

        # 3. Deterministic chunking
        raw_chunks = self.chunker.chunk_document(
            document_id=doc_id,
            document_version=version,
            content=doc.content,
            metadata=doc.metadata,
        )

        # 4. Construct Merkle tree over chunk hashes
        leaf_hashes = [c.chunk_hash for c in raw_chunks]
        tree = MerkleTree(leaf_hashes)
        merkle_root = tree.root

        # 5. Attach audit path proofs and root to chunks
        final_chunks: list[KnowledgeChunk] = []
        for idx, chunk in enumerate(raw_chunks):
            proof = tree.get_proof(idx)
            anchored_chunk = chunk.model_copy(
                update={"merkle_proof": proof, "merkle_root": merkle_root}
            )
            final_chunks.append(anchored_chunk)
            self._chunks[anchored_chunk.chunk_id] = anchored_chunk

        # 6. Finalize KnowledgeDocument with Merkle root and chunk count
        final_doc = doc.model_copy(
            update={
                "merkle_root": merkle_root,
                "total_chunks": len(final_chunks),
            }
        )

        # 7. Store immutable canonical object in Object Store
        obj_key = self.object_store.put_document(final_doc)
        final_doc = final_doc.model_copy(update={"object_uri": f"s3://cti-knowledge/{obj_key}"})

        # 8. Store on-chain anchor ledger record
        ledger_record = KnowledgeLedgerRecord(
            document_id=doc_id,
            source_id=final_doc.source_id,
            version=version,
            content_sha256=final_doc.content_sha256,
            merkle_root=merkle_root,
            total_chunks=len(final_chunks),
            status="active",
            object_uri=final_doc.object_uri,
            previous_version=prev_version,
        )
        self._ledger_records[(doc_id, version)] = ledger_record

        # 9. Register in active state
        self._documents.setdefault(doc_id, {})[version] = final_doc
        self._active_versions[doc_id] = version

        return final_doc, final_chunks

    def revoke_document(
        self, document_id: str, version: str, reason: str = "revoked_by_security_analyst"
    ) -> bool:
        """Revoke a document version."""
        if document_id not in self._documents and document_id.lower() in self._documents:
            document_id = document_id.lower()
        if document_id not in self._documents or version not in self._documents[document_id]:
            return False

        doc = self._documents[document_id][version]
        revoked_doc = doc.model_copy(update={"status": "revoked"})
        self._documents[document_id][version] = revoked_doc

        if (document_id, version) in self._ledger_records:
            self._ledger_records[(document_id, version)].status = "revoked"

        if self._active_versions.get(document_id) == version:
            del self._active_versions[document_id]

        return True

    def verify_chunk(
        self,
        chunk: KnowledgeChunk,
        enforce_active_version: bool = True,
    ) -> tuple[bool, str]:
        """Perform cryptographic verification of a knowledge chunk against its Merkle proof and ledger state."""
        # 1. Recompute chunk hash from canonical text
        canonical_text = canonicalize_text(chunk.canonical_text)
        recomputed_hash = compute_canonical_hash(canonical_text)
        if recomputed_hash != chunk.chunk_hash:
            return False, "chunk_content_tampered"

        # 2. Check document and version on ledger
        ledger_key = (chunk.document_id, chunk.document_version)
        ledger_record = self._ledger_records.get(ledger_key)
        if ledger_record is None:
            return False, "document_not_registered_on_ledger"

        # 3. Check lifecycle status
        if ledger_record.status == "revoked":
            return False, "document_version_revoked"
        if enforce_active_version:
            active_ver = self._active_versions.get(chunk.document_id)
            if active_ver != chunk.document_version:
                return (
                    False,
                    f"stale_version_rejected:active_{active_ver}_vs_chunk_{chunk.document_version}",
                )

        # 4. Check root matches anchored ledger root
        if chunk.merkle_root != ledger_record.merkle_root:
            return False, "merkle_root_mismatch_with_ledger"

        # 5. Verify cryptographic Merkle audit path
        is_proof_valid = verify_merkle_proof(
            leaf_hash=chunk.chunk_hash,
            proof=chunk.merkle_proof,
            expected_root=chunk.merkle_root,
        )
        if not is_proof_valid:
            return False, "merkle_proof_verification_failed"

        return True, "verified"

    def get_active_document(self, document_id: str) -> KnowledgeDocument | None:
        """Retrieve the currently active version of a knowledge document."""
        if document_id not in self._documents and document_id.lower() in self._documents:
            document_id = document_id.lower()
        active_ver = self._active_versions.get(document_id)
        if not active_ver or document_id not in self._documents:
            return None
        return self._documents[document_id].get(active_ver)

    def get_active_chunks(self) -> list[KnowledgeChunk]:
        """Return all chunks corresponding strictly to active document versions."""
        active_chunks: list[KnowledgeChunk] = []
        for doc_id, active_ver in self._active_versions.items():
            doc_chunks = [
                chk
                for chk in self._chunks.values()
                if chk.document_id == doc_id and chk.document_version == active_ver
            ]
            active_chunks.extend(doc_chunks)
        return active_chunks
