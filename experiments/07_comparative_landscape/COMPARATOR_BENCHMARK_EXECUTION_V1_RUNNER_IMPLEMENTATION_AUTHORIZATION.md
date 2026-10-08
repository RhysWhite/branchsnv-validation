# Comparator benchmark runner implementation authorization v1

A narrowly scoped one-use authorization is granted to implement and freeze the
truth-blind comparator benchmark runner.

The runner may orchestrate the eight already-frozen comparator workflows and
their frozen adapters, but this authorization does **not** permit execution of
the canonical 150-scenario benchmark or execution of any third-party
comparator.

## Truth boundary

Comparator execution must be structurally truth-blind. Benchmark truth must
not be available to command construction, subprocess environments, native
output parsing, prediction normalization, parameter selection or failure
handling.

The eventual scoring phase must be distinct from execution. Truth may only be
introduced after normalized predictions have been finalized and their
identities recorded.

## Frozen scientific contracts

The benchmark dataset, scenario matrix, method matrix, adapters, environment
recipes, metrics, source pins and TreeTime homoplasy amendment remain frozen.
The runner is orchestration code only and may not alter their scientific
contracts.

Machine-specific comparator installation paths must be supplied at runtime and
must not be embedded in reusable repository code.

## Validation boundary

Implementation validation must use synthetic temporary fixtures only. It must
not execute any comparator and must not read any canonical S001-S150 truth.

The next gate is:

`IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_RUNNER_V1`
