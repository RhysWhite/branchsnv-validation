# Experiment 07 metadata-retrieval live-execution authorization

Status: `FROZEN_PRE_LIVE_ENABLEMENT`

## Purpose

This amendment defines the authorization boundary for the first live execution
of the already frozen Experiment 07 metadata-resolution transport.

It does not alter the search corpus, citation graph, publication identities,
screening components, logical evidence queue, provider allocation, exact
identifier routes, transport mechanics, archive semantics, or scientific
screening rules.

## Frozen implementation dependency

Live execution may be enabled only from the separately frozen Amendment 34
implementation.

The frozen production evidence plan contains exactly:

- 1,342 attention components;
- 1,847 component-evidence assignments; and
- 1,731 unique logical lookup keys.

No new lookup may be introduced by live enablement.

## Production entry point

The only authorized production network entry point is:

`metadata_resolution_transport_archive.py --execute-live`

The lower-level transport module is not an authorized standalone production
runner.

All provider exchanges must therefore pass through the frozen archive/resume
layer.

## Independent authorization gates

Live execution requires all of the following simultaneously:

1. the source constant `LIVE_EXECUTION_ENABLED` is explicitly changed to
   `True` in a separately reviewed commit;
2. the command is invoked with `--execute-live`;
3. the environment contains exactly:
   `BRANCHSNV_ALLOW_METADATA_NETWORK=YES`;
4. `NCBI_EMAIL` is present and passes the frozen syntactic preflight;
5. all frozen dependency checksums pass; and
6. the exact frozen 1,731-lookup queue passes its full-set integrity gate.

Failure of any gate must occur before the first provider request.

## Credentials and contact configuration

`NCBI_EMAIL` is operational configuration and must not be committed or written
unredacted to retrieval evidence.

`OPENALEX_API_KEY` is optional.

`OPENCITATIONS_ACCESS_TOKEN` is optional.

No command used for authorization or preflight may print credential values.

The presence or absence of optional credentials may be reported only as a
boolean/status.

## First-network-request rule

No ad hoc connectivity probe, manual API request, `curl` test, or unarchived
credential test is authorized before production execution.

The first live provider exchange must itself be one of the frozen 1,731
logical lookups and must be written through the frozen raw-evidence archive.

This ensures that every live provider interaction relevant to this stage has
the same provenance and integrity guarantees.

## Production archive

The production archive root remains:

`results/07_comparative_landscape/metadata_resolution_retrieval`

For a fresh first run, this path must not already exist.

Once a production run has started, the archive becomes append-only through the
frozen resume logic. Existing accepted attempts must not be deleted, replaced,
or silently retried.

## Execution outcome

`COMPLETE` may be emitted only when all 1,731 frozen logical lookups terminate
as either:

- `success`; or
- `not_found`.

Any authentication, integrity, redirect, transport, retry-exhaustion, archive,
or validation failure blocks `COMPLETE`.

An `INCOMPLETE` run is retained as evidence and may be resumed only through the
frozen archive/resume mechanism.

It must not be converted to `COMPLETE` by manual editing.

## Failure handling

A provider failure does not authorize:

- fuzzy search;
- title search;
- an alternate provider;
- deletion of failed evidence;
- changing an identifier;
- changing a screening component; or
- bypassing the frozen transport.

Any later second-pass evidence plan must be separately derived, documented,
and frozen.

## Scientific boundary

Live metadata retrieval produces evidence for later reconciliation.

It does not itself:

- merge publication components;
- select a preferred identifier;
- consolidate software tools;
- determine comparator eligibility;
- perform scientific screening; or
- alter the frozen discovery universe.

Scientific screening therefore remains zero throughout live retrieval.

## Pre-execution verification

Immediately before the first live run, the operator must verify without making
a network request:

- clean Git worktree;
- expected live-authorization commit;
- current Amendment 34 implementation checksum manifest;
- source-contract amendment checksum manifest;
- frozen metadata-resolution queue checksum manifest;
- exact queue size of 1,731;
- `LIVE_EXECUTION_ENABLED = True`;
- `BRANCHSNV_ALLOW_METADATA_NETWORK=YES`;
- syntactically valid `NCBI_EMAIL`;
- optional credential presence without printing values;
- absence of an existing production retrieval directory for the first run;
- zero scientific screening decisions; and
- repository-neutrality gate.

## Post-execution verification

After the runner returns, the archive must be independently validated using the
frozen archive validator.

The resulting status, lookup counts, terminal counts, failure counts,
checksums, and provider outcome counts may then be reported.

Credentials and the unredacted NCBI contact address must never be displayed.

## Authorization scope

This amendment authorizes only the controlled transition from the frozen
offline implementation to its first archived live execution.

It does not authorize any transport redesign or scientific decision.

The actual code enablement must be a separate minimal commit after this
authorization contract is frozen.
