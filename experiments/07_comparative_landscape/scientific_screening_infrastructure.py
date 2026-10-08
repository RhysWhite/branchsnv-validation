#!/usr/bin/env python3

"""
Experiment 07 scientific-screening infrastructure.

This module creates only the deterministic pre-decision screening
infrastructure defined by the frozen scientific-screening design.

It does NOT:
- make record-level include/exclude decisions;
- infer exclusions from missing metadata;
- identify or consolidate software/method identities;
- perform source-backed method assessment;
- assign analytical roles;
- select canonical publications;
- promote Wave 1 anchors;
- perform network requests;
- modify discovery, retrieval or reconciliation evidence; or
- modify the historical screening_log.tsv.

Default CLI behaviour is dry-run only.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import argparse
import csv
import hashlib
import io
import json


HERE = Path(__file__).resolve().parent

REPO_ROOT = HERE.parent.parent

RESULTS_ROOT = (
    REPO_ROOT
    / "results"
    / "07_comparative_landscape"
)

DEFAULT_DATABASE = (
    RESULTS_ROOT
    / "merged_search_universe"
    / "deduplicated_records.tsv"
)

DEFAULT_CITATION = (
    RESULTS_ROOT
    / "citation_wave_0"
    / "neighbour_records.tsv"
)

DEFAULT_RECON_ROOT = (
    RESULTS_ROOT
    / "post_retrieval_reconciliation"
)

DESIGN_PATH = (
    HERE
    / "scientific_screening_design.json"
)

IDENTITY_BASELINE_PATH = (
    HERE
    / "screening_entity_identity_baseline.json"
)

CROSS_BASELINE_PATH = (
    HERE
    / "cross_stage_screening_entity_baseline.json"
)

IDENTITY_SOURCE = (
    HERE
    / "screening_entity_identity.py"
)

CROSS_SOURCE = (
    HERE
    / "cross_stage_screening_entities.py"
)

HISTORICAL_SCREENING_LOG = (
    HERE
    / "screening_log.tsv"
)


QUEUE_FILENAME = (
    "baseline_screening_queue.tsv"
)

ESCALATION_FILENAME = (
    "source_escalation.tsv"
)

METHOD_ASSESSMENT_FILENAME = (
    "method_assessments.tsv"
)

METHOD_EVIDENCE_FILENAME = (
    "method_evidence.tsv"
)

CANONICAL_FILENAME = (
    "canonical_publications.tsv"
)

WAVE1_FILENAME = (
    "wave1_promotion_candidates.tsv"
)

MANIFEST_FILENAME = (
    "manifest.json"
)

CHECKSUMS_FILENAME = (
    "checksums.sha256"
)


QUEUE_FIELDS = [
    "screening_entity_id",
    "screening_entity_class",
    "publication_reconciliation_key",
    "database_dedup_keys",
    "biotools_id",
    "citation_provenance_ids",
    "discovery_stages",
    "citation_wave_provenance",
    "title_or_software_name",
    "title_variants",
    "year",
    "doi",
    "pmid",
    "openalex_id",
    "omid",
    "identity_attention_status",
    "metadata_screenability",
    "screening_state",
    "record_decision",
    "exclusion_reason_code",
    "candidate_method_flag",
    "evidence_escalation_status",
    "operator",
    "decision_batch",
    "notes",
]


ESCALATION_FIELDS = [
    "screening_entity_id",
    "escalation_reason",
    "source_class",
    "source_locator",
    "evidence_accessed",
    "operator",
    "decision_batch",
    "resulting_screening_state",
    "resulting_record_decision",
    "notes",
]


METHOD_ASSESSMENT_FIELDS = [
    "method_id",
    "supporting_screening_entity_ids",
    "method_identity_status",
    "criterion_L1_documentation_exists",
    "criterion_L2_software_implementation_exists",
    "criterion_L3_relevant_data_scope",
    "criterion_L4_analytical_role",
    "landscape_decision",
    "landscape_exclusion_reason",
    "role_clade_lineage_marker_discovery",
    "role_branch_change_reconstruction",
    "role_homoplasy_recurrent_state_analysis",
    "role_marker_deployment_genotyping",
    "role_general_phylogenetic_parsimony_infrastructure",
    "role_upstream_variant_recombination_phylogeny_workflows",
    "directness_role",
    "operator",
    "decision_batch",
    "notes",
]


METHOD_EVIDENCE_FIELDS = [
    "method_id",
    "screening_entity_id",
    "evidence_type",
    "source_class",
    "source_locator",
    "evidence_statement",
    "supports_field",
    "operator",
    "decision_batch",
    "notes",
]


CANONICAL_FIELDS = [
    "method_id",
    "canonical_publication_status",
    "screening_entity_id",
    "doi",
    "pmid",
    "openalex_id",
    "stable_authoritative_url",
    "selection_basis",
    "previously_citation_expanded",
    "operator",
    "decision_batch",
    "notes",
]


WAVE1_FIELDS = [
    "method_id",
    "canonical_screening_entity_id",
    "canonical_publication_identifier",
    "method_identity_confirmed",
    "landscape_include",
    "direct_or_near_direct",
    "canonical_publication_established",
    "not_previously_expanded",
    "promotion_eligible",
    "operator",
    "decision_batch",
    "notes",
]


EXPECTED_ENTITY_CLASS_COUNTS = {
    "publication": 94898,
    "software_registry": 215,
}


EXPECTED_SCREENING_STATE_COUNTS = {
    "blocked_metadata": 484,
    "ready": 94629,
}


EXPECTED_METADATA_COUNTS = {
    "blocked_title_conflict": 2,
    "blocked_title_unresolved": 482,
    "screenable": 94629,
}


class ScreeningInfrastructureError(
    RuntimeError
):
    pass


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


def historical_compact_sha256(
    value: Any,
) -> str:
    """
    Historical Experiment 07 subsidiary-hash contract.

    The cross-stage freeze used compact, sorted JSON WITHOUT
    a trailing newline for:
      - automatic_links
      - cross_stage_conflicts
      - publication_components
      - software_registry_components

    The full complete_result used cross.result_bytes(), which
    DOES append a trailing newline.
    """
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )

    return sha256_bytes(
        payload
    )


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
    ).encode(
        "utf-8"
    )


def semicolon(
    values: list[str],
) -> str:
    return ";".join(
        sorted(
            {
                str(value)
                for value in values
                if str(value)
            }
        )
    )


def json_list(
    values: list[str],
) -> str:
    return json.dumps(
        sorted(
            {
                str(value)
                for value in values
                if str(value)
            }
        ),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def read_tsv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        fields = list(
            reader.fieldnames
            or []
        )

        rows = list(
            reader
        )

    return fields, rows


def tsv_bytes(
    *,
    fields: list[str],
    rows: list[dict[str, str]],
) -> bytes:
    stream = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        stream,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )

    writer.writeheader()

    for row in rows:
        if set(
            row
        ) != set(
            fields
        ):
            raise ScreeningInfrastructureError(
                "TSV row schema mismatch"
            )

        writer.writerow(
            row
        )

    return stream.getvalue().encode(
        "utf-8"
    )


def write_tsv(
    *,
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:
    path.write_bytes(
        tsv_bytes(
            fields=fields,
            rows=rows,
        )
    )


def validate_design() -> dict:
    value = json.loads(
        DESIGN_PATH.read_text(
            encoding="utf-8"
        )
    )

    if (
        value[
            "status"
        ]
        != "FROZEN_PRE_IMPLEMENTATION"
    ):
        raise ScreeningInfrastructureError(
            "Scientific-screening design "
            "is not FROZEN_PRE_IMPLEMENTATION"
        )

    if value[
        "baseline_universe"
    ] != {
        "attention_overlay_entities": 1342,
        "publication_entities": 94898,
        "screening_entities": 95113,
        "software_registry_entities": 215,
    }:
        raise ScreeningInfrastructureError(
            "Frozen baseline universe changed"
        )

    if value[
        "initial_screenability"
    ][
        "screenable_entities"
    ] != 94629:
        raise ScreeningInfrastructureError(
            "Frozen screenable count changed"
        )

    if value[
        "initial_screenability"
    ][
        "blocked_metadata_entities"
    ] != 484:
        raise ScreeningInfrastructureError(
            "Frozen metadata-block count changed"
        )

    boundary = value[
        "scientific_boundary"
    ]

    for field in [
        "screening_decisions_made",
        "method_assessments_made",
        "new_role_assignments_made",
        "wave1_promotions_made",
        "historical_screening_log_rows",
    ]:
        if boundary[
            field
        ] != 0:
            raise ScreeningInfrastructureError(
                "Frozen scientific boundary "
                f"is non-zero: {field}"
            )

    return value


def validate_historical_log() -> None:
    fields, rows = read_tsv(
        HISTORICAL_SCREENING_LOG
    )

    if fields != [
        "record_id",
        "source",
        "query_id",
        "title",
        "year",
        "identifier",
        "tool_candidate",
        "screening_status",
        "exclusion_reason",
        "notes",
    ]:
        raise ScreeningInfrastructureError(
            "Historical screening_log.tsv "
            "schema changed"
        )

    if rows:
        raise ScreeningInfrastructureError(
            "Historical screening_log.tsv "
            "is no longer empty"
        )


def load_frozen_modules():
    identity_baseline = json.loads(
        IDENTITY_BASELINE_PATH.read_text(
            encoding="utf-8"
        )
    )

    cross_baseline = json.loads(
        CROSS_BASELINE_PATH.read_text(
            encoding="utf-8"
        )
    )

    expected_identity = (
        identity_baseline[
            "implementation_sha256"
        ][
            "screening_entity_identity.py"
        ]
    )

    expected_cross = (
        cross_baseline[
            "implementation_sha256"
        ][
            "cross_stage_screening_entities.py"
        ]
    )

    if (
        sha256_file(
            IDENTITY_SOURCE
        )
        != expected_identity
    ):
        raise ScreeningInfrastructureError(
            "Frozen identity implementation changed"
        )

    if (
        sha256_file(
            CROSS_SOURCE
        )
        != expected_cross
    ):
        raise ScreeningInfrastructureError(
            "Frozen cross-stage implementation changed"
        )

    import screening_entity_identity as identity
    import cross_stage_screening_entities as cross

    return (
        identity,
        cross,
        cross_baseline,
    )


def validate_cross_stage_result(
    *,
    universe: dict,
    cross,
    baseline: dict,
) -> dict[str, str]:
    expected = baseline[
        "derived_sha256"
    ]

    observed = {
        "automatic_links":
            historical_compact_sha256(
                universe[
                    "automatic_links"
                ]
            ),

        "cross_stage_conflicts":
            historical_compact_sha256(
                universe[
                    "cross_stage_conflicts"
                ]
            ),

        "publication_components":
            historical_compact_sha256(
                universe[
                    "publication_components"
                ]
            ),

        "software_registry_components":
            historical_compact_sha256(
                universe[
                    "software_registry_components"
                ]
            ),

        "complete_result":
            sha256_bytes(
                cross.result_bytes(
                    universe
                )
            ),
    }

    if observed != expected:
        raise ScreeningInfrastructureError(
            "Frozen cross-stage derived hashes "
            "do not reproduce:\n"
            + json.dumps(
                {
                    "observed":
                        observed,
                    "expected":
                        expected,
                },
                indent=2,
                sort_keys=True,
            )
        )

    return observed


def load_reconciliation_overlay(
    recon_root: Path,
    design: dict,
) -> dict[
    str,
    dict[str, str],
]:
    path = (
        recon_root
        / "component_reconciliation.tsv"
    )

    expected_sha = (
        design[
            "frozen_dependencies"
        ][
            "reconciliation_component_output_sha256"
        ]
    )

    if sha256_file(
        path
    ) != expected_sha:
        raise ScreeningInfrastructureError(
            "Reconciliation component output "
            "does not match frozen design SHA"
        )

    fields, rows = read_tsv(
        path
    )

    required = {
        "component_id",
        "identifier_status",
        "derived_doi",
        "derived_pmid",
        "title_status",
        "resolved_title",
        "title_variants_json",
        "component_merge_performed",
        "scientific_screening_performed",
    }

    missing = (
        required
        - set(
            fields
        )
    )

    if missing:
        raise ScreeningInfrastructureError(
            "Reconciliation overlay missing: "
            + ",".join(
                sorted(
                    missing
                )
            )
        )

    if len(
        rows
    ) != 1342:
        raise ScreeningInfrastructureError(
            "Reconciliation overlay is not "
            "exactly 1,342 rows"
        )

    output = {}

    for row in rows:
        key = row[
            "component_id"
        ]

        if key in output:
            raise ScreeningInfrastructureError(
                "Duplicate reconciliation "
                "component ID: "
                + key
            )

        if row[
            "component_merge_performed"
        ] != "false":
            raise ScreeningInfrastructureError(
                "Reconciliation reports "
                "component merge"
            )

        if row[
            "scientific_screening_performed"
        ] != "false":
            raise ScreeningInfrastructureError(
                "Reconciliation reports "
                "scientific screening"
            )

        output[
            key
        ] = row

    return output


def citation_wave_by_row_sha(
    *,
    identity,
    citation_rows: list[
        dict[str, str]
    ],
) -> dict[
    str,
    set[str],
]:
    mapping: dict[
        str,
        set[str],
    ] = {}

    for row in citation_rows:
        digest = identity.row_sha256(
            row
        )

        wave = row.get(
            "wave",
            "",
        ).strip()

        if not wave:
            raise ScreeningInfrastructureError(
                "Citation provenance row "
                "lacks wave"
            )

        mapping.setdefault(
            digest,
            set(),
        ).add(
            wave
        )

    return mapping


def title_screenability(
    *,
    component: dict,
    overlay: dict[str, str] | None,
) -> tuple[
    str,
    str,
    list[str],
    str,
]:
    base_titles = sorted(
        {
            str(value)
            for value
            in component.get(
                "titles",
                [],
            )
            if str(value)
        }
    )

    entity_class = component[
        "screening_entity_class"
    ]

    if entity_class == "software_registry":
        if not base_titles:
            raise ScreeningInfrastructureError(
                "Software-registry component "
                "has no screenable name: "
                + component[
                    "screening_component_id"
                ]
            )

        selected = (
            base_titles[0]
            if len(
                base_titles
            ) == 1
            else ""
        )

        return (
            "screenable",
            selected,
            base_titles,
            "ready",
        )

    if entity_class != "publication":
        raise ScreeningInfrastructureError(
            "Unknown screening entity class"
        )

    if overlay is None:
        if not base_titles:
            raise ScreeningInfrastructureError(
                "Titleless publication is "
                "missing from reconciliation overlay: "
                + component[
                    "screening_component_id"
                ]
            )

        selected = (
            base_titles[0]
            if len(
                base_titles
            ) == 1
            else ""
        )

        return (
            "screenable",
            selected,
            base_titles,
            "ready",
        )

    status = overlay[
        "title_status"
    ]

    if status == "not_applicable":
        if not base_titles:
            raise ScreeningInfrastructureError(
                "title_status=not_applicable "
                "but component has no title"
            )

        selected = (
            base_titles[0]
            if len(
                base_titles
            ) == 1
            else ""
        )

        return (
            "screenable",
            selected,
            base_titles,
            "ready",
        )

    try:
        variants = json.loads(
            overlay[
                "title_variants_json"
            ]
        )

    except json.JSONDecodeError as exc:
        raise ScreeningInfrastructureError(
            "Invalid reconciliation "
            "title_variants_json"
        ) from exc

    if not isinstance(
        variants,
        list,
    ):
        raise ScreeningInfrastructureError(
            "title_variants_json is not a list"
        )

    variants = sorted(
        {
            str(value)
            for value in variants
            if str(value)
        }
    )

    resolved = overlay[
        "resolved_title"
    ].strip()

    if status == "title_resolved_exact":
        if not resolved:
            raise ScreeningInfrastructureError(
                "Resolved-title state lacks title"
            )

        if not variants:
            variants = [
                resolved
            ]

        return (
            "screenable",
            resolved,
            variants,
            "ready",
        )

    if status == "title_equivalent_variants":
        if resolved:
            raise ScreeningInfrastructureError(
                "Equivalent variants contain "
                "selected spelling"
            )

        if len(
            variants
        ) < 2:
            raise ScreeningInfrastructureError(
                "Equivalent-variant state "
                "lacks multiple exact variants"
            )

        return (
            "screenable",
            "",
            variants,
            "ready",
        )

    if status == "title_conflict_hold":
        if resolved:
            raise ScreeningInfrastructureError(
                "Title conflict contains winner"
            )

        if len(
            variants
        ) < 2:
            raise ScreeningInfrastructureError(
                "Title conflict lacks variants"
            )

        return (
            "blocked_title_conflict",
            "",
            variants,
            "blocked_metadata",
        )

    if status == "title_unresolved":
        if resolved or variants:
            raise ScreeningInfrastructureError(
                "Unresolved title carries "
                "inferred title evidence"
            )

        return (
            "blocked_title_unresolved",
            "",
            [],
            "blocked_metadata",
        )

    raise ScreeningInfrastructureError(
        "Unknown title status: "
        + status
    )


def build_queue(
    *,
    universe: dict,
    database_identity: dict,
    citation_identity: dict,
    citation_rows: list[
        dict[str, str]
    ],
    overlay: dict[
        str,
        dict[str, str],
    ],
    identity,
) -> list[
    dict[str, str]
]:
    components = (
        list(
            universe[
                "publication_components"
            ]
        )
        + list(
            universe[
                "software_registry_components"
            ]
        )
    )

    if len(
        components
    ) != 95113:
        raise ScreeningInfrastructureError(
            "Cross-stage universe does not "
            "contain exactly 95,113 entities"
        )

    component_by_id = {}

    for component in components:
        key = component[
            "screening_component_id"
        ]

        if key in component_by_id:
            raise ScreeningInfrastructureError(
                "Duplicate screening component ID"
            )

        component_by_id[
            key
        ] = component

    attention_ids = {
        row[
            "screening_component_id"
        ]
        for row in components
        if row.get(
            "attention_reasons"
        )
    }

    if attention_ids != set(
        overlay
    ):
        raise ScreeningInfrastructureError(
            "Reconciliation overlay does not "
            "exactly equal attention universe"
        )

    database_entities = {
        row[
            "provisional_entity_key"
        ]:
            row
        for row in database_identity[
            "entities"
        ]
    }

    citation_entities = {
        row[
            "provisional_entity_key"
        ]:
            row
        for row in citation_identity[
            "entities"
        ]
    }

    wave_by_sha = (
        citation_wave_by_row_sha(
            identity=identity,
            citation_rows=citation_rows,
        )
    )

    queue = []

    for component_id in sorted(
        component_by_id
    ):
        component = component_by_id[
            component_id
        ]

        reconciliation = overlay.get(
            component_id
        )

        (
            metadata_screenability,
            display_title,
            title_variants,
            screening_state,
        ) = title_screenability(
            component=component,
            overlay=reconciliation,
        )

        database_dedup_keys = []
        discovery_stages = []

        for entity_key in component.get(
            "database_entity_keys",
            [],
        ):
            entity = database_entities.get(
                entity_key
            )

            if entity is None:
                raise ScreeningInfrastructureError(
                    "Unknown database entity key: "
                    + entity_key
                )

            database_dedup_keys.extend(
                entity.get(
                    "database_dedup_keys",
                    [],
                )
            )

            discovery_stages.extend(
                entity.get(
                    "search_stages",
                    [],
                )
            )

        citation_waves = []

        for entity_key in component.get(
            "citation_entity_keys",
            [],
        ):
            entity = citation_entities.get(
                entity_key
            )

            if entity is None:
                raise ScreeningInfrastructureError(
                    "Unknown citation entity key: "
                    + entity_key
                )

            for source_sha in entity.get(
                "source_row_sha256s",
                [],
            ):
                waves = wave_by_sha.get(
                    source_sha
                )

                if not waves:
                    raise ScreeningInfrastructureError(
                        "Citation provenance SHA "
                        "not represented in frozen input"
                    )

                citation_waves.extend(
                    waves
                )

        for wave in sorted(
            set(
                citation_waves
            )
        ):
            discovery_stages.append(
                "citation_wave_"
                + wave
            )

        identifier_attention = ""

        derived_doi = ""
        derived_pmid = ""

        if reconciliation is not None:
            if reconciliation[
                "identifier_status"
            ] != "not_applicable":
                identifier_attention = (
                    reconciliation[
                        "identifier_status"
                    ]
                )

            derived_doi = reconciliation[
                "derived_doi"
            ].strip()

            derived_pmid = reconciliation[
                "derived_pmid"
            ].strip()

        dois = list(
            component.get(
                "doi_values",
                [],
            )
        )

        pmids = list(
            component.get(
                "pmid_values",
                [],
            )
        )

        if derived_doi:
            dois.append(
                derived_doi
            )

        if derived_pmid:
            pmids.append(
                derived_pmid
            )

        entity_class = component[
            "screening_entity_class"
        ]

        biotools_id = ""

        if entity_class == "software_registry":
            biotools_id = semicolon(
                list(
                    component.get(
                        "source_record_ids",
                        [],
                    )
                )
            )

        row = {
            "screening_entity_id":
                component_id,

            "screening_entity_class":
                entity_class,

            "publication_reconciliation_key":
                (
                    component_id
                    if entity_class
                    == "publication"
                    else ""
                ),

            "database_dedup_keys":
                semicolon(
                    database_dedup_keys
                ),

            "biotools_id":
                biotools_id,

            "citation_provenance_ids":
                semicolon(
                    list(
                        component.get(
                            "citation_source_record_ids",
                            [],
                        )
                    )
                ),

            "discovery_stages":
                semicolon(
                    discovery_stages
                ),

            "citation_wave_provenance":
                semicolon(
                    citation_waves
                ),

            "title_or_software_name":
                display_title,

            "title_variants":
                json_list(
                    title_variants
                ),

            "year":
                semicolon(
                    list(
                        component.get(
                            "years",
                            [],
                        )
                    )
                ),

            "doi":
                semicolon(
                    dois
                ),

            "pmid":
                semicolon(
                    pmids
                ),

            "openalex_id":
                semicolon(
                    list(
                        component.get(
                            "openalex_id_values",
                            [],
                        )
                    )
                ),

            "omid":
                semicolon(
                    list(
                        component.get(
                            "omid_values",
                            [],
                        )
                    )
                ),

            "identity_attention_status":
                identifier_attention,

            "metadata_screenability":
                metadata_screenability,

            "screening_state":
                screening_state,

            # Scientific-decision fields remain deliberately empty.
            "record_decision":
                "",

            "exclusion_reason_code":
                "",

            "candidate_method_flag":
                "",

            "evidence_escalation_status":
                "",

            "operator":
                "",

            "decision_batch":
                "",

            "notes":
                "",
        }

        if set(
            row
        ) != set(
            QUEUE_FIELDS
        ):
            raise ScreeningInfrastructureError(
                "Internal screening queue "
                "schema mismatch"
            )

        queue.append(
            row
        )

    return queue


def validate_queue(
    queue: list[
        dict[str, str]
    ],
) -> dict:
    if len(
        queue
    ) != 95113:
        raise ScreeningInfrastructureError(
            "Queue row count is not 95,113"
        )

    ids = [
        row[
            "screening_entity_id"
        ]
        for row in queue
    ]

    if len(
        set(
            ids
        )
    ) != 95113:
        raise ScreeningInfrastructureError(
            "Queue IDs are not unique"
        )

    if ids != sorted(
        ids
    ):
        raise ScreeningInfrastructureError(
            "Queue is not deterministically "
            "ordered by screening_entity_id"
        )

    class_counts = Counter(
        row[
            "screening_entity_class"
        ]
        for row in queue
    )

    state_counts = Counter(
        row[
            "screening_state"
        ]
        for row in queue
    )

    metadata_counts = Counter(
        row[
            "metadata_screenability"
        ]
        for row in queue
    )

    if dict(
        sorted(
            class_counts.items()
        )
    ) != EXPECTED_ENTITY_CLASS_COUNTS:
        raise ScreeningInfrastructureError(
            "Screening-entity class counts drifted"
        )

    if dict(
        sorted(
            state_counts.items()
        )
    ) != EXPECTED_SCREENING_STATE_COUNTS:
        raise ScreeningInfrastructureError(
            "Screening-state counts drifted"
        )

    if dict(
        sorted(
            metadata_counts.items()
        )
    ) != EXPECTED_METADATA_COUNTS:
        raise ScreeningInfrastructureError(
            "Metadata-screenability counts drifted"
        )

    decision_fields = [
        "record_decision",
        "exclusion_reason_code",
        "candidate_method_flag",
        "evidence_escalation_status",
        "operator",
        "decision_batch",
        "notes",
    ]

    for row in queue:
        if row[
            "screening_state"
        ] not in {
            "ready",
            "blocked_metadata",
        }:
            raise ScreeningInfrastructureError(
                "Initial queue contains "
                "post-screening state"
            )

        for field in decision_fields:
            if row[
                field
            ]:
                raise ScreeningInfrastructureError(
                    "Pre-decision queue contains "
                    f"non-empty {field}: "
                    + row[
                        "screening_entity_id"
                    ]
                )

    return {
        "screening_entity_count":
            len(
                queue
            ),

        "entity_class_counts":
            dict(
                sorted(
                    class_counts.items()
                )
            ),

        "screening_state_counts":
            dict(
                sorted(
                    state_counts.items()
                )
            ),

        "metadata_screenability_counts":
            dict(
                sorted(
                    metadata_counts.items()
                )
            ),

        "queue_sha256":
            sha256_bytes(
                tsv_bytes(
                    fields=QUEUE_FIELDS,
                    rows=queue,
                )
            ),
    }


def build_infrastructure(
    *,
    database_path: Path,
    citation_path: Path,
    recon_root: Path,
) -> dict:
    design = validate_design()

    validate_historical_log()

    (
        identity,
        cross,
        cross_baseline,
    ) = load_frozen_modules()

    frozen_inputs = cross_baseline[
        "frozen_input_sha256"
    ]

    if sha256_file(
        database_path
    ) != frozen_inputs[
        "merged_database_universe"
    ]:
        raise ScreeningInfrastructureError(
            "Database input SHA differs "
            "from frozen baseline"
        )

    if sha256_file(
        citation_path
    ) != frozen_inputs[
        "citation_wave_0_neighbours"
    ]:
        raise ScreeningInfrastructureError(
            "Citation input SHA differs "
            "from frozen baseline"
        )

    # identity.read_tsv() returns the row list directly.
    database_rows = identity.read_tsv(
        database_path
    )

    citation_rows = identity.read_tsv(
        citation_path
    )

    if len(
        database_rows
    ) != 79917:
        raise ScreeningInfrastructureError(
            "Frozen database row count changed"
        )

    if len(
        citation_rows
    ) != 33071:
        raise ScreeningInfrastructureError(
            "Frozen citation row count changed"
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

    if database_identity[
        "entity_count"
    ] != 79762:
        raise ScreeningInfrastructureError(
            "Database identity count changed"
        )

    if citation_identity[
        "entity_count"
    ] != 17605:
        raise ScreeningInfrastructureError(
            "Citation identity count changed"
        )

    universe = (
        cross.build_cross_stage_screening_universe(
            database_identity,
            citation_identity,
        )
    )

    derived_hashes = (
        validate_cross_stage_result(
            universe=universe,
            cross=cross,
            baseline=cross_baseline,
        )
    )

    if universe[
        "screening_component_count"
    ] != 95113:
        raise ScreeningInfrastructureError(
            "Frozen screening universe "
            "does not reproduce"
        )

    overlay = (
        load_reconciliation_overlay(
            recon_root,
            design,
        )
    )

    queue = build_queue(
        universe=universe,
        database_identity=
            database_identity,
        citation_identity=
            citation_identity,
        citation_rows=
            citation_rows,
        overlay=overlay,
        identity=identity,
    )

    summary = validate_queue(
        queue
    )

    manifest = {
        "status":
            "SCREENING_INFRASTRUCTURE_PRE_DECISION",

        "schema_version":
            1,

        "cross_stage_derived_sha256":
            derived_hashes,

        **summary,

        "source_escalation_rows":
            0,

        "method_assessment_rows":
            0,

        "method_evidence_rows":
            0,

        "canonical_publication_rows":
            0,

        "wave1_promotion_candidate_rows":
            0,

        "scientific_screening_decisions":
            0,

        "method_assessments_made":
            0,

        "new_role_assignments_made":
            0,

        "wave1_promotions_made":
            0,

        "network_access_performed":
            False,

        "historical_screening_log_modified":
            False,

        "discovery_corpus_modified":
            False,

        "retrieval_evidence_modified":
            False,

        "reconciliation_evidence_modified":
            False,
    }

    return {
        "queue":
            queue,

        "source_escalation":
            [],

        "method_assessments":
            [],

        "method_evidence":
            [],

        "canonical_publications":
            [],

        "wave1_promotion_candidates":
            [],

        "manifest":
            manifest,
    }


def output_root_is_safe(
    *,
    output_root: Path,
    recon_root: Path,
) -> None:
    output_root = (
        output_root.resolve()
    )

    recon_root = (
        recon_root.resolve()
    )

    if output_root == recon_root:
        raise ScreeningInfrastructureError(
            "Screening output cannot equal "
            "reconciliation root"
        )

    if recon_root in (
        output_root.parents
    ):
        raise ScreeningInfrastructureError(
            "Screening output cannot be "
            "inside reconciliation root"
        )

    if output_root == HERE.resolve():
        raise ScreeningInfrastructureError(
            "Screening output cannot equal "
            "tracked Experiment 07 directory"
        )


def write_output(
    *,
    result: dict,
    output_root: Path,
    recon_root: Path,
) -> None:
    output_root_is_safe(
        output_root=output_root,
        recon_root=recon_root,
    )

    if output_root.exists():
        if any(
            output_root.iterdir()
        ):
            raise ScreeningInfrastructureError(
                "Output root already exists "
                "and is non-empty"
            )

    else:
        output_root.mkdir(
            parents=True,
            exist_ok=False,
        )

    tables = [
        (
            QUEUE_FILENAME,
            QUEUE_FIELDS,
            result[
                "queue"
            ],
        ),
        (
            ESCALATION_FILENAME,
            ESCALATION_FIELDS,
            result[
                "source_escalation"
            ],
        ),
        (
            METHOD_ASSESSMENT_FILENAME,
            METHOD_ASSESSMENT_FIELDS,
            result[
                "method_assessments"
            ],
        ),
        (
            METHOD_EVIDENCE_FILENAME,
            METHOD_EVIDENCE_FIELDS,
            result[
                "method_evidence"
            ],
        ),
        (
            CANONICAL_FILENAME,
            CANONICAL_FIELDS,
            result[
                "canonical_publications"
            ],
        ),
        (
            WAVE1_FILENAME,
            WAVE1_FIELDS,
            result[
                "wave1_promotion_candidates"
            ],
        ),
    ]

    for name, fields, rows in tables:
        write_tsv(
            path=(
                output_root
                / name
            ),
            fields=fields,
            rows=rows,
        )

    manifest = dict(
        result[
            "manifest"
        ]
    )

    manifest[
        "output_table_sha256"
    ] = {
        name:
            sha256_file(
                output_root
                / name
            )
        for name, _, _
        in tables
    }

    (
        output_root
        / MANIFEST_FILENAME
    ).write_bytes(
        canonical_json_bytes(
            manifest
        )
    )

    checksum_targets = [
        name
        for name, _, _
        in tables
    ] + [
        MANIFEST_FILENAME
    ]

    (
        output_root
        / CHECKSUMS_FILENAME
    ).write_text(
        "".join(
            f"{sha256_file(output_root / name)}  {name}\n"
            for name
            in checksum_targets
        ),
        encoding="utf-8",
    )


def validate_output(
    output_root: Path,
) -> dict:
    expected_files = {
        QUEUE_FILENAME,
        ESCALATION_FILENAME,
        METHOD_ASSESSMENT_FILENAME,
        METHOD_EVIDENCE_FILENAME,
        CANONICAL_FILENAME,
        WAVE1_FILENAME,
        MANIFEST_FILENAME,
        CHECKSUMS_FILENAME,
    }

    observed_files = {
        path.relative_to(
            output_root
        ).as_posix()
        for path
        in output_root.rglob(
            "*"
        )
        if path.is_file()
    }

    if observed_files != expected_files:
        raise ScreeningInfrastructureError(
            "Output artifact set mismatch"
        )

    queue_fields, queue = read_tsv(
        output_root
        / QUEUE_FILENAME
    )

    if queue_fields != QUEUE_FIELDS:
        raise ScreeningInfrastructureError(
            "Queue schema changed"
        )

    queue_summary = validate_queue(
        queue
    )

    empty_tables = [
        (
            ESCALATION_FILENAME,
            ESCALATION_FIELDS,
        ),
        (
            METHOD_ASSESSMENT_FILENAME,
            METHOD_ASSESSMENT_FIELDS,
        ),
        (
            METHOD_EVIDENCE_FILENAME,
            METHOD_EVIDENCE_FIELDS,
        ),
        (
            CANONICAL_FILENAME,
            CANONICAL_FIELDS,
        ),
        (
            WAVE1_FILENAME,
            WAVE1_FIELDS,
        ),
    ]

    for name, expected_fields in (
        empty_tables
    ):
        fields, rows = read_tsv(
            output_root
            / name
        )

        if fields != expected_fields:
            raise ScreeningInfrastructureError(
                name
                + " schema changed"
            )

        if rows:
            raise ScreeningInfrastructureError(
                name
                + " contains scientific rows"
            )

    manifest = json.loads(
        (
            output_root
            / MANIFEST_FILENAME
        ).read_text(
            encoding="utf-8"
        )
    )

    for field in [
        "scientific_screening_decisions",
        "method_assessments_made",
        "new_role_assignments_made",
        "wave1_promotions_made",
    ]:
        if manifest[
            field
        ] != 0:
            raise ScreeningInfrastructureError(
                "Manifest scientific boundary "
                "is non-zero: "
                + field
            )

    if manifest[
        "queue_sha256"
    ] != queue_summary[
        "queue_sha256"
    ]:
        raise ScreeningInfrastructureError(
            "Queue SHA mismatch"
        )

    ledger = (
        output_root
        / CHECKSUMS_FILENAME
    ).read_text(
        encoding="utf-8"
    ).splitlines()

    covered = set()

    for line in ledger:
        if not line:
            continue

        digest, name = line.split(
            "  ",
            1,
        )

        covered.add(
            name
        )

        if digest != sha256_file(
            output_root
            / name
        ):
            raise ScreeningInfrastructureError(
                "Output checksum mismatch: "
                + name
            )

    if covered != (
        expected_files
        - {
            CHECKSUMS_FILENAME
        }
    ):
        raise ScreeningInfrastructureError(
            "Checksum ledger coverage mismatch"
        )

    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )

    parser.add_argument(
        "--citation",
        type=Path,
        default=DEFAULT_CITATION,
    )

    parser.add_argument(
        "--reconciliation-root",
        type=Path,
        default=DEFAULT_RECON_ROOT,
    )

    parser.add_argument(
        "--assert-frozen-counts",
        action="store_true",
    )

    parser.add_argument(
        "--write-output-root",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--validate-output-root",
        type=Path,
        default=None,
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

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

    result = build_infrastructure(
        database_path=
            args.database.resolve(),
        citation_path=
            args.citation.resolve(),
        recon_root=
            args.reconciliation_root.resolve(),
    )

    if args.assert_frozen_counts:
        validate_queue(
            result[
                "queue"
            ]
        )

    if (
        args.write_output_root
        is not None
    ):
        write_output(
            result=result,
            output_root=
                args.write_output_root,
            recon_root=
                args.reconciliation_root,
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
