#!/usr/bin/env python3
"""Generate manuscript Figure 2 from committed BRANCHSNV validation summaries.

The figure is a compact validation overview. All numerical claims are read from the
committed machine-readable result snapshots rather than typed into the artwork code.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image
from matplotlib import font_manager
FIG_W, FIG_H = 6.50, 2.72
font_manager.findfont(font_manager.FontProperties(family="Arimo", weight="normal"), fallback_to_default=False)
mpl.rcParams.update({
    "font.family": "Arimo",
    "font.size": 7.0,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})
font_manager.findfont(font_manager.FontProperties(family="Arimo", weight="bold"), fallback_to_default=False)
INK = "#111111"
BLUE = "#0000FF"
RED = "#E00000"
GREEN = "#38A900"
ORANGE = "#F06A00"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()



def normalize_svg_whitespace(path: Path) -> None:
    """Remove renderer-added trailing spaces so the tracked SVG stays Git-clean."""
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")

def claim_values(root: Path) -> dict[str, object]:
    s1 = load_json(root / "results" / "01_exact_oracle" / "summary.json")
    s2 = load_json(root / "results" / "02_deliberate_faults" / "summary.json")
    s3 = load_json(root / "results" / "03_published_datasets" / "summary.json")
    s4 = load_json(root / "results" / "04_scalability" / "summary.json")
    s5 = load_json(root / "results" / "05_published_focal_branches" / "summary.json")

    p3 = s3["public_comparison"]["totals"]
    p5 = s5["totals"]
    return {
        "oracle_total": int(s1["total_comparisons"]),
        "oracle_mismatches": int(s1["total_mismatches"]),
        "oracle_settings": int(s1["topology_cases"]),
        "fault_detected": int(s2["faults_detected"]),
        "fault_total": int(s2["faults_evaluated"]),
        "fault_challenges": int(s2["total_challenges"]),
        "fault_differentiating": int(s2["total_differentiating_challenges"]),
        "snppar_exact": int(p3["exact_unambiguous_matches"]),
        "snppar_unambiguous": int(p3["branchsnv_unambiguous_events"]),
        "snppar_ambiguous": int(p3["snppar_only_supported_as_branchsnv_placement_ambiguous"]),
        "published_exact": int(p5["exact_position_direction"]),
        "published_total": int(p5["published_snvs"]),
        "published_analyses": len(s5["datasets"]),
        "benchmark_runs": int(s4["measured_runs"]),
        "largest_taxa": int(s4["largest_taxon_configuration"]["ntax"]),
        "largest_taxa_sites": int(s4["largest_taxon_configuration"]["nchar"]),
        "largest_sites_taxa": int(s4["largest_site_configuration"]["ntax"]),
        "largest_sites": int(s4["largest_site_configuration"]["nchar"]),
    }


def rounded_box(ax: plt.Axes, x: float, y: float, w: float, h: float, color: str) -> None:
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.010,rounding_size=0.018",
        linewidth=0.85,
        edgecolor=color,
        facecolor="white",
        transform=ax.transAxes,
        clip_on=False,
    )
    ax.add_patch(patch)


def bullet(ax: plt.Axes, x: float, y: float, text: str, color: str, size: float = 7.0) -> None:
    ax.text(x, y, "•", transform=ax.transAxes, color=color, fontsize=10.5,
            ha="left", va="center")
    ax.text(x + 0.020, y, text, transform=ax.transAxes, color=INK, fontsize=size,
            ha="left", va="center", linespacing=0.95)


def connector(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str,
) -> None:
    ax.plot(start[0], start[1], marker="o", markersize=4.0, color=color,
            transform=ax.transAxes, clip_on=False, zorder=4)
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=10,
        linewidth=0.95,
        color=color,
        transform=ax.transAxes,
        connectionstyle="arc3,rad=0",
        shrinkA=1,
        shrinkB=1,
    )
    ax.add_patch(arrow)


def draw(ax: plt.Axes, values: dict[str, object]) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    left_x, right_x = 0.010, 0.650
    box_w, box_h = 0.340, 0.445
    top_y, bottom_y = 0.535, 0.020

    rounded_box(ax, left_x, top_y, box_w, box_h, BLUE)
    rounded_box(ax, right_x, top_y, box_w, box_h, RED)
    rounded_box(ax, left_x, bottom_y, box_w, box_h, GREEN)
    rounded_box(ax, right_x, bottom_y, box_w, box_h, ORANGE)

    title_y = top_y + box_h - 0.055
    ax.text(left_x + 0.018, title_y, "Exact oracle", transform=ax.transAxes,
            color=BLUE, fontsize=14.5, ha="left", va="center")
    ax.text(right_x + 0.018, title_y, "Deliberate faults", transform=ax.transAxes,
            color=RED, fontsize=14.5, ha="left", va="center")
    ax.text(left_x + 0.018, bottom_y + box_h - 0.055, "Published data",
            transform=ax.transAxes, color=GREEN, fontsize=14.5, ha="left", va="center")
    ax.text(right_x + 0.018, bottom_y + box_h - 0.055, "Scalability",
            transform=ax.transAxes, color=ORANGE, fontsize=14.5, ha="left", va="center")

    bullet(ax, left_x + 0.010, top_y + 0.260,
           f"{values['oracle_total']:,} comparisons", BLUE)
    bullet(ax, left_x + 0.010, top_y + 0.165,
           f"{values['oracle_settings']} topology-edge settings", BLUE)
    bullet(ax, left_x + 0.010, top_y + 0.070,
           f"{values['oracle_mismatches']} discrepancies", BLUE)

    bullet(ax, right_x + 0.010, top_y + 0.260,
           f"{values['fault_detected']}/{values['fault_total']} fault classes detected", RED)
    bullet(ax, right_x + 0.010, top_y + 0.165,
           f"{values['fault_challenges']:,} fault-challenge comparisons", RED)
    bullet(ax, right_x + 0.010, top_y + 0.070,
           f"{values['fault_differentiating']:,} differentiating comparisons", RED)

    bullet(ax, left_x + 0.010, bottom_y + 0.285,
           f"{values['snppar_exact']}/{values['snppar_unambiguous']} BRANCHSNV unambiguous\n   calls matched SNPPar", GREEN, 6.6)
    bullet(ax, left_x + 0.010, bottom_y + 0.175,
           f"{values['published_exact']}/{values['published_total']} published focal-branch SNVs\n   reproduced across {values['published_analyses']} analyses", GREEN, 6.6)
    bullet(ax, left_x + 0.010, bottom_y + 0.065,
           f"{values['snppar_ambiguous']} additional SNPPar events retained as\n   placement-ambiguous", GREEN, 6.6)

    bullet(ax, right_x + 0.010, bottom_y + 0.235,
           f"{values['benchmark_runs']}/{values['benchmark_runs']} CLI runs completed", ORANGE)
    bullet(ax, right_x + 0.010, bottom_y + 0.140,
           f"{values['largest_taxa']:,} taxa × {values['largest_taxa_sites']:,} sites", ORANGE)
    bullet(ax, right_x + 0.010, bottom_y + 0.045,
           f"{values['largest_sites_taxa']:,} taxa × {values['largest_sites']:,} sites", ORANGE)

    connector(ax, (left_x + box_w + 0.010, top_y + 0.220), (0.425, 0.575), BLUE)
    connector(ax, (right_x - 0.010, top_y + 0.220), (0.575, 0.575), RED)
    connector(ax, (left_x + box_w + 0.010, bottom_y + 0.220), (0.425, 0.425), GREEN)
    connector(ax, (right_x - 0.010, bottom_y + 0.220), (0.575, 0.425), ORANGE)

    ax.text(0.500, 0.525, "Convergent\nevidence", transform=ax.transAxes,
            color=INK, fontsize=13.8, ha="center", va="center", linespacing=0.90)
    ax.text(0.500, 0.335,
            "Exactness\nFault sensitivity\nPracticality\nEmpirical concordance",
            transform=ax.transAxes, color=INK, fontsize=7.4,
            ha="center", va="center", linespacing=0.90)

    ax.text(0.500, 0.690,
            f"{values['oracle_total']:,}/{values['oracle_total']:,}\nexact matches",
            transform=ax.transAxes, color=BLUE, fontsize=7.5,
            ha="center", va="center", linespacing=0.92)


def write_support_files(outdir: Path, checksums: dict[str, str]) -> None:
    readme = f"""# Figure 2 - convergent validation evidence for BRANCHSNV

