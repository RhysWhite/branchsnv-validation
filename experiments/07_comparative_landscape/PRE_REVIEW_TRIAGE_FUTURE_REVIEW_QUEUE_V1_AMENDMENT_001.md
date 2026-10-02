# Pre-review triage future review queue v1 — Amendment 001

Status: `FROZEN_IMPLEMENTATION_AMENDMENT_001_PRE_NEW_AUTHORIZATION`

## Incident

The first authorized production-generation attempt failed before creation of
the canonical queue output.

The failure was deterministic:

1. `tempfile.mkdtemp()` created the staging directory.
2. `write_outputs()` received that already-existing directory.
3. `write_outputs()` called `root.mkdir(..., exist_ok=False)`.
4. Python raised `FileExistsError`.

No canonical queue artifact was created.

No scientific decision, future-label access, blind-validation access, or
production-ledger mutation occurred.

The temporary staging directory was cleaned up.

## Authorization consumption

`PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_001` was exercised by
the failed production attempt and is therefore consumed.

It must not be reused.

The amended implementation accepts only the replacement authorization ID:

`PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_002`

A new separately frozen authorization is required before another production
generation attempt.

## Staging correction

The amended implementation retains `tempfile.mkdtemp()` as a unique staging
parent.

It now writes the queue into a new child:

`staging_parent/payload`

That child does not exist when passed to `write_outputs()`, preserving the
existing fail-if-present behavior.

After all four artifacts are validated, the implementation atomically moves:

`payload -> canonical output root`

The staging parent is then removed.

## Queue semantics unchanged

Amendment 001 changes no queue membership or ranking semantics.

The frozen contract remains:

- priority scored: 5,483
- residual scored: 6,422
- unscored manual review: 257
- total human-review universe: 12,162
- score ranking: continuous score descending, then screening entity ID
  ascending
- no raw-score threshold
- no cross-lane priority

## Regression validation

The amended suite contains:

- 10 original unit tests
- 10 original hostile tests
- 2 Amendment 001 regression tests
- 22 tests total

The new tests prove:

1. the consumed `GENERATION_001` authorization is rejected;
2. the corrected staging-parent/payload execution completes and leaves no
   staging residue.

## Scientific boundary

Amendment 001 grants no scientific decision authority and performs no
production queue generation.

## Next gate

`FREEZE_ONE_USE_PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_AUTHORIZATION_002`
