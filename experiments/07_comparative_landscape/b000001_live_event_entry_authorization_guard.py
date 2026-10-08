#!/usr/bin/env python3

"""
Experiment 07 B000001 live-event authorization guard.

Consumes:
- frozen B000001 authorization design; and
- B000001 authorization design Amendment 01.

Amendment 01 places ALL human-editable review-packet fields in the
`proposed_` namespace, preventing collisions with immutable baseline fields.

This implementation provides:
- deterministic 500-row B000001 review-packet generation;
- immutable review-packet validation;
- exact position-1 canary extraction;
- tracked one-use authorization validation;
- dry-run transaction preparation through the frozen event appender;
- T000001 checkpoint staging;
- guarded atomic event publication;
- checkpoint finalization/validation;
- fail-closed recovery-state detection.

This module does not create a live authorization artifact.

Without a separately committed authorization artifact satisfying the frozen
contract, real production execution fails closed.
"""

from __future__ import annotations

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
import shutil
import subprocess
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

RECEIPT_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_event_receipts"
)

DEFAULT_QUEUE = (
    SCREENING_ROOT
    / "baseline_screening_queue.tsv"
)

DEFAULT_LEDGER = (
    EXECUTION_ROOT
    / "event_ledger.tsv"
)

EVENT_ENTRY_DESIGN = (
    HERE
    / "baseline_scientific_screening_event_entry_design.json"
)

EVENT_ENTRY_DESIGN_SUMS = (
    HERE
    / "baseline_scientific_screening_event_entry_design.sha256"
)

APPENDER_SOURCE = (
    HERE
    / "baseline_scientific_screening_event_appender.py"
)

APPENDER_FREEZE = (
    HERE
    / "baseline_scientific_screening_event_appender_implementation.json"
)

APPENDER_FREEZE_SUMS = (
    HERE
    / "baseline_scientific_screening_event_appender_implementation.sha256"
)

B000001_DESIGN = (
    HERE
    / "b000001_live_event_entry_authorization_design.json"
)

B000001_DESIGN_SUMS = (
    HERE
    / "b000001_live_event_entry_authorization_design.sha256"
)

B000001_AMENDMENT = (
    HERE
    / "b000001_live_event_entry_authorization_design_amendment_01.json"
)

B000001_AMENDMENT_SUMS = (
    HERE
    / "b000001_live_event_entry_authorization_design_amendment_01.sha256"
)


EXPECTED_QUEUE_SHA256 = (
    "97575b71c4607c3dcad893d90210f913"
    "2a83d0ae2e299ac2f1aef7e94f527d58"
)

EXPECTED_GENESIS_LEDGER_SHA256 = (
    "d3ff9be1efe2b1237f616f25e702275c"
    "cc608577fa0ff8b301401a72900eb55f"
)

EXPECTED_APPENDER_SHA256 = (
    "abf4c15e9c993bcb96c73ccb53ff3dae"
    "56e229c533e9df25056c37cfd5eda98b"
)

EXPECTED_PARENT_DESIGN_COMMIT = (
    "ffd85ad0860c7af5bf02e5d568638638"
    "cb8e94df"
)

EXPECTED_BATCH_ID = "B000001"
EXPECTED_BATCH_COUNT = 500

EXPECTED_FIRST_ENTITY = (
    "publication_component:citation:publication:"
    "doi:10.1001/archdermatol.2012.1817"
)

EXPECTED_FIRST_ROW_SHA256 = (
    "bb8ef2c1e0fd980a70884709d3085b8e"
    "44b5b425500d390ae943f638f1d08048"
)

EXPECTED_MANIFEST_ORDERED_SHA256 = (
    "8a98c513759bc8a8d00a53cad104411a"
    "860aebe2ccdb20a825aa636ccfb06ceb"
)

EXPECTED_MEMBERSHIP_CANONICAL_SHA256 = (
    "dbf86779c8d82b0185cc1c5c03194d0"
    "0694b1322a2ef7235068c6d8082f3160b"
)

EXPECTED_BASELINE_CANONICAL_SHA256 = (
    "f9f1938f1fd296eb7ecc2ea9f0c87aae"
    "54a103e39d3374cd351293677698e12c"
)

TRANSACTION_ID = "T000001"

AUTH_STATUS = (
    "AUTHORIZED_B000001_POSITION_1_CANARY_ONE_USE"
)

AUTHORIZATION_FIELDS = {
    "status",
    "schema_version",
    "parent_commit",
    "b000001_authorization_design_freeze_sha256",
    "event_appender_implementation_sha256",
    "event_appender_implementation_freeze_sha256",
    "event_entry_design_freeze_sha256",
    "B000001_membership_identity",
    "batch_id",
    "authorized_position",
    "authorized_screening_entity_id",
    "authorized_baseline_row_sha256",
    "expected_pre_ledger_sha256",
    "max_live_event_count",
    "operator_id",
    "operator_type",
    "permitted_initial_event_types",
    "receipt_checkpoint_contract",
    "positions_2_to_500_authorized",
    "one_use",
    "scientific_decision_preselected",
}

REVIEW_MEMBERSHIP_FIELDS = [
    "batch_id",
    "position_in_batch",
    "global_active_index",
    "baseline_row_sha256",
]

AMENDED_HUMAN_FIELDS = [
    "proposed_event_type",
    "proposed_record_decision",
    "proposed_exclusion_reason_code",
    "proposed_candidate_method_flag",
    "proposed_evidence_basis",
    "proposed_evidence_source_locator",
    "proposed_evidence_escalation_status",
    "proposed_notes",
]

EXPECTED_PROPOSAL_MAPPING = {
    "proposed_event_type":
        "event_type",

    "proposed_record_decision":
        "record_decision",

    "proposed_exclusion_reason_code":
        "exclusion_reason_code",

    "proposed_candidate_method_flag":
        "candidate_method_flag",

    "proposed_evidence_basis":
        "evidence_basis",

    "proposed_evidence_source_locator":
        "evidence_source_locator",

    "proposed_evidence_escalation_status":
        "evidence_escalation_status",

    "proposed_notes":
        "notes",
}

LOWER_SHA256_RE = re.compile(
    r"^[0-9a-f]{64}$"
)

COMMIT_RE = re.compile(
    r"^[0-9a-f]{40}$"
)

