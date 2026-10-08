#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile

from collections import Counter
from dataclasses import dataclass
from pathlib import Path


EXPECTED_DESIGN_SUMS_SHA = (
    "754288330069b576dff1e68c7c99c6fb57279c4860c3913818984bb6f57cb484"
)

DESIGN_ID = (
    "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1"
)

DESIGN_SUMS_REL = Path(
    "experiments/07_comparative_landscape/"
    "pre_review_triage_future_review_workspace_v1_design.sha256"
)

DESIGN_REL = Path(
    "experiments/07_comparative_landscape/"
    "pre_review_triage_future_review_workspace_v1_design.json"
)

OUTPUT_REL = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_workspace_v1"
)

AUTH_REL = Path(
    "experiments/07_comparative_landscape/"
    "pre_review_triage_future_review_workspace_v1_"
    "generation_authorization.json"
)

AUTHORIZATION_ID = (
    "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_WORKSPACE_V1_"
    "GENERATION_001"
)

GENERATION_CONFIRMATION = (
    "GENERATE-FROZEN-FUTURE-REVIEW-WORKSPACE-V1"
)

EXPECTED_TRIAGE_ROWS = 12162
EXPECTED_REVIEW_ROWS = 12156
EXPECTED_CARRY_ROWS = 6

EXPECTED_LANE_ROWS = {
    "priority": 5477,
    "residual": 6422,
    "manual": 257,
}

EXPECTED_SOURCE_LANE_ROWS = {
    "priority": 5483,
    "residual": 6422,
    "manual": 257,
}

EXPECTED_PACKET_COUNTS = {
    "priority": 11,
    "residual": 13,
    "manual": 1,
}

EXPECTED_PACKET_FINAL_ROWS = {
    "priority": 477,
    "residual": 422,
    "manual": 257,
}

MAX_PACKET_SIZE = 500

LANE_ORDER = (
    "priority",
    "residual",
    "manual",
)

PRIORITY_REL = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_queue_v1/"
    "priority_scored_queue.tsv"
)

RESIDUAL_REL = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_queue_v1/"
    "residual_scored_queue.tsv"
)

MANUAL_REL = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_queue_v1/"
    "unscored_manual_review_queue.tsv"
)

INPUT_REL = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_text_retrieval_v1/"
    "input_manifest.tsv"
)

RESOLUTION_REL = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_text_retrieval_v1/"
    "reconciled_resolution.tsv"
)

TEXT_REL = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_text_retrieval_v1/"
    "reconciled_normalized_text.tsv"
)

BASELINE_REL = Path(
    "results/07_comparative_landscape/"
    "scientific_screening/"
    "baseline_screening_queue.tsv"
)

MEMBERSHIP_REL = Path(
    "results/07_comparative_landscape/"
    "baseline_scientific_screening_execution/"
    "batch_membership.tsv"
)

CARRY_REL = Path(
    "results/07_comparative_landscape/"
    "baseline_scientific_screening_execution/"
    "prior_anchor_carry_forwards.tsv"
)

LEDGER_REL = Path(
    "results/07_comparative_landscape/"
    "baseline_scientific_screening_execution/"
    "event_ledger.tsv"
)

WORK_MEMBERSHIP_NAME = (
    "review_work_membership.tsv"
)

CARRY_NAME = (
    "prior_carry_forwards.tsv"
)

PACKET_MANIFEST_NAME = (
    "packet_manifest.tsv"
)

WORKSPACE_MANIFEST_NAME = (
    "workspace_manifest.json"
)

CHECKSUMS_NAME = (
    "checksums.sha256"
)

PACKETS_DIR_NAME = (
    "packets"
)

SCORED_QUEUE_FIELDS = [
    "queue_position",
    "retrieval_record_index",
    "screening_entity_id",
    "selected_candidate_id",
    "continuous_score",
]

MANUAL_QUEUE_FIELDS = [
    "queue_position",
    "retrieval_record_index",
    "screening_entity_id",
    "abstract_status",
    "coverage_status",
]

INPUT_FIELDS = [
    "retrieval_record_index",
    "screening_entity_id",
    "candidate_row_sha256",
    "pmid",
    "openalex_id",
    "doi",
    "omid",
    "pubmed_route",
    "openalex_route",
    "openalex_lookup_value",
    "retrieval_cascade",
]

RESOLUTION_FIELDS = [
    "retrieval_record_index",
    "screening_entity_id",
    "resolution_lane",
    "provider_used",
    "provider_lookup_type",
    "provider_record_id",
    "source_body_sha256",
    "provider_identity_status",
    "parser_status",
    "abstract_status",
    "wave_a_request_sequence",
    "wave_a_request_identity_sha256",
    "wave_b_request_sequence",
    "wave_b_request_identity_sha256",
    "fallback_reason",
    "normalized_text_present",
]

TEXT_FIELDS = [
    "retrieval_record_index",
    "screening_entity_id",
    "provider_used",
    "provider_lookup_type",
    "provider_record_id",
    "source_body_sha256",
    "provider_identity_status",
    "parser_status",
    "abstract_status",
    "title_text",
    "abstract_text",
    "abstract_section_metadata_json",
]

