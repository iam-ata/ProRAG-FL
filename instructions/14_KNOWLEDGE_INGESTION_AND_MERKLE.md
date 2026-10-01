# Phase 6 — Threat-Knowledge Ingestion and Merkle Provenance

## Common schemas
`KnowledgeDocument`: document ID, source ID, canonical URI, version, title, issued/retrieved times, status, object URI, content hash, Merkle root, metadata.

`KnowledgeChunk`: chunk ID, document ID/version, chunk index, canonical text, chunk hash, Merkle proof, metadata.

## Authorized source adapters
Implement modular adapters for:
- MITRE ATT&CK;
- NVD/CVE;
- CISA advisories/KEV;
- consortium incident memory.

Start with one source end-to-end; then generalize. Do not mix source-specific parsing with generic indexing.

## Canonicalization
Before hashing:
- consistent Unicode normalization;
- line-ending normalization;
- deterministic whitespace/transport cleanup only;
- UTF-8 encoding;
- version the canonicalizer.

Changing canonicalization changes hashes and must create a new provenance version.

## Deterministic chunking
Persist chunk size, overlap, tokenizer/version, original offsets and chunker version. The same document/version must always reproduce the same ordered chunks.

## Merkle tree
For ordered chunks:
```text
leaf_k = SHA256(canonical_chunk_bytes)
parent = SHA256(left_hash || right_hash)
```
Define exact binary/hex encoding and odd-leaf behavior. Unit-test with fixed vectors.

## MinIO
Store immutable/versioned canonical objects, e.g.:
```text
<source>/<document_id>/<version>/<content_sha256>.json
```
Never overwrite historical content under the same provenance key.

## Ledger record
Store document/source/version/content hash/root/status/timestamps/previous version/endorsement metadata.

## Tamper test
Modify one retrieved/indexed chunk while retaining the old proof/root. Verification must fail.

## Version/revocation
A new upstream document version creates a new canonical object and root. Preserve history, update active version, and let retrieval use active content unless the experiment deliberately tests stale replay.
