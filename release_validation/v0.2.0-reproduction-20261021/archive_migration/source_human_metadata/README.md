# BRANCHSNV v0.2.0 — version-specific validation record

**Status: complete fresh reproduction, independently checked; publication release pending.**
This record is tied to BRANCHSNV production commit
`65eb791d9f1a202c3ca8816332a58c036794bd1f` and independent validation
commit `3c64a1d367253ddcaef06c2f07012f347606358e`.

The six experiments were freshly run on `jynx` as Slurm job 2557059 on
21 October 2026 (NZDT), after the missing GNU `time` executable and
fail-fast launcher were corrected. Job 2557058 was an earlier, retained,
incomplete run; **its outputs are not part of this record**.
The full run finished in 6 min 29 s with exit status 0. The retained log ends
with `REPRODUCED RESULTS: PASS`. Publication sign-off and DOI assignment
are separate decisions.

## Why, how, and principal results

The [experiment protocols](../../experiments/) define the question, controls,
inputs, scripts and pass criteria; the original canonical results remain
unchanged in [`../../results/`](../../results/).

| Test | Purpose and scope | Observed result |
|---|---|---|
| [01](../../experiments/01_exact_oracle/) | Equal-cost Sankoff reconstruction against independent exhaustive enumeration on seven small topology–edge cases | 128,881 comparisons; 0 mismatches |
| [02](../../experiments/02_deliberate_faults/) | Detect defined classes of deliberately defective reconstruction | 10/10 fault classes across 280,216 challenges |
| [03](../../experiments/03_published_datasets/) | Compare unambiguous directed changes with independently published SNPPar results | 877/877 BRANCHSNV-unambiguous changes concordant; 66 additional SNPPar events compatible with placement ambiguity |
| [04](../../experiments/04_scalability/) | Measure end-to-end runtime and peak memory for fixed deterministic synthetic inputs | 39/39 completed; 13 configurations × 3 runs; not a portable runtime guarantee |
| [05](../../experiments/05_published_focal_branches/) | Recover **prespecified** published branch SNVs in three examples | 46/46 matched in position and direction; all meet both BRANCHSNV criteria; not a sensitivity estimate |
| [06](../../experiments/06_empirical_cross_classification/) | Compare fixed-exclusive markers with unambiguous reconstruction over five phylogenies | 31,644 informative non-root-adjacent comparisons: 30,817 both, 675 unambiguous-only, 152 placement-ambiguous; 740 root-adjacent recorded separately; 1,617/1,617 production-QC matches |

An additional [NEXUS representation audit](input_equivalence/) tested 30
generated alignments in six conventional/transposed formats across three
analysis modes (540 CLI invocations). All equivalent representations produced
identical output content. This tests representation invariance, **not**
independent biological accuracy. The audit script and per-run SHA256 records
are retained; the test inputs can be deterministically regenerated.

## Contents and integrity

- `results/` — 47 result files; [`checksums.sha256`](checksums.sha256) records each byte identity.
- [`record.json`](record.json) — production and validation commit identities, dependency versions, export provenance and verification outcomes.
- `execution/` — unmodified Slurm reproduction log, status, 13 source-file hashes and exact run identity.
- `environment/` — explicit Conda and `pip freeze` records.
- `experiment04/input_manifest.json` — regenerated deterministic input hashes; the original benchmark input generator is [here](../../experiments/04_scalability/generate_inputs.py).
- `input_equivalence/` — independent audit script, summary and 540 execution records.
- `supplementary_checksums.sha256` — digest for each supporting evidence file.
- [`verify_counts.py`](verify_counts.py) — independent, dependency-free audit of retained table counts and orientation equivalence.
- [`MANUSCRIPT_CLAIM_CROSSWALK.tsv`](MANUSCRIPT_CLAIM_CROSSWALK.tsv) — exact source, script, output and metadata paths for manuscript drafting.
- [`MANUSCRIPT_REFERENCE_EXAMPLES.md`](MANUSCRIPT_REFERENCE_EXAMPLES.md) — concise, version-scoped citation examples without an invented DOI.

From the **validation repository root**, check the stable-result schema:

```bash
python verify_release_validation_record.py \
  --record-dir release_validation/v0.2.0 \
  --expected-version 0.2.0 \
  --expected-production-commit 65eb791d9f1a202c3ca8816332a58c036794bd1f \
  --expected-validation-framework-commit 3c64a1d367253ddcaef06c2f07012f347606358e
(cd release_validation/v0.2.0 && sha256sum -c supplementary_checksums.sha256)
python release_validation/v0.2.0/verify_counts.py
```

To reproduce the experiments afresh, follow `run_completed_experiments.sh` and
`release_candidate_check.sh` using the pinned source commits and environment.
Experiment 03 downloads the published upstream inputs and checks their hashes;
Experiment 04 regenerates 11 deterministic alignment/tree configurations and
uses GNU `time` v1.10. The performance measurements will vary between systems.

## Citation boundary

The manuscript may reference an exact versioned **file path** in this record,
but **a Zenodo version DOI and manuscript reference number must not be assigned
until the public archive has been created, downloaded and its files verified**.
The historical v0.1.0 DOI does not identify this record. Experiment 07 RC3's
comparative results are not included and remain scientifically unsigned.