BASELINE_FIELDS = [
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

MEMBERSHIP_FIELDS = [
    "batch_id",
    "batch_index",
    "position_in_batch",
    "global_active_index",
    "screening_entity_id",
    "baseline_row_sha256",
]

CARRY_FIELDS = [
    "anchor_id",
    "tool",
    "canonical_doi",
    "screening_entity_id",
    "baseline_row_sha256",
    "prior_anchor_decision",
    "prior_landscape_decision",
    "prior_confirmed_role",
    "record_decision",
    "candidate_method_flag",
    "mapping_basis",
    "source_resolution_sha256",
    "scientific_reassessment_performed",
]

LEDGER_FIELDS = [
    "event_id",
    "event_type",
    "screening_entity_id",
    "baseline_queue_sha256",
    "baseline_row_sha256",
    "batch_id",
    "record_decision",
    "exclusion_reason_code",
    "candidate_method_flag",
    "evidence_basis",
    "evidence_source_locator",
    "evidence_escalation_status",
    "operator_id",
    "operator_type",
    "decision_timestamp_utc",
    "supersedes_event_id",
    "reviewer_id",
    "review_status",
    "adjudication_status",
    "notes",
]

WORK_MEMBERSHIP_FIELDS = [
    "workspace_lane",
    "source_queue_position",
    "review_work_position",
    "packet_index_within_lane",
    "position_in_packet",
    "screening_entity_id",
    "retrieval_record_index",
    "baseline_batch_id",
    "baseline_batch_index",
    "baseline_position_in_batch",
    "global_active_index",
    "baseline_row_sha256",
    "retrieval_candidate_row_sha256",
    "doi",
    "pmid",
    "openalex_id",
    "omid",
    "provider_used",
    "provider_lookup_type",
    "provider_record_id",
    "source_body_sha256",
    "provider_identity_status",
    "parser_status",
    "abstract_status",
    "normalized_text_present",
    "baseline_title_or_software_name",
    "normalized_title_text",
    "normalized_abstract_text",
]

HUMAN_ENTRY_FIELDS = [
    "proposed_event_type",
    "proposed_record_decision",
    "proposed_exclusion_reason_code",
    "proposed_candidate_method_flag",
    "evidence_basis",
    "evidence_source_locator",
    "evidence_escalation_status",
    "notes",
]

PACKET_FIELDS = (
    WORK_MEMBERSHIP_FIELDS
    + HUMAN_ENTRY_FIELDS
)

PACKET_MANIFEST_FIELDS = [
    "packet_id",
    "workspace_lane",
    "packet_index_within_lane",
    "entity_count",
    "first_review_work_position",
    "last_review_work_position",
    "ordered_screening_entity_ids_sha256",
]

CARRY_OUTPUT_FIELDS = [
    "workspace_lane",
    "source_queue_position",
    "retrieval_record_index",
] + CARRY_FIELDS

FORBIDDEN_OUTPUT_FIELDS = {
    "continuous_score",
    "selected_candidate_id",
}


class WorkspaceError(
    RuntimeError
):
    pass


@dataclass(
    frozen=True
)
class RawInputs:
    design: dict
    lanes: dict[str, list[dict[str, str]]]
    input_by_id: dict[str, dict[str, str]]
    resolution_by_id: dict[str, dict[str, str]]
    text_by_id: dict[str, dict[str, str]]
    baseline_by_id: dict[str, dict[str, str]]
    membership_by_id: dict[str, dict[str, str]]
    carry_by_id: dict[str, dict[str, str]]
    events: list[dict[str, str]]
    ledger_sha256: str


@dataclass(
    frozen=True
)
class WorkspaceBundle:
    membership_rows: list[dict[str, str]]
    carry_rows: list[dict[str, str]]
    packet_manifest_rows: list[dict[str, str]]
    packets: dict[str, list[dict[str, str]]]
    manifest: dict


def repo_root() -> Path:
    return (
        Path(__file__)
        .resolve()
        .parents[2]
    )


OUTPUT_ROOT = (
    repo_root()
    / OUTPUT_REL
)


def sha256(
    path: Path,
) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def ids_sha256(
    ids: list[str],
) -> str:
    payload = (
        "".join(
            value + "\n"
            for value in ids
        )
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


def read_tsv_exact(
    path: Path,
    expected_fields: list[str],
) -> list[dict[str, str]]:

    if not path.is_file():
        raise WorkspaceError(
            "Required TSV missing: "
            + str(path)
        )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        if reader.fieldnames != expected_fields:
            raise WorkspaceError(
                "TSV schema changed: "
                + str(path)
            )

        return list(reader)


def unique_by_id(
    rows: list[dict[str, str]],
    label: str,
) -> dict[str, dict[str, str]]:

    result = {}

    for row in rows:
        sid = row.get(
            "screening_entity_id",
            "",
        )

        if not sid:
            raise WorkspaceError(
                f"{label}: blank screening entity ID"
            )

        if sid in result:
            raise WorkspaceError(
                f"{label}: duplicate screening entity ID"
            )

        result[sid] = row

    return result


def verify_checksum_manifest(
    path: Path,
) -> None:

    root = repo_root()

    if not path.is_file():
        raise WorkspaceError(
            "Checksum manifest missing: "
            + str(path)
        )

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        try:
            expected, rel = (
                line.split(
                    None,
                    1,
                )
            )
        except ValueError as exc:
            raise WorkspaceError(
                "Malformed checksum-manifest line"
            ) from exc

        rel = rel.strip()

        if rel.startswith("*"):
            rel = rel[1:]

        target = (
            root
            / rel
        )

        if not target.is_file():
            raise WorkspaceError(
                "Checksum target missing: "
                + rel
            )

        if sha256(target) != expected:
            raise WorkspaceError(
                "Checksum target changed: "
                + rel
            )


def load_frozen_design() -> dict:

    root = repo_root()

    sums = (
        root
        / DESIGN_SUMS_REL
    )

    if sha256(sums) != EXPECTED_DESIGN_SUMS_SHA:
        raise WorkspaceError(
            "Frozen workspace-design checksum identity changed"
        )

    verify_checksum_manifest(
        sums
    )

    design = json.loads(
        (
            root
            / DESIGN_REL
        ).read_text(
            encoding="utf-8"
        )
    )

    if design.get(
        "design_id"
    ) != DESIGN_ID:
        raise WorkspaceError(
            "Workspace design identity changed"
        )

    if design.get(
        "status"
    ) != "FROZEN_PRE_IMPLEMENTATION":
        raise WorkspaceError(
            "Workspace design status changed"
        )

    source = design[
        "source_contract"
    ]

    if (
        source["triage_universe_rows"]
        != EXPECTED_TRIAGE_ROWS
    ):
        raise WorkspaceError(
            "Frozen triage universe changed"
        )

    if (
        source["review_work_rows"]
        != EXPECTED_REVIEW_ROWS
    ):
        raise WorkspaceError(
            "Frozen review-work universe changed"
        )

    if (
        source["prior_carry_forward_rows"]
        != EXPECTED_CARRY_ROWS
    ):
        raise WorkspaceError(
            "Frozen carry-forward count changed"
        )

    lanes = design[
        "review_lanes"
    ]

    for lane in LANE_ORDER:
        if (
            lanes[lane]["review_rows"]
            != EXPECTED_LANE_ROWS[lane]
        ):
            raise WorkspaceError(
                f"Frozen {lane} review count changed"
            )

        if (
            lanes[lane]["packet_count"]
            != EXPECTED_PACKET_COUNTS[lane]
        ):
            raise WorkspaceError(
                f"Frozen {lane} packet count changed"
            )

    if (
        lanes["global_cross_lane_order_defined"]
        is not False
    ):
        raise WorkspaceError(
            "Cross-lane order unexpectedly defined"
        )

    if (
        lanes["manual_vs_scored_priority_defined"]
        is not False
    ):
        raise WorkspaceError(
            "Manual/scored cross-lane priority unexpectedly defined"
        )

    return design


def verify_source_artifacts(
    design: dict,
) -> None:

    root = repo_root()

    artifacts = (
        design[
            "source_contract"
        ][
            "artifacts"
        ]
    )

    for rel, expected in artifacts.items():

        path = (
            root
            / rel
        )

        if not path.is_file():
            raise WorkspaceError(
                "Frozen source artifact missing: "
                + rel
            )

        if sha256(path) != expected:
            raise WorkspaceError(
                "Frozen source artifact changed: "
                + rel
            )


def validate_lane_rows(
    lane: str,
    rows: list[dict[str, str]],
) -> None:

    expected = (
        EXPECTED_SOURCE_LANE_ROWS[
            lane
        ]
    )

    if len(rows) != expected:
        raise WorkspaceError(
            f"{lane}: source lane count changed"
        )

    ids = []
    indices = []

    for expected_position, row in enumerate(
        rows,
        start=1,
    ):

        try:
            position = int(
                row["queue_position"]
            )
            retrieval = int(
                row["retrieval_record_index"]
            )
        except ValueError as exc:
            raise WorkspaceError(
                f"{lane}: invalid integer field"
            ) from exc

        if position != expected_position:
            raise WorkspaceError(
                f"{lane}: queue position changed"
            )

        sid = row[
            "screening_entity_id"
        ]

        if not sid:
            raise WorkspaceError(
                f"{lane}: blank screening entity ID"
            )

        ids.append(
            sid
        )
        indices.append(
            retrieval
        )

    if len(set(ids)) != len(ids):
        raise WorkspaceError(
            f"{lane}: duplicate screening entity ID"
        )

    if (
        len(set(indices))
        != len(indices)
    ):
        raise WorkspaceError(
            f"{lane}: duplicate retrieval record index"
        )


def load_real_inputs() -> RawInputs:

    root = repo_root()

    design = (
        load_frozen_design()
    )

    verify_source_artifacts(
        design
    )

    priority = read_tsv_exact(
        root / PRIORITY_REL,
        SCORED_QUEUE_FIELDS,
    )

    residual = read_tsv_exact(
        root / RESIDUAL_REL,
        SCORED_QUEUE_FIELDS,
    )

    manual = read_tsv_exact(
        root / MANUAL_REL,
        MANUAL_QUEUE_FIELDS,
    )

    lanes = {
        "priority": priority,
        "residual": residual,
        "manual": manual,
    }

    for lane in LANE_ORDER:
        validate_lane_rows(
            lane,
            lanes[lane],
        )

    input_rows = read_tsv_exact(
        root / INPUT_REL,
        INPUT_FIELDS,
    )

    resolution_rows = read_tsv_exact(
        root / RESOLUTION_REL,
        RESOLUTION_FIELDS,
    )

    text_rows = read_tsv_exact(
        root / TEXT_REL,
        TEXT_FIELDS,
    )

    baseline_rows = read_tsv_exact(
        root / BASELINE_REL,
        BASELINE_FIELDS,
    )

    membership_rows = read_tsv_exact(
        root / MEMBERSHIP_REL,
        MEMBERSHIP_FIELDS,
    )

    carry_rows = read_tsv_exact(
        root / CARRY_REL,
        CARRY_FIELDS,
    )

    events = read_tsv_exact(
        root / LEDGER_REL,
        LEDGER_FIELDS,
    )

    raw = RawInputs(
        design=design,
        lanes=lanes,
        input_by_id=unique_by_id(
            input_rows,
            "input manifest",
        ),
        resolution_by_id=unique_by_id(
            resolution_rows,
            "resolution",
        ),
        text_by_id=unique_by_id(
            text_rows,
            "normalized text",
        ),
        baseline_by_id=unique_by_id(
            baseline_rows,
            "baseline queue",
        ),
        membership_by_id=unique_by_id(
            membership_rows,
            "baseline membership",
        ),
        carry_by_id=unique_by_id(
            carry_rows,
            "prior carry-forwards",
        ),
        events=events,
        ledger_sha256=sha256(
            root
            / LEDGER_REL
        ),
    )

    validate_raw_inputs(
        raw
    )

    return raw


def future_identity_maps(
    raw: RawInputs,
) -> tuple[
    dict[str, dict[str, str]],
    dict[str, str],
]:

    future = {}
    lane_by_id = {}

    for lane in LANE_ORDER:

        for row in raw.lanes[lane]:

            sid = row[
                "screening_entity_id"
            ]

            if sid in future:
                raise WorkspaceError(
                    "Future queue lanes overlap"
                )

            future[sid] = row
            lane_by_id[sid] = lane

    return (
        future,
        lane_by_id,
    )


def validate_raw_inputs(
    raw: RawInputs,
) -> None:

    for lane in LANE_ORDER:
        validate_lane_rows(
            lane,
            raw.lanes[lane],
        )

    future, lane_by_id = (
        future_identity_maps(
            raw
        )
    )

    future_ids = set(
        future
    )

    if (
        len(future_ids)
        != EXPECTED_TRIAGE_ROWS
    ):
        raise WorkspaceError(
            "Future triage universe changed"
        )

    retrieval_indices = []

    for row in future.values():
        try:
            retrieval_indices.append(
                int(
                    row[
                        "retrieval_record_index"
                    ]
                )
            )
        except ValueError as exc:
            raise WorkspaceError(
                "Invalid future retrieval index"
            ) from exc

    if (
        len(set(retrieval_indices))
        != len(retrieval_indices)
    ):
        raise WorkspaceError(
            "Duplicate retrieval index across future lanes"
        )

    if (
        set(raw.input_by_id)
        != future_ids
    ):
        raise WorkspaceError(
            "Input-manifest universe changed"
        )

    if (
        set(raw.resolution_by_id)
        != future_ids
    ):
        raise WorkspaceError(
            "Resolution universe changed"
        )

    scored_ids = {
        sid
        for sid in future_ids
        if lane_by_id[sid]
        in {
            "priority",
            "residual",
        }
    }

    manual_ids = {
        sid
        for sid in future_ids
        if lane_by_id[sid]
        == "manual"
    }

    if (
        set(raw.text_by_id)
        != scored_ids
    ):
        raise WorkspaceError(
            "Normalized-text universe changed"
        )

    if (
        manual_ids
        != (
            future_ids
            - set(raw.text_by_id)
        )
    ):
        raise WorkspaceError(
            "Manual-review universe changed"
        )

    if not future_ids <= set(
        raw.baseline_by_id
    ):
        raise WorkspaceError(
            "Future universe left baseline universe"
        )

    for sid in future_ids:

        row = raw.baseline_by_id[
            sid
        ]

        if (
            row["screening_entity_class"]
            != "publication"
        ):
            raise WorkspaceError(
                "Future entity class changed"
            )

        if (
            row["metadata_screenability"]
            != "screenable"
        ):
            raise WorkspaceError(
                "Future metadata-screenability changed"
            )

        if (
            row["screening_state"]
            != "ready"
        ):
            raise WorkspaceError(
                "Future genesis screening state changed"
            )

    carry_ids = (
        future_ids
        & set(raw.carry_by_id)
    )

    if (
        len(carry_ids)
        != EXPECTED_CARRY_ROWS
    ):
        raise WorkspaceError(
            "Future carry-forward count changed"
        )

    for sid in carry_ids:

        if lane_by_id[sid] != "priority":
            raise WorkspaceError(
                "Carry-forward left priority provenance"
            )

        row = raw.carry_by_id[
            sid
        ]

        if (
            row["record_decision"]
            != "retain_for_method_assessment"
        ):
            raise WorkspaceError(
                "Carry-forward record decision changed"
            )

        if (
            row["candidate_method_flag"]
            != "true"
        ):
            raise WorkspaceError(
                "Carry-forward candidate flag changed"
            )

        if (
            row["scientific_reassessment_performed"]
            != "false"
        ):
            raise WorkspaceError(
                "Carry-forward reassessment state changed"
            )

    review_ids = (
        future_ids
        - carry_ids
    )

    if (
        len(review_ids)
        != EXPECTED_REVIEW_ROWS
    ):
        raise WorkspaceError(
            "Review-work universe changed"
        )

    active_future = (
        future_ids
        & set(raw.membership_by_id)
    )

    if active_future != review_ids:
        raise WorkspaceError(
            "Active baseline membership no longer equals review-work universe"
        )

    if (
        carry_ids
        & set(raw.membership_by_id)
    ):
        raise WorkspaceError(
            "Carry-forward entered active batch membership"
        )

    for row in raw.events:

        sid = row.get(
            "screening_entity_id",
            "",
        )

        if sid in future_ids:
            raise WorkspaceError(
                "Future entity already has accepted scientific event"
            )


def packet_id(
    lane: str,
    packet_index: int,
) -> str:

    return (
        f"{lane}_{packet_index:03d}"
    )


def build_workspace(
    raw: RawInputs,
) -> WorkspaceBundle:

    validate_raw_inputs(
        raw
    )

    future, lane_by_id = (
        future_identity_maps(
            raw
        )
    )

    future_ids = set(
        future
    )

    carry_ids = (
        future_ids
        & set(raw.carry_by_id)
    )

    review_ids = (
        future_ids
        - carry_ids
    )

    membership_rows = []
    packets = {}

    for lane in LANE_ORDER:

        lane_review_ids = [
            row["screening_entity_id"]
            for row in raw.lanes[lane]
            if row["screening_entity_id"]
            in review_ids
        ]

        if (
            len(lane_review_ids)
            != EXPECTED_LANE_ROWS[lane]
        ):
            raise WorkspaceError(
                f"{lane}: derived review count changed"
            )

        for review_position, sid in enumerate(
            lane_review_ids,
            start=1,
        ):

            source = future[
                sid
            ]

            baseline = raw.baseline_by_id[
                sid
            ]

            membership = raw.membership_by_id[
                sid
            ]

            input_row = raw.input_by_id[
                sid
            ]

            resolution = raw.resolution_by_id[
                sid
            ]

            text = raw.text_by_id.get(
                sid,
                {},
            )

            packet_index = (
                (review_position - 1)
                // MAX_PACKET_SIZE
            ) + 1

            position_in_packet = (
                (review_position - 1)
                % MAX_PACKET_SIZE
            ) + 1

            row = {
                "workspace_lane":
                    lane,

                "source_queue_position":
                    source[
                        "queue_position"
                    ],

                "review_work_position":
                    str(
                        review_position
                    ),

                "packet_index_within_lane":
                    str(
                        packet_index
                    ),

                "position_in_packet":
                    str(
                        position_in_packet
                    ),

                "screening_entity_id":
                    sid,

                "retrieval_record_index":
                    source[
                        "retrieval_record_index"
                    ],

                "baseline_batch_id":
                    membership[
                        "batch_id"
                    ],

                "baseline_batch_index":
                    membership[
                        "batch_index"
                    ],

                "baseline_position_in_batch":
                    membership[
                        "position_in_batch"
                    ],

                "global_active_index":
                    membership[
                        "global_active_index"
                    ],

                "baseline_row_sha256":
                    membership[
                        "baseline_row_sha256"
                    ],

                "retrieval_candidate_row_sha256":
                    input_row[
                        "candidate_row_sha256"
                    ],

                "doi":
                    input_row[
                        "doi"
                    ],

                "pmid":
                    input_row[
                        "pmid"
                    ],

                "openalex_id":
                    input_row[
                        "openalex_id"
                    ],

                "omid":
                    input_row[
                        "omid"
                    ],

                "provider_used":
                    resolution[
                        "provider_used"
                    ],

                "provider_lookup_type":
                    resolution[
                        "provider_lookup_type"
                    ],

                "provider_record_id":
                    resolution[
                        "provider_record_id"
                    ],

                "source_body_sha256":
                    resolution[
                        "source_body_sha256"
                    ],

                "provider_identity_status":
                    resolution[
                        "provider_identity_status"
                    ],

                "parser_status":
                    resolution[
                        "parser_status"
                    ],

                "abstract_status":
                    resolution[
                        "abstract_status"
                    ],

                "normalized_text_present":
                    resolution[
                        "normalized_text_present"
                    ],

                "baseline_title_or_software_name":
                    baseline[
                        "title_or_software_name"
                    ],

                "normalized_title_text":
                    text.get(
                        "title_text",
                        "",
                    ),

                "normalized_abstract_text":
                    text.get(
                        "abstract_text",
                        "",
                    ),
            }

            membership_rows.append(
                row
            )

            pid = packet_id(
                lane,
                packet_index,
            )

            packet_row = dict(
                row
            )

            for field in HUMAN_ENTRY_FIELDS:
                packet_row[field] = ""

            packets.setdefault(
                pid,
                [],
            ).append(
                packet_row
            )

    carry_rows = []

    for sid in sorted(
        carry_ids,
        key=lambda value: int(
            future[value][
                "queue_position"
            ]
        ),
    ):

        source = future[
            sid
        ]

        carry = raw.carry_by_id[
            sid
        ]

        row = {
            "workspace_lane":
                lane_by_id[sid],

            "source_queue_position":
                source[
                    "queue_position"
                ],

            "retrieval_record_index":
                source[
                    "retrieval_record_index"
                ],
        }

        for field in CARRY_FIELDS:
            row[field] = carry[
                field
            ]

        carry_rows.append(
            row
        )

    packet_manifest_rows = []

    for lane in LANE_ORDER:

        for index in range(
            1,
            EXPECTED_PACKET_COUNTS[lane]
            + 1,
        ):

            pid = packet_id(
                lane,
                index,
            )

            rows = packets.get(
                pid,
                [],
            )

            if not rows:
                raise WorkspaceError(
                    "Expected packet missing: "
                    + pid
                )

            packet_manifest_rows.append({
                "packet_id":
                    pid,

                "workspace_lane":
                    lane,

                "packet_index_within_lane":
                    str(index),

                "entity_count":
                    str(
                        len(rows)
                    ),

                "first_review_work_position":
                    rows[0][
                        "review_work_position"
                    ],

                "last_review_work_position":
                    rows[-1][
                        "review_work_position"
                    ],

                "ordered_screening_entity_ids_sha256":
                    ids_sha256(
                        [
                            row[
                                "screening_entity_id"
                            ]
                            for row in rows
                        ]
                    ),
            })

    manifest = {
        "schema_version":
            1,

        "status":
            "FUTURE_REVIEW_WORKSPACE_GENERATED_PRE_REVIEW",

        "design_id":
            DESIGN_ID,

        "source_identity": {
            "workspace_design_checksum_manifest_sha256":
                EXPECTED_DESIGN_SUMS_SHA,

            "frozen_artifacts":
                raw.design[
                    "source_contract"
                ][
                    "artifacts"
                ],
        },

        "universe": {
            "frozen_triage_rows":
                EXPECTED_TRIAGE_ROWS,

            "new_review_work_rows":
                EXPECTED_REVIEW_ROWS,

            "prior_carry_forward_rows":
                EXPECTED_CARRY_ROWS,
        },

        "review_lanes": {
            lane: {
                "review_rows":
                    EXPECTED_LANE_ROWS[
                        lane
                    ],

                "packet_count":
                    EXPECTED_PACKET_COUNTS[
                        lane
                    ],
            }
            for lane in LANE_ORDER
        },

        "total_packet_count":
            sum(
                EXPECTED_PACKET_COUNTS.values()
            ),

        "maximum_packet_size":
            MAX_PACKET_SIZE,

        "packet_numbering":
            "lane_local",

        "global_cross_lane_order_defined":
            False,

        "manual_vs_scored_priority_defined":
            False,

        "authoritative_scientific_batch_membership_created":
            False,

        "existing_b000xxx_membership_mutated":
            False,

        "model_information": {
            "raw_continuous_score_exposed":
                False,

            "selected_candidate_id_exposed":
                False,
        },

        "scientific_boundary": {
            "scientific_decisions_present":
                False,

            "carry_forward_reassessment_performed":
                False,

            "live_event_authorization_created":
                False,

            "production_event_created":
                False,

            "production_ledger_mutated":
                False,

            "new_scientific_batch_membership_created":
                False,
        },

        "production_ledger_observation": {
            "event_count":
                len(
                    raw.events
                ),

            "ledger_sha256":
                raw.ledger_sha256,

            "future_entity_event_rows":
                0,
        },
    }

    bundle = WorkspaceBundle(
        membership_rows=membership_rows,
        carry_rows=carry_rows,
        packet_manifest_rows=packet_manifest_rows,
        packets=packets,
        manifest=manifest,
    )

    validate_workspace_bundle(
        bundle
    )

    return bundle


def validate_workspace_bundle(
    bundle: WorkspaceBundle,
) -> None:

    if (
        len(bundle.membership_rows)
        != EXPECTED_REVIEW_ROWS
    ):
        raise WorkspaceError(
            "Review-work row count changed"
        )

    if (
        len(bundle.carry_rows)
        != EXPECTED_CARRY_ROWS
    ):
        raise WorkspaceError(
            "Carry-forward output count changed"
        )

    counts = Counter(
        row[
            "workspace_lane"
        ]
        for row in bundle.membership_rows
    )

    if dict(counts) != EXPECTED_LANE_ROWS:
        raise WorkspaceError(
            "Review-work lane counts changed"
        )

    ids = [
        row[
            "screening_entity_id"
        ]
        for row in bundle.membership_rows
    ]

    if len(set(ids)) != len(ids):
        raise WorkspaceError(
            "Duplicate workspace review identity"
        )

    for row in bundle.membership_rows:

        if list(
            row.keys()
        ) != WORK_MEMBERSHIP_FIELDS:
            raise WorkspaceError(
                "Workspace membership schema changed"
            )

        if (
            FORBIDDEN_OUTPUT_FIELDS
            & set(row)
        ):
            raise WorkspaceError(
                "Forbidden model field entered workspace membership"
            )

    for lane in LANE_ORDER:

        rows = [
            row
            for row in bundle.membership_rows
            if row[
                "workspace_lane"
            ] == lane
        ]

        positions = [
            int(
                row[
                    "review_work_position"
                ]
            )
            for row in rows
        ]

        if positions != list(
            range(
                1,
                len(rows)
                + 1,
            )
        ):
            raise WorkspaceError(
                f"{lane}: review-work positions changed"
            )

    if (
        len(bundle.packets)
        != sum(
            EXPECTED_PACKET_COUNTS.values()
        )
    ):
        raise WorkspaceError(
            "Packet count changed"
        )

    packet_row_total = 0

    for lane in LANE_ORDER:

        for index in range(
            1,
            EXPECTED_PACKET_COUNTS[lane]
            + 1,
        ):

            pid = packet_id(
                lane,
                index,
            )

            if pid not in bundle.packets:
                raise WorkspaceError(
                    "Packet missing: "
                    + pid
                )

            rows = bundle.packets[
                pid
            ]

            packet_row_total += len(
                rows
            )

            if len(rows) > MAX_PACKET_SIZE:
                raise WorkspaceError(
                    "Packet exceeds maximum size"
                )

            if (
                index
                < EXPECTED_PACKET_COUNTS[
                    lane
                ]
                and len(rows)
                != MAX_PACKET_SIZE
            ):
                raise WorkspaceError(
                    "Non-final packet is not full"
                )

            if (
                index
                == EXPECTED_PACKET_COUNTS[
                    lane
                ]
                and len(rows)
                != EXPECTED_PACKET_FINAL_ROWS[
                    lane
                ]
            ):
                raise WorkspaceError(
                    "Final packet size changed"
                )

            for row in rows:

                if list(
                    row.keys()
                ) != PACKET_FIELDS:
                    raise WorkspaceError(
                        "Review packet schema changed"
                    )

                if (
                    FORBIDDEN_OUTPUT_FIELDS
                    & set(row)
                ):
                    raise WorkspaceError(
                        "Forbidden model field entered review packet"
                    )

                for field in HUMAN_ENTRY_FIELDS:

                    if row[field] != "":
                        raise WorkspaceError(
                            "Pre-populated human-entry field"
                        )

    if (
        packet_row_total
        != EXPECTED_REVIEW_ROWS
    ):
        raise WorkspaceError(
            "Packet universe does not close"
        )

    if (
        len(
            bundle.packet_manifest_rows
        )
        != sum(
            EXPECTED_PACKET_COUNTS.values()
        )
    ):
        raise WorkspaceError(
            "Packet-manifest row count changed"
        )

    boundary = bundle.manifest[
        "scientific_boundary"
    ]

    if any(
        boundary.values()
    ):
        raise WorkspaceError(
            "Scientific authority leaked into workspace manifest"
        )

    model = bundle.manifest[
        "model_information"
    ]

    if any(
        model.values()
    ):
        raise WorkspaceError(
            "Model information exposed in workspace manifest"
        )

    if (
        bundle.manifest[
            "global_cross_lane_order_defined"
        ]
        is not False
    ):
        raise WorkspaceError(
            "Cross-lane ordering leaked into manifest"
        )

    if (
        bundle.manifest[
            "manual_vs_scored_priority_defined"
        ]
        is not False
    ):
        raise WorkspaceError(
            "Manual/scored priority leaked into manifest"
        )


def write_tsv(
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
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


def expected_packet_ids() -> list[str]:

    return [
        packet_id(
            lane,
            index,
        )
        for lane in LANE_ORDER
        for index in range(
            1,
            EXPECTED_PACKET_COUNTS[
                lane
            ]
            + 1,
        )
    ]


def write_workspace(
    root: Path,
    bundle: WorkspaceBundle,
) -> None:

    validate_workspace_bundle(
        bundle
    )

    root.mkdir(
        parents=True,
        exist_ok=False,
    )

    packets_dir = (
        root
        / PACKETS_DIR_NAME
    )

    packets_dir.mkdir()

    write_tsv(
        root
        / WORK_MEMBERSHIP_NAME,
        WORK_MEMBERSHIP_FIELDS,
        bundle.membership_rows,
    )

    write_tsv(
        root
        / CARRY_NAME,
        CARRY_OUTPUT_FIELDS,
        bundle.carry_rows,
    )

    write_tsv(
        root
        / PACKET_MANIFEST_NAME,
        PACKET_MANIFEST_FIELDS,
        bundle.packet_manifest_rows,
    )

    for pid in expected_packet_ids():

        write_tsv(
            packets_dir
            / f"{pid}.tsv",
            PACKET_FIELDS,
            bundle.packets[
                pid
            ],
        )

    artifact_hashes = {}

    pre_manifest_paths = [
        root
        / WORK_MEMBERSHIP_NAME,

        root
        / CARRY_NAME,

        root
        / PACKET_MANIFEST_NAME,
    ] + [
        packets_dir
        / f"{pid}.tsv"
        for pid
        in expected_packet_ids()
    ]

    for path in pre_manifest_paths:

        artifact_hashes[
            str(
                path.relative_to(
                    root
                )
            )
        ] = sha256(
            path
        )

    manifest = dict(
        bundle.manifest
    )

    manifest[
        "artifact_sha256"
    ] = artifact_hashes

    (
        root
        / WORKSPACE_MANIFEST_NAME
    ).write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    checksum_paths = (
        pre_manifest_paths
        + [
            root
            / WORKSPACE_MANIFEST_NAME
        ]
    )

    lines = []

    for path in sorted(
        checksum_paths,
        key=lambda value: str(
            value.relative_to(
                root
            )
        ),
    ):

        lines.append(
            sha256(path)
            + "  "
            + str(
                path.relative_to(
                    root
                )
            )
            + "\n"
        )

    (
        root
        / CHECKSUMS_NAME
    ).write_text(
        "".join(
            lines
        ),
        encoding="utf-8",
    )

    validate_materialized_workspace(
        root
    )


def validate_materialized_workspace(
    root: Path,
) -> None:

    if not root.is_dir():
        raise WorkspaceError(
            "Workspace root missing"
        )

    expected_root_files = {
        WORK_MEMBERSHIP_NAME,
        CARRY_NAME,
        PACKET_MANIFEST_NAME,
        WORKSPACE_MANIFEST_NAME,
        CHECKSUMS_NAME,
    }

    actual_root_files = {
        path.name
        for path in root.iterdir()
        if path.is_file()
    }

    if (
        actual_root_files
        != expected_root_files
    ):
        raise WorkspaceError(
            "Materialized root file set changed"
        )

    packets_dir = (
        root
        / PACKETS_DIR_NAME
    )

    if not packets_dir.is_dir():
        raise WorkspaceError(
            "Packet directory missing"
        )

    expected_packet_files = {
        f"{pid}.tsv"
        for pid
        in expected_packet_ids()
    }

    actual_packet_files = {
        path.name
        for path in packets_dir.iterdir()
        if path.is_file()
    }

    if (
        actual_packet_files
        != expected_packet_files
    ):
        raise WorkspaceError(
            "Materialized packet file set changed"
        )

    unexpected_dirs = {
        path.name
        for path in root.iterdir()
        if path.is_dir()
        and path.name
        != PACKETS_DIR_NAME
    }

    if unexpected_dirs:
        raise WorkspaceError(
            "Unexpected workspace subdirectory"
        )

    checksum_path = (
        root
        / CHECKSUMS_NAME
    )

    checksum_entries = {}

    for line in checksum_path.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line:
            continue

        expected, rel = line.split(
            None,
            1,
        )

        rel = rel.strip()

        if rel in checksum_entries:
            raise WorkspaceError(
                "Duplicate workspace checksum entry"
            )

        checksum_entries[
            rel
        ] = expected

    expected_checksum_targets = (
        {
            WORK_MEMBERSHIP_NAME,
            CARRY_NAME,
            PACKET_MANIFEST_NAME,
            WORKSPACE_MANIFEST_NAME,
        }
        | {
            f"{PACKETS_DIR_NAME}/{name}"
            for name in expected_packet_files
        }
    )

    if (
        set(checksum_entries)
        != expected_checksum_targets
    ):
        raise WorkspaceError(
            "Workspace checksum target set changed"
        )

    for rel, expected in checksum_entries.items():

        path = (
            root
            / rel
        )

        if sha256(path) != expected:
            raise WorkspaceError(
                "Workspace artifact checksum mismatch: "
                + rel
            )

    membership_rows = read_tsv_exact(
        root
        / WORK_MEMBERSHIP_NAME,
        WORK_MEMBERSHIP_FIELDS,
    )

    carry_rows = read_tsv_exact(
        root
        / CARRY_NAME,
        CARRY_OUTPUT_FIELDS,
    )

    packet_manifest_rows = read_tsv_exact(
        root
        / PACKET_MANIFEST_NAME,
        PACKET_MANIFEST_FIELDS,
    )

    if (
        len(membership_rows)
        != EXPECTED_REVIEW_ROWS
    ):
        raise WorkspaceError(
            "Materialized review-work count changed"
        )

    if (
        len(carry_rows)
        != EXPECTED_CARRY_ROWS
    ):
        raise WorkspaceError(
            "Materialized carry-forward count changed"
        )

    if (
        len(packet_manifest_rows)
        != sum(
            EXPECTED_PACKET_COUNTS.values()
        )
    ):
        raise WorkspaceError(
            "Materialized packet-manifest count changed"
        )

    for pid in expected_packet_ids():

        rows = read_tsv_exact(
            packets_dir
            / f"{pid}.tsv",
            PACKET_FIELDS,
        )

        for row in rows:

            for field in HUMAN_ENTRY_FIELDS:

                if row[field] != "":
                    raise WorkspaceError(
                        "Materialized review packet contains pre-populated human field"
                    )

    manifest = json.loads(
        (
            root
            / WORKSPACE_MANIFEST_NAME
        ).read_text(
            encoding="utf-8"
        )
    )

    if (
        manifest.get(
            "status"
        )
        != "FUTURE_REVIEW_WORKSPACE_GENERATED_PRE_REVIEW"
    ):
        raise WorkspaceError(
            "Materialized workspace manifest status changed"
        )

    if (
        manifest[
            "universe"
        ][
            "new_review_work_rows"
        ]
        != EXPECTED_REVIEW_ROWS
    ):
        raise WorkspaceError(
            "Materialized manifest review count changed"
        )

    if any(
        manifest[
            "scientific_boundary"
        ].values()
    ):
        raise WorkspaceError(
            "Materialized manifest grants scientific authority"
        )

    if any(
        manifest[
            "model_information"
        ].values()
    ):
        raise WorkspaceError(
            "Materialized manifest exposes model information"
        )

    artifact_hashes = manifest[
        "artifact_sha256"
    ]

    expected_artifact_targets = (
        expected_checksum_targets
        - {
            WORKSPACE_MANIFEST_NAME
        }
    )

    if (
        set(artifact_hashes)
        != expected_artifact_targets
    ):
        raise WorkspaceError(
            "Manifest artifact-hash target set changed"
        )

    for rel, expected in artifact_hashes.items():

        if (
            sha256(
                root
                / rel
            )
            != expected
        ):
            raise WorkspaceError(
                "Manifest artifact hash mismatch: "
                + rel
            )


def expected_authorization_payload() -> dict:

    return {
        "schema_version":
            1,

        "status":
            "AUTHORIZED_ONE_USE",

        "authorization_id":
            AUTHORIZATION_ID,

        "generation_authorized":
            True,

        "one_use":
            True,

        "workspace_design_checksum_manifest_sha256":
            EXPECTED_DESIGN_SUMS_SHA,

        "expected_triage_rows":
            EXPECTED_TRIAGE_ROWS,

        "expected_review_work_rows":
            EXPECTED_REVIEW_ROWS,

        "expected_prior_carry_forward_rows":
            EXPECTED_CARRY_ROWS,

        "expected_packet_count":
            sum(
                EXPECTED_PACKET_COUNTS.values()
            ),

        "output_root":
            str(
                OUTPUT_REL
            ),

        "scientific_decision_authorized":
            False,

        "carry_forward_reassessment_authorized":
            False,

        "new_scientific_batch_membership_authorized":
            False,

        "production_ledger_mutation_authorized":
            False,

        "cross_lane_priority_inference_authorized":
            False,

        "confirmation":
            GENERATION_CONFIRMATION,
    }


def validate_generation_authorization(
    path: Path,
    confirmation: str,
) -> None:

    if (
        confirmation
        != GENERATION_CONFIRMATION
    ):
        raise WorkspaceError(
            "Exact generation confirmation required"
        )

    if not path.is_file():
        raise WorkspaceError(
            "Generation authorization missing"
        )

    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError as exc:
        raise WorkspaceError(
            "Generation authorization is invalid JSON"
        ) from exc

    if (
        value
        != expected_authorization_payload()
    ):
        raise WorkspaceError(
            "Generation authorization payload mismatch"
        )


def execute_authorized(
    authorization_path: Path,
    confirmation: str,
) -> None:

    validate_generation_authorization(
        authorization_path,
        confirmation,
    )

    if OUTPUT_ROOT.exists():
        raise WorkspaceError(
            "Canonical future review workspace already exists"
        )

    raw = load_real_inputs()

    ledger_before = sha256(
        repo_root()
        / LEDGER_REL
    )

    bundle = build_workspace(
        raw
    )

    parent = OUTPUT_ROOT.parent

    parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    staging_parent = Path(
        tempfile.mkdtemp(
            prefix=(
                ".pre_review_triage_"
                "future_review_workspace_v1."
            ),
            dir=parent,
        )
    )

    payload = (
        staging_parent
        / "payload"
    )

    try:
        write_workspace(
            payload,
            bundle,
        )

        ledger_after = sha256(
            repo_root()
            / LEDGER_REL
        )

        if (
            ledger_after
            != ledger_before
        ):
            raise WorkspaceError(
                "Production event ledger changed during workspace generation"
            )

        current_raw = load_real_inputs()

        if (
            current_raw.ledger_sha256
            != ledger_after
        ):
            raise WorkspaceError(
                "Production event ledger observation became inconsistent"
            )

        os.replace(
            payload,
            OUTPUT_ROOT,
        )

    finally:
        if staging_parent.exists():
            shutil.rmtree(
                staging_parent
            )


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--authorization",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--confirm",
        required=True,
    )

    args = parser.parse_args()

    execute_authorized(
        args.authorization,
        args.confirm,
    )

    print(
        (
            OUTPUT_ROOT
            / WORKSPACE_MANIFEST_NAME
        ).read_text(
            encoding="utf-8"
        )
    )


if __name__ == "__main__":
    main()
