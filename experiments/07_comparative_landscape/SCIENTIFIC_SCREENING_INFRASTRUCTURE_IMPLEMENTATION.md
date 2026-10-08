# Experiment 07 scientific-screening infrastructure implementation freeze

Status: `FROZEN_PRE_PRODUCTION`

## Purpose

This freeze records the implementation that constructs the deterministic
baseline scientific-screening infrastructure while making no scientific
screening decisions.

Parent scientific-screening design commit:

`c63a8528f3bab87fad5051a58b3d06d300e1bf00`

## Frozen implementation

Implementation:

`scientific_screening_infrastructure.py`

SHA-256:

`22e9660b8705968e2bdbc88b893c74a69905b5da63c0b8174f7ec2722bf6c5be`

Hostile tests:

`test_scientific_screening_infrastructure.py`

SHA-256:

`7f95dd31f3acce4f09580c60211b3747e557076730a86e32869a2f154effddfa`

## Frozen baseline universe

The implementation independently rebuilds the frozen cross-stage screening
universe from the canonical database and Wave 0 citation inputs.

Exact baseline:

- screening entities: 95,113
- publication entities: 94,898
- software-registry entities: 215
- pre-screening attention overlay: 1,342

## Initial queue state

The deterministic pre-decision queue contains:

- `ready`: 94,629
- `blocked_metadata`: 484

Metadata state:

- `screenable`: 94,629
- `blocked_title_unresolved`: 482
- `blocked_title_conflict`: 2

Deterministic queue SHA-256:

`97575b71c4607c3dcad893d90210f9132a83d0ae2e299ac2f1aef7e94f527d58`

These are operational queue states, not scientific include/exclude decisions.

## Historical cross-stage hash contract

All five frozen cross-stage hashes are reproduced exactly.

The historical subsidiary-hash representation for automatic links,
cross-stage conflicts, publication components and software-registry components
is compact sorted JSON without a trailing newline.

The full `complete_result` hash uses the frozen cross-stage
`result_bytes()` representation, including its trailing newline.

This encoding distinction is provenance only and changes no scientific
content.

## Scientific boundary

At this implementation freeze:

- scientific screening decisions = 0
- source-escalation rows = 0
- method assessments = 0
- method-evidence rows = 0
- new role assignments = 0
- canonical-publication rows = 0
- Wave 1 promotion candidates = 0
- Wave 1 promotions = 0
- network access = false
- historical screening log remains unchanged and empty
- discovery corpus remains unchanged
- retrieval evidence remains unchanged
- reconciliation evidence remains unchanged

## Production state

No production scientific-screening directory exists at this freeze.

No baseline screening queue has yet been written to production.

## Next gate

`RUN_CONTROLLED_SCIENTIFIC_SCREENING_INFRASTRUCTURE_PRODUCTION`

The controlled production run may create only deterministic pre-decision
screening infrastructure.

It must not make scientific include/exclude decisions, perform source-backed
method assessment, assign roles, select canonical publications, or promote
Wave 1 anchors.
