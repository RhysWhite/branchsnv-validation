# Pre-review triage operating-point design v1

## Status

`FROZEN_PRE_OPERATING_POINT_CURVE_IMPLEMENTATION`

## Purpose

This design defines how development out-of-fold scores may be used to study
review workload versus recall without selecting an operating point.

No threshold or review fraction is selected by this freeze.

## Why raw LinearSVC thresholds are not used

The frozen LinearSVC development scores come from nine separately fitted outer
models.

The score-scale diagnostic showed substantial variation in the positive-score
tail and in the behaviour of the conventional raw score boundary at zero.

Across batches:

- recall at raw score zero ranged from approximately 0.179 to 0.800;
- review fraction at raw score zero ranged from approximately 0.006 to 0.126;
- the review fraction required to capture every observed positive ranged from
  approximately 0.022 to 0.674.

A pooled numeric decision-function threshold is therefore not an authorized
v1 operating-point family.

Calibration would require additional fitted methodology and is outside this
design.

## Authorized development policy family

The only v1 development operating-point family is score ranking expressed as
review fraction.

Within each held-out batch, records are ranked by descending continuous
LinearSVC score. Exact score ties are resolved by ascending
`screening_entity_id`.

The ranking does not use the scientific label.

Every prefix from zero records through the full batch is evaluated.

For each prefix the implementation will calculate review fraction, recall and
precision.

Cross-batch summaries will include minimum, median and unweighted mean batch
recall.

No point on the curve is automatically selected.

## Routing interpretation

A future selected review fraction, if separately authorized, is a priority
review boundary rather than a scientific exclusion boundary.

Records below that boundary remain in a residual human-review queue.

Only human review may issue the terminal scientific screening disposition.

## No acceptance target yet

No acceptable recall target or workload target has been defined.

This design does not invent one.

Operating-point selection requires a later explicit criterion or workload
constraint and separate authorization after the descriptive development curve
has been frozen.

## Authority

This freeze does not authorize:

- fitting or refitting a model;
- fitting a score calibrator;
- selecting a raw score threshold;
- selecting a review fraction;
- future-universe scoring;
- blind-validation content use;
- automated scientific exclusion;
- production mutation.

## Next gate

`FREEZE_PRE_REVIEW_TRIAGE_OPERATING_POINT_CURVE_IMPLEMENTATION_V1_BEFORE_CURVE_GENERATION`
