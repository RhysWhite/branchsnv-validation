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

`OPENALEX_API_KEY` is required for production execution.

`OPENCITATIONS_ACCESS_TOKEN` is optional and, when present, is sent in the
authorization header.

Credential values are never serialized to result files.

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
