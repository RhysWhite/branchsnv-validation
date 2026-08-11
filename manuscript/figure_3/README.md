# Figure 3 - clade exclusivity and focal-edge substitution were not equivalent in empirical phylogenies

This directory contains the final Figure 3 artwork and the exact Python/Matplotlib code used to render it.

## Final figure

![Figure 3 preview](Figure_3_preview_600dpi.png)

## Data provenance

Panel A is generated directly from:

- `results/06_empirical_cross_classification/dataset_summary.tsv`
- `results/06_empirical_cross_classification/informative_events.tsv`

Panel B is generated directly from:

- `inputs/empirical/clade_a_tree.nwk`
- `inputs/empirical/clade_a_alignment.nex`

The displayed tree is a pruned **phylogram** from the supplied Clade A tree. Horizontal branch lengths are retained from the Newick input. No schematic or invented topology is used.

## Figure files

| File | Purpose | SHA-256 |
|---|---|---|
| `Figure_3.pdf` | Vector production/submission figure. | `3fa1f50f45317303996e89d51747a38cb9b92b480d595ed5f2c1f4dac517ffca` |
| `Figure_3_editable.svg` | Editable vector source. | `3457193210f57cf218518e1342183576c12e1d00eb47fa99a86c3c24c96259ee` |
| `Figure_3_preview_600dpi.png` | README/inspection preview. | `0fc1ff4911c9ce694145a8e73c543757df30d733391c0dce1f678e5215858ba8` |
| `Figure_3_1000dpi.tiff` | 1000-dpi LZW line-art TIFF. | `5e0bf2b581b7a6f3af2ca6fa808fd032d14a805a2e557e25eaaf94d75688a2b3` |
| `Figure_3_1000dpi_RGB.tiff` | Explicit RGB 1000-dpi LZW TIFF. | `d88bad3428bd0d49bba9b4ae5beae56135edec60ad2df65b4cab224c431d9bb4` |

## Cell Press preparation choices

- final artwork size: **6.5 × 4.4 in**;
- figure title and legend are not embedded in the artwork;
- capital panel labels A and B;
- text is approximately 6–8 pt at final print size;
- line weights are approximately 0.5–1.25 pt;
- vector PDF and editable SVG supplied;
- 1000-dpi LZW TIFF supplied for line-art production;
- RGB raster export supplied;
- Figure 1 color semantics retained: blue, orange, purple, and neutral grayscale.

### Font note

Cell Press production guidance requests Arial. Arial is not installed in the automated rendering environment, so Matplotlib resolves the requested Arial family to **Arimo**, an Arial-compatible metric substitute. The SVG keeps text editable so Arial can be substituted during final production if required.
