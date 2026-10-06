# PastML ambiguity-adapter amendment v1

Smoke testing of PastML 1.9.51 demonstrated that `--out_data` can represent an
uncertain ancestral state using multiple rows for the same node.

The previous parser assigned each row directly to the node key. A later row
could therefore overwrite an earlier row and incorrectly reduce a multi-state
reconstruction to one nucleotide.

The amended `parse_tabular_node_states()` aggregates rows by node and site.

For each node-site combination:

- one distinct A/C/G/T state is retained;
- no nucleotide state is encoded as `N`;
- more than one distinct nucleotide state is encoded as `N`.

No other adapter, metric, truth-generation rule, benchmark scenario, PastML
source revision, PastML version or PastML inference setting was changed.

A focused regression test verifies preservation of singleton states,
conservative handling of multi-state reconstructions, suppression of discrete
branch events at uncertain endpoints, and retention of ordinary resolved
branch-event detection.

The pre-existing toy implementation validation also passes.

## Next gate

`RESUME_COMPARATOR_BENCHMARK_ENVIRONMENT_AND_SMOKE_TEST_V1`
