# Comparator benchmark execution harness implementation authorization

## Status

Authorized, not yet consumed.

Authorization ID:

`COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_IMPLEMENTATION_001`

Parent commit:

`f4417aed9cafd39c8a0d8c206f61f719b64a4a65`

Exactly three future implementation artifacts are authorized:

1. `comparator_benchmark_execution_v1_harness.py`
2. `comparator_benchmark_execution_v1_harness_validation.py`
3. `COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_IMPLEMENTATION.md`

No existing runner or scientific implementation artifact may be modified.

The future harness must orchestrate exactly 150 frozen scenarios by exactly
eight frozen methods, for 1,200 deterministic method/scenario invocations.

Scenario seeds must come directly from the frozen
`generator.scenario_seed()` implementation.

Canonical execution will be required to use the frozen bubblewrap sandbox:
host root read-only, designated result root writable, private `/tmp`, and an
unshared network namespace.

Each method/scenario invocation must use a fresh worker process and record
invocation-specific peak RSS.

Comparator completion failures remain explicit failures and are not
automatically rerun.

## Truth boundary

Harness implementation and validation are truth-blind.

No canonical S001-S150 benchmark scenario may be executed during harness
implementation or validation.

No third-party comparator may be executed during harness implementation or
validation.

Benchmark truth may not be read, traversed, used for debugging, or supplied
to any runner/harness interface.

No scoring is permitted.

## Execution boundary

Canonical benchmark execution is still unauthorized.

The canonical execution result root must remain absent during harness
implementation and validation.

The next gate is:

`IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_EXECUTION_HARNESS_V1`
