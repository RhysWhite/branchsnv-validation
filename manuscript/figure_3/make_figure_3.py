from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
import hashlib

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image
import pandas as pd
from Bio import Phylo

# Figure 1 palette / manuscript conventions
INK = "#222222"
GREY = "#666666"
LIGHT_GREY = "#D9D9D9"
BLUE = "#1F5AA6"
ORANGE = "#D95F02"
PURPLE = "#7B3294"
PALE_ORANGE = "#FBE8D8"

# Final artwork is sized for a compact full-width landscape figure.
FIG_W = 6.50
FIG_H = 4.40

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Arimo", "Liberation Sans", "DejaVu Sans"],
    "font.size": 7.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})


@dataclass
class Summary:
    taxa: int
    variable_sites: int
    branches: int
    informative: int
    both: int
    both_pct: float
    unamb_not_fixed: int
    unamb_not_fixed_pct: float
    placement_ambiguous: int
    placement_ambiguous_pct: float
    derived_state_outside: int
    derived_state_outside_pct: float
    descendant_not_fixed: int
    descendant_not_fixed_pct: float


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_summary(root: Path) -> Summary:
    ds = pd.read_csv(root / "results/06_empirical_cross_classification/dataset_summary.tsv", sep="\t")
    ev = pd.read_csv(root / "results/06_empirical_cross_classification/informative_events.tsv", sep="\t")
    ev = ev[ev["root_adjacent"] == 0].copy()

    informative = int(ds["informative"].sum())
    both = int(ds["both"].sum())
    unamb_not_fixed = int(ds["unambiguous_not_fixed"].sum())
    placement = int(ds["placement_ambiguous"].sum())
    outside = int((ev["nonexclusivity_mechanism"] == "derived_state_outside").sum())
    not_fixed = int((ev["nonexclusivity_mechanism"] == "descendant_not_fixed").sum())

    return Summary(
        taxa=int(ds["taxa"].sum()),
        variable_sites=int(ds["variable_sites"].sum()),
        branches=int(ds["eligible_non_root_adjacent_branches"].sum()),
        informative=informative,
        both=both,
        both_pct=100 * both / informative,
        unamb_not_fixed=unamb_not_fixed,
        unamb_not_fixed_pct=100 * unamb_not_fixed / informative,
        placement_ambiguous=placement,
        placement_ambiguous_pct=100 * placement / informative,
        derived_state_outside=outside,
        derived_state_outside_pct=100 * outside / unamb_not_fixed,
        descendant_not_fixed=not_fixed,
        descendant_not_fixed_pct=100 * not_fixed / unamb_not_fixed,
    )


def load_alignment_site(root: Path, site_id: str) -> dict[str, str]:
    path = root / "inputs/empirical/clade_a_alignment.nex"
    taxa: list[str] = []
    in_matrix = False
    with path.open() as handle:
        for raw in handle:
            line = raw.strip()
            if line.startswith("taxlabels"):
                taxa = line.split("\t")[1:]
            elif line == "matrix":
                in_matrix = True
            elif in_matrix:
                if line == ";":
                    break
                if line.startswith(site_id + "\t"):
                    values = line.split("\t")[1:]
                    return dict(zip(taxa, values))
    raise ValueError(f"Site not found: {site_id}")


def load_clade_a_example(root: Path):
    site_id = "AP009378.1_4301132"
    states = load_alignment_site(root, site_id)
    g_taxa = sorted(t for t, state in states.items() if state == "G")

    tree_text = (root / "inputs/empirical/clade_a_tree.nwk").read_text().strip()
    tree = Phylo.read(StringIO(tree_text), "newick")

    focal_four = ["DRR092886", "SRR10420675", "SRR23133748", "SRR18207138"]
    outside_tip = "SRR8871728"
    subtree = tree.common_ancestor(g_taxa)  # 14-tip minimal clade containing all five G observations
    focal_clade = tree.common_ancestor(focal_four)
    return site_id, states, subtree, focal_four, focal_clade, outside_tip


def panel_letter(ax, letter: str) -> None:
    # Keep panel letters fully inside the axes so no glyph is clipped at the
    # top edge of the exported figure.
    ax.text(-0.04, 0.995, letter, transform=ax.transAxes,
            ha="left", va="top", fontsize=12.0, fontweight="bold", color=INK)


