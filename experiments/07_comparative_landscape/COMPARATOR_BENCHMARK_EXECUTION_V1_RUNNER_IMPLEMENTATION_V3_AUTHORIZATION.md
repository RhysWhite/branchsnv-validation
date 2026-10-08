# Comparator benchmark runner implementation v3 authorization

## Status

Authorized, not yet consumed.

Runner implementation authorizations v1 and v2 were never consumed.

Both were superseded by upstream frozen interface amendments before runner
implementation began.

The complete comparator-facing adapter layer is now frozen at commit:

`7cc3cac6bd7a70843f494354c262eedba5e4ab66`

This v3 authorization is the current runner implementation authorization.

## Authorized implementation

Exactly three new artifacts may be created:

1. `comparator_benchmark_execution_v1_runner.py`
2. `comparator_benchmark_execution_v1_runner_validation.py`
3. `COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION.md`

No existing scientific implementation file may be changed.

## Truth and execution boundary

Runner implementation and validation are truth-blind.

No canonical benchmark truth may be read.

No S001-S150 scenario may be executed.

No third-party comparator may be executed during implementation or
validation.

Synthetic validation may mock subprocess execution.

## Frozen comparator interfaces

All comparator-specific input generation and output normalization must use
the frozen adapter layer.

PastML uses projected categorical states plus `named.tree_tree.nwk`,
descendant-tip mapping and genomic-coordinate restoration.

POUTINE uses:

- `poutine_variant_fasta_text()`
- `poutine_dummy_phenotype_text()`
- `poutine_physical_positions_map_text()`
- `parse_poutine_result()`

The frozen POUTINE map row format is:

`1<TAB>markerN<TAB>0<TAB>GENOMIC_POSITION`

SNPPar recurrent-site scoring derives from normalized events in
`homoplasic_events_all_calls.tsv`.

TreeTime recurrent sites derive from normalized ancestral branch events.
TreeTime homoplasy top-N output is not executed or scored.

Cross-tool branch identity is based only on the frozen canonical
descendant-tip edge identifier.

## Runtime configuration

Executable, environment, source and build locations must be runtime supplied.

The reusable runner must not hard-code local comparator installation roots.

Each method/scenario execution uses an isolated working directory.

## Failure handling

Timeouts, non-zero exits, missing required native outputs, malformed outputs
and normalization failures are explicit completion failures.

Failures are never converted into zero-accuracy predictions.

Prediction normalization is completed before truth is supplied to any later
scoring stage.

## Historical authorizations

Runner implementation authorization v1 remains unconsumed and superseded.

Runner implementation authorization v2 remains unconsumed and superseded.

Neither may subsequently be consumed.

The next gate is:

`IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_RUNNER_V3`
