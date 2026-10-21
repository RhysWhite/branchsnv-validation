#!/usr/bin/env python3
"""Figure 3: pointwise head-to-head Experiment 07 benchmark.

Requires a reviewer-approved, semantically harmonised Experiment 07 long table.
The script DOES NOT transform native ancestral-state, homoplasy, or other
incommensurate output into a fictional branch-event F1 score.

Each dot = one observation, no distribution summaries and no aggregated bars.
By default the artwork carries a PRELIMINARY evidence label.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

METHODS = ["BRANCHSNV", "SNPPar", "TreeTime", "FastML", "PAML",
           "PastML", "ARPIP", "HomoplasyFinder", "POUTINE"]
REQUIRED = {"scenario_id", "pair_id", "method", "tips", "regime",
            "masking", "endpoint", "value", "runtime_seconds", "eligible"}
VALID_MASK = {"complete", "masked_5pct"}
TRUTHY = {"true", "1", "yes", "y"}
FALSY = {"false", "0", "no", "n"}


def stop(message: str) -> None:
    raise SystemExit(f"FIGURE 3 INPUT ERROR: {message}")


def stable_jitter(key: str, magnitude: float = 0.23) -> float:
    """Fixed per-row offsets stable across runs and independent of hash randomisation."""
    val = int(hashlib.sha256(key.encode()).hexdigest()[:12], 16) / (16**12 - 1)
    return (val - 0.5) * magnitude * 2


def load_table(path: Path, endpoint: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not path.is_file():
        stop(f"Input file does not exist: {path}")
    sep = "\t" if path.suffix.lower() == ".tsv" else ","
    df = pd.read_csv(path, sep=sep, dtype={"scenario_id": str, "pair_id": str, "method": str,
                                       "masking": str, "regime": str, "endpoint": str,
                                       "eligible": str})
    missing = REQUIRED - set(df.columns)
    if missing:
        stop(f"Missing columns {sorted(missing)}. See INPUT_CONTRACT.md")
    if df.empty:
        stop("Empty input")
    df["method"] = df["method"].str.strip().replace({"BranchSNV": "BRANCHSNV", "branchsnv": "BRANCHSNV"})
    df = df[df["endpoint"] == endpoint].copy()
    for identifier in ("scenario_id", "pair_id", "method", "masking", "regime"):
        if df[identifier].isna().any() or (df[identifier].astype(str).str.strip() == "").any():
            stop(f"Missing identifier values in {identifier}")
    if df.empty:
        stop(f"No rows for endpoint={endpoint!r}")
    unknown = set(df["method"]) - set(METHODS)
    if unknown:
        stop(f"Unrecognised method labels: {sorted(unknown)}")
    unknown_masks = set(df["masking"]) - VALID_MASK
    if unknown_masks:
        stop(f"Unknown masking states: {sorted(unknown_masks)}")
    df["eligible"] = df["eligible"].str.strip().str.lower()
    invalid = set(df["eligible"]) - TRUTHY - FALSY
    if invalid:
        stop(f"Unrecognised eligibility values: {sorted(invalid)}")
    df["plot_eligible"] = df["eligible"].isin(TRUTHY)
    for c in ("tips", "value", "runtime_seconds"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if (df["tips"].isna()).any():
        stop("Some tips values are missing/non-numeric")
    if (df.loc[df["plot_eligible"], "value"].isna()).any():
        stop("Eligible rows require finite numeric endpoint values")
    if (~np.isfinite(df.loc[df["plot_eligible"], "value"])).any():
        stop("Eligible rows contain non-finite endpoint values")
    df["exclusion_reason"] = np.where(df["plot_eligible"], "", "explicitly_ineligible")
    if (~df["plot_eligible"]).any():
        if "reason" not in df.columns:
            stop("Input contains ineligible rows but no reason column")
        if (df.loc[~df["plot_eligible"], "reason"].fillna("").str.strip() == "").any():
            stop("Ineligible rows must have an explicit 'reason'")
    if df["plot_eligible"].any() and "BRANCHSNV" not in set(df.loc[df["plot_eligible"], "method"]):
        stop("No eligible BRANCHSNV rows; cannot make paired comparisons")
    eligible = df[df["plot_eligible"]].copy()
    # A pair_id denotes the SAME biological/simulation history across masking states.
    for identity in ("tips", "regime"):
        if (eligible.groupby(["pair_id", "method"])[identity].nunique() > 1).any():
            stop(f"Inconsistent {identity} within a pair_id/method; mask pairs are not comparable")
    for cols in (["scenario_id", "method"], ["pair_id", "masking", "method"]):
        dup = eligible.duplicated(cols, keep=False)
        if dup.any():
            ex = eligible.loc[dup, cols].head(3).to_dict("records")
            stop(f"Duplicate eligible rows for {cols}: {ex}; include replicates in scenario_id/pair_id")
    return df, eligible


def xpoints(ax, df: pd.DataFrame, col: str, ordered: list[str],
            *, subtitle: str = "", y_label: str = "", hline: float | None = None,
            ylim: tuple[float,float] | None = None, vary_tip_shape: bool = False) -> None:
    if hline is not None:
        ax.axhline(hline, linestyle="--", linewidth=0.8, alpha=0.72, zorder=0)
    for i, method in enumerate(ordered):
        sample = df.loc[df["method"] == method]
        if sample.empty:
            continue
        tipsets = sorted(sample["tips"].dropna().unique()) if vary_tip_shape else [None]
        shapes = ["o", "s", "^"]
        for k, tips in enumerate(tipsets):
            block = sample.loc[sample["tips"] == tips] if tips is not None else sample
            xs = np.array([i + stable_jitter(f"{method}/{sid}/{pid}/{mask}")
                           for sid, pid, mask in zip(block["scenario_id"], block["pair_id"], block["masking"])])
            ys = block[col].to_numpy(dtype=float)
            marker = shapes[k % len(shapes)] if vary_tip_shape else "o"
            if method == "BRANCHSNV":
                ax.scatter(xs, ys, s=14, marker=marker, facecolors="none",
                           edgecolors="black", linewidths=0.75, alpha=0.80, zorder=3)
            else:
                ax.scatter(xs, ys, s=9, marker=marker, linewidths=0, alpha=0.49, zorder=2)
    ax.set_xticks(range(len(ordered)))
    ax.set_xticklabels(ordered, rotation=58, ha="right", rotation_mode="anchor", fontsize=7)
    ax.set_ylabel(y_label, fontsize=8)
    if subtitle:
        ax.set_title(subtitle, fontsize=9, loc="left", pad=8, weight="bold")
    ax.grid(axis="y", alpha=0.15, linewidth=0.5)
    if ylim is not None:
        ax.set_ylim(*ylim)


def build_figure(eligible: pd.DataFrame, all_rows: pd.DataFrame,
                 endpoint: str, direction: str, outdir: Path, preview: bool):
    present_methods = [m for m in METHODS if m in set(all_rows["method"])]
    if len(present_methods) < 2:
        stop("Need BRANCHSNV and at least one comparator for head-to-head plotting")

    # Strictly match BranchSNV/comparator on the SAME unique scenario and endpoint.
    branch = eligible[eligible["method"] == "BRANCHSNV"][["scenario_id", "value"]]
    others = eligible[eligible["method"] != "BRANCHSNV"].copy()
    comparisons = others.merge(branch.rename(columns={"value": "branchsnv_value"}),
                               on="scenario_id", how="inner", validate="many_to_one")
    comparisons["advantage"] = (comparisons["branchsnv_value"] - comparisons["value"])
    if direction == "lower":
        comparisons["advantage"] *= -1

    # Masking effects are paired by biological scenario family, NOT by scenario_id.
    pair = eligible.pivot(index=["pair_id", "method", "tips", "regime"],
                          columns="masking", values="value")
    for c in ["complete", "masked_5pct"]:
        if c not in pair.columns:
            stop(f"Masking analysis requires {c!r} rows")
    mask_pairs = pair.dropna(subset=["complete", "masked_5pct"]).reset_index()
    mask_pairs["masking_change"] = (mask_pairs["masked_5pct"] - mask_pairs["complete"])
    if direction == "lower":
        mask_pairs["masking_change"] *= -1
    # Each mark remains an individual matched pair; no medians/means or boxplots.
    mask_pairs["scenario_id"] = mask_pairs["pair_id"]
    mask_pairs["masking"] = "paired"
    runtimes = all_rows.loc[np.isfinite(all_rows["runtime_seconds"]) &
                            (all_rows["runtime_seconds"] > 0)].copy()
    # Runtime points are *measured observations* from rows for the specified endpoint.
    # Note: run environment comparability must be established in Experiment 07 evidence.

    fig, axes = plt.subplots(2, 2, figsize=(8.4, 9.7), dpi=250)
    plt.subplots_adjust(left=0.115, right=0.975, top=0.860,
                        bottom=0.200, wspace=0.48, hspace=0.58)
    axa, axb, axc, axd = axes.flat
    eligible_methods = [m for m in METHODS if m in set(eligible["method"])]
    xpoints(axa, eligible, "value", eligible_methods,
            subtitle="A  Endpoint versus truth", y_label="Scenario-level score")
    xpoints(axb, comparisons, "advantage", [m for m in eligible_methods if m != "BRANCHSNV"],
            subtitle="B  Paired BRANCHSNV advantage", y_label="Signed score difference", hline=0)
    xpoints(axc, mask_pairs, "masking_change", eligible_methods,
            subtitle="C  Effect of 5% masking", y_label="Signed change in score", hline=0)
    if not runtimes.empty:
        xpoints(axd, runtimes, "runtime_seconds", present_methods,
                subtitle="D  Observed runtime (all methods)", y_label="Runtime (seconds; log scale)", vary_tip_shape=True)
        axd.set_yscale("log")
    else:
        axd.set_title("D  Runtime not supplied", loc="left", fontsize=9, weight="bold")
        axd.text(0.5, 0.5, "No measured runtime rows", ha="center", va="center", transform=axd.transAxes)
        axd.set_xticks([])
    fig.text(0.115, 0.980, "Figure 3 | Experiment 07: head-to-head comparison",
             ha="left", va="top", fontsize=12, weight="bold")
    fig.text(0.115, 0.940, f"Endpoint: {endpoint}   |   Better performance: {direction} score",
             ha="left", va="top", fontsize=8.4)
    fig.text(0.115, 0.911, "Every dot is an individual scenario or matched scenario-pair. No bars or summaries.",
             ha="left", va="top", fontsize=8)
    fig.text(0.115, 0.080,
             "A-C: eligible endpoints only; unsupported methods excluded and audited. B: above zero favours BRANCHSNV.",
             fontsize=7, ha="left", va="bottom")
    fig.text(0.115, 0.054,
             "C: below zero indicates masking loss. D: measured runtime; circle/square/triangle = 32/128/512 tips.",
             fontsize=7, ha="left", va="bottom")
    if preview:
        label = ("SYNTHETIC DATA - LAYOUT ONLY" if "illustrative" in endpoint.lower()
                 else "PRELIMINARY - UNSIGNED EXPERIMENT 07")
        fig.text(0.52, 0.505, label,
                 ha="center", va="center", fontsize=17, weight="bold", rotation=22,
                 alpha=0.15)
    outdir.mkdir(parents=True, exist_ok=True)
    for suffix in ("svg", "pdf", "png"):
        fig.savefig(outdir / f"figure_3.{suffix}", dpi=400, facecolor="white")
    plt.close(fig)
    return comparisons, mask_pairs, runtimes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--outdir", type=Path, required=True)
    p.add_argument("--endpoint", required=True, help="Only one scientifically comparable endpoint per figure")
    p.add_argument("--direction", choices=["higher", "lower"], required=True)
    p.add_argument("--preliminary", action="store_true", help="Required: label unapproved results")
    args = p.parse_args()
    if not args.preliminary:
        stop("Refusing to emit unlabeled artwork. Use --preliminary; final release requires independent gate review.")
    all_rows, eligible = load_table(args.input, args.endpoint)
    if eligible.empty:
        stop("No explicitly eligible observations; no comparison plotted")
    if not eligible["method"].nunique() >= 2:
        stop("Fewer than two eligible methods, no direct comparative endpoint")
    comparison, pairs, times = build_figure(eligible, all_rows, args.endpoint,
                                            args.direction, args.outdir, preview=True)
    out = args.outdir
    all_rows.to_csv(out / "input_endpoint_rows.tsv", sep="\t", index=False)
    all_rows.loc[~all_rows["plot_eligible"]].to_csv(out / "excluded_rows.tsv", sep="\t", index=False)
    comparison.to_csv(out / "paired_comparisons.tsv", sep="\t", index=False)
    pairs.to_csv(out / "masking_pairs.tsv", sep="\t", index=False)
    times.to_csv(out / "runtime_rows.tsv", sep="\t", index=False)
    (out / "PROVENANCE.txt").write_text(
        f"Experiment 07: preliminary / NOT SIGNED OFF\n"
        f"Input file: {args.input}\nInput SHA256: {hashlib.sha256(args.input.read_bytes()).hexdigest()}\n"
        f"Endpoint: {args.endpoint}\nDirection: {args.direction}\n"
        f"Eligible rows: {len(eligible)}\nEligible methods: {eligible.method.nunique()}\n"
        f"Paired comparisons: {len(comparison)}\nMasking pairs: {len(pairs)}\n"
        f"Measured runtime rows: {len(times)}\n"
        "Excluded data are not imputed. Script cannot certify endpoint comparability or scientific sign-off.\n"
    )
    print((out / "PROVENANCE.txt").read_text())
    print("Rendered preliminary SVG/PDF/PNG in", out)


if __name__ == "__main__":
    main()