def rounded_box(ax, xy, width, height, edge, text, text_color=INK, face="white",
                fontsize=7.0, weight="normal"):
    x, y = xy
    box = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.008,rounding_size=0.014",
        facecolor=face, edgecolor=edge, linewidth=0.85,
    )
    ax.add_patch(box)
    ax.text(x + width / 2, y + height / 2, text,
            ha="center", va="center", fontsize=fontsize,
            color=text_color, fontweight=weight, linespacing=1.05)


def draw_panel_a(ax, s: Summary) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    panel_letter(ax, "A")

    ax.text(0.50, 1.005, "Empirical non-equivalence", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=9.0, fontweight="bold", color=INK)
    ax.text(0.50, 0.952,
            f"{s.taxa:,} genomes · {s.variable_sites:,} variable sites · {s.branches:,} branches",
            transform=ax.transAxes, ha="center", va="top", fontsize=6.7, color=GREY)

    rounded_box(ax, (0.09, 0.80), 0.82, 0.085, INK,
                f"{s.informative:,} informative\nsite–edge comparisons",
                fontsize=7.2, weight="bold")

    # Three stacked categories: no narrow columns and no text collisions.
    rows = [
        (0.635, BLUE, f"{s.both:,} ({s.both_pct:.2f}%)",
         "Fixed-exclusive + unambiguous\nfocal-edge substitution"),
        (0.505, ORANGE, f"{s.unamb_not_fixed:,} ({s.unamb_not_fixed_pct:.2f}%)",
         "Unambiguous focal-edge substitution,\nnot fixed-exclusive"),
        (0.375, PURPLE, f"{s.placement_ambiguous:,} ({s.placement_ambiguous_pct:.2f}%)",
         "Placement-ambiguous"),
    ]
    for y, color, count, label in rows:
        ax.add_patch(Rectangle((0.09, y), 0.018, 0.078, facecolor=color, edgecolor="none"))
        ax.text(0.125, y + 0.053, count, ha="left", va="center",
                fontsize=7.3, fontweight="bold", color=color)
        ax.text(0.125, y + 0.018, label, ha="left", va="center",
                fontsize=6.55, color=INK, linespacing=1.04)

    ax.text(0.09, 0.300,
            "No fixed-exclusive comparison lacked\nan unambiguous focal-edge substitution.",
            ha="left", va="center", fontsize=6.35, color=BLUE, fontweight="bold", linespacing=1.0)

    ax.text(0.09, 0.225, f"Why were {s.unamb_not_fixed:,} unambiguous focal-edge substitutions\nnot fixed-exclusive?",
            ha="left", va="center", fontsize=6.35, color=INK, fontweight="bold", linespacing=1.0)

    x0, y0, w, h = 0.09, 0.098, 0.82, 0.078
    frac = s.derived_state_outside / s.unamb_not_fixed
    ax.add_patch(Rectangle((x0, y0), w * frac, h, facecolor=ORANGE, edgecolor="none"))
    ax.add_patch(Rectangle((x0 + w * frac, y0), w * (1 - frac), h, facecolor=PALE_ORANGE, edgecolor="none"))
    ax.add_patch(FancyBboxPatch((x0, y0), w, h,
                                boxstyle="round,pad=0,rounding_size=0.01",
                                facecolor="none", edgecolor=ORANGE, linewidth=0.75))
    ax.text(x0 + w * frac / 2, y0 + h / 2,
            f"{s.derived_state_outside:,} ({s.derived_state_outside_pct:.2f}%)\nderived nucleotide also observed\noutside the focal clade",
            ha="center", va="center", fontsize=5.85, color="white", fontweight="bold", linespacing=0.93)

    # Small category is labelled below with a short leader, preserving the true 4.44% width.
    tiny_mid = x0 + w * frac + w * (1 - frac) / 2
    ax.plot([tiny_mid, tiny_mid], [y0, 0.064], color=INK, lw=0.65)
    ax.plot([tiny_mid, 0.865], [0.064, 0.064], color=INK, lw=0.65)
    ax.text(0.865, 0.055,
            f"{s.descendant_not_fixed} ({s.descendant_not_fixed_pct:.2f}%)\ndescendant clade not fixed",
            ha="right", va="top", fontsize=5.75, color=INK, linespacing=0.96)


