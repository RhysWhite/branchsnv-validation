# SNPPar reference-fixture amendment authorization

## Trigger

Authorized toy execution reached SNPPar itself and successfully read the SNP
alignment and reference sequence.

Execution then failed while SNPPar constructed its gene index because the
synthetic GenBank reference contained only a source feature and no CDS.

Inspection of the frozen SNPPar source showed that its gene index is built
from CDS features and that the zero-CDS fallback fails before tree processing.

## Authorized amendment

Only the synthetic SNPPar reference adapter and its focused toy-validation
coverage may be changed.

The reference adapter must:

- receive the scenario variable positions;
- preserve the nucleotide sequence exactly;
- preserve all variable-site coordinates exactly;
- deterministically find the first consecutive three-base interval containing
  no variable position;
- emit one synthetic CDS at that interval with a stable synthetic locus tag;
- ensure that no benchmark variable position lies within the synthetic CDS.

This keeps the artificial annotation outside every scored mutation while
providing the GenBank feature structure required by SNPPar.

## Boundaries

The SNPPar source, source revision, environment, command-line contract,
inference settings and output parser must not change.

Benchmark sequence generation, mutation generation, event truth, trees,
metrics and scenario definitions must not change.

Generation of the full 150-scenario dataset and execution of the full
benchmark remain unauthorized.

## Next gate

`IMPLEMENT_AND_FREEZE_SNPPAR_REFERENCE_FIXTURE_AMENDMENT_V1`
