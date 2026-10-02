# Pre-review triage future review workspace v1 — implementation

Status: `FROZEN_IMPLEMENTATION_PRE_GENERATION_AUTHORIZATION`

## Purpose

This implementation deterministically constructs the future-triage
human-review workspace defined by the frozen workspace design.

It has not generated the canonical review workspace.

## Frozen partition

The implementation preserves the frozen 12,162-record future-triage universe
as:

- 12,156 new human-review tasks;
- 6 previously adjudicated Wave 0 carry-forwards.

The six carry-forwards retain their existing frozen adjudications and are not
presented as new scientific-review tasks.

## Review lanes

The new-review workload is:

- priority: 5,477 records;
- residual: 6,422 records;
- manual: 257 records.

Packetization is lane-local:

- priority: 11 packets;
- residual: 13 packets;
- manual: 1 packet.

Maximum packet size is 500 records.

No global cross-lane ordering is introduced.

## Existing scientific authority

The implementation preserves the existing:

- `screening_entity_id`;
- B000xxx batch identity;
- `position_in_batch`;
- `global_active_index`;
- `baseline_row_sha256`;
- append-only baseline scientific-screening event ledger.

The derived workspace does not create or replace authoritative scientific
batch membership.

## Reviewer-facing model boundary

The implementation does not expose in review-work artifacts:

- `continuous_score`;
- `selected_candidate_id`.

Frozen lane and queue position are used only for review-work ordering.

They are not scientific inclusion/exclusion evidence.

## Review packets

Every review packet is generated with blank human-entry fields:

- `proposed_event_type`
- `proposed_record_decision`
- `proposed_exclusion_reason_code`
- `proposed_candidate_method_flag`
- `evidence_basis`
- `evidence_source_locator`
- `evidence_escalation_status`
- `notes`

No scientific decision is pre-populated.

## Production-ledger protection

Immediately before generation, the implementation verifies that no entity in
the frozen future-triage universe has an accepted scientific event.

The current event ledger may legitimately advance for unrelated baseline
records.

During an authorised generation, the event-ledger SHA is checked before and
after temporary workspace construction. Any change during generation causes
the operation to fail closed before canonical publication.

## Materialization

A future authorised generation will:

1. validate the frozen design and source identities;
2. reconstruct the 12,156 + 6 partition;
3. build the workspace in a temporary sibling directory;
4. validate exact schemas, packet membership, blank human fields and checksums;
5. revalidate the current event-ledger boundary;
6. atomically move the validated payload into the canonical output root.

The implementation refuses to overwrite an existing canonical workspace.

## Validation

The implementation passed:

- 12 unit tests;
- 14 hostile tests;
- 26 tests total;
- exact frozen-design validation;
- real-input read-only derivation;
- exact 12,156 + 6 partition validation;
- deterministic temporary workspace reconstruction;
- materialized temporary workspace round-trip validation;
- model-field exclusion checks;
- blank human-entry-field checks;
- accepted-event overlap checks;
- source and checksum tamper checks.

The canonical workspace remained absent throughout implementation validation.

## Authorization boundary

Canonical generation requires a separately frozen one-use authorization and
the exact confirmation:

`GENERATE-FROZEN-FUTURE-REVIEW-WORKSPACE-V1`

No such authorization exists at this implementation freeze.

## Scientific boundary

This implementation does not:

- conduct human scientific review;
- make a record-level scientific decision;
- reassess the six prior carry-forwards;
- create new scientific batch membership;
- infer cross-lane scientific priority;
- authorize or append a production scientific event;
- mutate the production event ledger.

## Next gate

`FREEZE_ONE_USE_PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_GENERATION_AUTHORIZATION`
