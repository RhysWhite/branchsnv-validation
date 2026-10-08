#!/usr/bin/env python3
"""Check recovery of the pre-search seed tool set in the formal search corpus.

This is a search-sensitivity diagnostic only.

A match means that a formal-search record contains a seed-tool name or
prespecified normalized alias in its title/name field. Matches are retained
for human confirmation; the script does not decide software-landscape
eligibility or benchmark eligibility.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SEEDS = (
    ROOT
    / "experiments"
    / "07_comparative_landscape"
    / "seed_tool_registry.tsv"
)

CANDIDATES = (
    ROOT
    / "results"
    / "07_comparative_landscape"
    / "formal_search"
    / "candidate_records.tsv"
)

OUTDIR = (
    ROOT
    / "results"
    / "07_comparative_landscape"
    / "screening"
)

MATCHES = OUTDIR / "seed_recovery_candidate_matches.tsv"
SUMMARY = OUTDIR / "seed_recovery_summary.tsv"


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.casefold()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


# Only aliases representing orthographic/version variants of the seed name.
# These are NOT newly discovered tools.
EXPLICIT_ALIASES = {
    "CLASSICO/Evidente": [
        "CLASSICO",
        "Evidente",
    ],
    "Clade-O-Matic": [
        "Clade-O-Matic",
        "Cladeomatic",
    ],
    "IQ-TREE 2": [
        "IQ-TREE 2",
        "IQ-TREE",
    ],
    "PAUP*": [
        "PAUP*",
        "PAUP",
    ],
    "PHYLIP DNAPARS": [
        "DNAPARS",
        "PHYLIP DNAPARS",
    ],
    "ETE 3": [
        "ETE 3",
        "ETE3",
    ],
    "kSNP3.0": [
        "kSNP3.0",
        "kSNP3",
        "kSNP",
    ],
    "FastTree": [
        "FastTree",
        "FastTree 2",
    ],
    "PAML": [
        "PAML",
    ],
}


def aliases_for(tool: str) -> list[str]:
    aliases = list(EXPLICIT_ALIASES.get(tool, [tool]))

    # Slash-separated seed names are also individually searchable.
    if "/" in tool:
        aliases.extend(part.strip() for part in tool.split("/") if part.strip())

    # Preserve order while removing duplicates after normalization.
    output = []
    seen = set()

    for alias in aliases:
        n = normalize(alias)
        if not n or n in seen:
            continue
        seen.add(n)
        output.append(alias)

    return output


def phrase_present(alias: str, title: str) -> bool:
    """Whole normalized phrase match, not arbitrary substring matching."""
    a = normalize(alias)
    t = normalize(title)

    if not a or not t:
        return False

    return bool(
        re.search(
            rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])",
            t,
        )
    )


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    with SEEDS.open(newline="", encoding="utf-8") as fh:
        seeds = list(csv.DictReader(fh, delimiter="\t"))

    with CANDIDATES.open(newline="", encoding="utf-8") as fh:
        records = list(csv.DictReader(fh, delimiter="\t"))

    if len(seeds) != 31:
        raise RuntimeError(
            f"Expected 31 seed tools; found {len(seeds)}"
        )

    match_rows = []
    summary_rows = []

    for seed in seeds:
        tool = seed["tool"]
        aliases = aliases_for(tool)

        found = []

        for record in records:
            title = record["title_or_name"]

            matched_aliases = [
                alias
                for alias in aliases
                if phrase_present(alias, title)
            ]

            if not matched_aliases:
                continue

            row = {
                "seed_tool": tool,
                "matched_aliases": ";".join(matched_aliases),
                "source": record["source"],
                "query_id": record["query_id"],
                "query_family": record["query_family"],
                "source_record_id": record["source_record_id"],
                "entity_type": record["entity_type"],
                "title_or_name": title,
                "year": record["year"],
                "doi": record["doi"],
                "pmid": record["pmid"],
                "source_url": record["source_url"],
            }

            found.append(row)
            match_rows.append(row)

        unique_evidence = {
            (
                r["source"],
                r["source_record_id"],
                r["title_or_name"],
            )
            for r in found
        }

        summary_rows.append({
            "seed_tool": tool,
            "seed_category": seed["category"],
            "seed_comparison_role": seed["comparison_role_candidate"],
            "aliases_tested": ";".join(aliases),
            "candidate_match_rows": len(found),
            "unique_candidate_records": len(unique_evidence),
            "automatic_status": (
                "candidate_match_found"
                if found
                else "not_recovered_by_name"
            ),
            "human_confirmation": "pending",
        })

    match_rows.sort(
        key=lambda r: (
            r["seed_tool"].casefold(),
            r["source"],
            r["title_or_name"].casefold(),
            r["query_id"],
        )
    )

    with MATCHES.open("w", newline="", encoding="utf-8") as fh:
        fields = [
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
        writer = csv.DictWriter(
            fh,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(match_rows)

    with SUMMARY.open("w", newline="", encoding="utf-8") as fh:
        fields = [
            "seed_tool",
            "seed_category",
            "seed_comparison_role",
            "aliases_tested",
            "candidate_match_rows",
            "unique_candidate_records",
            "automatic_status",
            "human_confirmation",
        ]
        writer = csv.DictWriter(
            fh,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    recovered = sum(
        row["automatic_status"] == "candidate_match_found"
        for row in summary_rows
    )

    print(f"seed tools                    = {len(summary_rows)}")
    print(f"candidate name recovery       = {recovered}")
    print(f"not recovered by name         = {len(summary_rows) - recovered}")
    print(f"candidate evidence rows       = {len(match_rows)}")
    print()
    print("IMPORTANT:")
    print("  candidate name recovery != confirmed tool recovery")
    print("  every candidate match remains pending human confirmation")
    print()
    print(f"WROTE {SUMMARY}")
    print(f"WROTE {MATCHES}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
