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
        "future_review_protocol_test_target",
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
    path: Path,
    fields,
    rows,
):

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


def clone_rows(
    rows,
):

    return [
        dict(
            row
        )
        for row in rows
    ]


impl = load_impl()

runtime = (
    impl.validate_upstream_contract()
)

assert runtime[
    "current_ledger"
][
    "status"
] == "EVENT_LEDGER_VALID"

assert runtime[
    "current_ledger"
][
    "mutation_performed"
] is False

assert runtime[
    "mutable_ledger_sha_pinned"
] is False

state = (
    impl.validate_frozen_workspace_contract()
)

assert state["review_rows"] == 12156
assert state["packet_count"] == 25
assert state["lane_rows"] == {
    "priority": 5477,
    "residual": 6422,
    "manual": 257,
}
assert state["prior_carry_forward_rows"] == 6
assert state["model_fields_exposed"] is False
assert state["scientific_decisions_present"] is False
assert state["production_proposals_present"] is False

assert impl.current_target_event_overlap() == []

manifest = impl.load_packet_manifest()

assert len(manifest) == 25

packet_id = "priority_001"

assert packet_id in manifest

source_path, source_rows = (
    impl.validate_canonical_packet(
        packet_id
    )
)

assert len(source_rows) > 2

source_bytes = (
    impl.canonical_packet_bytes(
        packet_id
    )
)

assert source_bytes == source_path.read_bytes()

original_sha = impl.sha256_file(
    source_path
)

with tempfile.TemporaryDirectory() as tmp_s:

    tmp = Path(tmp_s)

    reviewed = (
        tmp
        / "reviewed.tsv"
    )

    rows = clone_rows(
        source_rows
    )

    # One valid retained record.
    rows[0][
        "proposed_event_type"
    ] = "record_decision"

    rows[0][
        "proposed_record_decision"
    ] = "retain_for_method_assessment"

    rows[0][
        "proposed_candidate_method_flag"
    ] = "true"

    rows[0][
        "evidence_basis"
    ] = (
        "Primary or authoritative source supports "
        "retention for method assessment."
    )

    rows[0][
        "evidence_source_locator"
    ] = "https://example.invalid/source/retain"

    # One valid exclusion.
    rows[1][
        "proposed_event_type"
    ] = "record_decision"

    rows[1][
        "proposed_record_decision"
    ] = "exclude"

    rows[1][
        "proposed_exclusion_reason_code"
    ] = "application_only_no_reusable_method"

    rows[1][
        "proposed_candidate_method_flag"
    ] = "false"

    rows[1][
        "evidence_basis"
    ] = (
        "Authoritative source describes an application "
        "without a reusable analytical method."
    )

    rows[1][
        "evidence_source_locator"
    ] = "https://example.invalid/source/exclude"

    # One valid source escalation.
    rows[2][
        "proposed_event_type"
    ] = "source_escalation"

    rows[2][
        "evidence_basis"
    ] = (
        "Available evidence is insufficient for "
        "a terminal record disposition."
    )

    rows[2][
        "evidence_escalation_status"
    ] = "awaiting_source_escalation"

    write_tsv(
        reviewed,
        impl.PACKET_FIELDS,
        rows,
    )

    summary = (
        impl.validate_reviewed_packet(
            packet_id=packet_id,
            reviewed_path=reviewed,
            operator_id="SYNTHETIC-TEST-ONLY",
            operator_type="human_with_assistance",
            require_complete=False,
        )
    )

    assert summary[
        "completed_review_rows"
    ] == 3

    assert summary[
        "blank_review_rows"
    ] == (
        len(
            source_rows
        )
        - 3
    )

    assert summary[
        "review_complete"
    ] is False

    assert summary[
        "event_type_counts"
    ] == {
        "record_decision": 2,
        "source_escalation": 1,
    }

    assert summary[
        "record_decision_counts"
    ] == {
        "exclude": 1,
        "retain_for_method_assessment": 1,
    }

    assert summary[
        "production_proposal_persisted"
    ] is False

    assert summary[
        "production_authorization_created"
    ] is False

    assert summary[
        "event_ledger_mutated"
    ] is False

    # The immutable canonical source packet remains byte-identical.
    assert impl.sha256_file(
        source_path
    ) == original_sha

    assert source_path.read_bytes() == source_bytes


