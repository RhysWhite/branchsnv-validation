# Comparator benchmark output-normalization amendment authorization v1

Runner preflight identified normalization contracts that must be completed
before canonical benchmark execution.

## PastML

PastML receives only the frozen genomic variable sites as categorical columns.
The existing parser correctly preserves ambiguity, but its projected state
strings cannot be passed directly to the full-sequence event converter because
that would emit projected indices rather than genomic coordinates.

This amendment therefore authorizes an explicit projected-coordinate event
normalizer and descendant-tip-set node mapping. The already-observed
`named.tree_tree.nwk` PastML smoke artifact is added to the frozen output
contract.

## SNPPar

The frozen SNPPar workflow emits `homoplasic_events_all_calls.tsv`. This
amendment authorizes deterministic conversion of its normalized branch events
to recurrent genomic-site calls using two or more distinct branch events at
the same position.

## Boundary

No comparator may be executed. No canonical S001-S150 truth may be read.
No scenario, metric, source pin, software version, inference parameter,
generator or benchmark dataset may change.

The previously frozen runner-implementation authorization remains unconsumed.
Because this amendment will change frozen adapter/output-contract identities,
that authorization must not subsequently be consumed. Runner implementation
must be reauthorized against the amended identities.

The next gate is:

`IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_OUTPUT_NORMALIZATION_AMENDMENT_V1`
