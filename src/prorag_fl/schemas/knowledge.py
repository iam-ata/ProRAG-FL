"""Pydantic schemas for Knowledge Documents, Merkle Trees, and CTI Provenance."""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MerkleProofStep(BaseModel):
    """Step in a cryptographic Merkle audit path."""

    model_config = ConfigDict(extra="forbid")

    position: str = Field(..., description="Position of sibling node: 'left' or 'right'")
    sibling_hash: str = Field(..., description="SHA-256 hash of the sibling node")


class KnowledgeChunk(BaseModel):
    """Deterministically partitioned text chunk with cryptographic Merkle proof."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(..., description="Unique chunk identifier: <document_id>_chk_<index>")
    document_id: str = Field(..., description="Parent document identifier")
    document_version: str = Field(..., description="Version of the parent document (e.g. v1.0.0)")
    chunk_index: int = Field(..., ge=0, description="0-indexed position within document")
    total_chunks: int = Field(..., gt=0, description="Total chunks in document")
    canonical_text: str = Field(..., description="Canonicalized text content")
    chunk_hash: str = Field(..., description="SHA-256 hash of canonical_text")
    merkle_proof: list[MerkleProofStep] = Field(
        default_factory=list, description="Ordered audit path from leaf to root"
    )
    merkle_root: str = Field(..., description="Expected Merkle root of the document")
    start_char_offset: int = Field(
        default=0, ge=0, description="Start offset in canonical document"
    )
    end_char_offset: int = Field(default=0, ge=0, description="End offset in canonical document")
    chunker_version: str = Field(default="1.0.0", description="Version of the chunking algorithm")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Domain metadata (CVE, ATT&CK ID, etc.)"
    )


class KnowledgeDocument(BaseModel):
    """Canonicalized threat knowledge document with content hash and Merkle root."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., description="Unique document identifier")
    source_id: str = Field(
        ...,
        description="Source identifier: mitre_attack, nvd_cve, cisa_kev, or consortium_incident_memory",
    )
    canonical_uri: str = Field(
        default="", description="Original upstream URL or resource reference"
    )
    version: str = Field(default="v1.0.0", description="Semantic or sequential version string")
    title: str = Field(..., description="Human-readable title of the threat intelligence document")
    content: str = Field(..., description="Canonicalized document body")
    content_sha256: str = Field(..., description="SHA-256 digest of canonical document content")
    merkle_root: str = Field(..., description="SHA-256 Merkle root of ordered document chunks")
    total_chunks: int = Field(default=0, ge=0, description="Number of constituent chunks")
    status: str = Field(
        default="active", description="Lifecycle status: 'active', 'superseded', or 'revoked'"
    )
    object_uri: str = Field(
        default="",
        description="MinIO/S3 object storage location: <source>/<doc_id>/<version>/<hash>.json",
    )
    canonicalizer_version: str = Field(default="1.0.0", description="Version of the canonicalizer")
    issued_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat(),
        description="Timestamp when document was published or issued upstream",
    )
    retrieved_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat(),
        description="Timestamp when document was ingested and anchored",
    )
    previous_version: str | None = Field(
        default=None, description="Previous version string if superseded"
    )
    endorsement: dict[str, Any] = Field(
        default_factory=dict, description="Consortium endorsements or cryptographic signatures"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Taxonomy and threat mapping metadata"
    )


class KnowledgeLedgerRecord(BaseModel):
    """Immutable ledger anchor record for a knowledge document on blockchain."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    source_id: str
    version: str
    content_sha256: str
    merkle_root: str
    total_chunks: int
    status: str
    object_uri: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    previous_version: str | None = None
