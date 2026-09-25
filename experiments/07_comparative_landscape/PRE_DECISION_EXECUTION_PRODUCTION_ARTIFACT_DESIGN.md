# Experiment 07 controlled pre-decision execution production-artifact design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design freezes the exact on-disk package for baseline scientific-screening
execution before any record-level screening begins.

Parent amendment-implementation commit:

`8ffff79c51a7ce439e314daa5ea721095ea16f60`

No execution-production artifacts exist at this design freeze.

## Immutable scientific baseline

Baseline screening queue SHA-256:

`97575b71c4607c3dcad893d90210f9132a83d0ae2e299ac2f1aef7e94f527d58`

Frozen ready entities:

`94,629`

Frozen metadata blockers:

`484`

Historical prior anchors:

`8`

In-baseline historical carry-forwards:

`7`

Out-of-baseline historical prior anchors:

`1`

Active entities requiring ordinary record-level screening:

`94,622`

## Deterministic batching

Maximum batch size:

`500`

Batch count:

`190`

First batch:

`B000001`

Last batch:

`B000190`

Final batch size:

`122`

Frozen batch-manifest SHA-256:

`f2cc2c7ccaf230a56f9aa27f991b12885b600338b68b81d660af895f48adbfe0`

Frozen ordered active-entity-ID SHA-256:

`d0970cbd5a582ce05585926bc1e81acba502b01a96acc4b84ab8db454a0ea4c1`

## Production root

Future execution production may write only beneath:

`results/07_comparative_landscape/baseline_scientific_screening_execution`

The directory must not pre-exist when controlled production begins.

Production must be constructed in a temporary sibling directory, fully
validated, and moved atomically into the final path only after every gate
passes.

## Exact production artifact set

Exactly eight files are permitted at genesis:

1. `batch_manifest.tsv`
2. `batch_membership.tsv`
3. `prior_anchor_carry_forwards.tsv`
4. `out_of_baseline_prior_anchor.tsv`
5. `event_ledger.tsv`
6. `event_ledger_genesis.json`
7. `manifest.json`
8. `immutable_checksums.sha256`

No per-batch copies are authoritative at this stage.

Any later review packet or user-facing batch worksheet must be derived
deterministically from the immutable membership table and frozen baseline
rather than becoming a competing source of batch membership truth.

## 1. batch_manifest.tsv

This is the authoritative 190-row batch summary.

Its schema is exactly the frozen base-engine batch-manifest schema:

`batch_id,batch_index,entity_count,first_screening_entity_id,last_screening_entity_id,ordered_entity_ids_sha256`

Rows are sorted by numeric batch index.

Required properties:

- exactly 190 rows;
- IDs exactly `B000001` through `B000190`;
- batches 1-189 contain exactly 500 entities;
- batch 190 contains exactly 122 entities;
- total entity count = 94,622;
- each row's ordered membership SHA is validated against
  `batch_membership.tsv`;
- serialized file SHA-256 must equal:

`f2cc2c7ccaf230a56f9aa27f991b12885b600338b68b81d660af895f48adbfe0`

## 2. batch_membership.tsv

This is the sole authoritative entity-to-batch membership table.

Schema:

- `batch_id`
- `batch_index`
- `position_in_batch`
- `global_active_index`
- `screening_entity_id`
- `baseline_row_sha256`

Rows are ordered by:

1. numeric `batch_index`;
2. numeric `position_in_batch`.

Indices are one-based.

Required properties:

- exactly 94,622 rows;
- exactly 94,622 unique `screening_entity_id` values;
- every entity is a frozen baseline `ready` entity;
- none of the seven carry-forward targets appears;
- no `blocked_metadata` entity appears;
- every `baseline_row_sha256` equals the frozen base engine's canonical
  baseline-row hash;
- concatenating entity IDs in table order reproduces the frozen semantic
  ordered-ID SHA-256:

`d0970cbd5a582ce05585926bc1e81acba502b01a96acc4b84ab8db454a0ea4c1`

The semantic ordered-ID hash is authoritative for membership ordering even
though the membership TSV itself will receive its own byte-level SHA during
implementation/production.

## 3. prior_anchor_carry_forwards.tsv

Exactly seven rows are written, ordered by `anchor_id`.

Schema:

- `anchor_id`
- `tool`
- `canonical_doi`
- `screening_entity_id`
- `baseline_row_sha256`
- `prior_anchor_decision`
- `prior_landscape_decision`
- `prior_confirmed_role`
- `record_decision`
- `candidate_method_flag`
- `mapping_basis`
- `source_resolution_sha256`
- `scientific_reassessment_performed`

Requirements:

- all seven rows come exactly from the frozen prior-anchor resolution;
- each maps uniquely to one frozen `ready` publication entity;
- `record_decision = retain_for_method_assessment`;
- `candidate_method_flag = true`;
- `mapping_basis = exact_canonical_doi_to_database_dedup_key`;
- `scientific_reassessment_performed = false`.

These are historical carry-forwards, not new scientific decisions.

## 4. out_of_baseline_prior_anchor.tsv

Exactly one row is written.

Schema:

- `anchor_id`
- `tool`
- `canonical_doi`
- `prior_anchor_decision`
- `prior_landscape_decision`
- `prior_confirmed_role`
- `baseline_presence_status`
- `screening_entity_id`
- `preservation_status`
- `source_resolution_sha256`
- `scientific_reassessment_performed`

