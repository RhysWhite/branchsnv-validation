# Citation Wave 0 production Attempt 03

Status: FAILED_DURING_RETRIEVAL

Attempt 03 was the first Wave 0 production execution to reach the citation
APIs.

Multiple OpenAlex and OpenCitations responses were retrieved successfully
before the run failed while reading one OpenCitations response.

## Failure

Python raised `http.client.IncompleteRead`.

The contemporaneous traceback reports:

- 139,129 response bytes received;
- 4,673,415 additional bytes expected.

The response therefore terminated before its declared body was complete.

## Failure localization

The untouched raw-response tree establishes the failing operation as:

- anchor: W0A07 / PAML;
- source: OpenCitations;
- direction: forward;
- count request: completed;
- citation-data response: not written;
- next anchor W0A08: not started.

The retriever writes a raw response only after `response.read()` completes and
the payload is decoded. Therefore the incomplete W0A07 forward response itself
is not present in the saved raw corpus.

## Preservation

Every successfully written raw response was validated as JSON and hashed.

The complete untouched partial raw tree is preserved in a deterministic
`partial_wave_0_raw.tar.gz` archive. Its exact file inventory and per-file
SHA256 values are retained in this audit.

## Interpretation

This is a transport/retrieval failure, not a search, screening, or scientific
classification result.

No citation record from this partial attempt was screened for relevance, no
software method was classified, and no new anchor was promoted.

The partial retrieval must not be used for Wave 0 scientific analysis.

## Required implementation response

The frozen retriever currently retries selected HTTP and URL errors but does
not catch `http.client.IncompleteRead`.

Any retry hardening must be specified and regression-tested after this failed
attempt is frozen. It may change transport robustness only; it must not change
citation sources, anchors, queries, filtering, screening, or the saturation
rule.
