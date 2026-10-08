# Experiment 07 citation-chain anchor screening specification

Status: FROZEN_PRE_SCREENING

This specification operationalizes the protocol requirement that backward and
forward citation chaining begin from **included direct and near-direct
methods**.

It is frozen before human confirmation of candidate name matches, landscape
inclusion decisions for these candidates, identification of canonical primary
anchor publications, or any citation-chain retrieval.

## 1. Purpose

The purpose of this stage is only to determine the initial set of eligible
citation-chain anchors.

It does not perform:

- citation-chain retrieval;
- full software-landscape screening;
- capability-table completion;
- benchmark eligibility assessment; or
- search-query retuning.

## 2. Candidate-anchor population

Initial anchor screening includes every prespecified seed tool satisfying both:

1. `comparison_role_candidate` is `direct_candidate` or
   `near_direct_candidate`; and
2. the frozen merged-universe seed-recovery diagnostic reports
   `candidate_match_found`.

This rule is applied mechanically and without adding or removing tools by
name.

Under the frozen merged seed-recovery result, exactly nine seed tools satisfy
this rule.

A seed tool not recovered by name is not an initial citation-chain anchor.
This does **not** constitute exclusion from the software landscape. Such a
method may subsequently enter through the prespecified citation-chaining stage
or other protocol-defined evidence.

## 3. Candidate-name recovery is not confirmation

A seed-name match is discovery evidence only.

It does not establish that:

- the matched record actually describes the intended software;
- the record is the canonical method publication;
- the tool satisfies software-landscape eligibility;
- the prespecified candidate role is confirmed; or
- the tool is a citation-chain anchor.

False-positive name or alias matches must be recorded as such.

For compound seed labels such as `CLASSICO/Evidente`, the relationship between
the names must be established from primary or official evidence rather than
assumed.

## 4. Evidence permitted for anchor screening

Substantive decisions must be supported by one or more of the evidence classes
already allowed by the frozen protocol:

1. primary method publication;
2. official software documentation; or
3. official source repository.

Search-result metadata may be used to locate evidence but is not sufficient by
itself for substantive capability or identity claims.

## 5. Tool-identity confirmation

For each candidate, screening must first determine whether at least one
recovered record unambiguously corresponds to the intended seed tool.

Possible values are:

- `confirmed`
- `false_positive_only`
- `not_established`

The evidence source must be recorded.

## 6. Landscape eligibility

After identity confirmation, the four frozen software-landscape criteria are
evaluated independently:

1. publication or stable public documentation describing the method exists;
2. identifiable software implementation exists or existed;
3. tool operates on sequence, SNP, genotype, or phylogenetic data; and
4. tool addresses at least one of the six protocol-defined analytical roles.

Criterion values are:

- `yes`
- `no`
- `not_established`

Landscape decision is:

- `include` only when all four criteria are `yes`;
- `exclude` when a criterion is demonstrably `no`; or
- `pending` when necessary evidence is not established.

Any exclusion reason must be explicit.

## 7. Direct/near-direct role confirmation

The pre-search seed role is a candidate classification, not final evidence.

For landscape-included candidates, primary or official evidence must establish
whether the documented analytical purpose supports:

- `direct`
- `near_direct`
- `other_landscape_role`
- `not_established`

These values are operationally defined in the separately frozen
`CITATION_ANCHOR_ROLE_RUBRIC.md`. Role assignment is based on documented
output semantics relative to the prespecified BRANCHSNV comparison endpoints,
not on the seed-registry label.

This stage does not assign quantitative benchmark eligibility.

## 8. Canonical publication anchor

A citation-chain anchor requires one canonical publication or stable
publication-like record that describes the relevant method/tool.

The anchor must have a reproducible identifier when available, preferentially:

1. DOI;
2. PMID;
3. OpenAlex work identifier;
4. stable authoritative URL if no publication identifier exists.

When multiple publications exist for a tool, the canonical anchor is selected
using method identity and primary-method relevance, not citation count or
convenience.

Later update/version/application papers are not substituted for the canonical
method anchor unless they are the primary source describing the relevant
method.

## 9. Citation-chain anchor decision

A candidate becomes an initial citation-chain anchor only when all of the
following hold:

1. tool identity is `confirmed`;
2. landscape decision is `include`;
3. confirmed role is `direct` or `near_direct`; and
4. a canonical publication anchor is established.

Anchor decision values are:

- `include_as_anchor`
- `do_not_anchor`
- `pending`

A `do_not_anchor` decision does not necessarily mean exclusion from the
software landscape.

## 10. No citation retrieval before freeze

No backward or forward citation retrieval will occur until all nine candidate
rows have been evaluated and the resulting anchor table has been frozen.

Only those rows with `include_as_anchor` will seed the subsequent citation
graph retrieval.

## 11. No search retuning

Anchor-screening results will not be used to alter the completed formal or
high-recall search expressions.

Methods absent from the search remain eligible for discovery through the
prespecified citation-chaining stage.
