# Figure 1 — conceptual design of BRANCHSNV

This directory contains the final Figure 1 artwork, the exact Python/Matplotlib script used to generate it, and a plain-English line-by-line walkthrough of the code.

The figure is intentionally parsimonious: one branch, one site, two distinct analytical questions, complete retention of equally optimal focal-edge solutions, and the minimum set of safeguards needed to make the branch-level result auditable.

## Final figure

![Figure 1 preview](Figure_1_preview_600dpi.png)

## Figure legend

**Figure 1. Conceptual design of BRANCHSNV.** **(A)** A single nucleotide site is evaluated on an explicitly rooted phylogeny with a user-defined focal edge identified by its complete descendant set. In the illustrative example, all focal descendants carry G, while G also occurs in a sampled taxon outside the focal clade. **(B)** BRANCHSNV evaluates strict clade exclusivity and focal-edge substitution independently. Because G occurs outside the focal clade, the site is not fixed-exclusive. Under unordered equal-cost Sankoff parsimony, all globally minimum-change reconstructions support A→G on the focal edge, so the focal-edge substitution is classified as unambiguous. **(C)** BRANCHSNV retains all optimal parent-child nucleotide-state pairs on the focal edge. A single changing pair is reported as an unambiguous change; multiple changing pairs as state ambiguity; a mixture of changing and non-changing pairs as placement ambiguity; and exclusively non-changing pairs as no change. BRANCHSNV therefore retains reconstruction uncertainty rather than resolving equal-cost ties arbitrarily. The design safeguards shown below the panels make rooting, branch identity, taxon correspondence, optimal-solution retention, and analysis provenance explicit.

## Directory contents

| File | Purpose | SHA-256 |
|---|---|---|
| `Figure_1.pdf` | Vector PDF suitable for manuscript submission and production. | `3120521ba4053aabd08b883dde673c6d95dea3b5d11bffb6136ff4aee74c64ef` |
| `Figure_1_editable.svg` | Editable vector source. | `afcc11df780919d18370bd320fdb01bb9f637f224ec8a6a8d6d19020ebc28a66` |
| `Figure_1_preview_600dpi.png` | GitHub/README preview. | `81603ab43a5c67bd0f09e795f7af9afb0438b23dc3e6b2d28774679fe490d006` |
| `Figure_1_1000dpi.tiff` | 1000-dpi LZW-compressed TIFF generated directly by the plotting script. | `ab2136c751c565d9b6ef336b9e6dfbb361740e475e91f2ba80f0575234325d4d` |
| `Figure_1_1000dpi_RGB.tiff` | RGB-flattened 1000-dpi LZW TIFF for production workflows requiring RGB artwork. | `be66a65a27546dcc7f29b9bce83d32204382176ce57d0113936c74c349ab8918` |
| `make_figure_1.py` | Exact script used to generate the final figure files in this directory. | — |
| `CODE_WALKTHROUGH.md` | Plain-English explanation of the script, line by line. | — |
| `requirements.txt` | Python package versions used for the locked render and production conversion. | — |

## Reproducing the figure

The revised locked render and RGB production conversion used:

```text
Python 3.13.15
Matplotlib 3.10.8
Pillow 12.3.0
```

From this directory, run:

```bash
python make_figure_1.py
```

The script writes the PDF, SVG, PNG, and RGBA TIFF outputs into the same directory. The separate RGB production TIFF is generated from the RGBA TIFF by flattening transparency onto a white background with Pillow.

## Figure specifications

The final artwork is:

- 6.50 × 5.10 inches (16.5 × 13.0 cm);
- a single multi-panel figure with capital panel labels;
- predominantly vector line art;
- approximately 6–8 pt body text at final size;
- 0.5–1.5 pt line weights;
- RGB colour without a red/green pairing;
- supplied as vector PDF and editable SVG;
- supplied as a 1000-dpi LZW-compressed TIFF;
- supplied as a separate 600-dpi PNG for GitHub preview;
- free of numbered literature references inside the artwork.

The figure title and legend are kept outside the artwork so that the image file contains only the figure itself.

### Font note

The exact script uses **Arimo** because Microsoft Arial was not available in the environment used for the locked render. Arimo is metrically compatible with Arial, and the PDF/SVG retain editable text. If a production workflow requires Arial, replace Arimo with Arial in the editable vector artwork or script, then verify that no labels shift or overlap before exporting the final production files.

## Scientific logic of the illustrative example

Panel A uses a deliberately simple but internally consistent topology and nucleotide pattern.

The three focal descendants are:

```text
G G G
```

The six sampled taxa outside the focal clade are:

```text
A A A A A G
```

G is therefore **not fixed-exclusive**, because G is also present outside the focal clade.

For the illustrated rooted topology, unordered equal-cost Sankoff parsimony has a complete optimal focal-edge parent-child pair set of:

```text
A→G only
```

The focal-edge substitution is therefore unambiguous even though the derived G state is not clade-exclusive. This is the conceptual distinction BRANCHSNV is designed to preserve.

## Editing policy

The files in this directory represent the locked scientific content of Figure 1.

If the figure is edited:

1. regenerate the exported files from `make_figure_1.py` where possible;
2. confirm that the topology and nucleotide-state example are unchanged unless the scientific example is intentionally revised;
3. independently re-check the focal-edge parsimony result if the topology or site states are changed;
4. inspect the figure at final print size for text collisions, clipped labels, and alignment;
5. update the file checksums in this README.
