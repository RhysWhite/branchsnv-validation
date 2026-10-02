# Pre-review triage future scoring results v1

Status: `FROZEN_FUTURE_SCORING_RESULTS_V1`

## Completed execution

The one-use authorized future-scoring execution completed successfully.

Exactly one final deployment fit was performed using the frozen
`linear_svc_balanced_l2_v1` family and all 4,190 frozen development
records.

The fitted model generated continuous raw decision-function scores for
exactly 11,905 canonical future normalized-text records.

## Coverage

The complete future resolution population contains 12,162 records.

- 11,905 received continuous scores.
- 257 remained explicitly `no_normalized_text`.
- Those 257 comprise 246 `abstract_absent`, 10 `provider_not_found`,
  and one frozen `openalex_position_gap`.

No missing-text record was imputed or scored.

## Frozen production result set

The canonical result set contains exactly:

- `scored_records.tsv`
- `coverage.tsv`
- `execution_manifest.json`
- `checksums.sha256`
- `execution_completion.json`

Their exact byte identities are bound by this result freeze.

## One-use execution state

The authorized execution is consumed.

Rerun is not authorized.

The canonical production output root now exists, and the frozen scorer's
fail-closed output-root precondition independently prevents a second
production execution.

## Decision boundary

No threshold was selected.

No hard predictions were generated.

No probability calibration or review-fraction selection was performed.

The frozen result is continuous-score-only.

## Blind-validation boundary

Blind-validation content remains unused.

Future labels remain unused.

No unblinding occurred.

## Scientific boundary

This result freeze does not make scientific screening decisions, exclusions,
or production-ledger mutations.

It does not authorize any downstream threshold selection, unblinding,
validation interpretation, or scientific decision.

The repo-defined post-scoring gate must be resolved separately before any
such action.
