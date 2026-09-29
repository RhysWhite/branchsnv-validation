# Pre-review triage evaluator v1 implementation

## Status

`FROZEN_IMPLEMENTATION_PRE_DEVELOPMENT_EVALUATION`

This freeze records the exact evaluator implementation immediately before the
first vectorizer or classifier fit.

No fitting has occurred.

## Development population

The evaluator uses the frozen 4,190-record text-bearing development lane:

- 4,022 `exclude`;
- 168 `retain_for_method_assessment`.

Only normalized title and abstract text are predictive inputs.

Historical development batch is retained only as a validation grouping
variable and is not supplied to the model.

## Candidate families

The candidate order is fixed:

1. TF-IDF + balanced L2 logistic regression;
2. TF-IDF + balanced linear SVC;
3. TF-IDF + ComplementNB.

There is no hyperparameter grid, model-family search beyond these three frozen
candidates, character-ngram search, embedding model or transformer model.

## Nested whole-batch evaluation

Nine outer leave-one-whole-batch-out folds are encoded.

Within each outer training partition, the three frozen candidates are compared
over eight inner leave-one-whole-batch-out folds.

The TF-IDF vectorizer is fitted only on the training partition of each split.
The classifier is fitted only on that same training partition.

Candidate selection uses:

1. higher unweighted mean held-out-batch average precision;
2. higher minimum held-out-batch average precision;
3. higher median held-out-batch average precision;
4. frozen candidate order.

The implementation compares the raw Python floating-point values directly.
There is no metric rounding and no numerical tie tolerance.

The inner-selected candidate is then refitted on all eight outer-training
batches and generates continuous scores for the untouched outer batch.

A separately encoded nine-fold comparison of each fixed candidate family is
used for final development-family selection.

No score threshold or hard classification is selected.

## Score orientation

For logistic regression and ComplementNB, the positive probability is selected
by finding class `1` in `classes_`; column position is not assumed.

For LinearSVC, the implementation requires `classes_ == [0, 1]` before using
the decision function.

Both behaviours are covered by hostile tests.

## Fit surface

All `.fit()` and `.fit_transform()` calls are isolated in
`fit_and_score_partition()`.

That function itself begins by requiring the separately frozen execution
authorization. Therefore direct invocation cannot bypass the pre-fit
authorization gate.

The high-level development evaluator is independently authorization-gated.

## Future one-time execution

The later authorization must be a committed, clean Git-tracked artifact bound
to:

- this evaluator implementation hash;
- the frozen environment-state design;
- the canonical normalized-text hash;
- the evaluator implementation freeze commit;
- execution ID `TRIAGE-DEV-EVAL-V1-001`;
- one canonical development output directory.

The canonical output directory must not already exist.

After all pre-fit checks succeed, execution creates that directory and writes
`execution_claim.json` before the first fit. If the subsequent evaluation
fails, the claim remains and automatic rerun is therefore fail-closed.

`execution_completion.json` is written only after all planned evaluation
outputs have completed.

## Frozen execution outputs

A later authorized development run may create only the development-evaluation
artifact set:

- `execution_claim.json`;
- `inner_metrics.tsv`;
- `outer_metrics.tsv`;
- `outer_scores.tsv`;
- `final_candidate_batch_metrics.tsv`;
- `summary.json`;
- `execution_completion.json`.

These are development metrics and continuous scores only.

They do not constitute scientific screening decisions and contain no selected
score threshold.

## Validation

Twenty-one no-fit tests pass, including:

- exact candidate constructors;
- exact development population;
- exact whole-batch split geometry;
- deterministic candidate tie-breaking;
- train/test identity separation;
- two-class fold requirements;
- positive-score orientation;
- rejection of unknown or incomplete candidate sets;
- direct-fit authorization guarding;
- fail-closed unauthorized CLI execution;
- refusal to overwrite an existing execution directory.

No vectorizer or classifier fit was performed while validating this
implementation.

## Authority

This freeze does not authorize development evaluation execution or the first
fit.

It does not authorize hyperparameter selection, threshold selection, future
scoring, blind-validation content use, scientific screening decisions or
production mutation.

## Next gate

`FREEZE_ONE_TIME_PRE_REVIEW_TRIAGE_DEVELOPMENT_EVALUATION_EXECUTION_AUTHORIZATION_BEFORE_FIRST_MODEL_OR_VECTORIZER_FIT`
