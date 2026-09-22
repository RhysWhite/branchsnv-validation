# Experiment 07 — Comparative software landscape

`formal_search/` is the frozen formal-search corpus used for screening.

The search comprises 18 prespecified concepts queried against PubMed,
OpenAlex, and bio.tools. OpenAlex bibliographic retrieval is restricted to
title and abstract text to harmonise scope with the PubMed Title/Abstract
queries.

The raw API responses, normalized candidate records, deduplicated records,
per-query counts, retrieval manifest, and SHA-256 checksum manifest are
retained verbatim.

Screening decisions, capability classification, and benchmark eligibility are
downstream analyses and must not modify this formal-search corpus.
