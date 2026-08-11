<p align="center">
  <img src="assets/BRANCHSNV_logo.png" alt="BRANCHSNV" width="1000">
</p>

# BRANCHSNV publication validation

Reproducible validation, empirical analyses and benchmarks supporting
[BRANCHSNV](https://github.com/RhysWhite/branchsnv). This repository is kept
separate from the production software so that independent or deliberately incorrect
implementations cannot alter the production code being tested.

The committed publication snapshot evaluates **BRANCHSNV v0.1.0a1**. Production-source SHA-256 hashes are recorded in the canonical run metadata so the validated analytical source is identifiable independently of later documentation-only repository commits.

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

Reruns are written to `reproduced_results/` by default. Experiment 04 is a benchmark,
so its timings and peak-memory measurements are environment-specific; deterministic
analytical outputs should reproduce exactly.


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

The final manuscript-associated GitHub release should be archived in an immutable
repository such as Zenodo and its DOI added to `CITATION.cff` and the manuscript.

## Citation and licence

Citation metadata are provided in [`CITATION.cff`](CITATION.cff). Validation code is
released under the [MIT License](LICENSE). Public third-party material retains its
original attribution; see [`THIRD_PARTY.md`](THIRD_PARTY.md).
