# Experiment 07 ASR000002 validated-address failover and continuation guard

Status: `FROZEN_PRE_ASR000002_AUTHORIZATION`

Parent completion/continuation-design commit:

`9d94a84647d83f164f581abf56ed74037622e44b`

## Source state

ASR000001 is completed, checksum-valid production evidence and must not be
rerun.

## ASR000002 continuation

Run ID: `ASR000002`

Source run: `ASR000001`

Task count: `16`

Continuation queue SHA-256:

`d0a50b1610f0dcc5f61412cb2285b23391c38dd527890e1542c1b25ade7b3ca2`

Only NCBI tasks whose ASR000001 terminal transport state was
`transient_transport_error` are included.

No DOI task is included.

## Validated-address failover

Retry attempts rotate deterministically through addresses already accepted by
the frozen public-address / SSRF validation.

Each transport attempt records the actual validated address used.

No SSRF, TLS, HTTPS, redirect or timeout restriction is weakened.

## Transport module identity

The continuation guard caches exactly one process-wide imported instance of
the frozen transport module.

This preserves Python exception-class identity between:

- the guard;
- injected adapters;
- transport retry handling.

Hostile testing explicitly confirms that
`NetworkTransientError` has identical class identity throughout the
continuation process.

## Post-ASR000001 regression state

The existing transport hostile suite now requires:

- ASR000001 to remain checksum-valid;
- its consumed authorization to remain byte-identical;
- ASR000002 to remain absent before authorization;
- zero real DNS/network requests during hostile testing.

## Hostile validation

Tests demonstrate:

- exact 16-task continuation reconstruction;
- zero DOI tasks;
- stable transport-module / exception-class identity;
- synthetic transient failure on the first validated address;
- deterministic retry using the second validated address;
- attempted-address evidence retention;
- successful complete fake 16-task continuation;
- no scientific decisions;
- no real DNS/network access.

## Authority boundary

At this freeze:

- ASR000002 authorization exists: no;
- live execution authorized: no;
- dynamic child-route execution authorized: no;
- scientific decisions authorized: no;
- event-ledger mutation authorized: no;
- review-packet mutation authorized: no.

## Next gate

`CREATE_ASR000002_ONE_USE_CONTINUATION_AUTHORIZATION`
