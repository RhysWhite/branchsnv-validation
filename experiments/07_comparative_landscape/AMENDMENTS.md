# Experiment 07 protocol amendments

## Amendment 01 — OpenAlex query syntax

**Timing:** before formal database retrieval or screening.

After freezing the initial search protocol, the current OpenAlex API
documentation was checked against the recorded query syntax. OpenAlex documents
`search` as a stemmed text search supporting Boolean operators and quoted
phrases, and `search.exact` as an unstemmed text search. Wildcard expansion
using `*` was not documented.

Accordingly, OpenAlex queries Q13-Q17 were amended before retrieval to replace
wildcard shorthand with explicit lexical variants and to use the documented
`search` parameter.

The PubMed and bio.tools query definitions were not changed.

No formal search results had been retrieved or screened before this amendment.
The original pre-retrieval protocol remains preserved in Git history at commit
`f3ff6a3bb216e170c2a62cdfd3931a80f0c3596b`.

This amendment changes query syntax only and does not change the prespecified
search concepts, eligibility criteria, analytical roles, or benchmark
eligibility criteria.

## Amendment 02 — Harmonisation of OpenAlex search field

**Timing:** after retrieval attempt 01 and before record screening,
eligibility assessment, capability classification, or tool selection.

Retrieval attempt 01 completed successfully for all 18 queries across PubMed,
OpenAlex, and bio.tools. All 54 source-query retrievals were complete and all
reported counts matched retrieved counts.

Inspection of aggregate retrieval counts, before screening any individual
records, identified a systematic database-scope mismatch. The prespecified
PubMed queries searched Title/Abstract fields, whereas the OpenAlex `search`
parameter searched title, abstract, and full text.

This produced 33,217 OpenAlex candidate rows compared with 718 PubMed and
498 bio.tools rows. OpenAlex Q16 alone returned 17,179 records and Q11
returned 6,573 records. The resulting corpus contained 34,433 candidate rows
and 31,349 deduplicated records.

To harmonise bibliographic search scope across PubMed and OpenAlex, the
OpenAlex implementation will therefore be amended to search title and abstract
only. The 18 prespecified concepts, PubMed queries, bio.tools queries,
eligibility criteria, and benchmark criteria remain unchanged.

No candidate records from retrieval attempt 01 were screened before this
decision. Retrieval-attempt metadata, query counts, corpus checksums, and the
console-log checksum are retained in the repository audit record.

### Implementation of Amendment 02

The amended OpenAlex searches use OpenAlex Query Language (OQL) at the API
root. Each bibliographic concept query is expressed as:

`works where title/abstract has (<prespecified Boolean concept expression>)`

This limits OpenAlex bibliographic retrieval to title and abstract text while
preserving the 18 previously defined search concepts. Quoted phrases remain
exact phrases and unquoted terms use OpenAlex's documented stemmed search
behaviour.

All 18 amended OQL expressions will be passed through the OpenAlex `/query`
translation/validation endpoint before retrieval. This endpoint validates the
query without executing it against the search index.

The OpenAlex retrieval implementation is also changed from the classic
`/works?search=` interface to the API-root `?oql=` interface with cursor
pagination. No PubMed or bio.tools search definition is changed.

## Amendment 03 — Generic high-recall search expansion

**Timing:** after completion of the frozen seed-recovery diagnostic and before
formal eligibility screening, capability classification, or benchmark
selection.

The pre-search seed registry contained 14 tools classified prospectively as
direct, near-direct, or diagnostic-panel comparator candidates. A deterministic
name-recovery diagnostic, whose implementation was committed before execution,
found candidate name matches for 4 of these 14 tools (28.6%).

Candidate name recovery is not equivalent to confirmed tool recovery, and the
diagnostic was not used to make inclusion or exclusion decisions. However, the
low recovery demonstrated that the original exact-phrase-oriented search had
insufficient sensitivity to serve as the sole discovery mechanism for the
comparative software landscape.

A single supplementary high-recall search expansion will therefore be
performed before formal screening.

The expansion will:

1. use generic analytical concepts rather than software or author names;
2. retain title/abstract restriction for bibliographic databases;
3. broaden vocabulary for clade/lineage markers, branch-event reconstruction,
   ancestral reconstruction, phylogenetic genotyping, and recurrent/homoplasic
   variation;
