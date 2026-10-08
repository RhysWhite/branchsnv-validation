# Pre-review triage operating-point curve v1 Amendment 001

## Status

`FROZEN_SERIALIZATION_AMENDMENT_001_PRE_REGENERATION`

## Reason

The first deterministic curve-generation attempt failed while serializing the
first per-batch row.

The frozen v1 `format_number()` helper attempted to convert every non-null,
non-integer value to `float`.

The first field was the string batch identifier `B000001`, producing:

`ValueError: could not convert string to float: 'B000001'`

The failed output contained only the TSV header and no data rows.

## Preserved failure evidence

The exact header-only partial artifact is preserved under the failed-attempt
results directory together with a post-failure audit receipt.

Its SHA256 is:

`743ebdcfd7fb6896655c863c8b593f9dca8db1c0347a2f8fe2735f7062acc95b`

## Amendment scope

The original frozen implementation is not modified.

Amendment 001 loads that exact implementation by SHA256 and replaces only its
in-memory `format_number` callback.

The amended callback:

- writes `None` as an empty field;
- writes strings unchanged;
- preserves integer serialization;
- preserves the original `.17g` numeric serialization for other values.

No ranking, Fraction-grid, review-count, recall, precision or selection logic
changes.

## Scientific boundary

The failed attempt and this amendment perform no model fitting, calibration,
threshold selection, review-fraction selection, future scoring,
blind-validation content use, scientific screening decisions or production
mutation.

## Canonical failed output

After this amendment is committed and the exact failed header-only artifact is
safely preserved in Git, the original untracked canonical partial may be
retired so the amended deterministic generation can use the canonical output
path.

## Next gate

`GENERATE_AND_FREEZE_PRE_REVIEW_TRIAGE_OPERATING_POINT_CURVES_V1_WITH_AMENDMENT_001`
