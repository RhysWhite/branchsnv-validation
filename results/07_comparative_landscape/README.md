# Experiment 07 — Comparative software landscape

`formal_search/` is the frozen formal-search corpus used for screening.

The initial formal database stage comprised 18 prospectively specified
query families derived from the analytical roles defined in the Experiment 07
protocol and queried against PubMed, OpenAlex, and bio.tools. The number 18 was
an operational decomposition of those analytical roles, not an assumption that
18 query families were exhaustive.

Before formal eligibility screening or capability classification, the
sensitivity of this initial exact-phrase-oriented search was assessed using the
prospectively recorded seed registry. Candidate-name matches were found for
only 4 of 14 direct, near-direct, or diagnostic-panel comparator candidates.
This demonstrated that the initial formal search had insufficient sensitivity
to serve as the sole discovery mechanism.

A single generic high-recall expansion was therefore specified and frozen
before its retrieval. It broadened vocabulary across five analytical concept
blocks without using software or author names. Query vocabulary was not
subsequently retuned to maximise recovery of known tools. Remaining relevant
methods could enter through the separately prespecified backward and forward
citation-chaining stage.

OpenAlex bibliographic retrieval is restricted to title and abstract text to
harmonise search scope with the PubMed Title/Abstract queries.

The raw API responses, normalized candidate records, deduplicated records,
per-query counts, retrieval manifest, and SHA-256 checksum manifest are
retained verbatim.

Screening decisions, capability classification, and benchmark eligibility are
downstream analyses and must not modify this formal-search corpus.

## Citation-chain Wave 0

`citation_wave_0/` is the frozen first-wave citation-chain corpus generated
from the eight methods that satisfied the prospectively frozen citation-anchor
screening procedure. Eight was the outcome of applying that procedure, not a
prespecified target number of anchors. Citation edges were retrieved using
OpenAlex and OpenCitations.

The tracked production corpus contains citation edges, normalized neighbour
records, source-direction status, OpenCitations partition and snapshot
reconciliation ledgers, the retrieval manifest, and SHA-256 checksums.

Raw API responses are retained locally for provenance but are not tracked in
Git because of their size. Failed and pre-freeze retrieval runs are retained
as development evidence and likewise excluded from the production corpus.

Downstream comparator screening and capability classification must not modify
the frozen Wave 0 production files.

Scientific and operational design decisions, including the distinction between
rule-derived outcomes and pragmatic implementation bounds, are documented in
`experiments/07_comparative_landscape/SCIENTIFIC_DECISION_LEDGER.md`.
