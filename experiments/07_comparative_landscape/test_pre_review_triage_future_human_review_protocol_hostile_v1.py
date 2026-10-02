#!/usr/bin/env python3

from __future__ import annotations

import csv
import importlib.util
import tempfile

from pathlib import Path


HERE = Path(__file__).resolve().parent

IMPL = (
    HERE
    / "pre_review_triage_future_human_review_protocol_v1.py"
)


def load_impl():

    spec = importlib.util.spec_from_file_location(
        "future_review_protocol_hostile_target",
        IMPL,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "Unable to load implementation candidate"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


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


def cloned(
    rows,
):

    return [
        dict(row)
        for row in rows
    ]


def expect_failure(
    label,
    fn,
):

    try:
        fn()
    except Exception:
        print(
            "PASS | hostile rejection |",
            label,
        )
        return

    raise AssertionError(
        "Hostile case unexpectedly accepted: "
        + label
    )


impl = load_impl()

packet_id = "priority_001"


# A frozen source-contract dependency may not silently change.
with tempfile.TemporaryDirectory() as tmp_s:

    tmp = Path(
        tmp_s
    )

    fake_manifest = (
        tmp
        / "immutable_checksums.sha256"
    )

    fake_manifest.write_text(
        "0" * 64
        + "  deliberately-invalid\n",
        encoding="utf-8",
    )

    original = (
        impl.EXECUTION_IMMUTABLE_SUMS_PATH
    )

    impl.EXECUTION_IMMUTABLE_SUMS_PATH = (
        fake_manifest
    )

    try:
        expect_failure(
            "frozen execution checksum-manifest identity changed",
            lambda:
                impl.validate_upstream_contract(),
        )
    finally:
        impl.EXECUTION_IMMUTABLE_SUMS_PATH = (
            original
        )


# A malformed current ledger must fail the complete appender contract.
with tempfile.TemporaryDirectory() as tmp_s:

    tmp = Path(
        tmp_s
    )

    ledger_copy = (
        tmp
        / "event_ledger.tsv"
    )

    ledger_copy.write_bytes(
        impl.EVENT_LEDGER.read_bytes()
    )

    fields, ledger_rows = (
        impl.read_tsv(
            ledger_copy
        )
    )

    assert ledger_rows

    ledger_rows[0][
        "event_id"
    ] = "E999999999"

    write_tsv(
        ledger_copy,
        fields,
        ledger_rows,
    )

    original_ledger = (
        impl.EVENT_LEDGER
    )

    impl.EVENT_LEDGER = (
        ledger_copy
    )

    try:
        expect_failure(
            "malformed current ledger rejected by appender contract",
            lambda:
                impl.validate_upstream_contract(),
        )
    finally:
        impl.EVENT_LEDGER = (
            original_ledger
        )


source_path, source_rows = (
    impl.validate_canonical_packet(
        packet_id
    )
)

assert len(source_rows) >= 3

canonical_before = (
    source_path.read_bytes()
)

with tempfile.TemporaryDirectory() as tmp_s:

    tmp = Path(tmp_s)

    def validate_rows(
        rows,
        *,
        complete=False,
        operator_id="SYNTHETIC-TEST-ONLY",
        operator_type="human_with_assistance",
    ):

        path = (
            tmp
            / "candidate.tsv"
        )

        write_tsv(
            path,
            impl.PACKET_FIELDS,
            rows,
        )

        return impl.validate_reviewed_packet(
            packet_id=packet_id,
            reviewed_path=path,
            operator_id=operator_id,
            operator_type=operator_type,
            require_complete=complete,
        )

    # Canonical workspace itself cannot be used as the mutable review file.
    expect_failure(
        "canonical packet used as mutable reviewed packet",
        lambda:
            impl.validate_reviewed_packet(
                packet_id=packet_id,
                reviewed_path=source_path,
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "screening_entity_id"
    ] += ":tampered"

    expect_failure(
        "immutable screening_entity_id mutation",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "baseline_batch_id"
    ] = "B999999"

    expect_failure(
        "authoritative B membership mutation",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "baseline_row_sha256"
    ] = "0" * 64

    expect_failure(
        "baseline row hash mutation",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0], rows[1] = (
        rows[1],
        rows[0],
    )

    expect_failure(
        "row reordering",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows[:-1]
    )

    expect_failure(
        "row removal",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows.append(
        dict(
            rows[-1]
        )
    )

    expect_failure(
        "row addition",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "proposed_event_type"
    ] = "superseding_record_decision"

    rows[0][
        "proposed_record_decision"
    ] = "exclude"

    rows[0][
        "proposed_exclusion_reason_code"
    ] = "application_only_no_reusable_method"

    rows[0][
        "proposed_candidate_method_flag"
    ] = "false"

    rows[0][
        "evidence_basis"
    ] = "Synthetic hostile evidence."

    rows[0][
        "evidence_source_locator"
    ] = "https://example.invalid/hostile"

    expect_failure(
        "superseding event in initial-review protocol",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "proposed_event_type"
    ] = "record_decision"

    rows[0][
        "proposed_record_decision"
    ] = "exclude"

    rows[0][
        "proposed_exclusion_reason_code"
    ] = "application_only_no_reusable_method"

    rows[0][
        "proposed_candidate_method_flag"
    ] = "false"

    rows[0][
        "evidence_basis"
    ] = "Synthetic hostile evidence."

    # No evidence_source_locator.

    expect_failure(
        "terminal decision without evidence locator",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "proposed_event_type"
    ] = "source_escalation"

    rows[0][
        "proposed_record_decision"
    ] = "exclude"

    rows[0][
        "proposed_candidate_method_flag"
    ] = "false"

    rows[0][
        "evidence_basis"
    ] = "Synthetic hostile evidence."

    rows[0][
        "evidence_escalation_status"
    ] = "awaiting_source_escalation"

    expect_failure(
        "source escalation with terminal decision",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "proposed_event_type"
    ] = "source_escalation"

    rows[0][
        "evidence_basis"
    ] = "Synthetic hostile evidence."

    rows[0][
        "evidence_escalation_status"
    ] = "resolved"

    expect_failure(
        "initial source escalation not awaiting",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "proposed_event_type"
    ] = "exclude"

    expect_failure(
        "unknown event type",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "proposed_event_type"
    ] = "record_decision"

    rows[0][
        "proposed_record_decision"
    ] = "retain_for_method_assessment"

    rows[0][
        "proposed_candidate_method_flag"
    ] = "false"

    rows[0][
        "evidence_basis"
    ] = "Synthetic hostile evidence."

    rows[0][
        "evidence_source_locator"
    ] = "https://example.invalid/hostile"

    expect_failure(
        "retained record with candidate flag false",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "proposed_event_type"
    ] = "record_decision"

    rows[0][
        "proposed_record_decision"
    ] = "exclude"

    rows[0][
        "proposed_exclusion_reason_code"
    ] = "application_only_no_reusable_method"

    rows[0][
        "proposed_candidate_method_flag"
    ] = "true"

    rows[0][
        "evidence_basis"
    ] = "Synthetic hostile evidence."

    rows[0][
        "evidence_source_locator"
    ] = "https://example.invalid/hostile"

    expect_failure(
        "excluded record with candidate flag true",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "proposed_event_type"
    ] = "record_decision"

    rows[0][
        "proposed_record_decision"
    ] = "exclude"

    rows[0][
        "proposed_exclusion_reason_code"
    ] = "NOT_A_FROZEN_REASON"

    rows[0][
        "proposed_candidate_method_flag"
    ] = "false"

    rows[0][
        "evidence_basis"
    ] = "Synthetic hostile evidence."

    rows[0][
        "evidence_source_locator"
    ] = "https://example.invalid/hostile"

    expect_failure(
        "unknown exclusion reason",
        lambda:
            validate_rows(
                rows
            ),
    )

    rows = cloned(
        source_rows
    )
    rows[0][
        "evidence_basis"
    ] = "partial field without event type"

    expect_failure(
        "partial human-entry data on proposal-blank row",
        lambda:
            validate_rows(
                rows
            ),
    )

    # Blank packet cannot pass complete-review validation.
    expect_failure(
        "incomplete packet approved as complete",
        lambda:
            validate_rows(
                cloned(
                    source_rows
                ),
                complete=True,
            ),
    )

    # Filled scientific row requires explicit operator provenance.
    rows = cloned(
        source_rows
    )
    rows[0][
        "proposed_event_type"
    ] = "record_decision"

    rows[0][
        "proposed_record_decision"
    ] = "exclude"

    rows[0][
        "proposed_exclusion_reason_code"
    ] = "application_only_no_reusable_method"

    rows[0][
        "proposed_candidate_method_flag"
    ] = "false"

    rows[0][
        "evidence_basis"
    ] = "Synthetic hostile evidence."

    rows[0][
        "evidence_source_locator"
    ] = "https://example.invalid/hostile"

    expect_failure(
        "completed row without operator identity",
        lambda:
            validate_rows(
                rows,
                operator_id="",
            ),
    )

    expect_failure(
        "completed row with invalid operator type",
        lambda:
            validate_rows(
                rows,
                operator_type="not_a_valid_operator_type",
            ),
    )

    # Simulate a target acquiring a current event. Approval must fail closed.
    original_loader = (
        impl.load_current_events
    )

    try:
        entity_id = rows[0][
            "screening_entity_id"
        ]

        impl.load_current_events = (
            lambda: {
                entity_id: {
                    "event_id":
                        "E999999999",

                    "event_type":
                        "record_decision",
                }
            }
        )

        expect_failure(
            "target already has current accepted event",
            lambda:
                validate_rows(
                    rows
                ),
        )

    finally:
        impl.load_current_events = (
            original_loader
        )



old_review_root = (
    impl.PLANNED_REVIEW_ROOT
)

with tempfile.TemporaryDirectory() as tmp_s:

    tmp = Path(
        tmp_s
    )

    impl.PLANNED_REVIEW_ROOT = (
        tmp
        / "future_human_review"
    )

    try:
        impl.materialize_blank_review_packet(
            packet_id
        )

        working = (
            impl.review_working_packet_path(
                packet_id
            )
        )

        expect_failure(
            "working packet destination already exists",
            lambda:
                impl.materialize_blank_review_packet(
                    packet_id
                ),
        )

        fields, complete_rows = (
            impl.read_tsv(
                working
            )
        )

        expect_failure(
            "incomplete packet receives approval payload",
            lambda:
                impl.build_packet_approval_payload(
                    packet_id=packet_id,
                    reviewed_path=working,
                    operator_id=
                        "SYNTHETIC-TEST-ONLY",
                    operator_type=
                        "human_with_assistance",
                    human_approval_text=
                        "APPROVE SYNTHETIC TEST",
                ),
        )

        for row in complete_rows:

            row[
                "proposed_event_type"
            ] = "record_decision"

            row[
                "proposed_record_decision"
            ] = "retain_for_method_assessment"

            row[
                "proposed_candidate_method_flag"
            ] = "true"

            row[
                "evidence_basis"
            ] = "Synthetic hostile-test complete review."

            row[
                "evidence_source_locator"
            ] = (
                "https://example.invalid/"
                "hostile-complete-review"
            )

        write_tsv(
            working,
            fields,
            complete_rows,
        )

        expect_failure(
            "blank human approval text",
            lambda:
                impl.build_packet_approval_payload(
                    packet_id=packet_id,
                    reviewed_path=working,
                    operator_id=
                        "SYNTHETIC-TEST-ONLY",
                    operator_type=
                        "human_with_assistance",
                    human_approval_text="",
                ),
        )

        other_path = (
            tmp
            / "not_the_deterministic_working_path.tsv"
        )

        write_tsv(
            other_path,
            fields,
            complete_rows,
        )

        expect_failure(
            "approval uses non-deterministic reviewed path",
            lambda:
                impl.build_packet_approval_payload(
                    packet_id=packet_id,
                    reviewed_path=other_path,
                    operator_id=
                        "SYNTHETIC-TEST-ONLY",
                    operator_type=
                        "human_with_assistance",
                    human_approval_text=
                        "APPROVE SYNTHETIC TEST",
                ),
        )

        approval = (
            impl.build_packet_approval_payload(
                packet_id=packet_id,
                reviewed_path=working,
                operator_id=
                    "SYNTHETIC-TEST-ONLY",
                operator_type=
                    "human_with_assistance",
                human_approval_text=
                    "APPROVE SYNTHETIC TEST",
            )
        )

        tampered = dict(
            approval
        )

        tampered[
            "reviewed_packet_sha256"
        ] = "0" * 64

        expect_failure(
            "approval reviewed-packet hash tampered",
            lambda:
                impl.validate_packet_approval_payload(
                    payload=tampered,
                    reviewed_path=working,
                ),
        )

        tampered = dict(
            approval
        )

        tampered[
            "production_authority"
        ] = dict(
            approval[
                "production_authority"
            ]
        )

        tampered[
            "production_authority"
        ][
            "event_ledger_mutation_authorized"
        ] = True

        expect_failure(
            "approval payload grants production authority",
            lambda:
                impl.validate_packet_approval_payload(
                    payload=tampered,
                    reviewed_path=working,
                ),
        )

        original_loader = (
            impl.load_current_events
        )

        try:
            target_id = complete_rows[0][
                "screening_entity_id"
            ]

            impl.load_current_events = (
                lambda: {
                    target_id: {
                        "event_id":
                            "E999999999",

                        "event_type":
                            "record_decision",
                    }
                }
            )

            expect_failure(
                "approval recheck detects new current event",
                lambda:
                    impl.build_packet_approval_payload(
                        packet_id=packet_id,
                        reviewed_path=working,
                        operator_id=
                            "SYNTHETIC-TEST-ONLY",
                        operator_type=
                            "human_with_assistance",
                        human_approval_text=
                            "APPROVE SYNTHETIC TEST",
                    ),
            )

        finally:
            impl.load_current_events = (
                original_loader
            )

    finally:
        impl.PLANNED_REVIEW_ROOT = (
            old_review_root
        )


with tempfile.TemporaryDirectory() as tmp_s:

    forbidden = (
        impl.WORKSPACE_ROOT
        / "MUST_NOT_CREATE_REVIEW_WORK"
    )

    old_review_root = (
        impl.PLANNED_REVIEW_ROOT
    )

    impl.PLANNED_REVIEW_ROOT = (
        forbidden
    )

    try:
        expect_failure(
            "working-copy root inside canonical workspace",
            lambda:
                impl.materialize_blank_review_packet(
                    packet_id
                ),
        )

        assert not forbidden.exists()

    finally:
        impl.PLANNED_REVIEW_ROOT = (
            old_review_root
        )


assert source_path.read_bytes() == canonical_before

assert not impl.PLANNED_REVIEW_ROOT.exists()

print("PASS | frozen dependency tampering rejected")
print("PASS | malformed mutable ledger rejected semantically")
print("PASS | canonical workspace cannot be edited as review output")
print("PASS | immutable identity mutations rejected")
print("PASS | row addition/removal/reordering rejected")
print("PASS | invalid scientific-event semantics rejected")
print("PASS | invalid operator provenance rejected")
print("PASS | current-event conflicts rejected")
print("PASS | canonical packet remains byte-identical")
print("PASS | no review or production artifact created")
print("PASS | working-copy overwrite and canonical-root writes rejected")
print("PASS | incomplete/noncanonical packet approval rejected")
print("PASS | approval tampering and production authority rejected")
print("PASS | approval-time event conflicts rechecked")
print("FUTURE_HUMAN_REVIEW_PROTOCOL_V1_HOSTILE_TESTS=PASS")
