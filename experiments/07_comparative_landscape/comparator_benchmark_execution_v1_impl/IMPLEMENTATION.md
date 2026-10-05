# Comparator benchmark execution implementation v1

This implementation is **pre-execution**. It implements the independent truth generator, canonical edge identity, deterministic adapters, truth-blind metrics, exact comparator source pins, and static environment/invocation recipes.

It does not install or execute any comparator and does not generate the canonical 150 benchmark datasets.

## Independent truth generator

The generator is standard-library Python and imports neither BRANCHSNV nor comparator code.

A single frozen master seed (`20261005012417`) deterministically derives each scenario seed. Canonical generation is additionally guarded by an environment authorization token and fails closed without it.

Every dataset contains 40 event sites. The recurrence regimes are operationalized as:

- `unique_only`: 40 unique sites;
- `parallel`: 20 unique + 20 parallel sites;
- `convergent`: 20 unique + 20 convergent sites;
- `reversal`: 20 unique + 20 reversal sites;
- `mixed_recurrence`: 10 unique + 10 parallel + 10 convergent + 10 reversal sites.

Parallel sites contain two independent identical state transitions. Convergent sites contain two independent arrivals at the same derived nucleotide from different ancestral states. Reversal sites contain a forward mutation followed by a descendant reversion.

Branch lengths are positive and derived from the explicit event count on each edge divided by sequence length, with a `1e-6` floor on zero-event edges. Tree inference is not part of the benchmark.

## Canonical edge identity

Cross-tool branch identity is the SHA-256 of the newline-separated sorted descendant-tip set for each rooted edge. Tool-specific internal-node labels are never used as cross-tool identifiers.

## Missing observations

The `missing_5pct` condition masks exactly 5% of tip × variable-site cells as `N`, using a deterministic seed derived from the scenario seed.

Adapters preserve missingness according to each tool contract. For SNPPar, `N` becomes `-`; for PastML, it becomes an empty/missing table value.

## Metrics

Branch-change calls are scored as exact tuples:

`(edge_id, position, ancestral_state, derived_state)`

Homoplasy is scored primarily as recurrent-site detection.

If both truth and prediction contain no recurrent sites, site precision/recall/F1 are defined as 1.0. Completion failures are not passed to the metric engine as zero-accuracy calls.

## Source pins

All eight comparator repositories are pinned to exact commits captured by read-only `git ls-remote` at the authorized implementation boundary.

Release tags are used for PAML, PastML, SNPPar and TreeTime. ARPIP, FastML, HomoplasyFinder and POUTINE are frozen to exact repository snapshots.

## Static environment recipes

Environment recipes are authored but not executed.

POUTINE's public README does not expose its complete command-line flag contract in text. The implementation therefore explicitly refuses to guess an invocation. Its exact CLI is a required deliverable of the later authorized smoke-test gate.

PastML similarly requires smoke validation of the exact machine-readable ancestral-state export/API before canonical execution.

No canonical benchmark run is authorized by this implementation freeze.
