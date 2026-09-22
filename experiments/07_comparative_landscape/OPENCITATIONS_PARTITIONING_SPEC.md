# Experiment 07 OpenCitations deterministic partitioning specification

Status: FROZEN_PRE_IMPLEMENTATION

## 1. Purpose

This specification defines a transport-level mechanism for retrieving a
complete OpenCitations citation set when a single unpartitioned HTTP response
is too large to be transferred reliably.

It is frozen after Wave 0 Attempts 03 and 04 demonstrated repeated incomplete
HTTP bodies for the same OpenCitations forward-citation operation, and before
any partitioned production retrieval.

The partitioning changes transport only.

It must not change:

- citation source;
- citation direction;
- anchor publication;
- citation inclusion;
- search vocabulary;
- relevance screening;
- method eligibility;
- direct/near-direct classification; or
- the citation-chaining saturation rule.

## 2. API basis

The frozen implementation targets OpenCitations Index v2.

The documented Index API provides:

- `/citation-count/{id}`;
- `/reference-count/{id}`;
- `/citations/{id}`;
- `/references/{id}`; and
- generic result filtering via
  `filter=<field_name>:<value>`.

When no comparison operator is supplied to `filter`, the documented API treats
the value as a regular expression.

The `oci` result field is the Open Citation Identifier.

Its documented lexical form is:

`[0-9]+-[0-9]+`

The first numeric component identifies the citing bibliographic resource and
the second numeric component identifies the cited bibliographic resource.

## 3. Why partition OCI rather than bibliographic metadata

Partition membership must not depend on scientific content.

Therefore partitions must not use:

- title;
- abstract;
- author;
- journal;
- language;
- publication date;
- citation count;
- software name;
- relevance keywords; or
- membership in any known-tool list.

OCI is used because it is a citation identity field rather than a scientific
content field.

## 4. Direction-specific variable OCI component

For an incoming citation retrieved by `/citations/{anchor}`:

`CITING-COMPONENT - CITED-COMPONENT`

the cited component corresponds to the fixed anchor and the citing component
varies across citation records.

Therefore forward-citation partitioning operates on the **citing component**.

For an outgoing reference retrieved by `/references/{anchor}`, the citing
component corresponds to the fixed anchor and the cited component varies.

Therefore backward-reference partitioning operates on the **cited component**.

## 5. Root decimal partition

Every non-empty decimal integer has exactly one terminal decimal digit.

For forward citation retrieval, the root partition contains ten buckets:

`^[0-9]*0-[0-9]+$`
`^[0-9]*1-[0-9]+$`
...
`^[0-9]*9-[0-9]+$`

For backward reference retrieval, the root partition contains:

`^[0-9]+-[0-9]*0$`
`^[0-9]+-[0-9]*1$`
...
`^[0-9]+-[0-9]*9$`

Under the documented OCI lexical form these ten buckets are:

- mutually exclusive; and
- collectively exhaustive.

No citation can belong to two root buckets.

No valid OCI can belong to zero root buckets.

## 6. Why terminal digits are used

The partition uses the rightmost digits of the variable OCI component rather
than its leftmost digits.

OCI numeric components may share substantial leading structure because they
are identifiers assigned within bibliographic-resource namespaces.

Partitioning on the terminal digit avoids relying on diversity in those common
leading digits.

This is a transport distribution mechanism only.

No assumption that terminal digits are perfectly or randomly distributed is
required for completeness.

## 7. Recursive subdivision

A partition bucket is first retrieved under the existing bounded transport
retry policy.

If and only if that filtered response still exhausts the bounded retry policy
because of a retryable transport failure, that bucket may be subdivided.

Suppose a forward bucket currently represents numeric suffix `S`.

Its current regular expression is:

`^[0-9]*S-[0-9]+$`

It is replaced by the following disjoint child set:

### Exact-number child

`^S-[0-9]+$`

This preserves a citing numeric component whose complete value is exactly `S`.

### Extended children

For each decimal digit `d` in `0..9`:

`^[0-9]*dS-[0-9]+$`

These represent multi-digit citing components whose next digit to the left is
`d`.

The same rule is applied to backward-reference partitions on the cited
component:

exact:

`^[0-9]+-S$`

