# Comparator benchmark execution implementation authorization v1

## Authorization

This authorization permits one implementation pass for the benchmark design frozen in `COMPARATOR_BENCHMARK_EXECUTION_DESIGN_V1`.

The implementation may add the independent truth-generator code, deterministic seed and edge-identity machinery, truth-blind metric engine, canonical input/output adapters, noncanonical toy fixtures, unit tests, and exact per-method environment/install recipes.

It may also perform source/documentation research needed to pin exact comparator versions, releases, commits, source hashes or container digests.

## Hard boundary

This authorization does **not** permit:

- installation of any third-party comparator;
- execution of any third-party comparator;
- building comparator conda/container environments;
- execution of networked install commands;
- generation of the canonical 150-scenario benchmark dataset;
- execution of the canonical benchmark;
- tuning against benchmark truth;
- any production-screening bridge or production-ledger mutation.

Environment specifications and commands may be written and statically validated, but not executed.

Unit tests must use synthetic noncanonical toy fixtures only.

## Next gate

After the implementation itself is frozen and independently validated:

`AUTHORIZE_COMPARATOR_BENCHMARK_ENVIRONMENT_BUILD_AND_SMOKE_TEST_V1`
