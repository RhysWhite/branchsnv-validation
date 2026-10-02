# Pre-review triage future review workspace v1 — design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design defines a deterministic human-review workspace overlay for the
already-frozen future-triage queue.

It does not create a second scientific-screening universe.

The existing baseline `screening_entity_id`, existing B000xxx batch membership,
and existing append-only scientific-screening event ledger remain authoritative.

## Frozen source universe

The future-triage universe contains exactly **12,162** publication entities.

All 12,162 already belong to the frozen baseline scientific-screening universe.

Exactly **6** are previously adjudicated Wave 0 anchors represented by the
existing `prior_anchor_carry_forwards.tsv`.

Those six retain their frozen prior adjudications and must not receive a new
record-level scientific reassessment.

The resulting new human-review workload is therefore exactly:

**12,156 records**

## Review-work lanes

The new-review workload is:

- priority scored: **5,477**
- residual scored: **6,422**
- unscored manual review: **257**

The six prior carry-forwards remain represented in frozen priority-lane
provenance but are absent from new review work.

## Derived work packets

Review work is partitioned only for human workload management.

Maximum packet size:

**500 records**

Lane-local packet structure:

- priority: **11 packets**
  - 10 × 500
  - 1 × 477
- residual: **13 packets**
  - 12 × 500
  - 1 × 422
- manual: **1 packet**
  - 1 × 257

Total:

**25 derived review-work packets**

These are not new scientific B batches.

Packet numbering is lane-local.

No single global ordering is created across all three lanes.

In particular, no relative priority is invented between the manual-review lane
and either scored lane.

## Existing scientific batch membership

Every new-review entity remains bound to its existing immutable:

- `batch_id`
- `batch_index`
- `position_in_batch`
- `global_active_index`
- `baseline_row_sha256`

The existing B000xxx membership remains the only authoritative scientific batch
membership.

The review-work overlay does not modify it.

## Review ordering

Within each lane, work follows the already-frozen future-triage
`queue_position`.

The overlay may therefore change human work order relative to baseline batch
order without changing scientific identity or scientific batch membership.

Human review work and live production-event authority remain separate.

Any later accepted scientific event must still be projected back to the
record's existing B000xxx context and pass the separately frozen production
authorization machinery.

## Evidence presented for review

The workspace may expose:

- stable screening entity identity;
- retrieval record index;
- frozen lane and queue position;
- existing B000xxx membership provenance;
- baseline row SHA-256;
- opaque retrieval candidate-row SHA-256;
- publication identifiers;
- retrieval/provider provenance;
- abstract status;
- normalized title and abstract where available;
- baseline title/name metadata where available.

`candidate_row_sha256` is retained only as opaque retrieval provenance.

It is not equivalent to `baseline_row_sha256` and no equality relationship is
asserted.

## Model-information boundary

Reviewer-facing workspace artifacts must not expose:

- raw `continuous_score`;
- `selected_candidate_id`.

The deterministic lane and queue position may be used for workload ordering.

They must not be treated as scientific evidence for inclusion or exclusion.

## Human-entry fields

Every generated review packet must begin with blank fields for:

- `proposed_event_type`
- `proposed_record_decision`
- `proposed_exclusion_reason_code`
- `proposed_candidate_method_flag`
- `evidence_basis`
- `evidence_source_locator`
- `evidence_escalation_status`
- `notes`

No scientific decision may be pre-populated.

## Prior Wave 0 carry-forwards

The six prior anchors remain frozen carry-forwards.

Their existing record-level disposition is:

`retain_for_method_assessment`

Their prior method/landscape evidence remains authoritative.

`scientific_reassessment_performed = false` must remain unchanged.

They are represented in workspace provenance but not presented as new review
tasks.

## Planned output root

A later separately frozen implementation may construct:

`results/07_comparative_landscape/pre_review_triage_future_review_workspace_v1`

Planned artifacts are:

- `review_work_membership.tsv`
- `prior_carry_forwards.tsv`
- `packet_manifest.tsv`
- `workspace_manifest.json`
- `packets/priority_001.tsv` ... `packets/priority_011.tsv`
- `packets/residual_001.tsv` ... `packets/residual_013.tsv`
- `packets/manual_001.tsv`
- `checksums.sha256`

Generation is not authorized by this design freeze.

## Production boundary

This design creates no:

- review workspace output;
- scientific decision;
- scientific reassessment;
- new B000xxx identity;
- new scientific batch membership;
- live authorization;
- production event;
- transaction checkpoint;
- production-ledger mutation;
- cross-lane priority inference.

The existing append-only scientific-screening ledger remains authoritative.

## Generation-time fail-closed checks

A later implementation must verify immediately before generation that:

- the frozen triage universe remains exactly 12,162;
- exactly six future entities remain prior carry-forwards;
- exactly 12,156 entities remain active new-review targets;
- no target future entity has acquired an accepted scientific event;
- existing baseline membership remains unchanged;
- all six carry-forwards retain their frozen prior disposition;
- review packets contain no raw model score;
- review packets contain no selected candidate ID;
- every proposed scientific field is blank;
- no production ledger mutation occurs.

The current whole-ledger SHA is recorded only as design-freeze provenance.

Because the existing ledger is append-only, unrelated baseline screening may
legitimately advance before workspace generation. The generation gate must
therefore re-check record-level overlap rather than requiring the whole ledger
SHA to remain unchanged.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_WITHOUT_SCIENTIFIC_DECISIONS_OR_PRODUCTION_MUTATION`
