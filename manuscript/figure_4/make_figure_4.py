#!/usr/bin/env python3
"""Generate manuscript Figure 4 from committed BRANCHSNV scalability runs.

The benchmark experiment itself lives in experiments/04_scalability/. This script
only turns the committed stable-release measurements in
release_validation/v0.1.0/results/04_scalability/raw_runs.tsv into the publication figure.
It deliberately does not regenerate benchmark inputs or rerun BRANCHSNV.
"""

from __future__ import annotations

import csv
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image

# -----------------------------------------------------------------------------
# Locked publication style
# -----------------------------------------------------------------------------
FIG_W, FIG_H = 6.50, 7.10

mpl.rcParams.update({
    "font.family": "Arimo",
    "font.size": 7.0,
    "axes.titlesize": 7.8,
    "axes.labelsize": 7.2,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

INK = "#222222"
GREY = "#777777"
LIGHT = "#E5E5E5"
FIT_GREY = "#9A9A9A"
BLUE = "#0072B2"
ORANGE = "#D55E00"

TAXA_LEVELS = [50, 100, 250, 500, 1000, 2000]
SITE_LEVELS = [1000, 5000, 10000, 25000, 50000, 100000]
MODE_LEVELS = ["fixed-exclusive", "parsimony", "both"]


# -----------------------------------------------------------------------------
# Input parsing and validation
# -----------------------------------------------------------------------------
def normalize_header(value: str) -> str:
    """Normalize a TSV column name so small naming differences are tolerated."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def first_present(row: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    """Return the first non-empty value present under any accepted column alias."""
    for alias in aliases:
        if alias in row and str(row[alias]).strip() != "":
            return str(row[alias]).strip()
    return None


def as_int(value: str | None, label: str) -> int:
    if value is None:
        raise ValueError(f"Missing required value: {label}")
    return int(float(value))


def as_float(value: str | None, label: str) -> float:
    if value is None:
        raise ValueError(f"Missing required value: {label}")
    return float(value)


def read_raw_runs(path: Path) -> list[dict[str, object]]:
    """Read the committed run-level benchmark table using conservative aliases."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"No TSV header found in {path}")

        normalized = [normalize_header(name) for name in reader.fieldnames]
        rows: list[dict[str, object]] = []

        for original in reader:
            row = {
                normalized[i]: (original.get(reader.fieldnames[i]) or "")
                for i in range(len(reader.fieldnames))
            }

            dataset = first_present(row, ("dataset_id", "dataset_identifier", "dataset"))
            taxa = first_present(row, ("taxa", "number_of_taxa", "ntax"))
            sites = first_present(row, ("sites", "number_of_sites", "nchar"))
            mode = first_present(row, ("mode", "analysis_mode"))
            replicate = first_present(row, ("replicate", "rep", "run"))
            wall = first_present(
                row,
                ("wall_time_s", "wall_seconds", "wall_time", "elapsed_seconds", "elapsed_s"),
            )
            rss_mib = first_present(
                row,
                ("peak_rss_mib", "peak_resident_memory_mib", "peak_resident_set_size_mib"),
            )
            rss_kib = first_present(
                row,
                ("peak_rss_kib", "peak_resident_memory_kib", "maximum_resident_set_size_kib"),
            )

            if not all((dataset, taxa, sites, mode, wall)):
                continue
            if rss_mib is None and rss_kib is None:
                raise ValueError("Raw benchmark table lacks peak-RSS MiB or KiB values")

            rows.append({
                "dataset_id": dataset,
                "taxa": as_int(taxa, "taxa"),
                "sites": as_int(sites, "sites"),
                "mode": mode,
                "replicate": as_int(replicate or "1", "replicate"),
                "wall_s": as_float(wall, "wall time"),
                "rss_mib": as_float(rss_mib, "peak RSS MiB")
                if rss_mib is not None
                else as_float(rss_kib, "peak RSS KiB") / 1024.0,
            })

    if not rows:
        raise ValueError(f"No benchmark rows could be parsed from {path}")
    return rows


def group_values(
    rows: list[dict[str, object]],
    *,
    x_field: str,
    levels: list[object],
    metric: str,
    fixed: dict[str, object],
) -> list[list[float]]:
    """Collect exactly three replicate measurements for every requested level."""
    grouped: dict[object, list[tuple[int, float]]] = defaultdict(list)
    for row in rows:
        if all(row[key] == value for key, value in fixed.items()):
            grouped[row[x_field]].append((int(row["replicate"]), float(row[metric])))

    result: list[list[float]] = []
    for level in levels:
        reps = sorted(grouped.get(level, []), key=lambda item: item[0])
        if len(reps) != 3:
            raise ValueError(
                f"Expected 3 measured runs for {x_field}={level} with {fixed}; found {len(reps)}"
            )
        result.append([value for _, value in reps])
    return result


# -----------------------------------------------------------------------------
# Descriptive summaries and fits
# -----------------------------------------------------------------------------
def summaries(replicates: list[list[float]]) -> tuple[list[float], list[float], list[float]]:
    medians = [statistics.median(values) for values in replicates]
    minima = [min(values) for values in replicates]
    maxima = [max(values) for values in replicates]
    return medians, minima, maxima


def linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Ordinary least-squares y = slope*x + intercept, plus R-squared."""
    xbar = statistics.mean(xs)
    ybar = statistics.mean(ys)
    ssx = sum((x - xbar) ** 2 for x in xs)
    if ssx == 0:
        raise ValueError("Cannot fit a line when all x values are identical")
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / ssx
    intercept = ybar - slope * xbar
    fitted = [slope * x + intercept for x in xs]
    sst = sum((y - ybar) ** 2 for y in ys)
    sse = sum((y - fit) ** 2 for y, fit in zip(ys, fitted))
    r2 = 1.0 - sse / sst if sst else 1.0
    return slope, intercept, r2


def format_r2(r2: float) -> str:
    if r2 >= 0.9999:
        return f"{r2:.5f}"
    return f"{r2:.4f}"


# -----------------------------------------------------------------------------
# Plotting helpers
# -----------------------------------------------------------------------------
def style_axis(ax: plt.Axes) -> None:
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=LIGHT, linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#999999")
    ax.spines["bottom"].set_color("#999999")
    ax.spines["left"].set_linewidth(0.65)
    ax.spines["bottom"].set_linewidth(0.65)
    ax.tick_params(axis="both", colors=INK, width=0.55, length=2.8, pad=2)


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.14, 1.105, label, transform=ax.transAxes, fontsize=9.3,
            fontweight="bold", color=INK, ha="left", va="top")


def jitter_for(levels: list[float]) -> list[float]:
    diffs = [b - a for a, b in zip(levels[:-1], levels[1:]) if b > a]
    spacing = min(diffs) if diffs else 1.0
    return [-0.07 * spacing, 0.0, 0.07 * spacing]


def draw_scaling_panel(
    ax: plt.Axes,
    xs: list[float],
    reps: list[list[float]],
    *,
    color: str,
    title: str,
    xlabel: str,
    ylabel: str,
    label: str,
) -> tuple[float, float, float]:
    style_axis(ax)
    panel_label(ax, label)
    ax.set_title(title, pad=5, color=INK)
    ax.set_xlabel(xlabel, color=INK, labelpad=3)
    ax.set_ylabel(ylabel, color=INK, labelpad=3)

    medians, minima, maxima = summaries(reps)
    jitter = jitter_for(xs)

    for x, values, lo, hi, med in zip(xs, reps, minima, maxima, medians):
        ax.vlines(x, lo, hi, color=color, linewidth=0.75, alpha=0.70, zorder=2)
        for offset, value in zip(jitter, values):
            ax.scatter(x + offset, value, s=16, facecolor=color, edgecolor=color,
                       linewidth=0.55, alpha=0.28, zorder=3)
        ax.scatter(x, med, s=24, facecolor=color, edgecolor="white",
                   linewidth=0.55, zorder=4)

    ax.plot(xs, medians, color=color, linewidth=1.25, zorder=3)
    slope, intercept, r2 = linear_fit(xs, medians)
    fit_x = [min(xs), max(xs)]
    fit_y = [slope * x + intercept for x in fit_x]
    ax.plot(fit_x, fit_y, color=FIT_GREY, linewidth=0.85,
            linestyle=(0, (3, 3)), zorder=1)

    ax.set_xticks([x for x in xs if x not in ({100} if max(xs) <= 2000 else {5000})])
    ax.set_xticklabels([f"{int(x):,}" for x in xs if x not in ({100} if max(xs) <= 2000 else {5000})], rotation=45, ha="right")
    ax.tick_params(axis="x", labelsize=5.8)
    ax.margins(x=0.05, y=0.08)
    ax.text(0.98, 0.035, rf"$R^2$ = {format_r2(r2)}", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=6.6, color=INK)
    return slope, intercept, r2


def draw_mode_panel(
    ax: plt.Axes,
    reps: list[list[float]],
    *,
    color: str,
    ylabel: str,
    label: str,
) -> None:
    style_axis(ax)
    panel_label(ax, label)
    ax.set_title("Analysis mode", pad=5, color=INK)
    ax.set_xlabel("Analysis mode", color=INK, labelpad=3)
    ax.set_ylabel(ylabel, color=INK, labelpad=3)

    medians, minima, maxima = summaries(reps)
    xpos = list(range(len(MODE_LEVELS)))
    jitter = [-0.075, 0.0, 0.075]

    for x, values, lo, hi, med in zip(xpos, reps, minima, maxima, medians):
        ax.vlines(x, lo, hi, color=color, linewidth=0.75, alpha=0.75, zorder=2)
        for offset, value in zip(jitter, values):
            ax.scatter(x + offset, value, s=16, facecolor=color, edgecolor=color,
                       linewidth=0.55, alpha=0.28, zorder=3)
        ax.scatter(x, med, s=24, facecolor=color, edgecolor="white",
                   linewidth=0.55, zorder=4)

    ax.set_xticks(xpos)
    ax.set_xticklabels(MODE_LEVELS)
    ax.margins(x=0.10, y=0.12)


# -----------------------------------------------------------------------------
# Main figure assembly and export
# -----------------------------------------------------------------------------
def main() -> None:
    figure_dir = Path(__file__).resolve().parent
    repo_root = figure_dir.parents[1]
    raw_runs = repo_root / "release_validation" / "v0.1.0" / "results" / "04_scalability" / "raw_runs.tsv"

    if not raw_runs.exists():
        raise FileNotFoundError(
            f"Expected committed benchmark measurements at {raw_runs}. "
            "Run this script from its manuscript/figure_4 location inside the validation repository."
        )

    rows = read_raw_runs(raw_runs)

    taxon_wall = group_values(
        rows, x_field="taxa", levels=TAXA_LEVELS, metric="wall_s",
        fixed={"sites": 10000, "mode": "both"},
    )
    taxon_mem = group_values(
        rows, x_field="taxa", levels=TAXA_LEVELS, metric="rss_mib",
        fixed={"sites": 10000, "mode": "both"},
    )
    site_wall = group_values(
        rows, x_field="sites", levels=SITE_LEVELS, metric="wall_s",
        fixed={"taxa": 250, "mode": "both"},
    )
    site_mem = group_values(
        rows, x_field="sites", levels=SITE_LEVELS, metric="rss_mib",
        fixed={"taxa": 250, "mode": "both"},
    )
    mode_wall = group_values(
        rows, x_field="mode", levels=MODE_LEVELS, metric="wall_s",
        fixed={"taxa": 500, "sites": 10000},
    )
    mode_mem = group_values(
        rows, x_field="mode", levels=MODE_LEVELS, metric="rss_mib",
        fixed={"taxa": 500, "sites": 10000},
    )

    fig, axes = plt.subplots(3, 2, figsize=(FIG_W, FIG_H))
    fig.subplots_adjust(left=0.105, right=0.985, bottom=0.065, top=0.975,
                        wspace=0.30, hspace=0.43)

    fits = []
    fits.append(draw_scaling_panel(
        axes[0, 0], TAXA_LEVELS, taxon_wall, color=BLUE,
        title="Taxon scaling", xlabel="Number of taxa", ylabel="Wall time (s)", label="A",
    ))
    fits.append(draw_scaling_panel(
        axes[0, 1], TAXA_LEVELS, taxon_mem, color=ORANGE,
        title="Taxon scaling", xlabel="Number of taxa",
        ylabel="Peak resident memory (MiB)", label="B",
    ))
    fits.append(draw_scaling_panel(
        axes[1, 0], SITE_LEVELS, site_wall, color=BLUE,
        title="Site scaling", xlabel="Number of sites", ylabel="Wall time (s)", label="C",
    ))
    fits.append(draw_scaling_panel(
        axes[1, 1], SITE_LEVELS, site_mem, color=ORANGE,
        title="Site scaling", xlabel="Number of sites",
        ylabel="Peak resident memory (MiB)", label="D",
    ))
    draw_mode_panel(
        axes[2, 0], mode_wall, color=BLUE, ylabel="Wall time (s)", label="E",
    )
    draw_mode_panel(
        axes[2, 1], mode_mem, color=ORANGE,
        ylabel="Peak resident memory (MiB)", label="F",
    )

    pdf = figure_dir / "Figure_4.pdf"
    svg = figure_dir / "Figure_4_editable.svg"
    png = figure_dir / "Figure_4_preview_600dpi.png"
    tif = figure_dir / "Figure_4_1000dpi.tiff"
    rgb_tif = figure_dir / "Figure_4_1000dpi_RGB.tiff"

    fig.savefig(pdf)
    fig.savefig(svg)
    fig.savefig(png, dpi=600)
    fig.savefig(tif, dpi=1000, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)

    with Image.open(tif) as image:
        image.convert("RGB").save(
            rgb_tif,
            format="TIFF",
            compression="tiff_lzw",
            dpi=(1000, 1000),
        )

    print(f"Figure 4 generated from: {raw_runs}")
    for name, (slope, intercept, r2) in zip(
        ["runtime_taxa", "memory_taxa", "runtime_sites", "memory_sites"], fits
    ):
        print(f"{name}: slope={slope:.12g}; intercept={intercept:.12g}; R2={r2:.9f}")


if __name__ == "__main__":
    main()
