# Pre-review triage future scoring v1 — Design Amendment 001

Status: `FROZEN_PRE_IMPLEMENTATION_AMENDMENT`

## Reason

The original future-scoring design incorrectly referred to a frozen
development threshold and a pre-existing fitted development model.

The frozen development evaluation selected the candidate family:

`linear_svc_balanced_l2_v1`

but selected no raw-score threshold, generated no hard predictions, and did
not create a serialized final deployment fit.

## Corrected future-scoring semantics

Future scoring therefore consists of two inseparable operations under a later
explicit execution authorization:

1. fit the already-selected `linear_svc_balanced_l2_v1` family, using the
   frozen evaluator preprocessing and constructor, on all 4,190 frozen
   development normalized-text records; and
2. use that fitted state to emit continuous scores for exactly 11,905 future
   normalized-text records.

The final fit is **not** new model development. Candidate-family selection,
hyperparameter tuning, feature selection, threshold selection and calibration
remain prohibited.

## Threshold and decision boundary

No development threshold exists.

Future scoring may not emit:

- hard predictions;
- threshold-based decisions;
- calibrated probabilities;
- selected review fractions;
- an operating point.

Only continuous scores with the frozen development score orientation are
permitted.

## Leakage boundary

Future texts may be transformed/scored but may not enter model fitting.

Future or blind-validation labels may not be read, joined, inspected or used
during fitting or scoring.

The future score artifact must be frozen before any later unblinding.

## Execution boundary

This amendment performs no fitting and no future scoring.

A separately frozen implementation and hostile-test suite are required before
a separate execution authorization.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_AGAINST_DESIGN_PLUS_AMENDMENT_001_BEFORE_SEPARATE_EXECUTION_AUTHORIZATION`
