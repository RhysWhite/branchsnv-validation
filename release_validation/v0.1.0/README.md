# BRANCHSNV v0.1.0 release validation record

This directory preserves the complete fresh validation run performed for
BRANCHSNV v0.1.0 on 12 August 2026.

## Status

**PASS**

The regenerated results were checked with `verify_reproduced_results.py` and
reported:

- BRANCHSNV version: `0.1.0`
- production source identity: verified for all 13 Python source files
- validation-script identity: verified
- deterministic analytical outputs: exact match to the canonical scientific snapshot
- Experiments 01–06 headline and exact pass criteria: verified
- Experiment 04 benchmark protocol: 3 repetitions and 39 measured runs

The production repository state used for the run was
`71b055bdbd8e00ee63afda136b88892aee0062f8`. The validation framework used
for the run corresponds to
`cfb07389191540ca57c9e822b254c279ab903f36`.

## Headline results

- Experiment 01: 128,881 exhaustive-oracle comparisons; 0 mismatches.
- Experiment 02: 10/10 deliberate fault classes detected across 280,216 challenges.
- Experiment 03: 877/877 unambiguous BRANCHSNV substitutions matched SNPPar;
  66 additional SNPPar events were retained as placement-ambiguous.
- Experiment 04: 39/39 benchmark runs completed.
- Experiment 05: 46/46 published focal-branch SNVs reproduced exactly.
- Experiment 06: 31,644 informative comparisons; 30,817 both fixed-exclusive
  and unambiguous, 675 unambiguous but not fixed-exclusive, and 152
  placement-ambiguous; production QC was 1,617/1,617 exact.

## Relationship to the historical publication snapshot

The historical `v0.1.0a1` publication snapshot remains unchanged. This
directory is a separate stable-release validation record. The fresh v0.1.0
run reproduced the deterministic analytical outputs of the canonical
scientific snapshot while recording the stable software version and hardened
production-source identity.

## Performance data

Experiment 04 is intentionally retained in full because it documents the
actual stable-release validation run. Its wall-clock timings, memory
measurements, fitted scaling models, and derived benchmark summaries are
environment-dependent observations. They are not expected to be
byte-identical on another machine or on a later rerun.

The run environment was Python 3.13.15, NumPy 2.3.5, pandas 2.2.3, and
Numba 0.65.1. Detailed hardware and environment metadata are recorded in
`results/04_scalability/run_metadata.json`.

## Integrity

`checksums.sha256` contains SHA-256 hashes for all 47 generated result files.
`record.json` provides a machine-readable summary of the release-validation
record and the source/validation identities used for the run.

The original external capture of the fresh reproduction had SHA-256:

- ZIP: `9734fed6b9661716eab69e1ea45c7ff583bd6569250d8eb93c11e85651058788`
- checksum-manifest file:
  `1dee1736713e82d19b50ae1e66159934a7a8560bc22f3e77271ed2a1955ec1ae`
