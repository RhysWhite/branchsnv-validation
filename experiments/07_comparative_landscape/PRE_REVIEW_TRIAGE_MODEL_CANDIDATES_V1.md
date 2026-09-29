# Pre-review triage model candidates v1

## Status

`FROZEN_PRE_MODEL_IMPLEMENTATION`

This freeze defines the exact candidate model families, text representation,
nested whole-batch validation procedure, candidate-selection metric, and
environment requirements before any vectorizer or classifier is fitted.

## Development data

Only the 4,190 development records with usable normalized title and abstract
text are in the model-development lane:

- 4,022 `exclude`;
- 168 `retain_for_method_assessment`.

The positive class is `retain_for_method_assessment` and is encoded as 1.
`exclude` is encoded as 0.

The 309 abstract-absent records remain outside model training and scoring and
remain routed to human review.

## Text representation

For each eligible record:

`title_text + "\n\n" + abstract_text`

A single word-level TF-IDF representation is frozen:

- lowercase;
- Unicode accent stripping;
- word unigrams and bigrams;
- `min_df=2`;
- no maximum-document-frequency pruning beyond `max_df=1.0`;
- no fixed vocabulary;
- L2 normalization;
- IDF with smoothing;
- sublinear term frequency;
- no stop-word list;
- default two-or-more-character word-token pattern.

The vectorizer must be fitted inside each training partition only.

## Candidate families

Exactly three candidates are permitted:

1. balanced L2 logistic regression;
2. balanced L2 linear SVM;
3. Complement Naive Bayes.

No grid search, hyperparameter search, embeddings, transformer model,
character-ngram alternative, or additional classifier family is authorized by
this freeze.

## Nested whole-batch validation

Outer validation consists of nine leave-one-whole-batch-out folds.

For each outer fold, the eight training batches undergo an inner
leave-one-whole-batch-out comparison of the three candidate families.

Within every inner split:

1. fit a new TF-IDF vectorizer using inner-training text only;
2. fit each candidate classifier using inner-training labels only;
3. score the untouched inner-held-out batch;
4. calculate average precision for that held-out batch.

The candidate with the highest unweighted mean batch-level average precision
is selected inside that outer fold. Ties are resolved by higher minimum
batch-level AP, then higher median batch-level AP, then the frozen candidate
order.

The selected candidate is then refitted on all eight outer-training batches
using a newly fitted vectorizer and produces continuous scores for the
untouched outer batch.

No hard classifications or score thresholds are generated.

## Final family selection

After nested development evaluation, the same three fixed candidates may be
compared across all nine development batches using leave-one-whole-batch-out
average precision.

The candidate family with the highest macro mean batch AP is selected, with
the same pre-specified tie-break sequence.

This freeze does not yet authorize fitting that family to all 4,190 records.

## Metrics

Average precision is the primary threshold-independent ranking metric.

Per-batch AP, macro mean AP, median AP and minimum AP are reported.

No acceptable recall threshold is defined here. Precision/recall at a selected
threshold, automatic exclusion, and threshold optimization remain prohibited.

## Environment

API compatibility was inspected against:

- Python 3.10;
- scikit-learn 1.9.0;
- NumPy 1.26.4;
- SciPy 1.12.0.

That inspection used an existing unrelated environment read-only. That
environment is not authorized for BRANCHSNV modelling.

A dedicated pinned BRANCHSNV triage environment must be created and frozen
before implementation or fitting.

## Authority

This freeze authorizes no model fitting, vectorizer fitting, future scoring,
threshold selection, blind-validation use, scientific decision, production
write, or autonomous exclusion.

## Next gate

`CREATE_AND_FREEZE_DEDICATED_BRANCHSNV_TRIAGE_V1_MODELLING_ENVIRONMENT_BEFORE_MODEL_IMPLEMENTATION`
