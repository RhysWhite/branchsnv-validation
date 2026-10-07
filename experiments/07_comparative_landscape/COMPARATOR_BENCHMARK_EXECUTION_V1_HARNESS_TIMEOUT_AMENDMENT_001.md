# Comparator benchmark execution harness — timeout amendment 001

## Decision

The fixed 86,400-second timeout introduced by the harness implementation
authorization is superseded.

The frozen execution design already specifies:

- Core timeout: 3,600 seconds.
- Scale timeout: 14,400 seconds.

The earlier design did not explicitly classify the three benchmark tip-count
groups as core or scale.

The following classification was subsequently approved explicitly by the
project owner:

| Scenarios | Tips | Class | Timeout (seconds) |
|---|---:|---|---:|
| S001–S050 | 32 | Core | 3600 |
| S051–S100 | 128 | Core | 3600 |
| S101–S150 | 512 | Scale | 14400 |

This classification is a newly approved interpretation, not a historical
assertion that the original frozen design already specified this mapping.

## Source of authority

The existing frozen execution design supplies the timeout values.

The frozen scenario matrix supplies scenario identity, order, and tip count.

The project owner's explicit approval supplies the core/scale classification.

All eight frozen comparator methods receive the same timeout for any given
scenario.

## Supersession

The only superseded clause is:

`resource_contract.timeout_seconds_per_invocation = 86400`

in harness authorization
`COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_IMPLEMENTATION_001`.

Every other provision of that authorization remains unchanged.

The original authorization is retained as immutable historical evidence.

The frozen scientific design, runner, adapter, generator, scenario matrix,
method contracts, runtime identities and source revisions are unchanged.

## Implementation boundary

This amendment authorizes implementing the corrected timeout selection in
the harness. It does not authorize running the canonical benchmark.

Canonical comparator execution, benchmark truth access, scoring and
automatic reruns remain unauthorized.

Stage 1–4 synthetic and mocked validations remain historical implementation
evidence.

The next gate is:

`APPLY_APPROVED_TIMEOUT_POLICY_AND_FREEZE_COMPARATOR_BENCHMARK_EXECUTION_HARNESS_V1`
