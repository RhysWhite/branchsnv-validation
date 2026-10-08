# Experiment 07 pre-decision execution production completion

Status: `FROZEN_PRE_EVENT_ENTRY_AUTHORIZATION`

## Purpose

This freeze records successful production of the controlled pre-decision
baseline scientific-screening execution package.

Parent writer-implementation commit:

`3a172fadacf8ed2a1e328cb66f0878a08fca7d45`

The execution package now exists on disk, but scientific screening has not
begun.

## Production root

`results/07_comparative_landscape/baseline_scientific_screening_execution`

## Frozen genesis package

Artifacts:

`8`

Total bytes:

`15,447,922`

Package identity SHA-256:

`5e4de148fe431402276d2f06f0305071fefc1be9a9be1fc1498b6bfe114ea39d`

Exact artifact hashes:

- batch manifest:
  `f2cc2c7ccaf230a56f9aa27f991b12885b600338b68b81d660af895f48adbfe0`
- batch membership:
  `858da5437197b78898c1703318d2c9c9be23a8f0eaade31df7b0f2de81726a91`
- prior-anchor carry-forwards:
  `5db8663c9dbf0915ea56430caba40bc87d5781ac1704a90f2eb563ca39c259b7`
- out-of-baseline prior anchor:
  `fb6fb842b7be6d63796accc8b8bd01e3a50fcbc21fc6c6326f23e5554975befe`
- event-ledger genesis:
  `d3ff9be1efe2b1237f616f25e702275ccc608577fa0ff8b301401a72900eb55f`
- event-ledger genesis metadata:
  `89486b47eb83f896259b84a5dd90b8ae3a41083637bd331261167e1165e113be`
- manifest:
  `66cfa32ffd93dbfbaf98f6a48a1587797bb6a1497b4b4fbc4115e6956983302a`
- immutable checksum ledger:
  `3ea3cc193f47da8a32e817579c31f4ca294de615e1e0e29e4eb37963e374f13c`

Semantic ordered active-ID SHA-256:

`d0970cbd5a582ce05585926bc1e81acba502b01a96acc4b84ab8db454a0ea4c1`

## Execution population

The frozen production package contains:

- active screening entities: 94,622;
- deterministic batches: 190;
- batch size: at most 500;
- final batch size: 122;
- historical in-baseline carry-forwards: 7;
- out-of-baseline historical anchors: 1;
- blocked_metadata entities outside batches: 484.

## Prior-anchor handling

Seven exact historical canonical-publication adjudications are carried
forward and excluded from ordinary active screening.

W0A06 / kSNP3.0 remains preserved as an out-of-baseline historical canonical
anchor without fabrication of a baseline entity.

## Event-ledger genesis

The authoritative append-only event ledger currently contains:

`0` event rows.

Genesis size:

`338 bytes`

Genesis SHA-256:

`d3ff9be1efe2b1237f616f25e702275ccc608577fa0ff8b301401a72900eb55f`

Event entry remains unauthorised.

The event ledger is deliberately NOT included directly in this completion
freeze's checksum manifest because a later explicitly authorised append is
expected to change its bytes.

Its immutable genesis state is instead permanently pinned by:

- this completion document;
- this completion's machine-readable JSON;
- `event_ledger_genesis.json`;
- the immutable execution manifest.

## Immutable package boundary

The following production artifacts remain immutable:

- `batch_manifest.tsv`
- `batch_membership.tsv`
- `prior_anchor_carry_forwards.tsv`
- `out_of_baseline_prior_anchor.tsv`
- `event_ledger_genesis.json`
- `manifest.json`
- `immutable_checksums.sha256`

The only future-mutable artifact is:

- `event_ledger.tsv`

and it may change only by validated append after a separately frozen
authorisation/implementation gate.

## Validation evidence

Before this completion freeze:

- the frozen writer revalidated the real production package;
- all eight artifact hashes and sizes matched the frozen writer contract;
- the package contained exactly eight files;
- immutable checksum validation passed;
- the event ledger remained exact zero-row genesis;
- the 190-batch / 94,622-entity structure independently validated;
- seven carry-forward targets were absent from active membership;
- all 484 metadata blockers were absent from active membership;
- W0A06 remained out-of-baseline;
- an independent rebuild reproduced all eight artifacts byte-for-byte;
- upstream evidence remained unchanged;
- tracked repository state remained unchanged;
- the production write created no Git objects.

## Scientific boundary

At this completion freeze:

- event-ledger rows = 0;
- newly entered record-level scientific decisions = 0;
- method assessments = 0;
- role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- event entry is not authorised;
- scientific screening has not begun.

The seven prior canonical-publication carry-forwards remain historical
adjudications rather than newly entered screening events.

## Next gate

`DESIGN_CONTROLLED_BASELINE_SCIENTIFIC_SCREENING_EVENT_ENTRY`

The next gate may define how human record-level screening decisions are
represented, validated, appended, reviewed, superseded and projected from the
event ledger.

It must not itself append an event or make a scientific screening decision.