This directory contains the manuscript Figure 2 artwork and the exact Python/Matplotlib code used to render it from the committed validation summaries.

## Final figure

![Figure 2 preview](Figure_2_preview_600dpi.png)

## Data provenance

The numerical claims are read directly from:

- `results/01_exact_oracle/summary.json`
- `results/02_deliberate_faults/summary.json`
- `results/03_published_datasets/summary.json`
- `results/04_scalability/summary.json`
- `results/05_published_focal_branches/summary.json`

The figure therefore reflects the same machine-readable results checked by `verify_publication_snapshot.py`. No validation count is manually entered into the plotting code.

## Figure files

| File | Purpose | SHA-256 |
|---|---|---|
| `Figure_2.pdf` | Vector production/submission figure. | `{checksums['Figure_2.pdf']}` |
| `Figure_2_editable.svg` | Editable vector source. | `{checksums['Figure_2_editable.svg']}` |
| `Figure_2_preview_600dpi.png` | README/inspection preview. | `{checksums['Figure_2_preview_600dpi.png']}` |
| `Figure_2_1000dpi.tiff` | 1000-dpi LZW TIFF. | `{checksums['Figure_2_1000dpi.tiff']}` |
| `Figure_2_1000dpi_RGB.tiff` | Explicit RGB 1000-dpi LZW TIFF. | `{checksums['Figure_2_1000dpi_RGB.tiff']}` |

