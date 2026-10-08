# Wave A transport-evidence adapter v1 — amendment 01

## Status

`FROZEN_PRE_IMPLEMENTATION`

This amendment creates no network or execution authority.

## Why an amendment is required

Adapter v1 required an exact OpenAlex Work-ID equality check.

The existing frozen transport deliberately supports same-provider
redirects and already tests a request that redirects from one OpenAlex
Work to another canonical Work and completes successfully. Such a
redirect can represent provider-side canonicalisation or a merged Work.

Therefore a different returned Work ID is not, by itself, sufficient
evidence of an identity mismatch.

## Revised Work-ID rule

A direct exact Work-ID match remains valid.

A different final Work ID is also valid only when the archived raw
transport evidence demonstrates a contiguous, policy-valid OpenAlex
redirect from the exact requested Work to the final Work, and the final
request target, top-level response ID, and `ids.openalex` when present
all agree.

A different Work ID without that redirect provenance remains
`provider_identity_mismatch`.

## Raw archive bundle

The adapter evidence must additionally bind the complete raw lookup
archive using a deterministic bundle SHA256. This protects the redirect
metadata used to establish identity during later recovery.

## Process-restart pacing

The existing `ProviderPacer` is retained.

Because its state is process-local, the future runner must conservatively
wait 0.5 seconds before the first underlying request to each provider in
a new runner process. After that cold-start delay, `ProviderPacer` is
called immediately before every underlying request, including redirect
and retry requests.

## Next gate

Reimplement the pure adapter and mocked single-request runner against
the original v1 design plus this amendment. No real network execution or
live authorization is permitted.
