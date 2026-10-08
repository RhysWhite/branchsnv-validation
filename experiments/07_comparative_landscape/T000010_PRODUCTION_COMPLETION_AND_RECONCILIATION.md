# Experiment 07 T000010 production completion and B000001 reconciliation

Status:

`T000010_PRODUCTION_COMPLETE_RECONCILED_B000001_COMPLETE`

## Production transaction

T000010 completed successfully.

- batch: `B000001`
- positions: `387-500`
- events appended: **114**
- assigned event IDs: `E000000398-E000000511`
- pre-event count: **397**
- post-event count: **511**

Pre-ledger SHA-256:

`69bb54da69fc187c26aef4e1548073d09f1e8b7594b82005737088f42deeaa59`

Post-ledger SHA-256:

`080b60b63c46524fe3f97d7db37ca56aba255e8633170b8f709f648ab11cd413`

The original 397-event production ledger was independently verified as
the exact byte prefix of the completed 511-event ledger.

## T000010 scientific outcomes

- exclude: **96**
- retain for method assessment: **18**
- source escalation: **0**

Derived baseline state after T000010:

- complete: **500**
- ready: **94,122**
- blocked metadata: **484**
- awaiting source escalation: **0**

Cumulative retained records after T000010:

**91**

These remain record-level candidates for later source-backed
method assessment.

Retention does not itself establish final software-landscape inclusion,
canonical-publication status, analytical role, direct/near-direct status,
Wave-1 status, or benchmark eligibility.

## B000001 completion

B000001 is now complete:

- total positions: **500**
- terminal positions: **500**
- remaining positions: **0**
- outstanding source escalations: **0**

All positions `1-500` have completed record-level scientific screening.

## Authorization

Authorization commit:

`37f421975aa6c1a4abec78ca4c39409a894c675b`

Authorization SHA-256:

`62d651c51c201d719d058cdbd82514f7b3a55005db6ec69ef2a202f7467df4f8`

Fixed transaction timestamp:

`2026-09-26T20:50:52Z`

Approved proposal SHA-256:

`3396c649ecfa309f9f022cb321f89bbed503d877e70361877fb26a38fc589d2c`

Human authority:

- `AUTHORIZE T000010`
- `EXECUTE T000010`

## Persistent checkpoint

The canonical checkpoint contains exactly:

- `authorization.json`
- `proposal.tsv`
- `receipt.json`

Receipt SHA-256:

`1a132598a567e50847263af67265abdd0937143bdbb8df89b55778ad888dd465`

Post-publication validation passed.

Replay state:

`FINAL_CHECKPOINT_EXISTS`

T000010 must not be replayed.

## Review integrity

Approved review-packet SHA-256 remains:

`f3658a809a6adf8550db28f615a9412649898c3cd0a1dafbe6d04b28367db50d`

Execution did not modify the scientific review packet.

## Generic tranche machinery

Generic guard v2 SHA-256:

`68cc5c501f89a389a842e0bc716e58801b56188a7621a887dcc2c349a8427ba5`

T000010 design SHA-256:

`a38755fdbd4819f20833d1f27dace76f09ae84acd48732f3e20b4788d78d7809`

T000010 design-freeze SHA-256:

`c01f5244117767f72d7c89d700e80158445dc21bfe13fde057ec74cf524f6ba3`

## Next gate

`DEFINE_NEXT_BASELINE_SCREENING_BATCH_AFTER_B000001`
