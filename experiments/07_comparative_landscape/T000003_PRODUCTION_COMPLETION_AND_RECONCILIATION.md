# Experiment 07 T000003 production completion and reconciliation

Status: `COMPLETE_RECONCILED`

Authorization commit:

`9be448af913a3ebfd83a56c65a66166f9c143989`

## Transaction identity

Transaction:

`T000003`

Authorization SHA-256:

`8efd0d4311f3fe6c519ce9721df62c5fccce93aab82eb53dec272c65bd248386`

Proposal SHA-256:

`ebc3efe4aa43cdeee2d727a440e3ddf7919df5ca4ea4103c13027e69b6319593`

Receipt SHA-256:

`275ab0a5e700c0951deec71816c2a44afae492d591e298eb1f72fb6c7db73ecd`

Pre-transaction ledger SHA-256:

`fb90d762d4fe9e81410816fe9403c735de138fe1614c11cb83993b40f2c63dff`

Post-transaction ledger SHA-256:

`a1303b93bd70c2106582f2a5a8749fcdfd649c18ff31fc6c3712cce8dc2f54fe`

## Production result

T000003 atomically appended eight
`superseding_record_decision` events:

- `E000000012` through `E000000019`.

They supersede:

- `E000000002` through `E000000009`.

The historical production ledger is preserved as a strict byte-identical
prefix.

## Scientific result

Current decisions for B000001 positions 2–9:

- positions 2, 3, 4, 6, 7, 8 and 9:
  - `exclude`
  - `application_only_no_reusable_method`
  - candidate method `false`

- position 5:
  - `retain_for_method_assessment`
  - candidate method `true`

Positions 10 and 11 remain unchanged:

- current events `E000000010` and `E000000011`;
- state `awaiting_source_escalation`;
- no terminal disposition;
- no duplicate/version relationship inferred.

## Reconciled active state

- complete: 9
- awaiting_source_escalation: 2
- ready: 94,611
- blocked_metadata: 484

Total production events:

`19`

## Transaction safety

- checkpoint status: complete
- checkpoint contains authorization, proposal and receipt
- no T000003 staging directory remains
- stale pre-ledger SHA replay is rejected
- the one-use authorization is consumed
- no additional live-event authority is created by this completion freeze

## Remaining B000001 pilot work

Two independent workstreams remain:

1. authoritative-source resolution for positions 10 and 11;
2. method-level assessment of position 5.

Position 5 method-level assessment must not silently infer:

- directness;
- landscape role;
- canonical publication;
- distinct method identity;
- Wave-1 eligibility.

Positions 10–11 remain unresolved until adequate authoritative evidence is
obtained.

## Next gate

`RESOLVE_POSITIONS_10_11_AND_METHOD_ASSESS_POSITION_5`

## Completion-freeze writer recovery

The first attempt to construct the machine-readable completion freeze stopped
after the Markdown completion document was created because the freeze wrapper
looked for `transaction_timestamp_utc` at the top level of the T000003
checkpoint receipt.

The production transaction was not affected.

The checkpoint contract stores the authoritative transaction timestamp in the
nested `appender_receipt`; the same timestamp is also present in the committed
one-use authorization.

Recovery therefore:

- preserved the completed production ledger and checkpoint unchanged;
- verified the nested appender timestamp against the committed authorization;
- reused the already-created completion Markdown;
- created the machine-readable completion freeze using the verified nested
  timestamp;
- performed no scientific or production-ledger mutation.
