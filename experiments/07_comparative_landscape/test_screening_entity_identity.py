#!/usr/bin/env python3

from __future__ import annotations

import json

from pathlib import Path

import screening_entity_identity as impl


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent


def db_row(
    *,
    key,
    entity_type="publication",
    title="Example",
    year="2020",
    doi="",
    pmid="",
    sources="openalex",
):
    return {
        "dedup_key": key,
        "entity_type": entity_type,
        "title_or_name": title,
        "year": year,
        "doi": doi,
        "pmid": pmid,
        "search_stages": "formal",
        "sources": sources,
        "query_ids": "Q01",
        "query_families": "test",
        "stage_query_ids": "formal:Q01",
        "source_record_ids":
            f"{sources}:{key}",
    }


def keyed(result):
    return {
        row["provisional_entity_key"]: row
        for row in result["entities"]
    }


# ------------------------------------------------------------
# Synthetic DOI-first identity.
# ------------------------------------------------------------

rows = [
    db_row(
        key="doi:10.1/a",
        doi="10.1/A",
        pmid="100",
    ),
    db_row(
        key="pmid:100",
        pmid="PMID:100",
    ),
]

result = (
    impl.build_database_screening_entities(
        rows
    )
)

entities = keyed(result)

assert list(entities) == [
    "publication:doi:10.1/a"
]

assert (
    entities[
        "publication:doi:10.1/a"
    ]["database_dedup_keys"]
    ==
    [
        "doi:10.1/a",
        "pmid:100",
    ]
)

assert result["identity_conflict_count"] == 0

print(
    "PASS | DOI-less PMID record attaches to unique DOI group"
)


# ------------------------------------------------------------
# Shared PMID must not merge multiple DOI groups.
# ------------------------------------------------------------

rows = [
    db_row(
        key="doi:10.1/a",
        doi="10.1/a",
        pmid="200",
    ),
    db_row(
        key="doi:10.1/b",
        doi="10.1/b",
        pmid="200",
    ),
    db_row(
        key="pmid:200",
        pmid="200",
    ),
]

result = (
    impl.build_database_screening_entities(
        rows
    )
)

entities = keyed(result)

assert {
    "publication:doi:10.1/a",
    "publication:doi:10.1/b",
    "publication:conflict:pmid:200",
} == set(entities)

for key in (
    "publication:doi:10.1/a",
    "publication:doi:10.1/b",
    "publication:conflict:pmid:200",
):
    assert (
        entities[key]["identity_status"]
        == "conflict_hold"
    )

assert result["identity_conflict_count"] == 1

print(
    "PASS | shared PMID cannot bridge multiple DOI groups"
)


# ------------------------------------------------------------
# Identical title/year cannot establish identity.
# ------------------------------------------------------------

rows = [
    db_row(
        key="doi:10.1/c",
        doi="10.1/c",
        title="Same title",
        year="2024",
    ),
    db_row(
        key="doi:10.1/d",
        doi="10.1/d",
        title="Same title",
        year="2024",
    ),
]

result = (
    impl.build_database_screening_entities(
        rows
    )
)

assert result["entity_count"] == 2

print(
    "PASS | title/year equality does not merge DOI groups"
)


# ------------------------------------------------------------
# DOI/PMID-less publication stays under frozen database key.
# ------------------------------------------------------------

rows = [
    db_row(
        key="title:no identifiers|year:2020",
        title="No identifiers",
        year="2020",
    ),
]

result = (
    impl.build_database_screening_entities(
        rows
    )
)

entity = result["entities"][0]

assert entity["provisional_entity_key"] == (
    "publication:database:"
    "title:no identifiers|year:2020"
)

print(
    "PASS | identifier-poor publication preserves frozen-key fallback"
)


# ------------------------------------------------------------
# Registry record remains independent even with publication IDs.
# ------------------------------------------------------------

rows = [
    db_row(
        key="biotools:testtool",
        entity_type="software_registry",
        title="TestTool",
        doi="10.1/tool",
        pmid="300",
        sources="biotools",
    ),
    db_row(
        key="doi:10.1/tool",
        entity_type="publication",
        title="TestTool paper",
        doi="10.1/tool",
        pmid="300",
        sources="pubmed",
    ),
]

result = (
    impl.build_database_screening_entities(
        rows
    )
)

entities = keyed(result)

assert {
    "software_registry:biotools:testtool",
    "publication:doi:10.1/tool",
} == set(entities)

print(
    "PASS | software-registry identity remains independent of publication"
)


# ------------------------------------------------------------
# Input-order independence.
# ------------------------------------------------------------

rows = [
    db_row(
        key="doi:10.1/a",
        doi="10.1/a",
        pmid="100",
    ),
    db_row(
        key="pmid:100",
        pmid="100",
    ),
    db_row(
        key="doi:10.1/b",
        doi="10.1/b",
        pmid="200",
    ),
    db_row(
        key="doi:10.1/c",
        doi="10.1/c",
        pmid="200",
    ),
    db_row(
        key="pmid:200",
        pmid="200",
    ),
    db_row(
        key="biotools:x",
        entity_type="software_registry",
        title="X",
        sources="biotools",
    ),
]

forward = (
    impl.build_database_screening_entities(
        rows
    )
)

reverse = (
    impl.build_database_screening_entities(
        list(reversed(rows))
    )
)

assert (
    impl.result_bytes(forward)
    ==
    impl.result_bytes(reverse)
)

print(
    "PASS | synthetic database identity is order-independent"
)


# ------------------------------------------------------------
# Frozen database smoke/regression test.
# ------------------------------------------------------------

path = (
    REPO
    / "results"
    / "07_comparative_landscape"
    / "merged_search_universe"
    / "deduplicated_records.tsv"
)

real_rows = impl.read_tsv(path)

assert len(real_rows) == 79917

forward = (
    impl.build_database_screening_entities(
        real_rows
    )
)

reverse = (
    impl.build_database_screening_entities(
        list(reversed(real_rows))
    )
)

assert (
    impl.result_bytes(forward)
    ==
    impl.result_bytes(reverse)
)

assert forward["input_row_count"] == 79917

assert (
    forward[
        "software_registry_entity_count"
    ]
    == 215
)

assert (
    sum(
        len(entity["source_row_sha256s"])
        for entity in forward["entities"]
    )
    == 79917
)

print(
    "PASS | frozen 79,917-row database universe preserves every discovery row"
)

print(
    "INFO | derived database screening entities = "
    f"{forward['entity_count']:,}"
)

print(
    "INFO | derived publication entities = "
    f"{forward['publication_entity_count']:,}"
)

print(
    "INFO | software-registry entities = "
    f"{forward['software_registry_entity_count']:,}"
)

print(
    "INFO | conflict-hold entities = "
    f"{forward['conflict_hold_entity_count']:,}"
)

print(
    "INFO | identifier conflicts = "
    f"{forward['identity_conflict_count']:,}"
)

print()
print(
    "PASS | all database screening-entity identity tests"
)