# Confirm the row-wise semantic adapter can span more than one
# authoritative B batch without treating the packet as a transaction.
batch_ids = {
    row[
        "baseline_batch_id"
    ]
    for row in source_rows
}

if len(batch_ids) < 2:

    found = False

    for candidate in manifest:

        _, candidate_rows = (
            impl.validate_canonical_packet(
                candidate
            )
        )

        candidate_batches = {
            row[
                "baseline_batch_id"
            ]
            for row in candidate_rows
        }

        if len(
            candidate_batches
        ) >= 2:
            found = True
            break

    assert found
else:
    assert len(batch_ids) >= 2



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
        receipt = (
            impl.materialize_blank_review_packet(
                packet_id
            )
        )

        working = (
            impl.review_working_packet_path(
                packet_id
            )
        )

        assert working.is_file()

        assert (
            working.read_bytes()
            == source_bytes
        )

        assert receipt[
            "source_packet_sha256"
        ] == original_sha

        assert receipt[
            "working_packet_sha256"
        ] == original_sha

        assert receipt[
            "all_human_fields_blank"
        ] is True

        fields, approval_rows = (
            impl.read_tsv(
                working
            )
        )

        assert fields == (
            impl.PACKET_FIELDS
        )

        for row in approval_rows:

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
            ] = (
                "Synthetic complete human-review "
                "test disposition."
            )

            row[
                "evidence_source_locator"
            ] = (
                "https://example.invalid/"
                "complete-review-source"
            )

        write_tsv(
            working,
            impl.PACKET_FIELDS,
            approval_rows,
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
                    "APPROVE SYNTHETIC PACKET TEST",
            )
        )

        assert approval[
            "packet_id"
        ] == packet_id

        assert approval[
            "row_count"
        ] == len(
            approval_rows
        )

        assert approval[
            "source_packet_sha256"
        ] == original_sha

        assert approval[
            "reviewed_packet_sha256"
        ] == impl.sha256_file(
            working
        )

        assert approval[
            "review_summary"
        ][
            "record_decision_counts"
        ] == {
            "retain_for_method_assessment":
                len(
                    approval_rows
                )
        }

        assert not any(
            approval[
                "production_authority"
            ].values()
        )

        validated_approval = (
            impl.validate_packet_approval_payload(
                payload=approval,
                reviewed_path=working,
            )
        )

        assert (
            validated_approval
            == approval
        )

        assert not (
            impl.PLANNED_REVIEW_ROOT
            / "proposal.tsv"
        ).exists()

        assert not (
            impl.PLANNED_REVIEW_ROOT
            / "approval.json"
        ).exists()

    finally:
        impl.PLANNED_REVIEW_ROOT = (
            old_review_root
        )


assert not impl.PLANNED_REVIEW_ROOT.exists()

print("PASS | frozen upstream and current ledger validate")
print("PASS | current ledger SHA observed but not permanently pinned")
print("PASS | frozen workspace validates")
print("PASS | row-wise in-memory proposal-semantic reuse works")
print("PASS | retain/exclude/source-escalation synthetic cases valid")
print("PASS | multi-B packet does not become a production transaction")
print("PASS | canonical review packet remains byte-identical")
print("PASS | no review artifact or production artifact created")
print("PASS | deterministic blank working-copy materialization works")
print("PASS | complete packet approval binds reviewed bytes in memory")
print("PASS | packet approval grants no production authority")
print("FUTURE_HUMAN_REVIEW_PROTOCOL_V1_TESTS=PASS")
