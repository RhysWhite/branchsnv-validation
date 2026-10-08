# Pre-review triage future review queue v1 — generation authorization

Status: `FROZEN_ONE_USE_GENERATION_AUTHORIZATION_PRE_EXECUTION`

## Authorization

This freeze authorizes exactly one generation of the frozen future review
queue.

Authorization ID:

`PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_001`

## Frozen implementation binding

Implementation checksum identity:

`f7b3eca45cee5b49e2ee63e4a2ddc778dc1f46291346c0c855ea737e2bd0793d`

The generation authorization is valid only with that exact frozen
implementation.

## Authorized output

The execution may create exactly the frozen four-artifact queue:

- `priority_scored_queue.tsv`
- `residual_scored_queue.tsv`
- `unscored_manual_review_queue.tsv`
- `queue_manifest.json`

Expected lane sizes are:

- priority scored: 5,483
- residual scored: 6,422
- unscored manual review: 257
- total human-review universe: 12,162

## Scientific boundary

This authorization permits deterministic queue construction only.

It does not authorize:

- scientific inclusion;
- scientific exclusion;
- hard predictions;
- raw-score threshold selection;
- cross-lane priority invention;
- future-label use;
- blind-validation content access;
- production scientific-ledger mutation;
- network access.

## One-use boundary

The canonical queue output root must be absent before execution.

Once generation succeeds, the output root exists and the frozen
implementation refuses another execution.

## Exact generation confirmation

`GENERATE-FROZEN-FUTURE-REVIEW-QUEUE-V1`

## Next gate

`EXECUTE_ONCE_FROZEN_PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION`
