#!/usr/bin/env python3

"""
Experiment 07 B000001 T000002 continuation guard.

Implements the frozen post-canary continuation design for exactly
B000001 positions 2-11.

This module:
- consumes the already-frozen T000001 completion state;
- validates the exact ten-record continuation target;
- locks position 1 to the accepted T000001 review state;
- permits proposed scientific input only for positions 2-11;
- requires all ten target positions before transaction preparation;
- forbids proposals at positions 12-500;
- validates a future separately tracked one-use T000002 authorization;
- prepares exactly ten events, E000000002-E000000011;
- stages/finalizes the exact three-file T000002 checkpoint;
- detects partial-completion/recovery states;
- prevents replay.

This module does NOT create a live authorization artifact and does not itself
preselect any scientific disposition.
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

REVIEW_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_review_work"
    / "B000001"
)

DEFAULT_QUEUE = (
    SCREENING_ROOT
    / "baseline_screening_queue.tsv"
)

DEFAULT_LEDGER = (
    EXECUTION_ROOT
    / "event_ledger.tsv"
)

DEFAULT_REVIEW_PACKET = (
    REVIEW_ROOT
    / "review_packet.tsv"
)

T000001_CHECKPOINT = (
    RECEIPT_ROOT
    / "T000001"
)

T000002_CHECKPOINT = (
    RECEIPT_ROOT
    / "T000002"
)

BASE_GUARD_SOURCE = (
    HERE
    / "b000001_live_event_entry_authorization_guard.py"
)

BASE_GUARD_FREEZE_SUMS = (
    HERE
    / "b000001_live_event_entry_authorization_guard_implementation.sha256"
)

CONTINUATION_DESIGN = (
    HERE
    / "b000001_post_canary_continuation_design.json"
)

CONTINUATION_DESIGN_SUMS = (
    HERE
    / "b000001_post_canary_continuation_design.sha256"
)

T000001_COMPLETION = (
    HERE
    / "t000001_production_completion_and_reconciliation.json"
)

T000001_COMPLETION_SUMS = (
    HERE
    / "t000001_production_completion_and_reconciliation.sha256"
)


EXPECTED_PARENT_DESIGN_COMMIT = (
    "cbbc10804c88e1855cfd87b04d55a79927a86679"
)

EXPECTED_PRE_LEDGER_SHA256 = (
    "33b49116d126f45cb54354b121eb69eb"
    "0abb212738794fef524a667ee0b2f2ba"
)

EXPECTED_PRE_REVIEW_PACKET_SHA256 = (
    "bbaa8eeed4b60fa310434819dcf67ecf"
    "540d25112634818690bdb37cf5e0e286"
)

EXPECTED_PRE_REVIEW_PACKET_BYTES = 306073

EXPECTED_TARGET_IDS_SHA256 = (
    "ab135632dc02db9435ccec5ce5301ef9"
    "847770c1ee61a9d91de9103a9ca9ea65"
)

EXPECTED_TARGET_MEMBERSHIP_SHA256 = (
    "c35fb0b42daf9c7bec8ce70f7170452b"
    "6f19800d0bddcfd6e83ccdccb432ba09"
)

EXPECTED_TARGET_BASELINE_SHA256 = (
    "c02e9eb5d12fd8433c363bc24dccf1f3"
    "d965fa9c4fd64edb48a74576b98bdbd7"
)

EXPECTED_TARGET_IDENTITY_SHA256 = (
    "2f8188c05e3e804133604cbe9d2f1325"
    "657aa30f9aa87dcbe5c75572908eb671"
)

EXPECTED_TARGET_POSITIONS = list(
    range(
        2,
        12,
    )
)

EXPECTED_TARGET_COUNT = 10

EXPECTED_PRE_EVENT_COUNT = 1
EXPECTED_POST_EVENT_COUNT = 11

EXPECTED_FIRST_EVENT_ID = "E000000002"
EXPECTED_LAST_EVENT_ID = "E000000011"

TRANSACTION_ID = "T000002"
BATCH_ID = "B000001"

AUTH_STATUS = (
    "AUTHORIZED_B000001_T000002_POSITIONS_2_TO_11_ONE_USE"
)

AUTHORIZATION_FIELDS = {
    "status",
    "schema_version",
    "parent_commit",
    "post_canary_continuation_design_freeze_sha256",
    "t000001_completion_freeze_sha256",
    "event_appender_implementation_sha256",
    "event_appender_implementation_freeze_sha256",
    "event_entry_design_freeze_sha256",
    "target_identity",
    "batch_id",
    "authorized_positions",
    "expected_pre_ledger_sha256",
    "expected_pre_event_count",
    "max_live_event_count",
    "expected_first_event_id",
    "expected_last_event_id",
    "operator_id",
    "operator_type",
    "permitted_initial_event_types",
    "receipt_checkpoint_contract",
    "positions_12_to_500_authorized",
    "partial_transaction_permitted",
    "one_use",
    "scientific_decisions_preselected",
}

PROPOSED_FIELDS = [
    "proposed_event_type",
    "proposed_record_decision",
    "proposed_exclusion_reason_code",
    "proposed_candidate_method_flag",
    "proposed_evidence_basis",
    "proposed_evidence_source_locator",
    "proposed_evidence_escalation_status",
    "proposed_notes",
]

PROPOSAL_MAPPING = {
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

COMMIT_RE = re.compile(
    r"^[0-9a-f]{40}$"
)


class ContinuationGuardError(
    RuntimeError
):
    pass


class RecoveryRequiredError(
    ContinuationGuardError
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


def canonical_sha(
    value: Any,
) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            value
        )
    )


def pretty_json_bytes(
    value: Any,
) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
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


def load_base_guard():
    module_name = (
        "b000001_base_guard_for_t000002_continuation"
    )

    spec = importlib.util.spec_from_file_location(
        module_name,
        BASE_GUARD_SOURCE,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise ContinuationGuardError(
            "Unable to load frozen B000001 base guard"
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


def load_design() -> dict:
    value = json.loads(
        CONTINUATION_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if value[
        "status"
    ] != "FROZEN_PRE_IMPLEMENTATION":
        raise ContinuationGuardError(
            "Continuation design status changed"
        )

    if value[
        "design_id"
    ] != "B000001_POST_CANARY_CONTINUATION_DESIGN":
        raise ContinuationGuardError(
            "Continuation design identity changed"
        )

    if (
        value[
            "parent_t000001_completion_commit"
        ]
        != "5770934347af9d604c22c8c199cbb6e9c1db58ca"
    ):
        raise ContinuationGuardError(
            "Continuation-design T000001 parent changed"
        )

    t2 = value[
        "t000002"
    ]

    if t2[
        "transaction_id"
    ] != TRANSACTION_ID:
        raise ContinuationGuardError(
            "Transaction ID changed"
        )

    if t2[
        "batch_id"
    ] != BATCH_ID:
        raise ContinuationGuardError(
            "Batch ID changed"
        )

    if t2[
        "target_positions"
    ] != EXPECTED_TARGET_POSITIONS:
        raise ContinuationGuardError(
            "Target positions changed"
        )

    if t2[
        "target_event_count"
    ] != EXPECTED_TARGET_COUNT:
        raise ContinuationGuardError(
            "Target event count changed"
        )

    if t2[
        "partial_transaction_permitted"
    ] is not False:
        raise ContinuationGuardError(
            "Partial transaction unexpectedly permitted"
        )

    if t2[
        "pre_event_count"
    ] != EXPECTED_PRE_EVENT_COUNT:
        raise ContinuationGuardError(
            "Pre-event count changed"
        )

    if t2[
        "post_event_count_if_successful"
    ] != EXPECTED_POST_EVENT_COUNT:
        raise ContinuationGuardError(
            "Post-event count changed"
        )

    if t2[
        "expected_first_event_id"
    ] != EXPECTED_FIRST_EVENT_ID:
        raise ContinuationGuardError(
            "Expected first event ID changed"
        )

    if t2[
        "expected_last_event_id"
    ] != EXPECTED_LAST_EVENT_ID:
        raise ContinuationGuardError(
            "Expected last event ID changed"
        )

    if (
        t2[
            "expected_pre_ledger_sha256"
        ]
        != EXPECTED_PRE_LEDGER_SHA256
    ):
        raise ContinuationGuardError(
            "Expected pre-ledger identity changed"
        )

    if t2[
        "superseding_events_permitted"
    ] is not False:
        raise ContinuationGuardError(
            "Superseding event unexpectedly permitted"
        )

    if t2[
        "positions_12_to_500_authorized"
    ] is not False:
        raise ContinuationGuardError(
            "Positions 12-500 unexpectedly authorised"
        )

    if t2[
        "scientific_decisions_preselected"
    ] is not False:
        raise ContinuationGuardError(
            "Scientific decisions unexpectedly preselected"
        )

    identity = value[
        "target_identity"
    ]

    if identity[
        "entity_count"
    ] != EXPECTED_TARGET_COUNT:
        raise ContinuationGuardError(
            "Target identity count changed"
        )

    if (
        identity[
            "ordered_entity_ids_sha256"
        ]
        != EXPECTED_TARGET_IDS_SHA256
    ):
        raise ContinuationGuardError(
            "Target ordered-ID SHA changed"
        )

    if (
        identity[
            "canonical_membership_rows_sha256"
        ]
        != EXPECTED_TARGET_MEMBERSHIP_SHA256
    ):
        raise ContinuationGuardError(
            "Target membership SHA changed"
        )

    if (
        identity[
            "canonical_baseline_queue_rows_sha256"
        ]
        != EXPECTED_TARGET_BASELINE_SHA256
    ):
        raise ContinuationGuardError(
            "Target baseline SHA changed"
        )

    if (
        identity[
            "canonical_target_identity_sha256"
        ]
        != EXPECTED_TARGET_IDENTITY_SHA256
    ):
        raise ContinuationGuardError(
            "Target combined identity SHA changed"
        )

    if value[
        "live_mutation_permitted_by_this_design"
    ] is not False:
        raise ContinuationGuardError(
            "Design unexpectedly grants live mutation"
        )

    return value


def expected_target_identity(
    design: dict,
) -> dict:
    identity = design[
        "target_identity"
    ]

    return {
        "entity_count":
            identity[
                "entity_count"
            ],

        "ordered_entity_ids_sha256":
            identity[
                "ordered_entity_ids_sha256"
            ],

        "canonical_membership_rows_sha256":
            identity[
                "canonical_membership_rows_sha256"
            ],

        "canonical_baseline_queue_rows_sha256":
            identity[
                "canonical_baseline_queue_rows_sha256"
            ],

        "canonical_target_identity_sha256":
            identity[
                "canonical_target_identity_sha256"
            ],
    }


def reconstruct_target(
    *,
    base_context: dict,
    design: dict,
) -> dict:
    base_guard = base_context[
        "base_guard"
    ]

    membership_fields, membership = read_tsv(
        base_context[
            "execution_root"
        ]
        / "batch_membership.tsv"
    )

    del membership_fields

    queue_fields, queue = read_tsv(
        base_context[
            "queue_path"
        ]
    )

    del queue_fields

    target_membership = sorted(
        [
            row
            for row in membership
            if (
                row[
                    "batch_id"
                ] == BATCH_ID
                and int(
                    row[
                        "position_in_batch"
                    ]
                ) in EXPECTED_TARGET_POSITIONS
            )
        ],
        key=lambda row:
            int(
                row[
                    "position_in_batch"
                ]
            ),
    )

    if len(
        target_membership
    ) != EXPECTED_TARGET_COUNT:
        raise ContinuationGuardError(
            "Target membership count mismatch"
        )

    if [
        int(
            row[
                "position_in_batch"
            ]
        )
        for row in target_membership
    ] != EXPECTED_TARGET_POSITIONS:
        raise ContinuationGuardError(
            "Target membership ordering changed"
        )

    if [
        int(
            row[
                "global_active_index"
            ]
        )
        for row in target_membership
    ] != EXPECTED_TARGET_POSITIONS:
        raise ContinuationGuardError(
            "Target global active indices changed"
        )

    target_ids = [
        row[
            "screening_entity_id"
        ]
        for row in target_membership
    ]

    if len(
        set(
            target_ids
        )
    ) != EXPECTED_TARGET_COUNT:
        raise ContinuationGuardError(
            "Duplicate target entity"
        )

    queue_by_id = {
        row[
            "screening_entity_id"
        ]:
            row
        for row in queue
    }

    target_queue = []

    target_identity = []

    for membership_row in target_membership:
        entity_id = membership_row[
            "screening_entity_id"
        ]

        if entity_id not in queue_by_id:
            raise ContinuationGuardError(
                "Target missing from baseline queue"
            )

        qrow = queue_by_id[
            entity_id
        ]

        if qrow[
            "screening_state"
        ] != "ready":
            raise ContinuationGuardError(
                "Target entity not frozen baseline-ready"
            )

        target_queue.append(
            qrow
        )

        target_identity.append({
            "position_in_batch":
                int(
                    membership_row[
                        "position_in_batch"
                    ]
                ),

            "global_active_index":
                int(
                    membership_row[
                        "global_active_index"
                    ]
                ),

            "screening_entity_id":
                entity_id,

            "baseline_row_sha256":
                membership_row[
                    "baseline_row_sha256"
                ],

            "title_or_software_name":
                qrow[
                    "title_or_software_name"
                ],

            "year":
                qrow[
                    "year"
                ],

            "doi":
                qrow[
                    "doi"
                ],

            "pmid":
                qrow[
                    "pmid"
                ],
        })

    if canonical_sha(
        target_ids
    ) != EXPECTED_TARGET_IDS_SHA256:
        raise ContinuationGuardError(
            "Independent target ordered-ID SHA mismatch"
        )

    if canonical_sha(
        target_membership
    ) != EXPECTED_TARGET_MEMBERSHIP_SHA256:
        raise ContinuationGuardError(
            "Independent target membership SHA mismatch"
        )

    if canonical_sha(
        target_queue
    ) != EXPECTED_TARGET_BASELINE_SHA256:
        raise ContinuationGuardError(
            "Independent target baseline SHA mismatch"
        )

    if canonical_sha(
        target_identity
    ) != EXPECTED_TARGET_IDENTITY_SHA256:
        raise ContinuationGuardError(
            "Independent target combined identity SHA mismatch"
        )

    if target_identity != design[
        "target_identity"
    ][
        "entities"
    ]:
        raise ContinuationGuardError(
            "Target identity rows differ from frozen design"
        )

    return {
        "membership_rows":
            target_membership,

        "entity_ids":
            target_ids,

        "queue_rows":
            target_queue,

        "identity_rows":
            target_identity,

        "queue_by_id":
            queue_by_id,
    }


def load_context(
    *,
    queue_path: Path = DEFAULT_QUEUE,
    execution_root: Path = EXECUTION_ROOT,
) -> dict:
    base_guard = load_base_guard()

    design = load_design()

    base_context = (
        base_guard.load_guard_context(
            queue_path=
                queue_path,

            execution_root=
                execution_root,
        )
    )

    context = {
        "base_guard":
            base_guard,

        "design":
            design,

        "appender":
            base_context[
                "appender"
            ],

        "appender_context":
            base_context[
                "appender_context"
            ],

        "base_context":
            base_context,

        "queue_path":
            queue_path,

        "execution_root":
            execution_root,
    }

    context[
        "target"
    ] = reconstruct_target(
        base_context=
            context,

        design=
            design,
    )

    return context


def blank_reference_rows(
    context: dict,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    base_guard = context[
        "base_guard"
    ]

    payload = (
        base_guard.build_review_packet_bytes(
            scope=
                context[
                    "base_context"
                ][
                    "scope"
                ],

            contract=
                context[
                    "base_context"
                ][
                    "contract"
                ],
        )
    )

    handle = io.StringIO(
        payload.decode(
            "utf-8"
        ),
        newline="",
    )

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


def expected_position1_proposed_values() -> dict[str, str]:
    fields, rows = read_tsv(
        T000001_CHECKPOINT
        / "proposal.tsv"
    )

    del fields

    if len(
        rows
    ) != 1:
        raise ContinuationGuardError(
            "T000001 proposal no longer contains exactly one row"
        )

    proposal = rows[
        0
    ]

    return {
        "proposed_event_type":
            proposal[
                "event_type"
            ],

        "proposed_record_decision":
            proposal[
                "record_decision"
            ],

        "proposed_exclusion_reason_code":
            proposal[
                "exclusion_reason_code"
            ],

        "proposed_candidate_method_flag":
            proposal[
                "candidate_method_flag"
            ],

        "proposed_evidence_basis":
            proposal[
                "evidence_basis"
            ],

        "proposed_evidence_source_locator":
            proposal[
                "evidence_source_locator"
            ],

        "proposed_evidence_escalation_status":
            proposal[
                "evidence_escalation_status"
            ],

        "proposed_notes":
            proposal[
                "notes"
            ],
    }


def validate_review_packet(
    *,
    packet_path: Path,
    context: dict,
    mode: str,
) -> list[dict[str, str]]:
    if mode not in {
        "pre_authorization",
        "transaction_ready",
    }:
        raise ContinuationGuardError(
            "Unknown review-packet validation mode"
        )

    fields, rows = read_tsv(
        packet_path
    )

    reference_fields, reference_rows = (
        blank_reference_rows(
            context
        )
    )

    if fields != reference_fields:
        raise ContinuationGuardError(
            "Review packet schema differs from frozen schema"
        )

    if len(
        rows
    ) != 500:
        raise ContinuationGuardError(
            "Review packet must contain 500 rows"
        )

    if len(
        reference_rows
    ) != 500:
        raise ContinuationGuardError(
            "Frozen reference packet must contain 500 rows"
        )

    immutable_fields = [
        field
        for field in fields
        if field not in PROPOSED_FIELDS
    ]

    base_guard = context[
        "base_guard"
    ]

    for position, (
        row,
        reference,
    ) in enumerate(
        zip(
            rows,
            reference_rows,
        ),
        start=1,
    ):
        base_guard.validate_row_hygiene(
            row
        )

        if int(
            row[
                "position_in_batch"
            ]
        ) != position:
            raise ContinuationGuardError(
                "Review packet position ordering changed"
            )

        for field in immutable_fields:
            if (
                row[
                    field
                ]
                != reference[
                    field
                ]
            ):
                raise ContinuationGuardError(
                    f"Immutable review value changed "
                    f"at position {position}: {field}"
                )

    expected_p1 = (
        expected_position1_proposed_values()
    )

    for field in PROPOSED_FIELDS:
        if (
            rows[
                0
            ][
                field
            ]
            != expected_p1[
                field
            ]
        ):
            raise ContinuationGuardError(
                f"Position 1 T000001 proposal state changed: {field}"
            )

    # Positions 12-500 are always prohibited.
    for position in range(
        12,
        501,
    ):
        row = rows[
            position - 1
        ]

        for field in PROPOSED_FIELDS:
            if row[
                field
            ]:
                raise ContinuationGuardError(
                    "Positions 12-500 must remain proposal-blank"
                )

    # Positions 2-11 are blank before review, or all populated with
    # an event_type when the transaction is ready.
    target_rows = [
        rows[
            position - 1
        ]
        for position in EXPECTED_TARGET_POSITIONS
    ]

    if mode == "pre_authorization":
        for row in target_rows:
            for field in PROPOSED_FIELDS:
                if row[
                    field
                ]:
                    raise ContinuationGuardError(
                        "Positions 2-11 must remain blank "
                        "before T000002 review/authorization workflow"
                    )

    else:
        for position, row in zip(
            EXPECTED_TARGET_POSITIONS,
            target_rows,
        ):
            if not row[
                "proposed_event_type"
            ]:
                raise ContinuationGuardError(
                    f"Position {position} lacks a proposed event"
                )

    target_ids = [
        row[
            "screening_entity_id"
        ]
        for row in target_rows
    ]

    if (
        target_ids
        != context[
            "target"
        ][
            "entity_ids"
        ]
    ):
        raise ContinuationGuardError(
            "Review packet target identity differs from frozen target"
        )

    return rows


def expected_checkpoint_contract() -> dict:
    return {
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
                "T000002"
            ),

        "final_files": [
            "authorization.json",
            "proposal.tsv",
            "receipt.json",
        ],
    }


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
        raise ContinuationGuardError(
            "T000002 authorization schema mismatch"
        )

    return value


def validate_authorization(
    *,
    authorization_path: Path,
    context: dict,
    require_tracked: bool,
) -> dict:
    value = load_authorization(
        authorization_path
    )

    base_guard = context[
        "base_guard"
    ]

    appender = context[
        "appender"
    ]

    if value[
        "status"
    ] != AUTH_STATUS:
        raise ContinuationGuardError(
            "T000002 authorization status invalid"
        )

    if value[
        "schema_version"
    ] != 1:
        raise ContinuationGuardError(
            "T000002 authorization schema version invalid"
        )

    if not COMMIT_RE.fullmatch(
        value[
            "parent_commit"
        ]
    ):
        raise ContinuationGuardError(
            "Authorization parent commit malformed"
        )

    if (
        value[
            "post_canary_continuation_design_freeze_sha256"
        ]
        != sha256_file(
            CONTINUATION_DESIGN_SUMS
        )
    ):
        raise ContinuationGuardError(
            "Continuation-design freeze SHA mismatch"
        )

    if (
        value[
            "t000001_completion_freeze_sha256"
        ]
        != sha256_file(
            T000001_COMPLETION_SUMS
        )
    ):
        raise ContinuationGuardError(
            "T000001 completion-freeze SHA mismatch"
        )

    if (
        value[
            "event_appender_implementation_sha256"
        ]
        != base_guard.EXPECTED_APPENDER_SHA256
    ):
        raise ContinuationGuardError(
            "Frozen appender source SHA mismatch"
        )

    if (
        value[
            "event_appender_implementation_freeze_sha256"
        ]
        != sha256_file(
            base_guard.APPENDER_FREEZE_SUMS
        )
    ):
        raise ContinuationGuardError(
            "Frozen appender freeze SHA mismatch"
        )

    if (
        value[
            "event_entry_design_freeze_sha256"
        ]
        != sha256_file(
            base_guard.EVENT_ENTRY_DESIGN_SUMS
        )
    ):
        raise ContinuationGuardError(
            "Event-entry design freeze SHA mismatch"
        )

    if (
        value[
            "target_identity"
        ]
        != expected_target_identity(
            context[
                "design"
            ]
        )
    ):
        raise ContinuationGuardError(
            "Authorization target identity mismatch"
        )

    if value[
        "batch_id"
    ] != BATCH_ID:
        raise ContinuationGuardError(
            "Authorization batch mismatch"
        )

    if value[
        "authorized_positions"
    ] != EXPECTED_TARGET_POSITIONS:
        raise ContinuationGuardError(
            "Authorization position scope mismatch"
        )

    if (
        value[
            "expected_pre_ledger_sha256"
        ]
        != EXPECTED_PRE_LEDGER_SHA256
    ):
        raise ContinuationGuardError(
            "Authorization pre-ledger SHA mismatch"
        )

    if (
        value[
            "expected_pre_event_count"
        ]
        != EXPECTED_PRE_EVENT_COUNT
    ):
        raise ContinuationGuardError(
            "Authorization pre-event count mismatch"
        )

    if (
        value[
            "max_live_event_count"
        ]
        != EXPECTED_TARGET_COUNT
    ):
        raise ContinuationGuardError(
            "Authorization event count must equal 10"
        )

    if (
        value[
            "expected_first_event_id"
        ]
        != EXPECTED_FIRST_EVENT_ID
    ):
        raise ContinuationGuardError(
            "Authorization first event ID mismatch"
        )

    if (
        value[
            "expected_last_event_id"
        ]
        != EXPECTED_LAST_EVENT_ID
    ):
        raise ContinuationGuardError(
            "Authorization last event ID mismatch"
        )

    if not value[
        "operator_id"
    ].strip():
        raise ContinuationGuardError(
            "Authorization operator_id empty"
        )

    base_guard.validate_field_hygiene(
        value[
            "operator_id"
        ],
        field_name="operator_id",
    )

    if (
        value[
            "operator_type"
        ]
        not in set(
            appender.load_base_engine().OPERATOR_TYPES
        )
    ):
        raise ContinuationGuardError(
            "Authorization operator_type invalid"
        )

    if value[
        "permitted_initial_event_types"
    ] != [
        "record_decision",
        "source_escalation",
    ]:
        raise ContinuationGuardError(
            "Authorization event-type scope changed"
        )

    if (
        value[
            "receipt_checkpoint_contract"
        ]
        != expected_checkpoint_contract()
    ):
        raise ContinuationGuardError(
            "Authorization checkpoint contract mismatch"
        )

    if value[
        "positions_12_to_500_authorized"
    ] is not False:
        raise ContinuationGuardError(
            "Authorization illegally enables positions 12-500"
        )

    if value[
        "partial_transaction_permitted"
    ] is not False:
        raise ContinuationGuardError(
            "Authorization illegally permits partial T000002"
        )

    if value[
        "one_use"
    ] is not True:
        raise ContinuationGuardError(
            "T000002 authorization must be one-use"
        )

    if value[
        "scientific_decisions_preselected"
    ] is not False:
        raise ContinuationGuardError(
            "Authorization must not preselect scientific decisions"
        )

    if require_tracked:
        authorization_commit = (
            base_guard.ensure_tracked_authorization(
                authorization_path,
                value,
            )
        )

    else:
        authorization_commit = (
            "UNTRACKED_TEST_AUTHORIZATION"
        )

    return {
        "authorization":
            value,

        "authorization_sha256":
            sha256_file(
                authorization_path
            ),

        "authorization_commit":
            authorization_commit,
    }


def extract_proposal_bytes(
    *,
    packet_path: Path,
    authorization: dict,
    context: dict,
) -> bytes:
    rows = validate_review_packet(
        packet_path=
            packet_path,

        context=
            context,

        mode=
            "transaction_ready",
    )

    appender = context[
        "appender"
    ]

    proposals = []

    for position in EXPECTED_TARGET_POSITIONS:
        row = rows[
            position - 1
        ]

        proposal = {
            "screening_entity_id":
                row[
                    "screening_entity_id"
                ],

            "batch_id":
                BATCH_ID,

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

        for review_field, proposal_field in (
            PROPOSAL_MAPPING.items()
        ):
            proposal[
                proposal_field
            ] = row[
                review_field
            ]

        context[
            "base_guard"
        ].validate_row_hygiene(
            proposal
        )

        proposals.append(
            proposal
        )

    if len(
        proposals
    ) != EXPECTED_TARGET_COUNT:
        raise ContinuationGuardError(
            "T000002 proposal must contain exactly ten rows"
        )

    if [
        proposal[
            "screening_entity_id"
        ]
        for proposal in proposals
    ] != context[
        "target"
    ][
        "entity_ids"
    ]:
        raise ContinuationGuardError(
            "Proposal target order differs from frozen T000002 order"
        )

    return tsv_bytes(
        fields=
            list(
                appender.PROPOSAL_FIELDS
            ),

        rows=
            proposals,
    )


def validate_pre_transaction_state(
    *,
    ledger_path: Path,
    context: dict,
) -> dict:
    validation = (
        context[
            "appender"
        ].validate_current_ledger(
            ledger_path=
                ledger_path,

            context=
                context[
                    "appender_context"
                ],
        )
    )

    if validation[
        "event_count"
    ] != EXPECTED_PRE_EVENT_COUNT:
        raise ContinuationGuardError(
            "T000002 requires exactly one pre-existing event"
        )

    if (
        validation[
            "ledger_sha256"
        ]
        != EXPECTED_PRE_LEDGER_SHA256
    ):
        raise ContinuationGuardError(
            "T000002 expected pre-ledger SHA mismatch"
        )

    if validation[
        "derived_state_counts"
    ] != {
        "awaiting_source_escalation": 0,
        "blocked_metadata": 484,
        "complete": 1,
        "ready": 94621,
    }:
        raise ContinuationGuardError(
            "T000002 expected pre-state counts changed"
        )

    return validation


def detect_recovery_state(
    *,
    ledger_path: Path,
    receipt_root: Path,
) -> dict:
    if not (
        receipt_root
        / "T000001"
    ).is_dir():
        raise ContinuationGuardError(
            "T000001 checkpoint missing"
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
                for path in receipt_root.iterdir()
                if (
                    path.is_dir()
                    and path.name.startswith(
                        ".T000002.tmp."
                    )
                )
            ]
        )

    ledger_sha = sha256_file(
        ledger_path
    )

    if final_dir.exists():
        return {
            "status":
                "FINAL_CHECKPOINT_EXISTS",

            "ledger_sha256":
                ledger_sha,

            "temporary_checkpoint_count":
                len(
                    temp_dirs
                ),
        }

    if ledger_sha != EXPECTED_PRE_LEDGER_SHA256:
        return {
            "status":
                "RECOVERY_REQUIRED",

            "ledger_sha256":
                ledger_sha,

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

            "temporary_checkpoint_count":
                len(
                    temp_dirs
                ),
        }

    return {
        "status":
            "PRE_T000002_READY",

        "ledger_sha256":
            ledger_sha,

        "temporary_checkpoint_count":
            0,
    }


def prepare_transaction(
    *,
    authorization_path: Path,
    packet_path: Path,
    ledger_path: Path,
    context: dict,
    require_tracked_authorization: bool,
    transaction_timestamp_utc: str | None = None,
) -> dict:
    validate_pre_transaction_state(
        ledger_path=
            ledger_path,

        context=
            context,
    )

    authorization_info = (
        validate_authorization(
            authorization_path=
                authorization_path,

            context=
                context,

            require_tracked=
                require_tracked_authorization,
        )
    )

    authorization = (
        authorization_info[
            "authorization"
        ]
    )

    proposal_bytes = (
        extract_proposal_bytes(
            packet_path=
                packet_path,

            authorization=
                authorization,

            context=
                context,
        )
    )

    proposal_sha = sha256_bytes(
        proposal_bytes
    )

    with tempfile.TemporaryDirectory(
        prefix="branchsnv-exp07-t000002-dryrun-"
    ) as tmp:
        proposal_path = (
            Path(tmp)
            / "proposal.tsv"
        )

        proposal_path.write_bytes(
            proposal_bytes
        )

        prepared = (
            context[
                "appender"
            ].prepare_transaction_from_files(
                ledger_path=
                    ledger_path,

                proposal_path=
                    proposal_path,

                expected_pre_ledger_sha256=
                    EXPECTED_PRE_LEDGER_SHA256,

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
    ] != BATCH_ID:
        raise ContinuationGuardError(
            "Prepared T000002 batch changed"
        )

    if receipt[
        "new_event_count"
    ] != EXPECTED_TARGET_COUNT:
        raise ContinuationGuardError(
            "Prepared T000002 must contain ten events"
        )

    if receipt[
        "pre_append_event_count"
    ] != EXPECTED_PRE_EVENT_COUNT:
        raise ContinuationGuardError(
            "Prepared pre-event count changed"
        )

    if receipt[
        "post_append_event_count"
    ] != EXPECTED_POST_EVENT_COUNT:
        raise ContinuationGuardError(
            "Prepared post-event count changed"
        )

    if receipt[
        "first_assigned_event_id"
    ] != EXPECTED_FIRST_EVENT_ID:
        raise ContinuationGuardError(
            "Prepared first event ID mismatch"
        )

    if receipt[
        "last_assigned_event_id"
    ] != EXPECTED_LAST_EVENT_ID:
        raise ContinuationGuardError(
            "Prepared last event ID mismatch"
        )

    if receipt[
        "published"
    ] is not False:
        raise ContinuationGuardError(
            "Dry-run T000002 unexpectedly published"
        )

    if receipt[
        "strict_prefix_extension"
    ] is not True:
        raise ContinuationGuardError(
            "T000002 is not a strict ledger-prefix extension"
        )

    if receipt[
        "review_fields_blank"
    ] is not True:
        raise ContinuationGuardError(
            "Appender-managed review fields unexpectedly populated"
        )

    return {
        "status":
            "T000002_DRY_RUN_VALID",

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


def validate_checkpoint(
    *,
    checkpoint_dir: Path,
    ledger_path: Path,
) -> dict:
    if not checkpoint_dir.is_dir():
        raise ContinuationGuardError(
            "T000002 checkpoint directory missing"
        )

    children = list(
        checkpoint_dir.iterdir()
    )

    if any(
        path.is_symlink()
        for path in children
    ):
        raise ContinuationGuardError(
            "T000002 checkpoint contains symlink"
        )

    if any(
        not path.is_file()
        for path in children
    ):
        raise ContinuationGuardError(
            "T000002 checkpoint contains non-file artifact"
        )

    names = {
        path.name
        for path in children
    }

    if names != {
        "authorization.json",
        "proposal.tsv",
        "receipt.json",
    }:
        raise ContinuationGuardError(
            "T000002 checkpoint artifact set mismatch"
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
        raise ContinuationGuardError(
            "Checkpoint transaction ID mismatch"
        )

    if receipt[
        "proposal_sha256"
    ] != sha256_file(
        checkpoint_dir
        / "proposal.tsv"
    ):
        raise ContinuationGuardError(
            "Checkpoint proposal SHA mismatch"
        )

    if receipt[
        "authorization_json_sha256"
    ] != sha256_file(
        checkpoint_dir
        / "authorization.json"
    ):
        raise ContinuationGuardError(
            "Checkpoint authorization SHA mismatch"
        )

    if receipt[
        "validated_post_append_ledger_sha256"
    ] != sha256_file(
        ledger_path
    ):
        raise ContinuationGuardError(
            "Checkpoint post-ledger SHA mismatch"
        )

    if receipt[
        "pre_append_event_count"
    ] != EXPECTED_PRE_EVENT_COUNT:
        raise ContinuationGuardError(
            "Checkpoint pre-event count mismatch"
        )

    if receipt[
        "post_append_event_count"
    ] != EXPECTED_POST_EVENT_COUNT:
        raise ContinuationGuardError(
            "Checkpoint post-event count mismatch"
        )

    if receipt[
        "new_event_count"
    ] != EXPECTED_TARGET_COUNT:
        raise ContinuationGuardError(
            "Checkpoint new-event count mismatch"
        )

    if receipt[
        "first_assigned_event_id"
    ] != EXPECTED_FIRST_EVENT_ID:
        raise ContinuationGuardError(
            "Checkpoint first event ID mismatch"
        )

    if receipt[
        "last_assigned_event_id"
    ] != EXPECTED_LAST_EVENT_ID:
        raise ContinuationGuardError(
            "Checkpoint last event ID mismatch"
        )

    if receipt[
        "published"
    ] is not True:
        raise ContinuationGuardError(
            "Checkpoint not marked published"
        )

    if receipt[
        "post_publication_validation_passed"
    ] is not True:
        raise ContinuationGuardError(
            "Post-publication validation not recorded"
        )

    if receipt[
        "checkpoint_status"
    ] != "COMPLETE":
        raise ContinuationGuardError(
            "Checkpoint status not COMPLETE"
        )

    return {
        "status":
            "T000002_CHECKPOINT_VALID",

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

        "new_event_count":
            receipt[
                "new_event_count"
            ],
    }


def execute_transaction(
    *,
    authorization_path: Path,
    packet_path: Path,
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
            raise ContinuationGuardError(
                "Real production ledger requires canonical receipt root"
            )

        if not require_tracked_authorization:
            raise ContinuationGuardError(
                "Real production requires tracked T000002 authorization"
            )

    recovery = detect_recovery_state(
        ledger_path=
            ledger_path,

        receipt_root=
            receipt_root,
    )

    if recovery[
        "status"
    ] != "PRE_T000002_READY":
        raise RecoveryRequiredError(
            "T000002 cannot execute from state: "
            + recovery[
                "status"
            ]
        )

    prepared = prepare_transaction(
        authorization_path=
            authorization_path,

        packet_path=
            packet_path,

        ledger_path=
            ledger_path,

        context=
            context,

        require_tracked_authorization=
            require_tracked_authorization,

        transaction_timestamp_utc=
            transaction_timestamp_utc,
    )

    if sha256_file(
        ledger_path
    ) != EXPECTED_PRE_LEDGER_SHA256:
        raise ContinuationGuardError(
            "Ledger changed after T000002 preparation"
        )

    final_dir = (
        receipt_root
        / TRANSACTION_ID
    )

    if final_dir.exists():
        raise RecoveryRequiredError(
            "T000002 final checkpoint already exists"
        )

    temp_dir = Path(
        tempfile.mkdtemp(
            prefix=".T000002.tmp.",
            dir=receipt_root,
        )
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
        ) != EXPECTED_PRE_LEDGER_SHA256:
            raise ContinuationGuardError(
                "Ledger changed immediately before T000002 publication"
            )

        receipt = (
            context[
                "appender"
            ].append_transaction_atomic(
                ledger_path=
                    ledger_path,

                proposal_path=
                    proposal_copy,

                expected_pre_ledger_sha256=
                    EXPECTED_PRE_LEDGER_SHA256,

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
                "SYNTHETIC_T000002_FAILURE_AFTER_LEDGER_APPEND"
            )

        post_validation = (
            context[
                "appender"
            ].validate_current_ledger(
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
        ] != EXPECTED_POST_EVENT_COUNT:
            raise ContinuationGuardError(
                "Post-T000002 ledger event count must equal 11"
            )

        receipt = dict(
            receipt
        )

        receipt.update({
            "transaction_id":
                TRANSACTION_ID,

            "target_positions":
                EXPECTED_TARGET_POSITIONS,

            "target_identity":
                expected_target_identity(
                    context[
                        "design"
                    ]
                ),

            "authorization_commit":
                prepared[
                    "authorization_commit"
                ],

            "authorization_json_sha256":
                prepared[
                    "authorization_sha256"
                ],

            "post_canary_continuation_design_freeze_sha256":
                sha256_file(
                    CONTINUATION_DESIGN_SUMS
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
            raise ContinuationGuardError(
                "Final T000002 checkpoint unexpectedly appeared"
            )

        os.replace(
            temp_dir,
            final_dir,
        )

        fsync_directory(
            receipt_root
        )

        checkpoint = validate_checkpoint(
            checkpoint_dir=
                final_dir,

            ledger_path=
                ledger_path,
        )

        return {
            "status":
                "T000002_EXECUTION_COMPLETE",

            "transaction_id":
                TRANSACTION_ID,

            "checkpoint":
                checkpoint,

            "receipt":
                receipt,
        }

    except Exception as exc:
        current_sha = sha256_file(
            ledger_path
        )

        if (
            appended
            or current_sha != EXPECTED_PRE_LEDGER_SHA256
        ):
            raise RecoveryRequiredError(
                "Ledger changed but T000002 checkpoint did not "
                "finalize; preserve staged checkpoint and enter "
                "recovery workflow"
            ) from exc

        if temp_dir.exists():
            shutil.rmtree(
                temp_dir
            )

        raise


def describe_state(
    *,
    packet_path: Path,
    ledger_path: Path,
    receipt_root: Path,
    context: dict,
) -> dict:
    validate_pre_transaction_state(
        ledger_path=
            ledger_path,

        context=
            context,
    )

    rows = validate_review_packet(
        packet_path=
            packet_path,

        context=
            context,

        mode=
            "pre_authorization",
    )

    recovery = detect_recovery_state(
        ledger_path=
            ledger_path,

        receipt_root=
            receipt_root,
    )

    target = context[
        "target"
    ]

    return {
        "status":
            "T000002_GUARD_READY_PRE_AUTHORIZATION",

        "transaction_id":
            TRANSACTION_ID,

        "batch_id":
            BATCH_ID,

        "target_positions":
            EXPECTED_TARGET_POSITIONS,

        "target_event_count":
            EXPECTED_TARGET_COUNT,

        "target_entity_ids":
            target[
                "entity_ids"
            ],

        "target_ordered_entity_ids_sha256":
            EXPECTED_TARGET_IDS_SHA256,

        "target_membership_sha256":
            EXPECTED_TARGET_MEMBERSHIP_SHA256,

        "target_baseline_sha256":
            EXPECTED_TARGET_BASELINE_SHA256,

        "target_identity_sha256":
            EXPECTED_TARGET_IDENTITY_SHA256,

        "expected_first_event_id":
            EXPECTED_FIRST_EVENT_ID,

        "expected_last_event_id":
            EXPECTED_LAST_EVENT_ID,

        "pre_event_count":
            EXPECTED_PRE_EVENT_COUNT,

        "expected_post_event_count":
            EXPECTED_POST_EVENT_COUNT,

        "ledger_sha256":
            sha256_file(
                ledger_path
            ),

        "review_packet_sha256":
            sha256_file(
                packet_path
            ),

        "review_packet_bytes":
            packet_path.stat().st_size,

        "position_1_locked":
            True,

        "positions_2_to_11_blank":
            all(
                not row[
                    field
                ]
                for row in rows[
                    1:
                    11
                ]
                for field in PROPOSED_FIELDS
            ),

        "positions_12_to_500_blank":
            all(
                not row[
                    field
                ]
                for row in rows[
                    11:
                ]
                for field in PROPOSED_FIELDS
            ),

        "checkpoint_state":
            recovery[
                "status"
            ],

        "authorization_created_by_guard":
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
        "--review-packet",
        type=Path,
        default=DEFAULT_REVIEW_PACKET,
    )

    parser.add_argument(
        "--authorization-json",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if (
        args.dry_run
        and args.execute
    ):
        raise ContinuationGuardError(
            "Choose only one T000002 action"
        )

    context = load_context(
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

    packet_path = (
        args.review_packet.resolve()
    )

    if (
        args.dry_run
        or args.execute
    ):
        if args.authorization_json is None:
            raise ContinuationGuardError(
                "T000002 action requires authorization JSON"
            )

        if args.execute:
            result = execute_transaction(
                authorization_path=
                    args.authorization_json.resolve(),

                packet_path=
                    packet_path,

                ledger_path=
                    ledger_path,

                receipt_root=
                    receipt_root,

                context=
                    context,

                require_tracked_authorization=True,
            )

        else:
            prepared = prepare_transaction(
                authorization_path=
                    args.authorization_json.resolve(),

                packet_path=
                    packet_path,

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
            packet_path=
                packet_path,

            ledger_path=
                ledger_path,

            receipt_root=
                receipt_root,

            context=
                context,
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
