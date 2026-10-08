# Experiment 07 B000001 positions 2–9 approved scientific-decision freeze

Status: `FROZEN_PRE_LIVE_EVENT_AUTHORIZATION`

Parent ASR000002 production-completion commit:

`27323d1364206c55eb064fd39fdf5c374fba481f`

ASR000002 completion-freeze SHA-256:

`aa20d24a66482122156f8e6e11df8febc3b2c9a21354aa728c9d2b492c8ca25d`

## Human approval

Approval phrase:

`APPROVE POSITIONS 2-9`

Operator:

- ID: `Rhys`
- type: `human_with_assistance`

The human operator remains the scientific decision-maker.

## Exact approved scope

Exactly B000001 positions 2–9 are approved.

Current source-escalation events to supersede:

- `E000000002`
- `E000000003`
- `E000000004`
- `E000000005`
- `E000000006`
- `E000000007`
- `E000000008`
- `E000000009`

Expected future event IDs if subsequently authorized and appended atomically:

- `E000000012` through `E000000019`

## Approved dispositions

Positions 2, 3, 4, 6, 7, 8 and 9:

- decision: `exclude`
- exclusion reason:
  `application_only_no_reusable_method`
- candidate method: `false`
- evidence escalation status: `resolved`

Position 5:

- decision: `retain_for_method_assessment`
- exclusion reason: blank
- candidate method: `true`
- evidence escalation status: `resolved`

Position 5 is not yet assigned:

- directness;
- landscape role(s);
- canonical-publication state;
- Wave-1 promotion state.

Those belong to method-level assessment.

## Positions 10–11

Positions 10 and 11 remain outside this transaction.

Their current source-escalation events remain current.

No duplicate/version relationship is inferred.

No scientific disposition is assigned.

## Evidence

Frozen source-review JSON SHA-256:

`f3fb68cb08f03c255daf13ee0d72222b14528cf41920b31e0af57c6d3a005928`

Frozen source-review Markdown SHA-256:

`399d60f54ffe1f3273eb75ba7dceca2cab4c2e99d15af7deee79a458334f0952`

Approved proposal SHA-256:

`ebc3efe4aa43cdeee2d727a440e3ddf7919df5ca4ea4103c13027e69b6319593`

Approved decision-packet checksum SHA-256:

`8ae2e10abdad612ca31e2cbfd64735077dadae259fc462cf712f0b6c1d1aadee`

## Authority boundary

This freeze records approved scientific dispositions only.

It does **not** authorize production event-ledger mutation.

The event ledger must remain at 11 events until a separate one-use live
authorization is created.

The next live transaction, if separately authorized, must contain exactly
eight `superseding_record_decision` events and must be atomic.

## Next gate

`CREATE_ONE_USE_AUTHORIZATION_FOR_E000000012_TO_E000000019`
