#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import screening_entity_identity as identity
import cross_stage_screening_entities as cross


HERE = Path(__file__).resolve().parent

CROSS_STAGE_IMPLEMENTATION = (
    HERE / "cross_stage_screening_entities.py"
)

EXPECTED_CROSS_STAGE_SHA256 = (
    "956b4b55721479460c667486649c6ffd3bfbe3abbb509b725f958c898222d220"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as fh:
        for block in iter(
            lambda: fh.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


def verify_dependency() -> None:
    actual = sha256_file(
        CROSS_STAGE_IMPLEMENTATION
    )

    if actual != EXPECTED_CROSS_STAGE_SHA256:
        raise RuntimeError(
            "Frozen cross-stage implementation drift: "
            f"{actual} != {EXPECTED_CROSS_STAGE_SHA256}"
        )


verify_dependency()


def canonical_hash(value) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


def questions(component: dict) -> tuple[str, ...]:
    reasons = set(
        component["attention_reasons"]
    )

    output = []

    if "provider_specific_unresolved" in reasons:
        output.append(
            "resolve_provider_identity"
        )

    if any(
        reason in reasons
        for reason in (
            "citation_identity_conflict",
            "database_identity_conflict",
            "cross_stage_conflict_citation_side",
            "cross_stage_conflict_database_side",
        )
    ):
        output.append(
            "adjudicate_identifier_conflict"
        )

    if "missing_title" in reasons:
        output.append(
            "recover_title"
        )

    return tuple(output)


def identifier_sets(
    component: dict,
) -> dict[str, tuple[str, ...]]:
    values = {
        "doi":
            set(component["doi_values"]),

        "pmid":
            set(component["pmid_values"]),

        "openalex":
            set(
                component[
                    "openalex_id_values"
                ]
            ),

        "omid":
            set(component["omid_values"]),
    }

    for source_id in (
        component["database_source_record_ids"]
        + component["citation_source_record_ids"]
    ):
        if source_id.startswith("openalex:"):
            value = source_id[len("openalex:"):]

            if value:
                values["openalex"].add(value)

        elif source_id.startswith("pubmed:"):
            value = source_id[len("pubmed:"):]

            if value:
                values["pmid"].add(value)

    return {
        key: tuple(sorted(items))
        for key, items in values.items()
    }


def source_providers(
    component: dict,
) -> tuple[str, ...]:
    output = set()

    for source_id in (
        component["database_source_record_ids"]
        + component["citation_source_record_ids"]
    ):
        if source_id.startswith("openalex:"):
            output.add("openalex")

        elif source_id.startswith("pubmed:"):
            output.add("pubmed")

        elif source_id.startswith("opencitations:"):
            output.add("opencitations_meta")

    return tuple(sorted(output))


def native_title_routes(
    component: dict,
) -> tuple[tuple[str, str, str, str], ...]:
    ids = identifier_sets(component)

    providers = set(
        source_providers(component)
    )

    routes = []

    if (
        "openalex" in providers
        and ids["openalex"]
    ):
        for value in ids["openalex"]:
            routes.append((
                "openalex",
                "work_by_openalex_id",
                "openalex",
                value,
            ))

    if (
        "pubmed" in providers
        and ids["pmid"]
    ):
        for value in ids["pmid"]:
            routes.append((
                "pubmed",
                "record_by_pmid",
                "pmid",
                value,
            ))

    if (
        "opencitations_meta" in providers
        and ids["omid"]
    ):
        for value in ids["omid"]:
            routes.append((
                "opencitations_meta",
                "metadata_by_omid",
                "omid",
                value,
            ))

    return tuple(sorted(set(routes)))


def lookup_id(
    provider: str,
    route: str,
    namespace: str,
    identifier: str,
) -> str:
    digest = canonical_hash([
        provider,
        route,
        namespace,
        identifier,
    ])

    return "lookup:" + digest


def assignment_id(
    *,
    component_id: str,
    lookup: str,
    policy_class: str,
    purposes: tuple[str, ...],
) -> str:
    digest = canonical_hash({
        "component_id":
            component_id,

        "logical_lookup_id":
            lookup,

        "policy_class":
            policy_class,

        "purposes":
            list(purposes),
    })

    return "assignment:" + digest


def add_assignment(
    output: list[dict],
    *,
    component_id: str,
    provider: str,
    route: str,
    namespace: str,
    identifier: str,
    policy_class: str,
    purposes,
) -> None:
    purposes = tuple(sorted(set(purposes)))

    lid = lookup_id(
        provider,
        route,
        namespace,
        identifier,
    )

    row = {
        "component_id":
            component_id,

        "logical_lookup_id":
            lid,

        "provider":
            provider,

        "route":
            route,

        "identifier_namespace":
            namespace,

        "identifier":
            identifier,

        "policy_class":
            policy_class,

        "purposes":
            purposes,
    }

    row["assignment_id"] = assignment_id(
        component_id=component_id,
        lookup=lid,
        policy_class=policy_class,
        purposes=purposes,
    )

    output.append(row)


def build_queue(
    universe: dict,
) -> dict:
    components = [
        component
        for component
        in universe["publication_components"]
        if (
            component["identity_attention"]
            or component["metadata_attention"]
        )
    ]

    components = sorted(
        components,
        key=lambda row:
            row["screening_component_id"],
    )

    assignments = []

    for component in components:
        cid = component[
            "screening_component_id"
        ]

        ids = identifier_sets(component)

        qs = set(
            questions(component)
        )

        reasons = set(
            component["attention_reasons"]
        )

        provider_unresolved = (
            "provider_specific_unresolved"
            in reasons
        )

        conflict = any(
            reason in reasons
            for reason in (
                "citation_identity_conflict",
                "database_identity_conflict",
                "cross_stage_conflict_citation_side",
                "cross_stage_conflict_database_side",
            )
        )

        missing_title = (
            "missing_title"
            in reasons
        )

        if provider_unresolved:
            if conflict:
                raise RuntimeError(
                    "Provider-unresolved component "
                    "also marked conflict: "
                    + cid
                )

            if ids["openalex"]:
                if (
                    ids["doi"]
                    or ids["pmid"]
                    or ids["omid"]
                ):
                    raise RuntimeError(
                        "OpenAlex-only unresolved "
                        "component has non-native ID: "
                        + cid
                    )

                for value in ids["openalex"]:
                    add_assignment(
                        assignments,
                        component_id=cid,
                        provider="openalex",
                        route="work_by_openalex_id",
                        namespace="openalex",
                        identifier=value,
                        policy_class=
                            "native_provider_identity",
                        purposes=qs,
                    )

            elif ids["omid"]:
                if (
                    ids["doi"]
                    or ids["pmid"]
                    or ids["openalex"]
                ):
                    raise RuntimeError(
                        "OMID-only unresolved "
                        "component has non-native ID: "
                        + cid
                    )

                for value in ids["omid"]:
                    add_assignment(
                        assignments,
                        component_id=cid,
                        provider=
                            "opencitations_meta",
                        route="metadata_by_omid",
                        namespace="omid",
                        identifier=value,
                        policy_class=
                            "native_provider_identity",
                        purposes=qs,
                    )

            else:
                raise RuntimeError(
                    "Provider-unresolved component "
                    "lacks native identifier: "
                    + cid
                )

            continue

        if conflict:
            for value in ids["openalex"]:
                add_assignment(
                    assignments,
                    component_id=cid,
                    provider="openalex",
                    route="work_by_openalex_id",
                    namespace="openalex",
                    identifier=value,
                    policy_class=
                        "conflict_all_exact_evidence",
                    purposes=qs,
                )

            for value in ids["doi"]:
                add_assignment(
                    assignments,
                    component_id=cid,
                    provider="openalex",
                    route="work_by_doi",
                    namespace="doi",
                    identifier=value,
                    policy_class=
                        "conflict_all_exact_evidence",
                    purposes=qs,
                )

                add_assignment(
                    assignments,
                    component_id=cid,
                    provider=
                        "opencitations_meta",
                    route="metadata_by_doi",
                    namespace="doi",
                    identifier=value,
                    policy_class=
                        "conflict_all_exact_evidence",
                    purposes=qs,
                )

            for value in ids["pmid"]:
                add_assignment(
                    assignments,
                    component_id=cid,
                    provider="openalex",
                    route="work_by_pmid",
                    namespace="pmid",
                    identifier=value,
                    policy_class=
                        "conflict_all_exact_evidence",
                    purposes=qs,
                )

                add_assignment(
                    assignments,
                    component_id=cid,
                    provider="pubmed",
                    route="record_by_pmid",
                    namespace="pmid",
                    identifier=value,
                    policy_class=
                        "conflict_all_exact_evidence",
                    purposes=qs,
                )

            for value in ids["omid"]:
                add_assignment(
                    assignments,
                    component_id=cid,
                    provider=
                        "opencitations_meta",
                    route="metadata_by_omid",
                    namespace="omid",
                    identifier=value,
                    policy_class=
                        "conflict_all_exact_evidence",
                    purposes=qs,
                )

            continue

        if missing_title:
            if qs != {"recover_title"}:
                raise RuntimeError(
                    "Title-only branch has unexpected "
                    "evidence question: "
                    + cid
                )

            native = native_title_routes(
                component
            )

            if not native:
                raise RuntimeError(
                    "Title-only component lacks "
                    "native exact route: "
                    + cid
                )

            for (
                provider,
                route,
                namespace,
                identifier,
            ) in native:
                add_assignment(
                    assignments,
                    component_id=cid,
                    provider=provider,
                    route=route,
                    namespace=namespace,
                    identifier=identifier,
                    policy_class=
                        "native_title_evidence",
                    purposes=qs,
                )

            continue

        raise RuntimeError(
            "Attention component escaped queue "
            "policy: "
            + cid
        )

    assignments.sort(
        key=lambda row: (
            row["component_id"],
            row["provider"],
            row["route"],
            row["identifier_namespace"],
            row["identifier"],
            row["policy_class"],
            row["purposes"],
        )
    )

    if (
        len({
            row["assignment_id"]
            for row in assignments
        })
        != len(assignments)
    ):
        raise RuntimeError(
            "Duplicate assignment ID"
        )

    lookup_groups = defaultdict(list)

    for row in assignments:
        lookup_groups[
            row["logical_lookup_id"]
        ].append(row)

    lookups = []

    for lid in sorted(lookup_groups):
        rows = lookup_groups[lid]

        keys = {
            (
                row["provider"],
                row["route"],
                row["identifier_namespace"],
                row["identifier"],
            )
            for row in rows
        }

        if len(keys) != 1:
            raise RuntimeError(
                "Logical lookup ID collision: "
                + lid
            )

        (
            provider,
            route,
            namespace,
            identifier,
        ) = next(iter(keys))

        lookups.append({
            "logical_lookup_id":
                lid,

            "provider":
                provider,

            "route":
                route,

            "identifier_namespace":
                namespace,

            "identifier":
                identifier,

            "assignment_count":
                len(rows),

            "component_count":
                len({
                    row["component_id"]
                    for row in rows
                }),

            "component_ids":
                tuple(sorted({
                    row["component_id"]
                    for row in rows
                })),

            "policy_classes":
                tuple(sorted({
                    row["policy_class"]
                    for row in rows
                })),

            "purposes":
                tuple(sorted({
                    purpose
                    for row in rows
                    for purpose in row["purposes"]
                })),
        })

    assignment_by_component = defaultdict(list)

    for row in assignments:
        assignment_by_component[
            row["component_id"]
        ].append(row)

    component_rows = []

    for component in components:
        cid = component[
            "screening_component_id"
        ]

        rows = assignment_by_component[
            cid
        ]

        if not rows:
            raise RuntimeError(
                "Attention component has no "
                "evidence assignment: "
                + cid
            )

        ids = identifier_sets(component)

        component_rows.append({
            "component_id":
                cid,

            "questions":
                questions(component),

            "attention_reasons":
                tuple(
                    component[
                        "attention_reasons"
                    ]
                ),

            "source_providers":
                source_providers(
                    component
                ),

            "doi_values":
                ids["doi"],

            "pmid_values":
                ids["pmid"],

            "openalex_ids":
                ids["openalex"],

            "omid_values":
                ids["omid"],

            "assignment_count":
                len(rows),

            "logical_lookup_count":
                len({
                    row["logical_lookup_id"]
                    for row in rows
                }),
        })

    policy_counts = Counter(
        row["policy_class"]
        for row in assignments
    )

    provider_counts = Counter(
        row["provider"]
        for row in lookups
    )

    route_counts = Counter(
        (
            row["provider"],
            row["route"],
        )
        for row in lookups
    )

    question_counts = Counter(
        question
        for row in component_rows
        for question in row["questions"]
    )

    question_combinations = Counter(
        row["questions"]
        for row in component_rows
    )

    shared = [
        row
        for row in lookups
        if row["component_count"] > 1
    ]

    shared_policy_combinations = Counter(
        row["policy_classes"]
        for row in shared
    )

    title_components = [
        row
        for row in component_rows
        if row["questions"] == (
            "recover_title",
        )
    ]

    title_assignments = [
        row
        for row in assignments
        if row["policy_class"]
        == "native_title_evidence"
    ]

    title_assignment_counts = Counter(
        row["component_id"]
        for row in title_assignments
    )

    title_multiplicity = Counter(
        title_assignment_counts.values()
    )

    summary = {
        "attention_components":
            len(component_rows),

        "component_evidence_assignments":
            len(assignments),

        "logical_lookup_keys":
            len(lookups),

        "policy_counts":
            dict(sorted(
                policy_counts.items()
            )),

        "logical_lookup_provider_counts":
            dict(sorted(
                provider_counts.items()
            )),

        "logical_lookup_route_counts": {
            f"{provider}|{route}": count
            for (
                provider,
                route,
            ), count in sorted(
                route_counts.items()
            )
        },

        "question_counts":
            dict(sorted(
                question_counts.items()
            )),

        "question_combination_counts": {
            "|".join(combo): count
            for combo, count
            in sorted(
                question_combinations.items()
            )
        },

        "shared_logical_lookup_keys":
            len(shared),

        "shared_policy_combination_counts": {
            "|".join(combo): count
            for combo, count
            in sorted(
                shared_policy_combinations.items()
            )
        },

        "title_only_components":
            len(title_components),

        "title_native_route_multiplicity":
            {
                str(key): value
                for key, value
                in sorted(
                    title_multiplicity.items()
                )
            },
    }

    return {
        "components":
            component_rows,

        "assignments":
            assignments,

        "lookups":
            lookups,

        "summary":
            summary,
    }


def flatten(value) -> str:
    if isinstance(value, tuple):
        return ";".join(value)

    return str(value)


def write_tsv(
    path: Path,
    rows: list[dict],
    columns: list[str],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            delimiter="\t",
            lineterminator="\n",
            fieldnames=columns,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow({
                column:
                    flatten(
                        row[column]
                    )
                for column in columns
            })


def write_queue(
    queue: dict,
    output_dir: Path,
) -> None:
    write_tsv(
        output_dir
        / "metadata_resolution_queue_components.tsv",
        queue["components"],
        [
            "component_id",
            "questions",
            "attention_reasons",
            "source_providers",
            "doi_values",
            "pmid_values",
            "openalex_ids",
            "omid_values",
            "assignment_count",
            "logical_lookup_count",
        ],
    )

    write_tsv(
        output_dir
        / "metadata_resolution_queue_assignments.tsv",
        queue["assignments"],
        [
            "assignment_id",
            "component_id",
            "logical_lookup_id",
            "provider",
            "route",
            "identifier_namespace",
            "identifier",
            "policy_class",
            "purposes",
        ],
    )

    write_tsv(
        output_dir
        / "metadata_resolution_logical_lookups.tsv",
        queue["lookups"],
        [
            "logical_lookup_id",
            "provider",
            "route",
            "identifier_namespace",
            "identifier",
            "assignment_count",
            "component_count",
            "component_ids",
            "policy_classes",
            "purposes",
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--citation",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    database = (
        identity.build_database_screening_entities(
            identity.read_tsv(
                args.database
            )
        )
    )

    citation = (
        identity.build_citation_publication_entities(
            identity.read_tsv(
                args.citation
            )
        )
    )

    universe = (
        cross.build_cross_stage_screening_universe(
            database,
            citation,
        )
    )

    queue = build_queue(
        universe
    )

    write_queue(
        queue,
        args.output_dir,
    )

    print(
        json.dumps(
            queue["summary"],
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
