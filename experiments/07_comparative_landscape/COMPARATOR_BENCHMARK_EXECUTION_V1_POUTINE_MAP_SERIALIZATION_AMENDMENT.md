# POUTINE physical-position map serialization amendment v1

## Status

Frozen.

This amendment resolves the final native-input serialization gap identified
during comparator-runner preflight.

## Frozen serialization

The adapter function

`poutine_physical_positions_map_text()`

serializes each projected POUTINE site as:

`1<TAB>markerN<TAB>0<TAB>GENOMIC_POSITION`

There is no header.

`markerN` is numbered from one in the same order as the projected variant
FASTA columns. Input genomic-position order is therefore preserved.

Duplicate or non-positive genomic positions fail closed.

## Validation

For genomic positions `[10, 20, 30, 40]`, the new serializer reproduces the
already-frozen successful POUTINE smoke `toy.map` byte-for-byte.

The complete synthetic toy-validation suite passes.

The frozen POUTINE output parser continues to normalize the historical
successful smoke output to recurrent genomic position 20 with reported
recurrence count 2.

The existing PastML ambiguity regression also passes.

No third-party comparator was executed and no canonical benchmark truth was
read.

## Unchanged contracts

This amendment does not change POUTINE's source pin, environment, version,
run command, inference parameters, projected FASTA serialization, dummy
phenotype policy, output parser or scoring contract.

It does not change the benchmark dataset, scenarios, metrics or truth
generator.

## Runner authorization boundary

Runner implementation authorization v2 remains unconsumed.

Because this amendment changes the frozen adapter identity, runner-v2
authorization must not be consumed and is superseded.

The next gate is:

`REAUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V3`