4. be defined and committed before its retrieval results are observed; and
5. be merged with the previously frozen formal corpus without deleting
   provenance from either search stage.

The expansion will be performed once. Search terms will not subsequently be
retuned to maximise recovery of the seed registry. Any known relevant methods
not retrieved after this generic expansion will instead be handled through the
already-prespecified backward/forward citation-chaining stage and documented
accordingly.

No formal record screening, software-landscape inclusion/exclusion decisions,
capability classification, or benchmark selection had been performed before
this amendment.

## Amendment 04 — PubMed retrieval partitioning above 10,000 records

**Timing:** after failed high-recall retrieval Attempt 03 and before any
screening, eligibility assessment, capability classification, or benchmark
selection.

The frozen high-recall retrieval implementation failed closed on PubMed query
HR05 because PubMed reported 12,654 matching records. The implementation
allowed a maximum of 10,000 PubMed ESearch identifiers per query, consistent
with the PubMed ESearch retrieval ceiling.

This failure does not motivate any change to the scientific search expression.
The five high-recall concept queries therefore remain unchanged.

To permit complete retrieval of a PubMed query returning more than 10,000
records, the PubMed retrieval implementation will be amended to partition the
result set deterministically by PubMed Entry Date (EDAT).

The amended behaviour will be:

1. execute the original unmodified PubMed query and record its reported count;
2. if the reported count is <=10,000, retain the existing retrieval behaviour;
3. if the reported count is >10,000, retain the original query expression and
   recursively subdivide retrieval using `datetype=edat` with non-overlapping
   `mindate` and `maxdate` intervals;
4. bisect date intervals deterministically until every terminal interval
   reports <=10,000 records;
5. retrieve all PMIDs from every terminal interval;
6. require the sum of terminal interval counts to equal the count reported by
   the original unpartitioned query;
7. require the number of retrieved PMIDs and the number of unique PMIDs both
   to equal that original reported count;
8. fail closed if a single-day EDAT interval still exceeds 10,000 records, if
   interval counts do not reconcile, if duplicate PMIDs occur across
   non-overlapping intervals, or if any PubMed summary record is missing; and
9. retain the partition responses and partition metadata in the raw retrieval
   archive for audit.

EDAT is used only as a retrieval partition and is not an additional scientific
eligibility or search criterion. The original Title/Abstract query remains
unchanged.

A broad EDAT envelope will be used for partitioning. Before record retrieval,
the count within that envelope must equal the count from the original
unbounded query. If it does not, retrieval will stop rather than silently
exclude records.

The previously frozen OpenAlex and bio.tools retrieval implementations are
unchanged.

No records from failed Attempt 03 were screened or used for inclusion,
exclusion, capability classification, or benchmark selection.

## Amendment 05 — merged seed-recovery ordering validation

**Timing:** recorded after execution of the prespecified merged-universe
seed-recovery diagnostic and before any modification of validation code,
human confirmation, eligibility screening, capability classification, or
citation chaining.

The production diagnostic completed successfully, but an auxiliary
byte-for-byte comparison of its formal-stage candidate-match projection against
the earlier formal-search output failed.

A read-only differential audit demonstrated that the two outputs contain the
same 29-row multiset with zero missing and zero extra row occurrences. The
difference consists solely of the reversed order of two SNPPar OpenAlex Q11
records (`W3041660225` and `W4225492844`).

The original frozen checker sorts candidate matches by seed tool, source,
case-folded title, and query ID. Those two records are tied on every field in
that sort key, so Python's stable sort preserves their pre-existing input
order. The deterministic merged candidate universe supplies the tied records
in the opposite order.

Full-row deterministic canonicalization produces identical formal-stage
content (SHA-256
`7b00244753bbdc8b19637dfcc2bab96ba77633ea649a887a2b9203462fc20c14`).

Accordingly, the reproduction criterion for this ordering tie is clarified as
exact row-multiset equality plus byte-identical deterministic canonicalization,
rather than byte identity under an incomplete historical sort key.

This amendment does not change the seed registry, aliases, normalization,
phrase matching, uniqueness definition, recovery status, search expressions,
merged search universe, or generated production diagnostic. The production
diagnostic is retained unchanged.

Search retuning remains prohibited. Candidate matches remain pending human
confirmation.
