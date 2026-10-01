"""Deterministic chunking for threat knowledge documents."""

from __future__ import annotations

import hashlib
from typing import Any

from prorag_fl.knowledge.canonicalizer import canonicalize_text
from prorag_fl.schemas.knowledge import KnowledgeChunk

CHUNKER_VERSION = "1.0.0"


class DeterministicChunker:
    """Splits canonicalized threat documents into deterministic overlapping text chunks."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 60,
        chunker_version: str = CHUNKER_VERSION,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be strictly positive")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be non-negative and strictly less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunker_version = chunker_version

    def chunk_document(
        self,
        document_id: str,
        document_version: str,
        content: str,
        merkle_root_placeholder: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> list[KnowledgeChunk]:
        """Deterministically divide document content into ordered KnowledgeChunks.

        Preserves original offsets, records chunk indices, and hashes canonical text.
        """
        canonical_content = canonicalize_text(content)
        total_len = len(canonical_content)
        meta = metadata or {}

        if total_len == 0:
            empty_hash = hashlib.sha256(b"").hexdigest()
            return [
                KnowledgeChunk(
                    chunk_id=f"{document_id}_chk_0",
                    document_id=document_id,
                    document_version=document_version,
                    chunk_index=0,
                    total_chunks=1,
                    canonical_text="",
                    chunk_hash=empty_hash,
                    merkle_proof=[],
                    merkle_root=merkle_root_placeholder,
                    start_char_offset=0,
                    end_char_offset=0,
                    chunker_version=self.chunker_version,
                    metadata=meta,
                )
            ]

        # Sliding window chunking
        raw_chunks: list[tuple[int, int, str]] = []
        start = 0
        step = self.chunk_size - self.chunk_overlap

        while start < total_len:
            end = min(start + self.chunk_size, total_len)

            # If not at end, try to break cleanly at nearest whitespace/newline within last 40 chars
            if end < total_len:
                boundary = canonical_content.rfind(" ", start + step, end)
                nl_boundary = canonical_content.rfind("\n", start + step, end)
                chosen_split = max(boundary, nl_boundary)
                if chosen_split != -1 and chosen_split > start:
                    end = chosen_split

            chunk_text = canonical_content[start:end].strip()
            if chunk_text:
                raw_chunks.append((start, end, chunk_text))

            if end >= total_len:
                break
            start = end - self.chunk_overlap
            if start < 0 or (raw_chunks and start <= raw_chunks[-1][0]):
                start = end

        total_chunks = len(raw_chunks)
        chunks: list[KnowledgeChunk] = []

        for idx, (s_off, e_off, c_text) in enumerate(raw_chunks):
            c_hash = hashlib.sha256(c_text.encode("utf-8")).hexdigest()
            chunk_obj = KnowledgeChunk(
                chunk_id=f"{document_id}_chk_{idx}",
                document_id=document_id,
                document_version=document_version,
                chunk_index=idx,
                total_chunks=total_chunks,
                canonical_text=c_text,
                chunk_hash=c_hash,
                merkle_proof=[],
                merkle_root=merkle_root_placeholder,
                start_char_offset=s_off,
                end_char_offset=e_off,
                chunker_version=self.chunker_version,
                metadata=meta,
            )
            chunks.append(chunk_obj)

        return chunks
