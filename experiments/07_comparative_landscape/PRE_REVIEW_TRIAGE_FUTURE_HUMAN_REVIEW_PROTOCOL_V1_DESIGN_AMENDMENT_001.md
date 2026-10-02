# Pre-review triage future human-review protocol v1 — design amendment 001

Status: `FROZEN_DESIGN_AMENDMENT_001`

## Purpose

This amendment clarifies only the downstream production-bridge contract.

The frozen human-review design correctly separates triage work order,
scientific review, review approval and live production authorization.

However, two production-bridge statements were stronger than the evidence
supports when interpreted as general rules for the future-review population.

The review protocol must not itself authorize or determine the shape of a
later production transaction.

## Review population

The frozen future-review workload contains:

- 12,156 new human-review records;
- 155 existing authoritative B batches;
- 3 B-batch subsets that happen to be contiguous;
- 152 B-batch subsets that are non-contiguous;
- 0 future-only complete 500-position B batches.

The triage packets are therefore human-review work ordering only.

They are not production batches, production tranches, or event transactions.

## Superseded interpretation

The original design contains statements equivalent to:

- a later bridge must satisfy the current contiguous transaction contract;
- production may use one transaction per existing batch or a valid contiguous
  tranche.

Those statements remain in the original frozen bytes for provenance, but this
amendment supersedes their interpretation as generally authorized future
transaction shapes.

## Normative production-bridge contract

The human-review protocol:

- does not authorize a production transaction shape;
- does not authorize live production;
- does not create new B membership;
- does not permit cross-batch transactions;
- does not permit direct triage-packet-to-production-proposal projection;
- does not permit decisions for unreviewed positions to be inferred.

Existing authoritative B membership remains unchanged.

A later bridge may use only explicitly reviewed and approved scientific
dispositions.

If the then-applicable production contract requires additional non-triage
positions to be reviewed before a valid transaction can be formed, those
positions require actual human review.

The eventual production transaction shape must be determined by the
then-applicable, separately frozen production authorization/execution contract.

This amendment therefore neither requires nor prohibits a future full-batch or
contiguous-tranche transaction where such a transaction is independently valid
under that later frozen contract.

## Scientific effect

None.

This amendment changes no:

- review entity;
- review order;
- packet schema;
- scientific disposition;
- carry-forward disposition;
- approval;
- production proposal;
- live authorization;
- event-ledger row.

Scientific review approval remains separate from live production authorization.

## Next gate

`FREEZE_TESTED_PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1_IMPLEMENTATION`
