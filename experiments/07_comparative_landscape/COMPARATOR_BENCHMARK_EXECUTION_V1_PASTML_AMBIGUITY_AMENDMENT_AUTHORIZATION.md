# PastML ambiguity-adapter amendment authorization

## Trigger

Smoke testing of PastML 1.9.51 showed that `--out_data` may represent an
ambiguous ancestral reconstruction using multiple rows for the same node.

For example, a node-site state set `{A,G}` is represented by separate rows
rather than by a single scalar value.

The frozen parser currently assigns each row directly to the node key, so a
later row can overwrite an earlier row and incorrectly convert an ambiguous
reconstruction into a single nucleotide state.

## Authorized amendment

Only `parse_tabular_node_states()` in
`comparator_benchmark_execution_v1_impl/adapters.py` may be changed.

The amended parser must aggregate all rows by node and site.

For each node-site combination:

- exactly one distinct A/C/G/T state -> retain that state;
- zero nucleotide states -> `N`;
- more than one distinct nucleotide state -> `N`.

This preserves uncertainty without choosing among equally reported states.

The existing downstream event normalizer already requires both branch-end
states to be single A/C/G/T calls before emitting a branch-change event.
Therefore `N` prevents an ambiguous reconstruction from becoming a discrete
event call.

## Required validation

A focused test must demonstrate that:

1. singleton PastML states remain unchanged;
2. repeated rows representing multiple states become `N`;
3. downstream event normalization emits no event when either branch-end state
   is `N`;
4. all existing toy implementation validation still passes.

## Explicit boundary

This authorization does not permit changes to:

- any other adapter;
- benchmark metrics;
- truth generation;
- benchmark scenarios;
- PastML source, version or inference settings;
- any other comparator;
- full benchmark dataset generation;
- full benchmark execution; or
- production records.

## Next gate

`IMPLEMENT_AND_FREEZE_PASTML_AMBIGUITY_ADAPTER_AMENDMENT_V1`
