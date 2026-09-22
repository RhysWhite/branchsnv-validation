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
