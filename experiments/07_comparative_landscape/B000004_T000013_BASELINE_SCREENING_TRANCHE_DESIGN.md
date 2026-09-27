# Experiment 07 B000004 T000013 baseline-screening tranche design

Status:

`FROZEN_PRE_IMPLEMENTATION`

## Scope

T000013 targets the complete frozen B000004 batch:

- batch: `B000004`
- positions: `1-500`
- global active indices: `1501-2000`
- target records: **500**
- expected event IDs: `E000001512-E000002011`

## Parent production state

- events: **1,511**
- complete: **1,500**
- ready: **93,122**
- blocked metadata: **484**
- awaiting source escalation: **0**

Parent ledger SHA-256:

`edb131a6381f0d3afb03549c4773d55762c738eec435b3b5d8dfa0448865f08b`

## Review packet

The B000004 packet contains exactly **500** rows.

Pre-review SHA-256:

`3d05638abeb1b1c0f44feb371e098c5ddb12d2c3013f3fe50c32b81731fdd54c`

All proposed scientific-decision fields are blank.

## Scientific boundary

This design contains no scientific decisions.

Record-level screening remains governed by the frozen Experiment 07
eligibility criteria and six analytical roles.

Retention does not itself establish final software-landscape inclusion,
canonical-publication status, direct/near-direct status, Wave-1 status,
or benchmark eligibility.

## Authority boundary

This design creates no live authorization and grants no production
mutation authority.

## Next gate

`CONDUCT_T000013_SCIENTIFIC_REVIEW_B000004_POSITIONS_1_TO_500`