The row must be exactly:

- anchor: `W0A06`;
- tool: `kSNP3.0`;
- DOI: `10.1093/bioinformatics/btv271`;
- baseline presence: `out_of_baseline`;
- screening entity ID: empty;
- preservation status:
  `prior_adjudication_preserved_without_baseline_row`;
- scientific reassessment: `false`.

No substitute kSNP-family baseline entity is permitted.

## 5. event_ledger.tsv

The event ledger uses exactly the frozen base-engine event schema:

`event_id,event_type,screening_entity_id,baseline_queue_sha256,baseline_row_sha256,batch_id,record_decision,exclusion_reason_code,candidate_method_flag,evidence_basis,evidence_source_locator,evidence_escalation_status,operator_id,operator_type,decision_timestamp_utc,supersedes_event_id,reviewer_id,review_status,adjudication_status,notes`

At genesis it contains the header only.

Genesis byte count:

`338`

Genesis SHA-256:

`d3ff9be1efe2b1237f616f25e702275ccc608577fa0ff8b301401a72900eb55f`

No event rows may be written during pre-decision execution production.

After genesis, this file is append-only and is the only artifact in this
package permitted to change during future record-level screening.

Actual event entry remains prohibited until a later explicit execution gate.

## 6. event_ledger_genesis.json

This immutable artifact records:

- event schema;
- genesis event-row count = 0;
- genesis byte count;
- genesis SHA-256;
- baseline queue SHA;
- amendment implementation commit;
- statement that the ledger is append-only after genesis;
- statement that event entry is not yet authorised.

It provides a permanent immutable reference for the ledger's initial state.

## 7. manifest.json

The immutable execution manifest records at least:

- status = `PRE_DECISION_EXECUTION_PRODUCTION`;
- schema version;
- frozen baseline queue SHA;
- all relevant upstream freeze hashes;
- historical prior-anchor count = 8;
- carry-forward count = 7;
- out-of-baseline anchor count = 1;
- blocked metadata count = 484;
- active screening entity count = 94,622;
- maximum batch size = 500;
- batch count = 190;
- final batch size = 122;
- frozen batch-manifest SHA;
- frozen ordered active-ID SHA;
- produced byte-level hashes for immutable TSV/JSON artifacts;
- event-ledger genesis SHA;
- event-ledger row count = 0;
- scientific decision count = 0;
- method assessment count = 0;
- role assignment count = 0;
- canonical-publication decision count = 0;
- Wave 1 promotion count = 0;
- network access = false.

## 8. immutable_checksums.sha256

This checksum ledger covers exactly these six immutable payload artifacts:

- `batch_manifest.tsv`
- `batch_membership.tsv`
- `prior_anchor_carry_forwards.tsv`
- `out_of_baseline_prior_anchor.tsv`
- `event_ledger_genesis.json`
- `manifest.json`

It deliberately does not include:

- itself; or
- `event_ledger.tsv`.

The event ledger is excluded because later authorised execution appends are
expected to change its byte content.

Its immutable genesis hash is instead pinned by both
`event_ledger_genesis.json` and `manifest.json`.

## Mutability classes

Immutable after successful production:

- batch manifest;
- batch membership;
- seven-row carry-forward table;
- one-row out-of-baseline anchor table;
- ledger genesis metadata;
- execution manifest;
- immutable checksum ledger.

Append-only after a future explicit event-entry gate:

- `event_ledger.tsv`.

No artifact may be silently rewritten.

## No authoritative current-state table

No `current_state.tsv` is produced at genesis.

Current record state is a deterministic projection of:

- the immutable baseline;
- the seven historical carry-forwards;
- the append-only event ledger.

A current-state report may later be regenerated as a derived artifact, but it
must not become a second primary decision record.

## Production validation

Before atomic publication of the execution package, the writer must verify:

- exact eight-file artifact set;
- exact baseline queue SHA;
- exact 8 = 7 + 1 anchor contract;
- exact 94,622 active entities;
- exact 190 batch rows;
- exact batch-manifest SHA;
- exact ordered active-ID SHA;
- exact batch coverage with no duplicates or omissions;
- exact exclusion of the seven carry-forward targets;
- exact exclusion of all 484 metadata blockers;
- exact baseline-row hashes;
- exact seven carry-forward rows;
- exact W0A06 out-of-baseline row;
- header-only event ledger;
- exact ledger-genesis SHA;
- zero scientific event rows;
- zero scientific decisions;
- zero network access;
- unchanged upstream evidence.

An independent rebuild into a temporary path must reproduce all eight genesis
artifacts byte-for-byte before production is considered valid.

## Scientific boundary

At this design freeze:

- production execution artifacts = 0;
- event-ledger rows = 0;
- record-level scientific decisions = 0;
- method assessments = 0;
- role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- event entry is not authorised;
- scientific screening has not begun.

## Next gate

`IMPLEMENT_CONTROLLED_PRE_DECISION_EXECUTION_PRODUCTION_WRITER_WITHOUT_DECISIONS`

The next implementation may create writer/validator code and hostile tests.

It must not create the production execution directory or enter any scientific
event.
