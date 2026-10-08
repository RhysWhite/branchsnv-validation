# Experiment 07 baseline scientific-screening execution amendment 01 implementation

Status: `FROZEN_PRE_EXECUTION_PRODUCTION`

## Purpose

This freeze records the append-only implementation of execution contract
amendment 01.

It leaves the original frozen execution implementation unchanged.

Parent contract-amendment commit:

`70a692a70c4bc153bff0db3ebf70ba2eb5e84bd2`

## Frozen amendment implementation

Implementation:

`baseline_scientific_screening_execution_amendment_01.py`

SHA-256:

`a962c83e9e600995c97e66824d6d7a08caef4f5268d334be720da8d58954d725`

Hostile tests:

`test_baseline_scientific_screening_execution_amendment_01.py`

SHA-256:

`93e2556e74620d50e5aa3a1306199e03a3434ed39f04192beab3355b12d49839`

## Frozen prior-anchor contract

The implementation validates exactly:

- historical prior anchors: 8;
- in-baseline carry-forward targets: 7;
- out-of-baseline prior anchors: 1;
- ambiguous prior anchors: 0.

The out-of-baseline anchor remains:

- W0A06;
- kSNP3.0;
- DOI 10.1093/bioinformatics/btv271.

No substitute baseline entity is permitted.

## Frozen execution population

Baseline ready entities:

`94,629`

In-baseline historical carry-forwards:

`7`

Active ready entities:

`94,622`

Maximum batch size:

`500`

Deterministic batch count:

`190`

Final batch size:

`122`

## Deterministic batch invariants

Batch-manifest SHA-256:

`f2cc2c7ccaf230a56f9aa27f991b12885b600338b68b81d660af895f48adbfe0`

Ordered active screening-entity IDs SHA-256:

`d0970cbd5a582ce05585926bc1e81acba502b01a96acc4b84ab8db454a0ea4c1`

These hashes were reproduced identically across repeated independent dry runs.

The hashes describe in-memory deterministic execution state only.

No production batch artifacts have yet been written.

## Original frozen engine

The original execution implementation remains byte-exact and retains its
historical fail-closed behaviour requiring the previously unresolved mapping.

Amendment 01 is implemented by a separate append-only adapter layer.

## Scientific boundary

At this freeze:

- production screening batches created = 0;
- execution event-ledger rows = 0;
- record-level scientific decisions = 0;
- source-escalation events = 0;
- method assessments = 0;
- analytical-role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- network access = false;
- execution output root does not exist;
- historical screening log remains empty;
- immutable baseline remains unchanged.

## Next gate

`DESIGN_CONTROLLED_PRE_DECISION_EXECUTION_PRODUCTION_ARTIFACT_SET`

Before writing the 190 batches to production, the exact execution-production
artifact set, schemas, immutable membership representation, empty event-ledger
state, checksums, and production validation procedure must be frozen.

No scientific screening may begin during that design gate.
