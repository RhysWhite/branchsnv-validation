# Pre-review triage future scoring v1

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This freeze defines the next consumer of the completed future-text
reconciliation.

The stage will apply the already frozen development-stage evaluator/model
to the canonical future normalized-text population.

It is a **scoring** stage, not model development and not validation-result
evaluation.

## Frozen input population

- complete future resolution population: 12,162
- normalized-text rows eligible for scoring: 11,905
- records without normalized text: 257

The 257 non-scored records consist exactly of:

- 246 `abstract_absent`
- 10 `provider_not_found`
- 1 frozen `openalex_position_gap`

They remain explicit coverage/provenance states. They are not model-negative
records and are not scientific exclusions.

Canonical normalized-text SHA-256:

`8ee30e1bbd94140710e943fc2227805819fa88e84e31207ff64965d67489a1d3`

Future reconciliation completion SHA-256:

`0798d80b10c6fa4beb53cf1074bef959283c2cb0ef2e2be998c6ead4bbc048b1`

## Frozen-model rule

Future scoring must reuse the already frozen development evaluator/model,
preprocessing and decision rule.

This stage may not:

- fit or refit a model;
- compare model candidates;
- select or alter features;
- tune hyperparameters;
- select or alter a threshold;
- calibrate from future outcomes;
- change the design after observing future scores.

## Blind-validation boundary

Future validation labels/outcomes must remain inaccessible during scoring.

They may not be read, joined, inspected, summarized or used for:

- model selection;
- thresholding;
- calibration;
- error analysis;
- interpretation.

The score output must be frozen before any later unblinding step.

## Execution boundary

This design does not execute scoring.

No network access, scientific screening, scientific decision, production
ledger mutation, raw archive mutation or reconciliation mutation is
authorized.

A separate implementation and hostile-test freeze is required, followed by
a separate explicit execution authorization.

## Planned coverage

The implementation must produce:

- exactly 11,905 scored records;
- explicit coverage for all 12,162 resolution records;
- exactly 257 `no_normalized_text` coverage rows.

No missing-text record may be imputed or assigned a model score.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_BEFORE_SEPARATE_EXECUTION_AUTHORIZATION`
