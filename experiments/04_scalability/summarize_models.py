#!/usr/bin/env python3
"""Fit simple descriptive linear models to Experiment 4 medians."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def fit(name: str, rows: list[dict[str, str]], x_key: str, y_key: str, x_unit: str) -> dict[str, object]:
    xs = [float(row[x_key]) for row in rows]
    ys = [float(row[y_key]) for row in rows]
    count = len(xs)
    x_mean = sum(xs) / count
    y_mean = sum(ys) / count
    ss_x = sum((value - x_mean) ** 2 for value in xs)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / ss_x
    intercept = y_mean - slope * x_mean
    predictions = [intercept + slope * value for value in xs]
    residual = sum((observed - predicted) ** 2 for observed, predicted in zip(ys, predictions))
    total = sum((observed - y_mean) ** 2 for observed in ys)
    return {
        "model": name,
        "n": count,
        "x": x_key,
        "y": y_key,
        "slope_per_x_unit": f"{slope:.12g}",
        "intercept": f"{intercept:.12g}",
        "r_squared": f"{1 - residual / total:.9f}",
        "x_unit": x_unit,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.summary.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    both = [row for row in rows if row["mode"] == "both"]
    taxa = sorted(
        [row for row in both if int(row["nchar"]) == 10_000],
        key=lambda row: int(row["ntax"]),
    )
    sites = sorted(
        [row for row in both if int(row["ntax"]) == 250],
        key=lambda row: int(row["nchar"]),
    )
    models = [
        fit("runtime_by_taxa_10000_sites", taxa, "ntax", "wall_median_seconds", "taxon"),
        fit("runtime_by_sites_250_taxa", sites, "nchar", "wall_median_seconds", "site"),
        fit("memory_by_taxa_10000_sites", taxa, "ntax", "peak_rss_median_mib", "taxon"),
        fit("memory_by_sites_250_taxa", sites, "nchar", "peak_rss_median_mib", "site"),
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(models[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(models)


if __name__ == "__main__":
    main()
