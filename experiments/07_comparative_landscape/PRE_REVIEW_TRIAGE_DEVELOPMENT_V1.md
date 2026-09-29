# Pre-review triage development v1

## Status

`FROZEN_PRE_MODEL_CANDIDATE_SELECTION`

This freeze defines the development and authority boundaries for a possible
pre-review text triage model. It does not select or fit a model, choose
hyperparameters, choose a score threshold, define an acceptable recall
threshold, score future records, or make scientific decisions.

## Development population

The frozen expanded development corpus contains 4,500 human-labelled records:

- 4,297 `exclude`;
- 203 `retain_for_method_assessment`.

The reconciled retrieval lane contains 4,499 records. One
`identifier_conflict_hold` record remains outside that lane.

Of the 4,499 retrieval-lane records:

- 4,190 have usable normalized title/abstract text:
  - 4,022 `exclude`;
  - 168 `retain_for_method_assessment`.
- 309 have no usable abstract:
  - 274 `exclude`;
  - 35 `retain_for_method_assessment`.

The 309 abstract-absent records are not eligible for text-model training or
model scoring. Abstract absence is not negative scientific evidence. The
eventual operational route for such records is human review.

## Predictive feature boundary

Only `title_text` and `abstract_text` from the frozen canonical
`reconciled_normalized_text.tsv` may be proposed as predictive input in the
next model-candidate design.

Identifiers, provider/retrieval metadata, batch, discovery provenance,
identity-attention state, year, scientific decisions, exclusion reasons,
candidate-method flags, review evidence, operator fields and notes are
prohibited as predictive features.

Batch may be used only as a validation grouping variable.

## Distribution boundary

All 4,500 development records are publications discovered through
`citation_wave_0`.

There are no development examples from the atomic `formal` or `high_recall`
discovery stages, no `software_registry` development examples, and no
development examples with `provider_identity_anchored` or
`provider_identity_confirmed_unanchored` identity-attention states.

No performance claim or future scoring authority is therefore granted for
those unsupported strata.

## Validation boundary

Random row-level train/test splitting is prohibited. Validation must preserve
whole human-screening batches.

Blind validation content is not used for model development, candidate
selection, hyperparameter selection or threshold selection.

This design does not adopt any prior sequential-sampling minimum-positive rule
as a model-acceptance criterion. The existing retrieval contract records that
no acceptable recall threshold has yet been defined.

## Scientific authority

Model output, if later authorized, is triage information only. It is not a
scientific decision.

This freeze does not authorize autonomous exclusion, production scientific
decisions, production-ledger writes, production-queue mutation, or future
record scoring.

Existing uncertainty-toward-retention/source-checking rules remain unchanged.

## Next gate

`FREEZE_PRE_REVIEW_TRIAGE_MODEL_CANDIDATE_SET_V1_BEFORE_ANY_MODEL_FIT`
