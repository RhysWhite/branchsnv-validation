# Comparator benchmark runner implementation v3

## Status

Frozen pre-execution.

This implementation consumes the one-time authorization:

`COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION_V3_001`

Authorization parent commit:

`e5ad0ae3f760eaabcbc085b06e585c14ab182a72`

The implementation consists of exactly three authorized artifacts:

1. `comparator_benchmark_execution_v1_runner.py`
2. `comparator_benchmark_execution_v1_runner_validation.py`
3. `COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION.md`

No existing scientific implementation artifact was changed.

## Frozen implementation identities

Runner SHA-256:

`63a5e45a4082a5709e385e57f3af389769bc4520b5e2a4310bb20fb86e964a33`

Permanent validator SHA-256:

`47a53181b07575eebc8ff42e726c2c210d6500c27ee2f58cb8a6e6039b2f3f15`

## Comparator coverage

The reusable runner covers exactly:

- ARPIP
- FastML
- HomoplasyFinder
- PAML
- PastML
- POUTINE
- SNPPar
- TreeTime

Comparator-specific serialization and prediction normalization are delegated to
the previously frozen adapter layer. The runner does not duplicate the frozen
scientific adapter or metric logic.

## Truth boundary

Comparator command construction, subprocess environments, execution,
native-output parsing and prediction normalization are structurally
truth-blind.

No canonical benchmark truth was read during runner implementation or
validation.

No canonical benchmark scenario was executed during runner implementation or
validation.

No third-party comparator was executed during runner implementation or
validation. Synthetic validation used mocked execution only.

Truth scoring remains a separate later phase. Normalized prediction artifacts
and their SHA-256 identities are finalized before truth may be supplied to any
later scoring stage.

## Runtime execution

Executable, environment and other machine-specific comparator locations are
supplied at runtime. The reusable runner contains no local comparator
installation root.

Each comparator execution uses an isolated method/scenario working directory.

POUTINE retains the frozen wrapper interface while executing from its isolated
working directory: the frozen sibling `compiled` runtime is exposed through a
symlink inside the isolated native directory, and the supplied isolated
environment leads `PATH`. This preserves the wrapper's relative Java classpath
without executing from or modifying the external source tree.

SNPPar retains the frozen isolated environment overlay, including
`PYTHONNOUSERSITE=1`.

The execution record preserves command arguments, working directory,
subprocess environment, runtime identities, comparator-input identities,
elapsed time, exit state, stdout, stderr and native comparator outputs.

## Frozen normalization behavior

PastML uses its projected categorical state output and named output tree,
maps nodes by descendant-tip identity, and restores projected characters to
their frozen genomic positions.

POUTINE scoring normalization uses only the frozen physical-position and
allele-count fields.

SNPPar branch events use the frozen mutation-event parser. Recurrent-site calls
derive from normalized events in `homoplasic_events_all_calls.tsv`.

TreeTime uses the frozen ancestral reconstruction workflow. Recurrent-site
calls derive from normalized ancestral branch events. The TreeTime homoplasy
top-N CLI output is not executed or scored.

Cross-tool branch identity is based only on the frozen canonical
descendant-tip edge identifier.

## Failure handling

The runner records launch failures, timeouts, non-zero exits, missing required
native outputs, ambiguous required output states, malformed outputs and
normalization failures explicitly.

A failed comparator invocation never becomes a zero-accuracy prediction.

Normalized predictions are emitted only after successful execution and
successful frozen normalization.

## Permanent validation

`comparator_benchmark_execution_v1_runner_validation.py` uses synthetic
temporary comparator-facing fixtures only.

It validates:

- the exact eight-method runner boundary;
- frozen artifact identities;
- truth-blind runner interfaces;
- runtime-supplied comparator locations;
- fail-closed input, runtime and frozen-identity checks;
- all eight frozen command plans;
- isolated working directories;
- POUTINE relative-runtime handling;
- SNPPar environment isolation;
- TreeTime ancestral-only execution;
- all eight native-output normalization pathways;
- PastML genomic-coordinate restoration;
- SNPPar and TreeTime recurrent-site normalization;
- canonical descendant-tip branch identities;
- ambiguous native-output failure;
- mocked successful execution and prediction checksumming;
- explicit launch, timeout, non-zero, missing-output and malformed-output
  failures; and
- prevention of real subprocess execution during validation.

The permanent validator passes together with the existing frozen toy
implementation validator and the v3 authorization freeze validator.

## Authorization state

Runner implementation authorizations v1 and v2 remain unconsumed and
superseded and must not subsequently be consumed.

Runner implementation authorization v3 is consumed by this frozen
implementation.

Its rerun authorization remains false.

Canonical comparator benchmark execution remains unauthorized.

Any canonical execution requires a separate subsequent authorization.
