#!/usr/bin/env python3

"""
Experiment 07 controlled baseline scientific-screening event appender.

Implements the frozen event-entry design.

This module provides:
- exact proposal parsing;
- immutable package validation;
- existing-ledger validation;
- strict single-current-event chain validation;
- deterministic event-ID assignment;
- system-generated UTC transaction timestamps;
- compare-and-swap protection;
- strict byte-prefix append semantics;
- atomic ledger replacement;
- transaction receipts;
- post-publication validation.

The CLI deliberately REFUSES mutation of the real production event ledger.

A later separately frozen live-authorisation layer may import this module and
call append_transaction_atomic(..., allow_production=True) only after checking
that authorisation.

This implementation does NOT:
- decide scientific dispositions automatically;
- infer scientific classifications;
- resolve metadata blockers;
- perform method-level assessment;
- assign analytical roles or directness;
- select canonical publications;
- promote Wave 1 anchors;
- perform network access.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

RESULTS_ROOT = (
    REPO_ROOT
    / "results"
    / "07_comparative_landscape"
)

SCREENING_ROOT = (
    RESULTS_ROOT
    / "scientific_screening"
)

EXECUTION_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_execution"
)

DEFAULT_QUEUE = (
    SCREENING_ROOT
    / "baseline_screening_queue.tsv"
)

DEFAULT_LEDGER = (
    EXECUTION_ROOT
    / "event_ledger.tsv"
)

DEFAULT_DESIGN = (
    HERE
    / "baseline_scientific_screening_event_entry_design.json"
)

BASE_ENGINE_SOURCE = (
    HERE
    / "baseline_scientific_screening_execution.py"
)


EXPECTED_QUEUE_SHA256 = (
    "97575b71c4607c3dcad893d90210f913"
    "2a83d0ae2e299ac2f1aef7e94f527d58"
)

EXPECTED_GENESIS_LEDGER_SHA256 = (
    "d3ff9be1efe2b1237f616f25e702275c"
    "cc608577fa0ff8b301401a72900eb55f"
)

EXPECTED_ACTIVE_COUNT = 94622
EXPECTED_BLOCKED_COUNT = 484
EXPECTED_CARRY_FORWARD_COUNT = 7


PROPOSAL_FIELDS = [
    "screening_entity_id",
    "batch_id",
    "event_type",
    "record_decision",
    "exclusion_reason_code",
    "candidate_method_flag",
    "evidence_basis",
    "evidence_source_locator",
    "evidence_escalation_status",
    "supersedes_event_id",
    "operator_id",
    "operator_type",
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


IMMUTABLE_CHECKSUM_NAMES = [
    "batch_manifest.tsv",
    "batch_membership.tsv",
    "prior_anchor_carry_forwards.tsv",
    "out_of_baseline_prior_anchor.tsv",
    "event_ledger_genesis.json",
    "manifest.json",
]


PACKAGE_NAMES = {
    "batch_manifest.tsv",
    "batch_membership.tsv",
    "prior_anchor_carry_forwards.tsv",
    "out_of_baseline_prior_anchor.tsv",
    "event_ledger.tsv",
    "event_ledger_genesis.json",
    "manifest.json",
    "immutable_checksums.sha256",
}


EVENT_ID_RE = re.compile(
    r"^E[0-9]{9}$"
)

LOWER_SHA256_RE = re.compile(
    r"^[0-9a-f]{64}$"
)

UTC_SECOND_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)

FORBIDDEN_FIELD_CHARACTERS = (
    "\t",
    "\n",
    "\r",
    "\x00",
)


class EventAppenderError(
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


def canonical_json_bytes(
    value: Any,
) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode(
        "utf-8"
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


def parse_tsv_bytes(
    payload: bytes,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    try:
        text = payload.decode(
            "utf-8"
        )

    except UnicodeDecodeError as exc:
        raise EventAppenderError(
            "Ledger is not valid UTF-8"
        ) from exc

    handle = io.StringIO(
        text,
        newline="",
    )

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


def tsv_rows_without_header(
    *,
    fields: list[str],
    rows: list[dict[str, str]],
) -> bytes:
    handle = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        handle,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )

    writer.writerows(
        rows
    )

    return handle.getvalue().encode(
        "utf-8"
    )


def validate_field_hygiene(
    value: str,
    *,
    field_name: str,
) -> None:
    if any(
        character in value
        for character
        in FORBIDDEN_FIELD_CHARACTERS
    ):
        raise EventAppenderError(
            f"Forbidden control character in {field_name}"
        )


def validate_all_field_hygiene(
    row: dict[str, str],
) -> None:
    for field_name, value in row.items():
        validate_field_hygiene(
            value,
            field_name=field_name,
        )


def load_base_engine():
    module_name = (
        "baseline_scientific_screening_execution_"
        "for_event_appender"
    )

    spec = importlib.util.spec_from_file_location(
        module_name,
        BASE_ENGINE_SOURCE,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise EventAppenderError(
            "Unable to load frozen base execution engine"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        module_name
    ] = module

    spec.loader.exec_module(
        module
    )

    return module


def load_design(
    path: Path,
) -> dict:
    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if value[
        "status"
    ] != "FROZEN_PRE_IMPLEMENTATION":
        raise EventAppenderError(
            "Event-entry design is not frozen pre-implementation"
        )

    if value[
        "event_schema"
    ] != [
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
    ]:
        raise EventAppenderError(
            "Frozen event schema changed"
        )

    if value[
        "proposal_schema"
    ] != PROPOSAL_FIELDS:
        raise EventAppenderError(
            "Frozen proposal schema changed"
        )

    if value[
        "current_event_invariant"
    ][
        "max_unsuperseded_events_per_entity"
    ] != 1:
        raise EventAppenderError(
            "Single-current-event invariant changed"
        )

    if value[
        "review_contract_v1"
    ][
        "reviewer_id"
    ] != "must_be_empty":
        raise EventAppenderError(
            "Review contract changed"
        )

    if value[
        "first_live_authorization"
    ][
        "authorized_by_this_design"
    ] is not False:
        raise EventAppenderError(
            "Design unexpectedly authorises live event entry"
        )

    return value


def validate_immutable_package(
    execution_root: Path,
) -> None:
    if not execution_root.is_dir():
        raise EventAppenderError(
            "Execution production root missing"
        )

    children = list(
        execution_root.iterdir()
    )

    if any(
        path.is_symlink()
        for path in children
    ):
        raise EventAppenderError(
            "Execution production contains symlink"
        )

    if any(
        not path.is_file()
        for path in children
    ):
        raise EventAppenderError(
            "Execution production contains non-file artifact"
        )

    names = {
        path.name
        for path in children
    }

    if names != PACKAGE_NAMES:
        raise EventAppenderError(
            "Execution production artifact set changed"
        )

    checksum_path = (
        execution_root
        / "immutable_checksums.sha256"
    )

    lines = checksum_path.read_text(
        encoding="utf-8"
    ).splitlines()

    if len(
        lines
    ) != len(
        IMMUTABLE_CHECKSUM_NAMES
    ):
        raise EventAppenderError(
            "Immutable checksum ledger row count changed"
        )

    observed_names = []

    for line in lines:
        parts = line.split(
            "  ",
            1,
        )

        if len(parts) != 2:
            raise EventAppenderError(
                "Malformed immutable checksum ledger"
            )

        expected_sha, name = parts

        if not LOWER_SHA256_RE.fullmatch(
            expected_sha
        ):
            raise EventAppenderError(
                "Malformed immutable checksum SHA"
            )

        observed_names.append(
            name
        )

        target = (
            execution_root
            / name
        )

        if not target.is_file():
            raise EventAppenderError(
                f"Immutable artifact missing: {name}"
            )

        if sha256_file(
            target
        ) != expected_sha:
            raise EventAppenderError(
                f"Immutable artifact changed: {name}"
            )

    if (
        observed_names
        != IMMUTABLE_CHECKSUM_NAMES
    ):
        raise EventAppenderError(
            "Immutable checksum coverage/order changed"
        )

    genesis = json.loads(
        (
            execution_root
            / "event_ledger_genesis.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    if genesis[
        "genesis_sha256"
    ] != EXPECTED_GENESIS_LEDGER_SHA256:
        raise EventAppenderError(
            "Frozen ledger genesis SHA changed"
        )

    if genesis[
        "genesis_event_row_count"
    ] != 0:
        raise EventAppenderError(
            "Frozen ledger genesis row count changed"
        )

    if genesis[
        "event_entry_authorized"
    ] is not False:
        raise EventAppenderError(
            "Immutable genesis unexpectedly authorises events"
        )

    manifest = json.loads(
        (
            execution_root
            / "manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    if manifest[
        "baseline_queue_sha256"
    ] != EXPECTED_QUEUE_SHA256:
        raise EventAppenderError(
            "Execution manifest baseline SHA changed"
        )

    if manifest[
        "active_screening_entity_count"
    ] != EXPECTED_ACTIVE_COUNT:
        raise EventAppenderError(
            "Execution manifest active count changed"
        )

    if manifest[
        "blocked_metadata_count"
    ] != EXPECTED_BLOCKED_COUNT:
        raise EventAppenderError(
            "Execution manifest blocked count changed"
        )

    if manifest[
        "in_baseline_carry_forward_count"
    ] != EXPECTED_CARRY_FORWARD_COUNT:
        raise EventAppenderError(
            "Execution manifest carry-forward count changed"
        )


def load_batch_membership(
    execution_root: Path,
) -> tuple[
    dict[str, tuple[str, ...]],
    dict[str, dict[str, Any]],
]:
    fields, rows = read_tsv(
        execution_root
        / "batch_membership.tsv"
    )

    if fields != MEMBERSHIP_FIELDS:
        raise EventAppenderError(
            "Batch-membership schema changed"
        )

    if len(
        rows
    ) != EXPECTED_ACTIVE_COUNT:
        raise EventAppenderError(
            "Batch-membership row count changed"
        )

    by_batch_lists: dict[
        str,
        list[
            tuple[
                int,
                str,
            ]
        ],
    ] = {}

    by_entity: dict[
        str,
        dict[str, Any],
    ] = {}

    expected_global = 1

    for row in rows:
        validate_all_field_hygiene(
            row
        )

        entity_id = row[
            "screening_entity_id"
        ]

        batch_id = row[
            "batch_id"
        ]

        try:
            batch_index = int(
                row[
                    "batch_index"
                ]
            )

            position = int(
                row[
                    "position_in_batch"
                ]
            )

            global_index = int(
                row[
                    "global_active_index"
                ]
            )

        except ValueError as exc:
            raise EventAppenderError(
                "Non-integer batch-membership index"
            ) from exc

        if global_index != expected_global:
            raise EventAppenderError(
                "Batch membership global ordering changed"
            )

        expected_global += 1

        if entity_id in by_entity:
            raise EventAppenderError(
                "Duplicate entity in batch membership"
            )

        if not LOWER_SHA256_RE.fullmatch(
            row[
                "baseline_row_sha256"
            ]
        ):
            raise EventAppenderError(
                "Malformed baseline-row SHA in membership"
            )

        by_entity[
            entity_id
        ] = {
            "batch_id":
                batch_id,

            "batch_index":
                batch_index,

            "position_in_batch":
                position,

            "global_active_index":
                global_index,

            "baseline_row_sha256":
                row[
                    "baseline_row_sha256"
                ],
        }

        by_batch_lists.setdefault(
            batch_id,
            [],
        ).append(
            (
                position,
                entity_id,
            )
        )

    by_batch = {}

    for batch_id, values in by_batch_lists.items():
        ordered = sorted(
            values
        )

        positions = [
            position
            for position, _
            in ordered
        ]

        if positions != list(
            range(
                1,
                len(ordered) + 1,
            )
        ):
            raise EventAppenderError(
                "Non-contiguous position_in_batch"
            )

        by_batch[
            batch_id
        ] = tuple(
            entity_id
            for _, entity_id
            in ordered
        )

    if len(
        by_entity
    ) != EXPECTED_ACTIVE_COUNT:
        raise EventAppenderError(
            "Batch membership entity count changed"
        )

    return (
        by_batch,
        by_entity,
    )


def load_context(
    *,
    queue_path: Path,
    execution_root: Path,
    design_path: Path,
) -> dict:
    if sha256_file(
        queue_path
    ) != EXPECTED_QUEUE_SHA256:
        raise EventAppenderError(
            "Baseline queue SHA mismatch"
        )

    validate_immutable_package(
        execution_root
    )

    design = load_design(
        design_path
    )

    base = load_base_engine()

    baseline = base.load_baseline(
        queue_path
    )

    (
        batch_membership,
        membership_by_entity,
    ) = load_batch_membership(
        execution_root
    )

    for entity_id, membership in (
        membership_by_entity.items()
    ):
        if entity_id not in baseline.by_id:
            raise EventAppenderError(
                "Batch member absent from baseline"
            )

        row = baseline.by_id[
            entity_id
        ]

        if row[
            "screening_state"
        ] != "ready":
            raise EventAppenderError(
                "Non-ready entity in active membership"
            )

        if (
            baseline.row_sha256[
                entity_id
            ]
            != membership[
                "baseline_row_sha256"
            ]
        ):
            raise EventAppenderError(
                "Batch membership baseline-row SHA mismatch"
            )

    return {
        "design":
            design,

        "base":
            base,

        "baseline":
            baseline,

        "batch_membership":
            batch_membership,

        "membership_by_entity":
            membership_by_entity,
    }


def validate_transaction_timestamp(
    value: str,
    *,
    base,
) -> None:
    if not UTC_SECOND_RE.fullmatch(
        value
    ):
        raise EventAppenderError(
            "Transaction timestamp must be UTC Z "
            "with whole-second precision"
        )

    try:
        datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M:%SZ",
        )

    except ValueError as exc:
        raise EventAppenderError(
            "Invalid transaction timestamp"
        ) from exc

    base.validate_utc_timestamp(
        value
    )


def generate_transaction_timestamp() -> str:
    now = datetime.now(
        timezone.utc
    ).replace(
        microsecond=0
    )

    return now.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def derive_current_events(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    superseded = {
        row[
            "supersedes_event_id"
        ]
        for row in rows
        if row[
            "supersedes_event_id"
        ]
    }

    current = {}

    for row in rows:
        if row[
            "event_id"
        ] in superseded:
            continue

        entity_id = row[
            "screening_entity_id"
        ]

        if entity_id in current:
            raise EventAppenderError(
                "Entity has more than one current unsuperseded event"
            )

        current[
            entity_id
        ] = row

    return current


def validate_existing_ledger_contract(
    *,
    fields: list[str],
    rows: list[dict[str, str]],
    context: dict,
) -> dict:
    base = context[
        "base"
    ]

    baseline = context[
        "baseline"
    ]

    batch_membership = context[
        "batch_membership"
    ]

    if fields != list(
        base.EVENT_FIELDS
    ):
        raise EventAppenderError(
            "Event-ledger schema changed"
        )

    for index, row in enumerate(
        rows,
        start=1,
    ):
        validate_all_field_hygiene(
            row
        )

        expected_event_id = (
            f"E{index:09d}"
        )

        if row[
            "event_id"
        ] != expected_event_id:
            raise EventAppenderError(
                "Event IDs are not sequential in append order"
            )

        if not EVENT_ID_RE.fullmatch(
            row[
                "event_id"
            ]
        ):
            raise EventAppenderError(
                "Malformed event ID"
            )

        if not row[
            "evidence_basis"
        ].strip():
            raise EventAppenderError(
                "Event evidence_basis empty"
            )

        event_type = row[
            "event_type"
        ]

        if (
            event_type
            != "source_escalation"
            and not row[
                "evidence_source_locator"
            ].strip()
        ):
            raise EventAppenderError(
                "Terminal event evidence_source_locator empty"
            )

        if (
            row[
                "reviewer_id"
            ]
            or row[
                "review_status"
            ]
            or row[
                "adjudication_status"
            ]
        ):
            raise EventAppenderError(
                "Review/adjudication fields must remain blank in v1"
            )

    base_result = (
        base.validate_event_ledger(
            fields=fields,
            rows=rows,
            baseline=baseline,
            batch_membership=
                batch_membership,
        )
    )

    current_by_entity = {}

    for row in rows:
        entity_id = row[
            "screening_entity_id"
        ]

        event_type = row[
            "event_type"
        ]

        current = current_by_entity.get(
            entity_id
        )

        if event_type in {
            "record_decision",
            "source_escalation",
        }:
            if current is not None:
                raise EventAppenderError(
                    "Initial event layered beside existing current event"
                )

            if row[
                "supersedes_event_id"
            ]:
                raise EventAppenderError(
                    "Initial event cannot supersede"
                )

            if (
                event_type
                == "record_decision"
                and row[
                    "evidence_escalation_status"
                ]
            ):
                raise EventAppenderError(
                    "Initial terminal event must have blank "
                    "evidence escalation status"
                )

            current_by_entity[
                entity_id
            ] = row

        elif (
            event_type
            == "superseding_record_decision"
        ):
            if current is None:
                raise EventAppenderError(
                    "Superseding event has no current predecessor"
                )

            if (
                row[
                    "supersedes_event_id"
                ]
                != current[
                    "event_id"
                ]
            ):
                raise EventAppenderError(
                    "Superseding event does not reference "
                    "current predecessor"
                )

            if (
                current[
                    "event_type"
                ]
                == "source_escalation"
            ):
                if (
                    row[
                        "evidence_escalation_status"
                    ]
                    != "resolved"
                ):
                    raise EventAppenderError(
                        "Source-escalation resolution must be resolved"
                    )

            else:
                if (
                    row[
                        "evidence_escalation_status"
                    ]
                    != current[
                        "evidence_escalation_status"
                    ]
                ):
                    raise EventAppenderError(
                        "Terminal correction changed escalation history"
                    )

            current_by_entity[
                entity_id
            ] = row

        else:
            raise EventAppenderError(
                "Unknown event type"
            )

    independently_derived = (
        derive_current_events(
            rows
        )
    )

    if {
        key:
            value[
                "event_id"
            ]
        for key, value
        in current_by_entity.items()
    } != {
        key:
            value[
                "event_id"
            ]
        for key, value
        in independently_derived.items()
    }:
        raise EventAppenderError(
            "Current-event derivations disagree"
        )

    return {
        "base_validation":
            base_result,

        "current_by_entity":
            current_by_entity,
    }


def derive_active_state_counts(
    *,
    current_by_entity: dict[
        str,
        dict[str, str],
    ],
    membership_by_entity: dict[
        str,
        dict[str, Any],
    ],
) -> dict[str, int]:
    counts = Counter()

    for entity_id in membership_by_entity:
        current = current_by_entity.get(
            entity_id
        )

        if current is None:
            counts[
                "ready"
            ] += 1

        elif (
            current[
                "event_type"
            ]
            == "source_escalation"
        ):
            counts[
                "awaiting_source_escalation"
            ] += 1

        else:
            counts[
                "complete"
            ] += 1

    counts[
        "blocked_metadata"
    ] = EXPECTED_BLOCKED_COUNT

    return {
        key:
            counts.get(
                key,
                0,
            )
        for key in (
            "ready",
            "awaiting_source_escalation",
            "complete",
            "blocked_metadata",
        )
    }


def read_proposal(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
    str,
]:
    fields, rows = read_tsv(
        path
    )

    if fields != PROPOSAL_FIELDS:
        raise EventAppenderError(
            "Proposal schema mismatch"
        )

    if not rows:
        raise EventAppenderError(
            "Proposal contains no event rows"
        )

    for row in rows:
        validate_all_field_hygiene(
            row
        )

    return (
        fields,
        rows,
        sha256_file(
            path
        ),
    )


def validate_proposal_rows(
    *,
    proposal_rows: list[dict[str, str]],
    context: dict,
    current_by_entity: dict[
        str,
        dict[str, str],
    ],
) -> list[dict[str, str]]:
    membership_by_entity = context[
        "membership_by_entity"
    ]

    base = context[
        "base"
    ]

    seen_entities = set()
    batch_ids = set()

    for row in proposal_rows:
        entity_id = row[
            "screening_entity_id"
        ].strip()

        if not entity_id:
            raise EventAppenderError(
                "Proposal screening_entity_id empty"
            )

        if entity_id in seen_entities:
            raise EventAppenderError(
                "Proposal contains multiple events for one entity"
            )

        seen_entities.add(
            entity_id
        )

        membership = (
            membership_by_entity.get(
                entity_id
            )
        )

        if membership is None:
            raise EventAppenderError(
                "Proposal entity outside frozen active membership"
            )

        batch_id = row[
            "batch_id"
        ].strip()

        if (
            batch_id
            != membership[
                "batch_id"
            ]
        ):
            raise EventAppenderError(
                "Proposal batch does not match frozen membership"
            )

        batch_ids.add(
            batch_id
        )

        event_type = row[
            "event_type"
        ]

        if event_type not in set(
            base.EVENT_TYPES
        ):
            raise EventAppenderError(
                "Unknown proposal event type"
            )

        if not row[
            "operator_id"
        ].strip():
            raise EventAppenderError(
                "Proposal operator_id empty"
            )

        if (
            row[
                "operator_type"
            ]
            not in set(
                base.OPERATOR_TYPES
            )
        ):
            raise EventAppenderError(
                "Unknown proposal operator_type"
            )

        if not row[
            "evidence_basis"
        ].strip():
            raise EventAppenderError(
                "Proposal evidence_basis empty"
            )

        current = current_by_entity.get(
            entity_id
        )

        if event_type == "source_escalation":
            if current is not None:
                raise EventAppenderError(
                    "Source escalation requires entity with no current event"
                )

            if row[
                "record_decision"
            ]:
                raise EventAppenderError(
                    "Source escalation cannot contain terminal decision"
                )

            if row[
                "candidate_method_flag"
            ]:
                raise EventAppenderError(
                    "Source escalation cannot contain candidate flag"
                )

            if row[
                "exclusion_reason_code"
            ]:
                raise EventAppenderError(
                    "Source escalation cannot contain exclusion reason"
                )

            if (
                row[
                    "evidence_escalation_status"
                ]
                != "awaiting_source_escalation"
            ):
                raise EventAppenderError(
                    "Source escalation must be awaiting_source_escalation"
                )

            if row[
                "supersedes_event_id"
            ]:
                raise EventAppenderError(
                    "Initial source escalation cannot supersede"
                )

        elif event_type == "record_decision":
            if current is not None:
                raise EventAppenderError(
                    "Initial record decision requires entity "
                    "with no current event"
                )

            if row[
                "supersedes_event_id"
            ]:
                raise EventAppenderError(
                    "Initial record decision cannot supersede"
                )

            if row[
                "evidence_escalation_status"
            ]:
                raise EventAppenderError(
                    "Initial record decision escalation status "
                    "must be blank"
                )

            if not row[
                "evidence_source_locator"
            ].strip():
                raise EventAppenderError(
                    "Terminal decision evidence_source_locator empty"
                )

            base.validate_terminal_fields(
                record_decision=
                    row[
                        "record_decision"
                    ],

                exclusion_reason_code=
                    row[
                        "exclusion_reason_code"
                    ],

                candidate_method_flag=
                    row[
                        "candidate_method_flag"
                    ],
            )

        elif (
            event_type
            == "superseding_record_decision"
        ):
            if current is None:
                raise EventAppenderError(
                    "Superseding decision requires current event"
                )

            if (
                row[
                    "supersedes_event_id"
                ]
                != current[
                    "event_id"
                ]
            ):
                raise EventAppenderError(
                    "Superseding proposal must reference current event"
                )

            if not row[
                "evidence_source_locator"
            ].strip():
                raise EventAppenderError(
                    "Superseding terminal decision "
                    "evidence_source_locator empty"
                )

            base.validate_terminal_fields(
                record_decision=
                    row[
                        "record_decision"
                    ],

                exclusion_reason_code=
                    row[
                        "exclusion_reason_code"
                    ],

                candidate_method_flag=
                    row[
                        "candidate_method_flag"
                    ],
            )

            if (
                current[
                    "event_type"
                ]
                == "source_escalation"
            ):
                if (
                    row[
                        "evidence_escalation_status"
                    ]
                    != "resolved"
                ):
                    raise EventAppenderError(
                        "Source escalation resolution must be resolved"
                    )

            else:
                if (
                    row[
                        "evidence_escalation_status"
                    ]
                    != current[
                        "evidence_escalation_status"
                    ]
                ):
                    raise EventAppenderError(
                        "Terminal correction must preserve "
                        "escalation-history status"
                    )

        else:
            raise EventAppenderError(
                "Unhandled proposal event type"
            )

    if len(
        batch_ids
    ) != 1:
        raise EventAppenderError(
            "One append transaction must contain exactly one batch"
        )

    return sorted(
        proposal_rows,
        key=lambda row:
            context[
                "membership_by_entity"
            ][
                row[
                    "screening_entity_id"
                ]
            ][
                "position_in_batch"
            ],
    )


def validate_expected_sha(
    value: str,
) -> None:
    if not LOWER_SHA256_RE.fullmatch(
        value
    ):
        raise EventAppenderError(
            "Expected pre-ledger SHA must be lowercase SHA-256"
        )


def prepare_transaction_core(
    *,
    existing_fields: list[str],
    existing_rows: list[dict[str, str]],
    existing_bytes: bytes,
    expected_pre_ledger_sha256: str,
    proposal_rows: list[dict[str, str]],
    proposal_sha256: str,
    context: dict,
    transaction_timestamp_utc: str,
) -> dict:
    validate_expected_sha(
        expected_pre_ledger_sha256
    )

    if not LOWER_SHA256_RE.fullmatch(
        proposal_sha256
    ):
        raise EventAppenderError(
            "Proposal SHA malformed"
        )

    observed_pre_sha = sha256_bytes(
        existing_bytes
    )

    if (
        observed_pre_sha
        != expected_pre_ledger_sha256
    ):
        raise EventAppenderError(
            "Stale or incorrect expected pre-ledger SHA"
        )

    base = context[
        "base"
    ]

    validate_transaction_timestamp(
        transaction_timestamp_utc,
        base=base,
    )

    existing_validation = (
        validate_existing_ledger_contract(
            fields=existing_fields,
            rows=existing_rows,
            context=context,
        )
    )

    current_by_entity = (
        existing_validation[
            "current_by_entity"
        ]
    )

    ordered_proposals = (
        validate_proposal_rows(
            proposal_rows=
                proposal_rows,

            context=context,

            current_by_entity=
                current_by_entity,
        )
    )

    new_rows = []

    next_number = (
        len(
            existing_rows
        )
        + 1
    )

    baseline = context[
        "baseline"
    ]

    membership_by_entity = context[
        "membership_by_entity"
    ]

    for offset, proposal in enumerate(
        ordered_proposals
    ):
        entity_id = proposal[
            "screening_entity_id"
        ]

        event_id = (
            f"E{next_number + offset:09d}"
        )

        row = {
            "event_id":
                event_id,

            "event_type":
                proposal[
                    "event_type"
                ],

            "screening_entity_id":
                entity_id,

            "baseline_queue_sha256":
                EXPECTED_QUEUE_SHA256,

            "baseline_row_sha256":
                baseline.row_sha256[
                    entity_id
                ],

            "batch_id":
                membership_by_entity[
                    entity_id
                ][
                    "batch_id"
                ],

            "record_decision":
                proposal[
                    "record_decision"
                ],

            "exclusion_reason_code":
                proposal[
                    "exclusion_reason_code"
                ],

            "candidate_method_flag":
                proposal[
                    "candidate_method_flag"
                ],

            "evidence_basis":
                proposal[
                    "evidence_basis"
                ],

            "evidence_source_locator":
                proposal[
                    "evidence_source_locator"
                ],

            "evidence_escalation_status":
                proposal[
                    "evidence_escalation_status"
                ],

            "operator_id":
                proposal[
                    "operator_id"
                ],

            "operator_type":
                proposal[
                    "operator_type"
                ],

            "decision_timestamp_utc":
                transaction_timestamp_utc,

            "supersedes_event_id":
                proposal[
                    "supersedes_event_id"
                ],

            "reviewer_id":
                "",

            "review_status":
                "",

            "adjudication_status":
                "",

            "notes":
                proposal[
                    "notes"
                ],
        }

        validate_all_field_hygiene(
            row
        )

        new_rows.append(
            row
        )

    append_bytes = (
        tsv_rows_without_header(
            fields=
                list(
                    base.EVENT_FIELDS
                ),

            rows=
                new_rows,
        )
    )

    candidate_bytes = (
        existing_bytes
        + append_bytes
    )

    if not candidate_bytes.startswith(
        existing_bytes
    ):
        raise EventAppenderError(
            "Candidate ledger is not strict prefix extension"
        )

    candidate_fields, candidate_rows = (
        parse_tsv_bytes(
            candidate_bytes
        )
    )

    if len(
        candidate_rows
    ) != (
        len(
            existing_rows
        )
        + len(
            new_rows
        )
    ):
        raise EventAppenderError(
            "Candidate ledger event count mismatch"
        )

    candidate_validation = (
        validate_existing_ledger_contract(
            fields=candidate_fields,
            rows=candidate_rows,
            context=context,
        )
    )

    candidate_current = (
        candidate_validation[
            "current_by_entity"
        ]
    )

    state_counts = (
        derive_active_state_counts(
            current_by_entity=
                candidate_current,

            membership_by_entity=
                membership_by_entity,
        )
    )

    event_type_counts = dict(
        sorted(
            Counter(
                row[
                    "event_type"
                ]
                for row in new_rows
            ).items()
        )
    )

    terminal_decision_counts = dict(
        sorted(
            Counter(
                row[
                    "record_decision"
                ]
                for row in new_rows
                if row[
                    "record_decision"
                ]
            ).items()
        )
    )

    receipt = {
        "status":
            "EVENT_TRANSACTION_PREPARED",

        "batch_id":
            ordered_proposals[
                0
            ][
                "batch_id"
            ],

        "proposal_sha256":
            proposal_sha256,

        "pre_append_ledger_sha256":
            observed_pre_sha,

        "post_append_ledger_sha256":
            sha256_bytes(
                candidate_bytes
            ),

        "pre_append_event_count":
            len(
                existing_rows
            ),

        "post_append_event_count":
            len(
                candidate_rows
            ),

        "new_event_count":
            len(
                new_rows
            ),

        "first_assigned_event_id":
            new_rows[
                0
            ][
                "event_id"
            ],

        "last_assigned_event_id":
            new_rows[
                -1
            ][
                "event_id"
            ],

        "transaction_timestamp_utc":
            transaction_timestamp_utc,

        "event_type_counts":
            event_type_counts,

        "terminal_decision_counts":
            terminal_decision_counts,

        "derived_state_counts_after_append":
            state_counts,

        "strict_prefix_extension":
            True,

        "review_fields_blank":
            True,

        "published":
            False,
    }

    return {
        "receipt":
            receipt,

        "candidate_bytes":
            candidate_bytes,

        "candidate_rows":
            candidate_rows,

        "new_rows":
            new_rows,
    }


def prepare_transaction_from_files(
    *,
    ledger_path: Path,
    proposal_path: Path,
    expected_pre_ledger_sha256: str,
    context: dict,
    transaction_timestamp_utc: str | None = None,
) -> dict:
    existing_bytes = ledger_path.read_bytes()

    existing_fields, existing_rows = (
        parse_tsv_bytes(
            existing_bytes
        )
    )

    (
        proposal_fields,
        proposal_rows,
        proposal_sha,
    ) = read_proposal(
        proposal_path
    )

    if proposal_fields != PROPOSAL_FIELDS:
        raise EventAppenderError(
            "Proposal field order changed"
        )

    timestamp = (
        transaction_timestamp_utc
        if transaction_timestamp_utc
        is not None
        else generate_transaction_timestamp()
    )

    return prepare_transaction_core(
        existing_fields=
            existing_fields,

        existing_rows=
            existing_rows,

        existing_bytes=
            existing_bytes,

        expected_pre_ledger_sha256=
            expected_pre_ledger_sha256,

        proposal_rows=
            proposal_rows,

        proposal_sha256=
            proposal_sha,

        context=
            context,

        transaction_timestamp_utc=
            timestamp,
    )


def is_real_production_ledger(
    path: Path,
) -> bool:
    return (
        path.resolve()
        == DEFAULT_LEDGER.resolve()
    )


def atomic_replace_bytes(
    *,
    target: Path,
    payload: bytes,
) -> None:
    parent = target.resolve().parent

    fd, temp_name = tempfile.mkstemp(
        prefix=(
            "."
            + target.name
            + ".append."
        ),
        dir=parent,
    )

    temp_path = Path(
        temp_name
    )

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

        os.replace(
            temp_path,
            target,
        )

        try:
            dir_fd = os.open(
                parent,
                os.O_RDONLY,
            )

        except OSError:
            dir_fd = None

        if dir_fd is not None:
            try:
                os.fsync(
                    dir_fd
                )

            finally:
                os.close(
                    dir_fd
                )

    finally:
        if temp_path.exists():
            temp_path.unlink()


def append_transaction_atomic(
    *,
    ledger_path: Path,
    proposal_path: Path,
    expected_pre_ledger_sha256: str,
    context: dict,
    transaction_timestamp_utc: str | None = None,
    allow_production: bool = False,
) -> dict:
    if (
        is_real_production_ledger(
            ledger_path
        )
        and not allow_production
    ):
        raise EventAppenderError(
            "Real production event entry is not authorised"
        )

    prepared = (
        prepare_transaction_from_files(
            ledger_path=
                ledger_path,

            proposal_path=
                proposal_path,

            expected_pre_ledger_sha256=
                expected_pre_ledger_sha256,

            context=
                context,

            transaction_timestamp_utc=
                transaction_timestamp_utc,
        )
    )

    pre_bytes = ledger_path.read_bytes()

    if sha256_bytes(
        pre_bytes
    ) != expected_pre_ledger_sha256:
        raise EventAppenderError(
            "Ledger changed before publication"
        )

    if not prepared[
        "candidate_bytes"
    ].startswith(
        pre_bytes
    ):
        raise EventAppenderError(
            "Candidate no longer extends current ledger"
        )

    atomic_replace_bytes(
        target=
            ledger_path,

        payload=
            prepared[
                "candidate_bytes"
            ],
    )

    published_bytes = (
        ledger_path.read_bytes()
    )

    if (
        published_bytes
        != prepared[
            "candidate_bytes"
        ]
    ):
        raise EventAppenderError(
            "Published ledger bytes differ from validated candidate"
        )

    fields, rows = (
        parse_tsv_bytes(
            published_bytes
        )
    )

    validation = (
        validate_existing_ledger_contract(
            fields=fields,
            rows=rows,
            context=context,
        )
    )

    receipt = dict(
        prepared[
            "receipt"
        ]
    )

    receipt[
        "published"
    ] = True

    receipt[
        "validated_post_append_event_count"
    ] = len(
        rows
    )

    receipt[
        "validated_post_append_ledger_sha256"
    ] = sha256_bytes(
        published_bytes
    )

    receipt[
        "derived_state_counts_after_append"
    ] = derive_active_state_counts(
        current_by_entity=
            validation[
                "current_by_entity"
            ],

        membership_by_entity=
            context[
                "membership_by_entity"
            ],
    )

    return receipt


def validate_current_ledger(
    *,
    ledger_path: Path,
    context: dict,
) -> dict:
    payload = ledger_path.read_bytes()

    fields, rows = (
        parse_tsv_bytes(
            payload
        )
    )

    validation = (
        validate_existing_ledger_contract(
            fields=fields,
            rows=rows,
            context=context,
        )
    )

    state_counts = (
        derive_active_state_counts(
            current_by_entity=
                validation[
                    "current_by_entity"
                ],

            membership_by_entity=
                context[
                    "membership_by_entity"
                ],
        )
    )

    return {
        "status":
            "EVENT_LEDGER_VALID",

        "ledger_sha256":
            sha256_bytes(
                payload
            ),

        "event_count":
            len(
                rows
            ),

        "current_event_count":
            len(
                validation[
                    "current_by_entity"
                ]
            ),

        "derived_state_counts":
            state_counts,

        "production_ledger":
            is_real_production_ledger(
                ledger_path
            ),

        "mutation_performed":
            False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--baseline-queue",
        type=Path,
        default=DEFAULT_QUEUE,
    )

    parser.add_argument(
        "--execution-root",
        type=Path,
        default=EXECUTION_ROOT,
    )

    parser.add_argument(
        "--design",
        type=Path,
        default=DEFAULT_DESIGN,
    )

    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
    )

    parser.add_argument(
        "--proposal-tsv",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--expected-pre-ledger-sha256",
        default=None,
    )

    parser.add_argument(
        "--append",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    context = load_context(
        queue_path=
            args.baseline_queue.resolve(),

        execution_root=
            args.execution_root.resolve(),

        design_path=
            args.design.resolve(),
    )

    ledger_path = (
        args.ledger.resolve()
    )

    if args.proposal_tsv is None:
        if args.append:
            raise EventAppenderError(
                "--append requires --proposal-tsv"
            )

        result = validate_current_ledger(
            ledger_path=
                ledger_path,

            context=
                context,
        )

    else:
        if (
            args.expected_pre_ledger_sha256
            is None
        ):
            raise EventAppenderError(
                "Proposal requires "
                "--expected-pre-ledger-sha256"
            )

        if args.append:
            # CLI intentionally cannot authorise the real
            # production ledger.
            result = append_transaction_atomic(
                ledger_path=
                    ledger_path,

                proposal_path=
                    args.proposal_tsv.resolve(),

                expected_pre_ledger_sha256=
                    args.expected_pre_ledger_sha256,

                context=
                    context,

                allow_production=False,
            )

        else:
            prepared = (
                prepare_transaction_from_files(
                    ledger_path=
                        ledger_path,

                    proposal_path=
                        args.proposal_tsv.resolve(),

                    expected_pre_ledger_sha256=
                        args.expected_pre_ledger_sha256,

                    context=
                        context,
                )
            )

            result = dict(
                prepared[
                    "receipt"
                ]
            )

            result[
                "status"
            ] = "EVENT_TRANSACTION_DRY_RUN"

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
