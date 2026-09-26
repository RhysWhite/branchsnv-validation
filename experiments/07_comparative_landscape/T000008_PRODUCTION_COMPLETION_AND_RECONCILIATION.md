# Experiment 07 T000008 production completion and reconciliation

Status:

`T000008_PRODUCTION_COMPLETE_RECONCILED`

## Production transaction

T000008 completed successfully.

- batch: `B000001`
- positions: `87-186`
- events appended: **100**
- assigned event IDs: `E000000098-E000000197`
- pre-event count: **97**
- post-event count: **197**

Pre-ledger SHA-256:

`923de47d59a761a4992aab6ead9ba00390cacebbb4de6054ee601717f3c46e95`

Post-ledger SHA-256:

`0b802f7c80803193c1e3961dce47239839cf8ca4a0dbe757b39ac59d6a0d1dd3`

The original 97-event production ledger was independently verified as the
exact byte prefix of the completed 197-event ledger.

## Scientific outcomes

T000008:

- exclude: **93**
- retain for method assessment: **7**
- source escalation: **0**

Retained positions:

`87, 88, 90, 106, 130, 138, 170`

Derived baseline state after T000008:

- complete: **186**
- ready: **94,436**
- blocked metadata: **484**
- awaiting source escalation: **0**

Cumulative retained records after T000008:

**18**

These remain record-level candidates for later source-backed method
assessment. Retention does not itself establish final software-landscape
inclusion, analytical role, canonical publication, Wave-1 status, direct or
near-direct method status, or benchmark eligibility.

## Authorization

Authorization commit:

`bdd7cfb3b0e287c84ac90a4ac2cba1f5abfadfd7`

Authorization SHA-256:

`18cf3fb99c69b00ada6bfba1b38f21a3d7a93c66bdc5e23d77f5b0fabbcc6185`

Fixed transaction timestamp:

`2026-09-26T12:01:53Z`

Approved proposal SHA-256:

`da1eb2b9f6745f1b29e2c12e13a4774efe03760241687746221ee21943b1a434`

Human authority:

- `AUTHORIZE T000008`
- `EXECUTE T000008`

## Persistent checkpoint

The canonical checkpoint contains exactly:

- `authorization.json`
- `proposal.tsv`
- `receipt.json`

Receipt SHA-256:

`bc755ab5da207538329c10027ad4d99dfe00fea2aa1fb21cfe880fd0dd68801a`

Post-publication validation passed.

Replay state:

`FINAL_CHECKPOINT_EXISTS`

T000008 must not be replayed.

## Review integrity

Approved review-packet SHA-256 remains:

`9852bb143724aae7a17155bf9c033c003007a3c7b5d7b1b26c3e16a727e1c134`

Execution did not modify the scientific review packet.

## Generic tranche machinery

Generic guard v2 SHA-256:

`68cc5c501f89a389a842e0bc716e58801b56188a7621a887dcc2c349a8427ba5`

T000008 design SHA-256:

`9675e6cb835544fa0bd49f8f3b569c451b9940c3541ba2b270546722655514f3`

T000008 design-freeze SHA-256:

`a704e4decd268dd6140776bb28d0e5f641be6394518425ae7b651e0a327cb256`

## Next gate

`DEFINE_NEXT_POST_PILOT_SCREENING_TRANCHE_USING_FROZEN_GENERIC_GUARD_V2`
