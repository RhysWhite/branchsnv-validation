# Experiment 07 T000004 production completion and reconciliation

Status: `COMPLETE_RECONCILED`

Authorization commit:

`ee57d382ce2df3211718b064f71145a1e3035172`

## Transaction identity

Transaction:

`T000004`

Authorization SHA-256:

`e966f38b2e2836f6ad338817a78beb0e8b19e19be7f3677d6d23559f324b5fc7`

Proposal SHA-256:

`eb56ba69839d9e5507f05dec8898e382b1ae1d2059ff55607f865b8da231c068`

Receipt SHA-256:

`0d46c92019d71bbda8ca7e7dd378286d0ba37db9eeb353ff067d849700b7c773`

Pre-transaction ledger SHA-256:

`a1303b93bd70c2106582f2a5a8749fcdfd649c18ff31fc6c3712cce8dc2f54fe`

Post-transaction ledger SHA-256:

`3433a183d6a5bb4434a4b26e72bf6e380d546d6e53688a506328bf7f4bda5793`

Transaction timestamp:

`2026-09-25T22:27:42Z`

## Production result

T000004 atomically appended two `superseding_record_decision` events:

- `E000000020`
- `E000000021`

They supersede:

- position 5: `E000000015`
- position 11: `E000000011`

The pre-T000004 production ledger remains a strict byte-identical prefix.

## Current scientific state

Position 5:

- current event: `E000000020`
- decision: `exclude`
- reason: `duplicate_record_same_method_no_distinct_capability`
- candidate-method flag: `false`

Position 11:

- current event: `E000000021`
- decision: `exclude`
- reason: `application_only_no_reusable_method`
- candidate-method flag: `false`

Position 10 remains unchanged:

- current event: `E000000010`
- state: `awaiting_source_escalation`
- no terminal scientific decision

## Reconciled active state

- complete: 10
- awaiting_source_escalation: 1
- ready: 94,611
- blocked_metadata: 484

Total production events:

`21`

## Transaction safety

- checkpoint status: complete
- checkpoint contains authorization, proposal and receipt
- no T000004 staging directory remains
- stale pre-ledger SHA replay is rejected
- the one-use authorization is consumed
- no additional live-event authority is created by this completion freeze

## Remaining B000001 pilot work

Only position 10 remains unresolved within the initial positions 1–11 pilot.

Position 10 must remain source-backed and must not inherit a terminal
disposition solely from its publisher-established version relationship to
position 11.

## Next gate

`RESOLVE_B000001_POSITION_10`
