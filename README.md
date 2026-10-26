<p align="center">
  <img src="assets/BRANCHSNV_logo.png" alt="BRANCHSNV" width="1000">
</p>

# BRANCHSNV publication validation

**Published v0.2.0 archives:** [validation and reproducibility evidence (10.5281/zenodo.23518684)](https://doi.org/10.5281/zenodo.23518684) · [associated source release (10.5281/zenodo.23518619)](https://doi.org/10.5281/zenodo.23518619).

Reproducible validation, empirical analyses and benchmarks supporting
[BRANCHSNV](https://github.com/RhysWhite/branchsnv). This repository is kept
separate from the production software so that independent or deliberately incorrect
implementations cannot alter the production code being tested.

The committed publication snapshot was generated with **BRANCHSNV v0.1.0a1**. A separate stable-release validation record confirms **BRANCHSNV v0.1.0**. Production-source SHA-256 hashes are recorded in the canonical run metadata so the validated analytical source is identifiable independently of later documentation-only repository commits.

**Production software:** [GitHub](https://github.com/RhysWhite/branchsnv) · [PyPI](https://pypi.org/project/branchsnv/) · [Documentation](https://branchsnv.readthedocs.io/en/latest/) · [bio.tools](https://bio.tools/branchsnv) · [Zenodo](https://doi.org/10.5281/zenodo.21919038)

**Validation archive:** [Zenodo](https://doi.org/10.5281/zenodo.21919067)

## Versioned validation records (v0.2.0)

The Zenodo links above identify the **historical v0.1.0** releases, not the
v0.2.0 evidence. The two v0.2.0 executions are preserved separately:

- **Original validation (6 October 2026):** [`release_validation/v0.2.0/`](release_validation/v0.2.0/), production commit `b63b6db`, validation-framework commit `f48bd14`.
- **Independent reproduction (21 October 2026):** [`release_validation/v0.2.0-reproduction-20261021/`](release_validation/v0.2.0-reproduction-20261021/), production commit `65eb791`, validation-framework commit `3c64a1d`.

The 47 checksummed result files in each execution were verified. Deterministic
results and the tested scientific invariants agreed; Experiment 04 performance
measurements are machine-dependent. For source identities, validation commands
and manuscript file references, start at [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md)
and the [manuscript claim crosswalk](release_validation/v0.2.0-reproduction-20261021/MANUSCRIPT_CLAIM_CROSSWALK.tsv).
The v0.2.0 software and validation version-specific DOIs are linked above.

**Experiment 7:** The separately executed 30-history RC3 candidate has completed an automated evidence audit, but scientific approval remains **UNSIGNED/HOLD**. It is not part of the approved v0.2.0 validation conclusions.

## Validation summary

| Experiment | Primary result |
|---|---|
| [01 — Exact oracle](experiments/01_exact_oracle/) | 128,881/128,881 exact comparisons across seven topology–edge settings |
| [02 — Deliberate faults](experiments/02_deliberate_faults/) | 10/10 fault classes detected across 280,216 fault–challenge comparisons |
| [03 — SNPPar comparison](experiments/03_published_datasets/) | 877/877 BRANCHSNV-unambiguous substitutions matched SNPPar; the remaining 66 SNPPar events were placement-ambiguous in BRANCHSNV |
| [04 — Scalability](experiments/04_scalability/) | 39/39 measured end-to-end runs completed across the tested taxon, site and mode series |
| [05 — Published focal branches](experiments/05_published_focal_branches/) | 46/46 published SNVs reproduced across MRSA AK3, MRSA ST97 and *E. coli* ST131/OXA-48 |
| [06 — Complete-phylogeny empirical analysis](experiments/06_empirical_cross_classification/) | 31,644 informative comparisons across five phylogenies; 827 (2.61%) fell outside the fixed-exclusive/unambiguous-substitution intersection |

## Repository layout

```text
experiments/       Validation, empirical-analysis and benchmark code
inputs/empirical/  Exact checksum-gated inputs for Experiments 05 and 06
results/           Canonical publication result snapshot
manuscript/        Reproducible manuscript Figure 1–4 packages
assets/            Repository artwork
```

Synthetic benchmark inputs are generated deterministically and are not committed;
their manifest and expected SHA-256 hashes are retained under `results/04_scalability/`.
The public SNPPar inputs are downloaded from their upstream repository and accepted
only when their prespecified checksums match.

## Reproduce

Requirements:

- Python 3.10 or later;
- a local checkout of the source-identical BRANCHSNV release being tested;
- internet access only for retrieving the public SNPPar inputs in Experiment 03;
- GNU `time` for Experiment 04;
- NumPy 2.3.5, pandas 2.2.3 and Numba 0.65.1 for Experiment 06;
- Matplotlib, Pillow, pandas and Biopython for regenerating the manuscript figure packages.

For the manuscript environment:

```bash
python -m pip install -r requirements-analysis.txt
python -m pip install -r requirements-figures.txt   # optional manuscript figures
```

Place the production and validation repositories beside one another and run:

```bash
cd branchsnv-validation
bash run_completed_experiments.sh ../branchsnv
```

Reruns are written to `reproduced_results/` by default. The runner refuses to reuse a
non-empty output directory or write into the committed canonical `results/` tree, and it
finishes by verifying the newly generated results against the supplied BRANCHSNV source.
A successful full run therefore ends with `REPRODUCED RESULTS: PASS`. Experiment 04 is a
benchmark, so its timings and peak-memory measurements are environment-specific; its run
count, completion status, source identity and deterministic input manifest are verified.

To verify an already completed rerun directly:

```bash
python verify_reproduced_results.py \
  --results-dir reproduced_results \
  --branchsnv-root ../branchsnv
```


## Manuscript figure packages

The `manuscript/` directory contains repository-portable production packages for Figures 1–4. Each package includes the plotting script, vector and high-resolution raster artwork, a README describing data provenance, locked rendering requirements, and a line-by-line code walkthrough. Figure 2 is generated directly from the committed Experiment 01–05 summary files; Figure 3 reads the committed empirical cross-classification results and Clade A tree/alignment; Figure 4 reads the committed run-level scalability measurements.

The snapshot verifier also checks that every source line in each figure script is represented by the matching source line in its code walkthrough, preventing a rerendering or later edit from silently leaving the explanatory documentation out of sync.

## Empirical input provenance

Experiments 05 and 06 use the exact working alignments and rooted trees under
`inputs/empirical/`. Their hashes are recorded in
[`inputs/empirical/checksums.sha256`](inputs/empirical/checksums.sha256). The OXA-48
alignment labels its reference taxon as `REF`, while the tree labels the same isolate
`18AR0845`; the experiments apply the single documented `REF` → `18AR0845`
normalization in analysis without modifying the committed source file.

Experiment 05 commits exact focal-descendant lists. Experiment 06 excludes the two
branches directly incident to each degree-two root from its primary proportions and
retains them separately as a sensitivity analysis.

## Canonical results

From the repository root, verify both file integrity and the publication headline values:

```bash
python verify_publication_snapshot.py
```

The underlying result manifest can also be checked directly with
`sha256sum -c results/checksums.sha256`. Headline analytical claims are stored as
machine-readable JSON/TSV outputs rather than only in manuscript prose. Experiment 06 also runs a record-level comparison with
unmodified production BRANCHSNV on eight prespecified Clade A/B branches: 1,617/1,617
informative records must match in parsimony score, complete optimal pair set,
reconstruction class and fixed-exclusive status.

## Interpretation

The SNPPar experiment is a concordance and method-sensitivity comparison, not a claim
that the programs are interchangeable. The complete-phylogeny analysis likewise tests
the empirical relationship between two definitions under the supplied data, rooting and
equal-cost reconstruction criterion; it does not make a universal claim about all
phylogenies.

## Archiving

The manuscript-associated BRANCHSNV publication-validation release v0.1.0 is
permanently archived at https://doi.org/10.5281/zenodo.21919067.

The corresponding production BRANCHSNV software release is archived separately at
https://doi.org/10.5281/zenodo.21919038.

## Citation and licence

Citation metadata are provided in [`CITATION.cff`](CITATION.cff). Validation code is
released under the [MIT License](LICENSE). Public third-party material retains its
original attribution; see [`THIRD_PARTY.md`](THIRD_PARTY.md).

## Completed 150-scenario comparator benchmark (Experiment 07 extension)

The separately identified 26 October 2026 Experiment 07 publication extension
compares BRANCHSNV against eight external workflows on 150 frozen simulated
scenarios. Seven methods contribute exact branch-event scores and four external
methods contribute a **different** recurrent-site endpoint. This is a scored
**exploratory extension**, not a revision to the historical 0.1.0a1/0.1.0
validation release. Branch lengths in the simulator were derived from realised
events; results are conditional latent-history recovery, not an independent
branch-length validation.

See [accuracy benchmark methods and provenance](experiments/07_comparative_landscape/accuracy_benchmark_v1/),
[verified result tables](results/07_comparative_landscape/accuracy_benchmark_v1/),
[code-generated main and supplementary figures](manuscript/comparator_accuracy/), and
[the machine-readable manuscript claim register](publication_claims.json).

Verify with `python verify_experiment07_publication.py`. The original
`verify_publication_snapshot.py` continues to govern Experiments 01–06.
