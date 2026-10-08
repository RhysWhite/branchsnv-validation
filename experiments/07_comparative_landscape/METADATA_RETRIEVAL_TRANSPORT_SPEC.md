# Experiment 07 metadata-retrieval transport specification

Status: FROZEN_PRE_IMPLEMENTATION_TRANSPORT_CANDIDATE

## 1. Purpose

This specification defines the transport behavior used to retrieve the exact
logical metadata evidence frozen in:

`metadata_resolution_logical_lookups.tsv`

It does not change the evidence queue.

Transport is a separate layer from:

- discovery;
- publication identity construction;
- cross-stage component construction;
- logical evidence selection;
- metadata reconciliation; and
- scientific screening.

No live metadata retrieval had occurred when this specification was frozen.

## 2. Frozen upstream queue

The upstream metadata-resolution queue was frozen at repository commit:

`63869a032b53009755d6bde000ded71406da304f`

It contains exactly:

- 1,342 attention components;
- 1,847 component-evidence assignments; and
- 1,731 unique logical lookup keys.

Logical lookup keys by provider:

- OpenAlex: 1,169;
- OpenCitations Meta: 495;
- PubMed: 67.

Transport must neither add nor remove logical lookup keys.

## 3. Transport-unit policy

One frozen logical lookup is one primary provider operation.

No batching is used in the first transport implementation.

Therefore the frozen queue defines:

- 1,731 planned primary provider operations.

This is not a prediction of the final number of HTTP exchanges.

Actual HTTP exchanges may be greater because:

- redirects are followed explicitly;
- retryable failures may generate additional attempts.

The singleton transport policy is an operational choice made for:

- atomic raw-response provenance;
- unambiguous lookup-to-response mapping;
- isolated retries;
- isolated negative results; and
- simpler resumability and independent validation.

It is not claimed to be optimal for throughput or provider cost.

## 4. Provider routes

### 4.1 OpenAlex

Base host:

`https://api.openalex.org`

Logical routes map to exact Work singleton endpoints.

#### `work_by_openalex_id`

Method:

`GET`

Endpoint form:

`/works/<OpenAlex Work ID>`

Example shape:

`/works/W2741809807`

#### `work_by_doi`

Method:

`GET`

Endpoint form:

`/works/doi:<normalized DOI>`

#### `work_by_pmid`

Method:

`GET`

Endpoint form:

`/works/pmid:<normalized PMID>`

OpenAlex search/list endpoints are not permitted by this transport specification.

### 4.2 OpenCitations Meta

Base host:

`https://api.opencitations.net`

API prefix:

`/meta/v1`

#### `metadata_by_doi`

Method:

`GET`

Endpoint form:

`/metadata/doi:<normalized DOI>`

#### `metadata_by_omid`

Method:

`GET`

Endpoint form:

`/metadata/omid:<normalized OMID>`

Exactly one logical identifier is supplied per primary provider operation.

The API's support for multiple identifiers in one request is deliberately not
used by this first implementation.

### 4.3 PubMed

Base host:

`https://eutils.ncbi.nlm.nih.gov`

Endpoint:

`/entrez/eutils/efetch.fcgi`

Logical route:

`record_by_pmid`

Method:

`GET`

Required transport parameters:

- `db=pubmed`;
- `id=<normalized PMID>`;
- `retmode=xml`.

Exactly one PMID is supplied per primary provider operation.

No PubMed search operation is permitted.

## 5. Credentials

### 5.1 OpenAlex

An OpenAlex API key is optional.

If supplied, it may be read from:

`OPENALEX_API_KEY`

It must be transmitted only as:

`Authorization: Bearer <key>`

The key must never be:

- inserted into a request URL;
- printed;
- written to a manifest;
- written to raw request metadata;
- included in exception text; or
- included in checksums or provenance files.

Anonymous retrieval is permitted when no key is supplied.

### 5.2 OpenCitations

An OpenCitations access token is optional.

If supplied, it may be read from:

`OPENCITATIONS_ACCESS_TOKEN`

It must be transmitted only in the authorization header.

The token must never be persisted or displayed.

### 5.3 PubMed

The first implementation does not require or use an NCBI API key.

The PubMed transport rate remains below the documented unkeyed limit.

This avoids persisting an API key in query parameters or request provenance.

## 6. Request pacing

Transport pacing is a pragmatic operational bound rather than an optimality
claim.

