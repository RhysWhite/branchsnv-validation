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
