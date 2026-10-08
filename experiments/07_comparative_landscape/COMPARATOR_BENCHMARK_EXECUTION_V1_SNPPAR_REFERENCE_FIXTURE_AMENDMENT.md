# SNPPar reference-fixture amendment v1

The synthetic GenBank helper now requires the scenario variable positions and
adds exactly one three-base synthetic CDS.

The CDS is placed at the first consecutive three-base interval containing no
variable position and receives the stable locus tag `SYNTH_CDS_001`.

The nucleotide sequence is unchanged, and no benchmark variable position is
inside the synthetic CDS.

This supplies the feature structure required by SNPPar without changing the
benchmark sequence, mutation truth, tree, metrics, SNPPar source, environment,
execution settings or output interpretation.

The full benchmark remains unauthorized.

## Next gate

`RERUN_SNPPAR_TOY_SMOKE_WITH_FROZEN_REFERENCE_FIXTURE_V1`
