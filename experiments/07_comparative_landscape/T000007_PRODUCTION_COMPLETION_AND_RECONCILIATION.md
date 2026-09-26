# Experiment 07 T000007 production completion and reconciliation

Status:

`T000007_PRODUCTION_COMPLETE_RECONCILED`

## Production transaction

T000007 completed successfully.

- batch: `B000001`
- positions: `37-86`
- events appended: **50**
- assigned event IDs: `E000000048-E000000097`
- pre-event count: **47**
- post-event count: **97**

Pre-ledger SHA-256:

`dd83022eff2d2b069b80a6db495c90991e823fad03ece61010484e6fa839525b`

Post-ledger SHA-256:

`923de47d59a761a4992aab6ead9ba00390cacebbb4de6054ee601717f3c46e95`

The original 47-event production ledger was independently verified as the
exact byte prefix of the completed 97-event ledger.

## Scientific outcomes

T000007:

- exclude: **48**
- retain for method assessment: **2**
- source escalation: **0**

Retained T000007 positions:

`65, 80`

Derived baseline state after T000007:

- complete: **86**
- ready: **94,536**
- blocked metadata: **484**
- awaiting source escalation: **0**

Cumulative retained records after T000007:

**11**

These remain record-level candidates for later source-backed method
assessment. Retention does not itself establish final software-landscape
inclusion, analytical role, canonical publication, Wave-1 status, direct or
near-direct method status, or benchmark eligibility.

## Authorization

Authorization commit:

`28e3702e9bba041f5e533938f8020225f05cdab3`

Authorization SHA-256:

`6b68afda909d999c5f43ab33367b19f375c67dc732658490ee69946c501cdbe8`

Fixed transaction timestamp:

`2026-09-26T11:04:56Z`

Approved proposal SHA-256:

`5d5e21dfc6d51e0d92b35ee1dd7af8acdfaa0e69a5eae03e55b6226b0fd7c307`

Human authority:

- `AUTHORIZE T000007`
- `EXECUTE T000007`

## Persistent checkpoint

The canonical checkpoint contains exactly:

- `authorization.json`
- `proposal.tsv`
- `receipt.json`

Receipt SHA-256:

`d2a356c81a2f0feb34c7b8858c3ed3e3970caaeaf39897e9daaad48782c6430d`

Post-publication validation passed.

Replay state:

`FINAL_CHECKPOINT_EXISTS`

T000007 must not be replayed.

## Review integrity

Approved review-packet SHA-256 remains:

`cade5407e9a75bd45e282f7b4ca2e2b1c53973128be5aed76730ec85c344f7ab`

Execution did not modify the scientific review packet.

## Generic tranche machinery

Generic guard v2 SHA-256:

`68cc5c501f89a389a842e0bc716e58801b56188a7621a887dcc2c349a8427ba5`

T000007 design SHA-256:

`33359f4caa6746c3d52a0d79047e91927790ae5a6973ce8552b76bc28d918164`

T000007 design-freeze SHA-256:

`499023aff86d10058cb5035fe172b509cea6772e74064cefc924d190b21e6145`

## Next gate

`DEFINE_NEXT_POST_PILOT_SCREENING_TRANCHE_USING_FROZEN_GENERIC_GUARD_V2`
