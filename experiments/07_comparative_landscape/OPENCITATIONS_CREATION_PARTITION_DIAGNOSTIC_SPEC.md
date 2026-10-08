# OpenCitations creation-string partition diagnostic specification

Status: FROZEN_PRE_IMPLEMENTATION

## 1. Trigger

Wave 0 Attempt 05 reconstructed 12,845 unique valid OCIs for W0A07/PAML
forward citations while the independent OpenCitations citation-count endpoint
reported 12,846.

Diagnostic Attempt 01 then attempted an unfiltered CSV representation of the
same citation-data operation. That response failed with `IncompleteRead` after
all five bounded transport attempts.

A second diagnostic must therefore avoid another large unpartitioned response.

## 2. Purpose

This diagnostic tests the W0A07 citation-data result through a partition axis
independent of OCI.

The partition field is `creation`.

The diagnostic asks whether an independently partitioned citation-data
retrieval reconstructs:

- 12,846 rows;
- 12,845 rows; or
- another result.

It must not weaken the production completeness gate.

## 3. Raw-string semantics

`creation` is treated only as a raw returned string.

The diagnostic does not require or assume that every value is a complete
`YYYY-MM-DD` calendar date.

This is necessary because the frozen Attempt-05 corpus contains:

- complete dates;
- reduced-precision year-month values;
- reduced-precision year values; and
- empty values.

No creation value is normalized, imputed or discarded.

## 4. Frozen target

Only the following operation is diagnosed:

- source: OpenCitations Index v2;
- anchor: W0A07;
- tool: PAML;
- DOI: `10.1093/molbev/msm088`;
- direction: forward incoming citations.

## 5. Diagnostic sequence

The source-level sequence is:

1. retrieve the independent citation count;
2. retrieve the complete citation-data result through deterministic
   `creation`-string partitions;
3. retrieve the independent citation count again.

The two count requests bracket the partition retrieval.

## 6. Root partition

The root partition consists of twelve mutually exclusive categories:

1. empty string:

   `^$`

2. non-empty value beginning with a non-digit:

   `^[^0-9].*$`

3. ten digit-prefix buckets:

   `^0.*$`
   through
   `^9.*$`

For any present string value, these categories are mutually exclusive and
collectively exhaustive.

## 7. Recursive subdivision

A digit/hyphen prefix bucket may be recursively subdivided only if its request
exhausts the bounded retry policy because of `http.client.IncompleteRead`.

For a current literal prefix `P`, the parent is:

`^P.*$`

It is replaced by:

### Exact-prefix child

`^P$`

### Decimal children

`^P0.*$`
through
`^P9.*$`

### Hyphen child

`^P-.*$`

### Other-character child

`^P[^0-9-].*$`

These thirteen children are mutually exclusive and their union is exactly the
parent string language.

The exact child ensures that reduced-precision values such as `2021` or
`2021-03` are retained when a longer-prefix bucket is subdivided.

## 8. Unexpected strings

The diagnostic is not restricted to valid dates.

Unexpected creation strings are retained by either:

- the root non-digit bucket; or
- an `other-character` recursive child.

Such values are reported descriptively.

They are not discarded.

## 9. Missing versus empty field

Every citation row returned by a creation-filtered request must contain the
`creation` field.

An empty field is valid diagnostic data and belongs to the `^$` root bucket.

If the independent count exceeds the complete creation-partition row union,
the diagnostic must fail or report the discrepancy; it must not assume that
the missing relationship has a creation value.

Thus a countable relationship lacking an exposed `creation` field remains a
possible explanation if exact count reconciliation is not achieved.

## 10. Transport policy

Each filtered request uses the existing bounded five-attempt policy.

Incomplete bodies are discarded.

Subdivision is permitted only after exhausted
`http.client.IncompleteRead` on a subdividable prefix bucket.

Other persistent request failures remain fail-closed.

## 11. Recursion ceiling

The literal creation prefix may not exceed 32 characters.

Reaching this transport-safety ceiling is a diagnostic failure.

The ceiling has no scientific meaning.

## 12. Leaf validation

Every completed leaf records its exact regex.

Every returned row must:

- contain `creation`; and
- have a raw creation value matching that leaf regex exactly.

A row outside its leaf is a partition-integrity failure.

## 13. Cross-leaf duplicate handling

No row is silently deduplicated before diagnostic accounting.

For each returned row, a canonical full-row signature is formed from the
complete returned citation fields.

An identical row appearing more than once across completed leaves is reported
as a partition-integrity failure.

OCI duplicates are analysed separately because OCI itself is the object under
diagnosis.

## 14. Count reconciliation

When the pre-count and post-count are equal, the complete partition row count
is compared directly with that stable independent count.

No partial partition union is accepted.

If the bracketing counts differ, source count state changed during the
diagnostic interval and the result is reported separately.

## 15. OCI analysis after creation retrieval

The creation-partition result is analysed without using OCI for partition
membership.

Each row's OCI is classified as:

- empty;
- valid numeric OCI matching `^[0-9]+-[0-9]+$`; or
- nonconforming.

Valid OCI duplicates are reported.

The complete valid-OCI set is compared with the frozen Attempt-05 12,845-OCI
union.

Both set differences are preserved.

## 16. Interpretation

If stable bracketing counts equal 12,846 and creation partitioning returns
12,846 rows, the additional row or OCI representation can be inspected
directly.

If stable bracketing counts equal 12,846 and creation partitioning returns
12,845 rows, the OCI terminal-digit partition is no longer a unique explanation
for the one-record deficit. The result remains compatible with a source
count/data discrepancy or with a countable relationship not exposed through
creation-filtered citation data.

If the bracketing counts differ, source-state change during the diagnostic
interval is established at the count level.

Any other outcome is reported descriptively.

## 17. Scientific isolation

This is source forensics only.

It performs no relevance screening, comparator classification, citation
universe inclusion decision, Wave 1 promotion or change to the chaining
saturation rule.

## 18. Attempt 05 remains failed

Diagnostic results cannot retroactively convert Attempt 05 into a successful
production corpus.

The Wave 0 production acceptance gate remains unchanged.
