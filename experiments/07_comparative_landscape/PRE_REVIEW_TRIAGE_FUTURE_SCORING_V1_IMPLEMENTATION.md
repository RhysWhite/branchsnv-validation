# Pre-review triage future scoring v1 — implementation

Status: `FROZEN_IMPLEMENTATION_PRE_AUTHORIZATION`

## Scope

The future-scoring implementation is frozen but has not been executed.

No final deployment fit on the 4,190-record development set and no scoring
of the 11,905 future normalized-text records occurred during implementation
validation.

## Runtime

Execution is fail-closed to the frozen triage environment:

- Python 3.11
- NumPy 1.26.4
- SciPy 1.12.0
- scikit-learn 1.9.0
- joblib 1.6.0
- threadpoolctl 3.7.0
- interpreter:
  `/home/rwhite/.conda/envs/branchsnv-triage-v1/bin/python`

## Model

The only permitted candidate family is:

`linear_svc_balanced_l2_v1`

The TF-IDF and LinearSVC constructor ASTs are structurally identical to the
frozen development evaluator.

The TF-IDF contract includes `dtype=np.float64`.

## Final deployment fit

After a separate one-use authorization, exactly one final fit may use:

- 4,190 frozen development normalized-text records;
- 168 positives;
- 4,022 negatives.

Future text, future labels and blind-validation content may not enter fitting.

## Future scoring

Exactly 11,905 future normalized-text records are scoreable.

The other 257 reconciliation rows remain explicit `no_normalized_text`
coverage records and receive no score.

Only raw continuous LinearSVC decision-function scores may be emitted.

There is no threshold, hard classification, selected review fraction or
probability calibration.

## Validation

The implementation passed:

- 10 unit tests;
- 11 hostile tests;
- 21 tests total;
- exact frozen-runtime validation;
- exact frozen-evaluator constructor equivalence.

No real deployment fit or future scoring occurred.

## Next gate

`FREEZE_ONE_USE_PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_EXECUTION_AUTHORIZATION`
