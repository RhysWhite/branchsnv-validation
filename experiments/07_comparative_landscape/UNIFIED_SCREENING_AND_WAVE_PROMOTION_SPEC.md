# Experiment 07 unified screening and citation-wave promotion specification

Status: FROZEN_PRE_RECORD_SCREENING

## 1. Purpose

The formal database search, generic high-recall search, software-registry
search, and citation-chain discovery stages must feed one evidence-based
software landscape without allowing discovery route to determine eligibility.

The frozen discovery outputs are not themselves assumed to be one-to-one
scientific screening units.

This specification therefore distinguishes:

1. immutable discovery records;
2. screening entities;
3. source-backed software/method identities; and
4. canonical citation-expansion publications.

No record-level screening had been performed when this specification was
frozen.

## 2. Discovery records are immutable provenance

A discovery record may arise from:

- the formal bibliographic search;
- the high-recall bibliographic search;
- bio.tools;
- citation chaining; or
- more than one route.

The frozen merged database-search universe and frozen citation outputs remain
unchanged.

Discovery-stage presence is not itself:

- a publication-identity decision;
- a software-landscape inclusion decision;
- an analytical-role decision; or
- evidence that a record has already been screened.

## 3. Why frozen search deduplication is not the screening-unit definition

The merged database-search universe contains both publication records and
software-registry records.

Its frozen `dedup_key` hierarchy was designed to deduplicate retrieval output
deterministically. It was not claimed to establish a fully reconciled
bibliographic entity model.

The pre-screening audit found that:

- the frozen merged universe contains 79,702 records with
  `entity_type = publication`;
- it contains 215 records with
  `entity_type = software_registry`;
- some PMIDs occur across multiple frozen database deduplication keys;
- some of those PMID relationships connect one DOI-keyed record to a separate
  PMID-keyed record;
- some PMIDs are associated with more than one DOI key; and
- exact title/year matches can span multiple DOI records.

The frozen database deduplication keys are therefore preserved as discovery
provenance rather than reinterpreted as guaranteed publication identities.

## 4. Screening-entity classes

Every baseline discovery record is assigned to one of two screening-entity
classes:

1. `publication`
2. `software_registry`

These classes have different identity semantics.

A publication and a software-registry record are never automatically collapsed
into one screening entity.

They may later contribute evidence to the same source-backed software/method
identity.

## 5. Publication screening entities from the frozen database universe

Database records with `entity_type = publication` are projected into a
conservative publication-screening layer.

The original frozen `dedup_key` is retained permanently as discovery
provenance.

### 5.1 DOI-bearing publication records

Records carrying the same normalized DOI belong to one provisional publication
screening entity.

Different non-empty DOI values are not automatically merged because of:

- shared PMID;
- identical title;
- identical year;
- title/year equality; or
- any transitive identifier relationship.

### 5.2 DOI-less PMID records

For a database publication record without DOI but with PMID:

1. if that PMID occurs with exactly one DOI-bearing publication entity, the
   DOI-less record may attach to that entity;
2. if that PMID occurs with more than one DOI-bearing entity, the relationship
   enters `conflict_hold`;
3. if that PMID occurs with no DOI-bearing entity, the record forms a
   provisional PMID publication entity.

### 5.3 Records lacking both DOI and PMID

A database publication record lacking both DOI and PMID remains a separate
screening entity under its frozen database `dedup_key`.

Exact title/year equality may be retained as diagnostic evidence but cannot
establish automatic publication identity.

### 5.4 Conflict preservation

A PMID connecting multiple DOI groups does not collapse those DOI groups.

The relationship is retained as identity-conflict evidence until bibliographic
resolution establishes whether the records represent:

- duplicate provider records;
- different versions;
- preprint and published article;
- correction or companion record;
- erroneous metadata; or
- another relationship.

## 6. Citation-derived publication screening entities

Wave 0 citation provenance is reconciled under
`CITATION_PUBLICATION_RECONCILIATION_SPEC.md`.

The same anti-overcollapse principle applies:

different non-empty DOI values are not automatically merged through PMID,
OpenAlex ID, OMID, title/year, or transitive connected-component membership.

Citation provenance rows are not themselves screening units.

## 7. Cross-stage publication reconciliation

After citation reconciliation, citation-derived publication entities are linked
to database-derived publication screening entities conservatively.

Automatic linkage is permitted by:

