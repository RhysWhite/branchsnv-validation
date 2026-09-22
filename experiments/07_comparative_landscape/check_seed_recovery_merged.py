#!/usr/bin/env python3
"""Run the frozen seed-name recovery diagnostic on the merged search universe.

Matching semantics are imported directly from the original frozen
check_seed_recovery.py implementation.

This remains a search-sensitivity diagnostic only. A candidate name match is
not a software-landscape eligibility decision, capability classification, or
benchmark-eligibility decision.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

EXP = ROOT / "experiments/07_comparative_landscape"

ORIGINAL_CHECKER = EXP / "check_seed_recovery.py"
SEEDS = EXP / "seed_tool_registry.tsv"

MERGED = (
    ROOT
    / "results"
    / "07_comparative_landscape"
    / "merged_search_universe"
)

CANDIDATES = MERGED / "candidate_records.tsv"

OUTDIR = (
    ROOT
    / "results"
    / "07_comparative_landscape"
    / "merged_seed_recovery"
)

MATCHES = OUTDIR / "seed_recovery_candidate_matches.tsv"
SUMMARY = OUTDIR / "seed_recovery_summary.tsv"
DIAGNOSTIC = OUTDIR / "seed_recovery_diagnostic.json"
CHECKSUMS = OUTDIR / "checksums.sha256"

EXPECTED_ORIGINAL_CHECKER_SHA256 = (
    "c282af20ea7a6a09d3ec69e929865283"
    "6683ac13bb2120d34adf139d6d2b44bc"
)

EXPECTED_SEED_REGISTRY_SHA256 = (
    "df373f691df72a7a65de7067ef33ae500"
    "5a3a8e36a1165e0d467bad69082760c"
)

EXPECTED_SEEDS = 31
EXPECTED_CANDIDATES = 116_556
ALLOWED_STAGES = {"formal", "high_recall"}

MATCH_FIELDS = [
    "seed_tool",
    "matched_aliases",
    "search_stage",
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

SUMMARY_FIELDS = [
    "seed_tool",
    "seed_category",
    "seed_comparison_role",
    "aliases_tested",
    "candidate_match_rows",
    "unique_candidate_records",
    "search_stages_recovered",
    "automatic_status",
    "human_confirmation",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def verify_sha256_manifest(base: Path, manifest: Path) -> None:
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        expected, name = line.split(maxsplit=1)
        name = name.strip()

        if name.startswith("*"):
            name = name[1:]

        path = base / name

        if not path.is_file():
            raise RuntimeError(
                f"Checksum target missing: {path}"
            )

        observed = sha256_file(path)

        if observed != expected:
            raise RuntimeError(
                f"Checksum mismatch for {path}: "
                f"expected {expected}, observed {observed}"
            )


def load_original_checker():
    if (
        sha256_file(ORIGINAL_CHECKER)
        != EXPECTED_ORIGINAL_CHECKER_SHA256
    ):
        raise RuntimeError(
            "Original seed-recovery implementation hash changed"
        )

    if (
        sha256_file(SEEDS)
        != EXPECTED_SEED_REGISTRY_SHA256
    ):
        raise RuntimeError(
            "Seed-tool registry hash changed"
        )

    spec = importlib.util.spec_from_file_location(
        "branchsnv_original_seed_recovery",
        ORIGINAL_CHECKER,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load original checker: {ORIGINAL_CHECKER}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(
        newline="",
        encoding="utf-8",
    ) as fh:
        reader = csv.DictReader(fh, delimiter="\t")

        if reader.fieldnames is None:
            raise RuntimeError(f"No TSV header: {path}")

        return list(reader.fieldnames), list(reader)


def run_recovery(
    records: list[dict[str, str]],
    seeds: list[dict[str, str]],
    original,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Apply the original frozen matching semantics to supplied records."""

    if len(seeds) != EXPECTED_SEEDS:
        raise RuntimeError(
            f"Expected {EXPECTED_SEEDS} seed tools; "
            f"found {len(seeds)}"
        )

    match_rows: list[dict[str, str]] = []
    summary_rows: list[dict[str, str]] = []

    for seed in seeds:
        tool = seed["tool"]

        # Imported directly from the original frozen implementation.
        aliases = original.aliases_for(tool)

        found: list[dict[str, str]] = []

        for record in records:
            stage = record.get("search_stage", "")

            if stage not in ALLOWED_STAGES:
                raise RuntimeError(
                    f"Unexpected search_stage: {stage!r}"
                )

            title = record["title_or_name"]

            # Imported directly from the original frozen implementation.
            matched_aliases = [
                alias
                for alias in aliases
                if original.phrase_present(alias, title)
            ]

            if not matched_aliases:
                continue

            row = {
                "seed_tool": tool,
                "matched_aliases":
                    ";".join(matched_aliases),
                "search_stage": stage,
                "source": record["source"],
                "query_id": record["query_id"],
                "query_family": record["query_family"],
                "source_record_id":
                    record["source_record_id"],
                "entity_type": record["entity_type"],
                "title_or_name": title,
                "year": record["year"],
                "doi": record["doi"],
                "pmid": record["pmid"],
                "source_url": record["source_url"],
            }

            found.append(row)
            match_rows.append(row)

        # Preserve the exact original definition of unique candidate evidence.
        unique_evidence = {
            (
                r["source"],
                r["source_record_id"],
                r["title_or_name"],
            )
            for r in found
        }

        recovered_stages = sorted({
            r["search_stage"]
            for r in found
        })

        summary_rows.append({
            "seed_tool": tool,
            "seed_category": seed["category"],
            "seed_comparison_role":
                seed["comparison_role_candidate"],
            "aliases_tested":
                ";".join(aliases),
            "candidate_match_rows":
                str(len(found)),
            "unique_candidate_records":
                str(len(unique_evidence)),
            "search_stages_recovered":
                ";".join(recovered_stages),
            "automatic_status": (
                "candidate_match_found"
                if found
                else "not_recovered_by_name"
            ),
            "human_confirmation": "pending",
        })

    # Original sort semantics, with search_stage only as a final deterministic
    # provenance tie-breaker.
    match_rows.sort(
        key=lambda r: (
            r["seed_tool"].casefold(),
            r["source"],
            r["title_or_name"].casefold(),
            r["query_id"],
            r["search_stage"],
        )
    )

    return match_rows, summary_rows


