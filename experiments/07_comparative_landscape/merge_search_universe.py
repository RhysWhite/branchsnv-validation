#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]

EXP = ROOT / "experiments/07_comparative_landscape"
FORMAL = ROOT / "results/07_comparative_landscape/formal_search"
HIGH = ROOT / "results/07_comparative_landscape/high_recall_search"

DEFAULT_OUTPUT = (
    ROOT
    / "results/07_comparative_landscape/merged_search_universe"
)

FORMAL_SCRIPT = EXP / "retrieve_search_corpus.py"
HIGH_SCRIPT = EXP / "retrieve_high_recall_corpus.py"
MERGE_SPEC = EXP / "MERGE_SPEC.md"

EXPECTED_CANDIDATE_ROWS = 116_556
EXPECTED_DEDUPLICATED_ROWS = 79_917
EXPECTED_SEARCH_COUNT_ROWS = 69

STAGES = ("formal", "high_recall")
ALLOWED_SOURCES = {"pubmed", "openalex", "biotools"}

SOURCE_PRIORITY = {
    "pubmed": 0,
    "openalex": 1,
    "biotools": 2,
}

STAGE_OUTPUT_PRIORITY = {
    "formal": 0,
    "high_recall": 1,
}

CANDIDATE_REQUIRED = [
    "source",
    "query_id",
    "query_family",
    "source_record_id",
    "entity_type",
    "title_or_name",
    "year",
    "doi",
    "pmid",
    "openalex_id",
    "biotools_id",
    "source_url",
]

SEARCH_COUNT_REQUIRED = [
    "source",
    "query_id",
    "query_family",
    "reported_count",
    "retrieved_count",
    "response_files",
    "complete",
]

CONFLICT_FIELDS = [
    "entity_type",
    "title_or_name",
    "year",
    "doi",
    "pmid",
]

DEDUPLICATED_FIELDS = [
    "dedup_key",
    "entity_type",
    "title_or_name",
    "year",
    "doi",
    "pmid",
    "search_stages",
    "sources",
    "query_ids",
    "query_families",
    "stage_query_ids",
    "source_record_ids",
]

CONFLICT_OUTPUT_FIELDS = [
    "dedup_key",
    "field",
    "value_count",
    "values_json",
    "search_stages",
    "sources",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def verify_sha256_manifest(base: Path, manifest: Path) -> None:
    lines = manifest.read_text(encoding="utf-8").splitlines()

    if not lines:
        raise RuntimeError(f"Empty checksum manifest: {manifest}")

    for line in lines:
        if not line.strip():
            continue

        parts = line.split(maxsplit=1)

        if len(parts) != 2:
            raise RuntimeError(
                f"Malformed checksum line in {manifest}: {line!r}"
            )

        expected, name = parts
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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as fh:
        reader = csv.DictReader(fh, delimiter="\t")

        if reader.fieldnames is None:
            raise RuntimeError(f"No TSV header: {path}")

        return list(reader.fieldnames), list(reader)


def write_tsv(
    path: Path,
    fieldnames: list[str],
    rows: Iterable[dict[str, str]],
) -> None:
    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )

        writer.writeheader()
        writer.writerows(rows)