children:

`^[0-9]+-[0-9]*dS$`

Thus every subdivision replaces one parent with eleven mutually exclusive
children whose union is exactly the parent.

## 8. Empty buckets

A successful filtered request returning an empty JSON result is a valid
completed bucket.

Empty buckets are retained in the partition audit.

They are not interpreted as API failure.

## 9. Retry exhaustion

Subdivision is permitted only after the existing bounded retry policy for a
filtered request has been exhausted.

A response that succeeds after ordinary retry is accepted as that bucket and
is not subdivided.

A non-retryable API error remains fail-closed and must not trigger arbitrary
subdivision.

## 10. OCI validation

Every citation row returned from every filtered bucket must contain a
non-empty `oci`.

Every OCI must match the documented complete lexical form:

`^[0-9]+-[0-9]+$`

Every returned OCI must match the regular expression of the leaf bucket from
which it was retrieved.

Failure of any of these checks makes the operation incomplete.

## 11. Duplicate prohibition

Within one anchor × source × direction operation, each OCI must occur exactly
once in the reconstructed partition union.

An OCI observed in more than one accepted leaf bucket is a partition-integrity
failure.

Duplicate rows are not silently collapsed before this validation.

## 12. Independent count reconciliation

The existing independent count request remains authoritative for the expected
number of citation relationships.

For forward retrieval:

`expected = /citation-count/{anchor}`

For backward retrieval:

`expected = /reference-count/{anchor}`

After all partition leaves complete:

`number of unique reconstructed OCIs == expected`

must hold exactly.

The following are all fatal:

- reconstructed count < expected;
- reconstructed count > expected;
- duplicate OCI;
- missing OCI;
- malformed OCI;
- OCI outside its bucket;
- unfinished leaf;
- non-terminal request failure.

No partial partition union is accepted.

## 13. Count of zero

If the independent count endpoint reports zero, no partition requests are
required.

The operation is recorded as `resolved_zero_edges`.

## 14. Use for OpenCitations operations

For deterministic behaviour, positive-count OpenCitations citation-data
retrieval will use the root decimal partition from the outset rather than first
attempting another unpartitioned large response.

This applies to both:

- forward citations; and
- backward references.

Thus the result does not depend on whether a particular unpartitioned response
happened to survive transport on a particular run.

## 15. Cross-bucket ordering

Bucket execution order is fixed:

1. decimal suffix `0`;
2. `1`;
3. ...
4. `9`.

Recursive children are processed deterministically:

1. exact-number child;
2. extended child `0S`;
3. `1S`;
4. ...
5. `9S`.

Scientific results must be invariant to processing order.

The implementation will include an offline order-independence test for final
OCI union construction.

## 16. Raw-response preservation

Every completed filtered API response is retained separately.

Its provenance records at minimum:

- wave;
- anchor;
- direction;
- OCI suffix;
- recursion depth;
- leaf regular expression;
- request identity;
- raw-response path; and
- row count.

Failed incomplete bodies are never written as completed raw responses.

## 17. Rate limiting

Partitioning increases request count.

The implementation must retain a request delay compatible with the documented
OpenCitations rate limit.

Partitioning does not permit parallel request bursts that exceed the
prespecified source rate.

## 18. Safety against pathological recursion

Recursive subdivision must make strict lexical progress by increasing the
number of fixed terminal digits in the variable OCI component.

The implementation must also impose a finite transport-safety recursion
ceiling.

Reaching that ceiling is a retrieval failure, not permission to accept a
partial citation set.

The exact ceiling must be frozen in the implementation and must be generous
relative to OCI identifiers observed structurally; it has no scientific or
screening meaning.

## 19. Relationship to failed attempts

Attempts 03 and 04 remain failed attempts.

Their partial citation responses are archived for audit only and are never
merged into a later successful Wave 0 corpus.

A later successful production attempt starts from an empty Wave 0 production
directory and reconstructs the entire Wave 0 citation set under one frozen
implementation.

## 20. Scientific interpretation

Partition filters are not relevance filters.

They partition an identifier space whose complete union must equal the
independent OpenCitations count.

Therefore the partitioning procedure cannot intentionally remove a citation on
the basis of biological or methodological content.
