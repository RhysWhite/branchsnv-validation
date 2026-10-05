# Figure 1 code walkthrough

`make_figure_1.py` generates the complete Figure 1 artwork programmatically.

## Scientific purpose

Figure 1 illustrates the distinction between clade exclusivity and focal-edge substitution in BRANCHSNV.

### Panel a — one branch, one site

A rooted phylogeny contains one explicitly defined focal edge. All three focal descendants carry G at the illustrated nucleotide site, while G also occurs in a sampled genome outside the focal clade.

The state is therefore fixed within the focal clade but is not exclusive to it.

### Panel b — two questions, different answers

The observed tip states and the reconstructed focal-edge substitution are evaluated independently.

Because G occurs outside the focal clade, the site is not fixed-exclusive. However, every globally optimal equal-cost Sankoff reconstruction supports A→G on the focal edge, so the focal-edge substitution is unambiguous.

### Panel c — reconstruction uncertainty

BRANCHSNV retains every parent–child nucleotide-state pair attainable on the focal edge across globally optimal reconstructions.

The illustrated outcomes are:

- `A→G only` — unambiguous change;
- `A→G or C→G` — state ambiguity;
- `A→G or G→G` — placement ambiguity;
- `G→G only` — no change.

No arbitrary choice is made among tied optimal reconstructions.

## Design safeguards

The lower strip summarizes five explicit safeguards:

- the root defines evolutionary direction;
- the exact sampled descendant set defines the focal edge;
- exact taxon labels define tree–alignment correspondence;
- the complete optimal focal-edge state-pair set retains reconstruction uncertainty;
- deterministic provenance supports auditability.

## Rendering

The figure is generated at 180 × 135 mm.

Panel labels are lower-case bold `a`, `b` and `c`. Colour is used semantically rather than decoratively. PDF and SVG outputs remain vector-based; PNG and TIFF files are generated for preview and production.

The validated rendering environment is:

- Python 3.10.14
- Matplotlib 3.10.8
- Pillow 12.2.0
- DejaVu Sans

No manual editing of the generated artwork is required.
