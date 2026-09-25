# Experiment 07 T000002 authoritative-source retrieval implementation

Status: `FROZEN_PRE_NETWORK_TRANSPORT_DESIGN`

## Purpose

This freeze records the deterministic pre-network retrieval implementation for
the ten T000002 records currently awaiting authoritative-source escalation
resolution.

Parent authoritative-source design commit:

`bae2a0a6854df50a05163f7ffc8121379579fe3e`

The implementation validates and serializes the frozen retrieval seed queue but
contains no network transport capability.

## Frozen implementation identities

Runner:

`t000002_authoritative_source_retrieval.py`

SHA-256:

`f2ac303829b0d582737cde00a95384edc6cc64936dec601847258bc503f724eb`

Hostile tests:

`test_t000002_authoritative_source_retrieval.py`

SHA-256:

`b9f425285a1fc2cf446fd191fd41b61384af97d817a4c731fe0546c6daa4277d`

Deterministic seed retrieval queue SHA-256:

`04b758cb6feb7460811116efef9b38a509b5996f63ca30cf225d9cf75448c691`

The queue is deterministically reconstructed in memory and is not yet a
production retrieval artifact.

## Exact target

Target positions:

`2-11`

Current escalation events:

`E000000002-E000000011`

Target count:

`10`

Canonical target identity SHA-256:

`5970e1ec739b5b01c546e526c402d2f3a6e06e8f43aef0bfcd375e692bc2ab5e`

All ten records remain in:

`awaiting_source_escalation`

## Seed retrieval queue

The deterministic seed queue contains exactly 26 tasks:

- 8 PubMed authoritative-record routes;
- 8 PubMed-to-PMC discovery routes;
- 10 DOI publisher-article routes.

Every queue row:

- derives only from an identifier already frozen for the target;
- requires future network authority;
- carries no scientific decision authority;
- is marked `planned_pre_network_authorization`.

Positions 10 and 11 receive DOI routes only.

No PMID, duplicate relationship, repository, supplement or other route is
invented for them.

## Queue expansion boundary

The 26 tasks are seed routes only.

Additional routes may later be discovered from retrieved authoritative sources,
including:

- PMCID/full-text links;
- official supplementary files;
- official software repositories;
- official software documentation;
- stable software registry records.

Such expansion must be provenance-preserving and separately controlled.

It may not infer scientific conclusions.

## Retrieval output schemas

The implementation freezes schemas for:

- retrieval manifest;
- evidence assessment.

Retrieval manifest fields:

1. position_in_batch
2. current_event_id
3. screening_entity_id
4. source_id
5. source_class
6. authority_class
7. locator
8. retrieval_route
9. retrieved_at_utc
10. retrieval_status
11. http_status
12. content_type
13. payload_sha256
14. payload_bytes
15. storage_mode
16. local_path
17. license_or_access_note
18. notes

Evidence-assessment fields:

1. position_in_batch
2. current_event_id
3. screening_entity_id
4. source_id
5. evidence_question
6. evidence_present
7. evidence_locator
8. evidence_excerpt_or_summary
9. human_reviewer
10. assessment_status
11. notes

## Hostile validation

The implementation has demonstrated:

- exact ten-record target validation;
- reproduction of the frozen target-identity SHA;
- deterministic 26-task queue construction;
- byte-identical independent queue serialization;
- exact route distribution;
- exact queue-ID ordering;
- rejection of missing tasks;
- rejection of out-of-scope positions;
- rejection of scientific-decision authority in retrieval rows;
- rejection of unknown routes;
- rejection of current-event tampering;
- rejection of target-entity tampering;
- rejection of baseline-row tampering;
- preservation of positions 10 and 11 without inferred duplicate handling;
- preservation of the production ledger;
- preservation of the B000001 review packet;
- absence of the production retrieval root.

## Network boundary

The runner contains no network-capable imports.

Its live-network action raises:

`NetworkExecutionNotAuthorizedError`

with no production retrieval directory creation.

At this freeze:

- network transport implemented: no;
- live network retrieval authorized: no;
- production retrieval directory exists: no;
- scientific decisions allowed: no;
- production event mutation allowed: no.

## Scientific boundary

Production event count remains:

`11`

Current states remain:

- ready: 94,611
- awaiting source escalation: 10
- complete: 1
- blocked metadata: 484

No terminal disposition has been added for positions 2-11.

No source retrieval has occurred.

## Next gate

`DESIGN_T000002_AUTHORITATIVE_SOURCE_NETWORK_TRANSPORT_AND_LIVE_RETRIEVAL_AUTHORIZATION`

The next gate must keep transport capability, live authorization and scientific
resolution logically separate.

No live retrieval should occur merely because transport code exists.
