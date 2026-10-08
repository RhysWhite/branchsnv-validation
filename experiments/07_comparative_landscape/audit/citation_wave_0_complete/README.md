# Experiment 07 citation-chain Wave 0 freeze audit

This directory records the completion state of the frozen Wave 0
citation-chain retrieval.

The authoritative production corpus is:

`results/07_comparative_landscape/citation_wave_0/`

The retrieval was generated from an immutable committed implementation and
passed the production provenance, checksum, source-matrix, credential-leak,
and repository-hygiene gates.

The production corpus contains 33,071 citation edges and 33,071 normalized
neighbour records across the eight methods that satisfied the prospectively
frozen citation-anchor screening procedure. The number eight was therefore a
rule-derived outcome rather than a prespecified anchor count. All 32 expected
source-direction operations reached an accepted terminal state: 31 completed
without reconciliation and one completed using the explicitly validated
OpenCitations provider-reconciliation pathway.

The reconciled source-direction required three consecutive byte-identical
reconciled snapshots. All discrepant OpenCitations identifiers were directly
verified before acceptance.

Large raw API responses are intentionally not tracked in Git. They are
retained separately as retrieval provenance. Failed and pre-freeze runs are
development evidence and are not part of the authoritative production corpus.

Downstream screening, comparator classification, and benchmark-selection
steps must treat the frozen Wave 0 corpus as immutable input.

## Methodological decision audit

Scientific-scope decisions, rule-derived numerical outcomes, source-selection
rationale, operational thresholds, safeguards, and residual limitations are
recorded in:

`experiments/07_comparative_landscape/SCIENTIFIC_DECISION_LEDGER.md`

The decision ledger explicitly distinguishes scientific criteria from pragmatic
implementation bounds. It does not modify the frozen Wave 0 corpus.
