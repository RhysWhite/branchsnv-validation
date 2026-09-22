# Experiment 07 merged-search-universe specification

Status: FROZEN_PRE_IMPLEMENTATION

This specification defines how the completed formal search and the completed
high-recall expansion are combined before seed-recovery analysis, eligibility
screening, capability classification, or benchmark selection.

No screening or eligibility decisions had been made when this specification
was frozen.

## 1. Frozen inputs

The merge consumes only the frozen normalized retrieval outputs:

- `results/07_comparative_landscape/formal_search/`
- `results/07_comparative_landscape/high_recall_search/`

The formal corpus contains 3,108 candidate source-query rows and 2,204
deduplicated records.

The high-recall corpus contains 113,448 candidate source-query rows and 78,962
deduplicated records.

Both input corpora must pass their existing checksum verification before a
merge is permitted.

## 2. Search-stage provenance

Every formal candidate row is assigned:

`search_stage = formal`

Every high-recall candidate row is assigned:

`search_stage = high_recall`

No original candidate field is otherwise changed.

The stage-labelled candidate table retains every source-query hit from both
search stages. Candidate records are not collapsed before deduplication.

The expected candidate-row count is therefore:

3,108 + 113,448 = 116,556.

## 3. Identity rule

Record identity is defined exclusively by the already-frozen `dedup_key()`
implementation used identically by both retrieval scripts.

The merge must not introduce a new matching, fuzzy-matching, title-similarity,
DOI-resolution, PMID-resolution, or manual identity rule.

The frozen hierarchy remains:

1. bio.tools identifier for software-registry records;
2. normalized DOI when present;
3. normalized PMID when present;
4. normalized title plus year when present;
5. source plus source-record identifier otherwise.

The pre-merge structural diagnostic found 79,917 distinct frozen deduplication
keys across the union. This count is a validation invariant, not a newly
selected inclusion criterion.

## 4. Deterministic representative metadata

The existing retrieval-level `make_deduplicated()` implementation selects
title exemplars by source priority but selects DOI, PMID, and year using the
first non-empty value encountered in the input group.

A naive concatenation would therefore make representative metadata dependent
on whether the formal or high-recall table was supplied first.

The merged universe must not assign either search stage precedence.

Within each deduplication-key group, candidate rows are ordered using the
following deterministic, search-stage-neutral key:

1. source priority:
   `pubmed`, then `openalex`, then `biotools`;
2. `title_or_name`;
3. `year`;
4. normalized DOI;
5. normalized PMID;
6. `source_record_id`;
7. `query_id`;
8. `query_family`;
9. `search_stage`.

`search_stage` is only the final total-order tie-breaker, after all
bibliographic and retrieval fields that can affect representative metadata.

Representative `entity_type` and `title_or_name` are taken from the first row
under this order.

Representative DOI, PMID, and year are the first non-empty values under the
same order.

This does not alter record identity. It only makes representative display
metadata deterministic and independent of formal-versus-high-recall input
concatenation order.

## 5. Metadata disagreement audit

For every deduplication-key group, the merge records whether multiple distinct
stored non-empty values occur for any of:

- `entity_type`
- `title_or_name`
- `year`
- `doi`
- `pmid`

All such disagreements are written to a separate machine-readable conflict
table.

A disagreement does not split or exclude a record and does not change its
frozen deduplication key.

No disagreement may be manually resolved during construction of the merged
universe.

## 6. Aggregated provenance

Each merged deduplicated row must retain sorted unique provenance for:

- search stages;
- sources;
- query IDs;
- query families;
- source-record identifiers.

Stage-qualified query provenance must also be retained so that a query hit can
be assigned unambiguously to its retrieval stage.

The detailed candidate table remains the authoritative record of individual
source-query retrieval events.

## 7. Search-count provenance

The formal and high-recall `search_counts.tsv` files are combined with an
explicit `search_stage` field.

Zero-result source-query pulls remain represented.

No source-query pull is discarded because it produced zero candidate rows.

## 8. Required outputs

The merge implementation will create a dedicated merged-universe directory
containing at minimum:

- `candidate_records.tsv`
- `deduplicated_records.tsv`
- `metadata_conflicts.tsv`
- `search_counts.tsv`
- `merge_manifest.json`
- `checksums.sha256`

The original formal and high-recall corpora remain unchanged.

## 9. Fail-closed validation

The merge must fail if:

- either frozen input checksum verification fails;
- candidate schemas differ;
- the frozen deduplication implementations no longer agree;
- an unknown source is encountered;
- an unexpected search-stage value is encountered;
- the candidate-row count is not exactly 116,556;
- any deduplication key appears more than once in the merged deduplicated
  output;
- the number of merged deduplicated records is not exactly 79,917;
- provenance represented by candidate rows is lost from the merged
  deduplicated output;
- output checksum verification fails.

## 10. Order-independence test

The implementation must construct the complete merged outputs twice:

1. formal input followed by high-recall input;
2. high-recall input followed by formal input.

All normalized merged outputs must be byte-identical between these builds.

Failure of byte identity is a hard failure.

## 11. Stopping rule

This merge specification does not modify either scientific search strategy.

The completed high-recall expansion remains the single generic expansion
specified previously.

Results of the merged seed-recovery diagnostic must not be used to tune,
extend, or rewrite the search expressions.

Known seeds not recovered after the frozen merge proceed through the
prespecified citation-chaining route.

No eligibility screening, capability classification, or direct-benchmark
selection occurs until the merged universe has been built and frozen.
