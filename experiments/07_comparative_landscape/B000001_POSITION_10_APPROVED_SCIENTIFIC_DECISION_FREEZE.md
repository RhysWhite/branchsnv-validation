# Experiment 07 B000001 position 10 approved scientific-decision freeze

Status: `HUMAN_APPROVED_PRE_LIVE_FREEZE`

Parent commit:

`0d7e0b68de38fd120c3fa396648b430b0c77c60b`

## Scope

This freeze covers only B000001 position 10:

`publication_component:citation:publication:doi:10.1002/9780470015902.a0020859`

Current production event:

`E000000010`

Current state:

`awaiting_source_escalation`

## Human-approved scientific disposition

The human operator explicitly approved:

`APPROVE POSITION 10: exclude — application_only_no_reusable_method`

The approved terminal resolution is:

- event type: `superseding_record_decision`
- record decision: `exclude`
- exclusion reason: `application_only_no_reusable_method`
- candidate-method flag: `false`
- evidence escalation status: `resolved`
- supersedes: `E000000010`
- expected future event ID: `E000000022`

Operator:

- ID: `Rhys`
- type: `human_with_assistance`

## Evidence basis

The disposition is based on the separately frozen Position 10 source-resolution
evidence.

Evidence packet SHA-256:

`59d70f1a8dfea1042be3f48f03e09648ca173fe482841fd571e181ae56b928a5`

Evidence-freeze SHA-256:

`9e5be4661751d2af72d74e26f184478f3d2e5b1d9b6600d5b71df8b453a6800b`

The exact DOI record identifies the publication as an Encyclopedia of Life
Sciences article on purifying selection, amino-acid replacement mutations and
human genetic disease. The substantive registered source evidence does not
establish a distinct reusable sequence-analysis, variant-analysis or
phylogenetic software/method capability.

## Frozen decision packet

Proposal SHA-256:

`6d57c5b0dd105baa61635599641df6bb6e3abd2b107c7b6ebcfbb5eb04fd416b`

Decision summary SHA-256:

`1a4c29087d2b4657cc85d0749474d05ccf8909ebcc9b3ed295a7e6e673740198`

Decision-packet checksum-manifest SHA-256:

`1a3ef1a22c01c5cd9ec3dd39940924d28ab8159e56520b581421fafd9d99545f`

## Production boundary

The production ledger remains unchanged at:

`3433a183d6a5bb4434a4b26e72bf6e380d546d6e53688a506328bf7f4bda5793`

with exactly 21 events.

This decision freeze does not:

- append `E000000022`;
- mutate the production ledger;
- itself grant live-event mutation authority;
- consume any live authorization.

## Projected live transition

If separately authorized and successfully executed:

- event count: `21 -> 22`
- Position 10: `awaiting_source_escalation -> complete`
- awaiting source escalation: `1 -> 0`
- complete: `10 -> 11`

## Next gate

`CREATE_CONTROLLED_T000005_POSITION_10_ONE_USE_AUTHORIZATION`
