#!/usr/bin/env python3
"""Generate publication-oriented scalability figures from benchmark_summary.tsv."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def save_line(
    rows: list[dict[str, str]],
    x_key: str,
    y_key: str,
    y_min_key: str,
    y_max_key: str,
    xlabel: str,
    ylabel: str,
    output_stem: Path,
) -> None:
    x = [int(row[x_key]) for row in rows]
    y = [float(row[y_key]) for row in rows]
    lower = [value - float(row[y_min_key]) for value, row in zip(y, rows)]
    upper = [float(row[y_max_key]) - value for value, row in zip(y, rows)]
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.errorbar(x, y, yerr=[lower, upper], marker="o", capsize=3)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_stem.with_suffix(".png"), dpi=300)
    fig.savefig(output_stem.with_suffix(".svg"))
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_rows(args.summary)
    both = [row for row in rows if row["mode"] == "both"]

    taxon_rows = sorted(
        [row for row in both if int(row["nchar"]) == 10_000],
        key=lambda row: int(row["ntax"]),
    )
    site_rows = sorted(
        [row for row in both if int(row["ntax"]) == 250],
        key=lambda row: int(row["nchar"]),
    )
    save_line(
        taxon_rows,
        "ntax",
        "wall_median_seconds",
        "wall_min_seconds",
        "wall_max_seconds",
        "Number of taxa (10,000 sites)",
        "Wall time (s), median and range",
        args.output_dir / "runtime_by_taxa",
    )
    save_line(
        site_rows,
        "nchar",
        "wall_median_seconds",
        "wall_min_seconds",
        "wall_max_seconds",
        "Number of sites (250 taxa)",
        "Wall time (s), median and range",
        args.output_dir / "runtime_by_sites",
    )
    save_line(
        taxon_rows,
        "ntax",
        "peak_rss_median_mib",
        "peak_rss_min_mib",
        "peak_rss_max_mib",
        "Number of taxa (10,000 sites)",
        "Peak RSS (MiB), median and range",
        args.output_dir / "memory_by_taxa",
    )
    save_line(
        site_rows,
        "nchar",
        "peak_rss_median_mib",
        "peak_rss_min_mib",
        "peak_rss_max_mib",
        "Number of sites (250 taxa)",
        "Peak RSS (MiB), median and range",
        args.output_dir / "memory_by_sites",
    )

    mode_rows = sorted(
        [row for row in rows if row["dataset_id"] == "t500_s10000"],
        key=lambda row: row["mode"],
    )
    labels = [row["mode"] for row in mode_rows]
    values = [float(row["wall_median_seconds"]) for row in mode_rows]
    lower = [value - float(row["wall_min_seconds"]) for value, row in zip(values, mode_rows)]
    upper = [float(row["wall_max_seconds"]) - value for value, row in zip(values, mode_rows)]
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.bar(labels, values, yerr=[lower, upper], capsize=3)
    ax.set_xlabel("Analysis mode")
    ax.set_ylabel("Wall time (s), median and range")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(args.output_dir / "runtime_by_mode.png", dpi=300)
    fig.savefig(args.output_dir / "runtime_by_mode.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
