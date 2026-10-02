#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import tempfile

from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

RESULTS_ROOT = (
    REPO_ROOT
    / "results"
    / "07_comparative_landscape"
)

WORKSPACE_ROOT = (
    RESULTS_ROOT
    / "pre_review_triage_future_review_workspace_v1"
)

EXECUTION_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_execution"
)

PLANNED_REVIEW_ROOT = (
    RESULTS_ROOT
    / "pre_review_triage_future_human_review_v1"
)

DESIGN_PATH = (
    HERE
    / "pre_review_triage_future_human_review_protocol_v1_design.json"
)

DESIGN_SUMS_PATH = (
    HERE
    / "pre_review_triage_future_human_review_protocol_v1_design.sha256"
)

RESULT_SUMS_PATH = (
    HERE
    / "pre_review_triage_future_review_workspace_v1_results.sha256"
)

RESULT_AMENDMENT_SUMS_PATH = (
    HERE
    / "pre_review_triage_future_review_workspace_v1_results_amendment_001.sha256"
)

SCIENTIFIC_SCREENING_SUMS_PATH = (
    HERE
    / "scientific_screening_design.sha256"
)

TRANCHE_GUARD_PATH = (
    HERE
    / "baseline_scientific_screening_tranche_guard_v3.py"
)

CAMPAIGN_SUMS_PATH = (
    HERE
    / "baseline_scientific_screening_campaign_orchestration_v4_design.sha256"
)

EXECUTION_IMMUTABLE_SUMS_PATH = (
    EXECUTION_ROOT
    / "immutable_checksums.sha256"
)

BASELINE_QUEUE = (
    RESULTS_ROOT
    / "scientific_screening"
    / "baseline_screening_queue.tsv"
)

APPENDER_DESIGN_PATH = (
    HERE
    / "baseline_scientific_screening_event_entry_design.json"
)

APPENDER_PATH = (
    HERE
    / "baseline_scientific_screening_event_appender.py"
)

PACKET_MANIFEST = (
    WORKSPACE_ROOT
    / "packet_manifest.tsv"
)

REVIEW_MEMBERSHIP = (
    WORKSPACE_ROOT
    / "review_work_membership.tsv"
)

CARRY_FORWARDS = (
    WORKSPACE_ROOT
    / "prior_carry_forwards.tsv"
)

BATCH_MEMBERSHIP = (
    EXECUTION_ROOT
    / "batch_membership.tsv"
)

EVENT_LEDGER = (
    EXECUTION_ROOT
    / "event_ledger.tsv"
)

PACKET_FIELDS = [
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
    "proposed_event_type",
    "proposed_record_decision",
    "proposed_exclusion_reason_code",
    "proposed_candidate_method_flag",
    "evidence_basis",
    "evidence_source_locator",
    "evidence_escalation_status",
    "notes",
]

IDENTITY_FIELDS = PACKET_FIELDS[:28]

HUMAN_FIELDS = PACKET_FIELDS[28:]

MODEL_FIELDS = {
    "continuous_score",
    "selected_candidate_id",
}

REVIEW_TO_PROPOSAL = {
    "proposed_event_type":
        "event_type",

    "proposed_record_decision":
        "record_decision",

    "proposed_exclusion_reason_code":
        "exclusion_reason_code",

    "proposed_candidate_method_flag":
        "candidate_method_flag",

    "evidence_basis":
        "evidence_basis",

    "evidence_source_locator":
        "evidence_source_locator",

    "evidence_escalation_status":
        "evidence_escalation_status",

    "notes":
        "notes",
}

PACKET_MANIFEST_FIELDS = [
    "packet_id",
    "workspace_lane",
    "packet_index_within_lane",
    "entity_count",
    "first_review_work_position",
    "last_review_work_position",
    "ordered_screening_entity_ids_sha256",
]

BATCH_MEMBERSHIP_FIELDS = [
    "batch_id",
    "batch_index",
    "position_in_batch",
    "global_active_index",
    "screening_entity_id",
    "baseline_row_sha256",
]


class FutureHumanReviewProtocolError(
    RuntimeError
):
    pass


def sha256_bytes(
    payload: bytes,
) -> str:

    return hashlib.sha256(
        payload
    ).hexdigest()


def sha256_file(
    path: Path,
) -> str:

    return sha256_bytes(
        Path(path).read_bytes()
    )


def read_json(
    path: Path,
) -> dict[str, Any]:

    value = json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        value,
        dict,
    ):
        raise FutureHumanReviewProtocolError(
            f"Expected JSON object: {path}"
        )

    return value


