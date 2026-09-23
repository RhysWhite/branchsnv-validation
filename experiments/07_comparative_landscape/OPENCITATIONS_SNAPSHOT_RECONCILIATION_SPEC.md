# OpenCitations dual-axis snapshot reconciliation specification

Status: FROZEN_PRE_IMPLEMENTATION

## 1. Purpose

OpenCitations citation chaining requires a fail-closed completeness check that
remains reliable despite:

- large whole-response transport failures;
- asynchronous or evolving source state; and
- the possibility of a partition-specific omission.

The production retriever will therefore validate every positive-count
OpenCitations operation through two independently defined partition axes.

The scientific citation-chaining protocol is unchanged.

## 2. Evidence motivating this change

Wave 0 Attempt 05 returned an independent citation count of 12,846 for
W0A07/PAML but reconstructed 12,845 unique rows through the frozen OCI
terminal-digit partition.

No malformed OCI, duplicate OCI, incomplete root partition or recursive
transport failure was found in that reconstruction.

A subsequent unfiltered CSV diagnostic again failed whole-response transport.

A later diagnostic partitioned the same source operation exclusively on the
raw `creation` field. Its pre-count and post-count were both 12,846, and the
independent creation-partition union contained exactly:

- 12,846 citation rows;
- 12,846 unique complete rows;
- 12,846 unique valid numeric OCIs; and
- zero duplicate valid OCIs.

Comparison of the Attempt-05 and later diagnostic snapshots established
relationship-set evolution between retrieval times.

These observations do not establish an OCI-partition algorithm defect.

## 3. Scope

This reconciliation applies to every OpenCitations source-direction operation
with a positive independent count.

It applies uniformly to forward citations and backward references.

It is not specific to W0A07/PAML.

## 4. Snapshot attempt

One complete snapshot attempt consists of:

1. independent count before data retrieval;
2. complete OCI-partition retrieval;
3. complete creation-string-partition retrieval;
4. independent count after data retrieval;
5. within-axis integrity validation;
6. cross-axis reconciliation.

No rows from different snapshot attempts may be combined.

## 5. Count bracketing

Let:

- `Cpre` be the independent count before partition retrieval;
- `Cpost` be the independent count after partition retrieval.

An attempt can be accepted only if:

`Cpre == Cpost`

For positive counts, both independent partition unions must also contain
exactly that number of complete rows.

## 6. OCI partition axis

The existing frozen deterministic OCI partition remains the primary production
retrieval axis.

Its current mathematical and transport rules remain unchanged.

Every returned OCI must remain syntactically valid and belong to its recorded
partition.

Duplicate OCI relationships remain fatal.

## 7. Creation partition axis

The independently validated raw-string `creation` partition becomes a
production completeness witness.

It uses the generic partition defined by the creation-partition diagnostic:

- explicit empty-string root;
- explicit non-digit root;
- digit-prefix roots 0 through 9;
- deterministic exact/digit/hyphen/other-character recursion after exhausted
  `IncompleteRead`;
- bounded prefix-length ceiling.

The creation axis does not use OCI for partition membership.

Every returned row must expose a string-valued `creation` field and match its
recorded leaf.

## 8. Complete-row identity

For each axis, every citation row is serialized canonically using:

- complete returned row object;
- lexicographically sorted JSON keys;
- UTF-8;
- no semantically irrelevant whitespace.

Within one axis, duplicate canonical complete rows are fatal.

After each axis is complete, its canonical complete-row multiset is sorted and
hashed.

## 9. Cross-axis acceptance gate

A positive-count snapshot attempt is accepted only when all of the following
hold:

1. `Cpre == Cpost`;
2. OCI-axis complete-row count equals `Cpre`;
3. creation-axis complete-row count equals `Cpre`;
4. OCI-axis canonical complete rows are unique;
5. creation-axis canonical complete rows are unique;
6. the two canonical complete-row sets are exactly equal;
7. the OCI sets reconstructed independently from both axes are exactly equal;
8. neither axis has a transport, schema, partition-membership, recursion-ceiling
   or integrity failure.

Count equality alone is insufficient.

OCI-set equality alone is insufficient.

Exact complete-row equality across the independently partitioned axes is
required.

## 10. Canonical production corpus

When a snapshot attempt passes every reconciliation gate, the OCI-partition
union is the canonical OpenCitations production corpus.

The creation-partition union is retained only as an independent completeness
witness.

It is not added as a second citation source and is never double-counted.

## 11. Zero-count operations

If `Cpre == 0`, no data-partition request is required.

A post-count is still retrieved.

The operation is accepted as an empty result only if:

`Cpre == Cpost == 0`

Otherwise the snapshot attempt is unresolved.

## 12. Whole-snapshot retries

A source-reconciliation failure may trigger a fresh whole-snapshot attempt.

Maximum complete snapshot attempts:

3

This is an operational safety limit, not a scientific threshold.

A retry starts again from a new pre-count.

No successful response, partition leaf or row from the previous failed
snapshot attempt may be reused in the next attempt.

Every attempt is preserved separately.

## 13. Retry-eligible snapshot failures

A fresh whole-snapshot retry is permitted for:

- pre/post count disagreement;
- either complete partition union disagreeing with the stable count;
- cross-axis complete-row disagreement;
- cross-axis OCI-set disagreement; or
- exhausted retryable transport failure.

## 14. Non-retryable integrity failures

The following fail the source operation immediately:

- malformed returned row structure;
- malformed OCI where OCI is required;
- row outside its declared partition;
- duplicate complete row within one axis;
- duplicate OCI where prohibited;
- missing/non-string `creation` in a returned creation-partition row;
- deterministic recursion-ceiling exhaustion caused by a non-resolvable
  partition language;
- invariant or implementation failure.

These conditions are not treated as evidence of transient source evolution.

## 15. Accepted-attempt provenance

The source-operation record must state:

- accepted snapshot-attempt number;
- pre-count;
- post-count;
- OCI-axis row count;
- creation-axis row count;
- OCI-axis complete-row multiset hash;
- creation-axis complete-row multiset hash;
- OCI-set hash for each axis;
- equality of both complete-row sets;
- equality of both OCI sets;
- leaf counts and maximum recursion depth for both axes.

Failed snapshot attempts remain auditable and are not silently discarded.

## 16. Source evolution

A failed snapshot attempt is not automatically interpreted as a software
defect.

The retriever records the observed mismatch mechanically.

Source-side evolution or asynchronous index state may be considered only in
later audit interpretation.

The acceptance rule does not depend on assigning a cause.

## 17. Scientific isolation

This amendment changes source retrieval validation only.

It does not change:

- citation anchors;
- forward/backward chaining scope;
- literature-search expressions;
- landscape eligibility;
- direct/near-direct classification;
- screening decisions;
- Wave promotion rules; or
- citation-chaining saturation criteria.

## 18. Attempt 05

Attempt 05 remains failed.

The later successful diagnostic does not retroactively convert it into a
production corpus.

## 19. Fail-closed rule

If no complete snapshot attempt passes every acceptance gate within three
attempts, that OpenCitations source-direction operation remains unresolved and
the Wave cannot be declared complete.
