#!/usr/bin/env python3

from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile


HERE = Path(__file__).resolve().parent

MODULE_PATH = (
    HERE
    / "b000001_t000002_continuation_guard.py"
)

spec = importlib.util.spec_from_file_location(
    "b000001_t000002_continuation_guard_tests",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

guard = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = guard

spec.loader.exec_module(
    guard
)

context = guard.load_context()

appender = context[
    "appender"
]


def expect_error(
    label,
    fn,
):
    try:
        fn()

    except (
        guard.ContinuationGuardError,
        guard.RecoveryRequiredError,
        context[
            "base_guard"
        ].GuardError,
        appender.EventAppenderError,
    ):
        print(
            "PASS |",
            label,
        )

        return

    raise AssertionError(
        "Expected fail-closed error: "
        + label
    )


def read_tsv(
    path,
):
    with Path(path).open(
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


def write_tsv(
    path,
    fields,
    rows,
):
    with Path(path).open(
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


design = context[
    "design"
]

target = context[
    "target"
]


assert design[
    "t000002"
][
    "target_positions"
] == list(
    range(
        2,
        12,
    )
)

assert design[
    "t000002"
][
    "target_event_count"
] == 10

assert target[
    "entity_ids"
] == [
    item[
        "screening_entity_id"
    ]
    for item in design[
        "target_identity"
    ][
        "entities"
    ]
]

assert guard.canonical_sha(
    target[
        "entity_ids"
    ]
) == guard.EXPECTED_TARGET_IDS_SHA256

assert guard.canonical_sha(
    target[
        "membership_rows"
    ]
) == guard.EXPECTED_TARGET_MEMBERSHIP_SHA256

assert guard.canonical_sha(
    target[
        "queue_rows"
    ]
) == guard.EXPECTED_TARGET_BASELINE_SHA256

assert guard.canonical_sha(
    target[
        "identity_rows"
    ]
) == guard.EXPECTED_TARGET_IDENTITY_SHA256

print(
    "PASS | exact frozen T000002 target reconstructed"
)

print(
    "PASS | exact target identity hashes reproduced"
)


real_ledger_before = (
    guard.DEFAULT_LEDGER.read_bytes()
)

real_packet_before = (
    guard.DEFAULT_REVIEW_PACKET.read_bytes()
)

assert hashlib.sha256(
    real_ledger_before
).hexdigest() == guard.EXPECTED_PRE_LEDGER_SHA256

assert hashlib.sha256(
    real_packet_before
).hexdigest() == guard.EXPECTED_PRE_REVIEW_PACKET_SHA256


pre_rows = guard.validate_review_packet(
    packet_path=
        guard.DEFAULT_REVIEW_PACKET,

    context=
        context,

    mode=
        "pre_authorization",
)

assert len(
    pre_rows
) == 500

assert all(
    not row[
        field
    ]
    for row in pre_rows[
        1:
        11
    ]
    for field in guard.PROPOSED_FIELDS
)

assert all(
    not row[
        field
    ]
    for row in pre_rows[
        11:
    ]
    for field in guard.PROPOSED_FIELDS
)

print(
    "PASS | real pre-T000002 review packet valid"
)

print(
    "PASS | position 1 locked to T000001 state"
)

print(
    "PASS | positions 2-500 remain proposal-blank"
)


def synthetic_authorization():
    base_guard = context[
        "base_guard"
    ]

    return {
        "status":
            guard.AUTH_STATUS,

        "schema_version":
            1,

        "parent_commit":
            "0" * 40,

        "post_canary_continuation_design_freeze_sha256":
            guard.sha256_file(
                guard.CONTINUATION_DESIGN_SUMS
            ),

        "t000001_completion_freeze_sha256":
            guard.sha256_file(
                guard.T000001_COMPLETION_SUMS
            ),

        "event_appender_implementation_sha256":
            base_guard.EXPECTED_APPENDER_SHA256,

        "event_appender_implementation_freeze_sha256":
            guard.sha256_file(
                base_guard.APPENDER_FREEZE_SUMS
            ),

        "event_entry_design_freeze_sha256":
            guard.sha256_file(
                base_guard.EVENT_ENTRY_DESIGN_SUMS
            ),

        "target_identity":
            guard.expected_target_identity(
                design
            ),

        "batch_id":
            "B000001",

        "authorized_positions":
            list(
                range(
                    2,
                    12,
                )
            ),

        "expected_pre_ledger_sha256":
            guard.EXPECTED_PRE_LEDGER_SHA256,

        "expected_pre_event_count":
            1,

        "max_live_event_count":
            10,

        "expected_first_event_id":
            "E000000002",

        "expected_last_event_id":
            "E000000011",

        "operator_id":
            "synthetic-test-human",

        "operator_type":
            "human",

        "permitted_initial_event_types": [
            "record_decision",
            "source_escalation",
        ],

        "receipt_checkpoint_contract":
            guard.expected_checkpoint_contract(),

        "positions_12_to_500_authorized":
            False,

        "partial_transaction_permitted":
            False,

        "one_use":
            True,

        "scientific_decisions_preselected":
            False,
    }


with tempfile.TemporaryDirectory(
    prefix="branchsnv-exp07-t000002-tests-"
) as tmp:
    root = Path(
        tmp
    )

    packet_path = (
        root
        / "review.tsv"
    )

    packet_path.write_bytes(
        real_packet_before
    )

    fields, rows = read_tsv(
        packet_path
    )

    # Populate positions 2-11 with synthetic source-escalation events.
    # No terminal scientific conclusion is manufactured by the test.
    for position in range(
        2,
        12,
    ):
        row = rows[
            position - 1
        ]

        row[
            "proposed_event_type"
        ] = "source_escalation"

        row[
            "proposed_record_decision"
        ] = ""

        row[
            "proposed_exclusion_reason_code"
        ] = ""

        row[
            "proposed_candidate_method_flag"
        ] = ""

        row[
            "proposed_evidence_basis"
        ] = (
            f"SYNTHETIC_TEST_ONLY position {position}: "
            "additional authoritative source review required."
        )

        row[
            "proposed_evidence_source_locator"
        ] = ""

        row[
            "proposed_evidence_escalation_status"
        ] = "awaiting_source_escalation"

        row[
            "proposed_notes"
        ] = "synthetic temporary-ledger test only"

    write_tsv(
        packet_path,
        fields,
        rows,
    )

    validated_rows = (
        guard.validate_review_packet(
            packet_path=
                packet_path,

            context=
                context,

            mode=
                "transaction_ready",
        )
    )

    assert len(
        validated_rows
    ) == 500

    print(
        "PASS | synthetic ten-record transaction-ready packet valid"
    )

    print(
        "PASS | positions 2-11 may carry proposals"
    )

    print(
        "PASS | positions 12-500 remain blank"
    )


    authorization = (
        synthetic_authorization()
    )

    authorization_path = (
        root
        / "authorization.json"
    )

    authorization_path.write_bytes(
        guard.pretty_json_bytes(
            authorization
        )
    )

    validated_auth = (
        guard.validate_authorization(
            authorization_path=
                authorization_path,

            context=
                context,

            require_tracked=False,
        )
    )

    assert validated_auth[
        "authorization_commit"
    ] == "UNTRACKED_TEST_AUTHORIZATION"

    print(
        "PASS | synthetic T000002 authorization accepted for temporary tests"
    )


    prepared = guard.prepare_transaction(
        authorization_path=
            authorization_path,

        packet_path=
            packet_path,

        ledger_path=
            guard.DEFAULT_LEDGER,

        context=
            context,

        require_tracked_authorization=False,

        transaction_timestamp_utc=
            "2026-09-25T08:00:00Z",
    )

    receipt = prepared[
        "prepared_receipt"
    ]

    assert prepared[
        "status"
    ] == "T000002_DRY_RUN_VALID"

    assert receipt[
        "new_event_count"
    ] == 10

    assert receipt[
        "pre_append_event_count"
    ] == 1

    assert receipt[
        "post_append_event_count"
    ] == 11

    assert receipt[
        "first_assigned_event_id"
    ] == "E000000002"

    assert receipt[
        "last_assigned_event_id"
    ] == "E000000011"

    assert receipt[
        "event_type_counts"
    ] == {
        "source_escalation": 10,
    }

    assert receipt[
        "derived_state_counts_after_append"
    ] == {
        "awaiting_source_escalation": 10,
        "blocked_metadata": 484,
        "complete": 1,
        "ready": 94611,
    }

    assert receipt[
        "published"
    ] is False

    assert (
        guard.DEFAULT_LEDGER.read_bytes()
        == real_ledger_before
    )

    print(
        "PASS | ten-event dry run assigns E000000002-E000000011"
    )

    print(
        "PASS | multi-event state transition validated"
    )

    print(
        "PASS | dry run does not mutate real production"
    )

    print(
        "INFO | synthetic T000002 proposal SHA256 =",
        prepared[
            "proposal_sha256"
        ],
    )


    # One target cannot be omitted.
    _, missing_rows = read_tsv(
        packet_path
    )

    for field in guard.PROPOSED_FIELDS:
        missing_rows[
            10
        ][
            field
        ] = ""

    missing_path = (
        root
        / "missing-position11.tsv"
    )

    write_tsv(
        missing_path,
        fields,
        missing_rows,
    )

    expect_error(
        "partial T000002 transaction prohibited",
        lambda:
            guard.prepare_transaction(
                authorization_path=
                    authorization_path,

                packet_path=
                    missing_path,

                ledger_path=
                    guard.DEFAULT_LEDGER,

                context=
                    context,

                require_tracked_authorization=False,

                transaction_timestamp_utc=
                    "2026-09-25T08:01:00Z",
            ),
    )


    # Position 12 cannot receive proposed input.
    _, bad_rows = read_tsv(
        packet_path
    )

    bad_rows[
        11
    ][
        "proposed_event_type"
    ] = "source_escalation"

    bad_rows[
        11
    ][
        "proposed_evidence_basis"
    ] = "SYNTHETIC TEST"

    bad_rows[
        11
    ][
        "proposed_evidence_escalation_status"
    ] = "awaiting_source_escalation"

    bad_position12 = (
        root
        / "bad-position12.tsv"
    )

    write_tsv(
        bad_position12,
        fields,
        bad_rows,
    )

    expect_error(
        "position 12 proposal prohibited",
        lambda:
            guard.prepare_transaction(
                authorization_path=
                    authorization_path,

                packet_path=
                    bad_position12,

                ledger_path=
                    guard.DEFAULT_LEDGER,

                context=
                    context,

                require_tracked_authorization=False,

                transaction_timestamp_utc=
                    "2026-09-25T08:02:00Z",
            ),
    )


    # Position 1 may not be changed.
    _, bad_rows = read_tsv(
        packet_path
    )

    bad_rows[
        0
    ][
        "proposed_notes"
    ] += " TAMPER"

    bad_position1 = (
        root
        / "bad-position1.tsv"
    )

    write_tsv(
        bad_position1,
        fields,
        bad_rows,
    )

    expect_error(
        "position 1 T000001 review state immutable",
        lambda:
            guard.prepare_transaction(
                authorization_path=
                    authorization_path,

                packet_path=
                    bad_position1,

                ledger_path=
                    guard.DEFAULT_LEDGER,

                context=
                    context,

                require_tracked_authorization=False,

                transaction_timestamp_utc=
                    "2026-09-25T08:03:00Z",
            ),
    )


    bad_auth = dict(
        authorization
    )

    bad_auth[
        "max_live_event_count"
    ] = 9

    bad_auth_path = (
        root
        / "bad-auth-event-count.json"
    )

    bad_auth_path.write_bytes(
        guard.pretty_json_bytes(
            bad_auth
        )
    )

    expect_error(
        "authorization cannot permit fewer than ten events",
        lambda:
            guard.validate_authorization(
                authorization_path=
                    bad_auth_path,

                context=
                    context,

                require_tracked=False,
            ),
    )


    bad_auth = dict(
        authorization
    )

    bad_auth[
        "authorized_positions"
    ] = list(
        range(
            2,
            11,
        )
    )

    bad_auth_path = (
        root
        / "bad-auth-positions.json"
    )

    bad_auth_path.write_bytes(
        guard.pretty_json_bytes(
            bad_auth
        )
    )

    expect_error(
        "authorization must pin exactly positions 2-11",
        lambda:
            guard.validate_authorization(
                authorization_path=
                    bad_auth_path,

                context=
                    context,

                require_tracked=False,
            ),
    )


    bad_auth = dict(
        authorization
    )

    bad_auth[
        "positions_12_to_500_authorized"
    ] = True

    bad_auth_path = (
        root
        / "bad-auth-future-scope.json"
    )

    bad_auth_path.write_bytes(
        guard.pretty_json_bytes(
            bad_auth
        )
    )

    expect_error(
        "authorization cannot enable positions 12-500",
        lambda:
            guard.validate_authorization(
                authorization_path=
                    bad_auth_path,

                context=
                    context,

                require_tracked=False,
            ),
    )


    bad_auth = dict(
        authorization
    )

    bad_auth[
        "partial_transaction_permitted"
    ] = True

    bad_auth_path = (
        root
        / "bad-auth-partial.json"
    )

    bad_auth_path.write_bytes(
        guard.pretty_json_bytes(
            bad_auth
        )
    )

    expect_error(
        "authorization cannot permit partial transaction",
        lambda:
            guard.validate_authorization(
                authorization_path=
                    bad_auth_path,

                context=
                    context,

                require_tracked=False,
            ),
    )


    bad_auth = dict(
        authorization
    )

    bad_auth[
        "operator_id"
    ] = ""

    bad_auth_path = (
        root
        / "bad-auth-operator.json"
    )

    bad_auth_path.write_bytes(
        guard.pretty_json_bytes(
            bad_auth
        )
    )

    expect_error(
        "authorization requires explicit operator identity",
        lambda:
            guard.validate_authorization(
                authorization_path=
                    bad_auth_path,

                context=
                    context,

                require_tracked=False,
            ),
    )


    # Real production must reject untracked synthetic authorization.
    expect_error(
        "real production requires tracked T000002 authorization",
        lambda:
            guard.execute_transaction(
                authorization_path=
                    authorization_path,

                packet_path=
                    packet_path,

                ledger_path=
                    guard.DEFAULT_LEDGER,

                receipt_root=
                    guard.RECEIPT_ROOT,

                context=
                    context,

                require_tracked_authorization=True,

                transaction_timestamp_utc=
                    "2026-09-25T08:04:00Z",
            ),
    )

    assert not guard.T000002_CHECKPOINT.exists()

    assert (
        guard.DEFAULT_LEDGER.read_bytes()
        == real_ledger_before
    )

    print(
        "PASS | untracked authorization cannot mutate real T000002 production"
    )


    # Complete ten-event transaction on temporary copies.
    temp_ledger = (
        root
        / "temp-event-ledger.tsv"
    )

    temp_ledger.write_bytes(
        real_ledger_before
    )

    temp_receipts = (
        root
        / "temp-receipts"
    )

    temp_receipts.mkdir()

    shutil.copytree(
        guard.T000001_CHECKPOINT,
        temp_receipts
        / "T000001",
    )

    executed = guard.execute_transaction(
        authorization_path=
            authorization_path,

        packet_path=
            packet_path,

        ledger_path=
            temp_ledger,

        receipt_root=
            temp_receipts,

        context=
            context,

        require_tracked_authorization=False,

        transaction_timestamp_utc=
            "2026-09-25T08:05:00Z",
    )

    assert executed[
        "status"
    ] == "T000002_EXECUTION_COMPLETE"

    final_checkpoint = (
        temp_receipts
        / "T000002"
    )

    assert final_checkpoint.is_dir()

    assert {
        path.name
        for path in final_checkpoint.iterdir()
    } == {
        "authorization.json",
        "proposal.tsv",
        "receipt.json",
    }

    ledger_validation = (
        appender.validate_current_ledger(
            ledger_path=
                temp_ledger,

            context=
                context[
                    "appender_context"
                ],
        )
    )

    assert ledger_validation[
        "event_count"
    ] == 11

    assert ledger_validation[
        "derived_state_counts"
    ] == {
        "awaiting_source_escalation": 10,
        "blocked_metadata": 484,
        "complete": 1,
        "ready": 94611,
    }

    checkpoint_validation = (
        guard.validate_checkpoint(
            checkpoint_dir=
                final_checkpoint,

            ledger_path=
                temp_ledger,
        )
    )

    assert checkpoint_validation[
        "status"
    ] == "T000002_CHECKPOINT_VALID"

    assert checkpoint_validation[
        "new_event_count"
    ] == 10

    print(
        "PASS | temporary T000002 ten-event execution completes"
    )

    print(
        "PASS | exact three-file T000002 checkpoint created"
    )

    print(
        "PASS | temporary T000002 post-ledger validation passes"
    )


    expect_error(
        "T000002 one-use replay prohibited",
        lambda:
            guard.execute_transaction(
                authorization_path=
                    authorization_path,

                packet_path=
                    packet_path,

                ledger_path=
                    temp_ledger,

                receipt_root=
                    temp_receipts,

                context=
                    context,

                require_tracked_authorization=False,

                transaction_timestamp_utc=
                    "2026-09-25T08:06:00Z",
            ),
    )


    # Recovery simulation after successful append but before checkpoint finish.
    recovery_ledger = (
        root
        / "recovery-ledger.tsv"
    )

    recovery_ledger.write_bytes(
        real_ledger_before
    )

    recovery_receipts = (
        root
        / "recovery-receipts"
    )

    recovery_receipts.mkdir()

    shutil.copytree(
        guard.T000001_CHECKPOINT,
        recovery_receipts
        / "T000001",
    )

    try:
        guard.execute_transaction(
            authorization_path=
                authorization_path,

            packet_path=
                packet_path,

            ledger_path=
                recovery_ledger,

            receipt_root=
                recovery_receipts,

            context=
                context,

            require_tracked_authorization=False,

            transaction_timestamp_utc=
                "2026-09-25T08:07:00Z",

            _test_fail_after_append=True,
        )

    except guard.RecoveryRequiredError:
        pass

    else:
        raise AssertionError(
            "Expected T000002 recovery-required failure"
        )

    recovery_validation = (
        appender.validate_current_ledger(
            ledger_path=
                recovery_ledger,

            context=
                context[
                    "appender_context"
                ],
        )
    )

    assert recovery_validation[
        "event_count"
    ] == 11

    staged = [
        path
        for path in recovery_receipts.iterdir()
        if path.name.startswith(
            ".T000002.tmp."
        )
    ]

    assert len(
        staged
    ) == 1

    assert (
        staged[
            0
        ]
        / "authorization.json"
    ).is_file()

    assert (
        staged[
            0
        ]
        / "proposal.tsv"
    ).is_file()

    recovery_state = (
        guard.detect_recovery_state(
            ledger_path=
                recovery_ledger,

            receipt_root=
                recovery_receipts,
        )
    )

    assert recovery_state[
        "status"
    ] == "RECOVERY_REQUIRED"

    print(
        "PASS | T000002 post-append checkpoint failure enters recovery state"
    )

    print(
        "PASS | staged T000002 recovery evidence preserved"
    )

    expect_error(
        "T000002 recovery state blocks retry",
        lambda:
            guard.execute_transaction(
                authorization_path=
                    authorization_path,

                packet_path=
                    packet_path,

                ledger_path=
                    recovery_ledger,

                receipt_root=
                    recovery_receipts,

                context=
                    context,

                require_tracked_authorization=False,

                transaction_timestamp_utc=
                    "2026-09-25T08:08:00Z",
            ),
    )


assert (
    guard.DEFAULT_LEDGER.read_bytes()
    == real_ledger_before
)

assert (
    guard.DEFAULT_REVIEW_PACKET.read_bytes()
    == real_packet_before
)

assert not guard.T000002_CHECKPOINT.exists()

print(
    "PASS | real production ledger remained unchanged throughout tests"
)

print(
    "PASS | real review packet remained unchanged throughout tests"
)

print(
    "PASS | real T000002 checkpoint remained absent throughout tests"
)

print(
    "PASS | hostile T000002 continuation-guard tests complete"
)
