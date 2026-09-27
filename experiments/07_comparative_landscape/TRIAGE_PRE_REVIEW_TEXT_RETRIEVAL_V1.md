# Triage pre-review text retrieval v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This document freezes a development-only pre-review text retrieval
design. It does not authorize network access, production screening,
automated exclusion, model fitting, threshold selection, future
scoring, or blind-validation access.

## Development population

- Expanded frozen development corpus: 4,500 records.
- Publication-text retrieval lane: 4,499 records.
- Protected from this lane: 1 record with a non-empty identity-attention
  state.
- Final development labels remain outside the retrieval manifest:
  4,297 `exclude` and 203 `retain_for_method_assessment`.
- Historical and C000001 labels are treated as scientifically compatible
  for development under the common frozen screening contract.
- Batch remains a validation grouping and is prohibited as a predictive
  feature.

## Frozen retrieval manifest

Path:

`results/07_comparative_landscape/triage_pre_review_text_retrieval_v1/input_manifest.tsv`

SHA-256:

`4e5ba0313e008a58e968a9368ea90b6fdb70049b866003742ed1c967c31120ba`

Rows: 4499

The manifest contains identifiers and deterministic transport routing
only. It contains no scientific decision, exclusion reason, review
evidence, model score, or batch identifier.

## Retrieval cascade

For records with a PMID, PubMed exact-PMID EFetch is attempted first.
A usable PubMed abstract terminates the cascade for that record.

When PubMed is not applicable or does not yield a usable abstract,
OpenAlex is the fallback. OpenAlex lookup identity is selected in this
order:

1. exact OpenAlex Work ID;
2. exact DOI;
3. exact PMID.

Crossref is not a primary route in v1.

Retrieval failure, provider absence, or abstract absence is never itself
scientific evidence for exclusion.

## Transport

The implementation must reuse the existing exact-identifier transport
semantics and raw-response archival machinery. A separate independent
HTTP stack is prohibited.

Every successful raw response must remain byte-verifiable through its
SHA-256 and provider identity checks. Existing retry, rate-limit,
redirect, credential-sanitisation, and archive-integrity semantics are
preserved.

## Text normalization

### PubMed

The parser reads a single `PubmedArticle` or `PubmedBookArticle`,
validates the requested identity, extracts title text, and concatenates
non-empty `AbstractText` elements in document order.

`Label` and `NlmCategory` values are retained as metadata but are not
inserted into model text.

### OpenAlex

The parser reconstructs `abstract_inverted_index` by integer position.

Malformed tokens, position vectors, non-integer positions, or duplicate
positions fail closed at the parser layer.

Non-contiguous position sets receive an explicit position-gap status;
they are not silently treated as ordinary primary-model abstracts.

No minimum abstract-length threshold is frozen in v1.

## Leakage boundary

The normalized retrieval artifact must not contain scientific decisions,
review evidence, operator fields, notes, model scores, or thresholds.

Provider identity, retrieval status, failure state, batch, discovery
provenance, DOI prefix, journal, and publisher are not model features
under this design.

## Model and validation boundary

This freeze does not select a classifier or threshold.

Whole-batch nested development validation remains required.

The frozen blind validation sample remains outside this work and must
not be opened for model development. Future-universe records must not be
scored during development.

Missing abstract text must not be interpreted as negative scientific
evidence.

## Authority boundary

This design creates no network authority and no production authority.

Live retrieval requires a separate explicit authorization after the
parser and development-only retrieval runner have been implemented and
tested against archived payloads.

The production scientific-screening protocol remains unchanged.
