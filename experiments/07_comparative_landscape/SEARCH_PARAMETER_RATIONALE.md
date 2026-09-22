# Experiment 07 search-parameter rationale

Status: FROZEN_POST_DATABASE_SEARCH_PRE_CITATION_CHAINING

## Purpose

This document records the rationale for the database search parameters used in
Experiment 07.

It does **not** claim that the chosen search expressions are uniquely optimal,
maximally sensitive, or objectively "best".

For a software landscape whose complete relevant set is not known in advance,
such an optimality claim would not be testable at query-design time.

Instead, the search strategy was designed to satisfy three requirements:

1. derive search concepts from the analytical problem rather than from a final
   comparator list;
2. freeze query changes before eligibility/capability screening could influence
   them; and
3. measure search performance empirically after independent discovery routes
   have established a broader final relevant set.

The exact search strings remain frozen in `search_queries.tsv` and
`high_recall_queries.tsv`.

## 1. Conceptual basis

Before formal screening, Experiment 07 defined six analytical roles relevant to
the BRANCHSNV comparison:

1. clade/lineage marker discovery;
2. branch-change reconstruction;
3. homoplasy/recurrent-state analysis;
4. marker deployment/genotyping;
5. general phylogenetic/parsimony infrastructure; and
6. upstream variant-calling, recombination, and phylogeny workflows.

The database queries concentrate on terminology describing the analytical
questions most proximal to sequence-state interpretation:

- clade/lineage-associated SNP states;
- branch/node-associated mutations or substitutions;
- ancestral state/sequence reconstruction;
- recurrent/homoplasic variation; and
- phylogenetically informed SNP genotyping.

More generic phylogenetic and upstream software can enter the broader
landscape when discovered by these searches, software-registry retrieval,
citation chaining, or source-backed screening. The search does not claim
exhaustive enumeration of every generic phylogenetic or variant-calling
program ever published.

## 2. Role of the pre-search seed registry

The 31-tool seed registry was assembled from author domain knowledge and
exploratory searching before the formal search.

It served two purposes:

1. vocabulary development; and
2. a pre-screening search-sensitivity diagnostic.

It was not an inclusion list.

Seed identity was never inserted into formal or high-recall search expressions,
and presence in the seed registry does not determine final landscape
eligibility.

Because seed knowledge contributed to vocabulary development, seed recovery is
not treated as an unbiased estimate of search recall. It is a development-set
diagnostic.

## 3. Original 18-query search

The original search used 18 concept queries grouped around:

- clade-marker terminology;
- SNP genotyping;
- ancestral-state/sequence reconstruction;
- mutation/substitution mapping; and
- homoplasy/recurrent mutation.

Many expressions deliberately used exact domain phrases and common
orthographic variants.

This first stage was intended to provide an interpretable, relatively
high-specificity conceptual search rather than an assumption of exhaustive
sensitivity.

Where broad analytical phrases could retrieve large numbers of biological
application papers, selected queries additionally required terms such as
`software`, `tool`, `package`, `algorithm`, or `method`.

No software names or author names were required by the scientific search
expressions.

## 4. Search fields

PubMed bibliographic queries were restricted to Title/Abstract.

OpenAlex was ultimately restricted to the analogous title/abstract field.

This was a harmonization choice, not a claim that title/abstract searching is
intrinsically superior to full-text searching.

Retrieval attempt 01 revealed that the initial OpenAlex `search` implementation
searched a broader text scope than PubMed. Before any record screening,
OpenAlex produced 33,217 candidate rows compared with 718 PubMed rows and
498 bio.tools rows.

The problem was therefore unequal searchable fields across bibliographic
sources.

OpenAlex was changed to validated OQL expressions of the form:

`works where title/abstract has (...)`

while preserving the 18 scientific concepts.

The failed/broader attempt remains retained in the audit history rather than
being discarded.

## 5. OpenAlex lexical behaviour

