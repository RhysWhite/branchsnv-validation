#!/usr/bin/env python3

from __future__ import annotations

import copy
from pathlib import Path

import screening_entity_identity as identity
import cross_stage_screening_entities as cross
import build_metadata_resolution_queue as queue


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent


def component(
    cid,
    *,
    reasons,
    doi=(),
    pmid=(),
    openalex=(),
    omid=(),
    database_sources=(),
    citation_sources=(),
):
    return {
        "screening_component_id": cid,
        "screening_entity_class": "publication",
        "database_entity_keys": [],
        "citation_entity_keys": [],
        "cross_stage_link_bases": [],
        "doi_values": list(doi),
        "pmid_values": list(pmid),
        "openalex_id_values": list(openalex),
        "omid_values": list(omid),
        "titles": [],
        "years": [],
        "database_identity_statuses": [],
        "citation_identity_statuses": [],
        "database_source_record_ids":
            list(database_sources),
        "citation_source_record_ids":
            list(citation_sources),
        "cross_stage_conflict_keys": [],
        "attention_reasons": list(reasons),
        "identity_attention": any(
            reason != "missing_title"
            for reason in reasons
        ),
        "metadata_attention":
            "missing_title" in reasons,
    }


def universe(*components):
    return {
        "publication_components":
            list(components),

        "software_registry_components":
            [],
    }


# Native OpenAlex provider identity.
x = queue.build_queue(
    universe(
        component(
            "c1",
            reasons=(
                "provider_specific_unresolved",
                "missing_title",
            ),
            openalex=("W1",),
            citation_sources=(
                "openalex:W1",
            ),
        )
    )
)

assert x["summary"][
    "logical_lookup_keys"
] == 1

assert x["assignments"][0][
    "policy_class"
] == "native_provider_identity"

assert x["lookups"][0][
    "route"
] == "work_by_openalex_id"

print(
    "PASS | OpenAlex provider identity uses native Work ID"
)


# Native OpenCitations title must not switch to PubMed merely
# because PMID exists.
x = queue.build_queue(
    universe(
        component(
            "c2",
            reasons=("missing_title",),
            doi=("10.1/a",),
            pmid=("123",),
            omid=("br/01",),
            citation_sources=(
                "opencitations:10.1/a",
            ),
        )
    )
)

assert len(x["assignments"]) == 1
assert x["assignments"][0][
    "provider"
] == "opencitations_meta"
assert x["assignments"][0][
    "route"
] == "metadata_by_omid"

print(
    "PASS | OpenCitations-native title evidence does not switch to PubMed"
)


# Dual native title provenance retains both.
x = queue.build_queue(
    universe(
        component(
            "c3",
            reasons=("missing_title",),
            doi=("10.1/b",),
            openalex=("W3",),
            omid=("br/03",),
            citation_sources=(
                "openalex:W3",
                "opencitations:10.1/b",
            ),
        )
    )
)

assert len(x["assignments"]) == 2

assert {
    row["provider"]
    for row in x["assignments"]
} == {
    "openalex",
    "opencitations_meta",
}

print(
    "PASS | dual-native title evidence retains both exact routes"
)


# Conflict collects all applicable exact evidence.
x = queue.build_queue(
    universe(
        component(
            "c4",
            reasons=(
                "citation_identity_conflict",
            ),
            doi=("10.1/c",),
            pmid=("456",),
            openalex=("W4",),
            omid=("br/04",),
            citation_sources=(
                "openalex:W4",
                "opencitations:10.1/c",
            ),
        )
    )
)

assert len(x["assignments"]) == 6

assert {
    (
        row["provider"],
        row["route"],
    )
    for row in x["assignments"]
} == {
    ("openalex", "work_by_openalex_id"),
    ("openalex", "work_by_doi"),
    ("openalex", "work_by_pmid"),
    ("opencitations_meta", "metadata_by_doi"),
    ("opencitations_meta", "metadata_by_omid"),
    ("pubmed", "record_by_pmid"),
}

print(
    "PASS | conflict queue retains all exact evidence routes"
)


