# Pre-review triage future review queue v1 — design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design converts the already-frozen future continuous scores and the
already-frozen development operating point into deterministic review lanes.

It does not make scientific inclusion or exclusion decisions.

## Controlling operating point

The frozen development operating point is the exact review fraction:

`35/76 = 0.46052631578947367`

The frozen curve implementation applies an exact ceiling rule.

For 11,905 scoreable future records this gives:

`ceil(11905 × 35 / 76) = 5,483`

There is no raw-score threshold.

## Review lanes

### Priority scored queue

5,483 records.

Membership is the first 5,483 records after sorting by:

1. continuous score descending;
2. `screening_entity_id` ascending.

### Residual scored queue

6,422 records.

These are all remaining scoreable records after the priority prefix.

They remain in a human-review queue; they are not automatically excluded.

Their deterministic order remains the same frozen score ranking.

### Unscored manual-review queue

257 records.

These are exactly the records with:

`coverage_status = no_normalized_text`

They have no continuous model score and therefore cannot be placed into the
score-ranked prefix.

Because automatic scientific exclusion is not authorized, they remain in a
separate human-review lane.

Their deterministic within-lane order is ascending
`retrieval_record_index`.

## Complete human-review universe

The three lanes close exactly:

- 5,483 priority scored;
- 6,422 residual scored;
- 257 unscored manual review;
- 12,162 total.

No future record is automatically removed from human review by this design.

## Cross-lane ordering

No relative priority is assigned between the unscored manual-review lane and
either scored lane.

The existing frozen repository does not define such a relationship, so this
design does not invent one.

## Scientific boundary

This design performs no:

- automatic inclusion;
- automatic exclusion;
- hard prediction;
- raw-score thresholding;
- future-label use;
- blind-validation access;
- production-ledger mutation.

## Planned outputs

A later implementation may generate exactly:

- `priority_scored_queue.tsv`
- `residual_scored_queue.tsv`
- `unscored_manual_review_queue.tsv`
- `queue_manifest.json`

Generation is not authorized by this design freeze.

## Next gate

`FREEZE_PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_IMPLEMENTATION_BEFORE_GENERATION`
