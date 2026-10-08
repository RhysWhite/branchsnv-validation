# OpenCitations count-mismatch diagnostic implementation

Status: FROZEN_PRE_EXECUTION after successful offline validation.

This implementation executes the source-forensic diagnostic frozen in
`OPENCITATIONS_COUNT_MISMATCH_DIAGNOSTIC_SPEC.md`.

It is separate from the Wave 0 production citation retriever.

## Frozen target

- W0A07
- PAML
- DOI `10.1093/molbev/msm088`
- OpenCitations forward citations only

## Request sequence

Exactly three successful source operations are required:

1. unfiltered citation count, JSON;
2. unfiltered citations, CSV;
3. unfiltered citation count, JSON.

No relevance, date, software-name or other scientific filter is used.

## Raw preservation

The complete successful response body for each operation is written only after
the HTTP body has been read completely.

Incomplete bodies are not accepted or written.

Transient transport errors use at most five attempts.

## Attempt-05 comparator

The comparison set is reconstructed directly from the committed deterministic
Attempt-05 raw archive.

The implementation requires:

- all ten W0A07 forward root leaves;
- exactly 12,845 archived unique OCIs;
- valid numeric OCI syntax;
- no duplicate archived OCI; and
- correct suffix membership.

## CSV handling

The complete raw CSV response is retained byte-for-byte.

Parsing requires the fields:

- `oci`;
- `citing`; and
- `cited`.

Every CSV row is retained for interpretation.

OCI values are classified as:

- empty;
- valid numeric OCI; or
- nonconforming OCI.

Duplicate valid OCIs are reported rather than silently collapsed.

## Comparison outputs

The diagnostic records:

- bracketing counts;
- raw CSV row count;
- valid, empty and nonconforming OCI counts;
- duplicate valid OCIs;
- CSV-only OCIs;
- Attempt-05-only OCIs;
- complete CSV rows corresponding to CSV-only OCIs;
- exceptional OCI rows; and
- a descriptive interpretation class.

## Isolation

The diagnostic output is explicitly marked:

- `production_corpus = false`;
- `scientific_screening = false`;
- `attempt_05_reclassified = false`.

Its result cannot itself satisfy the Wave 0 production gate.
