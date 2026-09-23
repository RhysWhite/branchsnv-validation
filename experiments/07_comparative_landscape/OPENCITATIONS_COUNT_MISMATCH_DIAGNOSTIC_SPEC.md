# OpenCitations independent-count mismatch diagnostic specification

Status: FROZEN_PRE_EXECUTION

## 1. Trigger

Wave 0 production Attempt 05 failed closed for W0A07 / PAML forward
OpenCitations retrieval.

The independent `/citation-count/{id}` response reported:

12,846

The complete deterministic ten-leaf OCI partition union contained:

12,845 unique citation rows.

All ten terminal-digit root partitions completed.

Every returned OCI:

- was non-empty;
- matched the documented numeric OCI lexical form;
- belonged to the expected terminal-digit partition; and
- was unique across the ten-leaf union.

Attempts 03, 04 and 05 each independently returned the same W0A07 forward
citation count of 12,846.

No Attempt-05 citation result was accepted for scientific screening.

## 2. Purpose

The diagnostic must distinguish among materially different explanations for
the one-record discrepancy without changing the production retrieval
criterion.

The principal hypotheses are:

1. source-state change during retrieval;
2. count/data endpoint semantic inconsistency;
3. filtered-data semantics differing from unfiltered citation-data semantics;
4. a citation row that does not possess the assumed simple numeric OCI
   representation; or
5. another OpenCitations source-level condition not yet established.

These are diagnostic hypotheses, not conclusions.

## 3. Frozen target

The diagnostic target is only:

- anchor: W0A07 / PAML;
- DOI: 10.1093/molbev/msm088;
- direction: forward incoming citations;
- source: OpenCitations Index v2.

No other anchor is queried.

## 4. API operations

The diagnostic sequence is:

1. retrieve `/citation-count/doi:10.1093/molbev/msm088`;
2. retrieve the unfiltered `/citations/doi:10.1093/molbev/msm088`
   operation using `Accept: text/csv`;
3. retrieve `/citation-count/doi:10.1093/molbev/msm088` again.

The CSV request contains no `filter`, `require`, `sort`, relevance term,
software term, date condition or other scientific restriction.

## 5. Why CSV is diagnostic

OpenCitations Index v2 documents both JSON and CSV output according to the
requested MIME type.

The earlier whole-response transport failures occurred while retrieving the
large JSON citation response.

CSV is used here only as a lower-overhead serialization of the same
unfiltered `/citations/{id}` operation.

It is not substituted into the production corpus unless a later separately
frozen amendment explicitly establishes that this is appropriate.

## 6. Temporal bracketing

The independent count is collected immediately before and immediately after
the unfiltered CSV retrieval.

Interpretation:

- if pre-count != post-count, source state changed during the diagnostic
  interval;
- if pre-count == post-count, no count-level change was observed during that
  interval.

Equal bracketing counts do not prove the underlying citation set was immutable;
they only show count stability.

## 7. Frozen Attempt-05 comparator

The Attempt-05 partition union must be reconstructed only from the committed
Attempt-05 deterministic raw archive.

The live failed-attempt directory is not required and must not be reused.

The expected frozen Attempt-05 facts are:

- independent count: 12,846;
- partition rows: 12,845;
- unique OCIs: 12,845;
- duplicate OCIs: 0;
- root partitions: 10.

## 8. CSV preservation

The exact HTTP response body from the successful unfiltered CSV request must
be preserved byte-for-byte.

The pre-count and post-count JSON responses must also be preserved.

No successfully retrieved diagnostic response may be silently overwritten.

## 9. Transport policy

The diagnostic uses a bounded maximum of five attempts for transient
transport errors.

An incomplete response body is discarded and is not written as a successful
diagnostic response.

The retry policy must not modify the request between attempts.

If all attempts fail, the diagnostic fails and is frozen as such.

## 10. CSV structural validation

A successful CSV response must:

- parse with a single header row;
- contain the documented citation fields required for this comparison,
  including `oci`, `citing` and `cited`;
- contain only data rows represented as CSV records;
- preserve every row before any OCI-based interpretation.

The raw row count and parsed row count are recorded.

## 11. OCI analysis

For every CSV citation row, record whether `oci` is:

- empty;
- a single valid numeric OCI matching `^[0-9]+-[0-9]+$`; or
- non-empty but nonconforming.

No nonconforming row is silently discarded.

For valid numeric OCIs:

- duplicates are identified explicitly;
- the unique OCI set is calculated.

## 12. Comparison with Attempt 05

The diagnostic records:

- CSV data-row count;
- CSV rows with empty OCI;
- CSV rows with nonconforming OCI;
- CSV valid numeric OCI count;
- CSV unique valid numeric OCI count;
- duplicate valid OCI count;
- Attempt-05 unique OCI count;
- CSV OCI minus Attempt-05 OCI set;
- Attempt-05 OCI minus CSV OCI set.

Any differing records are preserved with their complete CSV fields.

## 13. Interpretation matrix

### A. Bracketing count changed

If the pre- and post-count differ, the diagnostic establishes count-level
source-state change during the diagnostic interval.

No production rule changes automatically follow.

### B. Counts stable at 12,846 and CSV has 12,846 unique valid OCIs

If the CSV contains 12,846 unique valid numeric OCIs while Attempt 05 contains
12,845, the exact OCI set difference is identified.

This establishes that the unfiltered citation-data representation can expose a
relationship absent from the frozen filtered partition union at those
respective retrieval times.

A later diagnostic may then test only the corresponding frozen partition query.

### C. Counts stable at 12,846 and CSV has 12,845 citation rows

This demonstrates a contemporaneous discrepancy between the count endpoint and
the unfiltered citation-data operation, subject to successful complete CSV
transport.

### D. Counts stable at 12,846 and CSV contains 12,846 rows but fewer than
12,846 valid numeric OCIs

The exceptional row or rows are retained explicitly.

This would test the hypothesis that a countable citation relationship can be
represented outside the assumed simple numeric OCI set.

### E. Other result

Any result not covered above is reported descriptively and remains unresolved.

## 14. Scientific isolation

This diagnostic is source forensics only.

It performs no:

- relevance screening;
- comparator eligibility decision;
- direct/near-direct classification;
- citation-universe reconciliation;
- Wave 1 promotion; or
- change to the citation-chaining saturation rule.

## 15. Production gate remains unchanged

The production acceptance criterion remains:

complete source retrieval plus exact reconciliation to its frozen completeness
checks.

Attempt 05 remains a failed production attempt regardless of the outcome of
this diagnostic.

A successful diagnostic does not retroactively convert Attempt 05 into a
successful Wave 0 corpus.
