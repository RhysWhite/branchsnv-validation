# Experiment 07 T000001 production completion and reconciliation

Status: `FROZEN_POST_CANARY_COMPLETION`

## Purpose

This freeze records independent reconciliation of the first live Experiment 07
baseline scientific-screening transaction.

Transaction:

`T000001`

Event:

`E000000001`

Authorization commit:

`6a09448946a21f49d554e05382f5e9cf4e97e230`

No additional B000001 positions are authorized by this freeze.

## Production transition

Pre-transaction event count:

`0`

Post-transaction event count:

`1`

Pre-ledger SHA-256:

`d3ff9be1efe2b1237f616f25e702275ccc608577fa0ff8b301401a72900eb55f`

Post-ledger SHA-256:

`33b49116d126f45cb54354b121eb69eb0abb212738794fef524a667ee0b2f2ba`

Post-ledger bytes:

`1288`

Live transaction timestamp:

`2026-09-25T07:08:47Z`

Derived state after T000001:

- ready: 94,621
- awaiting source escalation: 0
- complete: 1
- blocked metadata: 484

## Scientific event

Entity:

`publication_component:citation:publication:doi:10.1001/archdermatol.2012.1817`

Baseline-row SHA-256:

`bb8ef2c1e0fd980a70884709d3085b8e44b5b425500d390ae943f638f1d08048`

Publication:

`Skin Examination Behavior`

DOI:

`10.1001/archdermatol.2012.1817`

PMID:

`22801744`

Event type:

`record_decision`

Decision:

`exclude`

Exclusion reason:

`unrelated_variant_or_data_type`

Candidate method:

`false`

Evidence escalation:

blank / not required.

Operator ID:

`Rhys`

Operator type:

`human_with_assistance`

The source evidence records a cross-sectional web-based study of skin
examination behaviour rather than a reusable sequence/SNP/genotype/phylogenetic
analytical method.

## Reviewed packet

The human-reviewed B000001 packet is an external working artifact and remains
future-mutable for later positions.

Its exact state at T000001 is therefore pinned by identity rather than included
as an immutable path in this checksum freeze.

Rows:

`500`

SHA-256 at T000001:

`bbaa8eeed4b60fa310434819dcf67ecf540d25112634818690bdb37cf5e0e286`

Bytes at T000001:

`306073`

Only position 1 contained proposed scientific input.

Positions 2-500 remained blank and undecided.

## Persisted proposal

Checkpoint proposal:

`results/07_comparative_landscape/baseline_scientific_screening_event_receipts/T000001/proposal.tsv`

SHA-256:

`a4f262c77d1a469996c388916febd465f4ee107f25be4598afcdd82a0148891b`

Bytes:

`1003`

The proposal contains exactly one row.

## Authorization checkpoint

Checkpoint authorization:

`results/07_comparative_landscape/baseline_scientific_screening_event_receipts/T000001/authorization.json`

SHA-256:

`b316feae227a6a5917fa77d64a0a72887931702ca3bb08ea85173ba7c8584e5d`

Bytes:

`2132`

It is byte-identical to the tracked authorization artifact.

## Receipt

Checkpoint receipt:

`results/07_comparative_landscape/baseline_scientific_screening_event_receipts/T000001/receipt.json`

SHA-256:

`adc7b410a08d29ff3141300a3e40ee3f4ced3dbf9bcbe9967ac5513b1ef51733`

Bytes:

`1706`

Receipt status:

`COMPLETE`

Post-publication validation:

`true`

The checkpoint contains exactly:

1. `authorization.json`
2. `proposal.tsv`
3. `receipt.json`

## Replay protection

A post-completion replay attempt failed closed because the frozen guard detected:

`FINAL_CHECKPOINT_EXISTS`

The production ledger remained unchanged at the reconciled post-T000001 SHA.

## Mutable-artifact treatment

The production event ledger is append-only and is expected to change after
future separately authorized transactions.

Therefore this historical checksum manifest does not checksum
`event_ledger.tsv` by path.

Instead, its exact T000001 post-state SHA and byte count are frozen in this
document and the machine-readable completion artifact.

Likewise, the 500-row review packet is a working review artifact that may later
receive proposed values for additional positions. Its T000001 identity is
frozen by SHA and byte count rather than by immutable-path checksum.

The T000001 checkpoint itself is treated as immutable evidence and is included
directly in the checksum freeze.

## Scientific boundary after T000001

At this freeze:

- production events = 1;
- complete baseline entities = 1;
- ready baseline entities = 94,621;
- B000001 terminal exclusions = 1;
- B000001 source-escalation events = 0;
- retained candidate-method decisions = 0;
- method assessments = 0;
- role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- positions 2-500 remain undecided;
- positions 2-500 remain unauthorized.

Scientific screening has now begun, but only for the single completed canary
entity.

## Authorization boundary

The one-use position-1 authorization has been consumed by T000001.

It provides no authority for another event.

No further live event may be entered until a separate post-canary continuation
design and authorization are frozen.

## Next gate

`DESIGN_CONTROLLED_B000001_POST_CANARY_CONTINUATION_AUTHORIZATION`
