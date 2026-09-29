# Pre-review triage evaluator v1 execution authorization

## Status

`FROZEN_ONE_TIME_DEVELOPMENT_EVALUATION_AUTHORIZATION_PRE_FIRST_FIT`

This freeze authorizes exactly one execution of the already frozen
pre-review-triage development evaluator.

## Bound implementation

The authorization is bound to:

- evaluator implementation freeze commit
  `38f2934b48bef39f62657cbb3360e2daf61e17e2`;
- the exact frozen evaluator implementation SHA256;
- the exact frozen modelling-environment state;
- the canonical 4,190-record normalized development-text artifact;
- execution ID `TRIAGE-DEV-EVAL-V1-001`;
- one canonical development-evaluation output directory.

## Authorized computation

The authorization permits vectorizer and classifier fitting only as required
by the frozen nested development-evaluation algorithm.

The frozen algorithm contains:

- three candidate model families;
- nine outer whole-batch folds;
- eight inner whole-batch folds per outer fold;
- one outer refit for each outer fold;
- a final nine-fold comparison of all three fixed candidate families.

This corresponds to 252 fit partitions.

## One-time execution

Execution must occur from the exact authorization commit.

The canonical output directory must not exist before execution.

After every pre-fit check passes, the evaluator creates the canonical output
directory and writes `execution_claim.json` before the first fit. Therefore a
failed or interrupted run leaves durable evidence and must not be silently
deleted or automatically retried.

A successful run must end with `execution_completion.json`.

## Authority boundaries

This authorization does not permit:

- hyperparameter selection;
- score-threshold selection;
- hard scientific screening decisions;
- future-universe scoring;
- blind-validation content use;
- production mutation.

The output remains development evidence only.

## Next gate

`EXECUTE_ONCE_FROZEN_PRE_REVIEW_TRIAGE_DEVELOPMENT_EVALUATION`