def get_depths(clade, current=0.0, out=None):
    if out is None:
        out = {}
    out[id(clade)] = current
    for child in clade.clades:
        get_depths(child, current + (child.branch_length or 0.0), out)
    return out


def get_ycoords(clade, terminals, out=None):
    if out is None:
        out = {}
    if clade.is_terminal():
        out[id(clade)] = terminals.index(clade)
    else:
        for child in clade.clades:
            get_ycoords(child, terminals, out)
        out[id(clade)] = sum(out[id(child)] for child in clade.clades) / len(clade.clades)
    return out


def draw_phylogram(ax, subtree, states, focal_clade, focal_four, outside_tip):
    terminals = list(subtree.get_terminals())
    depths = get_depths(subtree)
    ycoords = get_ycoords(subtree, terminals)
    n = len(terminals)
    maxdepth = max(depths[id(t)] for t in terminals)

    def yplot(clade):
        return n - 1 - ycoords[id(clade)]

    # Base phylogram.
    def recurse(clade):
        x = depths[id(clade)]
        if clade.clades:
            ys = [yplot(c) for c in clade.clades]
            ax.plot([x, x], [min(ys), max(ys)], color=INK, lw=0.72, zorder=1)
            for child in clade.clades:
                xc = depths[id(child)]
                yc = yplot(child)
                ax.plot([x, xc], [yc, yc], color=INK, lw=0.72, zorder=1)
                recurse(child)
    recurse(subtree)

    # Focal branch and focal clade descendants in Figure-1 blue.
    focal_path = subtree.get_path(focal_clade)
    focal_parent = subtree if len(focal_path) == 1 else focal_path[-2]
    ax.plot([depths[id(focal_parent)], depths[id(focal_clade)]],
            [yplot(focal_clade), yplot(focal_clade)], color=BLUE, lw=1.25, zorder=3)

    def recolor_focal(clade):
        x = depths[id(clade)]
        if clade.clades:
            ys = [yplot(c) for c in clade.clades]
            ax.plot([x, x], [min(ys), max(ys)], color=BLUE, lw=1.05, zorder=2)
            for child in clade.clades:
                xc = depths[id(child)]
                yc = yplot(child)
                ax.plot([x, xc], [yc, yc], color=BLUE, lw=1.05, zorder=2)
                recolor_focal(child)
    recolor_focal(focal_clade)

    outside_term = next(t for t in terminals if t.name == outside_tip)
    outside_path = subtree.get_path(outside_term)
    outside_parent = subtree if len(outside_path) == 1 else outside_path[-2]
    # Only the terminal edge carrying the separate reconstructed event is orange.
    ax.plot([depths[id(outside_parent)], depths[id(outside_term)]],
            [yplot(outside_term), yplot(outside_term)], color=ORANGE, lw=1.25, zorder=3)

    # Tip markers, taxon labels, and site-state column.
    # IMPORTANT: label columns use axes-fraction x coordinates with data y coordinates.
    # This decouples text placement from phylogram branch-length units and prevents
    # overlaps when font metrics or rendering backends change.
    label_transform = ax.get_yaxis_transform()
    x_name_ax = 0.605
    x_state_ax = 0.810
    x_bracket_ax = 0.845
    x_bracket_label_ax = 0.868

    for term in terminals:
        y = yplot(term)
        x = depths[id(term)]
        state = states[term.name]
        if term.name in focal_four:
            face = edge = text_color = BLUE
            state_color = BLUE
            weight = "bold"
        elif term.name == outside_tip:
            face = edge = text_color = ORANGE
            state_color = ORANGE
            weight = "bold"
        else:
            face, edge, text_color, weight = "white", INK, INK, "normal"
            state_color = GREY
        ax.scatter([x], [y], s=30, facecolor=face, edgecolor=edge, linewidth=0.75, zorder=4)
        ax.text(x_name_ax, y, term.name, transform=label_transform,
                ha="left", va="center", fontsize=5.80,
                color=text_color, fontweight=weight, clip_on=False)
        ax.text(x_state_ax, y, state, transform=label_transform,
                ha="center", va="center", fontsize=6.35,
                color=state_color, fontweight=weight, clip_on=False)

    ax.text(x_state_ax, 0.895, "site state", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=5.95, color=GREY)

    # Focal-clade bracket, kept in its own column to the right of site states.
    focal_terms = [t for t in terminals if t.name in focal_four]
    top = max(yplot(t) for t in focal_terms)
    bottom = min(yplot(t) for t in focal_terms)
    ax.plot([x_bracket_ax, x_bracket_ax], [bottom, top], transform=label_transform,
            color=BLUE, lw=0.75, clip_on=False)
    ax.plot([x_bracket_ax - 0.018, x_bracket_ax], [top, top], transform=label_transform,
            color=BLUE, lw=0.75, clip_on=False)
    ax.plot([x_bracket_ax - 0.018, x_bracket_ax], [bottom, bottom], transform=label_transform,
            color=BLUE, lw=0.75, clip_on=False)
    ax.text(x_bracket_label_ax, (top + bottom) / 2, "focal clade\n(4 descendants)",
            transform=label_transform, ha="left", va="center", fontsize=5.00,
            color=BLUE, fontweight="bold", linespacing=1.0, clip_on=False)

    # Compact substitution annotations.
    fx = (depths[id(focal_parent)] + depths[id(focal_clade)]) / 2
    fy = yplot(focal_clade)
    ax.annotate("focal T→G", xy=(fx, fy), xytext=(maxdepth * 0.28, n + 0.42),
                ha="center", va="bottom", fontsize=6.6, color=BLUE, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=0.7, shrinkA=2, shrinkB=2))

    ox = (depths[id(outside_parent)] + depths[id(outside_term)]) / 2
    oy = yplot(outside_term)
    ax.annotate("terminal T→G", xy=(ox, oy), xytext=(maxdepth * 0.80, n + 1.12),
                ha="left", va="bottom", fontsize=6.6, color=ORANGE, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=0.7, shrinkA=2, shrinkB=2))

    # Scale and compact legend on separate baselines.
    scale = 0.01
    sx0, sy0 = 0.0, -0.55
    ax.plot([sx0, sx0 + scale], [sy0, sy0], color=INK, lw=0.7)
    ax.plot([sx0, sx0], [sy0 - 0.08, sy0 + 0.08], color=INK, lw=0.7)
    ax.plot([sx0 + scale, sx0 + scale], [sy0 - 0.08, sy0 + 0.08], color=INK, lw=0.7)
    ax.text(sx0 + scale / 2, sy0 - 0.22, "0.01 substitutions/site",
            ha="center", va="top", fontsize=5.9, color=GREY)

    # Legend uses axes coordinates so text widths cannot collide as branch-length
    # scaling changes. Each item has its own fixed horizontal slot.
    legend_y = 0.018
    legend_items = [
        (0.035, "white", INK, "T", INK),
        (0.335, BLUE, BLUE, "focal-clade G", BLUE),
        (0.720, ORANGE, ORANGE, "outside G", ORANGE),
    ]
    for xdot, face, edge, label, color in legend_items:
        ax.scatter([xdot], [legend_y], transform=ax.transAxes, s=24,
                   facecolor=face, edgecolor=edge, linewidth=0.7,
                   zorder=4, clip_on=False)
        ax.text(xdot + 0.025, legend_y, label, transform=ax.transAxes,
                ha="left", va="center", fontsize=5.9, color=color, clip_on=False)

    ax.set_xlim(-0.001, maxdepth + 0.022)
    ax.set_ylim(-1.9, n + 1.55)
    ax.axis("off")