Initial OpenAlex wildcard shorthand was corrected before formal retrieval
because wildcard expansion using `*` was not documented for the selected API
interface.

Explicit lexical variants were substituted while preserving the prespecified
scientific concepts.

All final formal and high-recall OQL expressions were passed through the
OpenAlex validation endpoint before retrieval. The validation endpoint did not
execute the search index.

## 6. Why PubMed, OpenAlex, and bio.tools

The three machine-queryable sources represent different discovery mechanisms:

- PubMed: biomedical/life-science bibliographic indexing;
- OpenAlex: broad scholarly bibliographic indexing plus citation-graph
  structure;
- bio.tools: a registry centred on identifiable bioinformatics software.

The purpose of combining them was not to assume any single database was
complete.

Source-specific recovery will be measured at the end of Experiment 07.

Google Scholar was retained only as a supplementary discovery check and does
not define the reproducible search corpus.

## 7. No scientific date restriction

The scientific PubMed queries contain no publication-date restriction.

The Entry Date (EDAT) intervals later used for PubMed HR05 are retrieval
partitions only. They were introduced because one result set exceeded the
10,000-identifier ESearch retrieval ceiling.

The unbounded query count was required to equal the partition envelope count,
and the scientific query expression remained unchanged.

Thus EDAT is not a study eligibility criterion or search parameter.

## 8. Prespecified sensitivity diagnostic

Before formal eligibility screening, the frozen seed-name diagnostic showed
that the exact-phrase-oriented search had inadequate sensitivity.

Among the 14 prespecified direct, near-direct, and diagnostic-panel candidates,
only 4 were recovered by candidate-name matching.

This result was used only to diagnose search sensitivity.

It was not used to declare any software eligible or ineligible.

## 9. Single generic high-recall expansion

A single expansion was then specified before screening.

Five broad concept blocks were defined:

- HR01 — phylogenetic clade or lineage SNP markers;
- HR02 — phylogenetic branch mutation or substitution mapping;
- HR03 — ancestral phylogenetic state or sequence inference;
- HR04 — phylogenetic homoplasy or recurrent variation;
- HR05 — phylogenetic SNP lineage genotyping.

Compared with the original search, these blocks broadened synonyms and
morphological variants while retaining conceptual conjunctions that preserve
the relevant analytical context.

No missing software name and no author name was inserted into the queries.

All five expressions were committed before their retrieval results were
observed.

## 10. Stopping query optimization

The high-recall expansion was permitted once.

After it completed, query vocabulary was frozen permanently for the primary
search corpus.

Known methods still not recovered were not used to generate further search
terms.

Instead they were routed to the already-prespecified citation-chaining stage.

This prevents iterative optimization against known software from creating an
artificially high apparent recovery rate.

## 11. Observed diagnostic improvement

The completed merged universe contains:

- 116,556 source-query candidate rows;
- 79,917 deduplicated records.

The merged seed-name diagnostic recovered:

- 23 of 31 prespecified seeds overall;
- 4 of 5 prespecified direct candidates; and
- 5 of 5 prespecified near-direct candidates.

The formal stage itself recovered 8 of 31 seeds; the high-recall stage
recovered candidate-name evidence for 21 of 31; because of overlap, the union
contains 23 recovered seeds.

These values demonstrate that generic broadening materially improved recovery.

They do not establish absolute recall because the seed registry influenced
vocabulary development and candidate-name matching is not equivalent to
confirmed software recovery.

## 12. What is not claimed

Experiment 07 does not claim that:

- the search strings are uniquely optimal;
- every possible relevant synonym was known a priori;
- title/abstract indexing contains every description of every tool;
- the 31 seed tools constitute a gold standard;
- database searching alone is complete; or
- failure of a tool name to appear constitutes exclusion.

Completeness is instead evaluated using multiple discovery routes and the
predeclared end-of-search validation plan.