def extract_function_source(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            source = ast.get_source_segment(text, node)

            if source is None:
                raise RuntimeError(
                    f"Could not recover {name} source from {path}"
                )

            return source

    raise RuntimeError(
        f"Function {name!r} missing from {path}"
    )


def verify_frozen_deduplication_identity() -> None:
    for name in ("dedup_key", "make_deduplicated"):
        formal = extract_function_source(FORMAL_SCRIPT, name)
        high = extract_function_source(HIGH_SCRIPT, name)

        if formal != high:
            raise RuntimeError(
                f"Frozen deduplication function differs "
                f"between retrievers: {name}"
            )


def load_formal_retriever():
    spec = importlib.util.spec_from_file_location(
        "branchsnv_formal_retriever",
        FORMAL_SCRIPT,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load formal retriever: {FORMAL_SCRIPT}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def verify_inputs() -> None:
    verify_sha256_manifest(
        FORMAL,
        FORMAL / "corpus_checksums.sha256",
    )

    verify_sha256_manifest(
        HIGH,
        HIGH / "normalized_inputs.sha256",
    )

    verify_sha256_manifest(
        EXP,
        EXP / "merge_spec.sha256",
    )

    verify_frozen_deduplication_identity()


def representative_sort_key(
    row: dict[str, str],
    retriever,
) -> tuple:
    source = row["source"]

    if source not in SOURCE_PRIORITY:
        raise RuntimeError(
            f"Unknown source encountered: {source!r}"
        )

    stage = row["search_stage"]

    if stage not in STAGES:
        raise RuntimeError(
            f"Unexpected search stage: {stage!r}"
        )

    return (
        SOURCE_PRIORITY[source],
        row["title_or_name"],
        row["year"],
        retriever.normalise_doi(row.get("doi")),
        retriever.normalise_pmid(row.get("pmid")),
        row["source_record_id"],
        row["query_id"],
        row["query_family"],
        stage,
    )


def candidate_output_sort_key(
    row: dict[str, str],
    retriever,
    candidate_fields: list[str],
) -> tuple:
    # Include every emitted field after the frozen identity key.
    # Therefore records that differ anywhere in the output cannot retain
    # input-order dependence.
    return (
        retriever.dedup_key(row),
        *(
            row.get(field, "")
            for field in candidate_fields
        ),
        row["search_stage"],
    )


def sorted_unique(values: Iterable[str]) -> str:
    return ";".join(sorted(set(values)))


def build_merged(
    input_order: tuple[str, str] = STAGES,
) -> dict:
    if set(input_order) != set(STAGES) or len(input_order) != 2:
        raise RuntimeError(
            f"Input order must be a permutation of {STAGES}: "
            f"{input_order}"
        )

    verify_inputs()

    retriever = load_formal_retriever()

    candidate_tables = {}
    count_tables = {}

    for stage, root in (
        ("formal", FORMAL),
        ("high_recall", HIGH),
    ):
        candidate_fields, candidates = read_tsv(
            root / "candidate_records.tsv"
        )

        count_fields, counts = read_tsv(
            root / "search_counts.tsv"
        )

        candidate_tables[stage] = (
            candidate_fields,
            candidates,
        )

        count_tables[stage] = (
            count_fields,
            counts,
        )

    formal_candidate_fields = candidate_tables["formal"][0]
    high_candidate_fields = candidate_tables["high_recall"][0]

    if formal_candidate_fields != high_candidate_fields:
        raise RuntimeError(
            "Candidate schemas differ between frozen inputs"
        )

    if formal_candidate_fields != CANDIDATE_REQUIRED:
        raise RuntimeError(
            "Unexpected frozen candidate schema: "
            f"{formal_candidate_fields}"
        )

    formal_count_fields = count_tables["formal"][0]
    high_count_fields = count_tables["high_recall"][0]

    if formal_count_fields != high_count_fields:
        raise RuntimeError(
            "Search-count schemas differ between frozen inputs"
        )

    if formal_count_fields != SEARCH_COUNT_REQUIRED:
        raise RuntimeError(
            "Unexpected frozen search-count schema: "
            f"{formal_count_fields}"
        )

    merged_candidates: list[dict[str, str]] = []

    for stage in input_order:
        for original in candidate_tables[stage][1]:
            row = dict(original)
            row["search_stage"] = stage

            if row["source"] not in ALLOWED_SOURCES:
                raise RuntimeError(
                    f"Unknown source encountered: "
                    f"{row['source']!r}"
                )

            merged_candidates.append(row)

    if len(merged_candidates) != EXPECTED_CANDIDATE_ROWS:
        raise RuntimeError(
            "Unexpected merged candidate-row count: "
            f"{len(merged_candidates):,}; "
            f"expected {EXPECTED_CANDIDATE_ROWS:,}"
        )

    candidate_fields = [
        "search_stage",
        *formal_candidate_fields,
    ]

    # Stable canonical output order independent of concatenation order.
    merged_candidates.sort(
        key=lambda row: candidate_output_sort_key(
            row,
            retriever,
            formal_candidate_fields,
        )
    )

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in merged_candidates:
        groups[retriever.dedup_key(row)].append(row)

    if len(groups) != EXPECTED_DEDUPLICATED_ROWS:
        raise RuntimeError(
            "Unexpected merged deduplication-key count: "
            f"{len(groups):,}; "
            f"expected {EXPECTED_DEDUPLICATED_ROWS:,}"
        )

    deduplicated: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []

    for key in sorted(groups):
        group = groups[key]

        ordered = sorted(
            group,
            key=lambda row: representative_sort_key(
                row,
                retriever,
            ),
        )

        exemplar = ordered[0]

        doi = next(
            (
                row["doi"]
                for row in ordered
                if row["doi"]
            ),
            "",
        )

        pmid = next(
            (
                row["pmid"]
                for row in ordered
                if row["pmid"]
            ),
            "",
        )

        year = next(
            (
                row["year"]
                for row in ordered
                if row["year"]
            ),
            "",
        )

        search_stages = sorted_unique(
            row["search_stage"]
            for row in group
        )

        sources = sorted_unique(
            row["source"]
            for row in group
        )

        query_ids = sorted_unique(
            row["query_id"]
            for row in group
        )

        query_families = sorted_unique(
            row["query_family"]
            for row in group
        )

        stage_query_ids = sorted_unique(
            f"{row['search_stage']}:{row['query_id']}"
            for row in group
        )

        source_record_ids = sorted_unique(
            f"{row['source']}:{row['source_record_id']}"
            for row in group
        )

        dedup_row = {
            "dedup_key": key,
            "entity_type": exemplar["entity_type"],
            "title_or_name": exemplar["title_or_name"],
            "year": year,
            "doi": doi,
            "pmid": pmid,
            "search_stages": search_stages,
            "sources": sources,
            "query_ids": query_ids,
            "query_families": query_families,
            "stage_query_ids": stage_query_ids,
            "source_record_ids": source_record_ids,
        }

        deduplicated.append(dedup_row)

        # Validate that all candidate provenance is represented.
        expected_provenance = {
            "search_stages": search_stages,
            "sources": sources,
            "query_ids": query_ids,
            "query_families": query_families,
            "stage_query_ids": stage_query_ids,
            "source_record_ids": source_record_ids,
        }

        for field, expected in expected_provenance.items():
            if dedup_row[field] != expected:
                raise RuntimeError(
                    f"Provenance loss for {key}: {field}"
                )

        for field in CONFLICT_FIELDS:
            values = sorted({
                row[field]
                for row in group
                if row[field]
            })

            if len(values) > 1:
                conflicts.append({
                    "dedup_key": key,
                    "field": field,
                    "value_count": str(len(values)),
                    "values_json": json.dumps(
                        values,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    "search_stages": search_stages,
                    "sources": sources,
                })

    if len(deduplicated) != EXPECTED_DEDUPLICATED_ROWS:
        raise RuntimeError(
            "Unexpected merged deduplicated-row count"
        )

    dedup_keys = [
        row["dedup_key"]
        for row in deduplicated
    ]

    if len(dedup_keys) != len(set(dedup_keys)):
        raise RuntimeError(
            "Duplicate deduplication key in merged output"
        )

    conflicts.sort(
        key=lambda row: (
            row["dedup_key"],
            row["field"],
        )
    )

    merged_counts: list[dict[str, str]] = []

    for stage in input_order:
        for original in count_tables[stage][1]:
            row = dict(original)
            row["search_stage"] = stage

            if row["source"] not in ALLOWED_SOURCES:
                raise RuntimeError(
                    "Unknown source in search counts: "
                    f"{row['source']!r}"
                )

            merged_counts.append(row)

    merged_counts.sort(
        key=lambda row: (
            STAGE_OUTPUT_PRIORITY[row["search_stage"]],
            row["source"],
            row["query_id"],
            row["query_family"],
        )
    )

    if len(merged_counts) != EXPECTED_SEARCH_COUNT_ROWS:
        raise RuntimeError(
            "Unexpected merged search-count row count: "
            f"{len(merged_counts):,}; "
            f"expected {EXPECTED_SEARCH_COUNT_ROWS:,}"
        )

    count_keys = [
        (
            row["search_stage"],
            row["source"],
            row["query_id"],
        )
        for row in merged_counts
    ]

    if len(count_keys) != len(set(count_keys)):
        raise RuntimeError(
            "Duplicate stage/source/query search-count row"
        )

    expected_by_pull = Counter(
        (
            row["search_stage"],
            row["source"],
            row["query_id"],
        )
        for row in merged_candidates
    )

    retrieved_total = 0

    for row in merged_counts:
        key = (
            row["search_stage"],
            row["source"],
            row["query_id"],
        )

        retrieved = int(row["retrieved_count"])
        reported = int(row["reported_count"])

        if row["complete"] != "True":
            raise RuntimeError(
                f"Incomplete frozen source-query pull: {key}"
            )

        if reported != retrieved:
            raise RuntimeError(
                f"Reported/retrieved mismatch: {key}"
            )

        if expected_by_pull[key] != retrieved:
            raise RuntimeError(
                f"Candidate/search-count mismatch for {key}: "
                f"{expected_by_pull[key]} versus {retrieved}"
            )

        retrieved_total += retrieved

    if retrieved_total != EXPECTED_CANDIDATE_ROWS:
        raise RuntimeError(
            "Merged search-count total does not equal "
            "candidate-row count"
        )

    conflict_keys = {
        row["dedup_key"]
        for row in conflicts
    }

    formal_manifest = json.loads(
        (FORMAL / "retrieval_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    high_manifest = json.loads(
        (HIGH / "retrieval_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    manifest = {
        "schema_version": 1,
        "experiment":
            "07_comparative_landscape_merged_search_universe",
        "status": "COMPLETE",
        "screening_performed": False,
        "eligibility_decisions_made": False,
        "capability_classification_performed": False,
        "identity_rule":
            "frozen retrieval dedup_key implementation",
        "search_stages": list(STAGES),
        "candidate_record_rows":
            len(merged_candidates),
        "deduplicated_record_rows":
            len(deduplicated),
        "metadata_conflict_rows":
            len(conflicts),
        "metadata_conflict_keys":
            len(conflict_keys),
        "search_count_rows":
            len(merged_counts),
        "merge_spec_sha256":
            sha256_file(MERGE_SPEC),
        "merge_script_sha256":
            sha256_file(Path(__file__).resolve()),
        "inputs": {
            "formal": {
                "candidate_records_sha256":
                    sha256_file(
                        FORMAL / "candidate_records.tsv"
                    ),
                "deduplicated_records_sha256":
                    sha256_file(
                        FORMAL / "deduplicated_records.tsv"
                    ),
                "retrieval_manifest_sha256":
                    sha256_file(
                        FORMAL / "retrieval_manifest.json"
                    ),
                "search_counts_sha256":
                    sha256_file(
                        FORMAL / "search_counts.tsv"
                    ),
                "repository_commit":
                    formal_manifest.get(
                        "repository_commit"
                    ),
                "retrieval_script_sha256":
                    formal_manifest.get(
                        "retrieval_script_sha256"
                    ),
                "search_queries_sha256":
                    formal_manifest.get(
                        "search_queries_sha256"
                    ),
            },
            "high_recall": {
                "candidate_records_sha256":
                    sha256_file(
                        HIGH / "candidate_records.tsv"
                    ),
                "deduplicated_records_sha256":
                    sha256_file(
                        HIGH / "deduplicated_records.tsv"
                    ),
                "retrieval_manifest_sha256":
                    sha256_file(
                        HIGH / "retrieval_manifest.json"
                    ),
                "search_counts_sha256":
                    sha256_file(
                        HIGH / "search_counts.tsv"
                    ),
                "repository_commit":
                    high_manifest.get(
                        "repository_commit"
                    ),
                "retrieval_script_sha256":
                    high_manifest.get(
                        "retrieval_script_sha256"
                    ),
                "search_queries_sha256":
                    high_manifest.get(
                        "search_queries_sha256"
                    ),
            },
        },
    }

    return {
        "candidate_fields": candidate_fields,
        "candidate_rows": merged_candidates,
        "deduplicated_fields": DEDUPLICATED_FIELDS,
        "deduplicated_rows": deduplicated,
        "conflict_fields": CONFLICT_OUTPUT_FIELDS,
        "conflict_rows": conflicts,
        "search_count_fields": [
            "search_stage",
            *formal_count_fields,
        ],
        "search_count_rows": merged_counts,
        "manifest": manifest,
    }


def write_outputs(result: dict, output: Path) -> None:
    if output.exists():
        raise RuntimeError(
            f"Output directory already exists: {output}"
        )

    output.mkdir(parents=True)

    write_tsv(
        output / "candidate_records.tsv",
        result["candidate_fields"],
        result["candidate_rows"],
    )

    write_tsv(
        output / "deduplicated_records.tsv",
        result["deduplicated_fields"],
        result["deduplicated_rows"],
    )

    write_tsv(
        output / "metadata_conflicts.tsv",
        result["conflict_fields"],
        result["conflict_rows"],
    )

    write_tsv(
        output / "search_counts.tsv",
        result["search_count_fields"],
        result["search_count_rows"],
    )

    (output / "merge_manifest.json").write_text(
        json.dumps(
            result["manifest"],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    checksum_names = [
        "candidate_records.tsv",
        "deduplicated_records.tsv",
        "metadata_conflicts.tsv",
        "search_counts.tsv",
        "merge_manifest.json",
    ]

    with (output / "checksums.sha256").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        for name in checksum_names:
            fh.write(
                f"{sha256_file(output / name)}  {name}\n"
            )

    verify_sha256_manifest(
        output,
        output / "checksums.sha256",
    )


def validate_written_output(output: Path) -> None:
    verify_sha256_manifest(
        output,
        output / "checksums.sha256",
    )

    candidate_fields, candidates = read_tsv(
        output / "candidate_records.tsv"
    )

    dedup_fields, deduplicated = read_tsv(
        output / "deduplicated_records.tsv"
    )

    _, counts = read_tsv(
        output / "search_counts.tsv"
    )

    manifest = json.loads(
        (output / "merge_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    if candidate_fields != [
        "search_stage",
        *CANDIDATE_REQUIRED,
    ]:
        raise RuntimeError(
            "Written candidate schema is incorrect"
        )

    if dedup_fields != DEDUPLICATED_FIELDS:
        raise RuntimeError(
            "Written deduplicated schema is incorrect"
        )

    if len(candidates) != EXPECTED_CANDIDATE_ROWS:
        raise RuntimeError(
            "Written candidate count is incorrect"
        )

    if len(deduplicated) != EXPECTED_DEDUPLICATED_ROWS:
        raise RuntimeError(
            "Written deduplicated count is incorrect"
        )

    if len(counts) != EXPECTED_SEARCH_COUNT_ROWS:
        raise RuntimeError(
            "Written search-count count is incorrect"
        )

    keys = [
        row["dedup_key"]
        for row in deduplicated
    ]

    if len(keys) != len(set(keys)):
        raise RuntimeError(
            "Written deduplicated output contains "
            "duplicate keys"
        )

    if manifest["candidate_record_rows"] != len(candidates):
        raise RuntimeError(
            "Manifest candidate count mismatch"
        )

    if manifest["deduplicated_record_rows"] != len(deduplicated):
        raise RuntimeError(
            "Manifest deduplicated count mismatch"
        )


def build_and_write(
    output: Path,
    input_order: tuple[str, str] = STAGES,
) -> None:
    result = build_merged(input_order=input_order)
    write_outputs(result, output)
    validate_written_output(output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build the frozen Experiment 07 merged search universe."
        )
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    args = parser.parse_args()

    build_and_write(
        args.output,
        input_order=("formal", "high_recall"),
    )

    manifest = json.loads(
        (args.output / "merge_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    print("PASS | merged search universe complete")
    print(
        "candidate rows    = "
        f"{manifest['candidate_record_rows']:,}"
    )
    print(
        "deduplicated rows = "
        f"{manifest['deduplicated_record_rows']:,}"
    )
    print(
        "conflict keys     = "
        f"{manifest['metadata_conflict_keys']:,}"
    )
    print(
        "conflict rows     = "
        f"{manifest['metadata_conflict_rows']:,}"
    )
    print(
        "search-count rows = "
        f"{manifest['search_count_rows']:,}"
    )
    print(f"output            = {args.output}")


if __name__ == "__main__":
    main()
