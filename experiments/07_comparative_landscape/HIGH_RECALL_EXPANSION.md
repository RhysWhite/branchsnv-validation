# Experiment 07 high-recall expansion

This file records the single generic high-recall search expansion specified
under Amendment 03.

## Purpose

A frozen pre-screening seed-recovery diagnostic found candidate name matches
for 4 of 14 prespecified direct, near-direct, and diagnostic-panel comparator
candidates. This indicated inadequate sensitivity of the original
exact-phrase-oriented database search.

The high-recall expansion therefore broadens analytical vocabulary without
using software names or author names.

## Search blocks

Five generic concept blocks are used:

- HR01 — phylogenetic clade or lineage SNP markers
- HR02 — phylogenetic branch mutation or substitution mapping
- HR03 — ancestral phylogenetic state or sequence inference
- HR04 — phylogenetic homoplasy or recurrent variation
- HR05 — phylogenetic SNP lineage genotyping

The exact source-specific query expressions are frozen in
`high_recall_queries.tsv`.

## Search scope

For PubMed and OpenAlex, bibliographic searching remains restricted to title
and abstract fields.

bio.tools searches use generic concept terms corresponding to the same five
analytical areas.

No software names or author names are used in the expansion queries.

## Pre-retrieval validation

All five OpenAlex OQL expressions were submitted to the OpenAlex OQL
translation/validation endpoint before retrieval.

All five:

- were valid;
- produced zero warnings;
- retained the title/abstract restriction;
- had canonical OQL exactly identical to the submitted expression.

The validation endpoint did not execute the search index. Validation evidence
is retained in `openalex_high_recall_oql_validation.json`.

## Stopping rule

This is the single generic high-recall expansion specified by Amendment 03.

The query vocabulary will not be retuned after retrieval to maximise recovery
of the seed registry. Methods still not recovered may enter through the
prespecified backward/forward citation-chaining stage, with provenance
recorded separately.

No formal eligibility screening, capability classification, or benchmark
selection occurred before specification of this expansion.
