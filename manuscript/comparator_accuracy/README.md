# Manuscript comparative accuracy figures — 150-scenario Experiment 07

This directory holds **two complete figures** generated from real, checksum-verified
Experiment 07 score data. Both use a consistent marker key, monochrome-safe styling,
point-level summaries instead of bars, and F1 on a percentage scale.

- `figures/BRANCHSNV_Exp07_MAIN_FIGURE.{pdf,svg,png}`
- `figures/BRANCHSNV_Exp07_SUPPLEMENTARY_FIGURE.{pdf,svg,png}`

Regenerate figures in a clean Python environment (locked versions):

```bash
python -m pip install -r manuscript/comparator_accuracy/requirements.lock.txt
python manuscript/comparator_accuracy/safe_rebuild_figures.py
```

The script refuses to proceed if the source archive hash or its embedded SHA256SUMS
changes. Figure code and data have intentionally separate manifests; do not change
files without updating and reviewing the publication evidence version.

The four-tip schematic in panel a is *illustrative*, not an empirical observation.
Paired intervals are frozen results from 25,000 matched-stratum replicates.
Small stratum markers are non-independent within-simulation summaries.

Consult `FIGURE_LEGENDS.md` for endpoint limitations and full legends.
