# Comparator benchmark feasibility assessment authorization v1

## Authorization

This authorization permits one source-backed feasibility assessment of the 29 method families frozen in `branchsnv_direct_near_comparators_v1.tsv`.

The assessment may use primary publications, official software repositories, official documentation, package registries, release archives and other stable authoritative sources. It may determine software/code availability, licensing, version pinning, installability, documented inputs and outputs, environment constraints, endpoint overlap, output mappability, automation status and benchmark-feasibility class.

The assessment must cover all 29 frozen method families in one campaign.

## Boundaries

This authorization does **not** permit software installation, software execution, benchmark-dataset execution, environment/container construction, production-bridge work, production-ledger mutation, expansion beyond the frozen 29-method universe, or reclassification of the frozen direct/near-direct scientific comparator status.

Feasibility classification is a separate layer from scientific comparator classification.

## Authorized output

The one-time assessment may produce the canonical `comparator_benchmark_feasibility_v1` result set under `results/07_comparative_landscape/comparator_benchmark_feasibility_v1/`.

The assessment result must remain pre-execution. Any installation or benchmark execution requires a later separately frozen design and authorization.

## Next gate

`FREEZE_COMPARATOR_BENCHMARK_FEASIBILITY_RESULTS_V1`
