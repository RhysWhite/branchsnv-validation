# Pre-review triage future review workspace v1 — terminology amendment 001

Status: `FROZEN_TERMINOLOGY_AMENDMENT_001`

## Purpose

This amendment corrects terminology only.

Five previously frozen workspace-contract occurrences described the six
carry-forwards using an unsupported category label referring to "Wave 0".

The authoritative records support a different description: these six records
are **prior-anchor carry-forwards**, equivalently **frozen prior adjudication
carry-forwards**.

This amendment does not rewrite any previously frozen file.

## Normative terminology

For all downstream interpretation and future contracts:

- preferred category label: `prior-anchor carry-forwards`;
- equivalent descriptive label: `frozen prior adjudication carry-forwards`;
- preferred future machine key: `prior_anchor_carry_forwards`.

The historical frozen machine key `prior_wave0_carry_forwards` is retained in
its original JSON bytes but is superseded semantically by this amendment.

It must not be interpreted as establishing a scientific category named
"Wave 0".

## Authoritative evidence

The frozen `prior_carry_forwards.tsv` contains exactly six records.

For all six:

- `prior_anchor_decision = include_as_anchor`;
- `record_decision = retain_for_method_assessment`;
- `scientific_reassessment_performed = false`.

Their existing anchor IDs remain stable historical identifiers and are not
renamed by this amendment.

An identifier prefix is not evidence for a carry-forward category label.

## Frozen historical files

The five historical occurrences remain byte-identical in their original frozen
files.

This amendment overlays their interpretation; it does not alter or replace
their provenance.

## Scientific effect

None.

This amendment changes no:

- screening entity;
- carry-forward identity;
- prior decision;
- record decision;
- candidate status;
- queue membership;
- queue order;
- workspace artifact;
- human-review task;
- production proposal;
- event ledger row.

No carry-forward is scientifically reassessed.

## Downstream requirement

Future workspace and human-review contracts must use the normative
prior-anchor terminology.

The deprecated historical machine key must not be introduced into new
contracts.

## Scientific boundary

This amendment authorizes no human review, scientific decision, carry-forward
reassessment, proposal generation, live event authorization, production event,
or production-ledger mutation.

## Next gate

`FREEZE_TESTED_PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_IMPLEMENTATION`