def write_tsv(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:
    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


def build_diagnostic(
    match_rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
) -> dict:
    recovered = [
        r
        for r in summary_rows
        if r["automatic_status"] == "candidate_match_found"
    ]

    unrecovered = [
        r
        for r in summary_rows
        if r["automatic_status"] == "not_recovered_by_name"
    ]

    stage_recovery = {
        "formal": sum(
            "formal" in r["search_stages_recovered"].split(";")
            for r in recovered
        ),
        "high_recall": sum(
            "high_recall"
            in r["search_stages_recovered"].split(";")
            for r in recovered
        ),
    }

    role_counts: dict[str, dict[str, int]] = {}

    for row in summary_rows:
        role = row["seed_comparison_role"]

        if role not in role_counts:
            role_counts[role] = {
                "total": 0,
                "candidate_match_found": 0,
                "not_recovered_by_name": 0,
            }

        role_counts[role]["total"] += 1
        role_counts[role][row["automatic_status"]] += 1

    return {
        "schema_version": 1,
        "experiment":
            "07_comparative_landscape_merged_seed_recovery",
        "status": "COMPLETE",
        "diagnostic_only": True,
        "seed_tools": len(summary_rows),
        "candidate_records_examined": EXPECTED_CANDIDATES,
        "candidate_name_recovery": len(recovered),
        "not_recovered_by_name": len(unrecovered),
        "candidate_evidence_rows": len(match_rows),
        "stage_recovery": stage_recovery,
        "comparison_role_summary": role_counts,
        "matching_semantics":
            "imported from frozen check_seed_recovery.py",
        "original_checker_sha256":
            sha256_file(ORIGINAL_CHECKER),
        "seed_registry_sha256":
            sha256_file(SEEDS),
        "merged_candidate_records_sha256":
            sha256_file(CANDIDATES),
        "merged_checksums_sha256":
            sha256_file(MERGED / "checksums.sha256"),
        "screening_performed": False,
        "eligibility_decisions_made": False,
        "capability_classification_performed": False,
        "search_retuning_permitted": False,
        "human_confirmation":
            "pending for every candidate name match",
    }


def write_outputs(
    outdir: Path,
    match_rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
) -> None:
    if outdir.exists():
        raise RuntimeError(
            f"Output directory already exists: {outdir}"
        )

    outdir.mkdir(parents=True)

    write_tsv(
        outdir / MATCHES.name,
        MATCH_FIELDS,
        match_rows,
    )

    write_tsv(
        outdir / SUMMARY.name,
        SUMMARY_FIELDS,
        summary_rows,
    )

    diagnostic = build_diagnostic(
        match_rows,
        summary_rows,
    )

    (outdir / DIAGNOSTIC.name).write_text(
        json.dumps(
            diagnostic,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    names = [
        MATCHES.name,
        SUMMARY.name,
        DIAGNOSTIC.name,
    ]

    with (
        outdir / CHECKSUMS.name
    ).open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        for name in names:
            fh.write(
                f"{sha256_file(outdir / name)}  {name}\n"
            )

    verify_sha256_manifest(
        outdir,
        outdir / CHECKSUMS.name,
    )


def main() -> int:
    original = load_original_checker()

    verify_sha256_manifest(
        MERGED,
        MERGED / "checksums.sha256",
    )

    _, seeds = read_tsv(SEEDS)
    fields, records = read_tsv(CANDIDATES)

    if len(records) != EXPECTED_CANDIDATES:
        raise RuntimeError(
            f"Expected {EXPECTED_CANDIDATES:,} merged candidate rows; "
            f"found {len(records):,}"
        )

    if not fields or fields[0] != "search_stage":
        raise RuntimeError(
            "Merged candidate corpus lacks leading search_stage field"
        )

    stages = {
        r["search_stage"]
        for r in records
    }

    if stages != ALLOWED_STAGES:
        raise RuntimeError(
            f"Unexpected merged stage set: {sorted(stages)}"
        )

    match_rows, summary_rows = run_recovery(
        records,
        seeds,
        original,
    )

    write_outputs(
        OUTDIR,
        match_rows,
        summary_rows,
    )

    recovered = sum(
        r["automatic_status"] == "candidate_match_found"
        for r in summary_rows
    )

    print(f"seed tools                    = {len(summary_rows)}")
    print(f"candidate name recovery       = {recovered}")
    print(
        "not recovered by name         = "
        f"{len(summary_rows) - recovered}"
    )
    print(f"candidate evidence rows       = {len(match_rows)}")
    print()
    print("IMPORTANT:")
    print("  candidate name recovery != confirmed tool recovery")
    print("  every candidate match remains pending human confirmation")
    print("  search expressions will not be retuned from this result")
    print()
    print(f"WROTE {OUTDIR / SUMMARY.name}")
    print(f"WROTE {OUTDIR / MATCHES.name}")
    print(f"WROTE {OUTDIR / DIAGNOSTIC.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
