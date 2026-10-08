# Wave B implementation freeze v1

Status: **FROZEN_PRE_AUTHORIZATION**

This freeze records the exact offline-tested implementation for
`TRIAGE_TEXT_LIVE_WAVE_B`.

It creates **no authorization** and grants **no network execution authority**.

## Frozen upstream

- Execution design SHA256: `4a607178762e9e884f430b8fe1c47d078408b5a51e4e47701f2f4302ab5ca2ca`
- Request manifest SHA256: `f099f86cce2321ab07d639aeef557014585faf49e2306a09f3fe40119535f0a6`
- Derivation SHA256: `a58356439478ca27a48c3967dbbab6a16b275987dc4af7b19f67dd430eeab32b`
- Normalizer SHA256: `cbe66fc9ab406fa5ee3745e099c16250c404a949c0f301e40a7397c285dc459d`
- Implementation design SHA256: `8a86d72137dbaa97c5f4996a89a8b4ae835d466e6e8871871a30742537a71681`

## Frozen execution scope

Wave B contains exactly 25 OpenAlex requests in frozen manifest order:

- 21 exact OpenAlex Work-ID requests
- 4 exact DOI requests

No PubMed request, search/list endpoint, Crossref lookup, or ad hoc probe is
permitted.

Execution remains serial with concurrency 1, a maximum of two OpenAlex
requests per second, and a 0.5-second cold start before the first OpenAlex
request.

## Recovery and evidence boundary

The implementation retains the fail-closed recovery contract:

- request intent is durably evidenced before network execution;
- verified terminal evidence is required before checkpointing;
- ambiguous or partial network intent is not automatically reissued;
- only the same execution ID may resume;
- runtime authorization and repository invariants are rechecked;
- a cross-process lock prevents concurrent use of the same authorization;
- credential values must not appear in durable evidence.

## Test freeze

The frozen Wave B implementation passed:

- 17 focused/static tests;
- 20 live-hostile tests;
- 37 Wave B tests total.

The unchanged Wave A stack also passed its 63 regression tests:

- 13 guard tests;
- 26 adapter/runner tests;
- 24 live-entrypoint hostile tests.

## Preservation boundary

Wave A implementation files and the low-level transport remain byte-identical
to their previously frozen hashes. Production mutation is not permitted.
Blind validation content has not been scientifically inspected or used.

## Authorization boundary

This freeze does not create an authorization file, claim, state, completion
receipt, or network authority.

A later Wave B authorization, if explicitly approved by a human, must bind the
exact git HEAD containing this freeze and must remain untracked at execution.

The next gate is therefore:

**commit the exact frozen implementation/test/freeze set, record the resulting
HEAD, and stop before authorization.**
