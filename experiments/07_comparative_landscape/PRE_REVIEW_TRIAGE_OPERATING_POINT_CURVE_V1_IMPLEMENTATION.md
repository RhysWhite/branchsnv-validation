# Pre-review triage operating-point curve implementation v1

## Status

`FROZEN_PRE_CURVE_GENERATION`

This freeze records the deterministic implementation used to generate
development review-fraction versus recall curves.

No operating point is selected.

## Input

The implementation consumes only the frozen 4,190-row development
out-of-fold LinearSVC score artifact.

It does not score any future records and does not access blind-validation
content.

## Ranking

Records are ranked independently within each historical development batch by:

1. descending continuous LinearSVC score;
2. ascending `screening_entity_id` for exact score ties.

Scientific labels are not used to construct the ranking.

## Per-batch curves

For each batch, every prefix from zero through the complete batch is
evaluated.

The output records:

- reviewed count;
- exact review-fraction numerator and denominator;
- decimal review fraction;
- number of retained positives reviewed;
- recall;
- precision.

Precision is undefined at zero reviewed records and is serialized as an empty
TSV value.

## Cross-batch curve

Candidate review fractions are the exact mathematical union of every `k/n`
fraction appearing in the nine batch-prefix curves.

Python `Fraction` arithmetic is used for the candidate grid.

For candidate fraction `q`, a batch of size `n` reviews exactly
`ceil(q*n)` records, computed using integer arithmetic rather than a
floating-point approximation.

The cross-batch output reports minimum, median and unweighted mean batch
recall, pooled development recall, unweighted mean batch precision, total
reviewed count and pooled review fraction.

## Selection boundary

Curve generation is descriptive only.

It does not choose:

- a raw LinearSVC threshold;
- a review fraction;
- an acceptable recall target;
- a workload target.

Records are not assigned terminal scientific dispositions.

## Authority

This implementation contains no model fitting, prediction, calibration,
future scoring, blind-validation use or production mutation.

## Next gate

`GENERATE_AND_FREEZE_PRE_REVIEW_TRIAGE_OPERATING_POINT_CURVES_V1`
