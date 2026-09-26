# Experiment 07 B000002 T000011 baseline-screening tranche design

Status:

`FROZEN_PRE_IMPLEMENTATION`

## Scope

T000011 targets the complete frozen B000002 batch:

- batch: `B000002`
- positions: `1-500`
- global active indices: `501-1000`
- target records: **500**
- expected event IDs: `E000000512-E000001011`

All 500 target records are frozen baseline-ready.

## Parent production state

- events: **511**
- complete: **500**
- ready: **94,122**
- blocked metadata: **484**
- awaiting source escalation: **0**

Parent ledger SHA-256:

`080b60b63c46524fe3f97d7db37ca56aba255e8633170b8f709f648ab11cd413`

## Review packet

The B000002 packet contains exactly **500** rows.

Pre-review SHA-256:

`ec10cccbe0a71b5111a392631fc5871b5b3ef936dcc6bae2669e0ffce7c6e47d`

All proposed scientific-decision fields are blank.

T000011 covers the entire batch, so there are no historical or future
B000002 positions outside this transaction.

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

`CONDUCT_T000011_SCIENTIFIC_REVIEW_B000002_POSITIONS_1_TO_500`