1. exact normalized DOI; or
2. when there is no conflicting DOI evidence, exact normalized PMID.

When an identifier would connect multiple DOI groups, the relationship enters
`conflict_hold`.

OpenAlex ID, OMID, title, year, or title/year alone cannot bridge different DOI
groups.

All discovery provenance is retained irrespective of whether an entity is
linked across stages.

## 8. Software-registry screening entities

Each frozen database record with
`entity_type = software_registry`
forms a software-registry screening entity.

Its frozen bio.tools identity is retained.

A bio.tools record is not a bibliographic publication merely because its
registry metadata contains or can be linked to a publication identifier.

Conversely, a publication record is not automatically the same screening
entity as a bio.tools registry entry.

Both may later support the same software/method identity during source-backed
tool-level assessment.

## 9. Screening unit

The screening unit is a stable screening entity, not:

- a citation edge;
- a citation provenance row;
- a raw source-query hit; or
- necessarily one frozen merged-search `dedup_key`.

For publication entities, the unit is the conservatively reconciled
publication/version identity defined above.

For software-registry entities, the unit is the frozen registry identity.

Every original discovery record remains traceable to its screening entity.

## 10. Baseline screening population

Before construction of Wave 1, the baseline screening population is constructed
from:

1. every publication discovery record in the complete frozen merged
   formal/high-recall database universe;
2. every software-registry discovery record in that universe; and
3. every reconciled Wave 0 citation publication.

These discovery records are projected to screening entities under the frozen
rules above.

The final number of screening entities is therefore a derived result.

It is not prespecified as 79,917 plus the citation-record count, and it is not
a target sample size.

## 11. Previously adjudicated initial anchors

The eight initial Wave 0 anchor methods already underwent the frozen
source-backed citation-anchor assessment.

Their established canonical anchor publications retain that adjudication and
need not undergo a duplicate scientific decision merely because the same
publication or software is encountered again.

All rediscovery provenance is nevertheless retained.

Any additional discovery entity associated with an initial anchor must still be
resolved to that existing method identity using source-backed evidence rather
than name matching alone.

## 12. Record-level screening rule

The existing frozen record-level screening rule remains unchanged.

An entity advances to source-backed method assessment whenever its available
title, name, abstract, description, metadata, or accessible source material
could plausibly describe, introduce, substantially extend, or document a
reusable analytical software/method relevant to one or more of the six
protocol-defined roles.

Uncertainty is resolved toward retention for source checking.

Clear exclusions must use the already-frozen exclusion criteria and record an
explicit reason.

Discovery route, citation frequency, anchor multiplicity, provider count and
seed status are not screening criteria.

## 13. Metadata escalation

A publication screening entity must have a stable screening identifier and
sufficient bibliographic metadata to permit the frozen screening rule to be
applied.

For citation publications, the metadata gate in
`CITATION_PUBLICATION_RECONCILIATION_SPEC.md` applies.

For database publication records, existing frozen metadata are used first.

If available title/metadata are insufficient for a defensible disposition, the
entity advances to abstract or accessible-source assessment.

A software-registry entity may be assessed from registry name, description,
documented functions, linked documentation and accessible primary sources.

Missing metadata is not itself a scientific exclusion.

## 14. Source-backed software/method assessment

Screening entities retained as potential software/method records advance to
tool-level assessment under the already-frozen software-landscape rules.

Multiple screening entities may support one software/method identity.

For example:

- a bio.tools registry entry;
- a software publication;
- a methods publication;
- a documentation page; and
- a citation-discovered publication

may all contribute evidence for the same tool.

Tool-level consolidation must preserve all supporting screening-entity and
discovery provenance.

## 15. Canonical publication decision

For an included software/method assigned `direct` or `near_direct`, a canonical
primary publication decision must be frozen before citation expansion.

Possible outcomes include:

- canonical publication established;
- no distinct primary publication identifiable; or
- unresolved.

An application paper that merely uses an existing method is not promoted as
the canonical method publication when a distinct primary publication can be
established.

A software-registry entry itself is never a citation anchor.

If an included direct/near-direct method has no identifiable canonical
publication, that explicit outcome is retained; the method remains part of the
software landscape but cannot generate bibliographic citation expansion.

An unresolved canonical-publication decision prevents completion of the
relevant screening/wave gate.

