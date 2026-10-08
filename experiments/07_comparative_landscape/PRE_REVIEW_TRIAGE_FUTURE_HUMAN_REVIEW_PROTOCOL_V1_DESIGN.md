# Pre-review triage future human-review protocol v1 design

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design defines how the frozen future-triage workspace may be used for
human scientific review without creating a second scientific batching system
or bypassing the existing baseline event-entry machinery.

No human scientific review is conducted by this design freeze.

## Frozen review universe

The frozen workspace contains:

- 12,162 records of triage provenance;
- 12,156 new human-review tasks;
- 6 prior carry-forwards not presented for reassessment;
- 25 lane-local review packets.

The new-review lanes remain:

- priority: 5,477;
- residual: 6,422;
- manual: 257.

## Triage order

Triage order is a human-work ordering aid only.

It does not:

- redefine scientific eligibility;
- create scientific batch membership;
- determine production event order;
- replace B000xxx membership;
- constitute scientific evidence.

Within each lane the frozen packet and row order is preserved.

No global ordering is introduced between the manual lane and scored lanes.

## Baseline mapping

All 12,156 review tasks retain their existing authoritative B000xxx identity.

They span 155 existing batches from B000010 through B000188.

No represented batch consists entirely of the future-triage review set.

Only 3 represented batches contain a contiguous future-position subset.

The remaining 152 contain non-contiguous future-position subsets.

Therefore the triage workspace cannot itself be interpreted as a valid
production transaction plan.

## Canonical packet immutability

The frozen 30-file pre-review workspace remains immutable.

Human review must not edit those canonical packet files.

Reviewed material must be written to a separate derived review area while
binding:

- source packet identity;
- source row identity;
- `screening_entity_id`;
- existing B000xxx batch;
- `position_in_batch`;
- `baseline_row_sha256`.

Rows may not be added, removed or reordered.

## Scientific review

Scientific fields remain human-entered.

For an initial review disposition the permitted event shapes remain:

- `record_decision`;
- `source_escalation`.

A terminal `record_decision` must be either:

- `retain_for_method_assessment`;
- `exclude`.

An exclusion requires exactly one frozen exclusion reason:

- `application_only_no_reusable_method`;
- `unrelated_variant_or_data_type`;
- `duplicate_record_same_method_no_distinct_capability`;
- `unsupported_by_primary_or_stable_authoritative_source`.

A terminal disposition requires an authoritative evidence-source locator.

If available evidence is insufficient for a terminal disposition, the review
must use source escalation, leave terminal-decision fields blank, set
`awaiting_source_escalation`, and explain the evidence deficiency.

The frozen high-recall rule remains unchanged: residual uncertainty is resolved
toward retention for method assessment rather than unsupported exclusion.

Triage lane, queue position, machine score or candidate-model output is not
scientific decision evidence.

## Review approval

Review work and review approval remain separate.

Review may be completed packet-by-packet.

An approved reviewed packet freezes its human dispositions but does not:

- create `proposal.tsv`;
- authorize event entry;
- mutate the production ledger;
- change B000xxx membership;
- authorize another review packet.

Before approval, the implementation must revalidate the exact frozen target
identity and confirm that no target has acquired a conflicting accepted event.

## Production bridge

Reviewed triage packets are not production proposals.

A later separately frozen bridge must project approved review dispositions back
onto existing B000xxx membership.

That bridge must:

1. group by existing B batch;
2. restore authoritative `position_in_batch` order;
3. preserve `baseline_row_sha256`;
4. combine only explicitly reviewed/approved scientific dispositions;
5. never infer decisions for unreviewed positions;
6. satisfy the current contiguous transaction contract;
7. obtain separate live production authorization;
8. preserve strict ledger-prefix semantics.

Because most triage subsets are non-contiguous, later production may require
review of additional non-triage positions before a valid existing B transaction
can be formed.

Historical non-contiguous B000001 superseding corrections are not generalized
into a new baseline-screening transaction shape.

## Mutable production ledger

The current audit found zero accepted-event overlap with the future workspace.

That observation is not pinned as a permanent ledger SHA requirement.

Unrelated append-only ledger advancement does not invalidate this review
protocol.

Target-specific accepted-event overlap must be rechecked:

- before review approval;
- again before any production projection or authorization.

## Scientific boundary

At this design freeze:

- human scientific review performed = false;
- scientific decisions made = false;
- review packets approved = false;
- proposals generated = false;
- new scientific batch membership created = false;
- live authorization created = false;
- production events created = false;
- production ledger mutated = false;
- prior carry-forwards reassessed = false.

## Next gate

`IMPLEMENT_PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_WITHOUT_SCIENTIFIC_DECISIONS_OR_PRODUCTION_MUTATION`
