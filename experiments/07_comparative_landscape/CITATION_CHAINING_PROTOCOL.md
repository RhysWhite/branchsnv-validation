# Experiment 07 iterative citation-chaining protocol

Status: FROZEN_PRE_RETRIEVAL

## 1. Purpose

This protocol operationalizes the prespecified backward and forward citation
chaining from included direct and near-direct methods.

It is frozen before any citation-neighbourhood retrieval.

Citation chaining is a discovery mechanism. It does not replace the frozen
software-landscape eligibility criteria, capability evidence requirements, or
direct/near-direct role rubric.

## 2. Initial anchor population

Wave 0 consists of every candidate satisfying the previously frozen
citation-anchor screening procedure.

Exactly eight methods currently satisfy that rule:

- CLASSICO/Evidente
- SNPPar
- SubRecon
- TreeTime
- FastML
- kSNP3.0
- PAML
- PastML

The number eight is an observed consequence of the frozen selection procedure,
not a target number.

The derivation is:

- 31 prespecified pre-search seed tools;
- 10 prospectively labelled direct or near-direct candidates;
- 9 of those 10 recovered by the frozen merged name-recovery diagnostic;
- all 9 screened using the same frozen source-backed criteria;
- 8 qualified as initial direct/near-direct citation anchors;
- 1 recovered name match, IQ-TREE 2, contained false-positive-only candidate
  evidence and was not promoted to an initial anchor.

Neither Clade-O-Matic nor IQ-TREE 2 is excluded from later discovery or from
the final software landscape.

## 3. Citation-graph sources

Citation edges will be retrieved from two open, machine-queryable sources:

1. OpenAlex Works;
2. OpenCitations Index v2.

The discovery corpus is the **union** of citation edges returned by these
sources.

Agreement between sources is not required for an edge to be retained.

Source-specific provenance is retained for every edge so overlap and unique
contribution can subsequently be quantified.

Using two sources is intended to reduce dependence on the coverage of any
single citation graph. It is not assumed that their citation data are
statistically independent.

## 4. Backward chaining

For every anchor publication in every wave, retrieve all available references
from both citation sources.

No reference is removed during retrieval because of:

- publication date;
- citation count;
- language;
- journal;
- publication type;
- title words;
- abstract words;
- software name; or
- membership in the original seed registry.

## 5. Forward chaining

For every anchor publication in every wave, retrieve all available works that
cite the anchor from both citation sources.

The same no-filter rule applies.

No citation-count threshold or publication-date window is used.

The citation graph is frozen as observed at the recorded retrieval timestamp.

## 6. Source-resolution requirement

Each canonical anchor must first be resolved reproducibly from its frozen
identifier.

DOI is the preferred cross-source identifier for the current Wave 0 anchors.

For OpenAlex, the DOI is resolved to a Work identifier before graph traversal.

For OpenCitations, the DOI is supplied using the identifier form supported by
the frozen implementation.

A network/API error is not equivalent to zero citations.

For each anchor × source × direction operation, the retrieval must finish with
an explicit status such as:

- `complete`
- `resolved_zero_edges`
- `not_indexed`

Transient request failure is not a terminal state and prevents the wave from
being declared complete.

## 7. Raw-data preservation

All raw API responses used to construct citation edges will be retained where
permitted.

For every retrieval retain:

- wave number;
- anchor tool;
- canonical anchor identifier;
- source;
- direction;
- request identity;
- retrieval timestamp;
- reported count where available;
- retrieved count;
- completion status; and
- response-file provenance.

Exact retrieval code and output checksums will be retained.

## 8. Edge representation

Each citation relationship will preserve at minimum:

- citation source;
- wave;
- anchor identifier;
- direction;
- citing-record identifier(s);
- cited-record identifier(s); and
- source-specific citation identifier when available.

The same scholarly relationship reported by both sources remains one logical
edge with multi-source provenance rather than being double-counted.

## 9. Record identity and deduplication

Citation records will be conservatively reconciled using persistent
identifiers.

Identity precedence is:

1. normalized DOI;
2. normalized PMID;
3. normalized OpenAlex Work identifier;
4. normalized OpenCitations identifier where available;
5. normalized title plus publication year;
6. source plus source-record identifier.

No fuzzy-title matching is performed automatically.

Potential metadata conflicts are retained for audit rather than silently
resolved.

This hierarchy is for record identity only and does not establish tool
identity.

## 10. Overlap with the completed database search

A citation-chain record is retained even when the same publication already
exists in the frozen formal/high-recall search universe.

Overlap is recorded explicitly.

This permits the final completeness analysis to distinguish:

- database-recovered methods;
- citation-recovered methods already represented in the database corpus; and
- methods discovered only through citation chaining.

Citation chaining does not alter the frozen database-search corpus.

