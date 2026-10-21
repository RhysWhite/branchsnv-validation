# Comparator environment build and smoke-test v1

Status: PROPOSED — NOT YET AUTHORISED

Parent freeze:
COMPARATOR_BENCHMARK_EXECUTION_IMPLEMENTATION_V1

Requested next gate:
AUTHORIZE_COMPARATOR_BENCHMARK_ENVIRONMENT_BUILD_AND_SMOKE_TEST_V1

## Permitted scope following explicit authorisation

1. Build eight isolated comparator environments.
2. Use only frozen comparator source versions.
3. Record exact dependencies and environment identities.
4. Run noncanonical toy fixtures for smoke validation.
5. Verify nucleotide input/output contracts.
6. Validate edge identity and missing-data handling.
7. Resolve PastML ancestral-state export.
8. Resolve POUTINE CLI invocation.
9. Preserve commands, logs, failures and resource metrics.
10. Independently review all smoke-test evidence.

## Prohibited

- Generating canonical benchmark datasets.
- Running any of the 150 canonical scenarios.
- Modifying frozen truth-generator or metric definitions.
- Tuning against canonical benchmark truth.
- Altering production screening results.
- Reporting smoke-test accuracy as benchmark accuracy.

## Required completion evidence

- Reproducible isolated environments.
- Exact installed source/dependency identities.
- Successful or explicitly failed smoke tests.
- Validated comparator output adapters.
- Independently reviewed execution manifest.
- Explicit subsequent authorisation for canonical execution.
