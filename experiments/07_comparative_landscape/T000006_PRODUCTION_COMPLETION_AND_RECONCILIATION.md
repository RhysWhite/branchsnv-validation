# Experiment 07 T000006 production completion and reconciliation

Status: `T000006_PRODUCTION_COMPLETE_RECONCILED`

## Production transaction

T000006 has completed successfully.

- batch: `B000001`
- positions: `12-36`
- events appended: **25**
- assigned event IDs: `E000000023-E000000047`
- pre-event count: **22**
- post-event count: **47**

Pre-ledger SHA-256:

`85eabc27f89cc215b75b4b48611e6131f8ef1f7e7d5a022b1229d1241bd960ac`

Post-ledger SHA-256:

`dd83022eff2d2b069b80a6db495c90991e823fad03ece61010484e6fa839525b`

The original 22-event ledger was independently verified as the exact byte
prefix of the completed 47-event ledger.

## Scientific outcomes

- exclude: **16**
- retain for method assessment: **9**
- source escalation: **0**

Derived baseline state after T000006:

- complete: **36**
- ready: **94,586**
- blocked metadata: **484**
- awaiting source escalation: **0**

The nine retained records remain record-level candidates for later source-backed
method assessment. T000006 does not itself assign final software-landscape
inclusion, analytical role, canonical publication or benchmark eligibility.

## Authorization

Authorization commit:

`2b6b0fcbc1b7af1dc27ad9c2683a37abd2a82a84`

Authorization SHA-256:

`9f0b7e28e0741b04d1e78c557fa3c87050e73bc77b9559cc497a365e6a469961`

Fixed transaction timestamp:

`2026-09-26T04:53:22Z`

Approved proposal SHA-256:

`dde6ad0df9506c2c468ff933d72723fe5a0eb621ae16f944b5b07d54f6c36e6f`

Human authority:

- `AUTHORIZE T000006`
- `EXECUTE T000006`

## Persistent checkpoint

The canonical checkpoint contains exactly:

- `authorization.json`
- `proposal.tsv`
- `receipt.json`

Receipt SHA-256:

`febb3d981ab5eb295aab13100902189bd54ddb809cdef0f05af2c70f045af8d4`

Post-publication validation passed.

Replay state:

`FINAL_CHECKPOINT_EXISTS`

T000006 must not be replayed.

## Review integrity

Approved review-packet SHA-256 remains:

`d49d162191ba4737aeaecbf0934130a7a8816ad203504b2603a709ceec8a8b7a`

Execution did not modify the scientific review packet.

## Next gate

`DEFINE_NEXT_POST_PILOT_SCREENING_TRANCHE_USING_FROZEN_GENERIC_GUARD`