# Shared lookup does not merge components.
x = queue.build_queue(
    universe(
        component(
            "c5a",
            reasons=(
                "provider_specific_unresolved",
            ),
            openalex=("W5",),
            citation_sources=(
                "openalex:W5",
            ),
        ),
        component(
            "c5b",
            reasons=(
                "database_identity_conflict",
            ),
            doi=("10.1/d",),
            openalex=("W5",),
            database_sources=(
                "openalex:W5",
            ),
        ),
    )
)

shared = [
    row
    for row in x["lookups"]
    if row["component_count"] == 2
]

assert len(shared) == 1
assert shared[0][
    "identifier"
] == "W5"

assert len(x["components"]) == 2

print(
    "PASS | shared evidence lookup does not merge components"
)


# Input component ordering cannot affect normalized result.
u = universe(
    component(
        "c6a",
        reasons=("missing_title",),
        openalex=("W6",),
        citation_sources=(
            "openalex:W6",
        ),
    ),
    component(
        "c6b",
        reasons=(
            "provider_specific_unresolved",
        ),
        omid=("br/06",),
        citation_sources=(
            "opencitations:foo",
        ),
    ),
)

forward = queue.build_queue(u)

reverse = copy.deepcopy(u)
reverse[
    "publication_components"
] = list(reversed(
    reverse[
        "publication_components"
    ]
))

backward = queue.build_queue(
    reverse
)

assert queue.canonical_hash(
    forward
) == queue.canonical_hash(
    backward
)

print(
    "PASS | queue construction is order-independent"
)


# Complete frozen corpus regression.
database = (
    identity.build_database_screening_entities(
        identity.read_tsv(
            REPO
            / "results"
            / "07_comparative_landscape"
            / "merged_search_universe"
            / "deduplicated_records.tsv"
        )
    )
)

citation = (
    identity.build_citation_publication_entities(
        identity.read_tsv(
            REPO
            / "results"
            / "07_comparative_landscape"
            / "citation_wave_0"
            / "neighbour_records.tsv"
        )
    )
)

cross_stage = (
    cross.build_cross_stage_screening_universe(
        database,
        citation,
    )
)

x = queue.build_queue(
    cross_stage
)

s = x["summary"]

assert s[
    "attention_components"
] == 1342

assert s[
    "component_evidence_assignments"
] == 1847

assert s[
    "logical_lookup_keys"
] == 1731

assert s[
    "policy_counts"
] == {
    "conflict_all_exact_evidence":
        621,

    "native_provider_identity":
        502,

    "native_title_evidence":
        724,
}

assert s[
    "logical_lookup_provider_counts"
] == {
    "openalex": 1169,
    "opencitations_meta": 495,
    "pubmed": 67,
}

assert s[
    "logical_lookup_route_counts"
] == {
    "openalex|work_by_doi":
        115,

    "openalex|work_by_openalex_id":
        987,

    "openalex|work_by_pmid":
        67,

    "opencitations_meta|metadata_by_doi":
        115,

    "opencitations_meta|metadata_by_omid":
        380,

    "pubmed|record_by_pmid":
        67,
}

assert s[
    "question_counts"
] == {
    "adjudicate_identifier_conflict":
        117,

    "recover_title":
        1067,

    "resolve_provider_identity":
        502,
}

assert s[
    "question_combination_counts"
] == {
    "adjudicate_identifier_conflict":
        107,

    "adjudicate_identifier_conflict|recover_title":
        10,

    "recover_title":
        723,

    "resolve_provider_identity":
        168,

    "resolve_provider_identity|recover_title":
        334,
}

assert s[
    "shared_logical_lookup_keys"
] == 116

assert s[
    "shared_policy_combination_counts"
] == {
    "conflict_all_exact_evidence":
        115,

    "conflict_all_exact_evidence|native_provider_identity":
        1,
}

assert s[
    "title_only_components"
] == 723

assert s[
    "title_native_route_multiplicity"
] == {
    "1": 722,
    "2": 1,
}

assert len(
    x["components"]
) == 1342

assert len(
    x["assignments"]
) == 1847

assert len(
    x["lookups"]
) == 1731

print(
    "PASS | frozen queue regression baseline"
)

print(
    "INFO | components = 1,342"
)

print(
    "INFO | assignments = 1,847"
)

print(
    "INFO | logical lookup keys = 1,731"
)

print(
    "PASS | all metadata-resolution queue tests"
)
