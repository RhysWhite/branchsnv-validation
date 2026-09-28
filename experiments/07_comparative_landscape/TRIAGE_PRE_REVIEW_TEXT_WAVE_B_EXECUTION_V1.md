# Triage pre-review text Wave B execution v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This design defines the execution boundary for the already frozen
25-request Wave B OpenAlex fallback manifest.

It does not authorize network access.

## Request population

Wave B contains exactly 25 requests:

- 21 exact OpenAlex Work ID requests;
- 4 exact DOI requests.

PubMed, OpenAlex search/list endpoints, Crossref, and ad hoc probes
are outside this execution contract.

## Architecture

The frozen Wave A implementation remains byte-identical.

Wave B receives dedicated:

- authorization guard;
- transport-evidence adapter;
- runner core;
- live entrypoint.

The already frozen low-level HTTP transport is reused unchanged.

The historical T000002 transport module remains a frozen
provenance/safety dependency and is not Wave B execution authority.

## Execution

Requests execute serially in ascending request sequence.

Concurrency is one.

OpenAlex is limited to no more than two requests per second, including
redirects, with a 0.5-second cold-start delay before the first request.

Only verified terminal evidence may advance the request checkpoint.

An unresolved or ambiguous fault halts execution fail-closed.

## Authorization

Wave B requires a separate explicit human authorization after the
implementation and hostile tests have themselves been frozen.

Canonical future authorization path:

`results/07_comparative_landscape/triage_pre_review_text_retrieval_v1/live_wave_b/authorization.json`

The authorization must remain untracked at execution time and is
one-use.

This design creates no authorization.

## Authority boundary

- No Wave B network authorization exists.
- No Wave B network request is permitted by this freeze.
- No production mutation is permitted.
- Blind-validation content is not used.
- Transport evidence contains no scientific decision fields.

## Design SHA-256

`4a607178762e9e884f430b8fe1c47d078408b5a51e4e47701f2f4302ab5ca2ca`
