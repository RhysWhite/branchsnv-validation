# Pre-review triage future text live retrieval v1

## Status

`FROZEN_PRE_AUTHORIZATION`

This freeze creates no live-network or execution authority.

## Purpose

This artifact freezes the live-retrieval authority boundary for the exact
12,162-record supported future publication lane.

It does not perform retrieval, scoring, scientific screening, model fitting,
threshold selection, blind-validation review or production mutation.

## Frozen Wave A

Wave ID:

`TRIAGE_FUTURE_TEXT_LIVE_WAVE_A`

Frozen requests:

- 8,539 PubMed exact-PMID EFetch requests;
- 3,576 OpenAlex exact Work-ID requests;
- 47 OpenAlex exact DOI requests;
- 12,162 total first-hop requests.

Frozen request manifest SHA-256:

`90a5bc130b51305ff88b020a90a7fd9dc5c88f6dde190cf8752f630905facbec`

Execution remains serial in ascending request sequence.

Maximum initiation rate remains two requests per second per provider.

## Reuse boundary

The existing exact-identifier transport, normalizer and transport-evidence
adapter are reused unchanged.

The development Wave A guard is not reused.

The existing Wave A runner core is used only as an implementation template
because it imports the development-specific guard directly.

A future-specific guard, runner core and live entrypoint must therefore be
implemented and hostile-tested before authorization.

The reused adapter retains its historical logical lookup prefix
`triage_text_wave_a:`. This string is not authority-bearing; future archives
remain isolated by the distinct future output root.

## Authorization

This freeze is not an authorization.

A later explicit human authorization must bind the exact Wave A manifest,
this design hash, design parent commit, normalizer hash, transport-source
hashes, maximum request count, execution output root and execution commit.

Authorization must be one-use. Same-execution-ID resume is permitted only
from verified durable checkpoints. A second execution ID and completed
authorization replay must fail closed.

## Scientific boundary

No automated exclusion, future scoring, model fitting, threshold selection,
scientific screening decision, blind-validation scientific-content use or
production mutation is authorized.

## Wave B

Future Wave B does not yet exist.

It may be derived only after verified Future Wave A PubMed terminal evidence
establishes eligibility under the frozen fallback rules. It requires a
separate human authorization.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_FUTURE_WAVE_A_GUARD_RUNNER_AND_ENTRYPOINT_WITHOUT_NETWORK`

Design SHA-256:

`826e400faccf7481219cd04661a4e7e785903ec2876e1384ef5cfda3b10dd9e5`
