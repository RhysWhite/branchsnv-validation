# Pre-review triage future review queue v1 — results freeze

Status: `FROZEN_FUTURE_REVIEW_QUEUE_V1_RESULTS`

## Purpose

This freeze records the completed deterministic generation of the
pre-review future review queue.

It freezes the exact generated queue artifacts and their provenance.
It does not make scientific inclusion or exclusion decisions.

## Production result

The complete 12,162-record human-review universe is represented by:

- 5,483 priority scored records;
- 6,422 residual scored records;
- 257 unscored manual-review records.

The two scored lanes together contain all 11,905 scoreable records.

The priority lane is the exact prefix defined by:

`ceil(11905 × 35 / 76) = 5,483`

after sorting by continuous score descending and then
`screening_entity_id` ascending.

The unscored lane is ordered by ascending `retrieval_record_index`.

## Generation provenance

Generation authorization:

`PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_002`

The one-use authorization is consumed. Rerun is not authorized.

The active queue builder is the Amendment 001 implementation.

## Validation

The completed queue has been independently checked for:

- exact source-identity hashes;
- exact generated-artifact hashes;
- expected lane dimensions;
- mutually exclusive lanes;
- complete coverage of the 12,162-record review universe;
- exact scored/unscored partitioning;
- byte-for-byte score preservation;
- deterministic scored ordering;
- exact 35/76 prefix selection;
- deterministic unscored ordering;
- agreement of manual-review metadata with the frozen coverage source.

## Scientific boundary

This freeze grants no authority for:

- automatic scientific inclusion;
- automatic scientific exclusion;
- hard prediction;
- raw-score threshold selection;
- cross-lane priority selection;
- future-label use;
- blind-validation access;
- unblinding;
- production-ledger mutation;
- scientific screening decisions.

All records remain in a human-review lane.

## Next gate

No downstream gate is authorized by this freeze.

The repository-defined post-queue human-review gate must be resolved
separately before further execution.
