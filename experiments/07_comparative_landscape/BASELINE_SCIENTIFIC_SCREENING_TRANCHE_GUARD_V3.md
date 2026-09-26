# Experiment 07 baseline scientific-screening tranche guard v3

Status:

`FROZEN_PRE_T000011_REVIEW`

## Purpose

Guard v3 generalizes the proven B000001 tranche machinery across
the frozen baseline-screening batch universe.

Frozen v2 remains unchanged:

`68cc5c501f89a389a842e0bc716e58801b56188a7621a887dcc2c349a8427ba5`

v3 SHA-256:

`469273c1d2ed9f5ca7ca01efb636b5a045b7e785de6812814780f1c3d73a5aec`

## Cross-batch changes

v3 derives:

- batch identity from the frozen transaction design;
- complete batch scope from frozen membership;
- review-packet path from batch identity;
- review-packet row count from actual batch membership;
- authorization status from batch and transaction identity.

The event appender itself is unchanged.

## Regression boundary

Validated explicitly:

- B000002 = 500 records;
- B000002 global indices = 501-1000;
- B000190 = 122 records;
- blank B000190 packet = 122 rows.

Thus v3 is not dependent on 500-row batches.

## Preserved controls

The existing controls remain:

- exact target-identity reconstruction;
- immutable baseline metadata;
- target-only proposal extraction;
- separate scientific-decision freeze;
- separate tracked one-use authorization;
- fixed transaction timestamp;
- projected post-ledger SHA;
- atomic append;
- three-file persistent checkpoint;
- recovery state detection;
- replay prevention;
- no partial transaction authority.

No production event is created by this implementation freeze.

## Event-appender regression maintenance

The frozen event-appender implementation itself is unchanged.

Its historical integration regression originally assumed that the live
production event ledger would remain permanently at the zero-event genesis
state. That assumption became stale after authorized production screening.

The regression now preserves the intended invariants without pinning live
production to a historical event count:

- the current production ledger is validated read-only;
- the zero-event genesis SHA remains independently verified;
- mutation tests reconstruct a temporary genesis ledger from the immutable
  ledger header;
- no mutation test runs against the live production ledger;
- the live production ledger must remain byte-identical throughout the test.

This is test maintenance only and does not alter event-appender semantics.

## Next gate

`VALIDATE_AND_FREEZE_B000002_T000011_DESIGN`
