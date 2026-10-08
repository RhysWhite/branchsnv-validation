# Experiment 07 controlled baseline scientific-screening execution design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This document freezes the operational procedure for baseline record-level
scientific screening.

It does not perform screening.

The immutable pre-decision baseline is the production-completion state frozen
at commit:

`4287580270a8fd3e867008824526eadde7edaaf3`

The baseline queue SHA-256 is:

`97575b71c4607c3dcad893d90210f9132a83d0ae2e299ac2f1aef7e94f527d58`

## Baseline population

The frozen screening population contains:

- 95,113 screening entities;
- 94,898 publication entities;
- 215 software-registry entities;
- 94,629 currently `ready` entities;
- 484 `blocked_metadata` entities;
- 482 `blocked_title_unresolved`;
- 2 `blocked_title_conflict`.

The 484 metadata-blocked entities are not exclusions.

They are excluded from active record-screening batches and remain baseline
completion blockers unless resolved through a separately frozen metadata
resolution or reconciliation amendment.

## Immutable baseline

The production directory:

`results/07_comparative_landscape/scientific_screening`

is immutable during baseline scientific-screening execution.

No execution process may edit, overwrite or append to:

- `baseline_screening_queue.tsv`;
- `source_escalation.tsv`;
- `method_assessments.tsv`;
- `method_evidence.tsv`;
- `canonical_publications.tsv`;
- `wave1_promotion_candidates.tsv`;
- `manifest.json`;
- `checksums.sha256`.

Scientific-screening execution must use a separate output root.

## Execution output root

The future implementation may write only beneath:

`results/07_comparative_landscape/baseline_scientific_screening_execution`

That output does not exist at this design freeze.

## Scope of this execution phase

This phase is record-level screening only.

Allowed terminal record decisions are:

- `retain_for_method_assessment`
- `exclude`

This phase must not:

- establish consolidated software/method identities;
- make landscape eligibility decisions at method level;
- assign directness;
- assign analytical roles;
- select canonical publications;
- create Wave 1 promotion decisions;
- claim saturation;
- reopen discovery search.

Those remain later gates.

## Frozen record-level eligibility logic

A record advances to source-backed method assessment whenever available
title, name, abstract, description, metadata or authoritative source could
plausibly describe, introduce, substantially extend or document reusable
analytical software or a reusable analytical method relevant to at least one
of the six frozen landscape roles.

Uncertainty is resolved toward retention for source checking.

Discovery route, citation frequency, anchor multiplicity, provider count,
seed status, tool name familiarity and perceived performance are not
eligibility criteria.

Absence of an abstract is not an exclusion criterion.

Missing or insufficient metadata is not a scientific exclusion.

## Frozen exclusion reasons

An `exclude` decision requires exactly one of:

1. `application_only_no_reusable_method`
2. `unrelated_variant_or_data_type`
3. `duplicate_record_same_method_no_distinct_capability`
4. `unsupported_by_primary_or_stable_authoritative_source`

Records must not be excluded merely because software is:

- organism-specific;
- historical;
- unmaintained;
- web-only; or
- not currently executable.

## Evidence sufficiency

A terminal decision may use frozen baseline metadata when that evidence is
sufficient under the frozen screening rules.

If the available evidence is insufficient for a defensible terminal
disposition, the record enters `awaiting_source_escalation`.

A record in `awaiting_source_escalation` has no terminal record decision.

Source escalation may consult appropriate source material such as:

- a primary publication;
- an abstract or bibliographic record;
- stable official software documentation;
- stable repository documentation; or
- another authoritative source permitted by the frozen protocol.

Source escalation must not infer analytical role, directness or canonical
publication during this phase.

## Pre-existing metadata blockers

Entities whose frozen baseline state is `blocked_metadata` cannot enter a
record-screening batch.

Record-level screening must not invent titles, select a title-conflict winner,
or convert unresolved metadata into a scientific exclusion.

Any mechanism intended to unblock those entities requires its own separately
frozen metadata-resolution design and implementation.

Therefore two distinct completion states are recognised:

- `READY_SUBSET_COMPLETE_WITH_METADATA_BLOCKERS`
- `BASELINE_RECORD_SCREENING_COMPLETE`

The first may be reached while the 484 frozen metadata blockers remain.

The second may not.

## Prior Wave 0 anchor adjudication

The frozen unified screening protocol states that the eight initial Wave 0
anchors retain their prior adjudication and must not be independently
re-screened merely because they are rediscovered in the unified baseline.

A future implementation may carry forward a prior anchor adjudication only
when:

1. the prior adjudication source is frozen and hash-verified;
2. the baseline screening entity is mapped uniquely by frozen identity
   evidence;
3. no fuzzy-title or semantic identity inference is used;
4. the carry-forward source and mapping are recorded explicitly; and
5. an ambiguous or absent mapping fails closed.

A carried-forward adjudication is historical provenance, not a new screening
decision.

The number and identities of successful carry-forwards must be derived and
validated during implementation rather than assumed by this design.

## Deterministic batching

Only active `ready` entities that do not have a validated prior-adjudication
carry-forward enter active screening batches.

