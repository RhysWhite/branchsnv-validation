# Experiment 07 authoritative-source network transport implementation amendment 01

Status: `FROZEN_PRE_REPLACEMENT_LIVE_RETRIEVAL_AUTHORIZATION`

## Reason for amendment

The frozen network-transport design correctly specified:

- connect timeout: 10 seconds;
- read timeout: 30 seconds;
- per-attempt wall-time limit: 60 seconds.

The first network-transport implementation used the read timeout for connection
setup and did not independently enforce the 60-second per-attempt wall-time
limit.

This discrepancy was identified before any live network retrieval.

## Prior authorization

The prior one-use authorization commit was:

`eb93edfc30ae29ce79eb0ca1bf1c086d92dea2f3`

Authorization SHA-256:

`20687900cdf36124fdc1c2d791c604507ff9048558055be3b9cec71bdd7ddd19`

Authorization bytes:

`2314`

It was never consumed.

No ASR000001 production directory was created.

No real DNS lookup or network retrieval occurred under that authorization.

The authorization is retained as historical evidence but is
`SUPERSEDED_BEFORE_USE` by this implementation amendment.

A replacement authorization is required after this amendment freeze.

## Original implementation

Original implementation commit:

`46c45aa851832810abe694b4f33e34636d7486a6`

Original implementation-freeze SHA-256:

`80a68505bcef25e0fef58053d7f40e6c097b61806357dfb065883aac2f0f8d63`

## Amended controls

The amended implementation separately enforces:

- TCP connect timeout of 10 seconds;
- read/TLS-I/O timeout of 30 seconds;
- per-attempt wall-time limit of 60 seconds.

The effective connect and read timeout supplied to each request is additionally
clamped to the remaining per-attempt wall-time budget.

The wall-time limit is measured through the injected monotonic clock and has
been hostile-tested without real network activity.

## Amended identities

Transport SHA-256:

`7830fea6fc9369609fe6ff0b7dc5392c714b23110d111480c068f5365754994c`

Hostile-test SHA-256:

`33d71d52a143f7da498988c92d8f105b88993a5ebdf9e79573d1abf5a85ebe7f`

Frozen network-policy SHA-256 remains:

`201ea525346222c72483e775aa2c5109aa355af22a27ccc2df4e956c50c63e6a`

Frozen live-authorization-contract SHA-256 remains:

`8117f35c0c348afe49478a666aba05231eff1bc131eba19b6baafb3bd7d82360`

## Scientific and production boundary

Production event-ledger SHA-256:

`fb90d762d4fe9e81410816fe9403c735de138fe1614c11cb83993b40f2c63dff`

B000001 review-packet SHA-256:

`09e08a25873e9a628a2c7900b82f384f7b5838bb166b89d412759fe92a9101d6`

Production events remain 11.

Ten records remain awaiting source escalation.

No scientific decision, event-ledger mutation or review-packet mutation has
occurred.

ASR000001 remains unexecuted.

## Authorization boundary

The historical authorization is not valid for the amended implementation.

The next gate must replace the canonical authorization JSON in a new
single-file commit whose parent is this amendment freeze.

No live retrieval may occur before that replacement authorization validates.

## Next gate

`REPLACE_ASR000001_ONE_USE_LIVE_RETRIEVAL_AUTHORIZATION_AFTER_TRANSPORT_AMENDMENT_01`
