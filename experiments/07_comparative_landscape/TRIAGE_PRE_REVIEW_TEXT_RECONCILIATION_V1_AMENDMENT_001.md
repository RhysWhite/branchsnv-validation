# Triage pre-review text reconciliation v1 — Amendment 001

## Status

`FROZEN_PRE_IMPLEMENTATION`

This amendment supplements, but does not modify, the reconciliation
design frozen at commit `1aa32f02387e4c5638b18b951bd5bc7a231c0b5f`.

## Reason for amendment

Post-freeze implementation prechecking established that the nine
records resolved from the historical cache depend on raw bodies under:

`results/07_comparative_landscape/metadata_resolution_retrieval`

The original reconciliation freeze pinned the derived offline cache
tables but did not explicitly pin this historical raw archive as an
implementation dependency.

This amendment closes that dependency gap before implementation.

## Frozen historical dependency

Checksum manifest:

`results/07_comparative_landscape/metadata_resolution_retrieval/checksums.sha256`

SHA256:

`f51080de3383cae1981e19c57687e4c8ea0e7f9832316a3936728a23995e8b86`

Entries: 8,666.

Exactly nine offline-cache lookup identities are admitted. Each
selected lookup, source-body SHA256 and expected abstract status is
enumerated in the machine-readable amendment design.

## Three usable cached OpenAlex rows

The existing frozen `offline_cached_normalized_text.tsv` remains the
normalized-text source for these three records.

Their historical raw bodies must nevertheless verify against the
historical checksum archive and must reproduce
`usable_abstract_openalex` under the frozen normalizer.

The existing cached normalized rows are not rewritten or reinterpreted.

## Six cached abstract-absent rows

These records remain present in the 4,499-row resolution output and
remain absent from the 4,190-row normalized-text output.

Their `provider_record_id` and `provider_identity_status` are derived
only by applying the frozen OpenAlex normalizer to the exact
checksum-verified historical body.

No blank-field convention and no fabricated provider identity is
permitted.

All six must reproduce:

- `parser_status = ok`
- `abstract_status = abstract_absent`
- the provider provenance pinned in the amendment JSON.

Abstract absence remains retrieval state only. It is not scientific
evidence for exclusion.

## Unchanged boundaries

This amendment does not change:

- 4,499 total reconciliation records;
- 4,190 usable abstracts;
- 309 abstract-absent records;
- the Wave A or Wave B archives;
- scientific eligibility rules;
- model fitting or thresholds;
- the blind validation boundary;
- the production ledger.

No network access is authorized.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_OFFLINE_TRIAGE_PRE_REVIEW_TEXT_RECONCILIATION_V1_AGAINST_DESIGN_PLUS_AMENDMENT_001`
