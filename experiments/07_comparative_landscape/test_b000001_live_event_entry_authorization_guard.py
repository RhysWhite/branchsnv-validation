#!/usr/bin/env python3

from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import sys
import tempfile


HERE = Path(__file__).resolve().parent

MODULE_PATH = (
    HERE
    / "b000001_live_event_entry_authorization_guard.py"
)

spec = importlib.util.spec_from_file_location(
    "b000001_live_event_entry_authorization_guard_tests",
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

appender = guard.load_appender()


def expect_error(
    label,
    fn,
):
    try:
        fn()

    except (
        guard.GuardError,
        guard.RecoveryRequiredError,
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


context = guard.load_guard_context(
    queue_path=
        guard.DEFAULT_QUEUE,

    execution_root=
        guard.EXECUTION_ROOT,
)

contract = context[
    "contract"
]

scope = context[
    "scope"
]


assert contract[
    "amendment"
][
    "amendment_id"
] == "B000001_AUTHORIZATION_DESIGN_AMENDMENT_01"

assert contract[
    "amendment"
][
    "amended_human_entry_fields"
] == guard.AMENDED_HUMAN_FIELDS

assert contract[
    "amendment"
][
    "proposal_extraction_mapping"
] == guard.EXPECTED_PROPOSAL_MAPPING

assert contract[
    "amendment"
][
    "scientific_contract_changed"
] is False

print(
    "PASS | Amendment 01 loaded as normative guard dependency"
)


assert len(
    scope[
        "membership_rows"
    ]
) == 500

assert scope[
    "entity_ids"
][
    0
] == guard.EXPECTED_FIRST_ENTITY

assert (
    scope[
        "canonical_ids_sha256"
    ]
    == guard.EXPECTED_MANIFEST_ORDERED_SHA256
)

assert (
    scope[
        "canonical_membership_sha256"
    ]
    == guard.EXPECTED_MEMBERSHIP_CANONICAL_SHA256
)

assert (
    scope[
        "canonical_baseline_sha256"
    ]
    == guard.EXPECTED_BASELINE_CANONICAL_SHA256
)

print(
    "PASS | exact frozen B000001 identity reconstructed"
)


fields = guard.review_packet_fields(
    scope=
        scope,

    contract=
        contract,
)

assert len(
    fields
) == len(
    set(
        fields
    )
)

assert all(
    field in fields
    for field in guard.AMENDED_HUMAN_FIELDS
)

assert "evidence_escalation_status" in fields
assert "proposed_evidence_escalation_status" in fields

assert "notes" in fields
assert "proposed_notes" in fields

assert (
    fields.count(
        "evidence_escalation_status"
    )
    == 1
)

assert (
    fields.count(
        "proposed_evidence_escalation_status"
    )
    == 1
)

assert fields.count(
    "notes"
) == 1

assert fields.count(
    "proposed_notes"
) == 1

print(
    "PASS | amended review-packet schema contains no duplicate columns"
)

print(
    "PASS | frozen and proposed evidence_escalation_status are distinct"
)

print(
    "PASS | frozen and proposed notes are distinct"
)


packet_a = guard.build_review_packet_bytes(
    scope=
        scope,

    contract=
        contract,
)

packet_b = guard.build_review_packet_bytes(
    scope=
        scope,

    contract=
        contract,
)

assert packet_a == packet_b

packet_sha = hashlib.sha256(
    packet_a
).hexdigest()

print(
    "PASS | deterministic 500-row amended review packet generated"
)

print(
    "INFO | B000001 review packet SHA256 =",
    packet_sha,
)

print(
    "INFO | B000001 review packet bytes =",
    len(
        packet_a
    ),
)


def synthetic_authorization():
    return {
        "status":
            guard.AUTH_STATUS,

        "schema_version":
            1,

        "parent_commit":
            "0" * 40,

        "b000001_authorization_design_freeze_sha256":
            guard.sha256_file(
                guard.B000001_DESIGN_SUMS
            ),

        "event_appender_implementation_sha256":
            guard.EXPECTED_APPENDER_SHA256,

        "event_appender_implementation_freeze_sha256":
            guard.sha256_file(
                guard.APPENDER_FREEZE_SUMS
            ),

        "event_entry_design_freeze_sha256":
            guard.sha256_file(
                guard.EVENT_ENTRY_DESIGN_SUMS
            ),

        "B000001_membership_identity":
            guard.expected_membership_identity(
                contract[
                    "design"
                ]
            ),

        "batch_id":
            "B000001",

        "authorized_position":
            1,

        "authorized_screening_entity_id":
            guard.EXPECTED_FIRST_ENTITY,

        "authorized_baseline_row_sha256":
            guard.EXPECTED_FIRST_ROW_SHA256,

        "expected_pre_ledger_sha256":
            guard.EXPECTED_GENESIS_LEDGER_SHA256,

        "max_live_event_count":
            1,

        "operator_id":
            "synthetic-test-human",

        "operator_type":
            "human",

        "permitted_initial_event_types": [
            "record_decision",
            "source_escalation",
        ],

        "receipt_checkpoint_contract": {
            "transaction_id":
                "T000001",

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
        },

        "positions_2_to_500_authorized":
            False,

        "one_use":
            True,

        "scientific_decision_preselected":
            False,
    }


with tempfile.TemporaryDirectory(
    prefix="branchsnv-exp07-b000001-amendment01-tests-"
) as tmp:
    root = Path(
        tmp
    )

    packet_path = (
        root
        / "review.tsv"
    )

    packet_path.write_bytes(
        packet_a
    )

    blank_rows = guard.validate_review_packet(
        packet_path=
            packet_path,

        scope=
            scope,

        contract=
            contract,

        require_all_human_fields_blank=True,
    )

    assert len(
        blank_rows
    ) == 500

    assert all(
        not row[
            field
        ]
        for row in blank_rows
        for field in guard.AMENDED_HUMAN_FIELDS
    )

    print(
        "PASS | generated amended packet has no preclassification"
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

            contract=
                contract,

            appender=
                appender,

            require_tracked=False,
        )
    )

    assert validated_auth[
        "authorization_commit"
    ] == "UNTRACKED_TEST_AUTHORIZATION"

    print(
        "PASS | synthetic authorization accepted for temporary tests"
    )


    packet_fields, rows = read_tsv(
        packet_path
    )

    # Frozen baseline fields remain untouched.
    frozen_baseline_notes = rows[
        0
    ][
        "notes"
    ]

    frozen_baseline_escalation = rows[
        0
    ][
        "evidence_escalation_status"
    ]

    rows[
        0
    ][
        "proposed_event_type"
    ] = "source_escalation"

    rows[
        0
    ][
        "proposed_evidence_basis"
    ] = (
        "SYNTHETIC_TEST_ONLY: authoritative source "
        "checking required before terminal disposition"
    )

    rows[
        0
    ][
        "proposed_evidence_escalation_status"
    ] = "awaiting_source_escalation"

    rows[
        0
    ][
        "proposed_notes"
    ] = "synthetic temporary-ledger test only"

    assert rows[
        0
    ][
        "notes"
    ] == frozen_baseline_notes

    assert rows[
        0
    ][
        "evidence_escalation_status"
    ] == frozen_baseline_escalation

    edited_packet = (
        root
        / "review-edited.tsv"
    )

    write_tsv(
        edited_packet,
        packet_fields,
        rows,
    )

    print(
        "PASS | proposed fields editable without altering frozen baseline fields"
    )


    real_before = (
        guard.DEFAULT_LEDGER.read_bytes()
    )

    prepared = guard.prepare_canary(
        authorization_path=
            authorization_path,

        review_packet_path=
            edited_packet,

        ledger_path=
            guard.DEFAULT_LEDGER,

        context=
            context,

        require_tracked_authorization=False,

        transaction_timestamp_utc=
            "2026-09-25T03:00:00Z",
    )

    assert prepared[
        "status"
    ] == "B000001_CANARY_DRY_RUN_VALID"

    assert prepared[
        "prepared_receipt"
    ][
        "first_assigned_event_id"
    ] == "E000000001"

    assert prepared[
        "prepared_receipt"
    ][
        "last_assigned_event_id"
    ] == "E000000001"

    assert prepared[
        "prepared_receipt"
    ][
        "new_event_count"
    ] == 1

    assert (
        guard.DEFAULT_LEDGER.read_bytes()
        == real_before
    )

    proposal_fields, proposal_rows = (
        appender.read_proposal(
            Path(
                root
                / "temporary-proposal-not-created.tsv"
            )
        )
        if False
        else (
            list(
                appender.PROPOSAL_FIELDS
            ),
            [],
        )
    )

    del proposal_fields
    del proposal_rows

    proposal_text = prepared[
        "proposal_bytes"
    ].decode(
        "utf-8"
    )

    assert (
        "awaiting_source_escalation"
        in proposal_text
    )

    assert (
        "synthetic temporary-ledger test only"
        in proposal_text
    )

    print(
        "PASS | amended proposed_ fields map into frozen appender proposal"
    )

    print(
        "PASS | one-row canary dry run validates against real genesis"
    )

    print(
        "PASS | canary dry run does not mutate real production"
    )

    print(
        "INFO | synthetic canary proposal SHA256 =",
        prepared[
            "proposal_sha256"
        ],
    )


    # Position 2 may not contain any proposed values.
    _, bad_rows = read_tsv(
        edited_packet
    )

    bad_rows[
        1
    ][
        "proposed_event_type"
    ] = "source_escalation"

    bad_packet = (
        root
        / "bad-position2.tsv"
    )

    write_tsv(
        bad_packet,
        packet_fields,
        bad_rows,
    )

    expect_error(
        "position 2 proposed scientific input prohibited",
        lambda:
            guard.prepare_canary(
                authorization_path=
                    authorization_path,

                review_packet_path=
                    bad_packet,

                ledger_path=
                    guard.DEFAULT_LEDGER,

                context=
                    context,

                require_tracked_authorization=False,

                transaction_timestamp_utc=
                    "2026-09-25T03:01:00Z",
            ),
    )


    # Immutable baseline notes cannot be altered even though proposed_notes exists.
    _, tampered_rows = read_tsv(
        edited_packet
    )

    tampered_rows[
        0
    ][
        "notes"
    ] = "TAMPERED FROZEN BASELINE NOTES"

    tampered_packet = (
        root
        / "tampered-baseline-notes.tsv"
    )

    write_tsv(
        tampered_packet,
        packet_fields,
        tampered_rows,
    )

    expect_error(
        "frozen baseline notes tampering prohibited",
        lambda:
            guard.prepare_canary(
                authorization_path=
                    authorization_path,

                review_packet_path=
                    tampered_packet,

                ledger_path=
                    guard.DEFAULT_LEDGER,

                context=
                    context,

                require_tracked_authorization=False,

                transaction_timestamp_utc=
                    "2026-09-25T03:02:00Z",
            ),
    )


    # Immutable baseline evidence-escalation status cannot be altered.
    _, tampered_rows = read_tsv(
        edited_packet
    )

    tampered_rows[
        0
    ][
        "evidence_escalation_status"
    ] = "TAMPERED"

    tampered_packet = (
        root
        / "tampered-baseline-escalation.tsv"
    )

    write_tsv(
        tampered_packet,
        packet_fields,
        tampered_rows,
    )

    expect_error(
        "frozen baseline evidence escalation field tampering prohibited",
        lambda:
            guard.prepare_canary(
                authorization_path=
                    authorization_path,

                review_packet_path=
                    tampered_packet,

                ledger_path=
                    guard.DEFAULT_LEDGER,

                context=
                    context,

                require_tracked_authorization=False,

                transaction_timestamp_utc=
                    "2026-09-25T03:03:00Z",
            ),
    )


    bad_auth = dict(
        authorization
    )

    bad_auth[
        "max_live_event_count"
    ] = 2

    bad_auth_path = (
        root
        / "bad-auth-count.json"
    )

    bad_auth_path.write_bytes(
        guard.pretty_json_bytes(
            bad_auth
        )
    )

    expect_error(
        "authorization cannot permit two events",
        lambda:
            guard.validate_authorization(
                authorization_path=
                    bad_auth_path,

                contract=
                    contract,

                appender=
                    appender,

                require_tracked=False,
            ),
    )


    bad_auth = dict(
        authorization
    )

    bad_auth[
        "positions_2_to_500_authorized"
    ] = True

    bad_auth_path = (
        root
        / "bad-auth-scope.json"
    )

    bad_auth_path.write_bytes(
        guard.pretty_json_bytes(
            bad_auth
        )
    )

    expect_error(
        "authorization cannot enable positions 2-500",
        lambda:
            guard.validate_authorization(
                authorization_path=
                    bad_auth_path,

                contract=
                    contract,

                appender=
                    appender,

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

                contract=
                    contract,

                appender=
                    appender,

                require_tracked=False,
            ),
    )


    # Real production may not run from an untracked synthetic authorization.
    expect_error(
        "real production requires committed tracked authorization",
        lambda:
            guard.execute_canary(
                authorization_path=
                    authorization_path,

                review_packet_path=
                    edited_packet,

                ledger_path=
                    guard.DEFAULT_LEDGER,

                receipt_root=
                    guard.RECEIPT_ROOT,

                context=
                    context,

                require_tracked_authorization=True,

                transaction_timestamp_utc=
                    "2026-09-25T03:04:00Z",
            ),
    )

    assert not guard.RECEIPT_ROOT.exists()

    assert (
        guard.DEFAULT_LEDGER.read_bytes()
        == real_before
    )

    print(
        "PASS | untracked authorization cannot mutate real production"
    )


    # Full canary transaction on temporary copies only.
    temp_ledger = (
        root
        / "temp-event-ledger.tsv"
    )

    temp_ledger.write_bytes(
        real_before
    )

    temp_receipts = (
        root
        / "temp-receipts"
    )

    executed = guard.execute_canary(
        authorization_path=
            authorization_path,

        review_packet_path=
            edited_packet,

        ledger_path=
            temp_ledger,

        receipt_root=
            temp_receipts,

        context=
            context,

        require_tracked_authorization=False,

        transaction_timestamp_utc=
            "2026-09-25T03:05:00Z",
    )

    assert executed[
        "status"
    ] == "B000001_CANARY_EXECUTION_COMPLETE"

    final_checkpoint = (
        temp_receipts
        / "T000001"
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

    temp_validation = (
        appender.validate_current_ledger(
            ledger_path=
                temp_ledger,

            context=
                context[
                    "appender_context"
                ],
        )
    )

    assert temp_validation[
        "event_count"
    ] == 1

    assert temp_validation[
        "derived_state_counts"
    ][
        "awaiting_source_escalation"
    ] == 1

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
    ] == "T000001_CHECKPOINT_VALID"

    receipt = json.loads(
        (
            final_checkpoint
            / "receipt.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        receipt[
            "b000001_authorization_design_amendment_01_freeze_sha256"
        ]
        == guard.sha256_file(
            guard.B000001_AMENDMENT_SUMS
        )
    )

    print(
        "PASS | temporary T000001 execution completes"
    )

    print(
        "PASS | exact three-file checkpoint created"
    )

    print(
        "PASS | receipt records Amendment 01 freeze"
    )

    print(
        "PASS | temporary post-ledger/checkpoint validation passes"
    )


    expect_error(
        "one-use canary replay prohibited",
        lambda:
            guard.execute_canary(
                authorization_path=
                    authorization_path,

                review_packet_path=
                    edited_packet,

                ledger_path=
                    temp_ledger,

                receipt_root=
                    temp_receipts,

                context=
                    context,

                require_tracked_authorization=False,

                transaction_timestamp_utc=
                    "2026-09-25T03:06:00Z",
            ),
    )


    # Recovery simulation.
    recovery_ledger = (
        root
        / "recovery-ledger.tsv"
    )

    recovery_ledger.write_bytes(
        real_before
    )

    recovery_receipts = (
        root
        / "recovery-receipts"
    )

    try:
        guard.execute_canary(
            authorization_path=
                authorization_path,

            review_packet_path=
                edited_packet,

            ledger_path=
                recovery_ledger,

            receipt_root=
                recovery_receipts,

            context=
                context,

            require_tracked_authorization=False,

            transaction_timestamp_utc=
                "2026-09-25T03:07:00Z",

            _test_fail_after_append=True,
        )

    except guard.RecoveryRequiredError:
        pass

    else:
        raise AssertionError(
            "Expected recovery-required failure"
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
    ] == 1

    staged = [
        path
        for path in recovery_receipts.iterdir()
        if path.name.startswith(
            ".T000001.tmp."
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
        "PASS | ledger-success/checkpoint-failure enters recovery state"
    )

    print(
        "PASS | staged checkpoint preserved after post-append failure"
    )

    expect_error(
        "recovery state blocks transaction retry",
        lambda:
            guard.execute_canary(
                authorization_path=
                    authorization_path,

                review_packet_path=
                    edited_packet,

                ledger_path=
                    recovery_ledger,

                receipt_root=
                    recovery_receipts,

                context=
                    context,

                require_tracked_authorization=False,

                transaction_timestamp_utc=
                    "2026-09-25T03:08:00Z",
            ),
    )


assert (
    hashlib.sha256(
        guard.DEFAULT_LEDGER.read_bytes()
    ).hexdigest()
    == guard.EXPECTED_GENESIS_LEDGER_SHA256
)

assert not guard.RECEIPT_ROOT.exists()

print(
    "PASS | real production ledger remained untouched throughout tests"
)

print(
    "PASS | real production receipt root remained absent throughout tests"
)

print(
    "PASS | hostile amendment-aware guard tests complete"
)
