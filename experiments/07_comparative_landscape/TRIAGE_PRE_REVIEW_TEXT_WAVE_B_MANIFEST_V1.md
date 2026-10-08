# Triage pre-review text Wave B manifest v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This freeze defines the deterministic Wave B OpenAlex fallback
request population. It does not authorize network access.

## Derivation

Wave A completed 3,956 PubMed logical requests.

Frozen offline normalization identified:

- 3,931 usable PubMed abstracts;
- 24 verified PubMed records with `abstract_absent`;
- 1 verified PubMed `not_found`;
- 0 blocked, malformed, or identity-mismatched PubMed outcomes.

Exactly 25 records therefore satisfy the frozen fallback contract.

## Wave B routes

- 21 exact OpenAlex Work ID requests;
- 4 exact DOI requests;
- 0 exact PMID-only requests.

The frozen precedence remains:

1. exact OpenAlex Work ID;
2. exact DOI;
3. exact PMID.

## Request manifest

Path:

`results/07_comparative_landscape/triage_pre_review_text_retrieval_v1/live_wave_b_request_manifest.tsv`

SHA-256:

`f099f86cce2321ab07d639aeef557014585faf49e2306a09f3fe40119535f0a6`

Rows: 25

The request manifest contains transport identity only. It contains no
scientific decision, exclusion reason, review evidence, model score,
batch identifier, or operator note.

## Derivation evidence

Path:

`results/07_comparative_landscape/triage_pre_review_text_retrieval_v1/live_wave_b_derivation.tsv`

SHA-256:

`a58356439478ca27a48c3967dbbab6a16b275987dc4af7b19f67dd430eeab32b`

The derivation table records only the Wave A retrieval/normalization
state necessary to establish deterministic fallback eligibility.

## Authority boundary

This freeze:

- does not authorize Wave B network access;
- does not create an authorization artifact;
- does not execute OpenAlex requests;
- does not mutate the production scientific ledger;
- does not use blind-validation content.

A separately implemented and tested Wave B execution boundary must be
frozen before any separate explicit human authorization.

## Design

Design SHA-256:

`15361410ddf5c7d5a2989fd5a257c39eabb0b8d0f770ad9beb0a56f0192338bc`
