# Experiment 07 controlled baseline scientific-screening event-appender implementation

Status: `FROZEN_PRE_LIVE_AUTHORIZATION`

## Purpose

This freeze records the implementation and hostile validation of the controlled
baseline scientific-screening event appender.

Parent event-entry-design commit:

`584134c97af6816629f5434bf9ad2199a828eb0b`

The implementation capability now exists, but live production event entry
remains unauthorised.

Scientific screening has not begun.

## Frozen implementation

Implementation:

`baseline_scientific_screening_event_appender.py`

SHA-256:

`abf4c15e9c993bcb96c73ccb53ff3dae56e229c533e9df25056c37cfd5eda98b`

Hostile tests:

`test_baseline_scientific_screening_event_appender.py`

SHA-256:

`fad1928184c43521afb77a340cc02fe953c8baa0af7c4edf42c6bc9a17fee87e`

## Implemented capability

The frozen appender implements:

- exact 13-field proposal parsing;
- exact 20-field authoritative event generation;
- immutable execution-package validation;
- frozen baseline-row and batch-membership validation;
- existing event-ledger validation;
- single-current-unsuperseded-event enforcement;
- valid initial terminal record decisions;
- valid source-escalation events;
- source-escalation resolution by superseding terminal event;
- terminal correction by superseding terminal event;
- deterministic sequential event IDs;
- UTC whole-second transaction timestamps;
- one-batch transaction scope;
- deterministic proposal ordering by immutable batch position;
- one proposal event per entity per transaction;
- evidence provenance validation;
- operator provenance validation;
- forced blank review/adjudication fields in v1;
- field-hygiene checks;
- compare-and-swap protection using expected pre-ledger SHA-256;
- strict byte-prefix append semantics;
- atomic temporary-file publication;
- post-publication validation;
- transaction receipt generation;
- derived current-state counts;
- stale-SHA replay protection.

## Event-chain contract

The implementation preserves the frozen transition model:

- ready -> initial terminal record decision;
- ready -> source escalation;
- source escalation -> superseding terminal resolution;
- terminal -> superseding terminal correction.

At most one current unsuperseded event is permitted per entity.

Branching event chains are prohibited.

A superseding event must reference the current event for the same entity.

## Scientific authority

The appender performs no scientific classification itself.

Scientific proposal values must be supplied by a human-controlled workflow.

The implementation does not infer:

- retain/exclude status;
- exclusion reason;
- candidate-method status;
- evidence sufficiency;
- method identity;
- analytical role;
- directness;
- canonical publication;
- Wave 1 eligibility.

`human_with_assistance` remains human-authorised provenance.

Autonomous model-authored production events remain prohibited.

## Live-production safety boundary

The appender's command-line interface explicitly refuses mutation of the real
production ledger.

A direct CLI attempt against:

`results/07_comparative_landscape/baseline_scientific_screening_execution/event_ledger.tsv`

fails with:

`Real production event entry is not authorised`

The underlying library routine contains an explicit
`allow_production` parameter solely so that a future separately frozen
authorisation layer can invoke the already-tested atomic transaction machinery.

That parameter is NOT authorisation by itself.

No current command or freeze authorises its use against production.

## Validation evidence

The implementation passed hostile tests covering:

- initial source escalation;
- deterministic first event ID;
- automatic blank review/adjudication fields;
- strict byte-prefix extension;
- source-escalation resolution;
- deterministic second event ID;
- terminal correction;
- preservation of escalation history;
- initial terminal decision;
- rejection of multiple proposed events for one entity;
- rejection of cross-batch transactions;
- terminal evidence-source requirement;
- terminal candidate-flag consistency;
- current-event supersession requirement;
- rejection of a second unsuperseded source escalation;
- embedded-newline rejection;
- stale expected-ledger SHA rejection;
- sub-second timestamp rejection;
- read-only validation of the real production genesis;
- successful atomic append to a temporary copy of the real genesis ledger;
- post-publication validation of that temporary ledger;
- stale-SHA replay rejection after successful temporary append;
- direct production-mutation refusal;
- proof that the real production ledger remained untouched.

## Production ledger state at freeze

Current production event rows:

`0`

Current production event-ledger SHA-256:

`d3ff9be1efe2b1237f616f25e702275ccc608577fa0ff8b301401a72900eb55f`

Derived active states:

- ready: 94,622;
- awaiting source escalation: 0;
- complete: 0;
- blocked metadata: 484.

The immutable execution package remains unchanged.

## Checksum-manifest treatment of event_ledger.tsv

The production `event_ledger.tsv` is deliberately not included directly in
this implementation freeze's checksum manifest.

Its current zero-event genesis SHA is pinned in:

- this document;
- the machine-readable implementation freeze;
- the prior production-completion freeze;
- `event_ledger_genesis.json`.

This prevents a future separately authorised append from falsely invalidating
the historical implementation freeze.

## Scientific boundary

At this freeze:

- accepted production event rows = 0;
- new scientific record-level decisions = 0;
- production source-escalation events = 0;
- method assessments = 0;
- role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- live event entry is not authorised;
- scientific screening has not begun.

## Next gate

`DESIGN_CONTROLLED_B000001_LIVE_EVENT_ENTRY_AUTHORIZATION`

The next gate may define the precise conditions under which the frozen
appender may first be used against production for batch B000001.

It must not itself append an event.
