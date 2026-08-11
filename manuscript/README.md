# Manuscript figure reproducibility packages

This directory contains the production artwork and repository-portable source used to generate BRANCHSNV manuscript Figures 1–4.

| Figure | Purpose | Primary committed source |
|---|---|---|
| [Figure 1](figure_1/) | Conceptual distinction, reconstruction classes and design safeguards | schematic definitions encoded in `make_figure_1.py` |
| [Figure 2](figure_2/) | Convergent validation evidence | Experiment 01–05 `summary.json` files |
| [Figure 3](figure_3/) | Empirical non-equivalence and Clade A recurrent-state example | Experiment 06 results plus committed Clade A tree/alignment |
| [Figure 4](figure_4/) | Runtime and peak-memory scaling | `results/04_scalability/raw_runs.tsv` |

Each figure directory contains:

- the exact Python script used for the locked render;
- vector PDF and editable SVG artwork;
- 600-dpi PNG preview;
- 1000-dpi LZW TIFF and explicit RGB TIFF;
- a README documenting provenance and rendering choices;
- a line-by-line code walkthrough;
- a small directory tree and locked figure requirements.

Run `python verify_publication_snapshot.py` from the repository root to verify the canonical result snapshot and confirm that the figure code walkthroughs remain line-for-line synchronized with their plotting scripts.
