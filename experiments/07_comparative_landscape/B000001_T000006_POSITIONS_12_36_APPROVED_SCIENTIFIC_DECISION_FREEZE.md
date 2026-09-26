# Experiment 07 T000006 approved scientific decision freeze

Status: `FROZEN_T000006_APPROVED_SCIENTIFIC_DECISIONS_PRE_LIVE_AUTHORIZATION`

Human approval:

`approve T000006 review`

## Scope

- batch: `B000001`
- transaction: `T000006`
- positions: `12-36`
- record count: `25`

## Approved record-level outcomes

- retain for method assessment: **9**
- exclude: **16**
- source escalation: **0**

Retained positions:

`14, 15, 16, 17, 19, 22, 23, 24, 25`

Exclusion reasons:

- `application_only_no_reusable_method`: **13**
- `unrelated_variant_or_data_type`: **3**
- duplicate: **0**
- unsupported authoritative source: **0**

These are record-level screening outcomes only.

A retained record is not yet an included comparator, direct method, near-direct
method, canonical publication, Wave-1 anchor, or benchmark-eligible tool.
Retained records advance to later source-backed method assessment.

## Approved artifacts

Proposal SHA-256:

`dde6ad0df9506c2c468ff933d72723fe5a0eb621ae16f944b5b07d54f6c36e6f`

Decision-summary SHA-256:

`3784dd3a2b9e8e359327bd1caad3a986a9a95e5983b6845c35c9298cc5e77545`

Review packet before T000006 review:

`09e08a25873e9a628a2c7900b82f384f7b5838bb166b89d412759fe92a9101d6`

Review packet after approved T000006 review:

`d49d162191ba4737aeaecbf0934130a7a8816ad203504b2603a709ceec8a8b7a`

## Validation

The generic post-pilot guard verified:

- positions 1-11 remained locked;
- exactly positions 12-36 carry the new approved proposals;
- positions 37-500 remain blank;
- exact target order and identity are preserved.

The frozen event appender independently prepared the exact 25-row transaction
without publication and validated:

- 25 new events;
- expected IDs E000000023-E000000047;
- post-event count 47;
- strict ledger-prefix extension;
- projected complete count 36;
- projected awaiting-source-escalation count 0;
- projected ready count 94,586;
- projected blocked-metadata count 484.

The validation timestamp was transient and is not authority for future live
execution.

## Authority boundary

This freeze records approved scientific decisions.

It does **not**:

- create the T000006 live authorization;
- authorize mutation of the production ledger;
- append any production event;
- establish method-level inclusion or comparator status.

Production ledger remains at 22 events.

## Next gate

`CREATE_T000006_ONE_USE_LIVE_AUTHORIZATION`
