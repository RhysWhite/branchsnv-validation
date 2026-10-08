# OpenCitations creation-partition diagnostic Attempt 02

Status: COMPLETE_SUCCESSFUL_SOURCE_DIAGNOSTIC

Diagnostic 02 independently reconstructed the W0A07/PAML incoming-citation
result using only the raw `creation` field as the partition axis.

The independent citation count was 12,846 both immediately before and after
partition retrieval.

The creation-partition union contained:

- 12,846 citation rows;
- 12,846 unique complete rows;
- 12,846 unique valid numeric OCIs;
- zero duplicate valid OCIs.

The diagnostic therefore demonstrates contemporaneous exact agreement between
the OpenCitations citation-count result and a complete citation-data retrieval
that does not use OCI for partition membership.

## Comparison with Attempt 05

The frozen Attempt-05 union contained 12,845 unique OCIs.

Relative to Attempt 05, Diagnostic 02 contains two new-only OCIs and lacks one
old-only OCI.

One old-only and one new-only record share the same citing OpenAlex identifier,
`openalex:W2806987055`, and the same cited target. Their OpenCitations resource
identifier, creation precision and associated metadata differ. This is
consistent with the same citing work having been reidentified or re-keyed in
the source between snapshots.

The remaining Diagnostic-02-only relationship has citing identifiers absent
from every Attempt-05 citing record under the DOI, PMID and OpenAlex identifiers
used for this comparison.

Thus the OpenCitations citation set demonstrably changed between the two
snapshots.

The relationship-level change is consistent with one stable-identifier-matched
replacement plus one additionally present citation relationship, producing the
net increase from 12,845 to 12,846 rows.

## What this does not establish

This comparison does not establish that the frozen Attempt-05 OCI partition
algorithm omitted a valid row.

It also does not fully explain why the independent count endpoint already
reported 12,846 during Attempt 05 while that frozen citation-data union
contained 12,845 rows.

That historical count/data mismatch therefore remains unresolved.

No production completeness rule, search rule, comparator classification or
citation-chaining rule is changed by this diagnostic.

Diagnostic 02 remains source forensics and is not itself the Wave 0 production
corpus.
