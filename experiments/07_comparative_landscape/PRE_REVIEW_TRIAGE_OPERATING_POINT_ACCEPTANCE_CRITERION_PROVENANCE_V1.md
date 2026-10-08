# Pre-review triage operating-point acceptance-criterion provenance v1

## Status

`FROZEN_NO_UPSTREAM_ACCEPTANCE_CRITERION_PRE_NEW_CRITERION`

## Finding

No model-acceptance criterion was pre-specified upstream.

The frozen development, retrieval and model-candidate contracts explicitly
record that no acceptable recall threshold had been defined and that threshold
optimization was not permitted.

No workload target, review fraction, raw score threshold or operating point was
pre-specified.

## The 60-positive rule

The earlier requirement for at least 60 retained-positive blind-validation
records is a validation-sample sufficiency rule.

If the stage-1 blind sample contains fewer than 60 retained positives, the
frozen design requires an additional pre-specified probability sample before
final recall interpretation.

It is not:

- a model-acceptance threshold;
- a recall target;
- a score threshold;
- a review-fraction target;
- an operating point.

The frozen development design explicitly records that this sampling rule was
not adopted as a model-acceptance rule.

## Consequence

Any acceptance criterion defined after this freeze is a new prospectively
declared criterion.

It must be justified from the intended operational/scientific use or an
external workload constraint.

It must be frozen before the already observed development curve is searched
for a qualifying operating point.

The criterion must not be reverse-engineered from a preferred point on that
curve.

## Current boundary

No acceptable recall target, workload target, review fraction, score threshold
or operating point is selected by this provenance freeze.

Blind-validation content has not been scientifically inspected or used.

## Next gate

`DEFINE_AND_FREEZE_NEW_ACCEPTANCE_CRITERION_FROM_INTENDED_USE_OR_EXTERNAL_WORKLOAD_CONSTRAINT_BEFORE_ANY_CURVE_BASED_OPERATING_POINT_SELECTION`
