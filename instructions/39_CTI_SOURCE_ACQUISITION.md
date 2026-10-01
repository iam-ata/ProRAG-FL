# CTI Source Acquisition and Corpus Construction

## Principle
The corpus is part of the experiment. Its acquisition time, source, version and transformation must be reproducible.

## Authorized source families
- MITRE ATT&CK;
- NVD/CVE;
- CISA KEV/advisories;
- approved consortium incident records.

Do not silently add arbitrary blogs/search results to the trusted corpus.

## Acquisition manifest
For every fetched source artifact record:
- source ID/name;
- canonical URL/API endpoint identifier;
- retrieval timestamp;
- upstream release/version/date if available;
- SHA-256 of downloaded raw content;
- HTTP metadata where useful;
- parser version;
- license/redistribution note.

## Raw-source preservation
Store fetched raw CTI in a gitignored/raw-knowledge cache or object store. Preserve the exact input from which canonical documents were derived.

## Normalization
Map source-specific data to common fields without deleting security-relevant facts. Keep original source identifiers (CVE IDs, ATT&CK IDs, advisory IDs) in metadata.

## Time consistency
For experiments that emulate a historical cutoff, the corpus must obey the cutoff. For the primary current-corpus experiment, record corpus snapshot date so future reproduction knows what knowledge was available.

## Leakage distinction
External CTI knowing the held-out Mirai/Malware family is permitted because the experiment is unseen-to-model. However, do not insert final test rows, their exact feature vectors, or ground-truth outputs into the knowledge store.

## Corpus summary report
Generate:
- documents by source;
- chunks by source;
- date distribution;
- unique CVE/ATT&CK/advisory IDs;
- active/revoked versions;
- corpus size;
- Merkle roots/manifest hashes.

Freeze a corpus manifest hash for every final RAG experiment.
