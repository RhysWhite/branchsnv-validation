# Experiment 07 T000008 approved scientific decision freeze

Status:

`FROZEN_T000008_APPROVED_SCIENTIFIC_DECISIONS_PRE_LIVE_AUTHORIZATION`

Human approval:

`APPROVE T000008 REVIEW`

## Scope

- batch: `B000001`
- transaction: `T000008`
- positions: `87-186`
- record count: **100**

## Approved record-level outcomes

- retain for method assessment: **7**
- exclude: **93**
- source escalation: **0**

Retained positions:

`87, 88, 90, 106, 130, 138, 170`

Exclusion reasons:

- `application_only_no_reusable_method`: **92**
- `unrelated_variant_or_data_type`: **1**
- `duplicate_record_same_method_no_distinct_capability`: **0**
- `unsupported_by_primary_or_stable_authoritative_source`: **0**

The unrelated-data/analytical-role exclusion is position **89**.

These are record-level screening decisions only.

A retained record is not yet an included comparator, direct method,
near-direct method, canonical publication, Wave-1 anchor, or executable
benchmark tool.

## Approved artifacts

Proposal SHA-256:

`da1eb2b9f6745f1b29e2c12e13a4774efe03760241687746221ee21943b1a434`

Decision-summary SHA-256:

`fb1194b7218148c76e5322c32a60fb27a2fce7b0a3123aa728c2608edd4e129c`

Review packet before T000008 review:

`cade5407e9a75bd45e282f7b4ca2e2b1c53973128be5aed76730ec85c344f7ab`

Review packet after approved T000008 review:

`9852bb143724aae7a17155bf9c033c003007a3c7b5d7b1b26c3e16a727e1c134`

## Validation

The generic post-pilot guard v2 verified:

- positions 1-86 remained locked to the frozen pre-review snapshot;
- exactly positions 87-186 contain the approved T000008 proposals;
- positions 187-500 remain proposal-blank;
- exact target identity and ordering are preserved.

The frozen event appender independently prepared the exact 100-row
transaction without publication and validated:

- 100 new events;
- expected IDs `E000000098-E000000197`;
- projected post-event count **197**;
- strict ledger-prefix extension;
- projected complete count **186**;
- projected ready count **94,436**;
- projected blocked-metadata count **484**;
- projected awaiting-source-escalation count **0**.

The validation timestamp is transient and is not live execution authority.

## Authority boundary

This freeze records approved scientific decisions.

It does **not**:

- create T000008 live authorization;
- authorize mutation of the production ledger;
- append any production event;
- establish final method-level inclusion or comparator status.

Production ledger remains at **97 events**.

## Next gate

`CREATE_T000008_ONE_USE_LIVE_AUTHORIZATION`
