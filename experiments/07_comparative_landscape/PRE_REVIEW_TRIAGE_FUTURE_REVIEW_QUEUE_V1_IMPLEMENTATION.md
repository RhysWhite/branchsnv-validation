# Pre-review triage future review queue v1 — implementation

Status: `FROZEN_IMPLEMENTATION_PRE_GENERATION_AUTHORIZATION`

## Purpose

This implementation deterministically converts the frozen future-scoring
result set into the three review lanes defined by the frozen queue design.

It has not generated the canonical review queue.

## Score-ranked population

The implementation reads exactly 11,905 frozen continuous-score records.

Records are ranked by:

1. continuous score descending;
2. `screening_entity_id` ascending.

The frozen 35/76 operating-point fraction is converted to a prefix count using
the frozen exact ceiling rule:

`ceil(11905 × 35 / 76) = 5483`

This produces:

- 5,483 priority scored records;
- 6,422 residual scored records.

No raw-score threshold is calculated or selected.

## Unscored population

Exactly 257 records with `coverage_status = no_normalized_text` form a
separate manual-review lane.

They are ordered deterministically by ascending `retrieval_record_index`.

They are not merged into an invented cross-lane score order.

## Human-review universe

The lanes are exhaustive and mutually exclusive:

- 5,483 priority scored;
- 6,422 residual scored;
- 257 unscored manual review;
- 12,162 total.

No record is automatically scientifically included or excluded.

## Planned canonical artifacts

Generation may later create exactly:

- `priority_scored_queue.tsv`
- `residual_scored_queue.tsv`
- `unscored_manual_review_queue.tsv`
- `queue_manifest.json`

Generation is atomic and fail-closed if the canonical output root already
exists.

## Authorization boundary

The production generation entry point requires a separately frozen one-use
authorization and the exact confirmation:

`GENERATE-FROZEN-FUTURE-REVIEW-QUEUE-V1`

No such authorization exists at this implementation freeze.

## Scientific boundary

The implementation does not:

- access future labels;
- access blind-validation content;
- generate hard predictions;
- select a raw-score threshold;
- make scientific inclusion or exclusion decisions;
- mutate the production scientific ledger.

## Validation

The implementation passed:

- 10 unit tests;
- 10 hostile tests;
- 20 tests total;
- exact frozen-input identity validation;
- deterministic real-input queue-membership derivation without writing
  production output.

## Next gate

`FREEZE_ONE_USE_PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_AUTHORIZATION`
