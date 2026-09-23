# Experiment 07 citation-publication reconciliation specification

Status: FROZEN_PRE_RECONCILIATION_AND_SCREENING

## 1. Purpose

Wave 0 citation retrieval produced citation-neighbour provenance records, not a
final set of unique publications suitable for scientific screening.

This specification defines how those immutable provenance rows will be
resolved to bibliographic publication records before record-level relevance
screening.

No relevance, eligibility, comparator-role, software-name, citation-count,
date, language, or publication-type criterion is applied during reconciliation.

The frozen Wave 0 retrieval corpus is never modified in place.

## 2. Why the existing database merge is not reused as the citation identity rule

The formal/high-recall merged search universe uses an already-frozen
`dedup_key()` hierarchy designed for those retrieval outputs.

Its specification explicitly prohibits introducing new DOI resolution, PMID
resolution, fuzzy matching, title similarity, or manual identity rules during
that merge.

Citation records have materially different identifier and metadata structure:

- OpenAlex backward neighbours can initially contain only an OpenAlex Work ID;
- OpenCitations neighbours can initially contain DOI, PMID and/or OMID but no
  title;
- the same underlying bibliographic relationship can be represented through
  different provider identifiers;
- provider metadata can associate one secondary identifier with multiple DOI,
  PMID, OpenAlex or OMID values.

The database universe therefore remains frozen and unchanged.

Citation reconciliation is a separate derived layer with separate provenance.

## 3. Immutable inputs

The reconciliation implementation will consume only:

- the frozen Wave 0 `neighbour_records.tsv`;
- the frozen Wave 0 retrieval manifest and checksum manifest;
- the frozen merged database-search universe for cross-stage comparison only;
- metadata responses obtained under the resolver rules below.

No original Wave 0 row may be changed or deleted.

## 4. Identifier normalization

Normalization must use the same DOI, PMID, OpenAlex Work ID and OMID
normalization semantics already frozen in the Wave 0 citation retriever.

Normalized identifier namespaces are:

- `doi`
- `pmid`
- `openalex`
- `omid`

Provider-local identifiers are evidence-bearing identifiers but are not assumed
to be globally equivalent merely because another provider associates them with
the same record.

## 5. Core anti-overcollapse rule

Different non-empty DOI values are never automatically merged into one
publication identity because of:

- a shared PMID;
- a shared OpenAlex Work ID;
- a shared OMID;
- a title match;
- a publication-year match; or
- transitive connected-component membership.

Such relationships are retained as identity-conflict evidence.

This explicitly prevents preprints, published articles, corrections, versions,
provider re-keying, or erroneous metadata bridges from being silently collapsed
into one publication.

## 6. Provisional publication identity

Reconciliation proceeds conservatively.

### 6.1 Exact DOI groups

Rows carrying the same normalized DOI form one provisional DOI group.

Any disagreement in PMID, OpenAlex ID, OMID, title, year, or retrieved
bibliographic metadata is recorded as a conflict.

An exact DOI match is not allowed to erase such conflict evidence.

### 6.2 DOI-less PMID rows

For a row without a DOI but with a PMID:

1. if that PMID is associated with exactly one DOI group, the row may attach to
   that DOI group;
2. if the PMID is associated with more than one DOI group, the row enters
   conflict hold;
3. if the PMID is associated with no DOI group, it forms a provisional PMID
   group.

### 6.3 Rows lacking DOI and PMID

Rows with only OpenAlex and/or OMID identity require metadata resolution before
cross-provider attachment.

After resolution:

- an exact uniquely resolved DOI may attach the row to that DOI group;
- otherwise an exact uniquely resolved PMID may attach the row to the relevant
  DOI or PMID group;
- otherwise the record remains provider-identifier-specific.

OpenAlex ID or OMID alone must not bridge two different DOI groups.

### 6.4 Provider-local fallback identity

When no DOI or PMID can be established, the fallback identity is provider
specific:

- `openalex:<Work ID>`
- `omid:<OMID>`

No automatic title/year merge is permitted between these fallback identities.

## 7. Conflict hold

A record or provisional group enters `conflict_hold` whenever automated
evidence would otherwise imply any of the following:

- one PMID associated with multiple DOI groups;
- one OpenAlex Work ID associated with multiple DOI groups;
- one OMID associated with multiple DOI groups;
- one DOI associated with materially conflicting publication metadata;
- DOI and PMID evidence pointing to different frozen database-search records;
- an identifier resolver returning incompatible identities from separate
  authoritative sources.

Conflict-held records are not excluded.

They require bibliographic identity resolution before relevance screening.

Resolution decisions must cite the metadata evidence used and preserve all
original identifiers.

## 8. Metadata-resolution sources