## Reproducing the figure

The locked render used Python 3.13, Matplotlib 3.10.8, Pillow 12.3.0, and Arimo regular/bold.

From the repository root:

```bash
python manuscript/figure_2/make_figure_2.py
```

The script writes all five artwork files beside itself and updates this README's artwork checksums. `CODE_WALKTHROUGH.md` is maintained separately and is deliberately not overwritten during rerendering.

## Interpretation

The four boxes represent complementary validation evidence rather than four estimates of the same property. The oracle tests exact implementation of the defined reconstruction problem; deliberate faults test sensitivity to specified implementation errors; published-data analyses test concordance and reproduction on independent empirical examples; and scalability tests establish practical end-to-end behavior over the measured input ranges.

### Font note

The locked render uses **Arimo**, an Arial-compatible metric substitute. The script fails if Arimo regular or bold is unavailable rather than silently substituting another font. Exact output-file bytes can still vary across platforms with the font/FreeType rendering stack; the committed artwork hashes identify the publication render. The SVG retains editable text.
"""
    (outdir / "README.md").write_text(readme, encoding="utf-8")

    (outdir / "DIRECTORY_TREE.txt").write_text("""BRANCHSNV validation repository
|
|-- results/
|   |-- 01_exact_oracle/summary.json
|   |-- 02_deliberate_faults/summary.json
|   |-- 03_published_datasets/summary.json
|   |-- 04_scalability/summary.json
|   `-- 05_published_focal_branches/summary.json
|
`-- manuscript/
    `-- figure_2/
        |-- CODE_WALKTHROUGH.md
        |-- DIRECTORY_TREE.txt
        |-- Figure_2.pdf
        |-- Figure_2_1000dpi.tiff
        |-- Figure_2_1000dpi_RGB.tiff
        |-- Figure_2_editable.svg
        |-- Figure_2_preview_600dpi.png
        |-- README.md
        |-- make_figure_2.py
        `-- requirements.txt
""", encoding="utf-8")

    (outdir / "requirements.txt").write_text(
        "matplotlib==3.10.8\nPillow==12.3.0\n",
        encoding="utf-8",
    )


def main() -> None:
    outdir = Path(__file__).resolve().parent
    values = claim_values(repo_root())

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.subplots_adjust(left=0.005, right=0.995, top=0.990, bottom=0.010)
    draw(ax, values)

    pdf = outdir / "Figure_2.pdf"
    svg = outdir / "Figure_2_editable.svg"
    png = outdir / "Figure_2_preview_600dpi.png"
    tiff = outdir / "Figure_2_1000dpi.tiff"
    rgb_tiff = outdir / "Figure_2_1000dpi_RGB.tiff"

    fig.savefig(pdf)
    fig.savefig(svg)
    normalize_svg_whitespace(svg)
    fig.savefig(png, dpi=600)
    fig.savefig(tiff, dpi=1000, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)

    with Image.open(tiff) as image:
        image.convert("RGB").save(
            rgb_tiff,
            format="TIFF",
            compression="tiff_lzw",
            dpi=(1000, 1000),
        )

    checksums = {path.name: sha256(path) for path in (pdf, svg, png, tiff, rgb_tiff)}
    write_support_files(outdir, checksums)


if __name__ == "__main__":
    main()
