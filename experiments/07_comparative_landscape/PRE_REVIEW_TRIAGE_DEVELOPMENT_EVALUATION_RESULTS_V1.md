# Pre-review triage development evaluation results v1

## Status

`FROZEN_DEVELOPMENT_EVALUATION_RESULTS_V1`

This freeze records the exact result artifacts from the one-time authorized
development evaluation `TRIAGE-DEV-EVAL-V1-001`.

The execution has been consumed and must not be rerun under the existing
authorization.

## Development population

The development evaluation contains 4,190 text-bearing records:

- 4,022 `exclude`;
- 168 `retain_for_method_assessment`.

Evaluation used nine historical development batches and whole-batch
cross-validation.

## Frozen candidate-family result

- logistic_regression_balanced_l2_v1: mean AP 0.688042656381; minimum AP 0.443265546714; median AP 0.710982756582
- linear_svc_balanced_l2_v1: mean AP 0.716509345031; minimum AP 0.528614328614; median AP 0.710118814467
- complement_nb_v1: mean AP 0.309795727534; minimum AP 0.103109625917; median AP 0.313492063492

The selected development family is:

`linear_svc_balanced_l2_v1`

Selection follows the previously frozen rule: higher unweighted macro mean
batch average precision, then higher minimum AP, then higher median AP, then
the frozen candidate order.

## Outer evaluation

- B000001: linear_svc_balanced_l2_v1; outer AP 0.806797964465
- B000002: linear_svc_balanced_l2_v1; outer AP 0.948051948052
- B000003: linear_svc_balanced_l2_v1; outer AP 0.528614328614
- B000004: linear_svc_balanced_l2_v1; outer AP 0.710118814467
- B000005: linear_svc_balanced_l2_v1; outer AP 0.826666666667
- B000006: linear_svc_balanced_l2_v1; outer AP 0.685424590889
- B000007: linear_svc_balanced_l2_v1; outer AP 0.757575757576
- B000008: linear_svc_balanced_l2_v1; outer AP 0.619528619529
- B000009: linear_svc_balanced_l2_v1; outer AP 0.565805415022

All nine nested outer folds independently selected the same LinearSVC family.

## Independent result audit

The saved result artifacts were independently audited without model fitting.

The audit reproduced:

- all nine nested inner candidate selections;
- the selected-candidate identity attached to all 4,190 outer-fold scores;
- all fixed-family leave-one-batch-out aggregates;
- the final family selection;
- all seven result-artifact SHA256 values.

## Interpretation boundary

These results establish the selected model family for subsequent development
work.

They do not establish a future-universe operating threshold or demonstrate
future-universe performance.

No threshold was selected and no hard screening classification was generated.

No future records were scored.

Blind validation content was not scientifically inspected or used.

No scientific screening decisions or production mutations occurred.

## Immutability

The seven development-evaluation result artifacts are frozen byte-for-byte.

They must not be regenerated, altered or silently replaced.

## Next gate

`FREEZE_PRE_REVIEW_TRIAGE_OPERATING_POINT_DESIGN_V1_BEFORE_ANY_THRESHOLD_SELECTION_OR_FUTURE_SCORING`
