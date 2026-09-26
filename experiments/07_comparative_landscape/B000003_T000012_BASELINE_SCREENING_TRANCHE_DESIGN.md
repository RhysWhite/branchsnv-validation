# Experiment 07 B000003 T000012 baseline-screening tranche design

Status:

`FROZEN_PRE_IMPLEMENTATION`

## Scope

T000012 targets the complete frozen B000003 batch:

- batch: `B000003`
- positions: `1-500`
- global active indices: `1001-1500`
- target records: **500**
- expected event IDs: `E000001012-E000001511`

## Parent production state

- events: **1,011**
- complete: **1,000**
- ready: **93,622**
- blocked metadata: **484**
- awaiting source escalation: **0**

Parent ledger SHA-256:

`ab183ceb88b2cd9f09072dc9a2e819c735cb95ef723b73a732b99d065410deae`

## Review packet

The B000003 packet contains exactly **500** rows.

Pre-review SHA-256:

`bb5124e6c427498a82dc2c6f50be7956076b6a8708d32bc4175b2effe3de38ac`

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

`CONDUCT_T000012_SCIENTIFIC_REVIEW_B000003_POSITIONS_1_TO_500`