Metadata resolution is bibliographic only and occurs before scientific
screening.

### 8.1 OpenAlex

OpenAlex single-Work retrieval may be performed using:

- OpenAlex Work ID;
- DOI; or
- PMID.

Relevant returned fields include:

- OpenAlex Work ID;
- DOI;
- known external IDs including PMID;
- title/display name;
- publication year;
- work type.

Official documentation frozen as methodological reference:

`https://help.openalex.org/api/get-single-entities/`

`https://help.openalex.org/data/works/attributes/`

### 8.2 OpenCitations Meta

OpenCitations Meta `/metadata/{ids}` may be used for bibliographic metadata
resolution using supported identifiers including:

- DOI; and
- OMID.

Relevant metadata include title, publication date, type and associated
identifiers.

Official documentation frozen as methodological reference:

`https://opencitations.net/meta/api/v1`

### 8.3 PubMed

PubMed ESummary and, when necessary, EFetch may be used for exact PMID-based
bibliographic metadata.

Official documentation frozen as methodological reference:

`https://www.ncbi.nlm.nih.gov/books/NBK25499/`

## 9. Resolver ordering

The resolver does not select a preferred scientific source.

Requests are determined by missing metadata and identifier type:

1. OpenAlex-ID-only records are resolved through the exact OpenAlex Work;
2. OMID-only records are resolved through exact OpenCitations Meta metadata;
3. PMID-only records may be resolved through PubMed and OpenAlex external-ID
   lookup;
4. DOI-bearing records lacking screenable title metadata may be resolved by
   exact DOI lookup;
5. conflict cases may query more than one source for bibliographic
   verification.

Identical resolver requests are made once and reused through an auditable local
cache.

## 10. Resolver provenance

Every resolver request must retain:

- requested identifier;
- provider;
- exact operation;
- retrieval timestamp;
- terminal status;
- raw response path;
- response SHA-256;
- parsed identifiers;
- parsed title;
- parsed publication year/date;
- parsed publication type where supplied.

Credentials must remain environment-only.

Raw resolver responses are provenance evidence and are not edited manually.

## 11. Screenable metadata gate

A reconciled publication becomes eligible for record-level relevance screening
only when it has:

- a stable reconciliation key or explicit conflict-hold identifier; and
- a non-empty bibliographic title.

Absence of an abstract is not itself an exclusion.

If a title cannot be established from the frozen resolver sources, the record
remains unresolved and cannot be counted as screened or as evidence of
saturation.

## 12. Abstract/source escalation

Record-level screening follows the already-frozen rule that uncertainty is
resolved toward retention.

Title and bibliographic metadata may support clear exclusion when the record
plainly meets an existing exclusion criterion.

When title/metadata are insufficient to determine whether a record could
describe, introduce, substantially extend, or document a relevant reusable
method, the record advances to abstract or accessible-source assessment.

This is screening, not reconciliation, and must be logged separately.

## 13. Required derived outputs

The reconciliation stage must produce at minimum:

- `citation_provenance_rows.tsv`
- `publication_records.tsv`
- `publication_provenance.tsv`
- `metadata_resolution.tsv`
- `identity_conflicts.tsv`
- `cross_stage_links.tsv`
- `reconciliation_manifest.json`
- `checksums.sha256`

The original Wave 0 files remain unchanged.

## 14. Cross-stage comparison with the frozen database universe

Cross-stage comparison must not modify the frozen database deduplication keys.

Automatic exact links may be established by:

1. normalized DOI; or
2. when no conflicting DOI evidence exists, normalized PMID.

If DOI and PMID evidence point to different frozen database records, the
cross-stage relationship is a conflict and is not automatically resolved.

Exact title/year similarity may be reported as a possible link but cannot
establish automatic publication identity.

A citation publication and a bio.tools software-registry record are never
automatically treated as the same bibliographic publication.

## 15. Order independence

Reconciliation output must be independent of:

- Wave 0 provenance-row order;
- citation source order;
- anchor order; and
- direction order.

A forward-order and reversed-order rebuild must produce byte-identical
normalized derived outputs.

## 16. Fail-closed conditions

Reconciliation fails if:

- a frozen input checksum fails;
- required columns are absent;
- identifier normalization is nondeterministic;
- a row loses provenance;
- different DOI groups are merged through a secondary identifier;
- an unresolved identity conflict is silently assigned a normal publication
  key;
- a resolver response cannot be tied to its exact request;
- output checksums fail; or
- order-independence validation fails.

## 17. Interpretation

The number of reconciled publication records is a derived property of the
frozen citation corpus and reconciliation rules.

It is not a target sample size.

Reconciliation is an identity/provenance operation and makes no statement about
scientific relevance.
