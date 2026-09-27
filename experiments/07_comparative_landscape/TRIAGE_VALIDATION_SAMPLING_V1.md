# Triage validation sampling v1

## Status

`FROZEN_BLIND_SAMPLE_MEMBERSHIP_NO_LABELS`

This artifact freezes a blind probability sample for later validation of
the scalable Experiment 07 scientific-triage layer.

It does not contain validation labels and it does not create scientific
decisions or production authority.

## Population

- Frozen active membership: 94,622
- Current terminal production entities: 2,000
- C000001 development entities: 2,500
- Blind validation sampling universe: 90,122
- Stage-1 validation sample: 2,000

The 2,500 C000001 human-reviewed entities are development data only and are
excluded completely from the validation sample.

## Sampling

The remaining 90,122 entities are stratified by frozen global active index
in 5,000-record strata. Allocation is proportional to stratum population
using deterministic largest remainders.

Within each stratum, records are selected by a SHA256 rank pinned to the
frozen queue, membership, production-ledger and C000001-freeze identities.

Titles, DOI prefixes, publisher identity, keywords, citation provenance and
future model scores do not influence selection.

An independent deterministic SHA256 ordering is used for eventual human
review so that records are not reviewed in active-index/DOI order.

## Validation discipline

The validation sample is frozen before development of the scalable triage
model.

Validation labels must not be used to train, tune or choose the triage
model or its threshold.

Stage 1 contains 2,000 records. If fewer than 60 retained-positive records
are found during later blinded review, a supplemental probability sample
will be drawn from the remaining unsampled universe before final recall
interpretation.

## Authority

This sampling freeze:

- creates no scientific screening decision;
- creates no event-ledger entry;
- creates no live authorization;
- does not modify the baseline queue;
- does not modify active batch membership;
- does not authorize or execute C000001.
