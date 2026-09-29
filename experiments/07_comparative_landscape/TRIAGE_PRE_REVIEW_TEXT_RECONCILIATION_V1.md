# Triage pre-review text reconciliation v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This freeze defines the offline deterministic reconciliation layer
after completed Wave A and Wave B retrieval.

It creates no network authority, performs no scientific screening,
fits no model, selects no threshold, accesses no blind-validation
content, and permits no production-ledger mutation.

## Frozen population

- Retrieval-lane records: 4,499
- Wave A records: 4,490
- No-network cached records: 9
- Wave B PubMed-to-OpenAlex fallbacks: 25
- Final usable abstracts: 4,190
- Final verified abstract-absent records: 309

Final abstract statuses:

- `usable_abstract_pubmed`: 3,931
- `usable_abstract_openalex`: 259
- `abstract_absent`: 309

## Frozen source provenance

Terminal source counts:

- offline cached OpenAlex: 9
- Wave A PubMed: 3,931
- Wave A OpenAlex: 534
- Wave B OpenAlex after PubMed abstract absence: 24
- Wave B OpenAlex after verified PubMed not-found: 1

Wave B fallback reasons:

- `pubmed_abstract_absent`: 24
- `pubmed_verified_not_found`: 1

There are no accepted parser faults, OpenAlex position-gap states,
provider-identity mismatches, or unresolved transport states in the
frozen reconciled population.

## Planned derived outputs

### Resolution table

`results/07_comparative_landscape/triage_pre_review_text_retrieval_v1/reconciled_resolution.tsv`

Exactly 4,499 rows, one for every retrieval input record, ordered by
`retrieval_record_index`.

It preserves retrieval provenance and terminal abstract state. An
`abstract_absent` row remains present and must not be converted into a
scientific exclusion.

### Normalized-text table

`results/07_comparative_landscape/triage_pre_review_text_retrieval_v1/reconciled_normalized_text.tsv`

Exactly 4,190 rows.

The schema is deliberately identical to the existing frozen
`offline_cached_normalized_text.tsv` schema.

Only `usable_abstract_pubmed` and `usable_abstract_openalex` rows are
written to this table. Title-only/abstract-absent records are not
silently promoted to primary model text in v1.

No minimum abstract-length threshold is introduced.

### Summary and checksums

`results/07_comparative_landscape/triage_pre_review_text_retrieval_v1/reconciliation_summary.json`

`results/07_comparative_landscape/triage_pre_review_text_retrieval_v1/reconciliation_outputs.sha256`

The summary contains counts, hashes and provenance only; it contains
no title or abstract text.

## Scientific boundary

Retrieval failure, provider absence, verified provider not-found and
abstract absence are not scientific evidence for exclusion.

This reconciliation layer may not contain scientific decisions,
scientific labels, review evidence, operator fields, notes, model
scores or thresholds.

The blind validation content is not used.

## Archive boundary

Wave A and Wave B raw archives are immutable inputs.

The implementation must fail closed on any body, checksum, request
identity, evidence or provider-identity mismatch.

No network request is permitted during reconciliation.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_OFFLINE_TRIAGE_PRE_REVIEW_TEXT_RECONCILIATION_V1`

Final derived outputs must not be generated until the offline
reconciler and its deterministic/hostile tests are implemented,
audited and frozen.
