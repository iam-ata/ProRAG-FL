"""Deterministic text canonicalization for threat intelligence provenance."""

from __future__ import annotations

import re
import unicodedata

CANONICALIZER_VERSION = "1.0.0"


def canonicalize_text(text: str) -> str:
    """Normalize text deterministically before hashing or chunking.

    Adheres strictly to instructions/14_KNOWLEDGE_INGESTION_AND_MERKLE.md:
    1. Unicode normalization (NFC)
    2. Line-ending normalization (\\r\\n -> \\n, \\r -> \\n)
    3. Trailing whitespace stripping per line
    4. Collapse 3+ consecutive newlines to 2 newlines (paragraph boundary preservation)
    5. Strip overall leading/trailing whitespace
    """
    if not text:
        return ""

    # 1. Unicode normalization (NFC)
    norm = unicodedata.normalize("NFC", text)

    # 2. Line ending normalization
    norm = norm.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Strip trailing whitespace from every line
    lines = [line.rstrip() for line in norm.split("\n")]
    norm = "\n".join(lines)

    # 4. Collapse excessive consecutive blank lines (max 2 newlines = 1 blank line)
    norm = re.sub(r"\n{3,}", "\n\n", norm)

    # 5. Strip document start and end whitespace
    return norm.strip()


def compute_canonical_hash(text: str) -> str:
    """Compute deterministic SHA-256 digest of canonicalized UTF-8 bytes."""
    import hashlib

    canonical_str = canonicalize_text(text)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
