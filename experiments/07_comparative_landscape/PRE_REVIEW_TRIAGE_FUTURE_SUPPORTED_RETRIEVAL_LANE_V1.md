# Pre-review triage supported future retrieval lane v1

## Status

`FROZEN_SUPPORTED_FUTURE_RETRIEVAL_LANE_PRE_RETRIEVAL`

## Purpose

This artifact defines the exact future publication lane for which the frozen
development model has matching discovery-stage/entity-class support and for
which text retrieval may subsequently be performed.

## Eligibility

Records must be:

- publication entities;
- metadata-screenable and ready;
- associated with citation-wave provenance `0`;
- free of an identity-attention hold;
- outside the development retrieval population;
- outside the frozen blind-validation sample.

Records may also have additional discovery-stage provenance; citation-wave
provenance `0` is the support-defining field.

## Count

Supported future retrieval records:

`12162`

Of these, post-membership additions:

`6`

Frozen blind-sample records in the supported lane were mechanically excluded
by entity ID before retrieval.

No blind title, abstract, label or scientific content was inspected or used.

## Boundary

No network retrieval, model fitting, future scoring, scientific screening
decision or production mutation occurred in constructing this lane.

## Next gate

`AUTHORIZE_AND_RUN_TEXT_RETRIEVAL_FOR_EXACT_SUPPORTED_FUTURE_LANE`
