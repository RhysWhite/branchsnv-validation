# Comparator benchmark output-normalization amendment v1

## Status

Frozen.

This amendment closes output-normalization gaps identified during runner
preflight. It does not authorize or perform canonical benchmark execution.

## PastML

PastML reconstructed categorical states are projected only across variable
genomic sites. The amended adapter now converts each projected character back
to its corresponding frozen genomic coordinate before emitting branch-change
events.

Tool-specific internal node names are not trusted. PastML's
`named.tree_tree.nwk` output is now part of the frozen output contract, and
node states are mapped onto the benchmark tree using sorted descendant-tip
sets.

The previously frozen ambiguity rule is unchanged: unresolved or multi-state
node-site calls are encoded as `N` and do not generate a discrete branch
event.

## SNPPar

SNPPar recurrent-site scoring is now explicitly normalized from
`homoplasic_events_all_calls.tsv`.

A genomic position is recurrent when it contains at least two distinct
normalized SNPPar branch events. The reported recurrence count is the number
of distinct normalized branch events at that position.

## TreeTime

The generic descendant-tip mapping helper may be used with TreeTime's
`ancestral_sequences.fasta` and `annotated_tree.nexus`.

TreeTime's executable, ancestral-reconstruction parameters and previously
frozen recurrent-site definition are unchanged.

## Validation

Synthetic toy validation passes, including:

- genomic projected-coordinate preservation;
- descendant-tip mapping with differing internal labels;
- fail-closed tree/node inconsistencies;
- SNPPar recurrent-site normalization.

The existing PastML ambiguity regression passes.

Read-only integration against the already-frozen successful smoke evidence
also passes:

- PastML named-tree mapping preserves the historical ambiguous calls and
  emits no false discrete events;
- SNPPar's two historical homoplasic events normalize to recurrent site 20
  with recurrence count 2;
- TreeTime's historical A20G event survives descendant-tip normalization and
  remains non-recurrent as a single event.

No third-party comparator was executed and canonical benchmark truth was not
read.

## Runner boundary

Runner implementation authorization v1 remains unconsumed. Because this
amendment changes frozen adapter and output-contract identities, that
authorization must not be consumed.

The next gate is:

`REAUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V2`
