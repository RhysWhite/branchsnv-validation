#!/usr/bin/env python3
"""Regression-test merged seed recovery against the frozen formal diagnostic."""

from __future__ import annotations

import csv
import importlib.util
import io
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

EXP = ROOT / "experiments/07_comparative_landscape"

MERGED_CHECKER = EXP / "check_seed_recovery_merged.py"

FORMAL_CANDIDATES = (
    ROOT
    / "results"
    / "07_comparative_landscape"
    / "formal_search"
    / "candidate_records.tsv"
)

ORIGINAL_MATCHES = (
    ROOT
    / "results"
    / "07_comparative_landscape"
    / "screening"
    / "seed_recovery_candidate_matches.tsv"
)

ORIGINAL_SUMMARY = (
    ROOT
    / "results"
    / "07_comparative_landscape"
    / "screening"
    / "seed_recovery_summary.tsv"
)


ORIGINAL_MATCH_FIELDS = [
    "seed_tool",
    "matched_aliases",
    "source",
    "query_id",
    "query_family",
    "source_record_id",
    "entity_type",
    "title_or_name",
    "year",
    "doi",
    "pmid",
    "source_url",
]

ORIGINAL_SUMMARY_FIELDS = [
    "seed_tool",
    "seed_category",
    "seed_comparison_role",
    "aliases_tested",
    "candidate_match_rows",
    "unique_candidate_records",
    "automatic_status",
    "human_confirmation",
]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load module: {path}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def read_tsv(path: Path):
    with path.open(
        newline="",
        encoding="utf-8",
    ) as fh:
        reader = csv.DictReader(
            fh,
            delimiter="\t",
        )
        return list(reader)


def render_tsv(
    fields: list[str],
    rows: list[dict[str, str]],
) -> bytes:
    buf = io.StringIO(newline="")

    writer = csv.DictWriter(
        buf,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )

    writer.writeheader()
    writer.writerows(rows)

    return buf.getvalue().encode("utf-8")


def main() -> None:
    merged = load_module(
        MERGED_CHECKER,
        "branchsnv_merged_seed_checker",
    )

    original = merged.load_original_checker()

    _, seeds = merged.read_tsv(
        merged.SEEDS
    )

    formal_records = read_tsv(
        FORMAL_CANDIDATES
    )

    if len(formal_records) != 3_108:
        raise RuntimeError(
            f"Unexpected formal candidate count: "
            f"{len(formal_records):,}"
        )

    for row in formal_records:
        row["search_stage"] = "formal"

    matches, summary = merged.run_recovery(
        formal_records,
        seeds,
        original,
    )

    projected_matches = [
        {
            field: row[field]
            for field in ORIGINAL_MATCH_FIELDS
        }
        for row in matches
    ]

    projected_summary = [
        {
            field: row[field]
            for field in ORIGINAL_SUMMARY_FIELDS
        }
        for row in summary
    ]

    observed_matches = render_tsv(
        ORIGINAL_MATCH_FIELDS,
        projected_matches,
    )

    observed_summary = render_tsv(
        ORIGINAL_SUMMARY_FIELDS,
        projected_summary,
    )

    expected_matches = ORIGINAL_MATCHES.read_bytes()
    expected_summary = ORIGINAL_SUMMARY.read_bytes()

    if observed_matches != expected_matches:
        raise RuntimeError(
            "Merged implementation does not reproduce the "
            "frozen original candidate-match TSV"
        )

    if observed_summary != expected_summary:
        raise RuntimeError(
            "Merged implementation does not reproduce the "
            "frozen original summary TSV"
        )

    for row in summary:
        if row["automatic_status"] == "candidate_match_found":
            if row["search_stages_recovered"] != "formal":
                raise RuntimeError(
                    "Recovered formal seed has unexpected "
                    "stage provenance"
                )
        else:
            if row["search_stages_recovered"]:
                raise RuntimeError(
                    "Unrecovered formal seed has stage provenance"
                )

    recovered = sum(
        r["automatic_status"] == "candidate_match_found"
        for r in summary
    )

    if recovered != 8:
        raise RuntimeError(
            f"Expected original recovery of 8; observed {recovered}"
        )

    print(
        "PASS | original candidate-match TSV reproduced byte-for-byte "
        "after removing added search_stage field"
    )
    print(
        "PASS | original summary TSV reproduced byte-for-byte "
        "after removing added search-stage summary field"
    )
    print("PASS | original formal recovery remains 8/31")
    print("PASS | added stage provenance is formal-only as expected")
    print()
    print(
        "PASS | merged diagnostic preserves frozen "
        "seed-name matching semantics"
    )


if __name__ == "__main__":
    main()
