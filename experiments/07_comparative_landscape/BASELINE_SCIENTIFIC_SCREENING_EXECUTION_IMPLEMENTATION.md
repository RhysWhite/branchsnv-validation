# Experiment 07 controlled baseline scientific-screening execution implementation

Status: `FROZEN_PRE_CARRY_FORWARD_MAPPING`

## Purpose

This freeze records the implementation of the controlled baseline
record-screening execution machinery.

It does not perform scientific screening.

Parent execution-design commit:

`3a49a9837a09cf3a49ff2bb567beb3db5bcf1b74`

## Frozen implementation

Implementation:

`baseline_scientific_screening_execution.py`

SHA-256:

`6084faeffe6d5b28aaeb6150ad434bf7f723507efde1c67e336549ee61a5e97a`

Hostile tests:

`test_baseline_scientific_screening_execution.py`

SHA-256:

`d452890c84080a80d05b9bd66ebca796afc8740a304ec1370bf85a00732624d0`

## Immutable baseline

The implementation validates the frozen baseline queue:

- screening entities: 95,113
- ready entities: 94,629
- blocked_metadata entities: 484

Queue SHA-256:

`97575b71c4607c3dcad893d90210f9132a83d0ae2e299ac2f1aef7e94f527d58`

The production scientific-screening infrastructure remains immutable.

## Implemented machinery

The implementation provides:

- frozen-baseline validation;
- deterministic baseline-row hashing;
- deterministic ordered batch-membership hashing;
- terminal decision invariant validation;
- source-escalation event validation;
- append-only event validation;
- explicit supersession validation;
- operator provenance validation;
- deterministic current-state projection;
- conflict detection;
- prior-adjudication carry-forward validation;
- deterministic batch construction after carry-forward validation;
- fail-closed handling of blocked metadata entities.

## Prior Wave 0 adjudication dependency

The eight initial Wave 0 anchors retain their prior adjudication under the
frozen protocol.

At this implementation freeze:

- expected prior anchors = 8;
- successfully mapped prior anchors = 0;
- mapping status = `PENDING_FROZEN_MAPPING`;
- fuzzy or semantic mapping is prohibited;
- real batch generation is prohibited;
- active ready population is therefore not yet instantiated;
- real batch count is therefore not yet instantiated.

This is an intentional fail-closed dependency.

The implementation does not infer or guess any mapping.

## Batch-generation boundary

Real batch generation becomes permissible only when a separately evidenced
carry-forward mapping:

1. contains exactly eight prior anchors;
2. maps each anchor uniquely to a frozen baseline entity;
3. maps only to `ready` entities;
4. records frozen prior-adjudication source provenance;
5. provides a SHA-256 for the prior source;
6. uses an explicit exact mapping basis; and
7. passes all carry-forward validation.

Until then:

`batch_generation_authorized = false`

## Scientific boundary

At this implementation freeze:

- record-level scientific decisions = 0;
- event-ledger rows = 0;
- source-escalation decisions = 0;
- method assessments = 0;
- analytical-role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- network access = false;
- execution output root does not exist;
- historical screening log remains empty;
- frozen scientific-screening production remains unchanged.

## Next gate

`RESOLVE_AND_FREEZE_PRIOR_WAVE0_ADJUDICATION_MAPPING`

The next gate is evidence resolution only.

It may determine the unique frozen-baseline mapping for the eight previously
adjudicated Wave 0 anchors.

It must not:

- make new scientific screening decisions;
- generate real screening batches before the mapping is frozen;
- modify prior anchor adjudications;
- use fuzzy or semantic title matching;
- alter the frozen baseline queue;
- perform method assessment;
- assign roles or directness;
- select canonical publications; or
- promote Wave 1 anchors.
