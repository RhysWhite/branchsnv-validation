# Pre-review triage future human-review protocol v1 — implementation Amendment 002

Status: `FROZEN_IMPLEMENTATION_AMENDMENT_002`

## Purpose

This amendment resolves the remaining lifecycle treatment of mutable
human-review state.

No frozen implementation, design, test, Amendment 001, or scientific-event
semantic is modified.

## Amendment 001 boundary-state issue

Implementation Amendment 001 correctly established that downstream review
artifacts and valid append-only ledger advancement do not invalidate the
implementation freeze.

Its validator nevertheless continued checking the exact rollback state while
`HEAD` was the Amendment 001 commit.

That state included:

- `priority_001` byte-identical to its blank source;
- 0 completed and 500 blank review rows;
- the Amendment 001 event count;
- the Amendment 001 event-ledger SHA;
- exactly one materialized review file.

Those facts are Amendment 001 boundary evidence.

They are not invariants of subsequent human review.

## Frozen test-suite lifecycle

The frozen normal and hostile suites contain assertions that the real
`PLANNED_REVIEW_ROOT` does not exist.

Those assertions were appropriate before real human review was materialized.

They remain valid evidence supporting the implementation freeze.

They are not live operational assertions after review begins.

The frozen test files remain byte-identical and are not rewritten.

## Operational validation during review

Once real review begins, current integrity is established through the frozen
implementation itself:

- validate immutable upstream contracts;
- validate the frozen canonical workspace;
- validate the current append-only event ledger semantically;
- validate each reviewed packet against its frozen source identity and order;
- validate completed scientific rows using explicit operator provenance.

Current review packets are allowed to contain valid human scientific review
content.

The implementation freeze does not require them to remain blank.

The mutable ledger is not required to retain the Amendment 001 event count or
SHA, provided it remains a valid append-only ledger under the frozen appender
contract.

## Review retry

The first ten previously approved dispositions may now be retried.

The validation invocation must explicitly supply:

- a non-empty human review `operator_id`;
- `operator_type = human_with_assistance`.

The expected post-retry state is:

- completed review rows: 10;
- blank review rows: 490;
- packet complete: no;
- packet approved: no;
- production proposal: none;
- live production authorization: none;
- production-ledger mutation: none.

## Scientific effect

This amendment itself makes no scientific decision.

## Next gate

`RETRY_PRIORITY_001_ROWS_001_010_WITH_EXPLICIT_OPERATOR_PROVENANCE`
