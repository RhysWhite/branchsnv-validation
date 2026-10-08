# Pre-review triage future text reconciliation v1

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design governs offline deterministic reconciliation of the frozen
12,162-record future pre-review text retrieval population after completion of
Future Wave A and Future Wave B.

## Architecture

A future-specific reconciliation module must be implemented.

The historical development reconciliation implementation is a semantic reference
only and must remain byte-identical. It is not directly executable for this
population because it is frozen around the historical 4,499-record population
and 25-request development Wave B.

## Frozen structural population

- total future input records: 12,162
- Future Wave A live requests: 12,147
- terminal offline rows: 15
- Future Wave B fallback rows: 40
- Future Wave B fallback reasons:
  - `abstract_absent`: 38
  - `verified_not_found`: 2
- Future Wave B routes:
  - `exact_work_id`: 31
  - `exact_doi`: 8
  - `exact_pmid`: 1
- Future Wave B retrieval:
  - transport `success`: 40
  - adapter `verified_success`: 40
  - provider identity `matched`: 40

## Deliberately unresolved before implementation

This design does not predeclare the final number of usable abstracts,
abstract-absent records, normalized-text rows, terminal-source status counts, or
canonical output hashes.

All 40 Future Wave B requests succeeded at the transport and identity layers,
but that does not establish whether each returned OpenAlex record contains a
usable abstract.

Those values may be determined only by applying the frozen normalizer during
future-specific deterministic reconciliation validation.

## Reconciliation semantics

The future implementation must retain the historical reconciliation semantics:

- exactly one resolution row per input record;
- resolution ordered by ascending retrieval-record index;
- only usable abstracts enter the normalized-text output;
- abstract absence, provider not-found and retrieval failure are provenance
  states, not scientific exclusion evidence;
- title-only records are not promoted to model text;
- frozen retrieval evidence must be independently verified before use.

Every Future Wave B raw archive must be reverified and every durable adapter
evidence object must reconstruct exactly before its body is normalized.

## Validation before canonical output

Implementation validation must use two independent temporary builds.

The two builds must be byte-identical.

Only after those builds establish the actual future reconciliation counts and
output hashes may an implementation freeze authorize a later controlled
canonical output write.

This design itself does not authorize canonical output generation.

## Safety boundary

No network access is permitted.

No Future Wave A or Future Wave B retrieval artifact may be modified.

No scientific screening decision, future score, model fit, threshold selection,
or blind-validation content use is permitted.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_FUTURE_TEXT_RECONCILIATION_V1_WITH_TWO_INDEPENDENT_TEMPORARY_BUILDS`
