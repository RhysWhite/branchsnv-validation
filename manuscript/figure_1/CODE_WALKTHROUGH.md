# Figure 1 — scientific and code walkthrough

This document explains the scientific choices, drawing logic and reproducibility controls in [`make_figure_1.py`](make_figure_1.py). **The script draws a conceptual figure; it does not run BRANCHSNV, perform ancestral-state reconstruction or generate benchmark results.** Its labels encode a worked example whose inference must be established independently of the illustration.

## Scientific question

BRANCHSNV distinguishes two properties of a nucleotide site relative to a specified branch:

1. **Clade exclusivity** is a statement about observed tip states: the focal descendants share a state that is absent from sampled non-descendants.
2. **Focal-edge substitution** is a statement about ancestral states: every globally minimum-cost reconstruction assigns a change to the selected parent–child edge, or only some do.

The second is an inference conditional on the topology, rooting, observed states and cost model; it cannot be read directly from a tip-state pattern. Minimum-change ancestral reconstruction is rooted in the methods of Fitch (1971) and Sankoff (1975). These citations support the parsimony framework, **not** an independent validation of the figure's particular example.

**Primary methods:** Fitch WM. *Toward defining the course of evolution: minimum change for a specific tree topology*. *Systematic Zoology* **20**, 406–416 (1971), [doi:10.1093/sysbio/20.4.406](https://doi.org/10.1093/sysbio/20.4.406); Sankoff D. *Minimal mutation trees of sequences*. *SIAM Journal on Applied Mathematics* **28**, 35–42 (1975), [doi:10.1137/0128004](https://doi.org/10.1137/0128004).

### Panel a — the observed pattern and the focal edge

The script draws a rooted topology with nine tips arranged in three three-tip groups. The following is an **explanatory topology sketch**, not a Newick export or a scaled tree:

```text
root
├── upper split
│   ├── [focal edge] ── G  G  G
│   └────────────────── A  A  A
└────────────────────── A  A  G
```

The focal descendants are all `G`, but a non-descendant also carries `G`. Thus `G` is fixed within the focal clade but **not fixed-exclusive**. The red focal edge and blue descendant bracket serve different purposes: one identifies the transition under study, the other identifies the taxa defining that branch.

### Panel b — inference is not exclusivity

On the depicted topology, unordered equal-cost parsimony gives a minimum of **two** changes at this site. In the globally optimal solution the parent of the focal edge is `A` and its child is `G`, so the focal-edge pair set is `{A→G}`. This conclusion is conditional on the stated rooted topology and reconstruction model. The code **draws the label** for this result; it does not calculate it, and therefore cannot serve as its own computational proof.

```text
Observed tip question                 Reconstructed edge question
Does G occur only below the edge?    Is A→G required on the focal edge?
                 │                                    │
             NO: G outside                      YES: {A→G}
```

The illustration therefore separates a descriptive property of sampled tips from an inferred historical event.

### Panel c — interpreting complete optimal-pair sets

The four rows show **possible output categories**, not four reconstructions of panel a. A complete set of attainable parent–child pairs distinguishes:

| Example pair set | Interpretation | Reason |
|---|---|---|
| `{A→G}` | Unambiguous change | All optimal assignments place the same change on the edge. |
| `{A→G, C→G}` | State ambiguity | A change is required, but the ancestral nucleotide differs. |
| `{A→G, G→G}` | Placement ambiguity | Some optimal assignments change on this edge; others do not. |
| `{G→G}` | No change | The edge is unchanged in every optimal assignment. |

An arbitrary single optimal reconstruction would lose these distinctions. The lower safeguard strip records the prerequisites for interpreting the result: an explicit root, an exact focal-descendant set, tree–alignment taxon identity, complete optimal state-pair retention and traceable provenance.

## How the source constructs the figure

```text
Fixed drawing configuration (lines 1–55)
           │
           ▼
Reusable shapes and text helpers (56–110)
           │
           ├─► Panel a: tree and observed states (111–185)
           ├─► Panel b: observed vs inferred (186–234)
           └─► Panel c: pair sets and safeguards (235–284)
           │
           ▼
Compose one canvas, export files and print hashes (285–362)
```

All placement coordinates use Matplotlib's `ax.transAxes`: `0` and `1` refer to the lower/upper or left/right limits of the figure canvas, independent of data units. This keeps the layout explicit but **does not** imply the branch lengths or nucleotide rows represent measured evolutionary distances.

## Rendering decisions and limitations

| Choice | Why it is made | What it does not guarantee |
|---|---|---|
| 180 × 135 mm single canvas | Controls printed size and panel proportions. | Compliance with every journal's current artwork specification. |
| DejaVu Sans, declared in the script | Avoids silent font substitutions when using the pinned environment. | Identical typography in unpinned Matplotlib/font installations. |
| Relative panel geometry and fixed palette | Keeps layouts and encodings reproducible. | Perceptual accessibility without separate visual inspection. |
| SVG text output and TrueType-compatible PDF fonts | Preserves vector artwork and supports editing. | Identical text rendering if font substitution occurs downstream. |
| Fixed PDF/SVG metadata and SVG identifier salt | Reduces unnecessary byte-level differences between renders. | Byte-for-byte identity across different software versions or operating systems. |
| Separate vector, preview and TIFF outputs | Serves manuscript, inspection and production workflows. | That all journal production constraints have been independently checked. |
| SHA-256 printed for each export | Makes generated outputs comparable to the archived release. | Scientific correctness of the example. |

For the committed Figure 1 revision reviewed here, the rendering dependencies listed in [`README.md`](README.md) are Python 3.10.14, Matplotlib 3.10.8 and Pillow 12.2.0. The script uses **DejaVu Sans**, not Arimo. The 1000-dpi RGB TIFF is produced using Pillow's `convert("RGB")`; the code does not perform a separate explicit alpha-compositing step. Inspect any production export at its intended physical size, especially the small safeguard-strip labels.

**Reproduction:** In a clean copy of the pinned source and environment, run `python make_figure_1.py`, then compare the printed output SHA-256 digests with the hashes documented in `README.md`. Re-rendering in an existing release checkout overwrites files, so use a disposable copy if byte-level preservation matters. Run `python verify_publication_snapshot.py` from the repository root to check the committed snapshot and source-to-walkthrough mapping.

## Line-indexed source reference

The verifier requires a verbatim, individually numbered copy of all 362 source lines, including empty lines. The index below preserves that contract. **Explanations are attached to meaningful operations and design choices, not every blank line or syntactic delimiter.** Section-level explanations above provide the rationale for groups of related operations.

<details>
<summary>Expand the exact 362-line source index</summary>

## Configuration and reproducible typography (lines 1–55)

The imports, fixed canvas dimensions, named palette and font settings establish an explicit render environment. The mm-to-inch conversion matters because Matplotlib expects figure dimensions in inches, while journal artwork is sized in millimetres.

### Line 1

```python
#!/usr/bin/env python3
```

### Line 2

```python
from pathlib import Path
```

### Line 3

```python
import hashlib
```

### Line 4

```python
from datetime import datetime, timezone
```

### Line 5

```python
import matplotlib as mpl
```

### Line 6

```python
import matplotlib.pyplot as plt
```

### Line 7

```python
from matplotlib.patches import Circle, FancyBboxPatch, Polygon
```

### Line 8

```python
from matplotlib import font_manager
```

### Line 9

```python
from PIL import Image
```

### Line 10

```python

```

### Line 11

```python
HERE = Path(__file__).resolve().parent
```

Use the script directory, not the caller’s current directory, to locate the five output files.

### Line 12

```python

```

### Line 13

```python
# Nature-style production dimensions: 180 mm wide, double-column figure.
```

### Line 14

```python
MM = 1 / 25.4
```

Matplotlib accepts inches; converting millimetres here keeps the physical production size explicit.

### Line 15

```python
FIG_W_MM = 180.0
```

Use 180 mm width for the artwork, with no silent rescaling by the plotting functions.

### Line 16

```python
FIG_H_MM = 135.0
```

The 135 mm height accommodates three panels and the safeguard strip in a 4:3 landscape canvas.

### Line 17

```python

```

### Line 18

```python
# Pin the font so the same generator does not silently change typography
```

### Line 19

```python
# according to whichever system fonts happen to be installed.
```

### Line 20

```python
# DejaVu Sans is distributed with Matplotlib and is therefore available
```

### Line 21

```python
# in the declared rendering environment.
```

### Line 22

```python
FONT = "DejaVu Sans"
```

The pinned family used by this generator is DejaVu Sans; update the README if this changes.

### Line 23

```python

```

### Line 24

```python
mpl.rcParams.update({
```

Global rendering settings are centralized so exports cannot silently diverge across panels.

### Line 25

```python
    "font.family": FONT,
```

Font selection affects text widths and label collision risk, not only appearance.

### Line 26

```python
    "font.size": 7.2,
```

### Line 27

```python
    "pdf.fonttype": 42,
```

Type 42 output embeds/uses TrueType-compatible font representations in vector-oriented exports.

### Line 28

```python
    "ps.fonttype": 42,
```

### Line 29

```python
    "svg.fonttype": "none",
```

Keeping SVG lettering as text makes later editorial adjustments possible without outlining every glyph.

### Line 30

```python
    "svg.hashsalt": "branchsnv-figure1-nature-methods-v1",
```

A fixed SVG identifier salt controls automatically generated element IDs, reducing avoidable diff noise.

### Line 31

```python
    "axes.linewidth": 0.7,
```

### Line 32

```python
    "lines.solid_capstyle": "round",
```

### Line 33

```python
    "lines.solid_joinstyle": "round",
```

### Line 34

```python
})
```

### Line 35

```python

```

### Line 36

```python
# Restrained semantic palette.
```

### Line 37

```python
INK = "#1F2328"
```

### Line 38

```python
MUTED = "#687078"
```

### Line 39

```python
RULE = "#C9CDD2"
```

### Line 40

```python
LIGHT = "#EEF3F7"
```

### Line 41

```python
LIGHT_BLUE = "#F2F7FC"
```

### Line 42

```python
LIGHT_ORANGE = "#FFF5EC"
```

### Line 43

```python
BLUE = "#1565C0"
```

### Line 44

```python
RED = "#D71920"
```

### Line 45

```python
ORANGE = "#F05A00"
```

### Line 46

```python
PURPLE = "#7B2CBF"
```

### Line 47

```python
WHITE = "#FFFFFF"
```

### Line 48

```python

```

### Line 49

```python
PANEL_FS = 8.0
```

### Line 50

```python
TITLE_FS = 9.7
```

### Line 51

```python
SUBHEAD_FS = 7.4
```

### Line 52

```python
BODY_FS = 7.0
```

### Line 53

```python
SMALL_FS = 6.2
```

### Line 54

```python
BIG_FS = 16.0
```

### Line 55

```python

```

## Reusable drawing primitives (lines 56–110)

Text, rule, patch and icon helpers work in axis coordinates; this avoids repeating coordinate transforms and reduces inconsistencies between panels. Icon paths are decorative labels, not analytical data.

### Line 56

```python
def T(ax, x, y, s, **kwargs):
```

All visible labels pass through one helper instead of redefining defaults at each call site.

### Line 57

```python
    base = dict(transform=ax.transAxes, color=INK, ha="left", va="center")
```

`transAxes` gives every label the same normalized coordinate system as the panels.

### Line 58

```python
    base.update(kwargs)
```

### Line 59

```python
    return ax.text(x, y, s, **base)
```

Forward keyword overrides to `ax.text`; callers can adjust font, alignment and line spacing while inheriting defaults.

### Line 60

```python

```

### Line 61

```python
def HLINE(ax, y):
```

The horizontal rule helper divides sections without changing the data coordinate limits.

### Line 62

```python
    ax.plot([0.015, 0.985], [y, y], transform=ax.transAxes, color=RULE, lw=0.75, clip_on=False)
```

### Line 63

```python

```

### Line 64

```python
def panel_label(ax, letter, title, y):
```

Panel letters remain lower-case and visually separate from panel titles.

### Line 65

```python
    T(ax, 0.016, y, letter, fontsize=PANEL_FS, fontweight="bold", va="top")
```

### Line 66

```python
    T(ax, 0.064, y, title, fontsize=TITLE_FS, fontweight="bold", va="top")
```

### Line 67

```python

```

### Line 68

```python
def rounded_box(ax, x, y, w, h, fc, ec="none", radius=0.012):
```

Rounded cards encode categorical groupings; the patch is added to the same axes as the text.

### Line 69

```python
    p = FancyBboxPatch((x, y), w, h, transform=ax.transAxes,
```

### Line 70

```python
                       boxstyle=f"round,pad=0.004,rounding_size={radius}",
```

### Line 71

```python
                       facecolor=fc, edgecolor=ec, linewidth=0.6)
```

### Line 72

```python
    ax.add_patch(p)
```

### Line 73

```python
    return p
```

### Line 74

```python

```

### Line 75

```python
def draw_tag_icon(ax, x, y, s=0.018):
```

The tag pictogram is assembled from a polygon and open circle, not an external image asset.

### Line 76

```python
    pts = [(x-s, y), (x-0.2*s, y+s), (x+s, y+s), (x+s, y-0.2*s),
```

### Line 77

```python
           (x-0.2*s, y-s)]
```

### Line 78

```python
    ax.add_patch(Polygon(pts, closed=True, fill=False, ec=INK, lw=0.75, transform=ax.transAxes))
```

### Line 79

```python
    ax.add_patch(Circle((x+0.55*s, y+0.55*s), 0.16*s, transform=ax.transAxes,
```

### Line 80

```python
                        fill=False, ec=INK, lw=0.7))
```

### Line 81

```python

```

### Line 82

```python
def draw_stack_icon(ax, x, y, s=0.016):
```

Three offset diamond shapes form the stack icon; there is no dependency on icon fonts.

### Line 83

```python
    for dy in (0.010, 0.000, -0.010):
```

### Line 84

```python
        pts = [(x-s, y+dy), (x, y+dy+s*0.7), (x+s, y+dy), (x, y+dy-s*0.7)]
```

### Line 85

```python
        ax.add_patch(Polygon(pts, closed=True, fill=False, ec=INK, lw=0.72, transform=ax.transAxes))
```

### Line 86

```python

```

### Line 87

```python
def draw_doc_icon(ax, x, y, w=0.022, h=0.034):
```

The document symbol is vector geometry, so it scales with the artwork.

### Line 88

```python
    rounded_box(ax, x-w/2, y-h/2, w, h, WHITE, INK, 0.003)
```

### Line 89

```python
    ax.plot([x+w*0.18, x+w*0.34], [y+h*0.50, y+h*0.28], transform=ax.transAxes, color=INK, lw=0.7)
```

### Line 90

```python
    ax.plot([x-w*0.28, x+w*0.20], [y+0.005, y+0.005], transform=ax.transAxes, color=INK, lw=0.6)
```

### Line 91

```python
    ax.plot([x-w*0.28, x+w*0.12], [y-0.003, y-0.003], transform=ax.transAxes, color=INK, lw=0.6)
```

### Line 92

```python
    ax.plot([x-w*0.28, x+w*0.05], [y-0.011, y-0.011], transform=ax.transAxes, color=INK, lw=0.6)
```

### Line 93

```python

```

### Line 94

```python
def draw_tree_icon(ax, x, y, descendants=False):
```

The branch/tree symbol changes shape according to whether it denotes descendants.

### Line 95

```python
    lw = 0.72
```

### Line 96

```python
    if descendants:
```

The descendant variant draws a small cluster of terminal taxa.

### Line 97

```python
        ax.plot([x-0.020, x-0.008], [y, y], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 98

```python
        ax.plot([x-0.008, x-0.008], [y-0.014, y+0.014], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 99

```python
        for yy in (y-0.014, y, y+0.014):
```

### Line 100

```python
            ax.plot([x-0.008, x+0.012], [yy, yy], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 101

```python
            ax.add_patch(Circle((x+0.014, yy), 0.004, transform=ax.transAxes, fill=False, ec=INK, lw=0.7))
```

### Line 102

```python
    else:
```

### Line 103

```python
        ax.add_patch(Circle((x-0.020, y-0.015), 0.0045, transform=ax.transAxes, fc=INK, ec=INK))
```

The other variant includes a dark root marker to emphasize orientation.

### Line 104

```python
        ax.plot([x-0.016, x-0.016], [y-0.015, y+0.015], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 105

```python
        ax.plot([x-0.016, x+0.006], [y+0.006, y+0.006], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 106

```python
        ax.plot([x+0.006, x+0.006], [y-0.006, y+0.016], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 107

```python
        for yy in (y-0.006, y+0.016):
```

### Line 108

```python
            ax.plot([x+0.006, x+0.022], [yy, yy], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 109

```python
            ax.add_patch(Circle((x+0.024, yy), 0.004, transform=ax.transAxes, fill=False, ec=INK, lw=0.7))
```

### Line 110

```python

```

## Panel a — topology and observed nucleotides (lines 111–185)

The tree is drawn segment by segment so the focal edge, root and descendant set remain visually distinct. The nine nucleotide states are specified explicitly; none are read from an alignment.

### Line 111

```python
def draw_panel_a(ax):
```

Panel a is a fixed explanatory topology, not a tree inferred from sequence data.

### Line 112

```python
    panel_label(ax, "a", "One branch, one site", 0.982)
```

### Line 113

```python

```

### Line 114

```python
    # Tree geometry
```

### Line 115

```python
    x0 = 0.165
```

### Line 116

```python
    x1 = 0.285
```

### Line 117

```python
    x2 = 0.420
```

### Line 118

```python
    xt = 0.535
```

### Line 119

```python
    ys = [0.930, 0.898, 0.866, 0.800, 0.768, 0.736, 0.665, 0.633, 0.601]
```

One y-coordinate per tip ensures the branch segments and nucleotide columns align.

### Line 120

```python
    y_focal = ys[1]
```

The selected focal edge joins the upper split to the three-`G` clade.

### Line 121

```python
    y_mid = ys[4]
```

### Line 122

```python
    y_bot = ys[7]
```

### Line 123

```python
    y_upper_split = (y_focal + y_mid) / 2
```

### Line 124

```python
    y_root = (y_upper_split + y_bot) / 2
```

The root marker is placed on the main trunk; its location establishes orientation in this diagram.

### Line 125

```python

```

### Line 126

```python
    lw = 0.90
```

### Line 127

```python
    # Root / main tree
```

### Line 128

```python
    ax.plot([x0, x0], [y_bot, y_upper_split], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 129

```python
    ax.plot([x0, x1], [y_upper_split, y_upper_split], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 130

```python
    ax.plot([x0, x2-0.115], [y_bot, y_bot], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 131

```python

```

### Line 132

```python
    # Upper split
```

### Line 133

```python
    ax.plot([x1, x1], [y_mid, y_focal], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 134

```python

```

### Line 135

```python
    # focal edge
```

### Line 136

```python
    ax.plot([x1, x2], [y_focal, y_focal], transform=ax.transAxes, color=RED, lw=1.65)
```

Only the focal connecting segment is highlighted red, avoiding confusion with the entire clade.

### Line 137

```python
    T(ax, (x1+x2)/2, y_focal+0.028, "focal edge", fontsize=SMALL_FS, fontweight="bold",
```

### Line 138

```python
      color=RED, ha="center")
```

### Line 139

```python

```

### Line 140

```python
    # Focal clade
```

### Line 141

```python
    ax.plot([x2, x2], [ys[2], ys[0]], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 142

```python
    for y in ys[:3]:
```

Three `G` terminals define the focal sampled descendants.

### Line 143

```python
        ax.plot([x2, xt], [y, y], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 144

```python

```

### Line 145

```python
    # Middle clade
```

### Line 146

```python
    ax.plot([x1, x2], [y_mid, y_mid], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 147

```python
    ax.plot([x2, x2], [ys[5], ys[3]], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 148

```python
    for y in ys[3:6]:
```

The middle clade contains three `A` tips.

### Line 149

```python
        ax.plot([x2, xt], [y, y], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 150

```python

```

### Line 151

```python
    # Bottom clade
```

### Line 152

```python
    xb = x2 - 0.115
```

### Line 153

```python
    ax.plot([xb, xb], [ys[8], ys[6]], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 154

```python
    for y in ys[6:9]:
```

The lower clade contains `A`, `A` and an external `G`.

### Line 155

```python
        ax.plot([xb, xt], [y, y], transform=ax.transAxes, color=INK, lw=lw)
```

### Line 156

```python

```

### Line 157

```python
    # tips
```

### Line 158

```python
    for y in ys:
```

### Line 159

```python
        ax.add_patch(Circle((xt, y), 0.0055, transform=ax.transAxes,
```

### Line 160

```python
                            fc=WHITE, ec=INK, lw=0.75))
```

### Line 161

```python

```

### Line 162

```python
    # root
```

### Line 163

```python
    ax.add_patch(Circle((x0, y_root), 0.006, transform=ax.transAxes, fc=INK, ec=INK))
```

A filled circle identifies the root separately from hollow tip markers.

### Line 164

```python
    T(ax, x0-0.014, y_root-0.005, "root", fontsize=SMALL_FS, color=MUTED, ha="right")
```

### Line 165

```python

```

### Line 166

```python
    # focal descendants bracket
```

### Line 167

```python
    bx = 0.562
```

### Line 168

```python
    ax.plot([bx, bx], [ys[2]-0.008, ys[0]+0.008], transform=ax.transAxes, color=BLUE, lw=0.9)
```

The blue bracket spans exactly the three focal tips rather than all nearby tips.

### Line 169

```python
    ax.plot([bx-0.010, bx], [ys[0]+0.008, ys[0]+0.008], transform=ax.transAxes, color=BLUE, lw=0.9)
```

### Line 170

```python
    ax.plot([bx-0.010, bx], [ys[2]-0.008, ys[2]-0.008], transform=ax.transAxes, color=BLUE, lw=0.9)
```

### Line 171

```python
    T(ax, bx+0.013, y_focal, "focal\ndescendants", fontsize=SMALL_FS, fontweight="bold",
```

### Line 172

```python
      color=BLUE, ha="left", linespacing=0.95)
```

### Line 173

```python

```

### Line 174

```python
    # site-state column
```

### Line 175

```python
    ax.plot([0.665, 0.665], [0.585, 0.947], transform=ax.transAxes, color=RULE, lw=0.7)
```

### Line 176

```python
    T(ax, 0.720, 0.952, "one site", fontsize=SUBHEAD_FS, fontweight="bold", ha="center")
```

### Line 177

```python

```

### Line 178

```python
    states = ["G","G","G","A","A","A","A","A","G"]
```

This is the entire observed tip-state dataset used by the illustration: `GGG / AAA / AAG`.

### Line 179

```python
    for i, (y, base) in enumerate(zip(ys, states)):
```

### Line 180

```python
        color = BLUE if i < 3 else (RED if i == 8 else INK)
```

The external `G` is red to demonstrate non-exclusivity; focal `G` labels are blue.

### Line 181

```python
        T(ax, 0.720, y, base, fontsize=BODY_FS, fontweight="bold", color=color, ha="center")
```

### Line 182

```python

```

### Line 183

```python
    T(ax, 0.800, 0.875, "Focal clade:  G G G", fontsize=BODY_FS, fontweight="bold", color=BLUE)
```

### Line 184

```python
    T(ax, 0.800, 0.815, "Outside includes G", fontsize=BODY_FS, fontweight="bold", color=RED)
```

### Line 185

```python

```

## Panel b — two separate tests (lines 186–234)

The left card displays observed tip states; the right card depicts the inferred A→G pair. These two outputs are deliberately drawn separately. The inference itself is not computed by this script.

### Line 186

```python
def draw_panel_b(ax):
```

The central panel compares observations and inference, not two algorithms or measured scores.

### Line 187

```python
    panel_label(ax, "b", "Two questions, different answers", 0.552)
```

### Line 188

```python

```

### Line 189

```python
    # left / right anchors
```

### Line 190

```python
    lx, rx = 0.065, 0.640
```

### Line 191

```python
    cx = 0.505
```

### Line 192

```python

```

### Line 193

```python
    T(ax, lx, 0.505, "OBSERVED", fontsize=SUBHEAD_FS, fontweight="bold", color=BLUE)
```

The left-hand question can be answered without ancestral-state reconstruction.

### Line 194

```python
    T(ax, lx, 0.474, "Clade-exclusive?", fontsize=BODY_FS, fontweight="bold")
```

### Line 195

```python

```

### Line 196

```python
    # Left observation card
```

### Line 197

```python
    rounded_box(ax, lx, 0.354, 0.345, 0.095, LIGHT_BLUE)
```

### Line 198

```python
    T(ax, lx+0.018, 0.415, "focal", fontsize=SMALL_FS, color=MUTED)
```

### Line 199

```python
    for x in (lx+0.098, lx+0.137, lx+0.176):
```

### Line 200

```python
        T(ax, x, 0.415, "G", fontsize=BODY_FS, fontweight="bold", color=BLUE, ha="center")
```

### Line 201

```python

```

### Line 202

```python
    T(ax, lx+0.018, 0.375, "outside", fontsize=SMALL_FS, color=MUTED)
```

### Line 203

```python
    bases = [("A",INK),("A",INK),("A",INK),("A",INK),("A",INK),("G",RED)]
```

The external list includes a single `G`; this is sufficient to reject exclusivity.

### Line 204

```python
    for i,(b,c) in enumerate(bases):
```

### Line 205

```python
        T(ax, lx+0.098+i*0.039, 0.375, b, fontsize=BODY_FS, fontweight="bold", color=c, ha="center")
```

### Line 206

```python

```

### Line 207

```python
    T(ax, lx, 0.318, "NO", fontsize=BIG_FS, fontweight="bold", color=BLUE)
```

The “NO” is specific to *fixed exclusivity*, not to existence of a substitution.

### Line 208

```python
    T(ax, lx+0.093, 0.322, "not fixed-exclusive", fontsize=BODY_FS, fontweight="bold")
```

### Line 209

```python
    T(ax, lx+0.093, 0.295, "G occurs outside the clade", fontsize=SMALL_FS, color=MUTED)
```

### Line 210

```python

```

### Line 211

```python
    # center separator
```

### Line 212

```python
    ax.plot([cx, cx], [0.285, 0.495], transform=ax.transAxes, color=RULE, lw=0.7)
```

A vertical separator keeps the two logical questions distinct.

### Line 213

```python
    T(ax, cx, 0.392, "≠", fontsize=21, fontweight="bold", ha="center")
```

### Line 214

```python
    T(ax, cx, 0.337, "kept separate", fontsize=SMALL_FS, color=MUTED, ha="center")
```

### Line 215

```python

```

### Line 216

```python
    # right
```

### Line 217

```python
    T(ax, rx, 0.505, "INFERRED", fontsize=SUBHEAD_FS, fontweight="bold", color=ORANGE)
```

The right-hand question concerns a specific parent–child edge in the optimal reconstruction.

### Line 218

```python
    T(ax, rx, 0.474, "Substitution on the focal edge?", fontsize=BODY_FS, fontweight="bold")
```

### Line 219

```python
    rounded_box(ax, rx, 0.354, 0.325, 0.095, LIGHT_ORANGE)
```

### Line 220

```python

```

### Line 221

```python
    px, gx, y = rx+0.082, rx+0.255, 0.382
```

### Line 222

```python
    T(ax, px, y+0.040, "parent", fontsize=SMALL_FS, color=MUTED, ha="center")
```

### Line 223

```python
    T(ax, gx, y+0.040, "child", fontsize=SMALL_FS, color=MUTED, ha="center")
```

### Line 224

```python
    ax.add_patch(Circle((px, y), 0.021, transform=ax.transAxes, fill=False, ec=ORANGE, lw=1.0))
```

Open circles represent inferred parent/child states, not sampled tips.

### Line 225

```python
    ax.add_patch(Circle((gx, y), 0.021, transform=ax.transAxes, fill=False, ec=BLUE, lw=1.0))
```

### Line 226

```python
    T(ax, px, y, "A", fontsize=BODY_FS, fontweight="bold", ha="center")
```

### Line 227

```python
    T(ax, gx, y, "G", fontsize=BODY_FS, fontweight="bold", color=BLUE, ha="center")
```

### Line 228

```python
    ax.annotate("", xy=(gx-0.030,y), xytext=(px+0.030,y), xycoords=ax.transAxes,
```

The arrow indicates direction from parent `A` to child `G`.

### Line 229

```python
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.9))
```

### Line 230

```python

```

### Line 231

```python
    T(ax, rx, 0.318, "YES", fontsize=BIG_FS, fontweight="bold", color=ORANGE)
```

“YES” encodes the worked parsimony conclusion; it is not computed inside this drawing function.

### Line 232

```python
    T(ax, rx+0.093, 0.322, "unambiguous A→G", fontsize=BODY_FS, fontweight="bold")
```

### Line 233

```python
    T(ax, rx+0.093, 0.295, "Only optimal focal-edge pair: A→G", fontsize=SMALL_FS, color=MUTED)
```

### Line 234

```python

```

## Panel c — uncertainty classes and safeguards (lines 235–284)

The table is an interpretive key for sets of globally optimal focal-edge pairs. It is not four observations from panel a. The bottom strip states conditions required to interpret a branch-level result.

### Line 235

```python
def draw_panel_c(ax):
```

These rows are an explanatory taxonomy of possible pair sets, not alternative outcomes for panel a.

### Line 236

```python
    panel_label(ax, "c", "Retain all optimal focal-edge state pairs", 0.258)
```

### Line 237

```python

```

### Line 238

```python
    x0, x1, x2 = 0.065, 0.390, 0.665
```

### Line 239

```python
    rounded_box(ax, x0, 0.194, x2-x0, 0.036, LIGHT)
```

### Line 240

```python
    T(ax, x0+0.012, 0.212, "Optimal parent→child pair(s)", fontsize=SMALL_FS, fontweight="bold")
```

### Line 241

```python
    T(ax, x1+0.012, 0.212, "BRANCHSNV reports", fontsize=SMALL_FS, fontweight="bold")
```

### Line 242

```python
    ax.plot([x1, x1], [0.095, 0.231], transform=ax.transAxes, color=RULE, lw=0.55)
```

### Line 243

```python

```

### Line 244

```python
    rows = [
```

Store the four pair sets with their distinct reporting categories for consistent row drawing.

### Line 245

```python
        ("A→G only", "Unambiguous change", BLUE),
```

### Line 246

```python
        ("A→G or C→G", "State ambiguity", ORANGE),
```

### Line 247

```python
        ("A→G or G→G", "Placement ambiguity", PURPLE),
```

### Line 248

```python
        ("G→G only", "No change", MUTED),
```

### Line 249

```python
    ]
```

### Line 250

```python
    ys = [0.179,0.153,0.127,0.101]
```

### Line 251

```python
    for i,(lhs,rhs,c) in enumerate(rows):
```

Render the rows from one structured list to prevent labels and colours becoming misaligned.

### Line 252

```python
        T(ax, x0+0.012, ys[i], lhs, fontsize=BODY_FS)
```

### Line 253

```python
        T(ax, x1+0.012, ys[i], rhs, fontsize=BODY_FS, fontweight="bold", color=c)
```

### Line 254

```python
        if i < 3:
```

### Line 255

```python
            ax.plot([x0, x2], [ys[i]-0.014, ys[i]-0.014], transform=ax.transAxes,
```

### Line 256

```python
                    color="#E1E5E8", lw=0.5)
```

### Line 257

```python

```

### Line 258

```python
    ax.plot([0.685,0.685], [0.100,0.228], transform=ax.transAxes, color=RULE, lw=0.65)
```

### Line 259

```python
    T(ax, 0.710, 0.186, "No arbitrary tie-breaking", fontsize=BODY_FS, fontweight="bold")
```

This statement makes clear why silently choosing one equally parsimonious assignment would be misleading.

### Line 260

```python
    T(ax, 0.710, 0.149, "All globally optimal focal-edge\nstate pairs are retained.",
```

### Line 261

```python
      fontsize=SMALL_FS, color=MUTED, va="center", linespacing=1.1)
```

### Line 262

```python

```

### Line 263

```python
    # Safeguards
```

### Line 264

```python
    HLINE(ax, 0.084)
```

Separate the safeguards from the uncertainty table; they concern prerequisites, not additional output classes.

### Line 265

```python
    T(ax, 0.015, 0.066, "DESIGN SAFEGUARDS", fontsize=SMALL_FS, fontweight="bold", color=MUTED)
```

### Line 266

```python

```

### Line 267

```python
    bounds = [0.015, 0.209, 0.403, 0.597, 0.791, 0.985]
```

### Line 268

```python
    modules = [
```

Five safeguard items correspond to rooting, branch definition, taxon identity, tie retention and provenance.

### Line 269

```python
        ("Explicit root", "defines direction"),
```

### Line 270

```python
        ("Exact descendant set", "defines branch"),
```

### Line 271

```python
        ("Exact taxon labels", "define correspondence"),
```

### Line 272

```python
        ("Complete optimal set", "retains uncertainty"),
```

### Line 273

```python
        ("Deterministic provenance", "supports auditability"),
```

### Line 274

```python
    ]
```

### Line 275

```python
    for i, (head, sub) in enumerate(modules):
```

### Line 276

```python
        left, right = bounds[i], bounds[i+1]
```

### Line 277

```python
        if i > 0:
```

### Line 278

```python
            ax.plot([left, left], [0.012, 0.065], transform=ax.transAxes, color=RULE, lw=0.55)
```

### Line 279

```python
        x = (left + right) / 2
```

### Line 280

```python
        head_fs = 5.45 if head == "Deterministic provenance" else 5.70
```

Long safeguard text uses a smaller fixed font size; check it at final physical dimensions.

### Line 281

```python
        sub_fs = 5.15 if head == "Deterministic provenance" else 5.35
```

### Line 282

```python
        T(ax, x, 0.043, head, fontsize=head_fs, fontweight="bold", ha="center")
```

### Line 283

```python
        T(ax, x, 0.023, sub, fontsize=sub_fs, color=MUTED, ha="center")
```

### Line 284

```python

```

## Output assembly and immutable metadata (lines 285–362)

The three panels share one figure canvas. Export settings and fixed metadata reduce accidental differences across renders; the final hashes are the means of verifying the exact produced files.

### Line 285

```python
def build():
```

The build function assembles the complete deliverable and records its hashes.

### Line 286

```python
    fig = plt.figure(figsize=(FIG_W_MM*MM, FIG_H_MM*MM), facecolor=WHITE)
```

Physical width/height is converted to inches once; exports use the same Figure object.

### Line 287

```python
    ax = fig.add_axes([0,0,1,1])
```

### Line 288

```python
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
```

Hide axes: all line art is explanatory geometry, not a quantitative plot.

### Line 289

```python

```

### Line 290

```python
    draw_panel_a(ax)
```

Draw panel a first so its tree and nucleotide pattern establish the context for the later conclusions.

### Line 291

```python
    HLINE(ax, 0.570)
```

A horizontal rule marks the transition from the observed-tip diagram to the two questions.

### Line 292

```python
    draw_panel_b(ax)
```

### Line 293

```python
    HLINE(ax, 0.270)
```

### Line 294

```python
    draw_panel_c(ax)
```

Panel c completes the logic with uncertainty classes and safeguards.

### Line 295

```python

```

### Line 296

```python
    fixed_dt = datetime(2026, 10, 5, 0, 0, 0, tzinfo=timezone.utc)
```

Use a fixed UTC instant for PDF creation and modification metadata instead of wall-clock timestamps.

### Line 297

```python
    fixed_date = "2026-10-05T00:00:00Z"
```

### Line 298

```python
    creator = "BRANCHSNV Figure 1 reproducible generator"
```

### Line 299

```python

```

### Line 300

```python
    fig.savefig(
```

The first export is a vector PDF with explicitly pinned provenance metadata.

### Line 301

```python
        HERE/"Figure_1.pdf",
```

### Line 302

```python
        facecolor=WHITE,
```

### Line 303

```python
        metadata={
```

### Line 304

```python
            "Title": "BRANCHSNV Figure 1",
```

### Line 305

```python
            "Author": "Rhys T. White et al.",
```

### Line 306

```python
            "Subject": "Analytical design of BRANCHSNV",
```

### Line 307

```python
            "Creator": creator,
```

### Line 308

```python
            "CreationDate": fixed_dt,
```

### Line 309

```python
            "ModDate": fixed_dt,
```

### Line 310

```python
        },
```

### Line 311

```python
    )
```

### Line 312

```python

```

### Line 313

```python
    fig.savefig(
```

SVG provides an editable vector version; text remains text because of the global rendering setting.

### Line 314

```python
        HERE/"Figure_1_editable.svg",
```

### Line 315

```python
        facecolor=WHITE,
```

### Line 316

```python
        metadata={
```

### Line 317

```python
            "Title": "BRANCHSNV Figure 1",
```

### Line 318

```python
            "Creator": creator,
```

### Line 319

```python
            "Date": fixed_date,
```

### Line 320

```python
        },
```

### Line 321

```python
    )
```

### Line 322

```python

```

### Line 323

```python
    fig.savefig(
```

The 600-dpi PNG is for review/preview, not the editable source.

### Line 324

```python
        HERE/"Figure_1_preview_600dpi.png",
```

### Line 325

```python
        dpi=600,
```

### Line 326

```python
        facecolor=WHITE,
```

### Line 327

```python
        metadata={
```

### Line 328

```python
            "Title": "BRANCHSNV Figure 1",
```

### Line 329

```python
            "Author": "Rhys T. White et al.",
```

### Line 330

```python
            "Software": creator,
```

### Line 331

```python
        },
```

### Line 332

```python
    )
```

### Line 333

```python

```

### Line 334

```python
    fig.savefig(
```

The 1000-dpi LZW TIFF is a high-resolution raster deliverable.

### Line 335

```python
        HERE/"Figure_1_1000dpi.tiff",
```

### Line 336

```python
        dpi=1000,
```

### Line 337

```python
        facecolor=WHITE,
```

### Line 338

```python
        pil_kwargs={"compression":"tiff_lzw"},
```

### Line 339

```python
    )
```

### Line 340

```python

```

### Line 341

```python
    plt.close(fig)
```

Close the Matplotlib figure before post-processing exported files to release resources.

### Line 342

```python

```

### Line 343

```python
    # Normalize Matplotlib SVG whitespace so the generated source is
```

### Line 344

```python
    # byte-stable and passes git diff --check.
```

### Line 345

```python
    svg_path = HERE/"Figure_1_editable.svg"
```

Normalize whitespace after SVG export for a stable committed text representation.

### Line 346

```python
    svg_text = svg_path.read_text(encoding="utf-8")
```

### Line 347

```python
    svg_text = "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n"
```

Strip trailing whitespace without changing geometric SVG elements or text content.

### Line 348

```python
    svg_path.write_text(svg_text, encoding="utf-8")
```

### Line 349

```python

```

### Line 350

```python
    with Image.open(HERE/"Figure_1_1000dpi.tiff") as im:
```

Open the TIFF produced above for a second RGB-specific export.

### Line 351

```python
        im.convert("RGB").save(HERE/"Figure_1_1000dpi_RGB.tiff",
```

Convert RGB channels with Pillow; this is not an explicit alpha compositing operation.

### Line 352

```python
                               compression="tiff_lzw", dpi=(1000,1000))
```

### Line 353

```python

```

### Line 354

```python
    print(f"Font: {FONT}")
```

Print the chosen font to make the effective render configuration visible in the build log.

### Line 355

```python
    print(f"Figure size: {FIG_W_MM:.1f} × {FIG_H_MM:.1f} mm")
```

### Line 356

```python
    for name in ["Figure_1.pdf","Figure_1_editable.svg","Figure_1_preview_600dpi.png",
```

### Line 357

```python
                 "Figure_1_1000dpi.tiff","Figure_1_1000dpi_RGB.tiff"]:
```

### Line 358

```python
        p=HERE/name
```

### Line 359

```python
        print(f"{name}\t{hashlib.sha256(p.read_bytes()).hexdigest()}")
```

Digest each final output only after TIFF conversion and SVG normalization have completed.

### Line 360

```python

```

### Line 361

```python
if __name__ == "__main__":
```

Prevent an import of this script from automatically overwriting the release artwork.

### Line 362

```python
    build()
```

Invoke the builder when called as a standalone program.

</details>
