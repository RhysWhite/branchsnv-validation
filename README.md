<p align="center">
  <img src="assets/BRANCHSNV_logo.png" alt="BRANCHSNV" width="1000">
</p>

# BRANCHSNV publication validation

This is the **independent evidence repository**, not the BRANCHSNV command-line
program. For installation and everyday usage, use the
[production repository](https://github.com/RhysWhite/branchsnv) and
[documentation](https://branchsnv.readthedocs.io/en/latest/).

## Find the evidence

| Question | Authoritative starting point |
|---|---|
| Which version, experiment and file supports a claim? | [Evidence index](EVIDENCE_INDEX.md) |
| How are the six original experiments reproduced? | [Reproducibility protocol](REPRODUCIBILITY.md) |
| Where are the baseline results? | [`results/`](results/README.md), historical BRANCHSNV v0.1.0a1 |
| Where are independent v0.2.0 reruns? | [`release_validation/v0.2.0/`](release_validation/v0.2.0/) and [`release_validation/v0.2.0-reproduction-20261021/`](release_validation/v0.2.0-reproduction-20261021/) |
| Where is the 150-scenario Experiment 07 study? | [Experiment 07 guide](docs/experiment07.md) and [immutable publication commit `2afa89f`](https://github.com/RhysWhite/branchsnv-validation/tree/2afa89f47815eac3b85b722c2fddd14d9c17f22e) |
| How were manuscript Figures 1–4 generated? | [`manuscript/`](manuscript/README.md), including figure-specific code walkthroughs |
| What upstream data or papers were used? | [Third-party attribution](THIRD_PARTY.md) |

**Version boundaries matter.** The default `main` branch preserves the
historical Experiments 01–06 framework. Experiment 07's 150-scenario
publication evidence lives at a **separate, immutable Git commit**; it must
not be inferred from `main/results/`. Earlier 30-history RC3 development
material was held for scientific review and is **not** the frozen 150-scenario
publication study.

## What was tested

| Experiment | Prespecified result |
|---|---|
| [01 — Independent exhaustive oracle](experiments/01_exact_oracle/) | 128,881/128,881 exact comparisons |
| [02 — Deliberate faults](experiments/02_deliberate_faults/) | 10/10 fault classes detected in 280,216 challenge comparisons |
| [03 — SNPPar concordance](experiments/03_published_datasets/) | 877/877 unambiguous BRANCHSNV events matched; 66 additional SNPPar events were placement-ambiguous |
| [04 — Scalability](experiments/04_scalability/) | 39/39 end-to-end runs completed; performance values are machine-dependent |
| [05 — Published focal branches](experiments/05_published_focal_branches/) | 46/46 published SNVs reproduced for three branches |
| [06 — Complete-phylogeny empirical analysis](experiments/06_empirical_cross_classification/) | 31,644 informative comparisons; 827 (2.61%) outside the intersection of strict exclusivity and unambiguous substitutions |
| [07 — Comparative landscape](docs/experiment07.md) | Separate 150-scenario study with seven methods and a strict truth-event endpoint; not part of the 01–06 pass criteria |

These outcomes are **conditional on their defined inputs, trees, scoring rules
and tested source revisions**. They are not a universal measure of bacterial
transmission inference accuracy.

## Reproduce Experiments 01–06

For the committed historical snapshot (without running the experiments):

```bash
python verify_publication_snapshot.py
```

For the pinned v0.2.0 records and an actual rerun, use
[`REPRODUCIBILITY.md`](REPRODUCIBILITY.md). The main entry point
`run_completed_experiments.sh` covers **Experiments 01–06 only**; it does
not regenerate the separate Experiment 07 study.

## Archives and source identity

| Evidence | DOI |
|---|---|
| Production software v0.2.0 | [10.5281/zenodo.23518619](https://doi.org/10.5281/zenodo.23518619) |
| Independent validation v0.2.0 | [10.5281/zenodo.23518684](https://doi.org/10.5281/zenodo.23518684) |
| Experiment 07 benchmark v0.3.0 | [10.5281/zenodo.23684441](https://doi.org/10.5281/zenodo.23684441) |
| Historical production v0.1.0 | [10.5281/zenodo.21919038](https://doi.org/10.5281/zenodo.21919038) |
| Historical validation v0.1.0 | [10.5281/zenodo.21919067](https://doi.org/10.5281/zenodo.21919067) |

The separate S8 post-hoc supplementary archive has passed candidate-level
byte-identical reproduction but **has not yet been published**. A candidate
archive is not a persistent public citation. See [Experiment 07](docs/experiment07.md)
for its scope and release status.

Validation code is under [MIT](LICENSE), with external inputs attributed in
[`THIRD_PARTY.md`](THIRD_PARTY.md). Licensing of the not-yet-released S8
supplement requires separate confirmation. Citation metadata are in
[`CITATION.cff`](CITATION.cff).
