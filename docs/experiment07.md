# Experiment 07 — comparative landscape and Supplementary Table S8

This guide covers the **150-scenario frozen publication study** and its
subsequent post-hoc diagnostic. For Experiments 01–06, use the
[separate evidence index](../EVIDENCE_INDEX.md). Experiment 07 is **not**
executed by `run_completed_experiments.sh` on `main`.

## Start with the immutable evidence

| What | Where |
|---|---|
| Publication snapshot | [Validation commit `2afa89f`](https://github.com/RhysWhite/branchsnv-validation/tree/2afa89f47815eac3b85b722c2fddd14d9c17f22e) |
| 150 simulated scenarios | [Frozen scenario matrix](https://github.com/RhysWhite/branchsnv-validation/blob/2afa89f47815eac3b85b722c2fddd14d9c17f22e/experiments/07_comparative_landscape/accuracy_benchmark_v1/scenario_matrix_150.tsv) |
| Aggregate and scenario-level results | [Frozen results directory](https://github.com/RhysWhite/branchsnv-validation/tree/2afa89f47815eac3b85b722c2fddd14d9c17f22e/results/07_comparative_landscape/accuracy_benchmark_v1) |
| Original benchmark archives | [Zenodo v0.3.0](https://doi.org/10.5281/zenodo.23684441) |
| Benchmark plus S8 reproducibility evidence | [Zenodo v0.3.1](https://doi.org/10.5281/zenodo.23752088) |
| Interpretation and verification | [`verify_experiment07_publication.py` at frozen commit](https://github.com/RhysWhite/branchsnv-validation/blob/2afa89f47815eac3b85b722c2fddd14d9c17f22e/verify_experiment07_publication.py) |
| S8 post-hoc attribution and identifiability | [Published reproducibility supplement, validation v0.3.1](https://doi.org/10.5281/zenodo.23752088) |

**Why not just browse `main`?** The 150-scenario results are held on the
publication integration branch, not the historical main-line `results/`
snapshot. A reader following `main` alone will not find those results.

## What the comparison measures

The 150 scenarios represent a controlled simulated evolutionary history with
known truth events. A strict event match requires the specified genomic site,
edge and nucleotide transition; matching only the observed tip pattern does
not establish an exact historical event. The published archive contains BRANCHSNV and eight external workflows,
giving 1,350 method–scenario outputs. The strict branch-event benchmark
scores seven methods (1,050 method–scenario records). These are distinct
analytical scopes, not different release versions. These are **conditional comparisons** on simulated histories and the benchmark's event-derived branch
lengths, not a test of independently inferred branch lengths or clinical
transmission accuracy.

The source data, original primary three-method aggregate, and later exploratory
comparator extension are distinct stages. The frozen extension provenance
records **900 additional comparator executions**; the original three-method
aggregate was imported without alteration, established by matching SHA-256
`4119341ee6ebf5c1d574c8d23aaf2375b819f21e10b28e249226468372406c7e`.
The corresponding original scoring provenance has SHA-256
`5e0e99fe17b13bdf6e7b56c9c2e7f64070ed691bf8c832a94df87488cd43f787`.
These identify different pipeline stages, not contradictory versions of the
same file.

For BRANCHSNV's strict primary endpoint across 150 scenarios, the frozen
independent scorer records **9,600 truth events**, **5,661 true positives**,
**890 false positives**, and **3,939 false negatives**. Ambiguous calls are
excluded from strict true positives. They are retained for the post-hoc
interpretation below, not silently promoted into correct predictions.

## What Supplementary Table S8 adds

**S8a — error attribution:** matches the original strict-scoring false
negatives, false positives and ambiguous calls to cases in the frozen truth
ledger. It reports all 150 scenarios and the same 9,600 truth events as the
primary scorer. It does **not** change the primary scoring endpoint, rerun
BRANCHSNV or rescore comparators. For example, 2,011 false negatives had an
ambiguous record compatible with the truth transition on the exact edge; such
compatibility is **diagnostic**, not a strict true positive.

**S8b — identifiability under the specified parsimony model:** replays 4,200
truth event records at 2,400 sites for 60 convergence and reversal scenarios,
and evaluates unit-cost Sankoff minimum-change solutions from observed tips,
including a fixed-true-root sensitivity analysis. It does **not** demonstrate
that a historical mutation is biologically impossible to infer using every
conceivable source of data. Its subset event counts are:

| Event class | Truth events in S8b | Excess above tip minimum | Exact-edge transition optimal-possible |
|---|---:|---:|---:|
| Convergence prerequisite | 600 | 27 | 586 |
| Convergent | 1,200 | 54 | 1,166 |
| Reversal back | 600 | 600 | 0 |
| Reversal forward | 600 | 600 | 5 |
| Unique | 1,200 | 15 | 1,185 |

Those figures are **subset counts**, not the corresponding totals across the
full 150-scenario experiment. The `subset_census` script corrects an earlier
assumption that full-study event counts applied to this 60-scenario subset.

## How the reproducibility check was performed

The original post-hoc evidence was checksum-verified, then S8a and S8b were
run from isolated local copies of their frozen inputs. Both analyses regenerated
outputs byte-for-byte. A second run started from a newly extracted release
candidate and reconstructed all **1,800 canonical input/run files** from the
public [Zenodo v0.3.0 benchmark](https://doi.org/10.5281/zenodo.23684441),
fetched pinned public Git commits, and again produced byte-identical S8a/S8b
results. This establishes **byte-identical computational repeatability** for the S8 analyses; it does not independently reproduce every external comparator execution.

The extracted supplement included additional validation records not present
in the original Zenodo v0.3.0 files, including the frozen scorer, edge-bridge
audit and original scoring provenance. These are now included in the
supplementary archive published as part of
[Zenodo v0.3.1](https://doi.org/10.5281/zenodo.23752088).
The original v0.3.0 files alone remain insufficient for reproducing S8.

### Source revisions used in the successful S8 replay

- [Validation source `14cc805c068edbf4e0923b7531a96cc1c35556f2`](https://github.com/RhysWhite/branchsnv-validation/tree/14cc805c068edbf4e0923b7531a96cc1c35556f2)
- [Production source `4f6f3662ba2b8f844eccdf8a947e91ff4585ce01`](https://github.com/RhysWhite/branchsnv/tree/4f6f3662ba2b8f844eccdf8a947e91ff4585ce01)

The post-hoc script entry points are
`experiment07_branchsnv_error_attribution_v1.py` and
`experiment07_reversal_identifiability_v1_subset_census.py`.
Earlier S8b root-compatibility variants are historical development artifacts,
not the authoritative replayed script. Full commands, input mapping and
hash verification belong in the separate S8 supplement's `REPRODUCE.md`.

## What to cite

For the original Experiment 07 benchmark, cite the
[v0.3.0 Zenodo release](https://doi.org/10.5281/zenodo.23684441)
and the frozen Git commit. For Supplementary Table S8 and its reproducibility
evidence, cite [validation v0.3.1](https://doi.org/10.5281/zenodo.23752088),
which retains the original 19 files and includes the corrected supplement.
For Experiments 01–06, use the
[v0.2.0 validation record](https://doi.org/10.5281/zenodo.23518684).

Source code and the data release are not interchangeable citation targets.