def draw_panel_b(ax, root: Path) -> None:
    ax.axis("off")
    panel_letter(ax, "B")
    ax.text(0.50, 1.005, "Clade A recurrent-state example", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=9.0, fontweight="bold", color=INK)
    ax.text(0.50, 0.955, "AP009378.1_4301132", transform=ax.transAxes,
            ha="center", va="top", fontsize=6.8, color=GREY)

    _, states, subtree, focal_four, focal_clade, outside_tip = load_clade_a_example(root)
    tree_ax = ax.inset_axes([0.02, 0.03, 0.96, 0.88])
    draw_phylogram(tree_ax, subtree, states, focal_clade, focal_four, outside_tip)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_rgb_tiff(src: Path, dst: Path) -> None:
    with Image.open(src) as image:
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(dst, compression="tiff_lzw", dpi=image.info.get("dpi", (1000, 1000)))


def write_docs(outdir: Path, checksums: dict[str, str]) -> None:
    readme = f"""# Figure 3 - clade exclusivity and focal-edge substitution were not equivalent in empirical phylogenies

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
| `Figure_3.pdf` | Vector production/submission figure. | `{checksums['Figure_3.pdf']}` |
| `Figure_3_editable.svg` | Editable vector source. | `{checksums['Figure_3_editable.svg']}` |
| `Figure_3_preview_600dpi.png` | README/inspection preview. | `{checksums['Figure_3_preview_600dpi.png']}` |
| `Figure_3_1000dpi.tiff` | 1000-dpi LZW line-art TIFF. | `{checksums['Figure_3_1000dpi.tiff']}` |
| `Figure_3_1000dpi_RGB.tiff` | Explicit RGB 1000-dpi LZW TIFF. | `{checksums['Figure_3_1000dpi_RGB.tiff']}` |

## Artwork preparation choices

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

Arial is requested first in the Matplotlib font stack. Arial is not installed in the automated rendering environment, so the locked render uses **Arimo**, an Arial-compatible metric substitute. The SVG keeps text editable so the font can be substituted later if required.
"""
    (outdir / "README.md").write_text(readme)

    walkthrough = """# Figure 3 code walkthrough

`make_figure_3.py` reads the committed experiment 06 tables and the committed Clade A tree/alignment, then renders both figure panels with Matplotlib.

Panel A uses a vertical summary layout to avoid narrow-box text wrapping at final print size. The 95.56%/4.44% discordance bar is proportional; the small 4.44% category is labelled externally rather than visually enlarged.

Panel B uses the actual 14-tip pruned Clade A phylogram containing the five observed G states at `AP009378.1_4301132`. Horizontal distances are cumulative branch lengths from the supplied Newick tree. The four-descendant focal clade is blue, the independent outside terminal G occurrence is orange, and ancestral T tips remain open black circles.
"""
    (outdir / "CODE_WALKTHROUGH.md").write_text(walkthrough)

    (outdir / "DIRECTORY_TREE.txt").write_text("""BRANCHSNV validation repository
|
`-- manuscript/
    `-- figure_3/
        |-- CODE_WALKTHROUGH.md
        |-- DIRECTORY_TREE.txt
        |-- Figure_3.pdf
        |-- Figure_3_1000dpi.tiff
        |-- Figure_3_1000dpi_RGB.tiff
        |-- Figure_3_editable.svg
        |-- Figure_3_preview_600dpi.png
        |-- README.md
        |-- make_figure_3.py
        `-- requirements.txt
""")

    (outdir / "requirements.txt").write_text("""matplotlib==3.10.8
pandas==2.2.3
Pillow==12.3.0
biopython==1.86
""")


