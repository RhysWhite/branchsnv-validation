# Pre-review triage resolved environment state v1

## Status

`FROZEN_RESOLVED_ENVIRONMENT_STATE_PRE_MODEL_IMPLEMENTATION`

This freeze records the exact resolved environment created under the previously
frozen one-time environment-creation authorization.

## Runtime

The dedicated environment is `branchsnv-triage-v1`.

Validated runtime:

- Python 3.11.16;
- NumPy 1.26.4;
- SciPy 1.12.0;
- scikit-learn 1.9.0.

The frozen candidate vectorizer and three classifier constructors imported and
instantiated successfully. No vectorizer or model was fitted.

## Resolved package state

The exact execution artifacts are preserved under
`pre_review_triage_environment_state_v1/`.

`conda-explicit.txt` is the authoritative resolved package specification for
this freeze. Its package URLs are from conda-forge.

`conda-from-history.yml` is retained as observed metadata. It reports both
bioconda and conda-forge in the channel list even though the authorized
creation command used `--override-channels` with only conda-forge. Therefore
the from-history channel list is not used as package-origin evidence.

## Environment immutability

Before evaluator implementation, this environment must not be upgraded,
downgraded, supplemented with pip packages, otherwise modified, or recreated
without an explicit amendment.

## Scientific boundary

This freeze records software environment state only.

It does not authorize evaluator implementation, model fitting, vectorizer
fitting, hyperparameter selection, threshold selection, future scoring,
blind-validation use, scientific screening decisions or production mutation.

## Next gate

`FREEZE_PRE_REVIEW_TRIAGE_EVALUATOR_IMPLEMENTATION_V1_BEFORE_ANY_MODEL_OR_VECTORIZER_FIT`
