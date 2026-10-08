# Experiment 07 cross-stage screening-entity implementation

Status: FROZEN_OFFLINE_CROSS_STAGE_IMPLEMENTATION_CANDIDATE

## 1. Purpose

`cross_stage_screening_entities.py` implements the offline cross-stage
screening-entity construction specified by the already-frozen Experiment 07
identity and unified-screening design.

It combines:

- database-derived publication screening entities;
- citation-derived provisional publication identities; and
- database-derived software-registry screening entities.

This is an implementation layer, not a new scientific-method amendment.

## 2. Frozen dependency

The implementation depends on the previously frozen
`screening_entity_identity.py`.

It verifies that dependency against the exact SHA-256 of the implementation
frozen at commit `c62452570d1b0dd922b5d83ada3eedb0626d303e`.

Dependency drift fails closed.

## 3. Scope

The implementation performs:

- conservative citation-to-database publication linkage;
- cross-stage conflict preservation;
- publication-component construction;
- independent software-registry component construction;
- bidirectional use of already-frozen title metadata;
- propagation of unresolved/conflict state;
- construction of pre-screening attention reasons;
- deterministic ordering; and
- membership/provenance validation.

It does not:

- perform network requests;
- enrich metadata externally;
- resolve identity conflicts;
- merge different DOI identities through PMID;
- perform scientific relevance screening;
- assign software/method identities;
- assign analytical roles;
- select canonical publications;
- modify frozen discovery corpora; or
- write production results.

## 4. Automatic cross-stage linkage

Automatic publication linkage is restricted to:

1. exact DOI when available PMID evidence does not identify a different
   database publication entity; or
2. for a DOI-less citation entity only, exact PMID when that PMID maps to
   exactly one database publication entity.

A citation DOI that is absent from the database is not replaced by another
database DOI merely because the PMID matches.

A DOI/PMID disagreement is retained as explicit cross-stage conflict evidence.

## 5. Many-to-one linkage

More than one citation provisional identity may safely converge on one database
publication when the independent identifiers are compatible.

In the frozen corpus, two database publications each receive two citation
provisional identities:

- one DOI-based citation identity; and
- one DOI-less exact-PMID citation identity.

This does not merge different database publication identities.

## 6. Cross-stage conflicts

Four cross-stage conflicts occur in the frozen inputs.

They comprise:

- two cases in which citation DOI evidence and PMID-linked database evidence
  identify different database publication identities; and
- two cases in which the citation DOI is absent from the database while its
  PMID maps to a different DOI-bearing database publication.

These remain separate publication components.

No conflict relationship is automatically collapsed.

## 7. Software-registry independence

The 215 software-registry screening entities remain independent components.

A software-registry component is never automatically merged with a publication
component because of DOI or PMID equality.

Tool-level evidence consolidation occurs later.

## 8. Metadata aggregation

Titles already present in either safely linked publication source may be used
within the combined publication component.

This is aggregation of frozen metadata, not external enrichment.

In the frozen corpus:

- 390 database publication entities initially lack titles;
- none of those 390 receive a safe citation link;
- 747 citation entities initially lack their own title;
- 70 of those receive a safe database publication link; and
- all 70 obtain a title from the linked database component.

After safe offline aggregation, 1,067 publication components still lack any
title.

## 9. Provisional combined screening universe

Against the frozen inputs, the offline component layer derives:

- 94,898 publication screening components;
- 215 software-registry screening components; and
- 95,113 provisional screening components in total.

These are derived implementation regression values.

They are not prespecified sample sizes and are not a claim that publication
identity is fully resolved.

Later evidence-backed identity resolution may change the number of provisional
publication components.

## 10. Pre-screening attention set

A component receives identity attention when it contains one or more of:

- provider-specific unresolved citation identity;
- citation identity conflict;
- database identity conflict;
- citation-side cross-stage conflict; or
- database-side cross-stage conflict.

A publication component receives metadata attention when it lacks a title
after all safe offline aggregation.

Against the frozen inputs:

- 619 publication components require identity attention;
- 1,067 publication components lack a title;
- their union is 1,342 publication components;
- no software-registry component currently requires name/identity attention.

The 1,342-component set is a pre-screening attention set.

It is not an API-request count.

Some components may be resolved using existing frozen evidence, and one
external metadata request may provide evidence relevant to more than one
component.

## 11. Provenance and membership invariant

Every database screening entity appears exactly once in the combined component
layer.

Every citation screening entity appears exactly once in the publication
component layer.

No discovery identity is discarded because it participates in an automatic
link or conflict.

## 12. DOI anti-overcollapse invariant

An automatically linked database-backed publication component may not contain
more than one DOI value.

Different DOI identities are retained separately when evidence conflicts.

PMID does not override this boundary.

## 13. Order independence

Cross-stage construction must be independent of database-entity and
citation-entity input order.

Synthetic and complete-corpus regression tests verify deterministic normalized
output.

## 14. Offline boundary

The implementation contains no network-capable imports.

It performs no metadata API requests.

The next stage may specify and test metadata resolution only after this
cross-stage offline implementation is frozen.

## 15. Interpretation

This implementation establishes the provisional screening-component universe
and identifies which components need additional identity and/or title evidence
before scientific screening.

It does not itself determine scientific relevance or software-landscape
eligibility.
