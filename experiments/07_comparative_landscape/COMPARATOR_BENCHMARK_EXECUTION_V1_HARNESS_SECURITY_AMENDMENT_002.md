# Comparator Benchmark Execution V1 — Security Amendment 002

## Status

**FROZEN_SCOPE_PRE_IMPLEMENTATION**

This amendment authorizes implementation and synthetic validation of
truth isolation and production-shaped orchestration. It does not
authorize running the canonical benchmark.

## Reason

The original implementation authorization requires:

- `--ro-bind / /`
- `--bind RESULT_ROOT RESULT_ROOT`

A read-only bind of the host root prevents writing to most host paths,
but leaves host files readable. That is insufficient to establish
benchmark-truth isolation.

## Supersession

Amendment 002 supersedes only the original authorization's
`sandbox_contract.host_root_read_only` and
`sandbox_contract.required_arguments[0:2]` for the new
production-shaped isolation pathway.

The original records remain unchanged.

The original sandbox's network restriction, private temporary
filesystem, parent-lifetime restriction and restricted writable
workspace remain requirements.

The Stage 3–5 synthetic sandbox may be retained for regression
validation, but it must not become the production comparator sandbox.

## Isolation requirements

Production-shaped comparator processes must receive an independently
verified, explicitly allowlisted filesystem view.

The host root, unrestricted HOME, repository and dataset parent must
not be exposed through broad bind mounts.

Only the permitted per-invocation input view may be supplied.

Executable and runtime dependencies must be resolved and checked,
including interpreters, libraries and runtime data.

Validation must cover symlinks, path escapes, mount overlap,
inherited file descriptors, `/proc` and changes to validated paths.

Synthetic truth sentinels must be inaccessible through direct,
indirect and descriptor-based paths. Any successful access fails
the implementation gate.

No canonical benchmark truth may be inspected during testing.

## Production-shaped orchestration

The implementation must preserve:

- 150 scenarios and eight frozen methods;
- 1,200 unique, method-major invocations;
- 800 core invocations with 3,600-second timeouts;
- 400 scale invocations with 14,400-second timeouts;
- fresh isolated workers;
- the frozen runner and native-output contracts;
- independently recorded elapsed time and peak child RSS;
- durable, checksummed, non-overwriting execution records;
- continuation after classified completion failures; and
- immediate termination after infrastructure or integrity failures.

Actual comparator execution remains disabled in the absence of
a separate, explicit and independently validated authorization.

## Preserved scientific boundaries

The frozen design, original implementation authorization, timeout
Amendment 001, scenario matrix, runner, comparator sources and
runtime identities remain unchanged.

No canonical input access, canonical output creation, comparator
execution, benchmark truth access, scoring or automatic rerun is
authorized by Amendment 002.

## Implementation and freeze sequence

1. Freeze Amendment 002 separately from the harness files.
2. Implement private-root truth isolation and synthetic adversarial tests.
3. Implement production-shaped orchestration behind a fail-closed gate.
4. Independently validate the complete harness using synthetic inputs.
5. Freeze the three authorized implementation artifacts separately.
6. Require another explicit authorization before canonical execution.

The amendment's approval is documented in the conversation; this
record is not a cryptographic signature or execution authorization.
