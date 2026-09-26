# Experiment 07 B000001 T000007 post-pilot continuation design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

T000007 is the second production tranche using the generic post-pilot
transaction machinery.

It targets exactly:

- batch: `B000001`
- positions: `37-86`
- records: **50**
- expected event IDs: `E000000048-E000000097`

The parent production state is the completed T000006 state:

- production events: **47**
- complete baseline entities: **36**
- ready baseline entities: **94,586**
- blocked metadata: **484**
- awaiting source escalation: **0**
- ledger SHA-256: `dd83022eff2d2b069b80a6db495c90991e823fad03ece61010484e6fa839525b`

## Generic guard reuse hardening

The original generic guard v1 remains unchanged at:

`598c14c595a4bc5c1faff6c5411cae1b7fe898dbfeb5227a15d707d76fea6575`

A v2 copy is used for T000007:

`68cc5c501f89a389a842e0bc716e58801b56188a7621a887dcc2c349a8427ba5`

The only semantic change is removal of the stale T000006-specific design
assumption that positions 12-500 must all still be blank.

For subsequent tranches the guard instead requires the actual generic
invariants already enforced by review-packet validation:

1. positions before the current tranche are locked exactly to the frozen
   pre-review snapshot;
2. current target positions are proposal-blank before review; and
3. future positions remain proposal-blank.

The v2 guard remains backward-compatible with the frozen T000006 design.

No scientific eligibility, exclusion, analytical role, software identity,
method identity, or comparator decision is changed by this reuse hardening.

## Review state

Frozen T000007 pre-review snapshot SHA-256:

`d49d162191ba4737aeaecbf0934130a7a8816ad203504b2603a709ceec8a8b7a`

Positions 1-36 are historical review state.

Positions 37-86 are the only T000007 review target.

Positions 87-500 remain scientifically untouched.

## Authority boundary

This design:

- creates no scientific decisions;
- does not edit the production review packet;
- creates no live authorization;
- appends no production event;
- grants no authority outside positions 37-86;
- prohibits partial execution;
- prohibits superseding events in this initial tranche.

## Next gate

`CONDUCT_T000007_SCIENTIFIC_REVIEW_POSITIONS_37_TO_86`
