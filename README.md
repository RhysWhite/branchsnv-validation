# BRANCHSNV publication validation

Reproducible experiments supporting the evaluation of
[BRANCHSNV](https://github.com/RhysWhite/branchsnv), a dependency-free command-line
tool for identifying fixed clade-associated nucleotide states and reconstructing
single-nucleotide substitutions on selected branches of rooted phylogenetic trees.

This repository is separate from the production software. It contains the
manuscript-specific validation code, canonical result files, benchmark summaries,
and figure-generation scripts. Downloaded public inputs and deterministic synthetic
benchmark matrices are regenerated locally rather than stored in Git.

## Validation summary

| Experiment | Primary result |
|---|---|
| [01 — Exact oracle](experiments/01_exact_oracle/) | 128,881 comparisons across seven topology and branch configurations; zero discrepancies from an independent exhaustive oracle |
| [02 — Deliberate faults](experiments/02_deliberate_faults/) | All 10 deliberately incorrect implementations detected across 280,216 fault–challenge comparisons |
| [03 — Published datasets](experiments/03_published_datasets/) | 877/877 unambiguous BRANCHSNV substitutions matched SNPPar in edge, position and direction; 23/23 published AK3 branch SNVs reproduced |
| [04 — Scalability](experiments/04_scalability/) | All 39 benchmark runs completed; tested to 2,000 taxa × 10,000 sites and 250 taxa × 100,000 sites |

The committed results evaluate BRANCHSNV **v0.1.0a1**. The experiments should be
repeated against the frozen publication release if its production source changes.

## Repository layout

```text
experiments/    Validation and benchmark scripts
results/        Canonical outputs used for the manuscript
LICENSE         Licence for the validation code
THIRD_PARTY.md  Sources and attribution for reused public material
```

The full synthetic scalability inputs are not committed because they are
deterministically generated and total approximately 84 MB. Their exact manifest and
SHA-256 hashes are retained in
[`results/04_scalability/input_manifest.json`](results/04_scalability/input_manifest.json).

## Reproduce the experiments

### Requirements

- Python 3.10 or later;
- a local checkout of BRANCHSNV v0.1.0a1 or a source-identical release;
- internet access for downloading the public SNPPar inputs used by Experiment 03;
- GNU `time` for peak-memory measurement in Experiment 04;
- Matplotlib only for regenerating the scalability figures.

Place the two repositories beside one another:

```text
work/
├── branchsnv/
└── branchsnv-validation/
```

Then run:

```bash
cd branchsnv-validation
bash run_completed_experiments.sh ../branchsnv
```

Local reruns are written to `reproduced_results/`, leaving the committed publication
snapshot unchanged. Set `BRANCHSNV_BENCHMARK_REPETITIONS` to change the number of
scalability repetitions. An exact AK3 input directory can be supplied as the third
argument when the archived files are available:

```bash
bash run_completed_experiments.sh ../branchsnv \
  public_inputs/03_published_datasets \
  /path/to/exact/ak3/files
```

Each experiment also has its own design, command and interpretation in the linked
README.

## Input and output provenance

| Material | Handling |
|---|---|
| BRANCHSNV production source | Read-only local checkout; source-file SHA-256 hashes are recorded in the result metadata |
| SNPPar comparison inputs | Downloaded from `d-j-e/SNPPar_test`; every file must match a prespecified SHA-256 checksum |
| Scalability inputs | Generated deterministically; the committed manifest records every expected file hash |
| AK3 alignment and tree | Not redistributed in this snapshot; expected SHA-256 hashes are recorded and the exact files remain to be placed in a permanent archive |
| Canonical outputs | Committed under `results/` with aggregate SHA-256 checksums |

Verify the committed result snapshot from the repository root:

```bash
sha256sum -c results/checksums.sha256
```

## Important interpretation

The SNPPar analysis is a concordance and method-sensitivity comparison, not a claim
that the programs are interchangeable. All 877 BRANCHSNV-unambiguous substitutions
matched SNPPar. A further 66 SNPPar assignments were among BRANCHSNV's globally
optimal state pairs but were classified as placement-ambiguous because equally
parsimonious reconstructions did not all place the change on that edge.

For AK3, the primary 360-descendant branch reproduced all 23 published SNV positions
and directions. The separate 385-descendant SaPI-like working-data comparison retains
an unresolved input-version difference and is excluded from the successful
reproduction claim.

## Archiving status

Before manuscript submission, the final repository release should be archived with a
permanent DOI, and the exact checksum-matched AK3 alignment and tree should be placed
in an appropriate public archive. Those identifiers should then be added to the
manuscript Data Summary and `CITATION.cff`.

## Funding and affiliation

<p align="center">
  <a href="https://www.genomics-aotearoa.org.nz/">
    <img
      src="assets/genomics-aotearoa-logo.png"
      alt="Genomics Aotearoa"
      height="80">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.phfscience.nz/">
    <img
      src="assets/phf-science-logo.png"
      alt="PHF Science"
      height="80">
  </a>
</p>

<p align="center">
  Development of BRANCHSNV was supported by
  <strong>Genomics Aotearoa</strong> and undertaken at
  <strong>Public Health and Forensic Science (PHF Science),
  Aotearoa New Zealand</strong>.
</p>

BRANCHSNV was developed and is maintained by [Rhys White](https://github.com/RhysWhite).

## Citation and licence

Citation metadata are provided in [`CITATION.cff`](CITATION.cff). The validation code
is released under the [MIT License](LICENSE). Reused public materials remain subject
to their original licences and citations; see [`THIRD_PARTY.md`](THIRD_PARTY.md).
