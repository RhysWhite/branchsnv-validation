# Experiment 07 T000002 production completion and reconciliation

Status: `FROZEN_POST_T000002_COMPLETION`

## Purpose

This freeze records independent reconciliation of the second live Experiment 07
baseline scientific-screening transaction.

Transaction:

`T000002`

Published events:

`E000000002-E000000011`

Authorization commit:

`66c4a7c637a7f556161e14bf9c0a0dc4ab483bc3`

The transaction records ten source-escalation events.

It does not record terminal inclusion/exclusion decisions for positions 2-11.

## Production transition

Pre-transaction event count:

`1`

Post-transaction event count:

`11`

Pre-ledger SHA-256:

`33b49116d126f45cb54354b121eb69eb0abb212738794fef524a667ee0b2f2ba`

Post-ledger SHA-256:

`fb90d762d4fe9e81410816fe9403c735de138fe1614c11cb83993b40f2c63dff`

Post-ledger bytes:

`12714`

Live transaction timestamp:

`2026-09-25T09:30:12Z`

Derived state after T000002:

- ready: 94,611
- awaiting source escalation: 10
- complete: 1
- blocked metadata: 484

## Scientific state of positions 2-11

All ten target records received:

`source_escalation`

with:

`evidence_escalation_status = awaiting_source_escalation`

For all ten:

- record decision is blank;
- exclusion reason is blank;
- candidate-method flag is blank;
- supersedes-event ID is blank.

Therefore positions 2-11 are not terminally screened.

They require authoritative source review before a terminal scientific
disposition may be entered.

## Human provenance

Operator ID:

`Rhys`

Operator type:

`human_with_assistance`

The human review explicitly selected source escalation for all ten records.

No autonomous model disposition was entered.

## Local evidence snapshot

The source-escalation decisions were based on a frozen local evidence snapshot
that established bibliographic identity and citation provenance but did not
provide sufficient substantive primary/stable-authoritative source evidence for
terminal screening.

Evidence snapshot:

`results/07_comparative_landscape/baseline_scientific_screening_review_work/B000001/T000002_position_2_11_evidence/local_evidence_matches.json`

SHA-256:

`0f4d82e3c20eb8b97d984cb7a6cc96c63ea5ff88081e99c8fb7c81f48efff785`

Bytes:

`134372`

Exact pre-decision target-row snapshot:

`results/07_comparative_landscape/baseline_scientific_screening_review_work/B000001/T000002_position_2_11_evidence/exact_rows.tsv`

SHA-256:

`01f9bb29f5c4ddab68a7b8fc4cb32be119cfd12152744599196cface8541d56c`

Bytes:

`6979`

These two evidence artifacts are frozen as direct immutable evidence by this
completion checksum manifest.

## Human-reviewed packet

The working review packet remains future-mutable because the ten source
escalations require later resolution and positions 12-500 remain available for
future separately authorized review.

Its exact T000002 state is pinned rather than directly checksummed by path.

SHA-256 at T000002:

`09e08a25873e9a628a2c7900b82f384f7b5838bb166b89d412759fe92a9101d6`

Bytes:

`314642`

At this state:

- position 1 retains its completed T000001 terminal exclusion;
- positions 2-11 contain source-escalation proposals;
- positions 12-500 remain blank.

## Persisted proposal

Checkpoint proposal:

`results/07_comparative_landscape/baseline_scientific_screening_event_receipts/T000002/proposal.tsv`

SHA-256:

`ce1eb7e2bf7cb3ea4ab09e5b8137658173e5893ce8995c103c3d830c29266f1e`

Bytes:

`9994`

The proposal contains exactly ten rows in B000001 position order 2-11.

## Authorization checkpoint

Checkpoint authorization:

`results/07_comparative_landscape/baseline_scientific_screening_event_receipts/T000002/authorization.json`

SHA-256:

`5b5988b435b62a73420c8b728a362b4e9e98029bac85e75e6aa85ad4a1b649f4`

It is byte-identical to the tracked T000002 authorization artifact.

The one-use authorization has been consumed.

It provides no authority for another T000002 transaction.

## Receipt

Checkpoint receipt:

`results/07_comparative_landscape/baseline_scientific_screening_event_receipts/T000002/receipt.json`

SHA-256:

`21486cef8d49f3497b0fe9a2671061a31969f76acbc06be6cb142fa73190d271`

Bytes:

`2047`

Checkpoint status:

`COMPLETE`

Published:

`true`

Post-publication validation:

`true`

The checkpoint contains exactly:

1. `authorization.json`
2. `proposal.tsv`
3. `receipt.json`

## Append-only reconciliation

The current event ledger is an exact strict extension of the pre-T000002 ledger.

The exact current header plus historical E000000001 bytes reproduce the frozen
pre-T000002 ledger SHA-256.

Events E000000002-E000000011 are the only appended events.

E000000001 remains unchanged.

## Replay protection

A post-completion replay attempt failed closed because the continuation guard
detected:

`FINAL_CHECKPOINT_EXISTS`

The production ledger remained unchanged at the reconciled post-T000002 SHA.

## Mutable-artifact treatment

The production event ledger remains append-only and may change after future
separately authorized transactions.

Therefore this historical checksum manifest does not checksum
`event_ledger.tsv` by path.

Its exact T000002 SHA and byte count are frozen in this document and the
machine-readable completion artifact.

The B000001 review packet also remains future-mutable and is represented by its
exact T000002 SHA and byte count rather than a direct path checksum.

The T000002 checkpoint and the two local pre-escalation evidence snapshot files
are immutable historical evidence and are directly included in the checksum
freeze.

## Scientific boundary after T000002

At this freeze:

- production events: 11;
- completed baseline entities: 1;
- ready baseline entities: 94,611;
- awaiting-source-escalation entities: 10;
- blocked-metadata entities: 484;
- terminal exclusions: 1;
- source-escalation events: 10;
- retained candidate-method decisions: 0;
- new terminal decisions from T000002: 0;
- method assessments: 0;
- role assignments: 0;
- canonical-publication decisions: 0;
- Wave 1 promotions: 0;
- positions 2-11 require authoritative source review;
- positions 12-500 remain blank;
- positions 12-500 remain unauthorized.

## Authorization boundary

The T000002 positions-2-11 one-use authorization has been consumed.

No new production event is authorized by this completion freeze.

Resolution of the ten source-escalation events will require a separately frozen
authoritative-source retrieval/review workflow and separately authorized
superseding terminal events.

No source retrieval should precede the next design gate.

## Next gate

`DESIGN_T000002_AUTHORITATIVE_SOURCE_RETRIEVAL_AND_ESCALATION_RESOLUTION`
