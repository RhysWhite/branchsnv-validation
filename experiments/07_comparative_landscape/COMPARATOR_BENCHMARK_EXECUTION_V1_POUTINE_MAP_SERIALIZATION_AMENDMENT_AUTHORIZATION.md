# POUTINE physical-position map serialization amendment authorization v1

## Status

Authorized, not yet consumed.

Runner-v2 preflight identified one unresolved native-input serialization.

The successful frozen POUTINE smoke evidence uses the following map form:

`1<TAB>markerN<TAB>0<TAB>GENOMIC_POSITION`

There is no header. Marker numbering is one-based and follows the projected
variant-FASTA column order.

The existing generic `positions_text()` adapter is not this format and must
not be substituted.

## Authorized change

Exactly two implementation files may change:

- `comparator_benchmark_execution_v1_impl/adapters.py`
- `comparator_benchmark_execution_v1_impl/toy_validation.py`

A single new adapter,
`poutine_physical_positions_map_text()`, may be added.

For ordered positions `[10, 20, 30, 40]`, it must produce exactly:

    1	marker1	0	10
    1	marker2	0	20
    1	marker3	0	30
    1	marker4	0	40

with a final newline.

Input order is preserved because projected POUTINE FASTA column N must
correspond to `markerN`. Duplicate or non-positive genomic positions fail
closed.

## Boundaries

No POUTINE source, environment, version, command, parameter, phenotype
policy, output parser or scoring rule may change.

No comparator may be executed. No canonical benchmark truth may be read.

Runner implementation v2 remains unconsumed. Because this amendment changes
a frozen adapter identity, runner-v2 authorization must not subsequently be
consumed.

The next gate is:

`IMPLEMENT_AND_FREEZE_POUTINE_MAP_SERIALIZATION_AMENDMENT_V1`
