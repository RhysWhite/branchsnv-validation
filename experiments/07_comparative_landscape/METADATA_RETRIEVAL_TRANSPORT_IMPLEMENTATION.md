# Experiment 07 metadata-retrieval transport implementation

Status: `FROZEN_PRE_LIVE_EXECUTION_METADATA_TRANSPORT_IMPLEMENTATION`

## Purpose

This freeze records the offline implementation of the metadata-resolution
transport contract. It implements retrieval, validation, retry, redirect,
archival, resume, checksum, and completion behavior for the already frozen
logical evidence queue.

This layer is operational. It does not alter publication identity, consolidate
tools, perform scientific screening, or change comparator eligibility.

## Frozen upstream dependencies

The implementation consumes the frozen 1,731-logical-lookup evidence queue and
the previously frozen metadata-retrieval transport specification.

The branch-history provenance record immediately preceding this freeze
documents the local history rewrite that removed an excluded publication-venue
label from four archived provider snapshots while preserving the retrieval
evidence and its dependent checksum manifests.

No upstream scientific decision, search query, identity rule, evidence
assignment, or logical lookup was changed by that rewrite.

## Implementation files

- `retrieve_metadata_resolution_queue.py`
- `metadata_resolution_transport_archive.py`
- `test_metadata_resolution_transport.py`
- `test_metadata_resolution_transport_archive.py`

Exact SHA256 values are recorded in
`metadata_retrieval_transport_implementation_baseline.json` and
`metadata_retrieval_transport_implementation.sha256`.

## Implemented transport contract

The implementation preserves one primary provider operation per frozen logical
lookup. Batching is disabled.

It implements exact-identifier retrieval for OpenAlex, OpenCitations Meta, and
PubMed; provider-specific response validation; explicit HTTPS/provider-bounded
redirect handling; deterministic retry behavior; `Retry-After` handling;
per-provider pacing; raw-byte preservation; sensitive-header redaction;
immutable attempt evidence; interrupted-attempt recovery; terminal-evidence
reuse; checksum validation; and deterministic production ledgers.

Retryable HTTP statuses are limited to the frozen set. A logical lookup can
make at most five transport attempts. Redirect chains are explicitly archived
and limited to five hops.

Exact negative evidence is terminal. Successful completion requires every one
of the 1,731 frozen logical lookups to terminate as either `success` or
`not_found`. Transport, authentication, redirect, integrity, or retry-exhausted
failures remain explicit blockers to `COMPLETE`.

## Archive integrity

The production archive contract includes:

- immutable raw request/response evidence;
- `lookup_status.tsv`;
- `attempts.tsv`;
- `redirects.tsv`;
- `manifest.json`;
- `checksums.sha256`.

The three TSV ledgers are not trusted merely because their checksums match.
Validation independently regenerates their expected rows from archived raw
evidence and requires exact equality.

Earlier retry and redirect evidence is revalidated during resume and cannot be
silently re-blessed after corruption. Accepted evidence can be finalized after
an interrupted terminal-write step without issuing another provider request.

## Credential boundary

Optional provider credentials are supplied in request headers only and are
redacted from persisted request evidence. PubMed retrieval does not use an
NCBI API key under this frozen contract.

## Live-execution boundary

`LIVE_EXECUTION_ENABLED` is frozen as `False`.

The implementation and archive CLIs are network-inert by default. Production
live execution remains unavailable at this freeze and requires a separate,
explicitly reviewed post-freeze authorization change.

No production metadata retrieval has been performed during implementation
development or validation.

## Validation

Before this freeze:

- the complete current offline pre-screening stack passed;
- the complete historical Experiment 07 regression stack passed;
- all core metadata-transport synthetic tests passed;
- all archive/resume and hostile-integrity tests passed;
- the full frozen 1,731-lookup completion gate was exercised synthetically;
- derived TSV ledger forgery remained detectable even after checksum
  regeneration;
- live execution remained disabled;
- scientific screening remained empty;
- no production metadata-retrieval directory existed;
- frozen upstream design and queue checksum manifests remained valid;
- repository-neutrality validation passed for the working tree, refs, and
  reachable history.

## Interpretation

The numeric transport bounds in this layer are frozen operational controls, not
claims of biological or statistical optimality.

Freezing this implementation does not establish metadata-resolution results,
tool eligibility, comparator inclusion, citation-chain saturation, or any
scientific conclusion. Those later stages remain gated on successful,
auditable retrieval and subsequent identity/metadata adjudication.
