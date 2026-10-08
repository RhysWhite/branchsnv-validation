# Comparator benchmark dataset generation v1 authorization

This authorization permits one generation pass for the frozen 150-scenario comparator benchmark dataset after successful completion and freezing of the environment and smoke-test stage.

## Authorized scope

Generation must use:

- the frozen benchmark design;
- the frozen S001–S150 scenario matrix;
- master seed `20261005012417` and the frozen deterministic scenario-seed derivation;
- the frozen truth generator;
- the frozen adapter implementation; and
- `comparator_benchmark_dataset_generation_v1.py` at the identity recorded in the authorization JSON.

The generation harness may write only the benchmark dataset tree under:

`results/07_comparative_landscape/comparator_benchmark_dataset_v1/`

Comparator-facing inputs and benchmark truth must remain in separate subdirectories. The harness must also write `benchmark_dataset_manifest.tsv` and `checksums.sha256`.

Both generation guards already enforced by the frozen generator and generation harness must be enabled only for this authorized execution.

## Explicit boundary

This authorization does **not** permit:

- execution of any third-party comparator;
- execution of the comparator benchmark;
- use of benchmark truth for comparator debugging or parameter tuning;
- modification of the frozen benchmark design or scenario matrix;
- modification of the frozen generator, adapters, source pins or generation harness;
- production-bridge operations; or
- production-ledger mutation.

If dataset generation fails in a way that requires implementation changes, the failure must be preserved and a separately frozen amendment is required before any retry.

## Consumption

This is a one-use authorization. It does not permit a second dataset-generation pass.

The generated dataset, manifest and checksums must be frozen and independently validated before benchmark execution can be authorized.

## Next gate

`FREEZE_COMPARATOR_BENCHMARK_DATASET_GENERATION_RESULTS_V1`
