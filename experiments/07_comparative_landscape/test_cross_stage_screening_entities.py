#!/usr/bin/env python3

from __future__ import annotations

import copy

from pathlib import Path

import screening_entity_identity as identity
import cross_stage_screening_entities as cross


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent


def db_row(
    *,
    key,
    entity_type="publication",
    title="Database title",
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


def citation_row(
    *,
    source="openalex",
    direction="forward",
    doi="",
    pmid="",
    openalex_id="",
    omid="",
    title="",
    year="",
    source_record_id=None,
    anchor_id="W0A01",
):
    if source_record_id is None:
        source_record_id = (
            openalex_id
            or omid
            or doi
            or pmid
        )

    return {
        "wave": "0",
        "anchor_id": anchor_id,
        "anchor_tool": "Synthetic",
        "source": source,
        "direction": direction,
        "doi": doi,
        "pmid": pmid,
        "openalex_id": openalex_id,
        "omid": omid,
        "title": title,
        "year": year,
        "source_record_id":
            source_record_id,
    }


def build(
    db_rows,
    citation_rows,
):
    return (
        cross.build_cross_stage_screening_universe(
            identity.build_database_screening_entities(
                db_rows
            ),
            identity.build_citation_publication_entities(
                citation_rows
            ),
        )
    )


# ------------------------------------------------------------
# Exact DOI cross-stage linkage.
# ------------------------------------------------------------

result = build(
    [
        db_row(
            key="doi:10.1/a",
            doi="10.1/a",
            pmid="100",
            title="A",
        ),
    ],
    [
        citation_row(
            doi="10.1/a",
            pmid="100",
            openalex_id="W1",
            title="A",
        ),
    ],
)

assert result[
    "automatic_link_count"
] == 1

assert result[
    "automatic_link_basis_counts"
] == {
    "exact_doi": 1,
}

assert result[
    "publication_component_count"
] == 1

print(
    "PASS | exact DOI links cross-stage"
)


# ------------------------------------------------------------
# DOI-less unique PMID linkage.
# ------------------------------------------------------------

result = build(
    [
        db_row(
            key="doi:10.1/b",
            doi="10.1/b",
            pmid="200",
        ),
    ],
    [
        citation_row(
            source="opencitations",
            pmid="200",
            omid="br/200",
        ),
    ],
)

assert result[
    "automatic_link_basis_counts"
] == {
    "exact_unique_pmid": 1,
}

print(
    "PASS | DOI-less exact unique PMID links cross-stage"
)


# ------------------------------------------------------------
# Safe many-to-one: DOI-only and PMID-only citation identities
# both converge on one database publication.
# ------------------------------------------------------------

result = build(
    [
        db_row(
            key="doi:10.1/c",
            doi="10.1/c",
            pmid="300",
            title="C",
        ),
    ],
    [
        citation_row(
            source="opencitations",
            doi="10.1/c",
            omid="br/doi",
        ),
        citation_row(
            source="opencitations",
            pmid="300",
            omid="br/pmid",
        ),
    ],
)

assert result[
    "automatic_link_count"
] == 2

assert result[
    "unique_database_publications_linked"
] == 1

assert result[
    "database_publications_with_multiple_citation_links"
] == 1

assert result[
    "publication_component_count"
] == 1

print(
    "PASS | safe many-to-one citation convergence"
)


# ------------------------------------------------------------
# DOI vs PMID disagreement does not auto-link.
# ------------------------------------------------------------

result = build(
    [
        db_row(
            key="doi:10.1/d",
            doi="10.1/d",
            pmid="400",
        ),
        db_row(
            key="doi:10.1/e",
            doi="10.1/e",
            pmid="401",
        ),
    ],
    [
        citation_row(
            doi="10.1/d",
            pmid="401",
            openalex_id="W4",
        ),
    ],
)

assert result[
    "automatic_link_count"
] == 0

assert result[
    "cross_stage_conflict_types"
] == {
    "doi_and_pmid_cross_stage_disagreement":
        1,
}

assert result[
    "publication_component_count"
] == 3

print(
    "PASS | DOI/PMID disagreement remains unmerged"
)


# ------------------------------------------------------------
# Citation DOI absent from database but PMID points to DB DOI.
# Must remain a separate conflict-held cross-stage component.
# ------------------------------------------------------------

result = build(
    [
        db_row(
            key="doi:10.1/f",
            doi="10.1/f",
            pmid="500",
        ),
    ],
    [
        citation_row(
            doi="10.1/g",
            pmid="500",
            openalex_id="W5",
        ),
    ],
)

assert result[
    "automatic_link_count"
] == 0

assert result[
    "cross_stage_conflict_types"
] == {
    "citation_doi_absent_from_database_but_pmid_links_database_entity":
        1,
}

assert result[
    "publication_component_count"
] == 2

print(
    "PASS | absent DOI cannot be replaced by PMID-linked DB DOI"
)


# ------------------------------------------------------------
# DOI-less PMID pointing to multiple DB DOI groups is not linked.
# ------------------------------------------------------------

result = build(
    [
        db_row(
            key="doi:10.1/h",
            doi="10.1/h",
            pmid="600",
        ),
        db_row(
            key="doi:10.1/i",
            doi="10.1/i",
            pmid="600",
        ),
    ],
    [
        citation_row(
            source="opencitations",
            pmid="600",
            omid="br/600",
        ),
    ],
)

assert result[
    "automatic_link_count"
] == 0

assert result[
    "cross_stage_conflict_types"
] == {
    "pmid_maps_multiple_database_entities":
        1,
}

print(
    "PASS | PMID cannot bridge multiple database DOI identities"
)


# ------------------------------------------------------------
# Citation title rescues linked database-titleless publication.
# ------------------------------------------------------------

result = build(
    [
        db_row(
            key="doi:10.1/j",
            doi="10.1/j",
            pmid="700",
            title="",
        ),
    ],
    [
        citation_row(
            doi="10.1/j",
            pmid="700",
            openalex_id="W7",
            title="Citation title",
        ),
    ],
)

assert result[
    "initial_titleless_database_publications"
] == 1

assert result[
    "titleless_database_publications_receiving_link"
] == 1

assert result[
    "titleless_database_publications_rescued"
] == 1

assert result[
    "publication_components_missing_title"
] == 0

print(
    "PASS | citation metadata can rescue linked database title"
)


# ------------------------------------------------------------
# Database title rescues titleless citation identity.
# ------------------------------------------------------------

result = build(
    [
        db_row(
            key="doi:10.1/k",
            doi="10.1/k",
            pmid="800",
            title="Database title",
        ),
    ],
    [
        citation_row(
            source="opencitations",
            doi="10.1/k",
            omid="br/800",
            title="",
        ),
    ],
)

assert result[
    "initial_titleless_citation_entities"
] == 1

assert result[
    "titleless_citation_entities_receiving_link"
] == 1

assert result[
    "titleless_citation_entities_rescued"
] == 1

assert result[
    "publication_components_missing_title"
] == 0

print(
    "PASS | database metadata rescues linked citation title"
)


# ------------------------------------------------------------
# Software registry remains independent of matching publication.
# ------------------------------------------------------------

result = build(
    [
        db_row(
            key="biotools:test",
            entity_type="software_registry",
            title="Test",
            doi="10.1/l",
            pmid="900",
            sources="biotools",
        ),
        db_row(
            key="doi:10.1/l",
            doi="10.1/l",
            pmid="900",
        ),
    ],
    [
        citation_row(
            doi="10.1/l",
            pmid="900",
            openalex_id="W9",
        ),
    ],
)

assert result[
    "publication_component_count"
] == 1

assert result[
    "software_registry_component_count"
] == 1

assert result[
    "screening_component_count"
] == 2

print(
    "PASS | software-registry component remains independent"
)


# ------------------------------------------------------------
# Conflict state survives an otherwise-safe exact DOI link.
# ------------------------------------------------------------

citation_conflict_rows = [
    citation_row(
        doi="10.1/m",
        pmid="1000",
        openalex_id="W10",
        source_record_id="a",
    ),
    citation_row(
        doi="10.1/m",
        pmid="1001",
        openalex_id="W10",
        source_record_id="b",
    ),
]

result = build(
    [
        db_row(
            key="doi:10.1/m",
            doi="10.1/m",
            pmid="1001",
        ),
    ],
    citation_conflict_rows,
)

assert result[
    "automatic_link_count"
] == 1

component = result[
    "publication_components"
][0]

assert (
    "citation_identity_conflict"
    in component[
        "attention_reasons"
    ]
)

print(
    "PASS | exact DOI link does not erase citation conflict state"
)


# ------------------------------------------------------------
# Input entity ordering cannot alter output.
# ------------------------------------------------------------

db_rows = [
    db_row(
        key="doi:10.1/n",
        doi="10.1/n",
        pmid="1100",
    ),
    db_row(
        key="biotools:n",
        entity_type="software_registry",
        title="N",
        sources="biotools",
    ),
]

citation_rows = [
    citation_row(
        doi="10.1/n",
        openalex_id="W11",
    ),
    citation_row(
        openalex_id="W12",
    ),
]

db_identity = (
    identity.build_database_screening_entities(
        db_rows
    )
)

citation_identity = (
    identity.build_citation_publication_entities(
        citation_rows
    )
)

forward = (
    cross.build_cross_stage_screening_universe(
        db_identity,
        citation_identity,
    )
)

reverse_db = copy.deepcopy(
    db_identity
)

reverse_citation = copy.deepcopy(
    citation_identity
)

reverse_db[
    "entities"
] = list(
    reversed(
        reverse_db[
            "entities"
        ]
    )
)

reverse_citation[
    "entities"
] = list(
    reversed(
        reverse_citation[
            "entities"
        ]
    )
)

reverse = (
    cross.build_cross_stage_screening_universe(
        reverse_db,
        reverse_citation,
    )
)

assert (
    cross.result_bytes(
        forward
    )
    ==
    cross.result_bytes(
        reverse
    )
)

print(
    "PASS | cross-stage construction is order-independent"
)


# ------------------------------------------------------------
# Complete frozen-data regression.
# ------------------------------------------------------------

database_rows = identity.read_tsv(
    REPO
    / "results"
    / "07_comparative_landscape"
    / "merged_search_universe"
    / "deduplicated_records.tsv"
)

citation_rows = identity.read_tsv(
    REPO
    / "results"
    / "07_comparative_landscape"
    / "citation_wave_0"
    / "neighbour_records.tsv"
)

database_identity = (
    identity.build_database_screening_entities(
        database_rows
    )
)

citation_identity = (
    identity.build_citation_publication_entities(
        citation_rows
    )
)

result = (
    cross.build_cross_stage_screening_universe(
        database_identity,
        citation_identity,
    )
)

assert result[
    "database_input_entity_count"
] == 79762

assert result[
    "citation_input_entity_count"
] == 17605

assert result[
    "automatic_link_count"
] == 2254

assert result[
    "automatic_link_basis_counts"
] == {
    "exact_doi": 2251,
    "exact_unique_pmid": 3,
}

assert result[
    "unique_database_publications_linked"
] == 2252

assert result[
    "database_publications_with_multiple_citation_links"
] == 2

assert result[
    "cross_stage_conflict_count"
] == 4

assert result[
    "cross_stage_conflict_types"
] == {
    "citation_doi_absent_from_database_but_pmid_links_database_entity":
        2,

    "doi_and_pmid_cross_stage_disagreement":
        2,
}

assert result[
    "citation_entities_without_cross_stage_link"
] == 15347

assert result[
    "publication_component_count"
] == 94898

assert result[
    "software_registry_component_count"
] == 215

assert result[
    "screening_component_count"
] == 95113

assert result[
    "initial_titleless_database_publications"
] == 390

assert result[
    "titleless_database_publications_receiving_link"
] == 0

assert result[
    "titleless_database_publications_rescued"
] == 0

assert result[
    "initial_titleless_citation_entities"
] == 747

assert result[
    "titleless_citation_entities_receiving_link"
] == 70

assert result[
    "titleless_citation_entities_rescued"
] == 70

assert result[
    "publication_components_missing_title"
] == 1067

assert result[
    "publication_components_requiring_identity_attention"
] == 619

assert result[
    "publication_components_requiring_any_attention"
] == 1342

assert result[
    "software_registry_components_requiring_attention"
] == 0

assert result[
    "screening_components_requiring_any_attention"
] == 1342

assert result[
    "attention_reason_combinations"
] == {
    "citation_identity_conflict":
        58,

    "citation_identity_conflict|cross_stage_conflict_citation_side":
        1,

    "citation_identity_conflict|cross_stage_conflict_database_side":
        1,

    "citation_identity_conflict|missing_title":
        9,

    "cross_stage_conflict_citation_side":
        2,

    "cross_stage_conflict_citation_side|missing_title":
        1,

    "cross_stage_conflict_database_side":
        5,

    "database_identity_conflict":
        40,

    "missing_title":
        723,

    "provider_specific_unresolved":
        168,

    "provider_specific_unresolved|missing_title":
        334,
}

# Every frozen identity entity is represented exactly once
# in the resulting component layer.
represented_db = [
    key
    for component
    in (
        result[
            "publication_components"
        ]
        + result[
            "software_registry_components"
        ]
    )
    for key
    in component[
        "database_entity_keys"
    ]
]

represented_citation = [
    key
    for component
    in result[
        "publication_components"
    ]
    for key
    in component[
        "citation_entity_keys"
    ]
]

assert len(
    represented_db
) == len(set(
    represented_db
)) == 79762

assert len(
    represented_citation
) == len(set(
    represented_citation
)) == 17605

print(
    "PASS | frozen cross-stage regression baseline"
)

print(
    "INFO | automatic links = 2,254"
)

print(
    "INFO | cross-stage conflicts = 4"
)

print(
    "INFO | publication components = 94,898"
)

print(
    "INFO | software-registry components = 215"
)

print(
    "INFO | provisional screening entities = 95,113"
)

print(
    "INFO | identity-attention components = 619"
)

print(
    "INFO | title-attention components = 1,067"
)

print(
    "INFO | union attention set = 1,342"
)

print()
print(
    "PASS | all cross-stage screening-entity tests"
)