def read_tsv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:

    with Path(path).open(
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


def parse_checksum_manifest(
    path: Path,
) -> dict[str, str]:

    entries: dict[str, str] = {}

    for raw in Path(path).read_text(
        encoding="utf-8"
    ).splitlines():

        if not raw.strip():
            continue

        try:
            digest, rel = raw.split(
                None,
                1,
            )
        except ValueError as exc:
            raise FutureHumanReviewProtocolError(
                "Malformed checksum manifest line"
            ) from exc

        rel = rel.strip()

        if rel.startswith("*"):
            rel = rel[1:]

        if rel in entries:
            raise FutureHumanReviewProtocolError(
                "Duplicate checksum target: "
                + rel
            )

        entries[rel] = digest

    return entries



def validate_repo_checksum_manifest(
    path: Path,
) -> dict[str, str]:

    entries = parse_checksum_manifest(
        path
    )

    if not entries:
        raise FutureHumanReviewProtocolError(
            "Checksum manifest empty: "
            + str(
                path
            )
        )

    for rel, expected in entries.items():

        target = (
            REPO_ROOT
            / rel
        ).resolve()

        try:
            target.relative_to(
                REPO_ROOT.resolve()
            )
        except ValueError as exc:
            raise FutureHumanReviewProtocolError(
                "Checksum target lies outside repository: "
                + rel
            ) from exc

        if target.is_symlink():
            raise FutureHumanReviewProtocolError(
                "Checksum target is symlink: "
                + rel
            )

        if not target.is_file():
            raise FutureHumanReviewProtocolError(
                "Checksum target missing: "
                + rel
            )

        if sha256_file(
            target
        ) != expected:
            raise FutureHumanReviewProtocolError(
                "Checksum target changed: "
                + rel
            )

    return entries


def validate_upstream_contract(
) -> dict[str, Any]:

    design = load_design()

    source = design[
        "source_contract"
    ]

    identity_contract = {
        RESULT_AMENDMENT_SUMS_PATH:
            source[
                "future_review_workspace_results_amendment_001_checksum_manifest_sha256"
            ],

        RESULT_SUMS_PATH:
            source[
                "future_review_workspace_results_checksum_manifest_sha256"
            ],

        SCIENTIFIC_SCREENING_SUMS_PATH:
            source[
                "scientific_screening_design_checksum_manifest_sha256"
            ],

        EXECUTION_IMMUTABLE_SUMS_PATH:
            source[
                "baseline_execution_immutable_checksums_sha256"
            ],

        TRANCHE_GUARD_PATH:
            source[
                "baseline_scientific_screening_tranche_guard_v3_sha256"
            ],

        CAMPAIGN_SUMS_PATH:
            source[
                "campaign_orchestration_v4_design_checksum_manifest_sha256"
            ],
    }

    for dependency, expected in (
        identity_contract.items()
    ):

        if not dependency.is_file():
            raise FutureHumanReviewProtocolError(
                "Frozen source-contract dependency missing: "
                + str(
                    dependency
                )
            )

        if sha256_file(
            dependency
        ) != expected:
            raise FutureHumanReviewProtocolError(
                "Frozen source-contract dependency changed: "
                + str(
                    dependency
                )
            )

    # Validate the human-review design closure itself.
    validate_repo_checksum_manifest(
        DESIGN_SUMS_PATH
    )

    # These two closures are archival and deliberately exclude
    # permanent pinning of the mutable production event ledger.
    validate_repo_checksum_manifest(
        RESULT_AMENDMENT_SUMS_PATH
    )

    validate_repo_checksum_manifest(
        RESULT_SUMS_PATH
    )

    appender = load_appender()

    # This validates all immutable, untracked execution-package
    # artifacts from immutable_checksums.sha256.
    appender.validate_immutable_package(
        EXECUTION_ROOT
    )

    # Reconstruct the full authoritative execution context:
    # frozen baseline queue + immutable membership + row hashes.
    context = appender.load_context(
        queue_path=
            BASELINE_QUEUE,

        execution_root=
            EXECUTION_ROOT,

        design_path=
            APPENDER_DESIGN_PATH,
    )

    # Validate the CURRENT append-only ledger semantically.
    # Its SHA is observed, not frozen as a permanent protocol identity.
    ledger_state = (
        appender.validate_current_ledger(
            ledger_path=
                EVENT_LEDGER,

            context=
                context,
        )
    )

    if (
        ledger_state[
            "status"
        ]
        != "EVENT_LEDGER_VALID"
    ):
        raise FutureHumanReviewProtocolError(
            "Current production ledger did not validate"
        )

    if (
        ledger_state[
            "mutation_performed"
        ]
        is not False
    ):
        raise FutureHumanReviewProtocolError(
            "Read-only ledger validation reported mutation"
        )

    return {
        "design":
            design,

        "appender":
            appender,

        "appender_context":
            context,

        "current_ledger":
            ledger_state,

        "mutable_ledger_sha_pinned":
            False,
    }


def repo_relative(
    path: Path,
) -> str:

    try:
        return (
            Path(path)
            .resolve()
            .relative_to(
                REPO_ROOT.resolve()
            )
            .as_posix()
        )
    except ValueError as exc:
        raise FutureHumanReviewProtocolError(
            "Path lies outside repository"
        ) from exc


def load_appender():

    spec = importlib.util.spec_from_file_location(
        "future_human_review_appender",
        APPENDER_PATH,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise FutureHumanReviewProtocolError(
            "Unable to load event appender"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


def load_design() -> dict[str, Any]:

    value = read_json(
        DESIGN_PATH
    )

    if (
        value.get("design_id")
        !=
        "PRE_REVIEW_TRIAGE_FUTURE_HUMAN_REVIEW_PROTOCOL_V1"
    ):
        raise FutureHumanReviewProtocolError(
            "Human-review design identity changed"
        )

    if (
        value.get("status")
        != "FROZEN_PRE_IMPLEMENTATION"
    ):
        raise FutureHumanReviewProtocolError(
            "Human-review design is not frozen pre-implementation"
        )

    boundary = value.get(
        "scientific_boundary"
    )

    if (
        not isinstance(
            boundary,
            dict,
        )
        or any(
            boundary.values()
        )
    ):
        raise FutureHumanReviewProtocolError(
            "Frozen design grants scientific or production authority"
        )

    return value


def load_packet_manifest(
) -> dict[str, dict[str, str]]:

    fields, rows = read_tsv(
        PACKET_MANIFEST
    )

    if fields != PACKET_MANIFEST_FIELDS:
        raise FutureHumanReviewProtocolError(
            "Packet-manifest schema changed"
        )

    if len(rows) != 25:
        raise FutureHumanReviewProtocolError(
            "Packet-manifest count changed"
        )

    result = {}

    for row in rows:

        packet_id = row[
            "packet_id"
        ]

        if not packet_id:
            raise FutureHumanReviewProtocolError(
                "Blank packet ID"
            )

        if (
            "/"
            in packet_id
            or "\\"
            in packet_id
            or packet_id in result
        ):
            raise FutureHumanReviewProtocolError(
                "Unsafe or duplicate packet ID"
            )

        result[
            packet_id
        ] = row

    if (
        sum(
            int(
                row[
                    "entity_count"
                ]
            )
            for row in rows
        )
        != 12156
    ):
        raise FutureHumanReviewProtocolError(
            "Packet-manifest review count changed"
        )

    return result


def packet_path(
    packet_id: str,
) -> Path:

    manifest = load_packet_manifest()

    if packet_id not in manifest:
        raise FutureHumanReviewProtocolError(
            "Unknown packet ID: "
            + packet_id
        )

    path = (
        WORKSPACE_ROOT
        / "packets"
        / f"{packet_id}.tsv"
    )

    if not path.is_file():
        raise FutureHumanReviewProtocolError(
            "Frozen packet missing: "
            + packet_id
        )

    return path


def result_freeze_expected_sha(
    path: Path,
) -> str:

    entries = parse_checksum_manifest(
        RESULT_SUMS_PATH
    )

    rel = repo_relative(
        path
    )

    if rel not in entries:
        raise FutureHumanReviewProtocolError(
            "Path absent from frozen result checksum closure: "
            + rel
        )

    return entries[
        rel
    ]


def validate_canonical_packet(
    packet_id: str,
) -> tuple[
    Path,
    list[dict[str, str]],
]:

    design = load_design()

    manifest = load_packet_manifest()

    row_contract = manifest[
        packet_id
    ]

    path = packet_path(
        packet_id
    )

    expected_sha = (
        result_freeze_expected_sha(
            path
        )
    )

    if sha256_file(
        path
    ) != expected_sha:
        raise FutureHumanReviewProtocolError(
            "Frozen packet bytes changed: "
            + packet_id
        )

    fields, rows = read_tsv(
        path
    )

    if fields != PACKET_FIELDS:
        raise FutureHumanReviewProtocolError(
            "Frozen packet schema changed: "
            + packet_id
        )

    if MODEL_FIELDS & set(
        fields
    ):
        raise FutureHumanReviewProtocolError(
            "Model-only fields leaked into review packet"
        )

    expected_count = int(
        row_contract[
            "entity_count"
        ]
    )

    if len(rows) != expected_count:
        raise FutureHumanReviewProtocolError(
            "Frozen packet row count changed: "
            + packet_id
        )

    if not rows:
        raise FutureHumanReviewProtocolError(
            "Frozen review packet unexpectedly empty"
        )

    lane = row_contract[
        "workspace_lane"
    ]

    packet_index = row_contract[
        "packet_index_within_lane"
    ]

    for position, row in enumerate(
        rows,
        start=1,
    ):

        if (
            row[
                "workspace_lane"
            ]
            != lane
        ):
            raise FutureHumanReviewProtocolError(
                "Packet lane changed"
            )

        if (
            row[
                "packet_index_within_lane"
            ]
            != packet_index
        ):
            raise FutureHumanReviewProtocolError(
                "Packet index changed"
            )

        if (
            int(
                row[
                    "position_in_packet"
                ]
            )
            != position
        ):
            raise FutureHumanReviewProtocolError(
                "Packet row order changed"
            )

        for field in HUMAN_FIELDS:
            if row[field]:
                raise FutureHumanReviewProtocolError(
                    "Canonical pre-review packet contains "
                    "scientific human-entry data"
                )

    if (
        int(
            rows[0][
                "review_work_position"
            ]
        )
        != int(
            row_contract[
                "first_review_work_position"
            ]
        )
    ):
        raise FutureHumanReviewProtocolError(
            "First review-work position changed"
        )

    if (
        int(
            rows[-1][
                "review_work_position"
            ]
        )
        != int(
            row_contract[
                "last_review_work_position"
            ]
        )
    ):
        raise FutureHumanReviewProtocolError(
            "Last review-work position changed"
        )

    if (
        design[
            "canonical_workspace_contract"
        ][
            "canonical_pre_review_packets_are_immutable"
        ]
        is not True
    ):
        raise FutureHumanReviewProtocolError(
            "Design no longer freezes canonical review packets"
        )

    return path, rows


def load_authoritative_membership(
) -> dict[str, dict[str, str]]:

    fields, rows = read_tsv(
        BATCH_MEMBERSHIP
    )

    if fields != BATCH_MEMBERSHIP_FIELDS:
        raise FutureHumanReviewProtocolError(
            "Authoritative batch-membership schema changed"
        )

    result: dict[
        str,
        dict[str, str],
    ] = {}

    for row in rows:

        entity_id = row[
            "screening_entity_id"
        ]

        if entity_id in result:
            raise FutureHumanReviewProtocolError(
                "Duplicate entity in authoritative batch membership"
            )

        result[
            entity_id
        ] = row

    return result


def load_current_events(
) -> dict[str, dict[str, str]]:

    runtime = (
        validate_upstream_contract()
    )

    appender = runtime[
        "appender"
    ]

    context = runtime[
        "appender_context"
    ]

    validated_state = runtime[
        "current_ledger"
    ]

    payload = (
        EVENT_LEDGER.read_bytes()
    )

    # Fail closed if ledger bytes changed after the validated
    # snapshot but before deriving current events.
    if (
        sha256_bytes(
            payload
        )
        != validated_state[
            "ledger_sha256"
        ]
    ):
        raise FutureHumanReviewProtocolError(
            "Production ledger changed during review validation"
        )

    fields, rows = (
        appender.parse_tsv_bytes(
            payload
        )
    )

    validation = (
        appender.validate_existing_ledger_contract(
            fields=
                fields,

            rows=
                rows,

            context=
                context,
        )
    )

    return validation[
        "current_by_entity"
    ]


def canonical_packet_bytes(
    packet_id: str,
) -> bytes:

    path, _ = validate_canonical_packet(
        packet_id
    )

    return path.read_bytes()



def review_working_packet_path(
    packet_id: str,
) -> Path:

    manifest = load_packet_manifest()

    if packet_id not in manifest:
        raise FutureHumanReviewProtocolError(
            "Unknown packet ID: "
            + packet_id
        )

    return (
        PLANNED_REVIEW_ROOT
        / "packets"
        / f"{packet_id}.tsv"
    )


def _fsync_directory(
    path: Path,
) -> None:

    fd = os.open(
        path,
        os.O_RDONLY,
    )

    try:
        os.fsync(
            fd
        )
    finally:
        os.close(
            fd
        )


def materialize_blank_review_packet(
    packet_id: str,
) -> dict[str, Any]:

    validate_upstream_contract()

    source_path, source_rows = (
        validate_canonical_packet(
            packet_id
        )
    )

    target = (
        review_working_packet_path(
            packet_id
        )
    )

    if _path_is_within(
        target,
        WORKSPACE_ROOT,
    ):
        raise FutureHumanReviewProtocolError(
            "Reviewed working packet cannot be "
            "materialized inside canonical workspace"
        )

    if (
        target.exists()
        or target.is_symlink()
    ):
        raise FutureHumanReviewProtocolError(
            "Reviewed working packet already exists"
        )

    payload = (
        source_path.read_bytes()
    )

    parent = target.parent

    parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if _path_is_within(
        parent,
        WORKSPACE_ROOT,
    ):
        raise FutureHumanReviewProtocolError(
            "Reviewed working-packet directory "
            "resolves inside canonical workspace"
        )

    if (
        target.exists()
        or target.is_symlink()
    ):
        raise FutureHumanReviewProtocolError(
            "Reviewed working packet appeared before publication"
        )

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{packet_id}.",
        suffix=".tmp",
        dir=parent,
    )

    temporary = Path(
        temporary_name
    )

    linked = False

    try:
        with os.fdopen(
            fd,
            "wb",
        ) as handle:

            handle.write(
                payload
            )

            handle.flush()

            os.fsync(
                handle.fileno()
            )

        try:
            os.link(
                temporary,
                target,
            )
        except FileExistsError as exc:
            raise FutureHumanReviewProtocolError(
                "Reviewed working packet publication "
                "lost fail-closed destination race"
            ) from exc

        linked = True

        _fsync_directory(
            parent
        )

    finally:

        if temporary.exists():
            temporary.unlink()

    if not linked:
        raise FutureHumanReviewProtocolError(
            "Reviewed working packet was not published"
        )

    if target.read_bytes() != payload:
        raise FutureHumanReviewProtocolError(
            "Materialized reviewed packet differs "
            "from frozen source bytes"
        )

    summary = validate_reviewed_packet(
        packet_id=packet_id,
        reviewed_path=target,
        require_complete=False,
    )

    if (
        summary[
            "completed_review_rows"
        ]
        != 0
        or summary[
            "blank_review_rows"
        ]
        != len(
            source_rows
        )
    ):
        raise FutureHumanReviewProtocolError(
            "Fresh reviewed working packet is not proposal-blank"
        )

    return {
        "packet_id":
            packet_id,

        "source_packet_path":
            repo_relative(
                source_path
            ),

        "source_packet_sha256":
            sha256_file(
                source_path
            ),

        "working_packet_sha256":
            sha256_file(
                target
            ),

        "row_count":
            len(
                source_rows
            ),

        "all_human_fields_blank":
            True,

        "production_proposal_created":
            False,

        "production_authorization_created":
            False,

        "event_ledger_mutated":
            False,
    }


def _path_is_within(
    child: Path,
    parent: Path,
) -> bool:

    try:
        child.resolve().relative_to(
            parent.resolve()
        )
    except ValueError:
        return False

    return True


def _validate_authoritative_identity(
    *,
    row: dict[str, str],
    membership_by_entity: dict[
        str,
        dict[str, str],
    ],
) -> None:

    entity_id = row[
        "screening_entity_id"
    ]

    membership = membership_by_entity.get(
        entity_id
    )

    if membership is None:
        raise FutureHumanReviewProtocolError(
            "Review row lies outside authoritative B membership"
        )

    comparisons = {
        "baseline_batch_id":
            "batch_id",

        "baseline_batch_index":
            "batch_index",

        "baseline_position_in_batch":
            "position_in_batch",

        "global_active_index":
            "global_active_index",

        "baseline_row_sha256":
            "baseline_row_sha256",
    }

    for review_field, member_field in comparisons.items():

        if (
            row[
                review_field
            ]
            != membership[
                member_field
            ]
        ):
            raise FutureHumanReviewProtocolError(
                "Review row differs from authoritative "
                f"B membership: {review_field}"
            )


def review_row_to_validation_proposal(
    *,
    row: dict[str, str],
    operator_id: str,
    operator_type: str,
) -> dict[str, str]:

    event_type = row[
        "proposed_event_type"
    ]

    if not event_type:
        raise FutureHumanReviewProtocolError(
            "Cannot project a proposal-blank review row"
        )

    proposal = {
        "screening_entity_id":
            row[
                "screening_entity_id"
            ],

        "batch_id":
            row[
                "baseline_batch_id"
            ],

        "event_type":
            "",

        "record_decision":
            "",

        "exclusion_reason_code":
            "",

        "candidate_method_flag":
            "",

        "evidence_basis":
            "",

        "evidence_source_locator":
            "",

        "evidence_escalation_status":
            "",

        "supersedes_event_id":
            "",

        "operator_id":
            operator_id,

        "operator_type":
            operator_type,

        "notes":
            "",
    }

    for review_field, proposal_field in (
        REVIEW_TO_PROPOSAL.items()
    ):
        proposal[
            proposal_field
        ] = row[
            review_field
        ]

    return proposal


def validate_reviewed_packet(
    *,
    packet_id: str,
    reviewed_path: Path,
    operator_id: str = "",
    operator_type: str = "",
    require_complete: bool = False,
) -> dict[str, Any]:

    validate_upstream_contract()

    design = load_design()

    source_path, source_rows = (
        validate_canonical_packet(
            packet_id
        )
    )

    reviewed_path = Path(
        reviewed_path
    )

    if not reviewed_path.is_file():
        raise FutureHumanReviewProtocolError(
            "Reviewed packet does not exist"
        )

    if _path_is_within(
        reviewed_path,
        WORKSPACE_ROOT,
    ):
        raise FutureHumanReviewProtocolError(
            "Reviewed packet must not be stored inside "
            "the immutable canonical workspace"
        )

    if (
        reviewed_path.resolve()
        == source_path.resolve()
    ):
        raise FutureHumanReviewProtocolError(
            "Canonical packet cannot be used as mutable review file"
        )

    fields, reviewed_rows = read_tsv(
        reviewed_path
    )

    if fields != PACKET_FIELDS:
        raise FutureHumanReviewProtocolError(
            "Reviewed packet schema differs from frozen schema"
        )

    if len(
        reviewed_rows
    ) != len(
        source_rows
    ):
        raise FutureHumanReviewProtocolError(
            "Reviewed packet row count changed"
        )

    membership_by_entity = (
        load_authoritative_membership()
    )

    current_by_entity = (
        load_current_events()
    )

    appender = load_appender()

    base = appender.load_base_engine()

    context = {
        "membership_by_entity":
            membership_by_entity,

        "base":
            base,
    }

    event_counts = Counter()
    decision_counts = Counter()
    exclusion_counts = Counter()

    completed_rows = 0
    blank_rows = 0

    validated_proposals = []

    allowed_initial = set(
        design[
            "scientific_review_contract"
        ][
            "allowed_initial_event_types"
        ]
    )

    for position, (
        source_row,
        reviewed_row,
    ) in enumerate(
        zip(
            source_rows,
            reviewed_rows,
            strict=True,
        ),
        start=1,
    ):

        for field in IDENTITY_FIELDS:

            if (
                reviewed_row[
                    field
                ]
                != source_row[
                    field
                ]
            ):
                raise FutureHumanReviewProtocolError(
                    "Immutable review field changed "
                    f"at packet position {position}: {field}"
                )

        _validate_authoritative_identity(
            row=reviewed_row,
            membership_by_entity=
                membership_by_entity,
        )

        event_type = reviewed_row[
            "proposed_event_type"
        ]

        if not event_type:

            if any(
                reviewed_row[
                    field
                ]
                for field in HUMAN_FIELDS
            ):
                raise FutureHumanReviewProtocolError(
                    "Proposal-blank row contains partial "
                    f"human-entry data at packet position {position}"
                )

            if require_complete:
                raise FutureHumanReviewProtocolError(
                    "Reviewed packet is incomplete at "
                    f"packet position {position}"
                )

            blank_rows += 1
            continue

        if event_type not in allowed_initial:
            raise FutureHumanReviewProtocolError(
                "Review row contains event type outside "
                "the frozen initial-review contract"
            )

        entity_id = reviewed_row[
            "screening_entity_id"
        ]

        if entity_id in current_by_entity:
            raise FutureHumanReviewProtocolError(
                "Review target already has a current "
                "accepted production event"
            )

        proposal = (
            review_row_to_validation_proposal(
                row=reviewed_row,
                operator_id=operator_id,
                operator_type=operator_type,
            )
        )

        appender.validate_all_field_hygiene(
            proposal
        )

        # validate_proposal_rows() requires one B batch per invocation.
        # Future triage packets span many existing B batches, so each
        # completed review row is projected and validated independently.
        validated = (
            appender.validate_proposal_rows(
                proposal_rows=[
                    proposal
                ],
                context=context,
                current_by_entity=
                    current_by_entity,
            )
        )

        if (
            len(validated) != 1
            or validated[0] != proposal
        ):
            raise FutureHumanReviewProtocolError(
                "Scientific-event semantic validator "
                "did not reproduce the validation projection"
            )

        validated_proposals.append(
            proposal
        )

        completed_rows += 1

        event_counts[
            proposal[
                "event_type"
            ]
        ] += 1

        if proposal[
            "record_decision"
        ]:
            decision_counts[
                proposal[
                    "record_decision"
                ]
            ] += 1

        if proposal[
            "exclusion_reason_code"
        ]:
            exclusion_counts[
                proposal[
                    "exclusion_reason_code"
                ]
            ] += 1

    if (
        completed_rows
        + blank_rows
        != len(
            reviewed_rows
        )
    ):
        raise FutureHumanReviewProtocolError(
            "Reviewed packet accounting mismatch"
        )

    return {
        "packet_id":
            packet_id,

        "source_packet_path":
            repo_relative(
                source_path
            ),

        "source_packet_sha256":
            sha256_file(
                source_path
            ),

        "reviewed_packet_sha256":
            sha256_file(
                reviewed_path
            ),

        "row_count":
            len(
                reviewed_rows
            ),

        "completed_review_rows":
            completed_rows,

        "blank_review_rows":
            blank_rows,

        "review_complete":
            (
                blank_rows
                == 0
            ),

        "event_type_counts":
            dict(
                sorted(
                    event_counts.items()
                )
            ),

        "record_decision_counts":
            dict(
                sorted(
                    decision_counts.items()
                )
            ),

        "exclusion_reason_counts":
            dict(
                sorted(
                    exclusion_counts.items()
                )
            ),

        "validated_in_memory_projection_count":
            len(
                validated_proposals
            ),

        "production_proposal_persisted":
            False,

        "production_authorization_created":
            False,

        "event_ledger_mutated":
            False,
    }



def build_packet_approval_payload(
    *,
    packet_id: str,
    reviewed_path: Path,
    operator_id: str,
    operator_type: str,
    human_approval_text: str,
) -> dict[str, Any]:

    validate_upstream_contract()

    expected_path = (
        review_working_packet_path(
            packet_id
        )
    ).resolve()

    reviewed_path = Path(
        reviewed_path
    )

    if (
        reviewed_path.resolve()
        != expected_path
    ):
        raise FutureHumanReviewProtocolError(
            "Packet approval must bind the deterministic "
            "reviewed working-packet path"
        )

    appender = load_appender()

    if not operator_id.strip():
        raise FutureHumanReviewProtocolError(
            "Approval operator_id empty"
        )

    appender.validate_field_hygiene(
        operator_id,
        field_name="operator_id",
    )

    base = appender.load_base_engine()

    if (
        operator_type
        not in set(
            base.OPERATOR_TYPES
        )
    ):
        raise FutureHumanReviewProtocolError(
            "Approval operator_type invalid"
        )

    if not human_approval_text.strip():
        raise FutureHumanReviewProtocolError(
            "Human approval text empty"
        )

    appender.validate_field_hygiene(
        human_approval_text,
        field_name="human_approval_text",
    )

    summary = validate_reviewed_packet(
        packet_id=packet_id,
        reviewed_path=reviewed_path,
        operator_id=operator_id,
        operator_type=operator_type,
        require_complete=True,
    )

    if not summary[
        "review_complete"
    ]:
        raise FutureHumanReviewProtocolError(
            "Packet approval requires complete review"
        )

    manifest_row = (
        load_packet_manifest()[
            packet_id
        ]
    )

    return {
        "schema_version":
            1,

        "approval_type":
            "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_PACKET_APPROVAL_V1",

        "status":
            "SCIENTIFIC_REVIEW_PACKET_APPROVED_PRE_PRODUCTION",

        "packet_id":
            packet_id,

        "workspace_lane":
            manifest_row[
                "workspace_lane"
            ],

        "packet_index_within_lane":
            int(
                manifest_row[
                    "packet_index_within_lane"
                ]
            ),

        "row_count":
            summary[
                "row_count"
            ],

        "source_packet_path":
            summary[
                "source_packet_path"
            ],

        "source_packet_sha256":
            summary[
                "source_packet_sha256"
            ],

        "reviewed_packet_sha256":
            summary[
                "reviewed_packet_sha256"
            ],

        "ordered_screening_entity_ids_sha256":
            manifest_row[
                "ordered_screening_entity_ids_sha256"
            ],

        "operator_id":
            operator_id,

        "operator_type":
            operator_type,

        "human_approval_text":
            human_approval_text,

        "review_summary": {
            "event_type_counts":
                summary[
                    "event_type_counts"
                ],

            "record_decision_counts":
                summary[
                    "record_decision_counts"
                ],

            "exclusion_reason_counts":
                summary[
                    "exclusion_reason_counts"
                ],
        },

        "approval_contract": {
            "source_packet_identity_bound":
                True,

            "reviewed_packet_identity_bound":
                True,

            "exact_target_identity_revalidated":
                True,

            "current_event_conflicts_revalidated":
                True,

            "approval_is_packet_local":
                True,

            "other_packets_authorized":
                False,
        },

        "production_authority": {
            "proposal_tsv_created":
                False,

            "batch_membership_changed":
                False,

            "live_event_authorization_created":
                False,

            "production_event_authorized":
                False,

            "event_ledger_mutation_authorized":
                False,
        },
    }


def validate_packet_approval_payload(
    *,
    payload: dict[str, Any],
    reviewed_path: Path,
) -> dict[str, Any]:

    expected_fields = {
        "schema_version",
        "approval_type",
        "status",
        "packet_id",
        "workspace_lane",
        "packet_index_within_lane",
        "row_count",
        "source_packet_path",
        "source_packet_sha256",
        "reviewed_packet_sha256",
        "ordered_screening_entity_ids_sha256",
        "operator_id",
        "operator_type",
        "human_approval_text",
        "review_summary",
        "approval_contract",
        "production_authority",
    }

    if set(
        payload
    ) != expected_fields:
        raise FutureHumanReviewProtocolError(
            "Packet-approval payload schema differs"
        )

    rebuilt = (
        build_packet_approval_payload(
            packet_id=
                payload[
                    "packet_id"
                ],

            reviewed_path=
                reviewed_path,

            operator_id=
                payload[
                    "operator_id"
                ],

            operator_type=
                payload[
                    "operator_type"
                ],

            human_approval_text=
                payload[
                    "human_approval_text"
                ],
        )
    )

    if payload != rebuilt:
        raise FutureHumanReviewProtocolError(
            "Packet-approval payload differs from "
            "current validated reviewed packet"
        )

    if any(
        rebuilt[
            "production_authority"
        ].values()
    ):
        raise FutureHumanReviewProtocolError(
            "Packet approval unexpectedly grants production authority"
        )

    return rebuilt


def validate_frozen_workspace_contract(
) -> dict[str, Any]:

    validate_upstream_contract()

    design = load_design()

    manifest = load_packet_manifest()

    total = 0

    lanes = Counter()

    for packet_id in sorted(
        manifest
    ):

        _, rows = validate_canonical_packet(
            packet_id
        )

        total += len(
            rows
        )

        lanes[
            manifest[
                packet_id
            ][
                "workspace_lane"
            ]
        ] += len(
            rows
        )

    if total != 12156:
        raise FutureHumanReviewProtocolError(
            "Frozen review-work total changed"
        )

    expected_lanes = {
        "priority":
            5477,

        "residual":
            6422,

        "manual":
            257,
    }

    if dict(
        lanes
    ) != expected_lanes:
        raise FutureHumanReviewProtocolError(
            "Frozen lane counts changed: "
            + repr(
                dict(
                    lanes
                )
            )
        )

    membership_fields, membership_rows = (
        read_tsv(
            REVIEW_MEMBERSHIP
        )
    )

    if (
        len(
            membership_rows
        )
        != 12156
    ):
        raise FutureHumanReviewProtocolError(
            "Review-work membership count changed"
        )

    carry_fields, carry_rows = read_tsv(
        CARRY_FORWARDS
    )

    if len(
        carry_rows
    ) != 6:
        raise FutureHumanReviewProtocolError(
            "Prior carry-forward count changed"
        )

    review_ids = {
        row[
            "screening_entity_id"
        ]
        for row in membership_rows
    }

    carry_ids = {
        row[
            "screening_entity_id"
        ]
        for row in carry_rows
    }

    if review_ids & carry_ids:
        raise FutureHumanReviewProtocolError(
            "Prior carry-forwards leaked into new review work"
        )

    if (
        design[
            "review_universe"
        ][
            "carry_forwards_presented_for_review"
        ]
        is not False
    ):
        raise FutureHumanReviewProtocolError(
            "Frozen design now exposes carry-forwards for reassessment"
        )

    return {
        "review_rows":
            total,

        "packet_count":
            len(
                manifest
            ),

        "lane_rows":
            dict(
                lanes
            ),

        "prior_carry_forward_rows":
            len(
                carry_rows
            ),

        "model_fields_exposed":
            False,

        "scientific_decisions_present":
            False,

        "production_proposals_present":
            False,
    }


def current_target_event_overlap(
) -> list[str]:

    validate_upstream_contract()

    _, membership_rows = read_tsv(
        REVIEW_MEMBERSHIP
    )

    targets = {
        row[
            "screening_entity_id"
        ]
        for row in membership_rows
    }

    current = load_current_events()

    return sorted(
        targets
        & set(
            current
        )
    )


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--validate-frozen",
        action="store_true",
    )

    parser.add_argument(
        "--packet",
    )

    args = parser.parse_args()

    if not args.validate_frozen:
        parser.error(
            "This implementation candidate exposes "
            "read-only validation only"
        )

    result = (
        validate_frozen_workspace_contract()
    )

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )

    overlap = (
        current_target_event_overlap()
    )

    print(
        "current_target_event_overlap =",
        len(
            overlap
        ),
    )

    if args.packet:

        path, rows = validate_canonical_packet(
            args.packet
        )

        print(
            "packet =",
            args.packet,
        )
        print(
            "packet_path =",
            repo_relative(
                path
            ),
        )
        print(
            "packet_rows =",
            len(
                rows
            ),
        )

    print(
        "PASS | frozen human-review protocol inputs validate"
    )
    print(
        "PASS | no reviewed artifact written"
    )
    print(
        "PASS | no production proposal written"
    )
    print(
        "PASS | no event-ledger mutation"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
