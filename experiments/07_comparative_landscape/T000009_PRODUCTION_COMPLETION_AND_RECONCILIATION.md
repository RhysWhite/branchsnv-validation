# Experiment 07 T000009 production completion and reconciliation

Status:

`T000009_PRODUCTION_COMPLETE_RECONCILED`

## Production transaction

T000009 completed successfully.

- batch: `B000001`
- positions: `187-386`
- events appended: **200**
- assigned event IDs: `E000000198-E000000397`
- pre-event count: **197**
- post-event count: **397**

Pre-ledger SHA-256:

`0b802f7c80803193c1e3961dce47239839cf8ca4a0dbe757b39ac59d6a0d1dd3`

Post-ledger SHA-256:

`69bb54da69fc187c26aef4e1548073d09f1e8b7594b82005737088f42deeaa59`

The original 197-event production ledger was independently verified as
the exact byte prefix of the completed 397-event ledger.

## Scientific outcomes

T000009:

- exclude: **145**
- retain for method assessment: **55**
- source escalation: **0**

Derived baseline state after T000009:

- complete: **386**
- ready: **94,236**
- blocked metadata: **484**
- awaiting source escalation: **0**

Cumulative retained records after T000009:

**73**

These remain record-level candidates for later source-backed method
assessment. Retention does not itself establish final software-landscape
inclusion, analytical role, canonical publication, Wave-1 status,
direct/near-direct status, or benchmark eligibility.

## Authorization

Authorization commit:

`83f162d601d709dd5621a067ae56433778fb7625`

Authorization SHA-256:

`045a21e0a1c44113d070907d3bb3d6152e16b672ea744ed82ea465fe585d256a`

Fixed transaction timestamp:

`2026-09-26T20:14:23Z`

Approved proposal SHA-256:

`1e929313c5cc1c7444c3aabe5ffc3152ac838e87dd51f2b66479148fd241461b`

Human authority:

- `AUTHORIZE T000009`
- `EXECUTE T000009`

## Persistent checkpoint

The canonical checkpoint contains exactly:

- `authorization.json`
- `proposal.tsv`
- `receipt.json`

Receipt SHA-256:

`53d67df01f244a87406cd7da9fa1329973036c7acf2f08e1ced93583d55df942`

Post-publication validation passed.

Replay state:

`FINAL_CHECKPOINT_EXISTS`

T000009 must not be replayed.

## Review integrity

Approved review-packet SHA-256 remains:

`75650de1ca004651c363b1b72eead99fbb4e6674816b181964a666108bc4434a`

Execution did not modify the scientific review packet.

## Generic tranche machinery

Generic guard v2 SHA-256:

`68cc5c501f89a389a842e0bc716e58801b56188a7621a887dcc2c349a8427ba5`

T000009 design SHA-256:

`1fd799189a1c8981da3b9952d980458073c7ee3c2912865506ae06dcdbc6bf29`

T000009 design-freeze SHA-256:

`da76ea6822a46ed8123b24a36bef1d9110baf974b15227f028ff717b6dcaf8f8`

## Next gate

`DEFINE_FINAL_B000001_SCREENING_TRANCHE_USING_FROZEN_GENERIC_GUARD_V2`
