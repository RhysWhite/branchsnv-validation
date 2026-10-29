# BRANCHSNV manuscript figure index

This index follows the manuscript's final figure numbering. The original
source packages retain their historical directory names and generator output
names; consult this index rather than inferring manuscript numbering from
those historical names.

## Main figures

| Manuscript figure | Subject | Final artwork | Original reproducibility package |
|---|---|---|---|
| Figure 1 | Conceptual framework | [Figure 1](submission_figures/Figure_1.pdf) | [Original Figure 1](figure_1/) |
| Figure 2 | Empirical non-equivalence | [Figure 2](submission_figures/Figure_2.pdf) | [Historical Figure 3](figure_3/) |
| Figure 3 | Layered validation | [Figure 3](submission_figures/Figure_3.pdf) | [Historical Figure 2](figure_2/) |
| Figure 4 | Comparative reconstruction accuracy | [Figure 4](submission_figures/Figure_4.pdf) | [Frozen Experiment 07 figure](comparator_accuracy/figures/) |

## Supplementary figures

| Manuscript figure | Subject | Final artwork | Original reproducibility package |
|---|---|---|---|
| Supplementary Figure S1 | Scalability | [S1](submission_figures/Supplementary_Figure_S1.pdf) | [Historical Figure 4](figure_4/) |
| Supplementary Figure S2 | Different inference targets | [S2](submission_figures/Supplementary_Figure_S2.pdf) | [Historical Figure S3](supplementary/experiment_07/) |
| Supplementary Figure S3 | Software identification | [S3](submission_figures/Supplementary_Figure_S3.pdf) | [Historical Figure S1](supplementary/experiment_07/) |
| Supplementary Figure S4 | Bibliographic reconciliation | [S4](submission_figures/Supplementary_Figure_S4.pdf) | [Historical Figure S2](supplementary/experiment_07/) |

The [submission figure package](submission_figures/) includes SVG, PNG,
PDF, and a SHA-256 source/output manifest. The original source
generators remain available in their historical locations. The
submission package corrects numbering; it is not a new scientific analysis.

The S2–S4 presentation files are derived renders with corrected visible
headings. Their original evidence package documents additional frozen
inputs and scientific limitations; its generator has not been established
as independently executable from `main` alone.

## Experiment 07 supplementary benchmark artwork

The [additional comparative supplementary artwork](comparator_accuracy/figures/)
is preserved separately from the numbered manuscript figures. It has
not been assigned a new supplementary figure number.

## Supplementary tables and archives

Supplementary Table S8a/S8b reproducibility evidence is archived in
[BRANCHSNV-validation v0.3.1](https://doi.org/10.5281/zenodo.23752088).
The original benchmark is preserved in
[v0.3.0](https://doi.org/10.5281/zenodo.23684441).

See the [Experiment 07 guide](../docs/experiment07.md) and
[evidence index](../EVIDENCE_INDEX.md) for source revisions,
scoring definitions, and reproduction limitations.

## Historical reproducibility packages

The original directory numbering predates the current manuscript:

- Original Figure 1 is current Figure 1.
- Original Figure 2 is current Figure 3.
- Original Figure 3 is current Figure 2.
- Original Figure 4 is current Supplementary Figure S1.

The following original instructions are retained for reproducibility.

### Original figure-generation instructions

These four directories preserve the original artwork and generation code, using the historical figure numbering.

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
