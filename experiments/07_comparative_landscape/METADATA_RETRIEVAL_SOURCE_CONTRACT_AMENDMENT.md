# Experiment 07 metadata-retrieval source-contract amendment

Status: `FROZEN_PRE_IMPLEMENTATION_SOURCE_CONTRACT_CORRECTION`

## Purpose

This amendment corrects provider-facing transport details after the offline
metadata-retrieval implementation freeze and before any live
metadata-resolution request.

The correction is operational only. It does not change the frozen logical
evidence queue, provider allocation, exact identifier routes, publication
identity rules, screening entities, comparator eligibility, or any scientific
decision.

## Trigger

A final live-execution preflight against current official provider
documentation identified two provider-contract differences relative to the
previously frozen transport specification.

The previously frozen specification and implementation remain preserved in
repository history as the exact pre-live design and implementation state.

## OpenAlex authentication

The frozen implementation reads an optional key from:

`OPENALEX_API_KEY`

The earlier transport specification required the key to be sent as:

`Authorization: Bearer <key>`

Current OpenAlex documentation instead instructs clients to supply the key as
the URL query parameter:

`api_key=<key>`

The post-freeze implementation amendment SHALL therefore:

1. continue reading the optional key from `OPENALEX_API_KEY`;
2. transmit it using the `api_key` query parameter;
3. remove OpenAlex Bearer authentication;
4. continue to permit anonymous exact singleton retrieval when no key is
   supplied;
5. redact `api_key` from every persisted or displayed URL;
6. ensure the raw key does not enter request ledgers, manifests, exceptions,
   checksums, or provenance artifacts; and
7. preserve the key across an allowed same-provider redirect without relying
   on the provider to repeat the query parameter in its `Location` header.

The exact OpenAlex Work lookup routes remain unchanged:

- OpenAlex Work ID;
- DOI shorthand; and
- PMID shorthand.

Explicit redirect handling remains required because OpenAlex documents HTTP
301 redirects for merged entities.

## PubMed E-utility identification

The frozen PubMed exact retrieval route remains EFetch by one PMID per logical
lookup.

Current NCBI E-utility guidance states that `tool` and `email` should be
included in all E-utility requests.

The post-freeze implementation amendment SHALL therefore:

1. add a fixed no-whitespace `tool` identifier for this Experiment 07
   transport;
2. read the developer contact address from `NCBI_EMAIL`;
3. add both `tool` and `email` to PubMed EFetch requests during live
   execution;
4. require a valid non-empty `NCBI_EMAIL` before any live frozen-queue
   execution can begin;
5. fail before creation of the production retrieval directory if that live
   prerequisite is absent or malformed;
6. redact the `email` query value from persisted or displayed request URLs;
7. not use an NCBI API key; and
8. retain the existing maximum initiation rate of two requests per second.

The 2 requests/second operational bound remains below NCBI's documented
unkeyed limit of 3 requests/second.

The fixed tool identifier SHALL be:

`branchsnv_validation_experiment_07`

The developer email itself is environment-provided operational configuration
and SHALL NOT be committed to the repository.

## OpenCitations Meta

No behavioral change is authorized.

The existing implementation remains:

- exact `/meta/v1/metadata/{id}` retrieval;
- optional `OPENCITATIONS_ACCESS_TOKEN`;
- token transmitted in the authorization header;
- two requests/second maximum initiation rate.

This remains below the documented 180 requests/minute/IP rate limit.

## Redirect credential preservation

Provider redirects remain transport evidence and do not imply publication
identity resolution.

For OpenAlex only, when an authenticated request follows an allowed same-host
redirect, the implementation SHALL preserve the already supplied `api_key`
credential even if the provider's `Location` header omits it.

The credential must remain redacted in all archived redirect/request evidence.

No credential may be copied across providers or to a different host.

## Live preflight

Live execution SHALL remain disabled while this amendment is implemented and
tested.

Before later live enablement, a preflight SHALL establish all of the
following before creating the production retrieval directory or issuing any
network request:

- the frozen 1,731-lookup queue is intact;
- live execution has been explicitly enabled;
- `NCBI_EMAIL` is available and syntactically acceptable;
- optional OpenAlex and OpenCitations credentials can be handled without
  persistence;
- frozen implementation/amendment checksums pass.

## Unchanged transport contract

This amendment does not alter:

- 1,731 logical lookup keys;
- one primary provider operation per logical lookup;
- no batching;
- provider assignment;
- exact identifier namespaces or values;
- maximum five transport attempts;
- maximum five redirect hops;
- retryable HTTP-status set;
- deterministic retry delays;
- `Retry-After` handling;
- provider-specific structural response validation;
- raw-byte preservation;
- immutable attempt evidence;
- archive/resume semantics;
- production ledger semantics;
- accepted terminal statuses `success` and `not_found`;
- the exact-frozen-set `COMPLETE` gate;
- reconciliation boundaries;
- tool consolidation boundaries; or
- scientific screening boundaries.

## Provider source snapshot

Provider contracts were rechecked on 2026-09-24 against:

- OpenAlex authentication documentation:
  `https://developers.openalex.org/api-reference/authentication`
- OpenAlex singleton retrieval documentation:
  `https://developers.openalex.org/guides/get`
- NCBI E-utilities parameter documentation:
  `https://www.ncbi.nlm.nih.gov/books/NBK25499/`
- NCBI E-utilities usage guidance:
  `https://www.ncbi.nlm.nih.gov/books/NBK25497/`
- OpenCitations Meta REST API:
  `https://api.opencitations.net/meta/v1`

## Classification

This is a post-freeze operational source-contract correction.

It does not reopen the scientific evidence plan or the frozen transport
architecture.

No live metadata-resolution request had been made when this amendment was
frozen.
