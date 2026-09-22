# Experiment 07 citation retrieval implementation

Status: FROZEN_PRE_PRODUCTION_RETRIEVAL

The implementation in `retrieve_citation_wave.py` operationalizes the frozen
citation-chaining protocol without scientific prefiltering.

## OpenAlex

Wave anchors are resolved from DOI to an OpenAlex Work.

Backward citation edges are taken from the resolved Work's complete
`referenced_works` array. The implementation requires
`referenced_works_count` to equal the retrieved array length.

Forward citations are obtained from the OpenAlex Works collection using the
`cites:<anchor Work ID>` filter with cursor pagination.

The implementation requires the final unique retrieved Work count to equal the
count reported by OpenAlex.

HTTP 404 during anchor resolution is recorded as `not_indexed`. A successfully
resolved operation with zero edges is `resolved_zero_edges`.

## OpenCitations

OpenCitations Index v2 is queried with independent count and data
operations:

- `/reference-count/doi:<DOI>` followed by `/references/doi:<DOI>` for
  backward citation edges;
- `/citation-count/doi:<DOI>` followed by `/citations/doi:<DOI>` for
  forward citation edges.

The number of citation rows retrieved must equal the independently reported
count. A mismatch fails closed.

Returned DOI, PMID, and OMID values are retained.

A successful count of zero reconciled to an empty citation response is
`resolved_zero_edges`. HTTP 404 from the count endpoint is `not_indexed`. If
the count endpoint resolves an anchor but the corresponding citation-data
endpoint returns 404, retrieval fails closed.

## Credentials

`OPENALEX_API_KEY` is required for production execution and is supplied only
through the HTTP `Authorization` header. It is not placed in request URLs.

`OPENCITATIONS_ACCESS_TOKEN` is optional and, when present, is supplied only
through the HTTP authorization header.

Credential values are never serialized to result files or intentionally
included in logged request URLs.

## Completeness

Every anchor must receive a terminal status for all four combinations:

- OpenAlex backward;
- OpenAlex forward;
- OpenCitations backward;
- OpenCitations forward.

The retriever fails closed if this matrix is incomplete or if a reported count
does not equal the retrieved count. Both citation sources therefore have an
independent count reconciliation: OpenAlex uses its Work/list metadata and
OpenCitations uses the Index v2 count endpoints.

## Transport retries

Transient transport failures handled by the common JSON fetcher include:

- URL/network errors;
- timeouts;
- `http.client.IncompleteRead`; and
- JSON decoding failures.

An `IncompleteRead` discards the incomplete body and retries the same request
from the beginning under the existing bounded retry policy.

A raw response file is written only after the complete HTTP body has been
received. Consequently, an incomplete HTTP body is not accepted as a raw
citation response.

If all retry attempts fail, retrieval terminates and the wave remains
incomplete.

## Deterministic OpenCitations OCI partitioning

For every OpenCitations source-direction operation, the independent
`citation-count` or `reference-count` request is performed first.

If that count is zero, the operation terminates as `resolved_zero_edges`
without issuing citation-data partition requests.

For every positive count, citation-data retrieval uses the frozen deterministic
OCI partition specification rather than an unfiltered whole-response request.

The root consists of ten regular-expression filters over the terminal decimal
digit of the variable OCI component:

- citing OCI component for forward citations;
- cited OCI component for backward references.

Every successful leaf response is validated before acceptance:

- every row must contain an OCI;
- every OCI must satisfy `^[0-9]+-[0-9]+$`;
- every OCI must belong to the leaf regex that retrieved it.

After all leaves complete, OCI identity is globally reconciled for that
anchor × source × direction operation. Duplicate OCIs are fatal, and the
number of unique OCIs must equal the independent count exactly.

If a filtered non-exact leaf exhausts the bounded request retry policy with
`http.client.IncompleteRead` as its cause, it is replaced deterministically by
an exact-number child followed by ten next-terminal-digit children.

No other exhausted exception class silently triggers partition subdivision.

The maximum variable-component suffix length is 64 decimal digits.
Reaching that ceiling fails closed.

Every completed partition leaf is retained separately under the raw response
tree and is recorded in `opencitations_partition_leaves.tsv`, including its
direction, execution order, recursion depth, suffix, regex, request hash,
raw-response path and row count.

The original unpartitioned failed responses from earlier production attempts
are not reused.

## Raw responses

Every successful API response used to construct an edge is retained under the
wave output's `raw/` directory.

## Scope of this implementation

This implementation retrieves citation graph edges and available source
metadata.

It does not:

- screen citation records;
- classify software;
- resolve OpenCitations-only records to full bibliographic metadata;
- deduplicate the cross-source citation union;
- promote new anchors; or
- assess saturation.

Those operations occur only after the raw citation wave has been frozen.
