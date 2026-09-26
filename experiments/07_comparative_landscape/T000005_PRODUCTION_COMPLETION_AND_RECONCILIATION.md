# Experiment 07 T000005 production completion and reconciliation

Status: `COMPLETE_RECONCILED`

Authorization commit:

`e450559584400ca0e621276ac34cf3c0d09e048b`

## Transaction identity

Transaction:

`T000005`

Authorization SHA-256:

`e8728251268b6366f9e4e4bace62f28250a4133929bd7eb5b8b18344871ac00c`

Proposal SHA-256:

`6d57c5b0dd105baa61635599641df6bb6e3abd2b107c7b6ebcfbb5eb04fd416b`

Receipt SHA-256:

`417c5bc50fcf3681ca3b864e2bb7e4aafece173397026b3d12b3704eb24d4bb6`

Pre-transaction ledger SHA-256:

`3433a183d6a5bb4434a4b26e72bf6e380d546d6e53688a506328bf7f4bda5793`

Post-transaction ledger SHA-256:

`85eabc27f89cc215b75b4b48611e6131f8ef1f7e7d5a022b1229d1241bd960ac`

Transaction timestamp:

`2026-09-26T02:56:57Z`

## Production result

T000005 atomically appended:

`E000000022`

as a `superseding_record_decision` for B000001 position 10.

It supersedes:

`E000000010`

Scientific disposition:

- decision: `exclude`
- exclusion reason: `application_only_no_reusable_method`
- candidate-method flag: `false`
- evidence escalation status: `resolved`

## Current Position 10 state

Position 10 now has exactly one current event:

`E000000022`

The prior source-escalation event `E000000010` remains preserved in event
history and is superseded.

## Reconciled active state

- complete: 11
- awaiting_source_escalation: 0
- ready: 94,611
- blocked_metadata: 484

Total production events:

`22`

## Initial B000001 positions 1-11 pilot

All positions 1-11 have current terminal scientific decisions.

Current unresolved pilot positions:

`0`

Current pilot events awaiting source escalation:

`0`

For terminal-event semantics, a direct terminal `record_decision` may have a
blank `evidence_escalation_status`. A terminal event produced by resolving a
prior source escalation may carry `resolved`.

Position 1 is the direct-terminal canary and therefore legitimately retains a
blank escalation-status field. It is not unresolved.

## Transaction safety

- checkpoint status: complete
- checkpoint contains exactly authorization, proposal and receipt
- published ledger SHA matches the authorized projected SHA
- no T000005 staging remains
- stale pre-ledger SHA replay was rejected
- the one-use T000005 authorization is consumed
- no additional live-event authority is created by this freeze

## Authority boundary

This freeze reconciles the already executed transaction.

It does not append another event, alter a scientific disposition, or authorize
future production mutation.

## Next gate

`DESIGN_POST_PILOT_BASELINE_SCIENTIFIC_SCREENING_CONTINUATION`
