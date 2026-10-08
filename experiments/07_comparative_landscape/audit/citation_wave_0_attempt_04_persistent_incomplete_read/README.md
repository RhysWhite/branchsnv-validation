# Citation Wave 0 production Attempt 04

Status: FAILED_DURING_RETRIEVAL

Attempt 04 used the hardened citation retriever in which
`http.client.IncompleteRead` is retryable under the existing bounded retry
policy.

The run again reached Wave 0 anchor W0A07 (PAML), OpenCitations forward
citation retrieval.

## Failure

The OpenCitations forward citation-data request failed on all five bounded
attempts.

The final attempt raised `http.client.IncompleteRead` after 859,003 response
bytes had been received, with 3,953,541 additional bytes still expected.

The retriever then failed closed with:

`Request failed after 5 attempts`

## Interpretation

Attempt 03 established that a single unpartitioned OpenCitations response
could terminate prematurely.

Attempt 04 establishes that ordinary bounded whole-response retry is
insufficient for this endpoint.

This is therefore treated as a persistent large-response transport problem,
not as a reason to increase retries indefinitely and not as a scientific
search failure.

The independent OpenCitations citation-count response completed. The failed
forward citation body was never written to the raw corpus. W0A08 had not
started.

## Preservation

Every successfully written response is preserved byte-for-byte in this audit,
with an inventory, per-file hashes, and a deterministic raw archive.

No record from this partial retrieval was screened or used for scientific
classification.

## Next implementation requirement

Before another production attempt, large OpenCitations response retrieval must
be made deterministic and partitionable while preserving the same complete
citation set.

Any partition scheme must:

- operate on the same OpenCitations Index v2 citation endpoint/data;
- introduce no scientific relevance filter;
- cover mutually auditable portions of the citation result;
- reconcile the union against the independently retrieved citation count;
- detect duplicate citation identities; and
- fail closed if the reconstructed union is incomplete.

The partition strategy must be frozen and regression-tested before production
reuse.
