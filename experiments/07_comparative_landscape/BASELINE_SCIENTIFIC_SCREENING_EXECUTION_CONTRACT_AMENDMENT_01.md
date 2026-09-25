# Experiment 07 baseline scientific-screening execution contract amendment 01

Status: `FROZEN_PRE_IMPLEMENTATION_AMENDMENT`

## Purpose

This append-only amendment corrects one operational assumption in the frozen
baseline scientific-screening execution design and implementation.

It does not alter the frozen scientific eligibility rules and does not make
any new scientific screening decision.

## Superseded operational assumption

The original execution contract required all eight historically adjudicated
initial Wave 0 anchors to map to eight distinct `ready` entities in the frozen
baseline before real batch generation could occur.

The subsequent frozen baseline-presence resolution demonstrated that this
assumption is too strong.

The historical anchor count and the number of baseline carry-forward targets
are not necessarily identical.

## Frozen evidence

The prior Wave 0 baseline-presence resolution establishes:

- historical prior anchors: 8;
- in-baseline canonical anchor publications: 7;
- out-of-baseline canonical anchor publications: 1;
- ambiguous anchor identities: 0.

The out-of-baseline prior anchor is:

- `W0A06`;
- `kSNP3.0`;
- canonical DOI `10.1093/bioinformatics/btv271`.

Its frozen prior adjudication remains authoritative.

There is no frozen baseline row to which that adjudication can be attached.

No substitute kSNP-family publication may inherit that adjudication.

## Amended prior-anchor invariant

The execution prerequisite is now:

> all eight historical prior anchors must have a frozen, unambiguous
> baseline-presence resolution.

A valid resolution may classify a historical anchor as either:

- `in_baseline`, with exactly one validated frozen baseline
  `screening_entity_id`; or
- `out_of_baseline`, with no baseline `screening_entity_id`.

For this frozen baseline, the required resolved state is exactly:

- 7 `in_baseline`;
- 1 `out_of_baseline`;
- 0 ambiguous.

The seven in-baseline entities receive historical carry-forward provenance.

The out-of-baseline anchor is accounted for in historical anchor provenance
but cannot receive, suppress, or replace any baseline record.

## Active screening population

The immutable baseline contains 94,629 `ready` entities.

Seven of those are canonical publications whose previous adjudications are
carried forward.

Therefore:

`94,629 - 7 = 94,622`

baseline entities require ordinary record-level screening.

The out-of-baseline W0A06 anchor is not subtracted from the baseline because
it is not a member of the baseline.

## Deterministic batching

After implementation of this amendment and successful validation of the
frozen resolution:

- active screening entities: 94,622;
- maximum batch size: 500;
- deterministic batch count: 190.

Batch construction remains:

1. start from frozen `ready` baseline entities;
2. exclude only the seven exact in-baseline carry-forward entity IDs;
3. retain all other baseline entities;
4. sort lexicographically by `screening_entity_id`;
5. partition sequentially into batches of at most 500;
6. hash exact ordered membership.

## Additional related discovery entities

Additional citation, registry or other discovery entities associated with an
initial anchor do not inherit the canonical publication's adjudication.

This includes same-DOI components that are distinct screening entities and
other members of the same software lineage.

They remain subject to ordinary source-backed record-level screening unless
separately resolved under a frozen rule.

## Implementation amendment requirement

The current frozen execution implementation requires exactly eight baseline
mappings and therefore remains fail-closed.

It must not be used to generate production batches under the amended contract.

The implementation amendment must:

1. consume and hash-verify the frozen prior-anchor baseline-presence
   resolution;
2. require exactly eight resolved historical anchors;
3. require exactly seven unique `in_baseline` mappings;
4. require exactly one `out_of_baseline` anchor;
5. require the out-of-baseline anchor to be W0A06 / kSNP3.0 /
   DOI `10.1093/bioinformatics/btv271`;
6. exclude only the seven mapped baseline IDs from active screening;
7. derive an active ready population of exactly 94,622;
8. derive exactly 190 batches at the frozen maximum size of 500;
9. fail closed on any ambiguous, missing, substituted or additional mapping;
10. continue to make no scientific decisions automatically.

## Scientific boundary

At this amendment freeze:

- new record-level scientific screening decisions = 0;
- scientific reassessments of prior anchors = 0;
- execution event rows = 0;
- real screening batches created = 0;
- method assessments = 0;
- role assignments = 0;
- canonical-publication decisions = 0;
- Wave 1 promotions = 0;
- frozen baseline remains unchanged;
- historical screening log remains empty.

## Normative precedence

This amendment overrides only the original operational requirement that all
eight historical anchors must map to eight baseline entities.

All other requirements of the frozen baseline scientific-screening execution
design and implementation remain in force unless explicitly amended later.

## Next gate

`IMPLEMENT_BASELINE_SCREENING_EXECUTION_CONTRACT_AMENDMENT_01_WITHOUT_DECISIONS`

The next gate may modify execution code and hostile tests to implement this
amended invariant.

It must not yet perform scientific screening.
