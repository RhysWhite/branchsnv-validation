#!/usr/bin/env python3
"""
Experiment 07 screening-entity identity implementation.

This module performs identity/provenance construction only.

It does NOT:
- perform HTTP requests;
- enrich metadata;
- screen scientific relevance;
- assign software-landscape eligibility;
- assign analytical role;
- choose canonical method publications; or
- write production results.

The implementation follows the frozen:
- CITATION_PUBLICATION_RECONCILIATION_SPEC.md
- UNIFIED_SCREENING_AND_WAVE_PROMOTION_SPEC.md

Core invariant:
different non-empty DOI values are never automatically merged through
PMID, OpenAlex ID, OMID, title/year, or transitive connectivity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import ast
import re
import json

from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
CITATION_RETRIEVER = ROOT / "retrieve_citation_wave.py"


# ---------------------------------------------------------------------
# Reuse the already-frozen citation identifier normalisation semantics.
# ---------------------------------------------------------------------

FROZEN_NORMALISER_SOURCE_SHA256 = {'normalise_doi': '1c12d0511cae74a9d85991658637464fa5a0f38923bfeaa686f879c1d2fb4165',
 'normalise_omid': 'b5792a3f33169e20b4f7c7912ea77d90c5a3a3f4dba25e19d6ce8ad7516ad07d',
 'normalise_openalex_id': 'f202dcede460a77afd4bcb0810f74b5bd6a5d2c8b933d5a650352fc154e5c9f2',
 'normalise_pmid': '61f2db6fd049506f7b6e8b38dae474f2095ea3360a08e63881fa3d357f07415c'}


def _extract_frozen_function_source(
    source: str,
    tree: ast.Module,
    name: str,
) -> str:
    matches = [
        node
        for node in tree.body
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == name
        )
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one {name!r} definition "
            f"in {CITATION_RETRIEVER}; found {len(matches)}"
        )

    segment = ast.get_source_segment(
        source,
        matches[0],
    )

    if segment is None:
        raise RuntimeError(
            f"Could not recover source for {name!r} "
            f"from {CITATION_RETRIEVER}"
        )

    return segment.strip() + "\n"


def load_citation_normalisers():
    """
    Load only the four frozen pure identifier-normalisation functions.

    The citation retriever is parsed as source; it is not imported or
    executed as a module. Therefore its network-capable retrieval machinery
    is outside this identity implementation's runtime namespace.

    Each extracted function definition must match the source hash frozen when
    this implementation was created.
    """

    source = CITATION_RETRIEVER.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source,
        filename=str(
            CITATION_RETRIEVER
        ),
    )

    names = (
        "normalise_doi",
        "normalise_pmid",
        "normalise_openalex_id",
        "normalise_omid",
    )

    function_sources = {}

    for name in names:
        function_source = (
            _extract_frozen_function_source(
                source,
                tree,
                name,
            )
        )

        actual = hashlib.sha256(
            function_source.encode(
                "utf-8"
            )
        ).hexdigest()

        expected = (
            FROZEN_NORMALISER_SOURCE_SHA256[
                name
            ]
        )

        if actual != expected:
            raise RuntimeError(
                f"Frozen normaliser source drift for {name}: "
                f"{actual} != {expected}"
            )

        function_sources[
            name
        ] = function_source

    isolated_source = (
        "\n\n".join(
            function_sources[name].rstrip()
            for name in names
        )
        + "\n"
    )

    isolated_tree = ast.parse(
        isolated_source,
        filename=(
            str(CITATION_RETRIEVER)
            + "::frozen_normalisers"
        ),
    )

    namespace = {
        "re": re,
    }

    exec(
        compile(
            isolated_tree,
            filename=(
                str(CITATION_RETRIEVER)
                + "::frozen_normalisers"
            ),
            mode="exec",
        ),
        namespace,
        namespace,
    )

    return tuple(
        namespace[name]
        for name in names
    )


(
    normalise_doi,
    normalise_pmid,
    normalise_openalex_id,
    normalise_omid,
) = load_citation_normalisers()


# ---------------------------------------------------------------------
# Generic deterministic helpers.
# ---------------------------------------------------------------------

def canonical_row_json(
    row: dict[str, str],
) -> str:
    return json.dumps(
        {
            str(k): str(v)
            for k, v in row.items()
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def row_sha256(
    row: dict[str, str],
) -> str:
    return hashlib.sha256(
        canonical_row_json(row).encode("utf-8")
    ).hexdigest()


def sorted_nonempty(
    values: Iterable[str],
) -> list[str]:
    return sorted({
        str(value).strip()
        for value in values
        if str(value).strip()
    })


def split_semicolon(
    value: str,
) -> list[str]:
    if not value:
        return []

    return [
        part
        for part in value.split(";")
        if part
    ]


def read_tsv(
    path: Path,
) -> list[dict[str, str]]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as fh:
        return list(
            csv.DictReader(
                fh,
                delimiter="\t",
            )
        )


def result_bytes(
    result: dict,
) -> bytes:
    return (
        json.dumps(
            result,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def assert_provenance_preserved(
    input_rows: list[dict[str, str]],
    entities: list[dict],
) -> None:
    expected = Counter(
        row_sha256(row)
        for row in input_rows
    )

    observed = Counter()

    for entity in entities:
        observed.update(
            entity["source_row_sha256s"]
        )

    if observed != expected:
        missing = expected - observed
        extra = observed - expected

        raise RuntimeError(
            "Provenance preservation failure: "
            f"missing={dict(missing)} "
            f"extra={dict(extra)}"
        )


# ---------------------------------------------------------------------
# Database-universe screening entities.
# ---------------------------------------------------------------------

def build_database_screening_entities(
    rows: list[dict[str, str]],
) -> dict:
    """
    Project frozen merged-search records to provisional screening entities.

    This function does not mutate the frozen database deduplication model.
    Every frozen dedup_key remains provenance.
    """

    required = {
        "dedup_key",
        "entity_type",
        "title_or_name",
        "year",
        "doi",
        "pmid",
        "search_stages",
        "sources",
        "source_record_ids",
    }

    if rows:
        missing = required - set(rows[0])

        if missing:
            raise RuntimeError(
                "Database input missing fields: "
                + ", ".join(sorted(missing))
            )

    prepared = []

    for original in rows:
        row = dict(original)

        entity_type = row["entity_type"].strip()

        if entity_type not in {
            "publication",
            "software_registry",
        }:
            raise RuntimeError(
                f"Unknown database entity_type: {entity_type!r}"
            )

        row["_doi"] = normalise_doi(
            row.get("doi")
        )

        row["_pmid"] = normalise_pmid(
            row.get("pmid")
        )

        row["_row_sha256"] = row_sha256(
            original
        )

        prepared.append(row)

    prepared.sort(
        key=lambda row: (
            row["dedup_key"],
            row["_row_sha256"],
        )
    )

    publications = [
        row
        for row in prepared
        if row["entity_type"] == "publication"
    ]

    registries = [
        row
        for row in prepared
        if row["entity_type"] == "software_registry"
    ]

    # -------------------------------------------------------------
    # DOI-bearing publication identities.
    # -------------------------------------------------------------

    doi_groups: dict[
        str,
        list[dict[str, str]],
    ] = defaultdict(list)

    for row in publications:
        if row["_doi"]:
            doi_groups[
                row["_doi"]
            ].append(row)

    # -------------------------------------------------------------
    # Which DOI groups does each PMID touch?
    # Only publication records participate.
    # -------------------------------------------------------------

    pmid_to_dois: dict[
        str,
        set[str],
    ] = defaultdict(set)

    for row in publications:
        if row["_pmid"] and row["_doi"]:
            pmid_to_dois[
                row["_pmid"]
            ].add(
                row["_doi"]
            )

    ambiguous_pmids = {
        pmid: sorted(dois)
        for pmid, dois in pmid_to_dois.items()
        if len(dois) > 1
    }

    # -------------------------------------------------------------
    # Allocate every publication discovery record to exactly one
    # provisional screening entity.
    # -------------------------------------------------------------

    groups: dict[
        str,
        list[dict[str, str]],
    ] = defaultdict(list)

    identity_basis = {}

    for row in publications:
        doi = row["_doi"]
        pmid = row["_pmid"]

        if doi:
            key = (
                "publication:doi:"
                + doi
            )

            basis = "doi"

        elif pmid:
            linked_dois = pmid_to_dois.get(
                pmid,
                set(),
            )

            if len(linked_dois) == 1:
                only_doi = next(
                    iter(linked_dois)
                )

                key = (
                    "publication:doi:"
                    + only_doi
                )

                basis = (
                    "pmid_attached_to_unique_doi"
                )

            elif len(linked_dois) > 1:
                key = (
                    "publication:conflict:"
                    "pmid:"
                    + pmid
                )

                basis = (
                    "ambiguous_pmid_multiple_doi"
                )

            else:
                key = (
                    "publication:pmid:"
                    + pmid
                )

                basis = "pmid"

        else:
            key = (
                "publication:database:"
                + row["dedup_key"]
            )

            basis = (
                "frozen_database_key_fallback"
            )

        groups[key].append(row)

        identity_basis.setdefault(
            key,
            set(),
        ).add(basis)

    # -------------------------------------------------------------
    # Software-registry identities remain independent.
    # -------------------------------------------------------------

    for row in registries:
        key = (
            "software_registry:"
            + row["dedup_key"]
        )

        groups[key].append(row)

        identity_basis.setdefault(
            key,
            set(),
        ).add(
            "software_registry_identity"
        )

    entities = []

    for key in sorted(groups):
        group = sorted(
            groups[key],
            key=lambda row: (
                row["dedup_key"],
                row["_row_sha256"],
            ),
        )

        classes = {
            row["entity_type"]
            for row in group
        }

        if len(classes) != 1:
            raise RuntimeError(
                f"Mixed entity classes in {key}: "
                f"{sorted(classes)}"
            )

        entity_class = next(
            iter(classes)
        )

        dois = sorted_nonempty(
            row["_doi"]
            for row in group
        )

        pmids = sorted_nonempty(
            row["_pmid"]
            for row in group
        )

        frozen_keys = sorted_nonempty(
            row["dedup_key"]
            for row in group
        )

        titles = sorted_nonempty(
            row["title_or_name"]
            for row in group
        )

        years = sorted_nonempty(
            row["year"]
            for row in group
        )

        search_stages = sorted({
            stage
            for row in group
            for stage in split_semicolon(
                row["search_stages"]
            )
        })

        sources = sorted({
            source
            for row in group
            for source in split_semicolon(
                row["sources"]
            )
        })

        source_record_ids = sorted({
            value
            for row in group
            for value in split_semicolon(
                row["source_record_ids"]
            )
        })

        conflict_pmids = sorted({
            pmid
            for pmid in pmids
            if pmid in ambiguous_pmids
        })

        status = "resolved_identity"

        if conflict_pmids:
            status = "conflict_hold"

        if key.startswith(
            "publication:conflict:pmid:"
        ):
            status = "conflict_hold"

        entities.append({
            "provisional_entity_key":
                key,

            "screening_entity_class":
                entity_class,

            "identity_basis":
                sorted(
                    identity_basis[key]
                ),

            "identity_status":
                status,

            "doi_values":
                dois,

            "pmid_values":
                pmids,

            "titles":
                titles,

            "years":
                years,

            "database_dedup_keys":
                frozen_keys,

            "search_stages":
                search_stages,

            "sources":
                sources,

            "source_record_ids":
                source_record_ids,

            "identity_conflict_pmids":
                conflict_pmids,

            "source_row_sha256s":
                sorted(
                    row["_row_sha256"]
                    for row in group
                ),
        })

    conflicts = []

    for pmid in sorted(ambiguous_pmids):
        dois = ambiguous_pmids[pmid]

        affected = [
            "publication:doi:" + doi
            for doi in dois
        ]

        conflict_key = (
            "publication:conflict:"
            "pmid:"
            + pmid
        )

        if conflict_key in groups:
            affected.append(
                conflict_key
            )

        conflicts.append({
            "conflict_type":
                "pmid_multiple_doi",

            "identifier_namespace":
                "pmid",

            "identifier":
                pmid,

            "doi_values":
                dois,

            "affected_entity_keys":
                sorted(affected),
        })

    assert_provenance_preserved(
        rows,
        entities,
    )

    return {
        "input_row_count":
            len(rows),

        "entity_count":
            len(entities),

        "publication_entity_count":
            sum(
                e[
                    "screening_entity_class"
                ]
                == "publication"
                for e in entities
            ),

        "software_registry_entity_count":
            sum(
                e[
                    "screening_entity_class"
                ]
                == "software_registry"
                for e in entities
            ),

        "conflict_hold_entity_count":
            sum(
                e[
                    "identity_status"
                ]
                == "conflict_hold"
                for e in entities
            ),

        "identity_conflict_count":
            len(conflicts),

        "entities":
            entities,

        "identity_conflicts":
            conflicts,
    }


# ---------------------------------------------------------------------
# Citation-publication provisional identities.
# ---------------------------------------------------------------------

def build_citation_publication_entities(
    rows: list[dict[str, str]],
) -> dict:
    """
    Construct provisional citation publication identities without enrichment.

    DOI-bearing records are DOI-first.

    DOI-less PMID records may attach only when the PMID points to exactly one
    DOI group.

    OpenAlex/OMID-only records remain provider-specific and unresolved until
    exact metadata resolution occurs.
    """

    required = {
        "wave",
        "anchor_id",
        "anchor_tool",
        "source",
        "direction",
        "doi",
        "pmid",
        "openalex_id",
        "omid",
        "title",
        "year",
        "source_record_id",
    }

    if rows:
        missing = required - set(rows[0])

        if missing:
            raise RuntimeError(
                "Citation input missing fields: "
                + ", ".join(sorted(missing))
            )

    prepared = []

    for original in rows:
        row = dict(original)

        row["_doi"] = normalise_doi(
            row.get("doi")
        )

        row["_pmid"] = normalise_pmid(
            row.get("pmid")
        )

        row["_openalex_id"] = (
            normalise_openalex_id(
                row.get("openalex_id")
            )
        )

        row["_omid"] = normalise_omid(
            row.get("omid")
        )

        row["_row_sha256"] = row_sha256(
            original
        )

        if not any(
            (
                row["_doi"],
                row["_pmid"],
                row["_openalex_id"],
                row["_omid"],
            )
        ):
            raise RuntimeError(
                "Citation provenance row has no usable identifier: "
                + canonical_row_json(
                    original
                )
            )

        if (
            not row["_doi"]
            and not row["_pmid"]
            and row["_openalex_id"]
            and row["_omid"]
        ):
            raise RuntimeError(
                "DOI/PMID-less row simultaneously carries "
                "OpenAlex ID and OMID; provider-specific fallback "
                "would be ambiguous"
            )

        prepared.append(row)

    prepared.sort(
        key=lambda row: (
            row["anchor_id"],
            row["source"],
            row["direction"],
            row["source_record_id"],
            row["_row_sha256"],
        )
    )

    # -------------------------------------------------------------
    # Secondary-identifier relationships to DOI groups.
    # -------------------------------------------------------------

    pmid_to_dois = defaultdict(set)
    openalex_to_dois = defaultdict(set)
    omid_to_dois = defaultdict(set)
    doi_to_pmids = defaultdict(set)

    for row in prepared:
        doi = row["_doi"]

        if not doi:
            continue

        if row["_pmid"]:
            pmid_to_dois[
                row["_pmid"]
            ].add(doi)

            doi_to_pmids[
                doi
            ].add(
                row["_pmid"]
            )

        if row["_openalex_id"]:
            openalex_to_dois[
                row["_openalex_id"]
            ].add(doi)

        if row["_omid"]:
            omid_to_dois[
                row["_omid"]
            ].add(doi)

    ambiguous_pmids = {
        key: sorted(values)
        for key, values
        in pmid_to_dois.items()
        if len(values) > 1
    }

    ambiguous_openalex = {
        key: sorted(values)
        for key, values
        in openalex_to_dois.items()
        if len(values) > 1
    }

    ambiguous_omids = {
        key: sorted(values)
        for key, values
        in omid_to_dois.items()
        if len(values) > 1
    }

    multi_pmid_dois = {
        doi: sorted(pmids)
        for doi, pmids
        in doi_to_pmids.items()
        if len(pmids) > 1
    }

    groups = defaultdict(list)
    basis_by_key = defaultdict(set)

    for row in prepared:
        doi = row["_doi"]
        pmid = row["_pmid"]
        openalex_id = row["_openalex_id"]
        omid = row["_omid"]

        if doi:
            key = (
                "publication:doi:"
                + doi
            )

            basis = "doi"

        elif pmid:
            linked_dois = pmid_to_dois.get(
                pmid,
                set(),
            )

            if len(linked_dois) == 1:
                only_doi = next(
                    iter(linked_dois)
                )

                key = (
                    "publication:doi:"
                    + only_doi
                )

                basis = (
                    "pmid_attached_to_unique_doi"
                )

            elif len(linked_dois) > 1:
                key = (
                    "publication:conflict:"
                    "pmid:"
                    + pmid
                )

                basis = (
                    "ambiguous_pmid_multiple_doi"
                )

            else:
                key = (
                    "publication:pmid:"
                    + pmid
                )

                basis = "pmid"

        elif openalex_id:
            key = (
                "publication:openalex:"
                + openalex_id
            )

            basis = (
                "provider_specific_openalex"
            )

        elif omid:
            key = (
                "publication:omid:"
                + omid
            )

            basis = (
                "provider_specific_omid"
            )

        else:
            raise AssertionError(
                "Identifierless citation row escaped validation"
            )

        groups[key].append(row)
        basis_by_key[key].add(basis)

    entities = []

    for key in sorted(groups):
        group = sorted(
            groups[key],
            key=lambda row: (
                row["anchor_id"],
                row["source"],
                row["direction"],
                row["source_record_id"],
                row["_row_sha256"],
            ),
        )

        dois = sorted_nonempty(
            row["_doi"]
            for row in group
        )

        pmids = sorted_nonempty(
            row["_pmid"]
            for row in group
        )

        openalex_ids = sorted_nonempty(
            row["_openalex_id"]
            for row in group
        )

        omids = sorted_nonempty(
            row["_omid"]
            for row in group
        )

        titles = sorted_nonempty(
            row["title"]
            for row in group
        )

        years = sorted_nonempty(
            row["year"]
            for row in group
        )

        conflict_reasons = set()

        for doi in dois:
            if doi in multi_pmid_dois:
                conflict_reasons.add(
                    "doi_multiple_pmids"
                )

        for pmid in pmids:
            if pmid in ambiguous_pmids:
                conflict_reasons.add(
                    "pmid_multiple_doi"
                )

        for oid in openalex_ids:
            if oid in ambiguous_openalex:
                conflict_reasons.add(
                    "openalex_id_multiple_doi"
                )

        for omid in omids:
            if omid in ambiguous_omids:
                conflict_reasons.add(
                    "omid_multiple_doi"
                )

        if key.startswith(
            "publication:conflict:"
        ):
            conflict_reasons.add(
                "ambiguous_secondary_identifier"
            )

        if (
            key.startswith(
                "publication:openalex:"
            )
            or key.startswith(
                "publication:omid:"
            )
        ):
            status = (
                "provider_specific_unresolved"
            )

        elif conflict_reasons:
            status = "conflict_hold"

        else:
            status = "resolved_identity"

        entities.append({
            "provisional_entity_key":
                key,

            "screening_entity_class":
                "publication",

            "identity_basis":
                sorted(
                    basis_by_key[key]
                ),

            "identity_status":
                status,

            "identity_conflict_reasons":
                sorted(
                    conflict_reasons
                ),

            "doi_values":
                dois,

            "pmid_values":
                pmids,

            "openalex_id_values":
                openalex_ids,

            "omid_values":
                omids,

            "titles":
                titles,

            "years":
                years,

            "anchor_ids":
                sorted_nonempty(
                    row["anchor_id"]
                    for row in group
                ),

            "anchor_tools":
                sorted_nonempty(
                    row["anchor_tool"]
                    for row in group
                ),

            "sources":
                sorted_nonempty(
                    row["source"]
                    for row in group
                ),

            "directions":
                sorted_nonempty(
                    row["direction"]
                    for row in group
                ),

            "source_record_ids":
                sorted_nonempty(
                    (
                        row["source"]
                        + ":"
                        + row["source_record_id"]
                    )
                    for row in group
                ),

            "source_row_sha256s":
                sorted(
                    row["_row_sha256"]
                    for row in group
                ),
        })

    conflicts = []

    for namespace, mapping in (
        (
            "pmid",
            ambiguous_pmids,
        ),
        (
            "openalex_id",
            ambiguous_openalex,
        ),
        (
            "omid",
            ambiguous_omids,
        ),
    ):
        for identifier in sorted(mapping):
            dois = mapping[identifier]

            conflicts.append({
                "conflict_type":
                    f"{namespace}_multiple_doi",

                "identifier_namespace":
                    namespace,

                "identifier":
                    identifier,

                "doi_values":
                    dois,

                "affected_entity_keys":
                    sorted(
                        "publication:doi:"
                        + doi
                        for doi in dois
                    ),
            })

    for doi in sorted(multi_pmid_dois):
        conflicts.append({
            "conflict_type":
                "doi_multiple_pmids",

            "identifier_namespace":
                "doi",

            "identifier":
                doi,

            "pmid_values":
                multi_pmid_dois[doi],

            "affected_entity_keys": [
                "publication:doi:"
                + doi
            ],
        })

    conflicts.sort(
        key=lambda row: (
            row["conflict_type"],
            row["identifier_namespace"],
            row["identifier"],
        )
    )

    assert_provenance_preserved(
        rows,
        entities,
    )

    return {
        "input_row_count":
            len(rows),

        "entity_count":
            len(entities),

        "resolved_identity_count":
            sum(
                e["identity_status"]
                == "resolved_identity"
                for e in entities
            ),

        "provider_specific_unresolved_count":
            sum(
                e["identity_status"]
                == "provider_specific_unresolved"
                for e in entities
            ),

        "conflict_hold_entity_count":
            sum(
                e["identity_status"]
                == "conflict_hold"
                for e in entities
            ),

        "identity_conflict_count":
            len(conflicts),

        "entities":
            entities,

        "identity_conflicts":
            conflicts,
    }


# ---------------------------------------------------------------------
# CLI: inspection only, no output files.
# ---------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database",
        type=Path,
    )

    parser.add_argument(
        "--citation",
        type=Path,
    )

    args = parser.parse_args()

    if not args.database and not args.citation:
        parser.error(
            "At least one of --database or --citation is required"
        )

    summary = {}

    if args.database:
        rows = read_tsv(
            args.database
        )

        result = (
            build_database_screening_entities(
                rows
            )
        )

        summary["database"] = {
            key: value
            for key, value
            in result.items()
            if key
            not in {
                "entities",
                "identity_conflicts",
            }
        }

        summary["database"][
            "identity_conflict_count"
        ] = len(
            result[
                "identity_conflicts"
            ]
        )

    if args.citation:
        rows = read_tsv(
            args.citation
        )

        result = (
            build_citation_publication_entities(
                rows
            )
        )

        summary["citation"] = {
            key: value
            for key, value
            in result.items()
            if key
            not in {
                "entities",
                "identity_conflicts",
            }
        }

        summary["citation"][
            "identity_conflict_count"
        ] = len(
            result[
                "identity_conflicts"
            ]
        )

    print(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
