# Future pre-review text reconciliation v1 — implementation amendment 001

Status: `FROZEN_PRE_CANONICAL_RECONCILIATION_OUTPUT_GENERATION`

## Reason for amendment

The frozen future-text reconciliation implementation correctly exposed
`canonical_confirmation` through the command-line interface and through
`write_reconciliation()`.

However, `validate_output_destination()` unconditionally rejected the
canonical future reconciliation output root and therefore ignored that
confirmation argument.

This discrepancy was identified after the implementation freeze but before
any canonical future reconciliation output was generated.

The historical reconciliation implementation requires an exact canonical
confirmation token. This amendment restores those already-established
semantics.

## Original implementation freeze

Original implementation-freeze commit:

`2d791a0c186144397706b0b0e556a8cef6c8ee7e`

Original implementation SHA-256:

`534b48e3db1eeccdb0c39f37c92a5542e13686418f198c5e6bc05ebb02e7a139`

Original implementation-freeze checksum-manifest SHA-256:

`f966e8b524f5636378b11bf04fa012c39e07b94e113cbe583197c4444c1a15e5`

The original implementation freeze remains historical evidence. It is
superseded only for this canonical-write guard.

## Amended control

Canonical future reconciliation output generation requires the exact token:

`WRITE-FROZEN-RECONCILIATION-V1`

A missing or non-exact token fails closed.

The exact token permits only destination validation. Existing reconciliation
outputs remain non-overwritable.

Amended implementation SHA-256:

`636705a79d75ec1ea1bf0a3fccff0c4fbcc30b560018dabe6600b04518f48b18`

Focused amendment-test SHA-256:

`5d09c5c983528cb5640e1713ed77b58ec3e06b93a5d43e1b6f877b4938dbd9a9`

## Reconciliation boundary

This amendment does not alter:

- reconciliation inputs;
- Wave A or Wave B retrieval evidence;
- request-10083 recovery semantics;
- Amendment 001 provider-not-found semantics;
- Amendment 002 OpenAlex position-gap semantics;
- normalized text;
- resolution rows;
- source selection;
- fallback selection;
- scientific screening;
- scientific labels;
- model fitting;
- thresholds.

No network request or canonical output generation is part of this amendment
commit.

## Frozen reconciliation totals

- resolution rows: 12,162
- normalized-text rows: 11,905
- usable PubMed abstracts: 8,499
- usable OpenAlex abstracts: 3,406
- abstract absent: 246
- provider not found: 10
- exact frozen OpenAlex position-gap provenance rows: 1
- Wave B fallbacks: 40

## Expected canonical output hashes

- `reconciled_resolution.tsv` — `437f21bde9c29ddc2ef531a356bd56491fb088f3a37e35ee5aa9be1609ec31f7`
- `reconciled_normalized_text.tsv` — `8ee30e1bbd94140710e943fc2227805819fa88e84e31207ff64965d67489a1d3`
- `reconciliation_summary.json` — `14b8099cecff8787a3a62efe5c796beebddf8635a66a38588f089435fdd14209`
- `reconciliation_outputs.sha256` — `237fd7080a3ff0617a486673ab122234edfbd6bfe12dc1734e5e16ea9e153279`

These hashes are unchanged from the original implementation freeze.

## Authority boundary

This amendment freeze does not itself perform or silently authorize a
canonical write.

The next gate requires the committed amendment identity, the exact explicit
confirmation token and subsequent byte-for-byte agreement with all four
frozen expected output hashes.

No network execution, scientific decision, scientific label, model fitting,
threshold selection, raw-archive mutation, Wave A mutation or Wave B mutation
is authorized.

## Next gate

`CONTROLLED_CANONICAL_RECONCILIATION_OUTPUT_GENERATION_WITH_EXACT_FROZEN_HASH_MATCH`
