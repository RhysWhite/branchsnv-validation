# Pre-review triage future text Wave B execution v1

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design defines the executable safety contract for the 40-request
Future Wave B OpenAlex fallback population.

It does not authorize network execution.

## Frozen population

Future Wave B contains exactly 40 OpenAlex exact lookups:

- 31 `exact_work_id -> work_by_openalex_id`;
- 8 `exact_doi -> work_by_doi`;
- 1 `exact_pmid -> work_by_pmid`.

The exact-PMID request is frozen Wave B request sequence 32.

## Transport boundary

The existing low-level exact transport already supports
`work_by_pmid`; it must remain byte-identical.

The historical development Wave B execution layer supports only
Work-ID and DOI routes and therefore must not be used unchanged for
this future population.

Future-specific guard and adapter implementations are required.

## Exact-PMID identity

A successful `work_by_pmid` response is checkpoint-eligible only when
the archived OpenAlex payload carries the exact requested PMID identity
under the future adapter's pinned normalization rules.

A missing or incompatible PMID identity is a fail-closed provider
identity mismatch.

The exact-PMID success, mismatch and not-found paths must be explicitly
hostile-tested before authorization is possible.

## Authorization boundary

No authorization is created by this freeze.

Future Wave B requires a separate explicit human authorization bound to
the final executable implementation commit.

The Future Wave A authorization cannot authorize this execution.

## Execution semantics

Requests execute sequentially in frozen manifest order with concurrency
1 and a maximum provider rate of 2 requests per second.

Partial archives, identity failures, non-checkpointing transport faults,
or unverifiable evidence halt execution. Automatic replay across an
ambiguous network-send boundary is forbidden.

Same-execution-ID durable-evidence recovery is permitted; a second
execution ID under the same one-use authorization is forbidden.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_FUTURE_WAVE_B_GUARD_ADAPTER_RUNNER_AND_LIVE_ENTRYPOINT_THEN_FREEZE_EXECUTABLE_COMMIT_BEFORE_SEPARATE_HUMAN_AUTHORIZATION`
