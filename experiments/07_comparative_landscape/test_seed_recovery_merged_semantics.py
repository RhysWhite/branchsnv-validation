#!/usr/bin/env python3
"""Regression-test merged seed recovery against the frozen formal diagnostic.

Two complementary checks are performed:

1. Applying the merged implementation directly to the original formal
   candidate table must still reproduce the historical output byte-for-byte.

2. Applying the same frozen matching semantics to the formal-stage subset of
   the deterministic merged candidate universe must reproduce exactly the same
   evidence-row multiset and byte-identical full-row canonicalization.

The second criterion handles ties in the historical output sort key without
changing any matching or recovery semantics.
"""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
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

MERGED_CANDIDATES = (
    ROOT
    / "results"
    / "07_comparative_landscape"
    / "merged_search_universe"
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

EXPECTED_CANONICAL_SHA256 = (
    "7b00244753bbdc8b19637dfcc2bab96ba"
    "77633ea649a887a2b9203462fc20c14"
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


def project_matches(rows):
    return [
        {
            field: row[field]
            for field in ORIGINAL_MATCH_FIELDS
        }
        for row in rows
    ]


def project_summary(rows):
    return [
        {
            field: row[field]
            for field in ORIGINAL_SUMMARY_FIELDS
        }
        for row in rows
    ]


def row_tuple(row):
    return tuple(
        row[field]
        for field in ORIGINAL_MATCH_FIELDS
    )


def canonical_key(row):
    return (
        row["seed_tool"].casefold(),
        row["source"],
        row["title_or_name"].casefold(),
        row["query_id"],
        row["source_record_id"],
        row["query_family"],
        row["entity_type"],
        row["year"],
        row["doi"],
        row["pmid"],
        row["source_url"],
        row["matched_aliases"],
    )


def main() -> None:
    merged = load_module(
        MERGED_CHECKER,
        "branchsnv_merged_seed_checker",
    )

    original = merged.load_original_checker()

    _, seeds = merged.read_tsv(
        merged.SEEDS
    )

    expected_match_rows = read_tsv(
        ORIGINAL_MATCHES
    )

    expected_summary_rows = read_tsv(
        ORIGINAL_SUMMARY
    )

    expected_matches_bytes = ORIGINAL_MATCHES.read_bytes()
    expected_summary_bytes = ORIGINAL_SUMMARY.read_bytes()

    # ---------------------------------------------------------------
    # Test 1: historical formal input must retain exact old behavior.
    # ---------------------------------------------------------------

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

    direct_matches, direct_summary = merged.run_recovery(
        formal_records,
        seeds,
        original,
    )

    direct_match_bytes = render_tsv(
        ORIGINAL_MATCH_FIELDS,
        project_matches(direct_matches),
    )

    direct_summary_bytes = render_tsv(
        ORIGINAL_SUMMARY_FIELDS,
        project_summary(direct_summary),
    )

    if direct_match_bytes != expected_matches_bytes:
        raise RuntimeError(
            "Direct formal-input candidate matches no longer "
            "reproduce historical output byte-for-byte"
        )

    if direct_summary_bytes != expected_summary_bytes:
        raise RuntimeError(
            "Direct formal-input summary no longer reproduces "
            "historical output byte-for-byte"
        )

    direct_recovered = sum(
        r["automatic_status"] == "candidate_match_found"
        for r in direct_summary
    )

    if direct_recovered != 8:
        raise RuntimeError(
            f"Expected original recovery of 8; "
            f"observed {direct_recovered}"
        )

    print(
        "PASS | direct original-formal candidate-match TSV "
        "reproduced byte-for-byte"
    )
    print(
        "PASS | direct original-formal summary TSV "
        "reproduced byte-for-byte"
    )
    print("PASS | original formal recovery remains 8/31")

    # ---------------------------------------------------------------
    # Test 2: formal subset of the deterministic merged universe.
    # ---------------------------------------------------------------

    merged_records = read_tsv(
        MERGED_CANDIDATES
    )

    if len(merged_records) != 116_556:
        raise RuntimeError(
            f"Unexpected merged candidate count: "
            f"{len(merged_records):,}"
        )

    merged_formal_records = [
        dict(row)
        for row in merged_records
        if row["search_stage"] == "formal"
    ]

    if len(merged_formal_records) != 3_108:
        raise RuntimeError(
            f"Expected 3,108 formal-stage rows in merged universe; "
            f"observed {len(merged_formal_records):,}"
        )

    merged_formal_matches, merged_formal_summary = (
        merged.run_recovery(
            merged_formal_records,
            seeds,
            original,
        )
    )

    projected_matches = project_matches(
        merged_formal_matches
    )

    projected_summary = project_summary(
        merged_formal_summary
    )

    # Summary has one row per seed in registry order and therefore has
    # no historical output-order ambiguity.
    merged_summary_bytes = render_tsv(
        ORIGINAL_SUMMARY_FIELDS,
        projected_summary,
    )

    if merged_summary_bytes != expected_summary_bytes:
        raise RuntimeError(
            "Merged-universe formal-stage summary differs "
            "from historical formal summary"
        )

    # Candidate evidence must be exactly the same multiset.
    expected_counter = Counter(
        row_tuple(row)
        for row in expected_match_rows
    )

    observed_counter = Counter(
        row_tuple(row)
        for row in projected_matches
    )

    missing = expected_counter - observed_counter
    extra = observed_counter - expected_counter

    if missing or extra:
        raise RuntimeError(
            "Merged-universe formal-stage candidate evidence "
            "differs from historical evidence content"
        )

    # Resolve historical stable-sort ties using all emitted fields.
    expected_canonical = sorted(
        expected_match_rows,
        key=canonical_key,
    )

    observed_canonical = sorted(
        projected_matches,
        key=canonical_key,
    )

    expected_canonical_bytes = render_tsv(
        ORIGINAL_MATCH_FIELDS,
        expected_canonical,
    )

    observed_canonical_bytes = render_tsv(
        ORIGINAL_MATCH_FIELDS,
        observed_canonical,
    )

    if expected_canonical_bytes != observed_canonical_bytes:
        raise RuntimeError(
            "Canonicalized merged-universe formal evidence "
            "differs from historical evidence"
        )

    canonical_sha = hashlib.sha256(
        expected_canonical_bytes
    ).hexdigest()

    if canonical_sha != EXPECTED_CANONICAL_SHA256:
        raise RuntimeError(
            f"Unexpected canonical SHA256: {canonical_sha}"
        )

    merged_formal_recovered = sum(
        r["automatic_status"] == "candidate_match_found"
        for r in merged_formal_summary
    )

    if merged_formal_recovered != 8:
        raise RuntimeError(
            "Merged-universe formal subset does not retain "
            "historical 8/31 recovery"
        )

    print(
        "PASS | merged-universe formal summary "
        "reproduces historical summary byte-for-byte"
    )
    print(
        "PASS | merged-universe formal candidate evidence "
        "has exact historical row multiset"
    )
    print(
        "PASS | merged-universe formal candidate evidence "
        "is byte-identical after deterministic canonicalization"
    )
    print(
        "PASS | canonical SHA256 = "
        + canonical_sha
    )
    print(
        "PASS | merged-universe formal recovery remains 8/31"
    )

    print()
    print(
        "PASS | merged diagnostic preserves frozen "
        "seed-name matching semantics"
    )


if __name__ == "__main__":
    main()