FORBIDDEN_FIELD_CHARACTERS = (
    "\t",
    "\n",
    "\r",
    "\x00",
)


class GuardError(
    RuntimeError
):
    pass


class RecoveryRequiredError(
    GuardError
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


def pretty_json_bytes(
    value: Any,
) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
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

        return (
            list(
                reader.fieldnames
                or []
            ),
            list(reader),
        )


def tsv_bytes(
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

    writer.writeheader()
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
        raise GuardError(
            f"Forbidden control character in {field_name}"
        )


def validate_row_hygiene(
    row: dict[str, str],
) -> None:
    for field_name, value in row.items():
        validate_field_hygiene(
            value,
            field_name=field_name,
        )


def load_appender():
    freeze = json.loads(
        APPENDER_FREEZE.read_text(
            encoding="utf-8"
        )
    )

    expected = freeze[
        "implementation"
    ][
        "sha256"
    ]

    if expected != EXPECTED_APPENDER_SHA256:
        raise GuardError(
            "Frozen appender implementation SHA contract changed"
        )

    if sha256_file(
        APPENDER_SOURCE
    ) != expected:
        raise GuardError(
            "Frozen appender source SHA mismatch"
        )

    module_name = (
        "baseline_scientific_screening_event_appender_"
        "for_b000001_guard_amendment_01"
    )

    spec = importlib.util.spec_from_file_location(
        module_name,
        APPENDER_SOURCE,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise GuardError(
            "Unable to load frozen event appender"
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


def load_contract() -> dict:
    design = json.loads(
        B000001_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    amendment = json.loads(
        B000001_AMENDMENT.read_text(
            encoding="utf-8"
        )
    )

    if design[
        "status"
    ] != "FROZEN_PRE_IMPLEMENTATION":
        raise GuardError(
            "Parent B000001 design status changed"
        )

    if amendment[
        "status"
    ] != "FROZEN_PRE_IMPLEMENTATION_AMENDMENT":
        raise GuardError(
            "B000001 Amendment 01 status changed"
        )

    if amendment[
        "amendment_id"
    ] != "B000001_AUTHORIZATION_DESIGN_AMENDMENT_01":
        raise GuardError(
            "B000001 Amendment 01 identity changed"
        )

    if (
        amendment[
            "parent_b000001_authorization_design_commit"
        ]
        != EXPECTED_PARENT_DESIGN_COMMIT
    ):
        raise GuardError(
            "B000001 Amendment 01 parent commit changed"
        )

    if (
        amendment[
            "parent_b000001_authorization_design_sha256"
        ]
        != sha256_file(
            B000001_DESIGN
        )
    ):
        raise GuardError(
            "B000001 Amendment 01 parent design SHA mismatch"
        )

    if (
        amendment[
            "amended_human_entry_fields"
        ]
        != AMENDED_HUMAN_FIELDS
    ):
        raise GuardError(
            "Amended human-entry schema changed"
        )

    if (
        amendment[
            "proposal_extraction_mapping"
        ]
        != EXPECTED_PROPOSAL_MAPPING
    ):
        raise GuardError(
            "Amended proposal mapping changed"
        )

    if amendment[
        "scientific_contract_changed"
    ] is not False:
        raise GuardError(
            "Amendment unexpectedly changes scientific contract"
        )

    if amendment[
        "failed_guard_implementation_adopted"
    ] is not False:
        raise GuardError(
            "Failed prior guard unexpectedly adopted"
        )

    unchanged = amendment[
        "unchanged_contract"
    ]

    if unchanged[
        "batch_id"
    ] != EXPECTED_BATCH_ID:
        raise GuardError(
            "B000001 batch identity changed"
        )

    if unchanged[
        "batch_entity_count"
    ] != EXPECTED_BATCH_COUNT:
        raise GuardError(
            "B000001 entity count changed"
        )

    if unchanged[
        "canary_position"
    ] != 1:
        raise GuardError(
            "Canary position changed"
        )

    if (
        unchanged[
            "canary_screening_entity_id"
        ]
        != EXPECTED_FIRST_ENTITY
    ):
        raise GuardError(
            "Canary entity changed"
        )

    if (
        unchanged[
            "canary_baseline_row_sha256"
        ]
        != EXPECTED_FIRST_ROW_SHA256
    ):
        raise GuardError(
            "Canary baseline-row SHA changed"
        )

    if unchanged[
        "max_live_events"
    ] != 1:
        raise GuardError(
            "Canary event limit changed"
        )

    if (
        unchanged[
            "expected_pre_ledger_sha256"
        ]
        != EXPECTED_GENESIS_LEDGER_SHA256
    ):
        raise GuardError(
            "Expected pre-ledger SHA changed"
        )

    if unchanged[
        "live_authorized"
    ] is not False:
        raise GuardError(
            "Amendment unexpectedly authorises live entry"
        )

    expected_review_fields = (
        REVIEW_MEMBERSHIP_FIELDS
        + design[
            "review_packet"
        ][
            "baseline_queue_fields"
        ]
        + AMENDED_HUMAN_FIELDS
    )

    if (
        amendment[
            "amended_review_packet_fields"
        ]
        != expected_review_fields
    ):
        raise GuardError(
            "Amended review-packet field order changed"
        )

    if len(
        expected_review_fields
    ) != len(
        set(
            expected_review_fields
        )
    ):
        raise GuardError(
            "Amended review-packet schema is not unique"
        )

    if not all(
        field.startswith(
            "proposed_"
        )
        for field in AMENDED_HUMAN_FIELDS
    ):
        raise GuardError(
            "Human-entry fields not fully namespaced"
        )

    return {
        "design":
            design,

        "amendment":
            amendment,
    }


def git_output(
    *args: str,
) -> bytes:
    return subprocess.check_output(
        [
            "git",
            *args,
        ],
        cwd=REPO_ROOT,
    )


def ensure_tracked_authorization(
    authorization_path: Path,
    authorization: dict,
) -> str:
    resolved = authorization_path.resolve()

    try:
        relative = resolved.relative_to(
            REPO_ROOT.resolve()
        )

    except ValueError as exc:
        raise GuardError(
            "Production authorization must be inside repository"
        ) from exc

    relative_text = relative.as_posix()

    try:
        subprocess.check_call(
            [
                "git",
                "ls-files",
                "--error-unmatch",
                "--",
                relative_text,
            ],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    except subprocess.CalledProcessError as exc:
        raise GuardError(
            "Production authorization must be tracked"
        ) from exc

    current_head = (
        git_output(
            "rev-parse",
            "HEAD",
        )
        .decode(
            "ascii"
        )
        .strip()
    )

    parent_head = (
        git_output(
            "rev-parse",
            "HEAD^",
        )
        .decode(
            "ascii"
        )
        .strip()
    )

    if authorization[
        "parent_commit"
    ] != parent_head:
        raise GuardError(
            "Authorization parent_commit does not equal HEAD^"
        )

    committed_bytes = git_output(
        "show",
        f"HEAD:{relative_text}",
    )

    if committed_bytes != resolved.read_bytes():
        raise GuardError(
            "Authorization working bytes differ from committed HEAD"
        )

    if subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
        ],
        cwd=REPO_ROOT,
    ).returncode != 0:
        raise GuardError(
            "Tracked worktree must be clean before production execution"
        )

    if subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--quiet",
        ],
        cwd=REPO_ROOT,
    ).returncode != 0:
        raise GuardError(
            "Index must be clean before production execution"
        )

    return current_head


def derive_b000001_scope(
    *,
    queue_path: Path,
    execution_root: Path,
    contract: dict,
) -> dict:
    membership_fields, membership = read_tsv(
        execution_root
        / "batch_membership.tsv"
    )

    queue_fields, queue = read_tsv(
        queue_path
    )

    manifest_fields, manifests = read_tsv(
        execution_root
        / "batch_manifest.tsv"
    )

    del membership_fields
    del manifest_fields

    rows = sorted(
        [
            row
            for row in membership
            if row[
                "batch_id"
            ] == EXPECTED_BATCH_ID
        ],
        key=lambda row:
            int(
                row[
                    "position_in_batch"
                ]
            ),
    )

    if len(
        rows
    ) != EXPECTED_BATCH_COUNT:
        raise GuardError(
            "B000001 membership count mismatch"
        )

    if [
        int(
            row[
                "position_in_batch"
            ]
        )
        for row in rows
    ] != list(
        range(
            1,
            501,
        )
    ):
        raise GuardError(
            "B000001 position ordering changed"
        )

    if [
        int(
            row[
                "global_active_index"
            ]
        )
        for row in rows
    ] != list(
        range(
            1,
            501,
        )
    ):
        raise GuardError(
            "B000001 global active ordering changed"
        )

    ids = [
        row[
            "screening_entity_id"
        ]
        for row in rows
    ]

    if len(
        set(
            ids
        )
    ) != EXPECTED_BATCH_COUNT:
        raise GuardError(
            "Duplicate entity in B000001"
        )

    if ids[
        0
    ] != EXPECTED_FIRST_ENTITY:
        raise GuardError(
            "B000001 first entity changed"
        )

    if (
        rows[
            0
        ][
            "baseline_row_sha256"
        ]
        != EXPECTED_FIRST_ROW_SHA256
    ):
        raise GuardError(
            "B000001 first baseline-row SHA changed"
        )

    queue_by_id = {
        row[
            "screening_entity_id"
        ]:
            row
        for row in queue
    }

    for entity_id in ids:
        if entity_id not in queue_by_id:
            raise GuardError(
                "B000001 entity missing from baseline queue"
            )

        if (
            queue_by_id[
                entity_id
            ][
                "screening_state"
            ]
            != "ready"
        ):
            raise GuardError(
                "B000001 contains non-ready baseline entity"
            )

    canonical_ids_sha = sha256_bytes(
        canonical_json_bytes(
            ids
        )
    )

    canonical_membership_sha = sha256_bytes(
        canonical_json_bytes(
            rows
        )
    )

    baseline_rows = [
        queue_by_id[
            entity_id
        ]
        for entity_id in ids
    ]

    canonical_baseline_sha = sha256_bytes(
        canonical_json_bytes(
            baseline_rows
        )
    )

    manifest_rows = [
        row
        for row in manifests
        if row[
            "batch_id"
        ] == EXPECTED_BATCH_ID
    ]

    if len(
        manifest_rows
    ) != 1:
        raise GuardError(
            "B000001 manifest row count changed"
        )

    manifest = manifest_rows[
        0
    ]

    if (
        manifest[
            "ordered_entity_ids_sha256"
        ]
        != EXPECTED_MANIFEST_ORDERED_SHA256
    ):
        raise GuardError(
            "B000001 manifest ordered-ID SHA changed"
        )

    if (
        canonical_ids_sha
        != EXPECTED_MANIFEST_ORDERED_SHA256
    ):
        raise GuardError(
            "Independent ordered-ID SHA mismatch"
        )

    if (
        canonical_membership_sha
        != EXPECTED_MEMBERSHIP_CANONICAL_SHA256
    ):
        raise GuardError(
            "Canonical membership SHA mismatch"
        )

    if (
        canonical_baseline_sha
        != EXPECTED_BASELINE_CANONICAL_SHA256
    ):
        raise GuardError(
            "Canonical baseline SHA mismatch"
        )

    design = contract[
        "design"
    ]

    identity = design[
        "batch_identity"
    ]

    if (
        identity[
            "canonical_ordered_entity_ids_sha256"
        ]
        != canonical_ids_sha
    ):
        raise GuardError(
            "Parent design ordered-ID identity mismatch"
        )

    if (
        identity[
            "canonical_membership_rows_sha256"
        ]
        != canonical_membership_sha
    ):
        raise GuardError(
            "Parent design membership identity mismatch"
        )

    if (
        identity[
            "canonical_baseline_rows_sha256"
        ]
        != canonical_baseline_sha
    ):
        raise GuardError(
            "Parent design baseline identity mismatch"
        )

    return {
        "membership_rows":
            rows,

        "entity_ids":
            ids,

        "queue_fields":
            queue_fields,

        "queue_by_id":
            queue_by_id,

        "canonical_ids_sha256":
            canonical_ids_sha,

        "canonical_membership_sha256":
            canonical_membership_sha,

        "canonical_baseline_sha256":
            canonical_baseline_sha,
    }


def review_packet_fields(
    *,
    scope: dict,
    contract: dict,
) -> list[str]:
    fields = (
        REVIEW_MEMBERSHIP_FIELDS
        + scope[
            "queue_fields"
        ]
        + AMENDED_HUMAN_FIELDS
    )

    if (
        fields
        != contract[
            "amendment"
        ][
            "amended_review_packet_fields"
        ]
    ):
        raise GuardError(
            "Review packet no longer matches Amendment 01"
        )

    if len(
        fields
    ) != len(
        set(
            fields
        )
    ):
        raise GuardError(
            "Review-packet schema contains duplicate field names"
        )

    return fields


def build_review_packet_bytes(
    *,
    scope: dict,
    contract: dict,
) -> bytes:
    fields = review_packet_fields(
        scope=
            scope,

        contract=
            contract,
    )

    rows = []

    for membership in scope[
        "membership_rows"
    ]:
        entity_id = membership[
            "screening_entity_id"
        ]

        baseline = scope[
            "queue_by_id"
        ][
            entity_id
        ]

        row = {
            "batch_id":
                membership[
                    "batch_id"
                ],

            "position_in_batch":
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
        }

        for field in scope[
            "queue_fields"
        ]:
            row[
                field
            ] = baseline[
                field
            ]

        for field in AMENDED_HUMAN_FIELDS:
            row[
                field
            ] = ""

        rows.append(
            row
        )

    return tsv_bytes(
        fields=
            fields,

        rows=
            rows,
    )


def validate_review_packet(
    *,
    packet_path: Path,
    scope: dict,
    contract: dict,
    require_all_human_fields_blank: bool,
) -> list[dict[str, str]]:
    fields, rows = read_tsv(
        packet_path
    )

    expected_fields = review_packet_fields(
        scope=
            scope,

        contract=
            contract,
    )

    if fields != expected_fields:
        raise GuardError(
            "Review-packet schema mismatch"
        )

    if len(
        rows
    ) != EXPECTED_BATCH_COUNT:
        raise GuardError(
            "Review packet must contain exactly 500 rows"
        )

    for index, row in enumerate(
        rows,
        start=1,
    ):
        validate_row_hygiene(
            row
        )

        membership = scope[
            "membership_rows"
        ][
            index - 1
        ]

        entity_id = membership[
            "screening_entity_id"
        ]

        baseline = scope[
            "queue_by_id"
        ][
            entity_id
        ]

        for field in REVIEW_MEMBERSHIP_FIELDS:
            if (
                row[
                    field
                ]
                != membership[
                    field
                ]
            ):
                raise GuardError(
                    f"Review packet immutable membership mismatch "
                    f"at position {index}: {field}"
                )

        for field in scope[
            "queue_fields"
        ]:
            if (
                row[
                    field
                ]
                != baseline[
                    field
                ]
            ):
                raise GuardError(
                    f"Review packet frozen baseline mismatch "
                    f"at position {index}: {field}"
                )

        if index >= 2:
            for field in AMENDED_HUMAN_FIELDS:
                if row[
                    field
                ]:
                    raise GuardError(
                        "Positions 2-500 must retain blank "
                        "proposed_ fields"
                    )

        elif require_all_human_fields_blank:
            for field in AMENDED_HUMAN_FIELDS:
                if row[
                    field
                ]:
                    raise GuardError(
                        "Generated review packet contains "
                        "pre-populated proposed_ field"
                    )

    return rows


def load_authorization(
    path: Path,
) -> dict:
    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if set(
        value
    ) != AUTHORIZATION_FIELDS:
        raise GuardError(
            "Authorization schema mismatch"
        )

    return value


def expected_membership_identity(
    design: dict,
) -> dict:
    identity = design[
        "batch_identity"
    ]

    return {
        "batch_manifest_ordered_entity_ids_sha256":
            identity[
                "batch_manifest_ordered_entity_ids_sha256"
            ],

        "canonical_ordered_entity_ids_sha256":
            identity[
                "canonical_ordered_entity_ids_sha256"
            ],

        "canonical_membership_rows_sha256":
            identity[
                "canonical_membership_rows_sha256"
            ],

        "canonical_baseline_rows_sha256":
            identity[
                "canonical_baseline_rows_sha256"
            ],
    }


def validate_authorization(
    *,
    authorization_path: Path,
    contract: dict,
    appender,
    require_tracked: bool,
) -> dict:
    authorization = load_authorization(
        authorization_path
    )

    design = contract[
        "design"
    ]

    if authorization[
        "status"
    ] != AUTH_STATUS:
        raise GuardError(
            "Authorization status invalid"
        )

    if authorization[
        "schema_version"
    ] != 1:
        raise GuardError(
            "Authorization schema version invalid"
        )

    if not COMMIT_RE.fullmatch(
        authorization[
            "parent_commit"
        ]
    ):
        raise GuardError(
            "Authorization parent commit malformed"
        )

    if (
        authorization[
            "b000001_authorization_design_freeze_sha256"
        ]
        != sha256_file(
            B000001_DESIGN_SUMS
        )
    ):
        raise GuardError(
            "Authorization B000001 design freeze SHA mismatch"
        )

    if (
        authorization[
            "event_appender_implementation_sha256"
        ]
        != EXPECTED_APPENDER_SHA256
    ):
        raise GuardError(
            "Authorization appender source SHA mismatch"
        )

    if (
        authorization[
            "event_appender_implementation_freeze_sha256"
        ]
        != sha256_file(
            APPENDER_FREEZE_SUMS
        )
    ):
        raise GuardError(
            "Authorization appender freeze SHA mismatch"
        )

    if (
        authorization[
            "event_entry_design_freeze_sha256"
        ]
        != sha256_file(
            EVENT_ENTRY_DESIGN_SUMS
        )
    ):
        raise GuardError(
            "Authorization event-entry design freeze SHA mismatch"
        )

    if (
        authorization[
            "B000001_membership_identity"
        ]
        != expected_membership_identity(
            design
        )
    ):
        raise GuardError(
            "Authorization B000001 membership identity mismatch"
        )

    if authorization[
        "batch_id"
    ] != EXPECTED_BATCH_ID:
        raise GuardError(
            "Authorization batch mismatch"
        )

    if authorization[
        "authorized_position"
    ] != 1:
        raise GuardError(
            "Authorization position mismatch"
        )

    if (
        authorization[
            "authorized_screening_entity_id"
        ]
        != EXPECTED_FIRST_ENTITY
    ):
        raise GuardError(
            "Authorization canary entity mismatch"
        )

    if (
        authorization[
            "authorized_baseline_row_sha256"
        ]
        != EXPECTED_FIRST_ROW_SHA256
    ):
        raise GuardError(
            "Authorization canary row SHA mismatch"
        )

    if (
        authorization[
            "expected_pre_ledger_sha256"
        ]
        != EXPECTED_GENESIS_LEDGER_SHA256
    ):
        raise GuardError(
            "Authorization pre-ledger SHA mismatch"
        )

    if authorization[
        "max_live_event_count"
    ] != 1:
        raise GuardError(
            "Authorization event limit must equal one"
        )

    if not authorization[
        "operator_id"
    ].strip():
        raise GuardError(
            "Authorization operator_id empty"
        )

    validate_field_hygiene(
        authorization[
            "operator_id"
        ],
        field_name="operator_id",
    )

    if (
        authorization[
            "operator_type"
        ]
        not in set(
            appender.load_base_engine().OPERATOR_TYPES
        )
    ):
        raise GuardError(
            "Authorization operator_type invalid"
        )

    if authorization[
        "permitted_initial_event_types"
    ] != [
        "record_decision",
        "source_escalation",
    ]:
        raise GuardError(
            "Authorization event-type scope changed"
        )

    expected_checkpoint = {
        "transaction_id":
            TRANSACTION_ID,

        "root":
            (
                "results/07_comparative_landscape/"
                "baseline_scientific_screening_event_receipts"
            ),

        "final_transaction_directory":
            (
                "results/07_comparative_landscape/"
                "baseline_scientific_screening_event_receipts/"
                "T000001"
            ),

        "final_files": [
            "authorization.json",
            "proposal.tsv",
            "receipt.json",
        ],
    }

    if (
        authorization[
            "receipt_checkpoint_contract"
        ]
        != expected_checkpoint
    ):
        raise GuardError(
            "Authorization checkpoint contract mismatch"
        )

    if authorization[
        "positions_2_to_500_authorized"
    ] is not False:
        raise GuardError(
            "Authorization illegally enables positions 2-500"
        )

    if authorization[
        "one_use"
    ] is not True:
        raise GuardError(
            "Authorization must be one-use"
        )

    if authorization[
        "scientific_decision_preselected"
    ] is not False:
        raise GuardError(
            "Authorization must not preselect scientific decision"
        )

    if require_tracked:
        authorization_commit = (
            ensure_tracked_authorization(
                authorization_path,
                authorization,
            )
        )

    else:
        authorization_commit = (
            "UNTRACKED_TEST_AUTHORIZATION"
        )

    return {
        "authorization":
            authorization,

        "authorization_sha256":
            sha256_file(
                authorization_path
            ),

        "authorization_commit":
            authorization_commit,
    }


def extract_canary_proposal_bytes(
    *,
    review_packet_path: Path,
    scope: dict,
    contract: dict,
    authorization: dict,
    appender,
) -> bytes:
    rows = validate_review_packet(
        packet_path=
            review_packet_path,

        scope=
            scope,

        contract=
            contract,

        require_all_human_fields_blank=False,
    )

    canary = rows[
        0
    ]

    if (
        canary[
            "screening_entity_id"
        ]
        != EXPECTED_FIRST_ENTITY
    ):
        raise GuardError(
            "Review packet canary entity changed"
        )

    event_type = canary[
        "proposed_event_type"
    ]

    if (
        event_type
        not in authorization[
            "permitted_initial_event_types"
        ]
    ):
        raise GuardError(
            "Canary event type not authorised"
        )

    mapping = contract[
        "amendment"
    ][
        "proposal_extraction_mapping"
    ]

    proposal = {
        "screening_entity_id":
            EXPECTED_FIRST_ENTITY,

        "batch_id":
            EXPECTED_BATCH_ID,

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
            authorization[
                "operator_id"
            ],

        "operator_type":
            authorization[
                "operator_type"
            ],

        "notes":
            "",
    }

    for review_field, proposal_field in mapping.items():
        proposal[
            proposal_field
        ] = canary[
            review_field
        ]

    validate_row_hygiene(
        proposal
    )

    return tsv_bytes(
        fields=
            list(
                appender.PROPOSAL_FIELDS
            ),

        rows=[
            proposal
        ],
    )


def load_guard_context(
    *,
    queue_path: Path,
    execution_root: Path,
) -> dict:
    if (
        sha256_file(
            queue_path
        )
        != EXPECTED_QUEUE_SHA256
    ):
        raise GuardError(
            "Frozen baseline queue SHA mismatch"
        )

    contract = load_contract()

    appender = load_appender()

    appender_context = (
        appender.load_context(
            queue_path=
                queue_path,

            execution_root=
                execution_root,

            design_path=
                EVENT_ENTRY_DESIGN,
        )
    )

    scope = derive_b000001_scope(
        queue_path=
            queue_path,

        execution_root=
            execution_root,

        contract=
            contract,
    )

    return {
        "contract":
            contract,

        "appender":
            appender,

        "appender_context":
            appender_context,

        "scope":
            scope,
    }


def write_new_file(
    *,
    path: Path,
    payload: bytes,
) -> None:
    if path.exists():
        raise GuardError(
            f"Refusing to overwrite existing path: {path}"
        )

    if not path.parent.is_dir():
        raise GuardError(
            f"Output parent does not exist: {path.parent}"
        )

    path.write_bytes(
        payload
    )


def fsync_file(
    path: Path,
) -> None:
    with path.open(
        "rb"
    ) as handle:
        os.fsync(
            handle.fileno()
        )


def fsync_directory(
    path: Path,
) -> None:
    try:
        fd = os.open(
            path,
            os.O_RDONLY,
        )

    except OSError:
        return

    try:
        os.fsync(
            fd
        )

    finally:
        os.close(
            fd
        )


def prepare_canary(
    *,
    authorization_path: Path,
    review_packet_path: Path,
    ledger_path: Path,
    context: dict,
    require_tracked_authorization: bool,
    transaction_timestamp_utc: str | None = None,
) -> dict:
    appender = context[
        "appender"
    ]

    authorization_info = (
        validate_authorization(
            authorization_path=
                authorization_path,

            contract=
                context[
                    "contract"
                ],

            appender=
                appender,

            require_tracked=
                require_tracked_authorization,
        )
    )

    authorization = (
        authorization_info[
            "authorization"
        ]
    )

    ledger_validation = (
        appender.validate_current_ledger(
            ledger_path=
                ledger_path,

            context=
                context[
                    "appender_context"
                ],
        )
    )

    if ledger_validation[
        "event_count"
    ] != 0:
        raise GuardError(
            "Canary authorization requires zero-event ledger"
        )

    if (
        ledger_validation[
            "ledger_sha256"
        ]
        != authorization[
            "expected_pre_ledger_sha256"
        ]
    ):
        raise GuardError(
            "Canary authorization is stale for current ledger"
        )

    proposal_bytes = (
        extract_canary_proposal_bytes(
            review_packet_path=
                review_packet_path,

            scope=
                context[
                    "scope"
                ],

            contract=
                context[
                    "contract"
                ],

            authorization=
                authorization,

            appender=
                appender,
        )
    )

    proposal_sha = sha256_bytes(
        proposal_bytes
    )

    with tempfile.TemporaryDirectory(
        prefix="branchsnv-exp07-canary-dryrun-"
    ) as tmp:
        proposal_path = (
            Path(tmp)
            / "proposal.tsv"
        )

        proposal_path.write_bytes(
            proposal_bytes
        )

        prepared = (
            appender.prepare_transaction_from_files(
                ledger_path=
                    ledger_path,

                proposal_path=
                    proposal_path,

                expected_pre_ledger_sha256=
                    authorization[
                        "expected_pre_ledger_sha256"
                    ],

                context=
                    context[
                        "appender_context"
                    ],

                transaction_timestamp_utc=
                    transaction_timestamp_utc,
            )
        )

    receipt = dict(
        prepared[
            "receipt"
        ]
    )

    if receipt[
        "batch_id"
    ] != EXPECTED_BATCH_ID:
        raise GuardError(
            "Prepared transaction batch changed"
        )

    if receipt[
        "new_event_count"
    ] != 1:
        raise GuardError(
            "Prepared canary must contain exactly one event"
        )

    if receipt[
        "first_assigned_event_id"
    ] != "E000000001":
        raise GuardError(
            "Prepared first event ID mismatch"
        )

    if receipt[
        "last_assigned_event_id"
    ] != "E000000001":
        raise GuardError(
            "Prepared last event ID mismatch"
        )

    if receipt[
        "pre_append_event_count"
    ] != 0:
        raise GuardError(
            "Prepared pre-event count changed"
        )

    if receipt[
        "post_append_event_count"
    ] != 1:
        raise GuardError(
            "Prepared post-event count changed"
        )

    if receipt[
        "published"
    ] is not False:
        raise GuardError(
            "Dry-run canary unexpectedly published"
        )

    return {
        "status":
            "B000001_CANARY_DRY_RUN_VALID",

        "authorization":
            authorization,

        "authorization_sha256":
            authorization_info[
                "authorization_sha256"
            ],

        "authorization_commit":
            authorization_info[
                "authorization_commit"
            ],

        "proposal_bytes":
            proposal_bytes,

        "proposal_sha256":
            proposal_sha,

        "prepared_receipt":
            receipt,
    }


def detect_recovery_state(
    *,
    ledger_path: Path,
    receipt_root: Path,
) -> dict:
    ledger_sha = sha256_file(
        ledger_path
    )

    final_dir = (
        receipt_root
        / TRANSACTION_ID
    )

    temp_dirs = []

    if receipt_root.exists():
        temp_dirs = sorted(
            [
                path
                for path
                in receipt_root.iterdir()
                if (
                    path.is_dir()
                    and path.name.startswith(
                        ".T000001.tmp."
                    )
                )
            ]
        )

    if final_dir.exists():
        return {
            "status":
                "FINAL_CHECKPOINT_EXISTS",

            "ledger_sha256":
                ledger_sha,

            "final_checkpoint_exists":
                True,

            "temporary_checkpoint_count":
                len(
                    temp_dirs
                ),
        }

    if (
        ledger_sha
        != EXPECTED_GENESIS_LEDGER_SHA256
    ):
        return {
            "status":
                "RECOVERY_REQUIRED",

            "ledger_sha256":
                ledger_sha,

            "final_checkpoint_exists":
                False,

            "temporary_checkpoint_count":
                len(
                    temp_dirs
                ),
        }

    if temp_dirs:
        return {
            "status":
                "UNEXPECTED_STAGED_CHECKPOINT_PRE_APPEND",

            "ledger_sha256":
                ledger_sha,

            "final_checkpoint_exists":
                False,

            "temporary_checkpoint_count":
                len(
                    temp_dirs
                ),
        }

    return {
        "status":
            "GENESIS_READY",

        "ledger_sha256":
            ledger_sha,

        "final_checkpoint_exists":
            False,

        "temporary_checkpoint_count":
            0,
    }


def validate_checkpoint(
    *,
    checkpoint_dir: Path,
    ledger_path: Path,
) -> dict:
    if not checkpoint_dir.is_dir():
        raise GuardError(
            "Checkpoint directory missing"
        )

    children = list(
        checkpoint_dir.iterdir()
    )

    if any(
        path.is_symlink()
        for path in children
    ):
        raise GuardError(
            "Checkpoint contains symlink"
        )

    if any(
        not path.is_file()
        for path in children
    ):
        raise GuardError(
            "Checkpoint contains non-file artifact"
        )

    expected = {
        "authorization.json",
        "proposal.tsv",
        "receipt.json",
    }

    names = {
        path.name
        for path in children
    }

    if names != expected:
        raise GuardError(
            "Checkpoint artifact set mismatch"
        )

    receipt = json.loads(
        (
            checkpoint_dir
            / "receipt.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    if receipt[
        "transaction_id"
    ] != TRANSACTION_ID:
        raise GuardError(
            "Checkpoint transaction ID mismatch"
        )

    if (
        receipt[
            "proposal_sha256"
        ]
        != sha256_file(
            checkpoint_dir
            / "proposal.tsv"
        )
    ):
        raise GuardError(
            "Checkpoint proposal SHA mismatch"
        )

    if (
        receipt[
            "authorization_json_sha256"
        ]
        != sha256_file(
            checkpoint_dir
            / "authorization.json"
        )
    ):
        raise GuardError(
            "Checkpoint authorization SHA mismatch"
        )

    if (
        receipt[
            "validated_post_append_ledger_sha256"
        ]
        != sha256_file(
            ledger_path
        )
    ):
        raise GuardError(
            "Checkpoint post-ledger SHA mismatch"
        )

    if receipt[
        "first_assigned_event_id"
    ] != "E000000001":
        raise GuardError(
            "Checkpoint first event ID mismatch"
        )

    if receipt[
        "last_assigned_event_id"
    ] != "E000000001":
        raise GuardError(
            "Checkpoint last event ID mismatch"
        )

    if receipt[
        "pre_append_event_count"
    ] != 0:
        raise GuardError(
            "Checkpoint pre-event count mismatch"
        )

    if receipt[
        "post_append_event_count"
    ] != 1:
        raise GuardError(
            "Checkpoint post-event count mismatch"
        )

    if receipt[
        "published"
    ] is not True:
        raise GuardError(
            "Checkpoint receipt not marked published"
        )

    if receipt[
        "post_publication_validation_passed"
    ] is not True:
        raise GuardError(
            "Post-publication validation not recorded"
        )

    if receipt[
        "checkpoint_status"
    ] != "COMPLETE":
        raise GuardError(
            "Checkpoint status not complete"
        )

    return {
        "status":
            "T000001_CHECKPOINT_VALID",

        "transaction_id":
            TRANSACTION_ID,

        "post_append_ledger_sha256":
            receipt[
                "validated_post_append_ledger_sha256"
            ],

        "proposal_sha256":
            receipt[
                "proposal_sha256"
            ],
    }


def execute_canary(
    *,
    authorization_path: Path,
    review_packet_path: Path,
    ledger_path: Path,
    receipt_root: Path,
    context: dict,
    require_tracked_authorization: bool,
    transaction_timestamp_utc: str | None = None,
    _test_fail_after_append: bool = False,
) -> dict:
    is_real_production = (
        ledger_path.resolve()
        == DEFAULT_LEDGER.resolve()
    )

    if is_real_production:
        if (
            receipt_root.resolve()
            != RECEIPT_ROOT.resolve()
        ):
            raise GuardError(
                "Real production ledger requires canonical receipt root"
            )

        if not require_tracked_authorization:
            raise GuardError(
                "Real production requires tracked authorization"
            )

    recovery = detect_recovery_state(
        ledger_path=
            ledger_path,

        receipt_root=
            receipt_root,
    )

    if recovery[
        "status"
    ] != "GENESIS_READY":
        raise RecoveryRequiredError(
            "T000001 cannot execute from state: "
            + recovery[
                "status"
            ]
        )

    prepared = prepare_canary(
        authorization_path=
            authorization_path,

        review_packet_path=
            review_packet_path,

        ledger_path=
            ledger_path,

        context=
            context,

        require_tracked_authorization=
            require_tracked_authorization,

        transaction_timestamp_utc=
            transaction_timestamp_utc,
    )

    authorization = prepared[
        "authorization"
    ]

    pre_sha = authorization[
        "expected_pre_ledger_sha256"
    ]

    if sha256_file(
        ledger_path
    ) != pre_sha:
        raise GuardError(
            "Ledger changed after canary preparation"
        )

    if receipt_root.exists():
        raise GuardError(
            "Receipt root unexpectedly exists before T000001"
        )

    receipt_root.mkdir(
        mode=0o755,
        parents=False,
    )

    temp_dir = Path(
        tempfile.mkdtemp(
            prefix=".T000001.tmp.",
            dir=receipt_root,
        )
    )

    final_dir = (
        receipt_root
        / TRANSACTION_ID
    )

    appended = False

    try:
        authorization_copy = (
            temp_dir
            / "authorization.json"
        )

        proposal_copy = (
            temp_dir
            / "proposal.tsv"
        )

        authorization_copy.write_bytes(
            authorization_path.read_bytes()
        )

        proposal_copy.write_bytes(
            prepared[
                "proposal_bytes"
            ]
        )

        fsync_file(
            authorization_copy
        )

        fsync_file(
            proposal_copy
        )

        fsync_directory(
            temp_dir
        )

        fsync_directory(
            receipt_root
        )

        if sha256_file(
            ledger_path
        ) != pre_sha:
            raise GuardError(
                "Ledger changed immediately before publication"
            )

        appender = context[
            "appender"
        ]

        receipt = (
            appender.append_transaction_atomic(
                ledger_path=
                    ledger_path,

                proposal_path=
                    proposal_copy,

                expected_pre_ledger_sha256=
                    pre_sha,

                context=
                    context[
                        "appender_context"
                    ],

                transaction_timestamp_utc=
                    transaction_timestamp_utc,

                allow_production=True,
            )
        )

        appended = True

        if _test_fail_after_append:
            raise RuntimeError(
                "SYNTHETIC_TEST_FAILURE_AFTER_LEDGER_APPEND"
            )

        post_validation = (
            appender.validate_current_ledger(
                ledger_path=
                    ledger_path,

                context=
                    context[
                        "appender_context"
                    ],
            )
        )

        if post_validation[
            "event_count"
        ] != 1:
            raise GuardError(
                "Post-canary ledger must contain exactly one event"
            )

        receipt = dict(
            receipt
        )

        receipt.update({
            "transaction_id":
                TRANSACTION_ID,

            "screening_entity_id":
                EXPECTED_FIRST_ENTITY,

            "authorization_commit":
                prepared[
                    "authorization_commit"
                ],

            "authorization_json_sha256":
                prepared[
                    "authorization_sha256"
                ],

            "event_appender_implementation_sha256":
                EXPECTED_APPENDER_SHA256,

            "b000001_authorization_design_amendment_01_freeze_sha256":
                sha256_file(
                    B000001_AMENDMENT_SUMS
                ),

            "proposal_sha256":
                prepared[
                    "proposal_sha256"
                ],

            "checkpoint_status":
                "COMPLETE",

            "post_publication_validation_passed":
                True,
        })

        receipt_path = (
            temp_dir
            / "receipt.json"
        )

        receipt_path.write_bytes(
            pretty_json_bytes(
                receipt
            )
        )

        fsync_file(
            receipt_path
        )

        fsync_directory(
            temp_dir
        )

        if final_dir.exists():
            raise GuardError(
                "Final T000001 checkpoint unexpectedly exists"
            )

        os.replace(
            temp_dir,
            final_dir,
        )

        fsync_directory(
            receipt_root
        )

        checkpoint_validation = (
            validate_checkpoint(
                checkpoint_dir=
                    final_dir,

                ledger_path=
                    ledger_path,
            )
        )

        return {
            "status":
                "B000001_CANARY_EXECUTION_COMPLETE",

            "transaction_id":
                TRANSACTION_ID,

            "checkpoint":
                checkpoint_validation,

            "receipt":
                receipt,
        }

    except Exception as exc:
        current_sha = sha256_file(
            ledger_path
        )

        if (
            appended
            or current_sha != pre_sha
        ):
            raise RecoveryRequiredError(
                "Ledger changed but T000001 checkpoint did not "
                "finalize; preserve staged checkpoint and enter "
                "recovery workflow"
            ) from exc

        if temp_dir.exists():
            shutil.rmtree(
                temp_dir
            )

        if (
            receipt_root.exists()
            and not any(
                receipt_root.iterdir()
            )
        ):
            receipt_root.rmdir()

        raise


def describe_state(
    *,
    context: dict,
    ledger_path: Path,
    receipt_root: Path,
) -> dict:
    appender = context[
        "appender"
    ]

    ledger = appender.validate_current_ledger(
        ledger_path=
            ledger_path,

        context=
            context[
                "appender_context"
            ],
    )

    packet = build_review_packet_bytes(
        scope=
            context[
                "scope"
            ],

        contract=
            context[
                "contract"
            ],
    )

    recovery = detect_recovery_state(
        ledger_path=
            ledger_path,

        receipt_root=
            receipt_root,
    )

    return {
        "status":
            "B000001_GUARD_READY_PRE_AUTHORIZATION",

        "amendment":
            "B000001_AUTHORIZATION_DESIGN_AMENDMENT_01",

        "batch_id":
            EXPECTED_BATCH_ID,

        "batch_entity_count":
            EXPECTED_BATCH_COUNT,

        "canary_position":
            1,

        "canary_screening_entity_id":
            EXPECTED_FIRST_ENTITY,

        "canary_baseline_row_sha256":
            EXPECTED_FIRST_ROW_SHA256,

        "review_packet_bytes":
            len(
                packet
            ),

        "review_packet_sha256":
            sha256_bytes(
                packet
            ),

        "review_packet_human_field_count":
            len(
                AMENDED_HUMAN_FIELDS
            ),

        "review_packet_human_fields":
            list(
                AMENDED_HUMAN_FIELDS
            ),

        "ledger_sha256":
            ledger[
                "ledger_sha256"
            ],

        "event_count":
            ledger[
                "event_count"
            ],

        "derived_state_counts":
            ledger[
                "derived_state_counts"
            ],

        "checkpoint_state":
            recovery[
                "status"
            ],

        "live_authorization_created_by_guard":
            False,

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
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
    )

    parser.add_argument(
        "--receipt-root",
        type=Path,
        default=RECEIPT_ROOT,
    )

    parser.add_argument(
        "--generate-review-packet",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--authorization-json",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--review-packet",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--dry-run-canary",
        action="store_true",
    )

    parser.add_argument(
        "--execute-canary",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    context = load_guard_context(
        queue_path=
            args.baseline_queue.resolve(),

        execution_root=
            args.execution_root.resolve(),
    )

    ledger_path = (
        args.ledger.resolve()
    )

    receipt_root = (
        args.receipt_root.resolve()
    )

    if (
        args.dry_run_canary
        and args.execute_canary
    ):
        raise GuardError(
            "Choose only one canary action"
        )

    if (
        args.generate_review_packet
        is not None
    ):
        if (
            args.dry_run_canary
            or args.execute_canary
        ):
            raise GuardError(
                "Review-packet generation cannot be combined "
                "with canary execution"
            )

        payload = build_review_packet_bytes(
            scope=
                context[
                    "scope"
                ],

            contract=
                context[
                    "contract"
                ],
        )

        output = (
            args.generate_review_packet.resolve()
        )

        write_new_file(
            path=
                output,

            payload=
                payload,
        )

        result = {
            "status":
                "B000001_REVIEW_PACKET_GENERATED",

            "path":
                str(
                    output
                ),

            "rows":
                500,

            "sha256":
                sha256_bytes(
                    payload
                ),

            "bytes":
                len(
                    payload
                ),

            "human_fields":
                list(
                    AMENDED_HUMAN_FIELDS
                ),

            "human_fields_prepopulated":
                False,

            "mutation_of_event_ledger":
                False,
        }

    elif (
        args.dry_run_canary
        or args.execute_canary
    ):
        if (
            args.authorization_json
            is None
            or args.review_packet
            is None
        ):
            raise GuardError(
                "Canary action requires authorization JSON "
                "and review packet"
            )

        if args.execute_canary:
            result = execute_canary(
                authorization_path=
                    args.authorization_json.resolve(),

                review_packet_path=
                    args.review_packet.resolve(),

                ledger_path=
                    ledger_path,

                receipt_root=
                    receipt_root,

                context=
                    context,

                require_tracked_authorization=True,
            )

        else:
            prepared = prepare_canary(
                authorization_path=
                    args.authorization_json.resolve(),

                review_packet_path=
                    args.review_packet.resolve(),

                ledger_path=
                    ledger_path,

                context=
                    context,

                require_tracked_authorization=True,
            )

            result = {
                "status":
                    prepared[
                        "status"
                    ],

                "authorization_commit":
                    prepared[
                        "authorization_commit"
                    ],

                "authorization_sha256":
                    prepared[
                        "authorization_sha256"
                    ],

                "proposal_sha256":
                    prepared[
                        "proposal_sha256"
                    ],

                "prepared_receipt":
                    prepared[
                        "prepared_receipt"
                    ],

                "mutation_performed":
                    False,
            }

    else:
        result = describe_state(
            context=
                context,

            ledger_path=
                ledger_path,

            receipt_root=
                receipt_root,
        )

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
