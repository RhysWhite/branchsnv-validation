# Attempt 04 storage policy

The complete high-recall retrieval contains 1,005 files totalling
354,306,316 bytes according to the frozen file inventory.

The raw API-response tree is intentionally not stored in Git history.
Instead, it has been packaged as a deterministic gzip-compressed tar archive:

`high_recall_attempt_04_raw.tar.gz`

SHA-256:

`56ef95ff2e337ec17f2601753eea020c0584c56e7d7e57305208ed40ee93f96c`

The archive contains the complete `raw/` subtree from the verified
Attempt 04 corpus. A second independently generated archive was byte-identical.

The normalized candidate and deduplicated tables, retrieval metadata, and
source/query counts are retained separately as the downstream screening
inputs.

The raw archive is retained locally pending archival with the validation
release (for example as a Zenodo release asset). Raw API responses are not
required to perform eligibility screening once the normalized corpus has been
frozen, but are retained for retrieval-level provenance.
