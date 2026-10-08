# Pre-review triage environment creation v1

## Status

`FROZEN_ENVIRONMENT_CREATION_AUTHORIZATION_PRE_EXECUTION`

This freeze authorizes one fail-closed creation of a dedicated modelling
environment named `branchsnv-triage-v1`.

It does not authorize model fitting.

## Environment request

The environment must be created with:

- Python 3.11;
- NumPy 1.26.4;
- SciPy 1.12.0;
- scikit-learn 1.9.0.

The solver is `mamba`.

Only `conda-forge` is permitted, using `--override-channels` and strict channel
priority.

`CONDA_PKGS_DIRS` must be set to `$HOME/.conda/pkgs` so creation does not
require write access to the shared system package cache.

## Fail-closed creation

The environment must not exist before execution.

If `branchsnv-triage-v1` already exists, execution must stop for audit. The
environment must not be automatically removed, overwritten or reused.

No altered versions, additional channels or pip fallback are authorized on
solver failure.

## Post-creation checks

Before any model implementation:

- verify Python is 3.11;
- verify NumPy is exactly 1.26.4;
- verify SciPy is exactly 1.12.0;
- verify scikit-learn is exactly 1.9.0;
- import the frozen modelling components;
- instantiate the frozen vectorizer and three candidate classifiers;
- do not fit them;
- capture the resolved conda package inventory;
- capture the explicit conda specification;
- capture the from-history environment specification.

The resolved environment state must then receive its own repository freeze.

## Authority

This freeze authorizes package installation only as part of creation of this
single dedicated environment.

It does not authorize repository mutation during environment creation, model
or vectorizer fitting, hyperparameter selection, threshold selection, future
scoring, blind-validation use, scientific screening decisions or production
mutation.

## Next gate

`CREATE_VALIDATE_AND_FREEZE_RESOLVED_BRANCHSNV_TRIAGE_V1_ENVIRONMENT_STATE`
