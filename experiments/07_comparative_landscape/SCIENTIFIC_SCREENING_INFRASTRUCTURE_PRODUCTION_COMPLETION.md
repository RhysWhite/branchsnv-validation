# Experiment 07 scientific-screening infrastructure production completion

Status: `FROZEN_PRE_SCREENING`

## Scope

This completion freeze records the controlled production of the deterministic
pre-decision scientific-screening infrastructure.

No scientific screening decisions have been made.

## Frozen implementation

Production was generated from implementation commit:

`2e887383d37fbf091d6901864d373a4ec0491907`

The implementation and hostile tests had already been frozen before production.

## Production artifact set

Exactly eight production artifacts exist under:

`results/07_comparative_landscape/scientific_screening`

They are:

1. `baseline_screening_queue.tsv`
2. `source_escalation.tsv`
3. `method_assessments.tsv`
4. `method_evidence.tsv`
5. `canonical_publications.tsv`
6. `wave1_promotion_candidates.tsv`
7. `manifest.json`
8. `checksums.sha256`

Total production size:

`48,819,751 bytes`

## Baseline queue

The production baseline contains exactly:

- screening entities: 95,113
- publication entities: 94,898
- software-registry entities: 215
- ready: 94,629
- blocked_metadata: 484
- screenable: 94,629
- blocked_title_unresolved: 482
- blocked_title_conflict: 2

Queue SHA-256:

`97575b71c4607c3dcad893d90210f9132a83d0ae2e299ac2f1aef7e94f527d58`

## Scientific boundary

At completion:

- every queue scientific-decision field is blank;
- source-escalation rows = 0;
- method-assessment rows = 0;
- method-evidence rows = 0;
- canonical-publication rows = 0;
- Wave 1 promotion-candidate rows = 0;
- scientific screening decisions = 0;
- method assessments made = 0;
- new role assignments made = 0;
- Wave 1 promotions made = 0;
- historical screening log remains unchanged and empty.

The 484 metadata-blocked entities are not scientific exclusions.

## Reproducibility

The frozen implementation independently regenerated all eight production
artifacts byte-for-byte identically.

The frozen implementation also independently validated the production output.

## Upstream integrity

The following remained unchanged through production:

- discovery evidence;
- metadata-retrieval archive;
- post-retrieval reconciliation;
- frozen scientific-screening design;
- frozen scientific-screening infrastructure implementation;
- historical screening log.

## Next gate

`DESIGN_CONTROLLED_BASELINE_SCIENTIFIC_SCREENING_EXECUTION`

No scientific screening should begin until the execution procedure, batching,
decision capture, source-escalation handling, reviewer/operator provenance,
fail-closed validation, and completion criteria are explicitly frozen.
