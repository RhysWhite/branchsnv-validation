# OpenCitations creation-partition diagnostic implementation

Status: FROZEN_PRE_EXECUTION after successful offline validation.

This implementation executes the OCI-independent diagnostic frozen in
`OPENCITATIONS_CREATION_PARTITION_DIAGNOSTIC_SPEC.md`.

It is separate from both the Wave 0 production retriever and Diagnostic 01.

## Comparator identity

The frozen Attempt-05 comparator contains:

- 12,845 citation rows;
- 12,845 unique complete rows;
- 12,845 unique numeric OCIs;
- one uniform seven-field schema.

The canonical complete-row multiset SHA-256 is:

`82e2992dda9fe3f3d5a18cb417343edb47ba1af617832aec3b2f241d5500e928`

## Source sequence

The implementation performs:

1. citation-count;
2. deterministic `creation`-string partition retrieval;
3. citation-count.

All responses use JSON.

## Root partition

The creation string is partitioned into:

- empty;
- non-empty/non-digit first character;
- first digit 0 through 9.

No OCI information participates in partition assignment.

## Recursive transport subdivision

Only a literal-prefix leaf that exhausts bounded retries specifically because
of `http.client.IncompleteRead` may subdivide.

Its deterministic children are:

1. exact prefix;
2. prefix + digits 0 through 9;
3. prefix + hyphen;
4. prefix + any other character.

This exactly partitions the parent string language.

The maximum literal prefix length is 32 characters. Reaching that ceiling
fails closed.

## Row integrity

Every successful citation row must expose a string-valued `creation` field and
must match its leaf regular expression.

Complete citation rows are canonicalized using deterministic JSON
serialization.

An identical complete row occurring more than once in the reconstructed union
is a partition-integrity failure.

## OCI analysis

OCI is analysed only after the creation-based result has been reconstructed.

Empty, nonconforming and duplicated OCIs are reported.

Valid numeric OCI set differences against Attempt 05 are preserved.

## Output isolation

The result is explicitly marked as diagnostic and non-production.

It cannot itself satisfy the Wave 0 production gate or reclassify Attempt 05.
