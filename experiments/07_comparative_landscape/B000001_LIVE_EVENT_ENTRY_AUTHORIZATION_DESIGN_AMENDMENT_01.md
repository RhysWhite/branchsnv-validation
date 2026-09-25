# Experiment 07 B000001 live event-entry authorization design amendment 01

Status: `FROZEN_PRE_IMPLEMENTATION_AMENDMENT`

## Purpose

This amendment corrects a structural naming collision discovered during the
first implementation attempt of the frozen B000001 live-event authorization
design.

The implementation failed closed before generation of a review packet and
before any live authorization, checkpoint or production event existed.

No failed implementation is adopted by this amendment.

## Parent design

Parent commit:

`ffd85ad0860c7af5bf02e5d568638638cb8e94df`

The parent B000001 authorization design remains immutable.

This amendment changes only the names of human-editable columns in the derived
review packet.

It does not change:

- scientific eligibility criteria;
- exclusion criteria;
- event semantics;
- evidence requirements;
- operator requirements;
- B000001 membership;
- position-1 canary identity;
- one-event canary limit;
- expected pre-ledger state;
- checkpoint semantics;
- recovery semantics;
- authorization semantics.

## Defect

The parent design required the review packet to contain:

1. four immutable membership fields;
2. every frozen baseline-queue field;
3. eight human-editable fields.

Two proposed human-editable field names were already frozen baseline-queue
field names:

- `evidence_escalation_status`
- `notes`

This made the requested TSV schema non-unique and therefore invalid.

The implementation correctly failed closed rather than constructing an
ambiguous packet.

## Resolution

All human-editable review-packet fields now use an explicit `proposed_`
namespace.

The amended human-entry fields are exactly:

1. `proposed_event_type`
2. `proposed_record_decision`
3. `proposed_exclusion_reason_code`
4. `proposed_candidate_method_flag`
5. `proposed_evidence_basis`
6. `proposed_evidence_source_locator`
7. `proposed_evidence_escalation_status`
8. `proposed_notes`

The first four names are unchanged from the parent design.

The following four names are amended:

- `evidence_basis`
  -> `proposed_evidence_basis`
- `evidence_source_locator`
  -> `proposed_evidence_source_locator`
- `evidence_escalation_status`
  -> `proposed_evidence_escalation_status`
- `notes`
  -> `proposed_notes`

## Separation of frozen metadata and proposed scientific input

The review packet must continue to include every original baseline-queue field,
unchanged.

Therefore baseline fields such as:

- `record_decision`
- `exclusion_reason_code`
- `candidate_method_flag`
- `evidence_escalation_status`
- `notes`

remain the frozen baseline values.

They are not editable proposal fields.

Human scientific input exists only in columns beginning with `proposed_`.

This eliminates ambiguity between frozen source state and proposed live-event
state.

## Proposal extraction mapping

The future guard must map review-packet proposal columns to the frozen
13-field appender proposal schema as follows:

- `proposed_event_type`
  -> `event_type`
- `proposed_record_decision`
  -> `record_decision`
- `proposed_exclusion_reason_code`
  -> `exclusion_reason_code`
- `proposed_candidate_method_flag`
  -> `candidate_method_flag`
- `proposed_evidence_basis`
  -> `evidence_basis`
- `proposed_evidence_source_locator`
  -> `evidence_source_locator`
- `proposed_evidence_escalation_status`
  -> `evidence_escalation_status`
- `proposed_notes`
  -> `notes`

The appender proposal fields:

- `screening_entity_id`
- `batch_id`
- `supersedes_event_id`
- `operator_id`
- `operator_type`

continue to be supplied from frozen canary identity, event state and the
separately frozen authorization contract.

For the genesis canary,
`supersedes_event_id` remains empty.

## Generated packet state

At deterministic review-packet generation, all eight `proposed_` fields must
be blank for all 500 rows.

Software and model preclassification remain prohibited.

Only position 1 may later contain non-empty `proposed_` fields during the
canary authorization cycle.

Positions 2-500 must remain blank.

## Scientific boundary

This amendment makes no scientific decision.

At this freeze:

- production event rows = 0;
- B000001 accepted decisions = 0;
- B000001 source-escalation events = 0;
- authoritatively reviewed B000001 positions = 0;
- method assessments = 0;
- role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- no live authorization artifact exists;
- no receipt/checkpoint root exists;
- B000001 live entry remains unauthorised;
- scientific screening has not begun.

## Next gate

`IMPLEMENT_CONTROLLED_B000001_LIVE_AUTHORIZATION_GUARD_UNDER_AMENDMENT_01_WITHOUT_EVENTS`

The next implementation must consume this amendment in addition to the parent
design.

It must not create a live authorization artifact, create the real T000001
checkpoint, or append an event to the production ledger.
