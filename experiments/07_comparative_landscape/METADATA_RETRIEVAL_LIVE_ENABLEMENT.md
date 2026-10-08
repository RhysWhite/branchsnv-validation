# Experiment 07 metadata-retrieval live enablement

Status: `FROZEN_LIVE_CAPABLE_PRE_FIRST_NETWORK_EXECUTION`

## Scope

This freeze implements the separate live-enablement step authorized by
Amendment 35.

The source-level constant `LIVE_EXECUTION_ENABLED` is now `True`.

This change does not by itself authorize a provider request.

## Remaining independent gates

Production execution still requires all of the following:

1. invocation through the frozen archive runner with `--execute-live`;
2. `BRANCHSNV_ALLOW_METADATA_NETWORK=YES`;
3. a syntactically valid `NCBI_EMAIL`;
4. frozen dependency verification;
5. exact 1,731-lookup queue validation; and
6. production archive/resume integrity checks.

The lower-level transport CLI remains outside the authorized production entry
point.

## Test changes

Tests that previously treated `LIVE_EXECUTION_ENABLED=False` as the primary
safety condition now test the independent runtime gates directly.

The offline regression suites were executed with the real network
authorization, NCBI contact value, OpenAlex credential, and OpenCitations
credential removed from the child-process environment.

No test therefore inherited the operator's production authorization.

Synthetic tests demonstrated that:

- missing explicit network authorization fails closed;
- missing or malformed NCBI contact information fails closed;
- those failures occur before production-directory creation; and
- the authorization helper accepts a fully valid synthetic configuration
  without performing network I/O.

## Frozen scientific state

This enablement does not alter:

- the 1,731 logical lookups;
- the 1,342 attention components;
- the 1,847 evidence assignments;
- provider allocation;
- identifiers;
- transport routes;
- retry or redirect behavior;
- pacing;
- response validation;
- archive/resume semantics;
- publication identity;
- tool consolidation; or
- screening rules.

Scientific screening remains zero.

## Network state

At this freeze boundary:

- source code is live-capable;
- no production retrieval directory exists;
- no production provider request has been made.

The first live provider exchange must occur only after this freeze is
committed and revalidated, and only through the frozen archive runner.
