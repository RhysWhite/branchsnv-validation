# Experiment 07 post-retrieval reconciliation completion

Status: `COMPLETE`

## Stage

The Experiment 07 post-retrieval metadata-reconciliation stage is complete.

The stage used the frozen reconciliation design and frozen implementation to
derive metadata-reconciliation evidence from the completed metadata-retrieval
archive.

No scientific screening was performed.

No publication components were merged.

No network access was performed.

The metadata-retrieval archive was not modified.

## Production outputs

The completed derived production directory contains exactly four files:

- `component_reconciliation.tsv`
- `reconciliation_evidence.tsv`
- `manifest.json`
- `checksums.sha256`

The production output contains:

- 1,342 component-level reconciliation rows;
- 1,847 assignment-level evidence rows; and
- evidence covering all 1,731 frozen logical lookups.

## Identifier reconciliation

The completed identifier-state distribution is:

- `identifier_conflict_hold`: 117
- `provider_identity_anchored`: 311
- `provider_identity_confirmed_unanchored`: 183
- `provider_identity_not_found`: 8
- `not_applicable`: 723

All 117 pre-existing identifier-conflict components remain conflict-held.

No identifier winner was selected for those components.

No component merge occurred.

## Title reconciliation

The completed title-state distribution is:

- `title_resolved_exact`: 575
- `title_equivalent_variants`: 8
- `title_conflict_hold`: 2
- `title_unresolved`: 482
- `not_applicable`: 275

The eight normalisation-equivalent title sets remain explicitly unselected.

The two substantive title conflicts remain unresolved.

The 482 components without retrieved title evidence remain unresolved.

No title was inferred.

## Reproducibility

Before completion freeze:

- the production checksum manifest validated;
- the frozen implementation independently validated the production output;
- a fresh independent reconstruction was created from the same frozen
  retrieval archive;
- all four reconstructed files were byte-identical to production.

## Retrieval evidence integrity

The completed metadata-retrieval archive remains checksum-valid and unchanged.

The reconciliation stage produced derived evidence only.

## Scientific boundary

At completion:

- `component_merge_performed = false`;
- `scientific_screening_performed = false`;
- `network_access_performed = false`;
- `raw_retrieval_archive_modified = false`;
- `screening_log.tsv` remains empty.

## Next gate

The next gate is:

`FREEZE_SCIENTIFIC_SCREENING_DESIGN_BEFORE_EXECUTION`

No scientific screening should begin before that design is explicitly frozen.
