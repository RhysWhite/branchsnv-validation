# Experiment 07 post-retrieval reconciliation implementation

Status: `FROZEN_PRE_PRODUCTION`

## Scope

This record freezes the implementation of the Experiment 07
post-retrieval metadata-reconciliation design.

The implementation operates only on the previously frozen metadata-resolution
queue and completed retrieval archive.

It does not perform scientific screening.

It does not merge publication components.

It does not modify retrieval evidence.

## Implementation

The implementation is:

`post_retrieval_reconciliation.py`

The hostile/offline test suite is:

`test_post_retrieval_reconciliation.py`

The implementation is offline-only with respect to reconciliation.

The default CLI behaviour is dry-run computation.

No derived production output is written unless an explicit
`--write-output-root` is supplied.

## Frozen reconciliation behaviour

The implementation reproduces exactly 1,342 component-level reconciliation
states from 1,847 frozen assignments and 1,731 frozen logical lookups.

### Identifier states

The frozen expected identifier-state counts are:

- `identifier_conflict_hold`: 117
- `provider_identity_anchored`: 311
- `provider_identity_confirmed_unanchored`: 183
- `provider_identity_not_found`: 8
- `not_applicable`: 723

All 117 pre-existing identifier-conflict components remain conflict-held.

No identifier winner is selected for those components.

No components are merged.

For native-provider identities, exact DOI and/or PMID anchors are emitted only
when a successful self-confirming native-provider response contains no more
than one identifier in each publication-anchor namespace.

Multiple DOI or PMID anchors fail closed.

A successful native-provider lookup that does not self-confirm its requested
native identifier fails closed.

### Title states

The frozen expected title-state counts are:

- `title_resolved_exact`: 575
- `title_equivalent_variants`: 8
- `title_conflict_hold`: 2
- `title_unresolved`: 482
- `not_applicable`: 275

A single exact retrieved title may be emitted as `resolved_title`.

Equivalent title variants remain explicitly unselected; their exact source
strings are preserved.

Residual disagreement remains conflict-held.

Missing titles remain unresolved.

No title is inferred.

### PubMed focal-record boundary

PubMed identifier parsing is restricted to the focal record:

- primary `MedlineCitation/PMID` or `BookDocument/PMID`; and
- focal `PubmedData/ArticleIdList` or `PubmedBookData/ArticleIdList`.

Nested reference and correction identifiers are excluded.

The hostile tests explicitly verify this boundary.

## Output boundary

When later executed with an explicit output root, the implementation is
designed to produce derived reconciliation evidence only:

- `component_reconciliation.tsv`
- `reconciliation_evidence.tsv`
- `manifest.json`
- `checksums.sha256`

The retrieval archive cannot be selected as the derived-output root or contain
the derived-output root.

Existing non-empty output roots fail closed.

The production reconciliation output has not yet been created at this freeze.

## Hostile tests

The frozen hostile tests verify, at minimum:

- exact-title recovery;
- equivalent-title preservation without display-string selection;
- substantive title conflict holding;
- unresolved missing titles;
- identifier-conflict non-resolution despite apparently coherent evidence;
- exact native-provider DOI/PMID anchoring;
- confirmed-but-unanchored native identities;
- native-provider `not_found`;
- self-confirmation failure rejection;
- multiple DOI-anchor rejection;
- multiple PMID-anchor rejection;
- OpenAlex focal identifier parsing;
- OpenCitations focal identifier parsing;
- exclusion of nested PubMed correction/reference identifiers;
- protection of the retrieval archive from derived-output writes; and
- fail-closed detection of frozen-count drift.

## Production dry-run validation

Before implementation freeze, the implementation was run against the complete
real frozen retrieval archive without an output path.

It independently reproduced:

- 1,342 component rows;
- 1,847 evidence rows;
- 1,731 logical lookups;
- the complete frozen identifier-state distribution; and
- the complete frozen title-state distribution.

The dry-run made no network request and created no reconciliation output.

## Scientific boundary

At implementation freeze:

- `component_merge_performed = false`;
- `scientific_screening_performed = false`;
- `network_access_performed = false`;
- `raw_retrieval_archive_modified = false`;
- `screening_log.tsv` remains empty.

## Next gate

The next gate is:

`RUN_CONTROLLED_POST_RETRIEVAL_RECONCILIATION_PRODUCTION`

That run may create only derived reconciliation outputs using this frozen
implementation.

It must not modify the completed retrieval archive, merge components, or
perform scientific screening.
