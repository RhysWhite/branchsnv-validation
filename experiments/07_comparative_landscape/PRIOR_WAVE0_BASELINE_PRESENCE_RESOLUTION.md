# Experiment 07 prior Wave 0 baseline-presence resolution

Status: `FROZEN_PRE_EXECUTION_CONTRACT_AMENDMENT`

## Purpose

This freeze resolves how the eight previously adjudicated initial Wave 0
canonical anchor publications intersect the frozen 95,113-entity baseline.

No new scientific screening decision is made.

## Frozen prior-anchor evidence

The eight prior anchors remain those already frozen under the citation-anchor
screening and Wave 0 citation-chaining protocol.

Their prior source-backed adjudications remain authoritative.

The canonical publication of each prior anchor was matched against the frozen
baseline using exact canonical DOI identity only.

No fuzzy-title, name-only or semantic mapping was used.

## Result

Of the eight historical canonical anchor publications:

- 7 occur as exactly one `ready`, database-derived publication component;
- 1 is absent from the frozen baseline;
- 0 are ambiguous.

The seven in-baseline canonical publications may therefore receive historical
carry-forward provenance rather than duplicate scientific screening.

The out-of-baseline canonical publication is:

- anchor: `W0A06`
- tool: `kSNP3.0`
- canonical DOI: `10.1093/bioinformatics/btv271`

No baseline screening entity carries that DOI.

Its prior anchor adjudication remains valid historical evidence, but there is
no baseline row to which that adjudication can be attached.

No substitute kSNP publication is permitted.

## kSNP-related baseline records

Other kSNP-family records in the baseline are distinct discovery entities.

They do not inherit the W0A06 adjudication merely because they concern the
same software lineage or share the term kSNP.

They remain subject to ordinary source-backed record-level screening.

## Derived execution population

Frozen baseline ready count:

`94,629`

In-baseline prior canonical anchor publications:

`7`

Therefore active ready entities requiring ordinary record-level screening:

`94,622`

At the frozen maximum batch size of 500:

`190` deterministic batches are required.

The 484 `blocked_metadata` entities remain unchanged and remain full-baseline
completion blockers.

## Scientific boundary

This resolution:

- does not modify any prior anchor adjudication;
- does not create a new record-level screening decision;
- does not screen any additional kSNP entity;
- does not alter the baseline queue;
- does not create execution batches;
- does not perform method assessment;
- does not assign roles or directness;
- does not select canonical publications;
- does not promote Wave 1 anchors.

## Next gate

`AMEND_BASELINE_SCREENING_EXECUTION_CONTRACT_FOR_OUT_OF_BASELINE_PRIOR_ANCHOR`

The frozen execution design and implementation currently require exactly eight
baseline carry-forward mappings.

That assumption is now demonstrated to be too strong.

The next amendment must distinguish:

1. eight historical prior anchors;
2. seven in-baseline carry-forward mappings; and
3. one out-of-baseline prior canonical anchor.

Batch generation must remain prohibited until that amended contract and its
implementation are frozen.
