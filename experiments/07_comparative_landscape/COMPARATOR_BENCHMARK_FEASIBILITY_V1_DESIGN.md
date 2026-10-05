# Comparator benchmark feasibility design v1

## Purpose

This freeze defines the assessment protocol for determining which of the 29 frozen direct/near-direct BRANCHSNV comparator method families can support a fair and reproducible quantitative benchmark.

It does **not** authorize installation or execution of comparator software and does not change the scientific classification frozen in `comparative_landscape_v1`.

## Frozen input

The sole method-family universe for this feasibility assessment is:

`results/07_comparative_landscape/comparative_landscape_v1/branchsnv_direct_near_comparators_v1.tsv`

This contains 29 method families: 3 direct and 26 near-direct. The direct set remains exactly SNPPar, SubRecon, and TreeTime.

Supporting/relevant methods and frozen noncomparators are outside this feasibility gate.

## Assessment principle

Feasibility is separate from scientific relevance. A method can remain a valid direct or near-direct comparator while being unsuitable or impossible to execute in a reproducible benchmark.

Each method family must be assessed from primary/authoritative sources for software/code availability, licensing, version pinning, installability, environment reproducibility, documented inputs and outputs, required phylogenetic/alignment preconditions, supported character type, overlap with the frozen BRANCHSNV endpoints, output mappability, automation, and blocking constraints.

Uncertainty remains explicit.

## Feasibility classes

- `quantitative_benchmark_candidate`: reproducibly executable and sufficiently comparable at the relevant endpoint(s).
- `endpoint_specific_benchmark_candidate`: fair quantitative comparison is possible only for one or a subset of overlapping endpoints.
- `contextual_comparator_only`: scientifically relevant, but a quantitative head-to-head comparison would be task-mismatched or otherwise invalid.
- `blocked_reproducibility`: scientifically benchmarkable in principle, but reproducible execution is blocked.
- `unresolved`: source evidence is insufficient for a terminal feasibility decision.

## Fairness boundary

The assessment must not force all 29 methods into executable benchmarking. It must not penalize methods merely for age, speed, popularity, or inconvenience. It must not collapse different scientific tasks into one generic accuracy metric.

No installation, software execution, benchmark dataset execution, production bridge, or scientific reclassification is authorized by this design freeze.

## Next gate

`AUTHORIZE_COMPARATOR_BENCHMARK_FEASIBILITY_ASSESSMENT_V1`
