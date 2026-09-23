# Experiment 07 screening-entity identity implementation

Status: FROZEN_OFFLINE_IMPLEMENTATION_CANDIDATE

## 1. Purpose

`screening_entity_identity.py` implements the deterministic identity layer
specified prospectively in:

- `CITATION_PUBLICATION_RECONCILIATION_SPEC.md`; and
- `UNIFIED_SCREENING_AND_WAVE_PROMOTION_SPEC.md`.

It constructs screening-entity identities and preserves discovery provenance.

It does not perform scientific screening.

## 2. Scope

The implementation performs only:

- identifier normalization;
- DOI-first publication grouping;
- conservative PMID attachment;
- explicit conflict preservation;
- provider-specific fallback identity construction;
- separation of publication and software-registry screening entities;
- provenance aggregation;
- deterministic ordering; and
- fail-closed structural validation.

It does not:

- perform HTTP or other network requests;
- enrich bibliographic metadata;
- retrieve abstracts;
- resolve identity conflicts using external sources;
- classify scientific relevance;
- make software-landscape inclusion/exclusion decisions;
- assign analytical roles;
- consolidate screening entities into software/method identities;
- select canonical method publications; or
- write production result artifacts.

## 3. Frozen inputs used for validation

The implementation has been validated read-only against:

- `results/07_comparative_landscape/merged_search_universe/deduplicated_records.tsv`
- `results/07_comparative_landscape/citation_wave_0/neighbour_records.tsv`

Neither input is modified.

The historical production `screening_log.tsv` remains empty.

## 4. Identifier-normalization dependency

The identity layer must use the exact DOI, PMID, OpenAlex Work ID and OMID
normalization semantics already used by the frozen citation retriever.

The implementation does not import or execute the citation retriever as a
module.

Instead, it:

1. parses the retriever source with the Python AST;
2. extracts only the four pure normalization function definitions;
3. verifies each function definition against an implementation-frozen SHA-256;
4. compiles those four definitions in an isolated namespace; and
5. fails closed if their source changes.

This preserves exact normalization behavior without bringing network-capable
retrieval machinery into the identity module runtime.

## 5. Database screening-entity construction

The frozen merged database universe contains heterogeneous discovery entities.

Publication records use DOI-first provisional identity.

A DOI-less PMID record attaches automatically to a DOI entity only if that
PMID is associated with exactly one DOI group.

A PMID associated with multiple DOI groups does not merge those groups.
Affected identities enter explicit conflict hold.

Publication records lacking both DOI and PMID retain their frozen database
deduplication key as a fallback identity.

Software-registry records remain independent screening entities even when their
metadata contain DOI or PMID values also represented by publication records.

Title/year equality does not establish publication identity.

## 6. Citation publication-identity construction

Citation provenance rows are projected to provisional publication entities.

The same DOI-first anti-overcollapse rule applies.

DOI-less PMID rows attach to a DOI entity only when the PMID identifies exactly
one DOI group.

OpenAlex Work IDs and OMIDs may expose identity conflicts but cannot bridge
different DOI groups.

Rows with neither DOI nor PMID remain provider-specific provisional identities:

- `publication:openalex:<Work ID>`
- `publication:omid:<OMID>`

These remain unresolved pending the separately specified metadata-resolution
stage.

A DOI associated with multiple PMIDs is also retained under conflict hold.

## 7. Provenance invariant

Every frozen input row must occur exactly once in the derived entity
provenance.

No discovery record may be lost or represented more than once.

This invariant is checked against both complete frozen input corpora.

## 8. Order independence

Entity construction must be independent of input-row order.

Forward-order and reversed-order builds of both complete frozen inputs must be
byte-identical after normalized serialization.

## 9. Offline boundary

The module contains no network imports or network-call symbols.

The citation retriever itself is never imported or executed.

Testing and real-data validation of this implementation therefore require no
metadata API access.

## 10. Validated database behavior

Against the frozen 79,917-row merged database universe:

- 79,762 screening entities are derived;
- 79,547 are publication screening entities;
- 215 are software-registry screening entities;
- 40 entities are held for identity conflict; and
- 20 identifier conflicts are recorded.

The reduction from 79,917 discovery records to 79,762 screening entities is
exactly 155 records.

Before implementation, the independent screening-unit audit had identified
exactly 155 simple cases in which one PMID was represented by one DOI-keyed
record plus one separate PMID-keyed record.

All 20 database identity conflicts correspond to the independently observed
PMIDs associated with multiple DOI keys.

These counts are implementation regression baselines derived from frozen
inputs. They were not target sample sizes.

## 11. Validated citation behavior

Against the frozen 33,071-row Wave 0 citation-neighbour corpus:

- 17,605 provisional publication entities are derived;
- 17,034 currently have resolved provisional identity;
- 502 remain provider-specific unresolved identities;
- 69 entities are held for identity conflict; and
- 38 identifier-conflict relationships are recorded.

The 502 unresolved entities comprise:

- 495 unique OpenAlex-only identities derived from 531 OpenAlex-only provenance
  rows; and
- 7 unique OMID-only identities derived from 7 OMID-only provenance rows.

The 38 citation identifier conflicts comprise:

- 32 PMID-to-multiple-DOI relationships; and
- 6 DOI-to-multiple-PMID relationships.

The 69 conflict-held entities comprise:

- 63 affected only by PMID-to-multiple-DOI conflict;
- 5 affected only by DOI-to-multiple-PMID conflict; and
- 1 affected by both conflict classes.

No provisional citation entity contains more than one DOI value.

These counts are implementation regression baselines, not prespecified
scientific outcomes.

## 12. Regression coverage

The dedicated regression tests cover at minimum:

- unique PMID attachment to DOI;
- multi-DOI PMID conflict preservation;
- multiple-PMID DOI conflict preservation;
- title/year non-identity;
- OpenAlex non-bridging;
- OMID non-bridging;
- provider-specific unresolved identities;
- ambiguous provider-only failure;
- software-registry/publication separation;
- identifier-poor database fallback;
- provenance preservation; and
- order independence.

The pre-existing Experiment 07 regression suite must also remain green.

## 13. Failure behavior

The identity implementation fails closed when required structural assumptions
are violated.

Examples include:

- unknown database entity class;
- required input columns missing;
- citation rows without any usable identifier;
- ambiguous DOI/PMID-less rows carrying both provider-local identifier classes;
- frozen normalization-source drift;
- provenance loss or duplication; and
- unexpected mixed screening-entity classes.

## 14. Interpretation

This implementation creates auditable identity/provenance structures only.

It does not determine whether a discovered entity is scientifically relevant.

The next implementation stage may add bibliographic metadata resolution only
after this offline identity implementation has been frozen.
