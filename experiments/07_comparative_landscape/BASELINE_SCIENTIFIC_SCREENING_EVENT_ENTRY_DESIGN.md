# Experiment 07 controlled baseline scientific-screening event-entry design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design freezes the operational contract for entering human record-level
scientific-screening events into the already-produced append-only execution
event ledger.

It does not authorise event entry.

It does not make a scientific screening decision.

The parent pre-decision execution production-completion freeze remains the
authoritative genesis state.

## Scope

This contract is limited to baseline record-level screening.

It supports only:

- an initial terminal record decision;
- an initial source-escalation event;
- a terminal decision that resolves an existing source escalation; and
- a terminal correction that supersedes an existing terminal decision.

It does not perform:

- method-level identity assessment;
- analytical-role assignment;
- directness classification;
- canonical-publication selection;
- Wave 1 promotion;
- saturation assessment;
- metadata-blocker resolution;
- automated scientific classification.

## Frozen event schema

The event ledger schema remains exactly:

1. `event_id`
2. `event_type`
3. `screening_entity_id`
4. `baseline_queue_sha256`
5. `baseline_row_sha256`
6. `batch_id`
7. `record_decision`
8. `exclusion_reason_code`
9. `candidate_method_flag`
10. `evidence_basis`
11. `evidence_source_locator`
12. `evidence_escalation_status`
13. `operator_id`
14. `operator_type`
15. `decision_timestamp_utc`
16. `supersedes_event_id`
17. `reviewer_id`
18. `review_status`
19. `adjudication_status`
20. `notes`

No field may be added, removed, renamed or reordered.

## Frozen event types

Exactly three event types are permitted:

- `record_decision`
- `source_escalation`
- `superseding_record_decision`

No fourth event type is introduced.

## Frozen terminal decisions

Exactly two terminal record decisions are permitted:

- `retain_for_method_assessment`
- `exclude`

### retain_for_method_assessment

Requires:

- `record_decision = retain_for_method_assessment`;
- `candidate_method_flag = true`;
- `exclusion_reason_code` empty.

This means the record advances only to later source-backed method assessment.

It does not itself establish method identity, analytical role, directness,
canonical publication or Wave 1 eligibility.

### exclude

Requires:

- `record_decision = exclude`;
- `candidate_method_flag = false`;
- exactly one frozen exclusion reason.

The exact permitted exclusion reasons remain:

- `application_only_no_reusable_method`
- `unrelated_variant_or_data_type`
- `duplicate_record_same_method_no_distinct_capability`
- `unsupported_by_primary_or_stable_authoritative_source`

No other exclusion reason is permitted.

Records remain protected by the previously frozen rule that software is not
excluded merely because it is organism-specific, historical, unmaintained,
web-only or currently non-executable.

## Source escalation

A source-escalation event is explicitly non-terminal.

For `event_type = source_escalation`:

- `record_decision` is empty;
- `candidate_method_flag` is empty;
- `exclusion_reason_code` is empty;
- `evidence_escalation_status = awaiting_source_escalation`;
- `supersedes_event_id` is empty.

A source escalation is used when the available evidence is insufficient for a
terminal record-level decision and authoritative source checking is required.

A source-escalation event must not infer:

- method identity;
- role;
- directness;
- canonical publication;
- Wave 1 eligibility.

## Resolving source escalation

A record currently in `awaiting_source_escalation` may become terminal only
through:

`event_type = superseding_record_decision`

The new event must:

- reference the current source-escalation event in `supersedes_event_id`;
- contain a valid terminal decision;
- set `evidence_escalation_status = resolved`;
- preserve the historical source-escalation row unchanged.

A direct terminal `record_decision` must never be layered beside an unresolved
source escalation.

## Terminal corrections

A completed record may change only through:

`event_type = superseding_record_decision`

A correction must:

- reference the current unsuperseded terminal event;
- apply to the same `screening_entity_id`;
- contain a complete valid terminal decision;
- preserve the superseded historical event unchanged.

For correction of a terminal event:

- if the prior terminal event has blank `evidence_escalation_status`, the new
  terminal event must also have it blank;
- if the prior terminal event has `evidence_escalation_status = resolved`,
  the new terminal event must retain `resolved`.

This preserves whether source escalation occurred in the event chain.

## Single-current-event operational invariant

The frozen base validator rejects conflicting unsuperseded terminal decisions
but can technically represent more than one unsuperseded source-escalation
event.

The controlled appender is intentionally stricter.

