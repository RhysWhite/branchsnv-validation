# Wave A transport-evidence adapter v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This design creates no live authorization and performs no network
activity.

## Why the adapter exists

The frozen exact-identifier transport is retained byte-for-byte.

Two gaps are handled above that transport:

1. OpenAlex successful responses must be explicitly validated against
   the exact requested Work ID or DOI before they are considered
   checkpoint-eligible.
2. Several transport failure outcomes return a status without writing
   the `terminal.json` required for verified terminal evidence.

The adapter does not rewrite those transport semantics. It validates
them and fails closed where the frozen evidence requirement cannot be
met.

## Checkpoint eligibility

Only two adapter outcomes may advance the Wave A guard:

- `verified_success`;
- `verified_not_found`.

Authentication failure, redirect failure, response-integrity failure,
retry exhaustion, identity mismatch, missing terminal archive, archive
verification failure, and unknown statuses halt execution without
advancing the guard checkpoint.

No automatic retry or automatic live resume after such a fault is
authorized by this design.

## OpenAlex identity

For exact Work-ID retrieval, the canonical Work token returned by
OpenAlex must match the requested Work token.

For exact DOI retrieval, `ids.doi` must be present and normalize to the
same DOI as the exact requested DOI.

A successful HTTP response that fails either comparison is
`provider_identity_mismatch`, not successful evidence.

## Pacing

The existing `ProviderPacer` remains authoritative for the two
requests-per-second provider bound.

The future runner must wrap the injected HTTP executor so that
`ProviderPacer.wait(request.provider)` executes immediately before
every underlying request initiation. This includes redirects as well as
initial requests.

## Evidence order

For checkpoint-eligible outcomes:

1. frozen manifest row;
2. exact transport request;
3. raw transport archive;
4. transport archive verification;
5. provider identity validation;
6. durable adapter evidence record;
7. Wave A guard checkpoint.

The guard may never be advanced before step 6 is durable.

## Next gate

Implement the pure adapter plus a mocked single-request runner.
Every test must use an injected synthetic executor. No real network
request, live authorization, scientific decision, model operation,
future scoring or production mutation is permitted.
