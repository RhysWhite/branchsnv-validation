# Experiment 07 metadata retrieval completion

Status: `COMPLETE`

## Scope

This record freezes the completed metadata-retrieval state for the Experiment
07 comparative-landscape workflow.

The production archive remains external to the tracked Git repository. This
completion record cryptographically pins its archive checksum manifest and key
derived ledgers.

## Frozen retrieval universe

The metadata-resolution queue contains exactly 1,731 logical lookup keys.

The completed production archive contains:

- 1,698 `success`;
- 33 `not_found`;
- 0 unresolved terminal failures.

The archive therefore has accepted terminal evidence for all 1,731 frozen
logical lookup keys.

## Amendment 36 adjudication

Seven historical OpenCitations Meta lookups had originally terminated as
`response_integrity_failure` because exact metadata responses contained more
than one row.

Under frozen Amendment 36, all seven preserved responses satisfied the
identity-concordant multiplicity rule.

Exactly seven `adjudication.json` records were therefore created.

No new provider exchange occurred during this transition:

- attempt-directory count remained 1,731;
- archived request count remained 1,731;
- archived response-metadata count remained 1,731;
- archived response-body count remained 1,731.

No `attempt_02` was created for any adjudicated lookup.

No synthetic successful attempt was created.

No `terminal.json` was manufactured for any adjudicated historical failure.

## Historical evidence preservation

For each of the seven adjudicated lookups:

- the original `failure.json` remains present;
- the original `attempt_01` remains present;
- the original attempt outcome remains `response_integrity_failure`;
- the original request, response metadata and response body remain
  byte-identical;
- effective success exists only in the Amendment 36 adjudication layer.

The original failed evidence was not deleted, rewritten or silently
reclassified.

## Validation

The completed production archive passed:

- exact archive checksum validation;
- exact frozen-queue validation;
- raw-evidence validation;
- derived-ledger reconstruction;
- Amendment 36 semantic adjudication validation; and
- the production `COMPLETE` gate.

Each of the seven adjudications independently reproduces from immutable raw
evidence.

## Scientific boundary

Metadata retrieval completion does not perform:

- title reconciliation;
- descriptive-field selection;
- publication-component merging;
- software consolidation;
- scientific inclusion/exclusion screening; or
- comparative-tool ranking.

At retrieval completion:

- `scientific_screening_performed = false`;
- `component_merge_performed = false`;
- `screening_log.tsv` remains empty.

## Completion state

The Experiment 07 metadata-retrieval stage is complete.

Subsequent metadata reconciliation, identity decisions and scientific
screening must occur in separately frozen stages and must not modify this raw
retrieval evidence.