Under this operational contract, each active screening entity may have at most
one current unsuperseded event.

Therefore:

- an entity with no current event may receive either one `record_decision` or
  one `source_escalation`;
- an entity with a current `source_escalation` may receive only a
  `superseding_record_decision` resolving that exact event;
- an entity with a current terminal event may receive only a
  `superseding_record_decision` correcting that exact event;
- a superseding event must point to the current unsuperseded event, never an
  older already-superseded historical event;
- branching event chains are prohibited.

This is a conservative operational restriction. It does not change the frozen
scientific eligibility criteria.

## Entity eligibility

An event may be entered only for a screening entity present in the immutable
`batch_membership.tsv`.

This automatically excludes:

- the seven historical carry-forward canonical publications;
- the 484 `blocked_metadata` entities;
- W0A06, which has no baseline screening entity;
- any entity outside the frozen active population.

Every event must match:

- the exact frozen baseline queue SHA;
- the entity's exact frozen baseline-row SHA;
- the entity's exact frozen batch membership.

## Event IDs

The controlled appender will assign event IDs.

Operators do not provide them manually.

The event-ID format is:

`E#########`

where `#` is a decimal digit.

Examples:

- `E000000001`
- `E000000002`

IDs are sequential in append order.

For a transaction beginning from an N-row validated ledger, the first new
event receives ID N+1.

Existing IDs can never be reused.

## Transaction scope and ordering

One append transaction operates on exactly one frozen screening batch.

A transaction may contain one or more proposed events, subject to:

- every proposed entity belonging to the same `batch_id`;
- at most one proposed event per entity in the transaction;
- a superseding event referencing only an event that already existed in the
  accepted ledger before the transaction;
- no proposed event superseding another event created in the same transaction.

Before assignment of event IDs, proposed rows are ordered by immutable
`position_in_batch`.

This makes multi-row transaction ordering deterministic.

## Compare-and-swap ledger protection

Every append operation requires the caller to provide the expected current
event-ledger SHA-256.

Before accepting the transaction, the appender must verify that the actual
ledger SHA exactly matches that expected SHA.

If it does not, the append fails closed.

After a successful append, rerunning the same command with the old expected
ledger SHA therefore fails instead of duplicating decisions.

## Logical append-only publication

The accepted post-transaction ledger must be a strict byte-prefix extension
of the previously accepted ledger:

`new_ledger_bytes.startswith(old_ledger_bytes)`

No previous byte may change.

A crash-safe implementation may construct a complete candidate ledger in a
temporary file and atomically replace the ledger only if:

- the old ledger bytes are preserved as the exact prefix;
- all proposed rows validate;
- the complete candidate ledger validates;
- the expected pre-ledger SHA still matches immediately before publication.

This is content-level append-only semantics.

No accepted historical row may be edited or deleted.

## Event timestamp

`decision_timestamp_utc` is system-generated by the appender.

Operators do not provide it manually.

The timestamp must:

- be UTC;
- end in `Z`;
- represent the append transaction time;
- use whole-second precision.

All events accepted in one transaction receive the same transaction timestamp.

## Operator provenance

Every event requires:

- non-empty `operator_id`;
- `operator_type` exactly one of:
  - `human`
  - `human_with_assistance`

`operator_id` identifies the human responsible for the scientific event.

`human_with_assistance` means computational or language-model assistance may
have been used to organise, retrieve, summarise or inspect evidence, but the
human operator remains responsible for:

- checking the source evidence;
- selecting the record-level decision;
- confirming the event before append.

Model output alone is not authoritative evidence and must never
automatically create an accepted event.

No autonomous model-authored scientific event is permitted.

## Evidence provenance

Every proposed event requires non-empty `evidence_basis`.

For a terminal decision, `evidence_source_locator` must also be non-empty.

The locator must identify the frozen evidence used for the decision, for
example:

- the frozen baseline entity/metadata;
- a DOI or PMID;
- a stable authoritative publication;
- stable authoritative software documentation;
- another frozen or stable source locator.

`evidence_basis` records why the cited evidence is sufficient for the
record-level disposition.

For an initial source-escalation event:

- `evidence_basis` is required and must explain why existing evidence is
  insufficient;
- `evidence_source_locator` may be empty when the required authoritative
  source has not yet been located.

For the resolving terminal event, the authoritative source locator must be
recorded.

Evidence provenance must support the scientific decision itself; model
reasoning is not a substitute for a source locator.

## Review and adjudication fields

The frozen schema contains:

