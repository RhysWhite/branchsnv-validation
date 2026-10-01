# Pre-review triage future text reconciliation v1 — Amendment 001

## Status

`FROZEN_PRE_IMPLEMENTATION`

This amendment supplements, but does not modify, the future reconciliation
design frozen at commit `3047e7b1aef8d479bd988a8779890877d056a173`.

## Reason for amendment

Implementation validation against the frozen Future Wave-A archive established
that ten direct OpenAlex requests terminate as independently verified provider
not-found responses.

The original implementation candidate inherited the historical assumption that
every Wave-A `verified_not_found` record was PubMed and therefore eligible for
the frozen PubMed-to-OpenAlex Wave-B fallback. That assumption is false for the
future population.

The affected reconciliation record indices are:

`2421, 2603, 3092, 3348, 3492, 3535, 4738, 4739, 5283, 11061`

Each exact request identity, retrieval-record index, screening entity,
identifier, route, terminal path, terminal JSON SHA256 and terminal-body SHA256
is pinned in the machine-readable amendment design.

## Frozen evidence

The ten records:

- are direct Future Wave-A OpenAlex requests;
- terminate with `terminal_status = not_found`;
- terminate after HTTP 404 evidence with `outcome = not_found`;
- have no frozen Future Wave-B fallback;
- are provider-level absence states, not abstract-absence states.

The frozen Future Wave-B population remains exactly 40 rows: 38 derived from
PubMed `abstract_absent` and two derived from PubMed `verified_not_found`.

## Resolution semantics

Each of the ten direct OpenAlex not-found records must remain present in
`reconciled_resolution.tsv`.

They must not enter `reconciled_normalized_text.tsv`.

They are represented as:

- `resolution_lane = wave_a_primary`
- `provider_used = openalex`
- `provider_lookup_type` from the frozen Wave-A manifest
- blank `provider_record_id`
- `source_body_sha256` from the verified terminal body
- `provider_identity_status = not_applicable`
- `parser_status = not_applicable`
- `abstract_status = provider_not_found`
- no Wave-B request identity
- no fallback reason
- `normalized_text_present = 0`

`provider_not_found` is retrieval provenance only. It is not scientific
exclusion evidence and must not be reinterpreted as `abstract_absent`.

Because no provider record exists to normalize, `parser_status =
not_applicable` is not a parser failure and must not contribute to the
parser/position-gap failure count.

Final population accounting must therefore include usable abstracts,
abstract-absent records and these ten provider-not-found records, together
covering all 12,162 future reconciliation inputs.

## Unchanged boundaries

This amendment does not change:

- the 12,162-record future reconciliation population;
- the 12,147 Future Wave-A request population;
- any Future Wave-A raw archive;
- the 40-row Future Wave-B fallback population;
- the 38 PubMed abstract-absent fallbacks;
- the two PubMed verified-not-found fallbacks;
- scientific eligibility rules;
- the blind-validation boundary;
- model fitting or thresholds.

No network access is authorized.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_FUTURE_TEXT_RECONCILIATION_V1_AGAINST_DESIGN_PLUS_AMENDMENT_001_WITH_TWO_INDEPENDENT_TEMPORARY_BUILDS`