## 16. Why database-derived methods remain eligible for Wave 1

The initial eight anchors were a prospectively frozen graph-bootstrap
population derived from prespecified seed candidates.

They were not a claim that every direct/near-direct method in the complete
database-search universe had already been identified.

Because the full database universe had not undergone record-level screening, a
non-seed direct/near-direct method established during baseline screening
remains eligible for citation expansion.

## 17. Wave 1 anchor population

No Wave 1 citation retrieval occurs until baseline screening is complete.

A canonical publication enters the Wave 1 anchor set when all of the following
are true:

1. the associated software/method identity is confirmed;
2. software-landscape decision is `include`;
3. evidence-supported role is `direct` or `near_direct`;
4. a canonical primary publication has been established; and
5. that canonical publication has not previously been citation-expanded.

This rule applies regardless of whether the supporting discovery route was:

- formal search;
- high-recall search;
- bio.tools;
- Wave 0 citation chaining; or
- multiple routes.

Anchor provenance records all contributing discovery routes.

## 18. Wave attribution

A method present in the frozen database universe but first classified during
baseline screening retains database-stage discovery provenance.

It is not retrospectively described as a Wave 0 citation discovery.

If its canonical publication has not already been expanded, Wave 1 is its first
eligible future citation-expansion opportunity.

## 19. Subsequent waves

For Wave n >= 1:

1. retrieve complete backward and forward citation neighbourhoods for every
   Wave n anchor from both frozen citation sources;
2. reconcile publication identity under the frozen citation reconciliation
   rules;
3. link records to existing screening entities where permitted;
4. create new screening entities for genuinely new records;
5. screen all newly encountered screening entities;
6. complete source-backed tool-level assessment;
7. freeze all screening, method and role decisions for the wave; and
8. promote every newly established, previously unexpanded direct/near-direct
   canonical publication to Wave n+1.

Each canonical publication is citation-expanded at most once.

## 20. Screening log

The existing empty historical `screening_log.tsv` is not silently repurposed.

The production screening implementation must define a screening table capable
of retaining at minimum:

- stable screening-entity identifier;
- screening-entity class;
- publication-reconciliation key where applicable;
- frozen database deduplication keys;
- bio.tools identifier where applicable;
- citation reconciliation/provenance identifiers where applicable;
- discovery stages;
- citation-wave provenance;
- title or software name;
- year;
- DOI;
- PMID;
- OpenAlex ID;
- OMID;
- record-level decision;
- exclusion reason;
- candidate-method flag;
- evidence-escalation status;
- reviewer/operator;
- decision timestamp or batch provenance; and
- notes.

Source-backed software/method assessment is retained separately from
record-level screening.

## 21. Order independence

Screening-entity construction must be independent of:

- database-record order;
- citation-row order;
- source order;
- anchor order; and
- citation direction.

A forward-order and reversed-order rebuild of the screening-entity construction
must produce byte-identical normalized identity/provenance outputs.

Scientific screening decisions are recorded against the resulting stable
screening-entity identifiers.

## 22. Baseline completion gate

Wave 1 cannot be constructed while any baseline screening entity is:

- unreconciled where reconciliation is required;
- in an identity conflict that can affect screening or anchor determination;
- missing required screenable metadata;
- unscreened;
- awaiting required source escalation;
- awaiting candidate-method assessment; or
- associated with an unresolved direct/near-direct canonical-publication
  decision.

This prevents incomplete database screening from being mistaken for citation
saturation.

## 23. Saturation

The previously frozen zero-new-anchor saturation rule remains unchanged.

Citation chaining stops only after a complete wave produces:

`0 new eligible direct/near-direct methods requiring citation expansion`

A complete wave requires all newly encountered screening entities and candidate
methods to have the dispositions required by the frozen citation-chaining
protocol.

The number of citation waves is not prespecified.

## 24. Search strategy remains closed

Neither reconciliation, screening-entity construction, scientific screening nor
tool-level consolidation may modify:

- Q01-Q18;
- HR01-HR05;
- the formal search corpus;
- the high-recall search corpus;
- the frozen merged database-search universe;
- the frozen Wave 0 citation corpus;
- the software-landscape eligibility criteria;
- the direct/near-direct role definitions; or
- the citation-chain saturation criterion.

Misses, duplicate discovery records, provider conflicts and discovery-route
differences are analytical results, not reasons to retune the search.
