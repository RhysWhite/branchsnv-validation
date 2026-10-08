# Comparator benchmark execution v1: environment-build and smoke-test authorization

This authorization advances the frozen comparator benchmark implementation to
environment construction and noncanonical smoke testing only.

## Authorized scope

Exactly eight frozen comparator workflows may be installed in isolated
environments from their already frozen source pins:

- ARPIP
- FastML
- HomoplasyFinder
- PAML
- POUTINE
- PastML
- SNPPar
- TreeTime

Network access is permitted only as required to retrieve the frozen source
revisions and dependencies during environment construction.

Each comparator may then be executed on dedicated noncanonical toy fixtures to
validate installation, invocation, input adapters, output parsing and
normalization.

The smoke stage must also resolve the two implementation items deliberately
left open at the previous freeze:

1. capture POUTINE's command-line help and freeze its exact non-GWAS homoplasy
   invocation and required input paths;
2. determine and freeze PastML's exact machine-readable ancestral-state output
   or API.

Commands, environment identities, dependency versions, stdout, stderr and
other execution metadata must be retained.

## Explicit boundary

This authorization does **not** authorize:

- generation of the canonical 150-scenario dataset;
- execution of the canonical benchmark;
- inspection of canonical truth for tuning or debugging;
- modification of the frozen benchmark design;
- modification of the frozen comparator source pins;
- silent patching of third-party software;
- production-bridge operations;
- production-ledger mutation; or
- redistribution of third-party source or binaries.

If a comparator cannot be installed or smoke-tested under the frozen contract,
the failure must be retained as evidence. Any remediation requiring a changed
source pin, parameter contract, adapter or implementation requires a separately
recorded amendment before proceeding.

## Consumption

This is a one-use authorization. Completion of the environment-build and
smoke-test stage must be frozen in a separate immutable result record before
canonical dataset generation or benchmark execution can be authorized.

## Next gate

`FREEZE_COMPARATOR_BENCHMARK_ENVIRONMENT_AND_SMOKE_RESULTS_V1`