Maximum primary-attempt initiation rate per provider:

- OpenAlex: 2 requests/second;
- OpenCitations Meta: 2 requests/second;
- PubMed: 2 requests/second.

The OpenCitations bound is below its documented 180 requests/minute/IP limit.

The PubMed bound is below its documented 3 requests/second unkeyed limit.

A server-provided `Retry-After` instruction overrides the ordinary local
pacing when retrying.

## 7. Redirect handling

Automatic HTTP redirect following must be disabled.

Redirects are transport evidence.

Redirect status codes handled explicitly:

- 301;
- 302;
- 303;
- 307;
- 308.

For each redirect hop, archive:

- requested URL after credential redaction;
- response status;
- `Location` target;
- response headers after sensitive-header redaction; and
- raw response body, including an empty body.

A redirect may be followed only when the target:

- uses HTTPS;
- remains on the expected provider host; and
- remains within the expected provider endpoint family.

Maximum redirect hops per logical lookup:

- 5.

A redirect loop or redirect outside the allowed provider host/path fails closed.

A redirect does not modify the frozen logical lookup key.

## 8. Attempt and retry policy

Maximum transport attempts per logical lookup:

- 5 primary attempts.

Retryable conditions include:

- connection reset;
- timeout;
- incomplete transport;
- HTTP 408;
- HTTP 425;
- HTTP 429;
- HTTP 500;
- HTTP 502;
- HTTP 503;
- HTTP 504.

Every failed attempt is retained.

No failed attempt may be overwritten by a later success.

Deterministic retry delays, unless a valid `Retry-After` requires longer:

- after attempt 1: 1 second;
- after attempt 2: 2 seconds;
- after attempt 3: 4 seconds;
- after attempt 4: 8 seconds.

Retry exhaustion is non-terminal for scientific interpretation but blocks a
COMPLETE transport manifest.

The retry-count and delay schedule are pragmatic operational bounds.

## 9. Non-retryable HTTP failures

The following are integrity/configuration failures and fail closed:

- 400;
- 401;
- 403.

Unexpected non-retryable 4xx or 5xx statuses also fail closed unless explicitly
classified elsewhere in this specification.

A `401` or `403` must not be converted into a per-record negative result.

## 10. Exact negative results

A valid exact lookup can return no bibliographic record.

Negative exact evidence is retained rather than retried indefinitely.

### OpenAlex

HTTP `404` is terminal:

`not_found`

### OpenCitations Meta

Either of the following is terminal negative evidence:

- HTTP `404`; or
- HTTP `200` containing a structurally valid empty result list.

Status:

`not_found`

### PubMed

A structurally valid PubMed EFetch response containing no record for the
requested PMID is terminal:

`not_found`

Negative evidence does not authorize fuzzy search.

## 11. Successful-response structural validation

Transport validates response structure only.

It does not adjudicate scientific identity.

### 11.1 OpenAlex

A successful terminal response must:

- have HTTP status 200;
- decode as JSON;
- decode to one JSON object;
- contain a non-empty `id`;
- contain an `ids` object.

Fields such as title, DOI, PMID, type and publication date may be absent and are
handled later by metadata reconciliation.

When a Work-ID lookup was redirected, the final returned OpenAlex ID may differ
from the requested Work ID.

Both values must be retained.

A returned provider identifier does not rewrite the frozen lookup key.

### 11.2 OpenCitations Meta

A successful terminal response must:

- have HTTP status 200;
- decode as JSON;
- decode to a list.

For one exact requested identifier:

- zero entries is terminal `not_found`;
- exactly one entry is terminal `success`;
- more than one entry is an ambiguity/integrity failure and fails closed.

The transport layer does not decide whether returned DOI/OMID relationships
authorize component merging.

### 11.3 PubMed

A successful terminal response must:

- have HTTP status 200;
- parse as XML;
- be structurally valid PubMed EFetch output.

For one exact requested PMID:

- zero returned records is terminal `not_found`;
- exactly one matching record is terminal `success`;
- multiple returned records or an incompatible requested PMID fails closed.

Metadata extraction and identifier reconciliation occur in a later layer.

## 12. Raw archive

Planned retrieval root:

`results/07_comparative_landscape/metadata_resolution_retrieval/`

The transport implementation must not overwrite the frozen queue artifacts.

Required production structure:

- `manifest.json`
- `lookup_status.tsv`
- `attempts.tsv`
- `redirects.tsv`
- `checksums.sha256`
- `raw/`

Each logical lookup receives its own raw evidence directory derived from the
stable logical lookup ID.

Each transport attempt receives an immutable attempt directory.

An attempt archive must contain enough information to reconstruct:

- logical lookup ID;
- provider;
- route;
- identifier namespace;
- identifier value;
- attempt number;
- request method;
- sanitized request URL;
- sanitized request headers;
- response status;
- sanitized response headers;
- redirect chain;
- raw response bytes;
- body SHA-256;
- timestamp; and
- transport outcome.

Authorization values must never be persisted.

## 13. Raw-byte rule

Provider response bodies are archived exactly as received.

The production archive must not retain only parsed or normalized metadata.

Parsing is a derived operation.

Raw response SHA-256 values are calculated on the exact archived response
bytes.

## 14. Sensitive-header policy

The archive must exclude or redact at minimum:

- `Authorization`;
- API-key headers;
- cookies; and
- other credential-bearing headers.

Sanitized request metadata must make it possible to reconstruct the request
without reconstructing a credential.

Response headers may be retained after removal of credential/cookie material.

## 15. Terminal lookup statuses

Permitted logical-lookup terminal statuses:

- `success`;
- `not_found`.

Non-terminal/failure statuses include:

- `pending`;
- `retry_exhausted`;
- `transport_failure`;
- `redirect_failure`;
- `authentication_failure`;
- `response_integrity_failure`.

Only `success` and `not_found` count as completed evidence lookups.

## 16. Retrieval completion gate

A metadata transport run may be marked `COMPLETE` only when:

1. all 1,731 frozen logical lookup IDs are represented;
2. every logical lookup has exactly one terminal accepted status;
3. every accepted response or negative result has complete provenance;
4. all raw archived bodies match recorded SHA-256 values;
5. all redirect chains are closed;
6. no retry-exhausted lookup remains;
7. no pending lookup remains;
8. no authentication/configuration failure remains;
9. no response-integrity failure remains;
10. the frozen logical lookup manifest is byte-identical to the queue-freeze
    artifact;
11. no logical lookup has been added or removed; and
12. no scientific screening or component merge has occurred.

A partial retrieval cannot be called complete.

## 17. Resume behavior

A resumed transport run may reuse an existing terminal lookup only when:

- the logical lookup ID matches exactly;
- provider/route/namespace/identifier match exactly;
- archived terminal evidence passes checksum validation; and
- archive schema/version is compatible.

Otherwise the lookup must not be silently reused.

Failed attempts are never deleted during resume.

## 18. Execution order

The implementation executes logical lookups in the deterministic order already
present in:

`metadata_resolution_logical_lookups.tsv`

Execution order has no scientific interpretation.

Per-provider pacing is maintained independently.

## 19. Transport/reconciliation boundary

Transport may determine only:

- whether exact provider evidence was obtained;
- whether no record was found;
- whether retrieval failed; and
- what raw provider bytes and redirect evidence were returned.

Transport must not determine:

- whether two DOI records are the same publication;
- whether preprint and published versions should merge;
- whether a provider identifier is scientifically preferable;
- whether a title is sufficient for screening;
- whether a candidate is relevant to Experiment 07; or
- whether a method enters the comparator landscape.

Those are later reconciliation/screening stages.

## 20. Source-contract snapshot

Transport design was checked against provider documentation on 2026-09-24.

At that time:

- OpenAlex documented exact singleton Work lookup by OpenAlex ID, DOI and PMID;
- OpenAlex documented HTTP 301 redirects for merged entity IDs;
- OpenAlex documented optional bearer-token authentication;
- OpenCitations Meta documented exact `/metadata/{ids}` retrieval for DOI and
  OMID, including support for one or more identifiers;
- OpenCitations documented a 180 requests/minute/IP rate limit;
- PubMed ESummary/EFetch documented exact UID-list retrieval; and
- NCBI documented a 3 requests/second unkeyed E-utilities limit.

The singleton no-batching design is a local provenance choice, not a provider
requirement.

## 21. Interpretation

This specification freezes transport mechanics only.

The 1,731 planned primary provider operations are operational objects, not
scientific sample sizes.

Retries and redirects may increase the number of actual HTTP exchanges.

No provider response has yet been retrieved or accepted.