- `reviewer_id`
- `review_status`
- `adjudication_status`

The existing base validator does not freeze controlled vocabularies or a
complete workflow for these fields.

To avoid inventing uncontrolled review semantics, event-entry contract v1
requires all three fields to be empty for every accepted event.

A later review/adjudication workflow requires a separately frozen contract
amendment.

No review status or adjudication status may be improvised in free text.

## Notes

`notes` is optional.

Notes may record concise operational context but do not replace required
evidence provenance.

Tabs, newlines and NUL characters are prohibited inside individual event
fields.

## Proposed-event input

The future appender will accept a proposal TSV separate from the authoritative
ledger.

Its exact input fields are:

1. `screening_entity_id`
2. `batch_id`
3. `event_type`
4. `record_decision`
5. `exclusion_reason_code`
6. `candidate_method_flag`
7. `evidence_basis`
8. `evidence_source_locator`
9. `evidence_escalation_status`
10. `supersedes_event_id`
11. `operator_id`
12. `operator_type`
13. `notes`

The appender supplies:

- `event_id`;
- `baseline_queue_sha256`;
- `baseline_row_sha256`;
- `decision_timestamp_utc`;
- blank `reviewer_id`;
- blank `review_status`;
- blank `adjudication_status`.

The proposal TSV is not itself authoritative scientific history.

Only successfully validated rows appended to `event_ledger.tsv` become
authoritative events.

## Atomic validation sequence

Before any append, the future implementation must:

1. validate the immutable production package;
2. validate the complete existing event ledger;
3. verify the expected pre-ledger SHA;
4. validate proposal schema and field hygiene;
5. verify one-batch transaction scope;
6. verify entity uniqueness within the proposal;
7. resolve immutable batch position for deterministic proposal ordering;
8. verify current-event state for each proposed entity;
9. apply event-type-specific transition rules;
10. assign deterministic event IDs;
11. generate the UTC transaction timestamp;
12. fill frozen baseline hashes;
13. force review/adjudication fields blank;
14. construct candidate append rows;
15. verify the old ledger is the exact byte prefix of the candidate ledger;
16. validate the complete candidate ledger with the frozen base validator;
17. apply the stricter one-current-event invariant;
18. recheck the pre-ledger SHA immediately before publication;
19. publish the ledger transaction atomically;
20. re-read and validate the published ledger.

Failure at any point must leave the accepted ledger unchanged.

## Transaction receipt

Every successful append operation must report at least:

- batch ID;
- proposal SHA-256;
- pre-append ledger SHA-256;
- post-append ledger SHA-256;
- pre-append event count;
- post-append event count;
- first assigned event ID;
- last assigned event ID;
- transaction timestamp UTC;
- counts by event type;
- counts by terminal decision;
- derived state counts after append.

The receipt is operational provenance.

Its persistent checkpointing strategy will be frozen before live event entry.

## Derived state

The event ledger remains the primary record.

Current screening state is derived, never independently edited.

For each active entity:

- no current event -> `ready`;
- current `source_escalation` -> `awaiting_source_escalation`;
- current terminal decision -> `complete`.

The 484 metadata blockers remain `blocked_metadata` outside this event-entry
workflow.

## Batch progression

The appender implementation may support any valid frozen batch, but this
design does not authorise live event entry for any batch.

The first live authorisation will be a separate gate and should begin with
`B000001` only.

No later batch is automatically authorised by implementation readiness.

## Resumability and idempotence

The accepted event ledger is authoritative for progress.

A successful transaction followed by accidental rerun with the prior expected
ledger SHA must fail closed.

Validation without a new proposal must never mutate the ledger.

Restarting the workflow must reconstruct state solely from:

- immutable baseline;
- immutable batch membership;
- immutable historical carry-forwards; and
- append-only event ledger.

## Scientific boundary

At this design freeze:

- event-ledger rows = 0;
- newly entered scientific decisions = 0;
- source-escalation events = 0;
- method assessments = 0;
- role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- live event entry is not authorised;
- scientific screening has not begun.

## Next gate

`IMPLEMENT_CONTROLLED_BASELINE_SCIENTIFIC_SCREENING_EVENT_APPENDER_WITHOUT_EVENTS`

The next gate may implement:

- proposal parsing;
- strict event validation;
- deterministic event-ID assignment;
- compare-and-swap protection;
- append-only atomic publication;
- post-append validation;
- transaction receipts;
- hostile tests.

It must not append any event to the real production ledger.
