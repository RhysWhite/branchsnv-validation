# Pre-review triage future text reconciliation v1 — Amendment 002

## Status

`FROZEN_PRE_IMPLEMENTATION`

This amendment supplements the future reconciliation design and Amendment 001.

## Reason for amendment

Exhaustive validation of all 3,608 Future Wave-A OpenAlex requests identified
exactly one transport-successful, identity-verified OpenAlex record whose
abstract inverted index cannot be reconstructed contiguously by the frozen
normalizer.

The affected record is:

- request sequence: `9180`
- retrieval record index: `9191`
- OpenAlex work: `W2119850564`
- screening entity: `publication_component:citation:publication:doi:10.5897/ajb11.773`
- body SHA256: `30228dfcd8815a4e8dfbbefc810d9033a579b2733cb7091c6314e514178943a1`

The frozen inverted index contains 256 unique positions between 0 and 261, with
no duplicate positions, but positions 86, 110, 215, 217, 250 and 251 are
absent.

## Resolution semantics

The record remains present in `reconciled_resolution.tsv` with:

- `resolution_lane = wave_a_primary`
- `provider_used = openalex`
- `provider_lookup_type = exact_work_id`
- `provider_record_id = https://openalex.org/W2119850564`
- `provider_identity_status = matched`
- `parser_status = ok`
- `abstract_status = openalex_position_gap`
- no Wave-B fallback
- `normalized_text_present = 0`

It must not enter `reconciled_normalized_text.tsv`.

## Safety boundary

No attempt may be made to infer, synthesize, reorder or repair missing abstract
tokens.

No network reretrieval is authorized.

This state is retrieval provenance only and is not scientific exclusion
evidence.

The exception applies only to this exact frozen request identity and body SHA.

## Population accounting

The final 12,162-record reconciliation population must be accounted for as:

usable abstracts + abstract-absent + provider-not-found +
OpenAlex-position-gap = 12,162.

Exactly one `openalex_position_gap` record is permitted.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_FUTURE_TEXT_RECONCILIATION_V1_AGAINST_DESIGN_PLUS_AMENDMENTS_001_002_WITH_TWO_INDEPENDENT_TEMPORARY_BUILDS`
