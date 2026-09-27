# Experiment 07 baseline scientific-screening campaign orchestration v4 design

Status:

`FROZEN_PRE_IMPLEMENTATION`

## Purpose

The single-batch production workflow has now been validated through
B000001-B000004.

The remaining baseline screen will therefore use a campaign-level
orchestration layer to reduce repetitive human gating without weakening the
existing scientific or production controls.

## What changes

A campaign groups several adjacent frozen screening batches under one human
review/authorization/execution cycle.

Initial campaign width:

- **5 batches**
- **500 records per full batch**
- **2,500 records per full campaign**

The first campaign is:

`C000001`

covering:

- B000005 / T000014
- B000006 / T000015
- B000007 / T000016
- B000008 / T000017
- B000009 / T000018

Global active indices:

`2001-4500`

## What does not change

There is still **one production transaction per batch**.

The event appender remains prohibited from accepting a cross-batch
transaction.

Every transaction retains:

- an independent scientific proposal
- a one-use authorization
- a deterministic event-ID range
- a strict ledger-prefix extension
- a three-file persistent checkpoint
- independent post-publication validation
- an independent completion/reconciliation freeze
- a replay barrier

## Human gates

The repetitive per-batch human interaction is replaced by three explicit
campaign-level gates:

`APPROVE C000001 REVIEW`

`AUTHORIZE C000001`

`EXECUTE C000001`

Scientific review approval and live production authorization remain separate.

## Execution semantics

Execution remains sequential.

The campaign controller must process one batch at a time in ascending order.

For each batch it must:

1. construct the exact single-batch transaction context;
2. generate a v3-compatible one-use authorization;
3. commit that authorization as current HEAD;
4. reconstruct and validate the dry run;
5. publish only that batch;
6. validate the persistent checkpoint;
7. reconcile the post-ledger state;
8. freeze that transaction's completion;
9. only then advance to the next batch.

The next transaction's expected pre-ledger SHA must be the independently
validated post-ledger SHA of the preceding transaction.

## Failure behaviour

Campaign execution is fail-closed.

If any transaction fails, execution stops immediately.

Already completed transactions remain final and replay-protected.

No later transaction may publish until the failure/recovery state has been
resolved.

There is no rollback of a successfully appended transaction.

## Campaign scaling

Campaign width is initially fixed at five batches.

There is no automatic increase to ten batches.

Any later width increase requires a separately frozen amendment after the
initial campaign implementation and production behaviour have been validated.

## Final partial batch

B000190 contains 122 records and remains explicitly supported.

## Authority

This design creates:

- no scientific decisions
- no review-packet mutations
- no authorization
- no production event
- no checkpoint

## Next gate

`IMPLEMENT_BASELINE_SCREENING_CAMPAIGN_ORCHESTRATION_V4_WITHOUT_PRODUCTION_MUTATION`
