# Retrieval attempt 04 — completed high-recall expansion

Attempt 04 is the completed retrieval for the single generic high-recall
expansion specified under Amendment 03.

Retrieval was executed from repository commit:

`6b3e5338f97f79bcdf0ee51af89862986f1178b8`

## Result

- candidate source/query rows: 113,448
- deduplicated records: 78,962
- queries: 5
- source/query retrievals: 15
- status: COMPLETE

All reported source-query counts equalled retrieved counts.

PubMed HR05 exceeded the single-query ESearch identifier ceiling and was
retrieved using the deterministic EDAT partitioning specified in Amendment 04.
The original count, EDAT-envelope count, terminal-interval count sum, retrieved
PMID count, and unique PMID count were all exactly 12,654. The scientific
Title/Abstract query was not modified.

No retrieved records had been screened, classified for eligibility, assigned
capabilities, or selected for benchmarking before this corpus was completed.

The complete local corpus is cryptographically fixed by
`corpus_checksums.sha256`. The audit record additionally preserves the
retrieval manifest, source/query counts, PubMed partition metadata, complete
console log, and file-size inventory.

The complete raw corpus is not committed as part of this audit commit pending
a separate storage/archive decision because of its substantially larger size.
