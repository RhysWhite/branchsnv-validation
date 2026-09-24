#!/usr/bin/env python3

"""
Experiment 07 frozen post-retrieval metadata reconciliation.

This module implements the contract frozen in:

    POST_RETRIEVAL_RECONCILIATION_DESIGN.md
    post_retrieval_reconciliation_design.json

Scientific boundary
-------------------

This module:

- performs no network access;
- does not modify the metadata-retrieval archive;
- does not merge publication components;
- does not perform scientific screening;
- does not select a winner among identifier-conflict components;
- does not infer identifiers from title similarity;
- does not infer missing titles.

By default the CLI is dry-run only.

Production-like derived files are written only when an explicit
--write-output-root is supplied.

Those derived files are:

    component_reconciliation.tsv
    reconciliation_evidence.tsv
    manifest.json
    checksums.sha256
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET


SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_ARCHIVE_ROOT = (
    SCRIPT_DIR.parent.parent
    / "results"
    / "07_comparative_landscape"
    / "metadata_resolution_retrieval"
)

COMPONENTS_FILENAME = (
    "metadata_resolution_queue_components.tsv"
)

ASSIGNMENTS_FILENAME = (
    "metadata_resolution_queue_assignments.tsv"
)

LOOKUPS_FILENAME = (
    "metadata_resolution_logical_lookups.tsv"
)

LOOKUP_STATUS_FILENAME = "lookup_status.tsv"

DESIGN_FILENAME = (
    "post_retrieval_reconciliation_design.json"
)

COMPONENT_OUTPUT_FILENAME = (
    "component_reconciliation.tsv"
)

EVIDENCE_OUTPUT_FILENAME = (
    "reconciliation_evidence.tsv"
)

MANIFEST_FILENAME = "manifest.json"
CHECKSUMS_FILENAME = "checksums.sha256"


COMPONENT_FIELDS = [
    "component_id",
    "questions",
    "attention_reasons",
    "source_providers",
    "identifier_status",
    "derived_doi",
    "derived_pmid",
    "identifier_evidence_lookup_ids",
    "title_status",
    "resolved_title",
    "title_variants_json",
    "title_evidence_lookup_ids",
    "all_logical_lookup_ids",
    "component_merge_performed",
    "scientific_screening_performed",
]


EVIDENCE_FIELDS = [
    "component_id",
    "assignment_id",
    "logical_lookup_id",
    "provider",
    "route",
    "status",
    "policy_class",
    "purposes",
    "requested_identifier_namespace",
    "requested_identifier",
    "returned_dois",
    "returned_pmids",
    "title_candidates_json",
]


EXPECTED_IDENTIFIER_STATUS_COUNTS = {
    "identifier_conflict_hold": 117,
    "not_applicable": 723,
    "provider_identity_anchored": 311,
    "provider_identity_confirmed_unanchored": 183,
    "provider_identity_not_found": 8,
}


EXPECTED_TITLE_STATUS_COUNTS = {
    "not_applicable": 275,
    "title_conflict_hold": 2,
    "title_equivalent_variants": 8,
    "title_resolved_exact": 575,
    "title_unresolved": 482,
}


class ReconciliationError(RuntimeError):
    """Fail-closed reconciliation error."""


def canonical_json_bytes(
    value: Any,
) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(
    value: bytes,
) -> str:
    return hashlib.sha256(
        value
    ).hexdigest()


def sha256_file(
    path: Path,
) -> str:
    return sha256_bytes(
        path.read_bytes()
    )


def read_tsv(
    path: Path,
) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        rows = list(reader)

        fields = list(
            reader.fieldnames
            or []
        )

    return fields, rows


def require_exact_fields(
    observed: Iterable[str],
    expected: Iterable[str],
    label: str,
) -> None:
    observed = list(observed)
    expected = list(expected)

    if observed != expected:
        raise ReconciliationError(
            f"{label} schema mismatch: "
            f"observed={observed!r} "
            f"expected={expected!r}"
        )


def split_semicolon(
    value: str,
) -> list[str]:
    if not value:
        return []

    return [
        item
        for item in value.split(";")
        if item
    ]


def localname(
    tag: str,
) -> str:
    return tag.rsplit(
        "}",
        1,
    )[-1]


def element_text(
    element: ET.Element | None,
) -> str:
    if element is None:
        return ""

    return " ".join(
        "".join(
            element.itertext()
        ).split()
    ).strip()


def direct_children(
    element: ET.Element,
    name: str,
) -> list[ET.Element]:
    return [
        child
        for child in list(
            element
        )
        if localname(
            child.tag
        ) == name
    ]


def direct_child(
    element: ET.Element,
    name: str,
) -> ET.Element | None:
    values = direct_children(
        element,
        name,
    )

    if not values:
        return None

    if len(values) != 1:
        raise ReconciliationError(
            f"Expected <=1 direct "
            f"{name!r}; "
            f"observed {len(values)}"
        )

    return values[0]


def canonical_identifier(
    namespace: str,
    value: str,
) -> str | None:
    namespace = (
        namespace
        .strip()
        .lower()
    )

    value = unquote(
        value.strip()
    )

    if namespace == "doi":
        value = re.sub(
            r"^https?://(?:dx\.)?doi\.org/",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"^doi:",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = (
            value
            .strip()
            .lower()
        )

        if not value.startswith(
            "10."
        ):
            return None

        return "doi:" + value

    if namespace == "pmid":
        value = re.sub(
            r"^https?://pubmed\.ncbi\.nlm\.nih\.gov/",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"^pmid:",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = value.strip(
            "/ "
        )

        if not re.fullmatch(
            r"\d+",
            value,
        ):
            return None

        return "pmid:" + value

    if namespace == "openalex":
        value = re.sub(
            r"^https?://openalex\.org/",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"^openalex:",
            "",
            value,
            flags=re.IGNORECASE,
        )

        match = re.fullmatch(
            r"[Ww](\d+)",
            value.strip(),
        )

        if match is None:
            return None

        return (
            "openalex:W"
            + match.group(1)
        )

    if namespace == "omid":
        value = re.sub(
            r"^omid:",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = (
            value
            .strip()
            .lower()
        )

        if not re.fullmatch(
            r"[a-z]+/\d+",
            value,
        ):
            return None

        return "omid:" + value

    return None


def identifier_namespace(
    token: str,
) -> str:
    return token.split(
        ":",
        1,
    )[0]


def identifier_value(
    token: str,
) -> str:
    return token.split(
        ":",
        1,
    )[1]


def title_token_key(
    value: str,
) -> str:
    value = unicodedata.normalize(
        "NFKC",
        value,
    ).casefold()

    chars: list[str] = []

    for char in value:
        category = (
            unicodedata.category(
                char
            )
        )

        if (
            category.startswith("L")
            or category.startswith("N")
        ):
            chars.append(
                char
            )

        else:
            chars.append(
                " "
            )

    return " ".join(
        "".join(
            chars
        ).split()
    )


def title_compact_key(
    value: str,
) -> str:
    value = unicodedata.normalize(
        "NFKC",
        value,
    ).casefold()

    return "".join(
        char
        for char in value
        if (
            unicodedata.category(
                char
            ).startswith("L")
            or unicodedata.category(
                char
            ).startswith("N")
        )
    )


def classify_title_values(
    titles: Iterable[str],
) -> tuple[str, list[str]]:
    exact = sorted(
        {
            value.strip()
            for value in titles
            if value.strip()
        }
    )

    if not exact:
        return (
            "title_unresolved",
            [],
        )

    if len(exact) == 1:
        return (
            "title_resolved_exact",
            exact,
        )

    token_keys = {
        title_token_key(
            value
        )
        for value in exact
    }

    if len(token_keys) == 1:
        return (
            "title_equivalent_variants",
            exact,
        )

    compact_keys = {
        title_compact_key(
            value
        )
        for value in exact
    }

    if len(compact_keys) == 1:
        return (
            "title_equivalent_variants",
            exact,
        )

    return (
        "title_conflict_hold",
        exact,
    )


def lookup_directory(
    archive_root: Path,
    logical_lookup_id: str,
) -> Path:
    return (
        archive_root
        / "raw"
        / logical_lookup_id.replace(
            ":",
            "_",
        )
    )


def accepted_attempt_number(
    lookup_root: Path,
) -> int:
    adjudication_path = (
        lookup_root
        / "adjudication.json"
    )

    terminal_path = (
        lookup_root
        / "terminal.json"
    )

    if adjudication_path.is_file():
        if terminal_path.exists():
            raise ReconciliationError(
                "Adjudicated lookup must "
                "not also contain terminal.json: "
                f"{lookup_root}"
            )

        value = json.loads(
            adjudication_path.read_text(
                encoding="utf-8"
            )
        )

        return int(
            value[
                "source_attempt_number"
            ]
        )

    if terminal_path.is_file():
        value = json.loads(
            terminal_path.read_text(
                encoding="utf-8"
            )
        )

        return int(
            value[
                "attempt_count"
            ]
        )

    raise ReconciliationError(
        "Successful lookup lacks "
        "terminal/adjudication evidence: "
        f"{lookup_root}"
    )


def archived_success_body(
    archive_root: Path,
    logical_lookup_id: str,
) -> bytes:
    lookup_root = lookup_directory(
        archive_root,
        logical_lookup_id,
    )

    attempt_number = (
        accepted_attempt_number(
            lookup_root
        )
    )

    attempt_root = (
        lookup_root
        / f"attempt_{attempt_number:02d}"
    )

    response_paths = sorted(
        attempt_root.glob(
            "hop_*_response.json"
        )
    )

    if not response_paths:
        raise ReconciliationError(
            "Successful lookup has no "
            "archived response metadata: "
            f"{logical_lookup_id}"
        )

    response = json.loads(
        response_paths[-1].read_text(
            encoding="utf-8"
        )
    )

    body_path = (
        attempt_root
        / response[
            "body_file"
        ]
    )

    body = body_path.read_bytes()

    observed = sha256_bytes(
        body
    )

    expected = response[
        "body_sha256"
    ]

    if observed != expected:
        raise ReconciliationError(
            "Archived response body "
            "hash mismatch for "
            f"{logical_lookup_id}"
        )

    return body


def parse_openalex_record(
    body: bytes,
) -> dict[str, Any]:
    value = json.loads(
        body.decode(
            "utf-8"
        )
    )

    if not isinstance(
        value,
        dict,
    ):
        raise ReconciliationError(
            "OpenAlex successful body "
            "is not a JSON object"
        )

    identifiers: set[str] = set()

    native = value.get(
        "id"
    )

    if isinstance(
        native,
        str,
    ):
        token = canonical_identifier(
            "openalex",
            native,
        )

        if token is not None:
            identifiers.add(
                token
            )

    ids = value.get(
        "ids"
    )

    if isinstance(
        ids,
        dict,
    ):
        mapping = {
            "openalex":
                "openalex",

            "doi":
                "doi",

            "pmid":
                "pmid",
        }

        for field, namespace in (
            mapping.items()
        ):
            raw = ids.get(
                field
            )

            if not isinstance(
                raw,
                str,
            ):
                continue

            token = canonical_identifier(
                namespace,
                raw,
            )

            if token is not None:
                identifiers.add(
                    token
                )

    titles: list[str] = []

    for field in (
        "display_name",
        "title",
    ):
        title = value.get(
            field
        )

        if (
            isinstance(
                title,
                str,
            )
            and title.strip()
        ):
            titles.append(
                title.strip()
            )

    return {
        "identifiers":
            sorted(
                identifiers
            ),

        "titles":
            sorted(
                set(
                    titles
                )
            ),
    }


def parse_opencitations_record(
    body: bytes,
) -> dict[str, Any]:
    value = json.loads(
        body.decode(
            "utf-8"
        )
    )

    if not isinstance(
        value,
        list,
    ):
        raise ReconciliationError(
            "OpenCitations successful "
            "body is not a JSON list"
        )

    identifiers: set[str] = set()
    titles: set[str] = set()

    for record in value:
        if not isinstance(
            record,
            dict,
        ):
            raise ReconciliationError(
                "OpenCitations response "
                "contains non-object row"
            )

        raw_ids = record.get(
            "id"
        )

        if isinstance(
            raw_ids,
            str,
        ):
            for raw in raw_ids.split():
                if ":" not in raw:
                    continue

                namespace, identifier = (
                    raw.split(
                        ":",
                        1,
                    )
                )

                token = canonical_identifier(
                    namespace,
                    identifier,
                )

                if token is not None:
                    identifiers.add(
                        token
                    )

        title = record.get(
            "title"
        )

        if (
            isinstance(
                title,
                str,
            )
            and title.strip()
        ):
            titles.add(
                title.strip()
            )

    return {
        "identifiers":
            sorted(
                identifiers
            ),

        "titles":
            sorted(
                titles
            ),
    }


def pubmed_primary_pmid(
    article: ET.Element,
) -> str | None:
    kind = localname(
        article.tag
    )

    if kind == "PubmedArticle":
        record = direct_child(
            article,
            "MedlineCitation",
        )

    elif kind == "PubmedBookArticle":
        record = direct_child(
            article,
            "BookDocument",
        )

    else:
        return None

    if record is None:
        return None

    pmid = direct_child(
        record,
        "PMID",
    )

    value = element_text(
        pmid
    )

    if not value:
        return None

    return canonical_identifier(
        "pmid",
        value,
    )


def parse_pubmed_record(
    body: bytes,
    requested_pmid: str,
) -> dict[str, Any]:
    root = ET.fromstring(
        body
    )

    candidates = [
        element
        for element in root.iter()
        if localname(
            element.tag
        )
        in {
            "PubmedArticle",
            "PubmedBookArticle",
        }
    ]

    matched = [
        article
        for article in candidates
        if (
            pubmed_primary_pmid(
                article
            )
            == requested_pmid
        )
    ]

    if len(matched) != 1:
        raise ReconciliationError(
            "PubMed body does not contain "
            "exactly one focal record for "
            f"{requested_pmid}: "
            f"{len(matched)}"
        )

    article = matched[0]

    identifiers: set[str] = {
        requested_pmid
    }

    kind = localname(
        article.tag
    )

    if kind == "PubmedArticle":
        record = direct_child(
            article,
            "MedlineCitation",
        )

        data = direct_child(
            article,
            "PubmedData",
        )

    else:
        record = direct_child(
            article,
            "BookDocument",
        )

        data = direct_child(
            article,
            "PubmedBookData",
        )

    if data is not None:
        article_id_list = direct_child(
            data,
            "ArticleIdList",
        )

        if article_id_list is not None:
            for article_id in (
                direct_children(
                    article_id_list,
                    "ArticleId",
                )
            ):
                id_type = (
                    article_id.attrib.get(
                        "IdType",
                        "",
                    )
                    .strip()
                    .lower()
                )

                raw = element_text(
                    article_id
                )

                if id_type == "doi":
                    token = (
                        canonical_identifier(
                            "doi",
                            raw,
                        )
                    )

                elif id_type in {
                    "pubmed",
                    "pmid",
                }:
                    token = (
                        canonical_identifier(
                            "pmid",
                            raw,
                        )
                    )

                else:
                    token = None

                if token is not None:
                    identifiers.add(
                        token
                    )

    titles: set[str] = set()

    if record is not None:
        for element in record.iter():
            if localname(
                element.tag
            ) not in {
                "ArticleTitle",
                "BookTitle",
                "CollectionTitle",
            }:
                continue

            value = element_text(
                element
            )

            if value:
                titles.add(
                    value
                )

    return {
        "identifiers":
            sorted(
                identifiers
            ),

        "titles":
            sorted(
                titles
            ),
    }


def parse_successful_lookup(
    *,
    archive_root: Path,
    logical_lookup_id: str,
    provider: str,
    requested_namespace: str,
    requested_identifier: str,
) -> dict[str, Any]:
    body = archived_success_body(
        archive_root,
        logical_lookup_id,
    )

    if provider == "openalex":
        return parse_openalex_record(
            body
        )

    if provider == "opencitations_meta":
        return (
            parse_opencitations_record(
                body
            )
        )

    if provider == "pubmed":
        requested = (
            canonical_identifier(
                requested_namespace,
                requested_identifier,
            )
        )

        if (
            requested is None
            or identifier_namespace(
                requested
            )
            != "pmid"
        ):
            raise ReconciliationError(
                "PubMed successful lookup "
                "does not have canonical "
                "requested PMID"
            )

        return parse_pubmed_record(
            body,
            requested,
        )

    raise ReconciliationError(
        "Unexpected provider: "
        f"{provider!r}"
    )


def validate_design(
    design: dict[str, Any],
) -> None:
    if (
        design.get(
            "status"
        )
        != "FROZEN_PRE_IMPLEMENTATION"
    ):
        raise ReconciliationError(
            "Reconciliation design is "
            "not frozen pre-implementation"
        )

    if (
        design[
            "inputs"
        ][
            "component_count"
        ]
        != 1342
    ):
        raise ReconciliationError(
            "Frozen component count changed"
        )

    if (
        design[
            "identifier_conflict_policy"
        ][
            "automatic_resolution"
        ]
        is not False
    ):
        raise ReconciliationError(
            "Frozen conflict policy changed"
        )

    if (
        design[
            "scientific_boundary"
        ][
            "scientific_screening_performed"
        ]
        is not False
    ):
        raise ReconciliationError(
            "Frozen scientific boundary "
            "changed"
        )


def load_inputs(
    *,
    source_root: Path,
    archive_root: Path,
) -> dict[str, Any]:
    design = json.loads(
        (
            source_root
            / DESIGN_FILENAME
        ).read_text(
            encoding="utf-8"
        )
    )

    validate_design(
        design
    )

    component_fields, components = (
        read_tsv(
            source_root
            / COMPONENTS_FILENAME
        )
    )

    assignment_fields, assignments = (
        read_tsv(
            source_root
            / ASSIGNMENTS_FILENAME
        )
    )

    lookup_fields, lookups = (
        read_tsv(
            source_root
            / LOOKUPS_FILENAME
        )
    )

    status_fields, statuses = (
        read_tsv(
            archive_root
            / LOOKUP_STATUS_FILENAME
        )
    )

    require_exact_fields(
        component_fields,
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
        "component table",
    )

    require_exact_fields(
        assignment_fields,
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
        "assignment table",
    )

    require_exact_fields(
        lookup_fields,
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
        "logical lookup table",
    )

    if "logical_lookup_id" not in (
        status_fields
    ):
        raise ReconciliationError(
            "lookup_status.tsv lacks "
            "logical_lookup_id"
        )

    if "status" not in status_fields:
        raise ReconciliationError(
            "lookup_status.tsv lacks status"
        )

    if len(components) != 1342:
        raise ReconciliationError(
            "Expected 1,342 components; "
            f"observed {len(components)}"
        )

    if len(assignments) != 1847:
        raise ReconciliationError(
            "Expected 1,847 assignments; "
            f"observed {len(assignments)}"
        )

    if len(lookups) != 1731:
        raise ReconciliationError(
            "Expected 1,731 logical "
            f"lookups; observed {len(lookups)}"
        )

    if len(statuses) != 1731:
        raise ReconciliationError(
            "Expected 1,731 lookup "
            f"statuses; observed "
            f"{len(statuses)}"
        )

    component_by_id = {
        row[
            "component_id"
        ]:
            row
        for row in components
    }

    if len(component_by_id) != 1342:
        raise ReconciliationError(
            "Duplicate component_id"
        )

    lookup_by_id = {
        row[
            "logical_lookup_id"
        ]:
            row
        for row in lookups
    }

    if len(lookup_by_id) != 1731:
        raise ReconciliationError(
            "Duplicate logical_lookup_id"
        )

    status_by_id = {
        row[
            "logical_lookup_id"
        ]:
            row
        for row in statuses
    }

    if len(status_by_id) != 1731:
        raise ReconciliationError(
            "Duplicate lookup status ID"
        )

    if (
        set(
            lookup_by_id
        )
        != set(
            status_by_id
        )
    ):
        raise ReconciliationError(
            "Logical lookup universe "
            "does not equal status universe"
        )

    assignments_by_component: dict[
        str,
        list[dict[str, str]],
    ] = defaultdict(
        list
    )

    for row in assignments:
        component_id = row[
            "component_id"
        ]

        logical_id = row[
            "logical_lookup_id"
        ]

        if component_id not in (
            component_by_id
        ):
            raise ReconciliationError(
                "Assignment references "
                "unknown component: "
                f"{component_id}"
            )

        if logical_id not in (
            lookup_by_id
        ):
            raise ReconciliationError(
                "Assignment references "
                "unknown lookup: "
                f"{logical_id}"
            )

        assignments_by_component[
            component_id
        ].append(
            row
        )

    return {
        "design":
            design,

        "components":
            components,

        "assignments":
            assignments,

        "lookups":
            lookups,

        "statuses":
            statuses,

        "component_by_id":
            component_by_id,

        "lookup_by_id":
            lookup_by_id,

        "status_by_id":
            status_by_id,

        "assignments_by_component":
            assignments_by_component,
    }


def build_lookup_evidence(
    *,
    archive_root: Path,
    input_data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    lookup_by_id = input_data[
        "lookup_by_id"
    ]

    status_by_id = input_data[
        "status_by_id"
    ]

    evidence: dict[
        str,
        dict[str, Any],
    ] = {}

    for logical_id in sorted(
        lookup_by_id
    ):
        lookup = lookup_by_id[
            logical_id
        ]

        status = status_by_id[
            logical_id
        ][
            "status"
        ]

        if status not in {
            "success",
            "not_found",
        }:
            raise ReconciliationError(
                "Completed archive contains "
                "non-accepted status: "
                f"{logical_id}={status}"
            )

        requested = (
            canonical_identifier(
                lookup[
                    "identifier_namespace"
                ],
                lookup[
                    "identifier"
                ],
            )
        )

        if requested is None:
            raise ReconciliationError(
                "Cannot canonicalize "
                "requested identifier for "
                f"{logical_id}"
            )

        if status == "success":
            parsed = (
                parse_successful_lookup(
                    archive_root=archive_root,
                    logical_lookup_id=logical_id,
                    provider=lookup[
                        "provider"
                    ],
                    requested_namespace=lookup[
                        "identifier_namespace"
                    ],
                    requested_identifier=lookup[
                        "identifier"
                    ],
                )
            )

        else:
            parsed = {
                "identifiers":
                    [],

                "titles":
                    [],
            }

        evidence[
            logical_id
        ] = {
            "logical_lookup_id":
                logical_id,

            "provider":
                lookup[
                    "provider"
                ],

            "route":
                lookup[
                    "route"
                ],

            "status":
                status,

            "requested_identifier":
                requested,

            "identifiers":
                parsed[
                    "identifiers"
                ],

            "titles":
                parsed[
                    "titles"
                ],
        }

    return evidence


def derive_identifier_state(
    *,
    component: dict[str, str],
    assignments: list[
        dict[str, str]
    ],
    lookup_evidence: dict[
        str,
        dict[str, Any]
    ],
) -> dict[str, str]:
    questions = set(
        split_semicolon(
            component[
                "questions"
            ]
        )
    )

    policy_classes = {
        row[
            "policy_class"
        ]
        for row in assignments
    }

    if (
        "adjudicate_identifier_conflict"
        in questions
    ):
        if policy_classes != {
            "conflict_all_exact_evidence"
        }:
            raise ReconciliationError(
                "Identifier-conflict "
                "component has unexpected "
                "policy classes: "
                f"{component['component_id']}"
            )

        return {
            "identifier_status":
                "identifier_conflict_hold",

            "derived_doi":
                "",

            "derived_pmid":
                "",

            "identifier_evidence_lookup_ids":
                ";".join(
                    sorted(
                        {
                            row[
                                "logical_lookup_id"
                            ]
                            for row
                            in assignments
                        }
                    )
                ),
        }

    if (
        "resolve_provider_identity"
        in questions
    ):
        native = [
            row
            for row in assignments
            if (
                row[
                    "policy_class"
                ]
                == "native_provider_identity"
            )
        ]

        if len(native) != 1:
            raise ReconciliationError(
                "Native-provider identity "
                "component must have "
                "exactly one native "
                "assignment: "
                f"{component['component_id']} "
                f"observed={len(native)}"
            )

        assignment = native[0]

        logical_id = assignment[
            "logical_lookup_id"
        ]

        evidence = lookup_evidence[
            logical_id
        ]

        if evidence[
            "status"
        ] == "not_found":
            return {
                "identifier_status":
                    "provider_identity_not_found",

                "derived_doi":
                    "",

                "derived_pmid":
                    "",

                "identifier_evidence_lookup_ids":
                    logical_id,
            }

        requested = evidence[
            "requested_identifier"
        ]

        returned = set(
            evidence[
                "identifiers"
            ]
        )

        if requested not in returned:
            raise ReconciliationError(
                "Successful native-provider "
                "lookup does not "
                "self-confirm requested "
                "identifier: "
                f"{logical_id}"
            )

        dois = sorted(
            token
            for token in returned
            if (
                identifier_namespace(
                    token
                )
                == "doi"
            )
        )

        pmids = sorted(
            token
            for token in returned
            if (
                identifier_namespace(
                    token
                )
                == "pmid"
            )
        )

        if (
            len(dois) > 1
            or len(pmids) > 1
        ):
            raise ReconciliationError(
                "Native-provider identity "
                "lookup contains multiple "
                "publication anchors: "
                f"{logical_id}; "
                f"dois={dois!r}; "
                f"pmids={pmids!r}"
            )

        if dois or pmids:
            return {
                "identifier_status":
                    "provider_identity_anchored",

                "derived_doi":
                    (
                        identifier_value(
                            dois[0]
                        )
                        if dois
                        else ""
                    ),

                "derived_pmid":
                    (
                        identifier_value(
                            pmids[0]
                        )
                        if pmids
                        else ""
                    ),

                "identifier_evidence_lookup_ids":
                    logical_id,
            }

        return {
            "identifier_status":
                "provider_identity_confirmed_unanchored",

            "derived_doi":
                "",

            "derived_pmid":
                "",

            "identifier_evidence_lookup_ids":
                logical_id,
        }

    return {
        "identifier_status":
            "not_applicable",

        "derived_doi":
            "",

        "derived_pmid":
            "",

        "identifier_evidence_lookup_ids":
            "",
    }


def derive_title_state(
    *,
    component: dict[str, str],
    assignments: list[
        dict[str, str]
    ],
    lookup_evidence: dict[
        str,
        dict[str, Any]
    ],
) -> dict[str, str]:
    questions = set(
        split_semicolon(
            component[
                "questions"
            ]
        )
    )

    if "recover_title" not in questions:
        return {
            "title_status":
                "not_applicable",

            "resolved_title":
                "",

            "title_variants_json":
                "[]",

            "title_evidence_lookup_ids":
                "",
        }

    logical_ids = sorted(
        {
            row[
                "logical_lookup_id"
            ]
            for row in assignments
            if (
                "recover_title"
                in split_semicolon(
                    row[
                        "purposes"
                    ]
                )
            )
        }
    )

    titles_by_lookup: dict[
        str,
        list[str],
    ] = {}

    for logical_id in logical_ids:
        titles = list(
            lookup_evidence[
                logical_id
            ][
                "titles"
            ]
        )

        if titles:
            titles_by_lookup[
                logical_id
            ] = titles

    all_titles = [
        title
        for titles in (
            titles_by_lookup.values()
        )
        for title in titles
    ]

    status, exact = (
        classify_title_values(
            all_titles
        )
    )

    if (
        status
        == "title_resolved_exact"
    ):
        resolved = exact[0]

    else:
        resolved = ""

    evidence_ids = sorted(
        logical_id
        for logical_id, titles
        in titles_by_lookup.items()
        if titles
    )

    return {
        "title_status":
            status,

        "resolved_title":
            resolved,

        "title_variants_json":
            json.dumps(
                exact,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),

        "title_evidence_lookup_ids":
            ";".join(
                evidence_ids
            ),
    }


def build_reconciliation(
    *,
    source_root: Path,
    archive_root: Path,
) -> dict[str, Any]:
    input_data = load_inputs(
        source_root=source_root,
        archive_root=archive_root,
    )

    lookup_evidence = (
        build_lookup_evidence(
            archive_root=archive_root,
            input_data=input_data,
        )
    )

    components = input_data[
        "components"
    ]

    assignments_by_component = (
        input_data[
            "assignments_by_component"
        ]
    )

    component_rows: list[
        dict[str, str]
    ] = []

    evidence_rows: list[
        dict[str, str]
    ] = []

    identifier_counts: Counter[
        str
    ] = Counter()

    title_counts: Counter[
        str
    ] = Counter()

    for component in sorted(
        components,
        key=lambda row: row[
            "component_id"
        ],
    ):
        component_id = component[
            "component_id"
        ]

        assignments = sorted(
            assignments_by_component[
                component_id
            ],
            key=lambda row: row[
                "assignment_id"
            ],
        )

        expected_assignment_count = int(
            component[
                "assignment_count"
            ]
        )

        if len(
            assignments
        ) != expected_assignment_count:
            raise ReconciliationError(
                "Component assignment count "
                "does not reproduce: "
                f"{component_id}"
            )

        identifier_state = (
            derive_identifier_state(
                component=component,
                assignments=assignments,
                lookup_evidence=lookup_evidence,
            )
        )

        title_state = (
            derive_title_state(
                component=component,
                assignments=assignments,
                lookup_evidence=lookup_evidence,
            )
        )

        identifier_counts[
            identifier_state[
                "identifier_status"
            ]
        ] += 1

        title_counts[
            title_state[
                "title_status"
            ]
        ] += 1

        all_lookup_ids = sorted(
            {
                row[
                    "logical_lookup_id"
                ]
                for row in assignments
            }
        )

        component_rows.append({
            "component_id":
                component_id,

            "questions":
                component[
                    "questions"
                ],

            "attention_reasons":
                component[
                    "attention_reasons"
                ],

            "source_providers":
                component[
                    "source_providers"
                ],

            **identifier_state,

            **title_state,

            "all_logical_lookup_ids":
                ";".join(
                    all_lookup_ids
                ),

            "component_merge_performed":
                "false",

            "scientific_screening_performed":
                "false",
        })

        for assignment in assignments:
            logical_id = assignment[
                "logical_lookup_id"
            ]

            evidence = lookup_evidence[
                logical_id
            ]

            returned = evidence[
                "identifiers"
            ]

            dois = sorted(
                identifier_value(
                    token
                )
                for token in returned
                if (
                    identifier_namespace(
                        token
                    )
                    == "doi"
                )
            )

            pmids = sorted(
                identifier_value(
                    token
                )
                for token in returned
                if (
                    identifier_namespace(
                        token
                    )
                    == "pmid"
                )
            )

            evidence_rows.append({
                "component_id":
                    component_id,

                "assignment_id":
                    assignment[
                        "assignment_id"
                    ],

                "logical_lookup_id":
                    logical_id,

                "provider":
                    assignment[
                        "provider"
                    ],

                "route":
                    assignment[
                        "route"
                    ],

                "status":
                    evidence[
                        "status"
                    ],

                "policy_class":
                    assignment[
                        "policy_class"
                    ],

                "purposes":
                    assignment[
                        "purposes"
                    ],

                "requested_identifier_namespace":
                    assignment[
                        "identifier_namespace"
                    ],

                "requested_identifier":
                    assignment[
                        "identifier"
                    ],

                "returned_dois":
                    ";".join(
                        dois
                    ),

                "returned_pmids":
                    ";".join(
                        pmids
                    ),

                "title_candidates_json":
                    json.dumps(
                        evidence[
                            "titles"
                        ],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
            })

    if len(component_rows) != 1342:
        raise ReconciliationError(
            "Reconciliation did not emit "
            "exactly 1,342 component rows"
        )

    if len(evidence_rows) != 1847:
        raise ReconciliationError(
            "Evidence ledger did not emit "
            "exactly 1,847 assignment rows"
        )

    manifest = {
        "status":
            "RECONCILED_METADATA_PRE_SCREENING",

        "schema_version":
            1,

        "component_count":
            len(
                component_rows
            ),

        "evidence_row_count":
            len(
                evidence_rows
            ),

        "logical_lookup_count":
            1731,

        "identifier_status_counts":
            dict(
                sorted(
                    identifier_counts.items()
                )
            ),

        "title_status_counts":
            dict(
                sorted(
                    title_counts.items()
                )
            ),

        "component_merge_performed":
            False,

        "scientific_screening_performed":
            False,

        "network_access_performed":
            False,

        "raw_retrieval_archive_modified":
            False,
    }

    return {
        "component_rows":
            component_rows,

        "evidence_rows":
            evidence_rows,

        "manifest":
            manifest,
    }


def assert_frozen_counts(
    result: dict[str, Any],
) -> None:
    manifest = result[
        "manifest"
    ]

    if (
        manifest[
            "identifier_status_counts"
        ]
        != EXPECTED_IDENTIFIER_STATUS_COUNTS
    ):
        raise ReconciliationError(
            "Identifier-state counts do "
            "not reproduce frozen design: "
            f"{manifest['identifier_status_counts']!r}"
        )

    if (
        manifest[
            "title_status_counts"
        ]
        != EXPECTED_TITLE_STATUS_COUNTS
    ):
        raise ReconciliationError(
            "Title-state counts do not "
            "reproduce frozen design: "
            f"{manifest['title_status_counts']!r}"
        )

    if (
        manifest[
            "component_count"
        ]
        != 1342
    ):
        raise ReconciliationError(
            "Frozen component count "
            "does not reproduce"
        )

    if (
        manifest[
            "evidence_row_count"
        ]
        != 1847
    ):
        raise ReconciliationError(
            "Frozen evidence row count "
            "does not reproduce"
        )

    if (
        manifest[
            "component_merge_performed"
        ]
        is not False
    ):
        raise ReconciliationError(
            "Component merge boundary "
            "violated"
        )

    if (
        manifest[
            "scientific_screening_performed"
        ]
        is not False
    ):
        raise ReconciliationError(
            "Scientific screening boundary "
            "violated"
        )


def write_tsv(
    *,
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            delimiter="\t",
            fieldnames=fields,
            lineterminator="\n",
        )

        writer.writeheader()

        for row in rows:
            if set(
                row
            ) != set(
                fields
            ):
                raise ReconciliationError(
                    "Attempt to write TSV "
                    "with unexpected fields"
                )

            writer.writerow(
                row
            )


def output_root_is_safe(
    *,
    output_root: Path,
    archive_root: Path,
    source_root: Path,
) -> None:
    output_root = (
        output_root
        .resolve()
    )

    archive_root = (
        archive_root
        .resolve()
    )

    source_root = (
        source_root
        .resolve()
    )

    if output_root == archive_root:
        raise ReconciliationError(
            "Output root cannot equal "
            "retrieval archive root"
        )

    if archive_root in (
        output_root.parents
    ):
        raise ReconciliationError(
            "Output root cannot be "
            "inside retrieval archive"
        )

    if output_root in (
        archive_root.parents
    ):
        raise ReconciliationError(
            "Output root cannot contain "
            "retrieval archive"
        )

    if output_root == source_root:
        raise ReconciliationError(
            "Output root cannot equal "
            "source directory"
        )


def write_output(
    *,
    result: dict[str, Any],
    output_root: Path,
    archive_root: Path,
    source_root: Path,
) -> None:
    output_root_is_safe(
        output_root=output_root,
        archive_root=archive_root,
        source_root=source_root,
    )

    if output_root.exists():
        if any(
            output_root.iterdir()
        ):
            raise ReconciliationError(
                "Output root already exists "
                "and is non-empty: "
                f"{output_root}"
            )

    else:
        output_root.mkdir(
            parents=True,
            exist_ok=False,
        )

    component_path = (
        output_root
        / COMPONENT_OUTPUT_FILENAME
    )

    evidence_path = (
        output_root
        / EVIDENCE_OUTPUT_FILENAME
    )

    manifest_path = (
        output_root
        / MANIFEST_FILENAME
    )

    checksums_path = (
        output_root
        / CHECKSUMS_FILENAME
    )

    write_tsv(
        path=component_path,
        fields=COMPONENT_FIELDS,
        rows=result[
            "component_rows"
        ],
    )

    write_tsv(
        path=evidence_path,
        fields=EVIDENCE_FIELDS,
        rows=result[
            "evidence_rows"
        ],
    )

    manifest = dict(
        result[
            "manifest"
        ]
    )

    manifest[
        "component_reconciliation_sha256"
    ] = sha256_file(
        component_path
    )

    manifest[
        "reconciliation_evidence_sha256"
    ] = sha256_file(
        evidence_path
    )

    manifest_path.write_bytes(
        canonical_json_bytes(
            manifest
        )
    )

    checksum_targets = [
        component_path,
        evidence_path,
        manifest_path,
    ]

    lines = []

    for path in checksum_targets:
        lines.append(
            f"{sha256_file(path)}  "
            f"{path.name}\n"
        )

    checksums_path.write_text(
        "".join(
            lines
        ),
        encoding="utf-8",
    )


def validate_output(
    output_root: Path,
) -> dict[str, Any]:
    component_path = (
        output_root
        / COMPONENT_OUTPUT_FILENAME
    )

    evidence_path = (
        output_root
        / EVIDENCE_OUTPUT_FILENAME
    )

    manifest_path = (
        output_root
        / MANIFEST_FILENAME
    )

    checksums_path = (
        output_root
        / CHECKSUMS_FILENAME
    )

    for path in [
        component_path,
        evidence_path,
        manifest_path,
        checksums_path,
    ]:
        if not path.is_file():
            raise ReconciliationError(
                "Missing reconciliation "
                f"output file: {path}"
            )

    component_fields, component_rows = (
        read_tsv(
            component_path
        )
    )

    evidence_fields, evidence_rows = (
        read_tsv(
            evidence_path
        )
    )

    require_exact_fields(
        component_fields,
        COMPONENT_FIELDS,
        "component reconciliation output",
    )

    require_exact_fields(
        evidence_fields,
        EVIDENCE_FIELDS,
        "reconciliation evidence output",
    )

    if len(component_rows) != 1342:
        raise ReconciliationError(
            "Derived component output "
            "does not contain 1,342 rows"
        )

    if len(evidence_rows) != 1847:
        raise ReconciliationError(
            "Derived evidence output "
            "does not contain 1,847 rows"
        )

    component_ids = [
        row[
            "component_id"
        ]
        for row in component_rows
    ]

    if len(
        set(
            component_ids
        )
    ) != 1342:
        raise ReconciliationError(
            "Derived component output "
            "contains duplicate IDs"
        )

    if any(
        row[
            "component_merge_performed"
        ]
        != "false"
        for row in component_rows
    ):
        raise ReconciliationError(
            "Derived output claims "
            "component merging"
        )

    if any(
        row[
            "scientific_screening_performed"
        ]
        != "false"
        for row in component_rows
    ):
        raise ReconciliationError(
            "Derived output claims "
            "scientific screening"
        )

    identifier_counts = Counter(
        row[
            "identifier_status"
        ]
        for row in component_rows
    )

    title_counts = Counter(
        row[
            "title_status"
        ]
        for row in component_rows
    )

    if (
        dict(
            sorted(
                identifier_counts.items()
            )
        )
        != EXPECTED_IDENTIFIER_STATUS_COUNTS
    ):
        raise ReconciliationError(
            "Derived identifier counts "
            "do not match frozen design"
        )

    if (
        dict(
            sorted(
                title_counts.items()
            )
        )
        != EXPECTED_TITLE_STATUS_COUNTS
    ):
        raise ReconciliationError(
            "Derived title counts "
            "do not match frozen design"
        )

    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    if (
        manifest[
            "component_reconciliation_sha256"
        ]
        != sha256_file(
            component_path
        )
    ):
        raise ReconciliationError(
            "Component output hash "
            "does not match manifest"
        )

    if (
        manifest[
            "reconciliation_evidence_sha256"
        ]
        != sha256_file(
            evidence_path
        )
    ):
        raise ReconciliationError(
            "Evidence output hash "
            "does not match manifest"
        )

    checksum_lines = [
        line
        for line in (
            checksums_path
            .read_text(
                encoding="utf-8"
            )
            .splitlines()
        )
        if line
    ]

    expected_names = {
        COMPONENT_OUTPUT_FILENAME,
        EVIDENCE_OUTPUT_FILENAME,
        MANIFEST_FILENAME,
    }

    observed_names = set()

    for line in checksum_lines:
        digest, name = line.split(
            "  ",
            1,
        )

        observed_names.add(
            name
        )

        target = (
            output_root
            / name
        )

        if digest != sha256_file(
            target
        ):
            raise ReconciliationError(
                "Output checksum mismatch: "
                f"{name}"
            )

    if observed_names != expected_names:
        raise ReconciliationError(
            "Checksum manifest does not "
            "cover exact derived outputs"
        )

    return manifest


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Experiment 07 frozen "
            "post-retrieval reconciliation"
        )
    )

    parser.add_argument(
        "--archive-root",
        type=Path,
        default=DEFAULT_ARCHIVE_ROOT,
    )

    parser.add_argument(
        "--write-output-root",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--assert-frozen-counts",
        action="store_true",
    )

    parser.add_argument(
        "--validate-output-root",
        type=Path,
        default=None,
    )

    return parser.parse_args(
        argv
    )


def main(
    argv: list[str] | None = None,
) -> int:
    args = parse_args(
        argv
    )

    if (
        args.validate_output_root
        is not None
    ):
        manifest = validate_output(
            args.validate_output_root
        )

        print(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    archive_root = (
        args.archive_root
        .resolve()
    )

    source_root = SCRIPT_DIR

    result = build_reconciliation(
        source_root=source_root,
        archive_root=archive_root,
    )

    if args.assert_frozen_counts:
        assert_frozen_counts(
            result
        )

    if (
        args.write_output_root
        is not None
    ):
        write_output(
            result=result,
            output_root=args.write_output_root,
            archive_root=archive_root,
            source_root=source_root,
        )

        manifest = validate_output(
            args.write_output_root
        )

    else:
        manifest = result[
            "manifest"
        ]

    print(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