Batch construction is deterministic:

1. select eligible active entities;
2. sort lexicographically by `screening_entity_id`;
3. partition sequentially;
4. default maximum batch size = 500 entities;
5. assign batch IDs sequentially as `B000001`, `B000002`, ...;
6. record the exact ordered entity list and content hash for every batch.

The exact number of active batches is derived only after prior-adjudication
carry-forward mapping is validated.

Changing batch boundaries does not change scientific eligibility but requires
a new execution manifest; previously frozen batch manifests are never
silently rewritten.

## Append-only decision events

Scientific decisions are captured as append-only events.

No decision ledger row may be edited or deleted after it has entered an
accepted batch.

Corrections require a new event that explicitly references the event it
supersedes.

A current-state table, if produced, is a deterministic projection from the
append-only event ledger and is never the primary evidence record.

Each decision event must contain at least:

- `event_id`
- `event_type`
- `screening_entity_id`
- `baseline_queue_sha256`
- `baseline_row_sha256`
- `batch_id`
- `record_decision`
- `exclusion_reason_code`
- `candidate_method_flag`
- `evidence_basis`
- `evidence_source_locator`
- `evidence_escalation_status`
- `operator_id`
- `operator_type`
- `decision_timestamp_utc`
- `supersedes_event_id`
- `reviewer_id`
- `review_status`
- `adjudication_status`
- `notes`

## Decision invariants

For `retain_for_method_assessment`:

- `candidate_method_flag = true`;
- `exclusion_reason_code` is empty.

For `exclude`:

- `candidate_method_flag = false`;
- exactly one frozen exclusion reason is present.

For `awaiting_source_escalation`:

- `record_decision` is empty;
- `candidate_method_flag` is empty;
- `exclusion_reason_code` is empty.

A baseline `blocked_metadata` entity cannot receive any scientific decision
event under this execution contract.

Unknown decision values or exclusion codes fail closed.

## Operator provenance

Every scientific event requires an explicit operator identifier and operator
type.

Permitted operator types are:

- `human`
- `human_with_assistance`

Automated or model-generated preclassification may be used only as
non-authoritative working assistance unless a separate automated-screening
procedure has itself been frozen and validated.

Terminal scientific responsibility must therefore remain attributable in the
event ledger.

No mandatory double-screening percentage is introduced by this design.

If independent duplicate screening or formal inter-rater assessment is later
required, that is a separate frozen amendment rather than an implicit change.

## Review and correction

A terminal event may optionally receive reviewer provenance.

Conflicting unsuperseded terminal events for the same screening entity are a
hard failure.

A correction requires:

- a new unique event ID;
- `supersedes_event_id` pointing to the prior event;
- an explicit operator;
- an explicit reason in `notes`.

Historical events remain preserved.

## Resumability

Execution must be safely resumable.

Before accepting a batch, the implementation must verify:

- the frozen baseline queue SHA;
- the batch manifest hash;
- entity membership;
- absence of duplicate event IDs;
- valid state transitions;
- decision invariants;
- existing accepted event hashes.

Re-running validation without new accepted events must be idempotent.

A partially completed batch must never be represented as complete.

## State transitions

Permitted record-screening transitions are:

`ready -> complete`

or

`ready -> awaiting_source_escalation -> complete`

A `complete` record may change only through an explicit superseding event.

`blocked_metadata` has no transition under this execution phase.

## Ready-subset completion gate

`READY_SUBSET_COMPLETE_WITH_METADATA_BLOCKERS` requires:

- every active `ready` entity has exactly one current terminal disposition;
- all source escalations for active `ready` entities are resolved;
- no conflicting unsuperseded decisions remain;
- all validated prior-anchor carry-forwards are accounted for;
- no active batch is partial or invalid;
- the immutable baseline queue still has its frozen SHA;
- the original 484 metadata blockers remain separately accounted for.

This state is not full baseline completion.

## Full baseline record-screening completion gate

`BASELINE_RECORD_SCREENING_COMPLETE` additionally requires:

- zero unresolved `blocked_metadata` entities;
- all previously blocked entities are resolved through separately frozen
  metadata/reconciliation procedures;
- every resulting screenable entity has a terminal record decision;
- no unresolved source escalation exists;
- no unresolved decision conflict exists.

Until then, baseline screening is incomplete.

## Downstream gates

Method assessment remains separate from record-level screening.

Directness classification remains separate.

Canonical-publication selection remains separate.

Wave 1 promotion remains prohibited until the entire baseline completion gate
defined by the frozen unified protocol is satisfied.

Saturation cannot be assessed during baseline record-level screening.

## Scientific boundary at this freeze

At this design freeze:

- scientific screening decisions = 0;
- method assessments = 0;
- role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- the historical screening log remains empty;
- the frozen production screening infrastructure remains unchanged.

## Next gate

`IMPLEMENT_CONTROLLED_BASELINE_SCIENTIFIC_SCREENING_EXECUTION_WITHOUT_DECISIONS`

The implementation gate may create validators, deterministic batch
construction, append-only event-ledger machinery and derived-state logic.

It must not itself make scientific screening decisions.
