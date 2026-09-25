# Experiment 07 T000002 authoritative-source network transport and live-retrieval authorization design

Status: `FROZEN_PRE_NETWORK_TRANSPORT_IMPLEMENTATION`

Parent retrieval-implementation commit:

`a756caf01d49b6ffdd8ff7e4081d3f8fc12bdc9a`

## Purpose

This design defines the network-security, retrieval, archival, recovery and
one-use authorization contract for the 26 frozen T000002 authoritative-source
seed tasks.

It does not implement network transport and it does not authorize live
retrieval.

## Frozen input

Seed task count:

`26`

Seed queue SHA-256:

`04b758cb6feb7460811116efef9b38a509b5996f63ca30cf225d9cf75448c691`

Target identity SHA-256:

`5970e1ec739b5b01c546e526c402d2f3a6e06e8f43aef0bfcd375e692bc2ab5e`

Current production event count:

`11`

Awaiting source escalation:

`10`

## Seed transport routes

### PubMed authoritative record

- HTTPS GET only.
- Host: `eutils.ncbi.nlm.nih.gov`.
- Path: `/entrez/eutils/efetch.fcgi`.
- `db=pubmed`.
- `retmode=xml`.
- PMID supplied only from the frozen queue.
- Maximum payload: 4 MiB.
- Cross-host redirects prohibited.

### PubMed-to-PMC link discovery

- HTTPS GET only.
- Host: `eutils.ncbi.nlm.nih.gov`.
- Path: `/entrez/eutils/elink.fcgi`.
- `dbfrom=pubmed`.
- `db=pmc`.
- `retmode=xml`.
- PMID supplied only from the frozen queue.
- Maximum payload: 4 MiB.
- Any discovered PMCID is recorded only.
- Discovered full-text routes are not executed under the seed authorization.

### DOI publisher article

- HTTPS GET begins at `doi.org`.
- DOI supplied only from the frozen queue.
- HTTPS redirects may reach public publisher hosts.
- Maximum redirects: 8.
- Maximum payload: 32 MiB.
- No authentication, login automation, CAPTCHA bypass or paywall bypass.

## SSRF and redirect controls

All live requests require:

- HTTPS;
- TLS certificate validation;
- DNS hostnames rather than IP literals;
- public address resolution;
- rejection of loopback, private, link-local, multicast, reserved and
  unspecified addresses;
- rejection of URL userinfo;
- rejection of non-default ports;
- rejection of HTTP downgrade;
- complete redirect-chain recording.

NCBI routes may not redirect to another host.

The DOI route may redirect to a public HTTPS publisher host.

## Request controls

Only `GET` is permitted.

Requests have no body.

Persistent cookies are disabled.

Authorization and Cookie request headers are prohibited.

Destination credentials are never supplied.

`Accept-Encoding: identity` is required so archived response bytes have a
direct auditable identity.

A conservative global minimum request interval of one second is required.

## Retry contract

At most three attempts may occur for one seed task.

Retries are restricted to transient transport failures and HTTP:

- 429
- 502
- 503
- 504

TLS validation failures, SSRF-policy failures, payload-limit failures and
ordinary non-transient 4xx responses are not retried.

Every attempt is recorded.

## Response contract

Every attempted task must receive a final transport outcome.

Successful retrieval of all 26 tasks is not required.

For obtained payloads the transport records:

- HTTP status;
- content type;
- final URL;
- redirect chain;
- retrieval timestamp;
- response headers;
- SHA-256;
- byte count.

HTTP failure, access denial, not-found and transport failure remain transport
outcomes only.

They are not scientific exclusion decisions.

## Production evidence structure

Future production root:

`results/07_comparative_landscape/t000002_authoritative_source_retrieval`

Frozen run identity:

`ASR000001`

The live implementation will use a staging directory matching:

`.ASR000001.tmp.*`

and may atomically finalize only to:

`ASR000001`

Required artifacts include:

- `seed_queue.tsv`
- `retrieval_manifest.tsv`
- `retrieval_summary.json`
- `evidence_assessment.tsv`
- `checksums.sha256`
- `raw/`

`evidence_assessment.tsv` begins header-only.

Transport does not populate human scientific assessments.

Raw source payloads remain untracked production evidence.

## Dynamic route boundary

The live seed run may discover and record:

- PMCIDs;
- supplementary links;
- repository links;
- documentation links.

It may not execute those discovered child routes.

They require later review and separate authorization.

## Recovery contract

The one-use authorization is consumed when the live run begins.

Once the first network attempt has occurred, staging evidence is preserved.

A failed/interrupted run must not be silently restarted.

An existing staging or final ASR000001 run blocks a second live invocation.

Recovery may finalize already-collected evidence without new network requests.

Unattempted tasks after an interrupted run require a separate continuation
authorization.

Already-attempted tasks must not be silently reissued.

## Future live authorization

The exact future authorization schema contains 27
fields.

Authorization status:

`AUTHORIZED_T000002_AUTHORITATIVE_SOURCE_SEED_RETRIEVAL_ONE_USE`

The future authorization must pin:

- the transport implementation freeze;
- this transport design freeze;
- the pre-network retrieval implementation freeze;
- the original retrieval design;
- T000002 completion;
- run identity `ASR000001`;
- target identity;
- exact 26-row queue SHA;
- all queue IDs RQ000001-RQ000026;
- the permitted three route codes;
- the network-policy SHA;
- exact pre-run ledger and review-packet SHAs;
- production root;
- explicit operator identity;
- one-use status.

It must explicitly state:

- all seed tasks must be considered;
- successful retrieval of every source is not required;
- dynamic child-route execution is unauthorized;
- scientific decisions are unauthorized;
- event-ledger mutation is unauthorized;
- review-packet mutation is unauthorized.

Network-policy SHA-256:

`201ea525346222c72483e775aa2c5109aa355af22a27ccc2df4e956c50c63e6a`

Future live-authorization contract SHA-256:

`8117f35c0c348afe49478a666aba05231eff1bc131eba19b6baafb3bd7d82360`

## Scientific boundary

Network transport may acquire and archive evidence.

It may not determine:

- landscape eligibility;
- exclusion;
- candidate-method status;
- directness;
- canonical publication;
- Wave 1 promotion.

The production event ledger remains untouched.

The B000001 review packet remains untouched.

All ten records remain `awaiting_source_escalation` until a later human
scientific-review and separately authorized superseding-event workflow.

## Authority boundary

This design creates:

- no network implementation;
- no live retrieval authorization;
- no production evidence directory;
- no scientific decision;
- no event authority.

## Next gate

`IMPLEMENT_T000002_AUTHORITATIVE_SOURCE_NETWORK_TRANSPORT_WITHOUT_LIVE_NETWORK_EXECUTION`