def build(outdir: Path) -> None:
    root = repo_root()
    s = load_summary(root)

    fig = plt.figure(figsize=(FIG_W, FIG_H))
    grid = fig.add_gridspec(
        1, 2, width_ratios=[0.95, 1.25],
        left=0.055, right=0.985, top=0.955, bottom=0.065, wspace=0.10,
    )
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])
    draw_panel_a(ax_a, s)
    draw_panel_b(ax_b, root)

    # restrained separator only; no boxed panel frames
    fig.lines.append(Line2D([0.435, 0.435], [0.075, 0.945], transform=fig.transFigure,
                            color=LIGHT_GREY, lw=0.65))

    pdf = outdir / "Figure_3.pdf"
    svg = outdir / "Figure_3_editable.svg"
    png = outdir / "Figure_3_preview_600dpi.png"
    tiff = outdir / "Figure_3_1000dpi.tiff"
    rgb_tiff = outdir / "Figure_3_1000dpi_RGB.tiff"

    fig.savefig(pdf, dpi=600)
    fig.savefig(svg, dpi=600)
    fig.savefig(png, dpi=600)
    fig.savefig(tiff, dpi=1000, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    save_rgb_tiff(tiff, rgb_tiff)

    checksums = {p.name: sha256(p) for p in (pdf, svg, png, tiff, rgb_tiff)}
    write_docs(outdir, checksums)


if __name__ == "__main__":
    build(Path(__file__).resolve().parent)
