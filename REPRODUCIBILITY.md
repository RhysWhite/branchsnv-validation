# Reproducibility and manuscript evidence

The **v0.2.0 software version** has two separately preserved validation executions.
They must not be treated as the same Git snapshot or the same scalability
measurement.

| Execution | Source and framework | Evidence |
|---|---|---|
| Original public validation, 6 October 2026 | Production `b63b6db`; validation `f48bd14` | [`release_validation/v0.2.0/`](release_validation/v0.2.0/) |
| Independent reproduction, 21 October 2026 | Production `65eb791d9f1a202c3ca8816332a58c036794bd1f`; validation `3c64a1d367253ddcaef06c2f07012f347606358e` | [`release_validation/v0.2.0-reproduction-20261021/`](release_validation/v0.2.0-reproduction-20261021/) |

The two sets have 47 verifiable result files each. Across the compared records,
36 shared files are byte-identical and 14 differ. Seven differing files are run
metadata, four are performance tables/summary in Experiment 04, and three are
record and checksum/documentation metadata. No discrepancies were detected in
the prespecified scientific invariant comparison. This is not a universal
software-correctness or clinical-performance claim.

For the independently reproduced Experiment 05, the 46 prespecified nucleotide
substitutions and their source metadata are at
[`release_validation/v0.2.0-reproduction-20261021/results/05_published_focal_branches/`](release_validation/v0.2.0-reproduction-20261021/results/05_published_focal_branches/),
including `summary.json`, `focal_branch_comparison.tsv` and `run_metadata.json`.
For precise methods-to-result mappings, use the
[seven-claim crosswalk](release_validation/v0.2.0-reproduction-20261021/MANUSCRIPT_CLAIM_CROSSWALK.tsv).

**Citation boundary:** cite a version-specific, independently verified Zenodo
record only after that record actually exists. A Git commit is not a Zenodo DOI.
The original software `v0.2.0` tag points to `b63b6db`; the October reproduction
used documentation descendant `65eb791d9f1a202c3ca8816332a58c036794bd1f`. Experiment 7 RC3 remains
**UNSIGNED/HOLD** and is not part of the validated Experiments 01–06.
