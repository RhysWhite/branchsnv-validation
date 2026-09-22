# Completed merged-universe seed-recovery diagnostic

This audit freezes the prespecified seed-name recovery diagnostic run against
the completed Experiment 07 merged search universe.

The production diagnostic was executed from commit:

`a0d97c38245345a7528144149601e4175849a4de`

using the frozen execution script SHA-256:

`fcf05e61bbaa5d3e39396ba4f383cc2b83ff00effb23b82b1dad0d2e77d3a737`

## Result

- prespecified seed tools: 31
- candidate-name recovered: 23
- not recovered by name: 8
- candidate evidence rows: 101
- recovered by the formal stage: 8
- recovered by the high-recall stage: 21
- recovered only after the high-recall expansion: 15

Candidate name recovery is not equivalent to confirmed software recovery.
Every candidate match remains pending human confirmation.

The eight seeds not recovered by name are:

- Clade-O-Matic
- PHYLIP DNAPARS
- TB-Profiler
- SPANDx
- Snippy
- ClonalFrameML
- FastTree
- ETE 3

Per the prespecified stopping rule, this result cannot be used to retune the
search expressions. Unrecovered prespecified seeds proceed through the
citation-chaining route.

## Ordering validation

An auxiliary formal-stage byte-comparison performed after execution identified
one historical stable-sort tie involving two SNPPar/OpenAlex/Q11 evidence
rows. The evidence-row multiset was identical and deterministic full-row
canonicalization was byte-identical.

This was documented before validator modification in Amendment 05 and the
`merged_seed_recovery_ordering` audit.

The validator was subsequently hardened to represent that criterion correctly.
The production execution script and production diagnostic output were not
modified or regenerated.

No eligibility screening, capability classification, benchmark selection, or
human confirmation had occurred when this result was frozen.
