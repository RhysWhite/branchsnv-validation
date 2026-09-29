# Pre-review triage model candidates v1 — Amendment 001

## Status

`FROZEN_AMENDMENT_PRE_ENVIRONMENT_CREATION`

This amendment corrects one environment-compatibility statement in the
previously frozen model-candidate design.

## Reason

The original design recorded Python 3.10 together with:

- scikit-learn 1.9.0;
- NumPy 1.26.4;
- SciPy 1.12.0.

A subsequent conda-forge solver dry run demonstrated that scikit-learn 1.9.0
does not resolve for Python 3.10 in the selected environment solve.

The exact same NumPy, SciPy and scikit-learn versions resolve successfully
with Python 3.11.

The earlier read-only constructor/API inspection was performed in an existing
unrelated environment running Python 3.12.14. That environment remains
unauthorized for BRANCHSNV modelling.

## Amendment

The intended dedicated BRANCHSNV triage runtime is changed from Python 3.10 to
Python 3.11.

The following remain unchanged:

- scikit-learn 1.9.0;
- NumPy 1.26.4;
- SciPy 1.12.0;
- all three model candidates;
- every model parameter;
- TF-IDF representation;
- nested whole-batch validation;
- average-precision ranking metric;
- tie-break rules;
- development population;
- scientific authority boundaries.

Python 3.11 has been solver-validated only. Runtime imports and candidate
constructor compatibility under Python 3.11 must be verified after the
dedicated environment is created.

## Authority

This amendment itself does not authorize package installation or environment
creation. It does not authorize model fitting, vectorizer fitting, threshold
selection, future scoring, blind-validation use, scientific decisions or
production mutation.

## Next gate

`FREEZE_DEDICATED_BRANCHSNV_TRIAGE_V1_ENVIRONMENT_CREATION_DESIGN_FOR_PYTHON_3_11`
