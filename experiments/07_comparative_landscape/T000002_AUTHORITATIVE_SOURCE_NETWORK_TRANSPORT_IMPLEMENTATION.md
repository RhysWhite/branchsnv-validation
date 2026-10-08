# Experiment 07 T000002 authoritative-source network transport implementation

Status: `FROZEN_PRE_LIVE_RETRIEVAL_AUTHORIZATION`

## Purpose

This freeze records implementation and hostile validation of the network
transport capability for the frozen T000002 authoritative-source seed
retrieval.

Parent transport-design commit:

`3312c68ed2b2a5e23769345cb457dddbfd32bcfe`

Network transport capability now exists.

Live network retrieval remains unauthorized.

## Frozen implementation identities

Transport:

`t000002_authoritative_source_network_transport.py`

SHA-256:

`eea4de31a7ac9eae2605c460df6951f706543111da637c215ca9a6a51988e47a`

Hostile tests:

`test_t000002_authoritative_source_network_transport.py`

SHA-256:

`44439a0f4b91f32add6871f74adaa35bd013344716a2277bbd06ad4f678c5dad`

Frozen network-policy SHA-256:

`201ea525346222c72483e775aa2c5109aa355af22a27ccc2df4e956c50c63e6a`

Frozen live-authorization-contract SHA-256:

`8117f35c0c348afe49478a666aba05231eff1bc131eba19b6baafb3bd7d82360`

Frozen seed retrieval queue SHA-256:

`04b758cb6feb7460811116efef9b38a509b5996f63ca30cf225d9cf75448c691`

Frozen target identity SHA-256:

`5970e1ec739b5b01c546e526c402d2f3a6e06e8f43aef0bfcd375e692bc2ab5e`

## Implemented transport controls

The transport implements:

- HTTPS GET-only retrieval;
- system TLS certificate validation;
- TLS hostname validation;
- DNS resolution before connection;
- public-address validation;
- connection pinning to the validated IP;
- rejection of IP-literal destination hosts;
- rejection of private, loopback, link-local, multicast, reserved and
  unspecified destination addresses;
- rejection of URL userinfo;
- rejection of non-default HTTPS ports;
- rejection of HTTP downgrade;
- NCBI same-host redirect enforcement;
- DOI public-HTTPS cross-host redirects;
- bounded redirect count;
- frozen request headers;
- no destination credentials;
- no persistent cookies;
- bounded response sizes;
- bounded retries;
- transport-attempt logging;
- response payload hashing;
- response byte counting;
- response-header recording;
- redirect-chain recording;
- deterministic seed-queue use;
- child-route discovery without child-route execution;
- retrieval evidence staging;
- atomic finalization;
- interrupted-run staging preservation;
- rejection of silent rerun when staging/final run exists.

## Hostile validation

Tests use injected fake resolver and transport adapters only.

They demonstrated:

- frozen network-policy identity reproduction;
- frozen live-authorization-contract identity reproduction;
- exact 26-task queue reproduction;
- valid public HTTPS destination acceptance;
- HTTP rejection;
- userinfo rejection;
- non-default-port rejection;
- IPv4-literal rejection;
- IPv6-literal rejection;
- loopback rejection;
- private-address rejection;
- link-local rejection;
- unspecified-address rejection;
- frozen PMID route construction;
- DOI percent encoding;
- NCBI cross-host redirect rejection;
- DOI public HTTPS redirect acceptance;
- DOI HTTP downgrade rejection;
- test-only synthetic authorization validation;
- complete fake 26-task retrieval;
- deterministic persisted seed queue;
- transport-only retrieval manifest generation;
- header-only evidence assessment;
- discovered PMC child routes recorded but not executed;
- evidence checksum verification;
- preservation of zero scientific decisions;
- interrupted-run recovery-state behavior;
- preservation of interrupted staging evidence;
- silent rerun rejection;
- rejection of untracked authorization for real live retrieval.

No real DNS or network request occurred during hostile testing.

## Production evidence boundary

Future live production root:

`results/07_comparative_landscape/t000002_authoritative_source_retrieval`

Frozen run ID:

`ASR000001`

At this freeze:

- production retrieval state: `NO_RUN`;
- production retrieval root exists: no;
- live authorization exists: no;
- live network retrieval performed: no.

## Scientific boundary

Production event count remains:

`11`

Current scientific state remains:

- ready: 94,611
- awaiting source escalation: 10
- complete: 1
- blocked metadata: 484

The production event ledger SHA remains:

`fb90d762d4fe9e81410816fe9403c735de138fe1614c11cb83993b40f2c63dff`

The B000001 review-packet SHA remains:

`09e08a25873e9a628a2c7900b82f384f7b5838bb166b89d412759fe92a9101d6`

No terminal disposition has been added.

No candidate-method decision has been added.

The transport is prohibited from modifying either the event ledger or review
packet.

## Capability versus authority

This freeze creates network capability but does not create live-network
authority.

The transport's live CLI requires the separately tracked one-use
authorization frozen by the transport-design contract.

An absent or untracked authorization fails before production-directory
creation or DNS/network activity.

The future authorization must be a separate one-file commit whose parent is
this implementation freeze.

## Next gate

`CREATE_T000002_AUTHORITATIVE_SOURCE_ASR000001_ONE_USE_LIVE_RETRIEVAL_AUTHORIZATION`

That authorization may grant only the frozen 26-task seed retrieval envelope.

It must not authorize:

- dynamic child-route execution;
- scientific decisions;
- event-ledger mutation;
- review-packet mutation.
