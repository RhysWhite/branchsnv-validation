# Pre-review triage future review workspace v1 — generation authorization

Status: `FROZEN_ONE_USE_GENERATION_AUTHORIZATION_PRE_EXECUTION`

## Authorization

This freeze authorizes exactly one deterministic generation attempt for the
already-frozen future review workspace implementation.

Authorization ID:

`PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_GENERATION_001`

The authorization has not yet been exercised.

## Frozen implementation binding

Implementation checksum-manifest SHA-256:

`884c8e45ac89cdcd6631579b00be02cab664b8c644c58aec9c725e4d917e7449`

Active workspace-builder SHA-256:

`b347de8b56325a56b5bb62d000d567c367b75270aed1566bdd907463992c05a0`

Workspace-design checksum-manifest SHA-256:

`754288330069b576dff1e68c7c99c6fb57279c4860c3913818984bb6f57cb484`

Authorization JSON SHA-256:

`42fc9031cf1a684406b591fb976d6bd8cd3f3ac8d433a510f7a29f31fcf003ce`

The generation attempt is valid only with these exact identities.

## Authorized workspace

The authorized deterministic generation contains:

- frozen future-triage universe: **12,162**
- new human-review tasks: **12,156**
- prior carry-forwards: **6**
- priority review tasks: **5,477**
- residual review tasks: **6,422**
- manual review tasks: **257**
- priority packets: **11**
- residual packets: **13**
- manual packets: **1**
- total derived review packets: **25**
- maximum packet size: **500**

The six prior Wave 0 carry-forwards remain provenance-only carry-forwards and
must not be scientifically reassessed.

## Generation semantics

The frozen implementation must:

1. revalidate the frozen source identities;
2. verify that no future-triage entity has acquired an accepted scientific
   event;
3. require the canonical output root to be absent;
4. build the complete workspace in a temporary sibling staging directory;
5. validate exact schemas, packet membership, blank human-entry fields and
   checksums;
6. verify the production event ledger did not change during generation;
7. atomically publish the validated payload;
8. remove temporary staging residue.

## Scientific boundary

This authorization permits deterministic review-workspace generation only.

It does not authorize:

- scientific inclusion or exclusion;
- human scientific adjudication;
- reassessment of the six prior carry-forwards;
- new scientific B000xxx membership;
- cross-lane scientific priority inference;
- live scientific-event authorization;
- production-ledger mutation;
- reviewer exposure to raw continuous scores;
- reviewer exposure to selected candidate ID.

The generated review packets remain derived working artifacts rather than
authoritative scientific history.

## Exact confirmation

`GENERATE-FROZEN-FUTURE-REVIEW-WORKSPACE-V1`

## One-use boundary

A production invocation exercises this authorization whether it succeeds or
fails after entering the generation attempt.

It must not be silently reused.

If generation fails before a canonical workspace is frozen, the failure must
be recorded and a separately frozen replacement authorization must precede any
retry.

## Next gate

`EXECUTE_ONCE_FROZEN_PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_GENERATION_001`