## 11. Screening unit

Every unique newly encountered citation record is placed into the screening
queue.

There is no keyword or machine-learning prefilter that can remove a citation
record before screening.

Records already screened in an earlier citation wave are not screened again,
but additional citation provenance is attached to them.

## 12. Record-level screening

Each newly encountered record is assessed against the already-frozen
software-landscape scope.

A record advances to source-backed method assessment whenever its title,
abstract, metadata, or accessible source material could plausibly describe,
introduce, substantially extend, or document a reusable analytical
software/method relevant to one or more of the six protocol-defined roles.

Uncertainty is resolved toward retention for source checking.

Records clearly meeting a frozen record-level exclusion criterion may be
excluded with the reason recorded.

No record is excluded merely because a software name is unfamiliar or absent
from the seed registry.

## 13. Tool-level assessment

Potential software/method records are evaluated using the existing frozen
rules for:

- identifiable method documentation;
- identifiable software implementation;
- sequence/SNP/genotype/phylogenetic data scope;
- analytical-role relevance; and
- source-backed evidence.

The direct/near-direct role is assigned using
`CITATION_ANCHOR_ROLE_RUBRIC.md`.

The seed registry does not influence this final classification.

## 14. Newly discovered anchor

A method discovered during citation chaining becomes an anchor for a later wave
only when all of the following are established:

1. software/method identity is confirmed;
2. software-landscape decision is `include`;
3. evidence-supported role is `direct` or `near_direct`; and
4. a canonical primary publication anchor is established.

An application paper that merely uses a method is not itself promoted to an
anchor when a distinct canonical method publication can be established.

## 15. Wave construction

Wave 0 contains the eight initial anchors.

For Wave n:

1. retrieve complete backward citation neighbourhoods for every Wave n anchor
   from both citation sources;
2. retrieve complete forward citation neighbourhoods for every Wave n anchor
   from both citation sources;
3. union citation edges while retaining source provenance;
4. resolve and deduplicate publication records;
5. identify records not previously screened;
6. screen all newly encountered records;
7. perform source-backed assessment of candidate methods;
8. freeze all Wave n screening and method decisions;
9. collect newly included direct/near-direct methods whose canonical anchors
   have never previously been expanded.

Those new anchors constitute Wave n+1.

A method discovered early in a wave is **not** traversed immediately. It waits
until the next wave. This makes output independent of within-wave processing
order.

## 16. Previously expanded anchors

Each canonical publication anchor is citation-expanded at most once.

If the same tool/publication is rediscovered from another anchor or source,
additional provenance is retained but no duplicate expansion occurs.

## 17. Saturation stopping rule

Citation chaining stops only after a **complete wave** produces:

`0 new eligible direct/near-direct methods requiring citation expansion`

A wave is complete only when:

- every anchor has terminal backward and forward retrieval status for both
  citation sources;
- all retrieved records have been reconciled;
- every newly encountered record has a completed screening disposition;
- all candidate methods have completed source-backed eligibility/role
  assessment or an explicit unresolved status;
- all eligible direct/near-direct methods discovered in the wave have had their
  canonical publication decision frozen.

A partial API failure, unfinished screening queue, or unresolved candidate
method cannot be interpreted as saturation.

## 18. Per-wave reporting

For every completed wave report at minimum:

- number of anchors expanded;
- backward citation edges by source;
- forward citation edges by source;
- union citation edges;
- unique publication records;
- records already present in previous discovery stages;
- newly encountered records;
- records screened;
- candidate methods requiring source-backed assessment;
- newly included software-landscape methods;
- newly included direct methods;
- newly included near-direct methods;
- new anchors promoted to the next wave; and
- unresolved records/candidates.

These are descriptive yields, not performance rankings.

## 19. Final citation-only yield

After saturation, methods will be linked back to the frozen formal/high-recall
database corpus.

A direct/near-direct method is `citation_only` only when source-backed identity
establishes that the final method was not represented by any corresponding
record in the frozen merged database-search universe.

This definition is frozen before citation results are observed.

## 20. Search strategy remains closed

No citation-chain observation can alter:

- Q01-Q18;
- HR01-HR05;
- searched bibliographic fields;
- original database corpus;
- high-recall database corpus; or
- merged database universe.

New terminology observed during chaining may be discussed as a reason for a
database-search miss, but it cannot be added retrospectively to the primary
search.

## 21. End-of-search validation

After saturation, the already-frozen
`SEARCH_COMPLETENESS_VALIDATION_PLAN.md` will be executed.

This will quantify the relative recall and unique contribution of:

- original formal search;
- generic high-recall expansion;
- combined database search;
- individual bibliographic sources;
- query families;
- individual queries;
- citation chaining; and
- non-seed methods.

The validation result is reported whether favourable or unfavourable.
