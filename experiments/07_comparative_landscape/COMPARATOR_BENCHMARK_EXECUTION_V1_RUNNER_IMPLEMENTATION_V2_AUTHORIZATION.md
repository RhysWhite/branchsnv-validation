# Comparator benchmark runner implementation v2 authorization

## Status

Authorized, not yet consumed.

Runner implementation authorization v1 was never consumed. It was superseded
when the output-normalization amendment changed the frozen adapter and
environment-recipe identities.

This v2 authorization is pinned to the frozen state at commit
`05312d6ddbb216731631fb203817d2e17f2e5204`.

## Authorized implementation

Exactly three new runner artifacts may be created:

1. `comparator_benchmark_execution_v1_runner.py`
2. `comparator_benchmark_execution_v1_runner_validation.py`
3. `COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION.md`

The runner must orchestrate the eight frozen comparator workflows without
changing their scientific contracts.

## Truth boundary

Runner implementation and validation are truth-blind.

No canonical benchmark truth may be read. No frozen S001-S150 benchmark
scenario may be executed. No third-party comparator may be executed during
implementation or validation.

Comparator-facing execution and normalization must remain structurally
separate from later truth scoring.

## Frozen normalization contracts

PastML must use the frozen `reconstructed_states.tsv` plus
`named.tree_tree.nwk` contract, descendant-tip-set node mapping, and projected
genomic-coordinate normalization.

SNPPar homoplasy calls must derive from normalized branch events parsed from
`homoplasic_events_all_calls.tsv`.

TreeTime recurrent sites must derive from normalized ancestral branch events;
the top-N homoplasy CLI output is not scored.

Cross-tool branches are identified only through the frozen canonical
descendant-tip edge identity.

## Runtime configuration

Executable, environment, source and build locations are runtime-supplied.
Reusable runner code must not hard-code local comparator installation roots.

## Failure handling

Timeouts, non-zero exits, missing required outputs, malformed outputs and
normalization failures are completion failures. They must never be converted
to zero-accuracy predictions.

The next gate is:

`IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_RUNNER_V2`
