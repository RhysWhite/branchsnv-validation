# Pre-review triage future scoring v1 — execution authorization

Status: `FROZEN_ONE_USE_AUTHORIZATION_PRE_EXECUTION`

## Authorization

This freeze authorizes one production execution of the frozen future-scoring
implementation.

Authorization ID:

`PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_EXECUTION_001`

The authorized execution consists only of:

1. one final fit of the already-selected
   `linear_svc_balanced_l2_v1` family using all 4,190 frozen development
   records; and
2. continuous scoring of exactly 11,905 canonical future normalized-text
   records.

## Implementation binding

Implementation-freeze checksum identity:

`fc3110e70c0454d69743dd4371e41396644a784fca58d2230152efec01c49684`

The authorization is valid only for that frozen implementation and the exact
frozen triage runtime.

## Authorized population

Development fit:

- 4,190 records
- 168 positives
- 4,022 negatives

Future population:

- 12,162 resolution records
- 11,905 scoreable normalized-text records
- 257 explicit no-normalized-text coverage records

## Output contract

The canonical output root is:

`results/07_comparative_landscape/pre_review_triage_future_scoring_v1`

It must be absent before execution.

The authorized implementation may create exactly the frozen five-artifact
future-scoring production set.

## Explicit exclusions

This authorization does not permit:

- model-family selection;
- hyperparameter tuning;
- feature selection;
- threshold selection;
- hard predictions;
- probability calibration;
- review-fraction selection;
- blind-validation content use;
- future-label use;
- scientific screening decisions;
- network access;
- production-ledger mutation.

The output remains continuous-score-only.

## Pre-execution state

At this authorization freeze:

- no final deployment fit has occurred;
- no future scoring has occurred;
- no future-scoring output exists;
- no threshold has been selected;
- blind-validation content remains unused.

## Exact execution confirmation

`EXECUTE-FROZEN-FUTURE-SCORING-V1`

## Next gate

`EXECUTE_ONCE_FROZEN_PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1`
