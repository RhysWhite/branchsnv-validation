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
MODULE_PATH = HERE / "b000001_post_pilot_tranche_guard.py"

spec = importlib.util.spec_from_file_location(
    "b000001_post_pilot_tranche_guard_tests",
    MODULE_PATH,
)
assert spec is not None
assert spec.loader is not None

guard = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = guard
spec.loader.exec_module(guard)

context = guard.load_context()
design = context["design"]
runtime = context["runtime"]
appender = context["appender"]


def expect_error(label, fn):
    try:
        fn()
    except (
        guard.TrancheGuardError,
        guard.RecoveryRequiredError,
        context["base_guard"].GuardError,
        appender.EventAppenderError,
    ):
        print("PASS |", label)
        return
    raise AssertionError("Expected fail-closed error: " + label)


def read_tsv(path):
    with Path(path).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def write_tsv(path, fields, rows):
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
        writer.writerows(rows)


assert runtime["transaction_id"] == "T000006"
assert runtime["positions"] == list(range(12, 37))
assert runtime["count"] == 25
assert runtime["pre_event_count"] == 22
assert runtime["post_event_count"] == 47
assert runtime["first_event_id"] == "E000000023"
assert runtime["last_event_id"] == "E000000047"

assert context["target"]["entity_ids"] == [
    item["screening_entity_id"]
    for item in design["target_identity"]["entities"]
]

assert guard.identity_summary(design) == {
    "entity_count": 25,
    "target_position_start": 12,
    "target_position_end": 36,
    "ordered_entity_ids_sha256": (
        "a169877057cf928be5c945a266405406ae15833271daef89c0179d3d5260b5f2"
    ),
    "canonical_membership_rows_sha256": (
        "0ea1bb77b778a8105389da08336eed90f6163c41f4fd7d8c1eb559a788f3c126"
    ),
    "canonical_baseline_queue_rows_sha256": (
        "1fbad740eb36d57838f46f60a4ff7cf81fe7d448ee7e8e0950fad72638bc5c59"
    ),
    "canonical_target_identity_sha256": (
        "2c558ee5be00441beefffdb8632b1daaee6f427d384879dbdad5e85497316647"
    ),
}

print("PASS | exact frozen T000006 target reconstructed")
print("PASS | exact 25-record target identity hashes reproduced")

real_ledger_before = guard.DEFAULT_LEDGER.read_bytes()
real_packet_before = guard.DEFAULT_REVIEW_PACKET.read_bytes()
pre_review_snapshot = guard.pre_review_snapshot_path(context)
assert pre_review_snapshot.is_file()
assert pre_review_snapshot.read_bytes() == real_packet_before

assert hashlib.sha256(real_ledger_before).hexdigest() == (
    "85eabc27f89cc215b75b4b48611e6131f8ef1f7e7d5a022b1229d1241bd960ac"
)
assert hashlib.sha256(real_packet_before).hexdigest() == (
    "09e08a25873e9a628a2c7900b82f384f7b5838bb166b89d412759fe92a9101d6"
)

pre_rows = guard.validate_review_packet(
    packet_path=guard.DEFAULT_REVIEW_PACKET,
    context=context,
    mode="pre_review",
)
assert len(pre_rows) == 500
assert all(
    not pre_rows[position - 1][field]
    for position in runtime["positions"]
    for field in guard.PROPOSED_FIELDS
)
assert all(
    not pre_rows[position - 1][field]
    for position in range(runtime["end"] + 1, 501)
    for field in guard.PROPOSED_FIELDS
)

print("PASS | real pre-T000006 review packet valid")
print("PASS | positions 1-11 historical proposal state locked")
print("PASS | positions 12-500 remain proposal-blank")

pre_validation = guard.validate_pre_transaction_state(
    ledger_path=guard.DEFAULT_LEDGER,
    context=context,
)
assert pre_validation["event_count"] == 22
assert pre_validation["derived_state_counts"] == {
    "awaiting_source_escalation": 0,
    "blocked_metadata": 484,
    "complete": 11,
    "ready": 94611,
}

print("PASS | exact T000006 production pre-state validated")


def build_synthetic_authorization(packet_path, timestamp):
    operator_id = "synthetic-test-human"
    operator_type = "human"

    proposal_bytes = guard.extract_proposal_bytes(
        packet_path=packet_path,
        operator_id=operator_id,
        operator_type=operator_type,
        context=context,
    )
    proposal_sha = guard.sha256_bytes(proposal_bytes)

    with tempfile.TemporaryDirectory(
        prefix="branchsnv-exp07-t000006-projection-"
    ) as tmp:
        proposal_path = Path(tmp) / "proposal.tsv"
        proposal_path.write_bytes(proposal_bytes)
        prepared = appender.prepare_transaction_from_files(
            ledger_path=guard.DEFAULT_LEDGER,
            proposal_path=proposal_path,
            expected_pre_ledger_sha256=runtime["pre_ledger_sha256"],
            context=context["appender_context"],
            transaction_timestamp_utc=timestamp,
        )

    projected_sha = appender.sha256_bytes(prepared["candidate_bytes"])
    receipt = prepared["receipt"]

    return {
        "status": guard.authorization_status(context),
        "schema_version": 1,
        "parent_commit": "0" * 40,
        "tranche_design_freeze_sha256": context["design_freeze_sha256"],
        "post_pilot_tranche_guard_sha256": guard.sha256_file(MODULE_PATH),
        "event_appender_implementation_sha256": (
            context["base_guard"].EXPECTED_APPENDER_SHA256
        ),
        "event_appender_implementation_freeze_sha256": guard.sha256_file(
            context["base_guard"].APPENDER_FREEZE_SUMS
        ),
        "event_entry_design_freeze_sha256": guard.sha256_file(
            context["base_guard"].EVENT_ENTRY_DESIGN_SUMS
        ),
        "target_identity": guard.identity_summary(design),
        "batch_id": "B000001",
        "authorized_positions": runtime["positions"],
        "expected_pre_ledger_sha256": runtime["pre_ledger_sha256"],
        "expected_pre_event_count": runtime["pre_event_count"],
        "authorized_event_count": runtime["count"],
        "expected_assigned_event_ids": runtime["expected_event_ids"],
        "operator_id": operator_id,
        "operator_type": operator_type,
        "permitted_initial_event_types": [
            "record_decision",
            "source_escalation",
        ],
        "receipt_checkpoint_contract": guard.expected_checkpoint_contract(
            context
        ),
        "positions_outside_target_authorized": False,
        "partial_transaction_permitted": False,
        "one_use": True,
        "proposal_sha256": proposal_sha,
        "scientific_decisions_frozen_before_authorization": True,
        "authorization_does_not_modify_scientific_decisions": True,
        "transaction_timestamp_utc": timestamp,
        "projected_post_ledger_sha256": projected_sha,
        "projected_post_state_counts": receipt[
            "derived_state_counts_after_append"
        ],
        "event_ledger_mutation_authorized": True,
        "review_packet_mutation_authorized": False,
        "human_approval_text": "SYNTHETIC TEST ONLY",
    }


with tempfile.TemporaryDirectory(
    prefix="branchsnv-exp07-post-pilot-guard-tests-"
) as tmp:
    root = Path(tmp)
    packet_path = root / "review.tsv"
    packet_path.write_bytes(real_packet_before)

    fields, rows = read_tsv(packet_path)

    # Populate the 25 target positions only with synthetic source escalations.
    # This exercises transaction mechanics without manufacturing terminal
    # scientific conclusions.
    for position in runtime["positions"]:
        row = rows[position - 1]
        row["proposed_event_type"] = "source_escalation"
        row["proposed_record_decision"] = ""
        row["proposed_exclusion_reason_code"] = ""
        row["proposed_candidate_method_flag"] = ""
        row["proposed_evidence_basis"] = (
            f"SYNTHETIC_TEST_ONLY position {position}: "
            "additional authoritative source review required."
        )
        row["proposed_evidence_source_locator"] = ""
        row["proposed_evidence_escalation_status"] = (
            "awaiting_source_escalation"
        )
        row["proposed_notes"] = "synthetic temporary-ledger test only"

    write_tsv(packet_path, fields, rows)

    validated_rows = guard.validate_review_packet(
        packet_path=packet_path,
        context=context,
        mode="transaction_ready",
    )
    assert len(validated_rows) == 500
    print("PASS | synthetic 25-record transaction-ready packet valid")
    print("PASS | positions 12-36 may carry proposals")
    print("PASS | positions 37-500 remain blank")

    timestamp = "2026-09-26T04:00:00Z"
    authorization = build_synthetic_authorization(packet_path, timestamp)
    authorization_path = root / "authorization.json"
    authorization_path.write_bytes(guard.pretty_json_bytes(authorization))

    validated_auth = guard.validate_authorization(
        authorization_path=authorization_path,
        context=context,
        require_tracked=False,
    )
    assert validated_auth["authorization_commit"] == (
        "UNTRACKED_TEST_AUTHORIZATION"
    )
    print("PASS | synthetic generic T000006 authorization accepted")

    prepared = guard.prepare_transaction(
        authorization_path=authorization_path,
        packet_path=packet_path,
        ledger_path=guard.DEFAULT_LEDGER,
        context=context,
        require_tracked_authorization=False,
    )
    receipt = prepared["prepared_receipt"]
    assert prepared["status"] == "T000006_DRY_RUN_VALID"
    assert receipt["new_event_count"] == 25
    assert receipt["pre_append_event_count"] == 22
    assert receipt["post_append_event_count"] == 47
    assert receipt["first_assigned_event_id"] == "E000000023"
    assert receipt["last_assigned_event_id"] == "E000000047"
    assert receipt["event_type_counts"] == {"source_escalation": 25}
    assert receipt["derived_state_counts_after_append"] == {
        "awaiting_source_escalation": 25,
        "blocked_metadata": 484,
        "complete": 11,
        "ready": 94586,
    }
    assert receipt["published"] is False
    assert guard.DEFAULT_LEDGER.read_bytes() == real_ledger_before

    print("PASS | dry run assigns E000000023-E000000047")
    print("PASS | projected 25-event state transition validated")
    print("PASS | dry run does not mutate real production")

    # Partial target is prohibited.
    _, missing_rows = read_tsv(packet_path)
    for field in guard.PROPOSED_FIELDS:
        missing_rows[runtime["end"] - 1][field] = ""
    missing_path = root / "missing-last-target.tsv"
    write_tsv(missing_path, fields, missing_rows)
    expect_error(
        "partial post-pilot tranche prohibited",
        lambda: guard.extract_proposal_bytes(
            packet_path=missing_path,
            operator_id="synthetic-test-human",
            operator_type="human",
            context=context,
        ),
    )

    # Future position cannot receive proposed input.
    _, bad_rows = read_tsv(packet_path)
    future_position = runtime["end"] + 1
    bad_rows[future_position - 1]["proposed_event_type"] = "source_escalation"
    bad_rows[future_position - 1]["proposed_evidence_basis"] = "SYNTHETIC TEST"
    bad_rows[future_position - 1][
        "proposed_evidence_escalation_status"
    ] = "awaiting_source_escalation"
    bad_future = root / "bad-future-position.tsv"
    write_tsv(bad_future, fields, bad_rows)
    expect_error(
        "future position proposal prohibited",
        lambda: guard.validate_review_packet(
            packet_path=bad_future,
            context=context,
            mode="transaction_ready",
        ),
    )

    # Historical reviewed state cannot be changed.
    _, bad_rows = read_tsv(packet_path)
    bad_rows[10]["proposed_notes"] += " TAMPER"
    bad_history = root / "bad-history.tsv"
    write_tsv(bad_history, fields, bad_rows)
    expect_error(
        "historical positions 1-11 immutable",
        lambda: guard.validate_review_packet(
            packet_path=bad_history,
            context=context,
            mode="transaction_ready",
        ),
    )

    bad_auth = dict(authorization)
    bad_auth["authorized_positions"] = runtime["positions"][:-1]
    bad_auth_path = root / "bad-auth-positions.json"
    bad_auth_path.write_bytes(guard.pretty_json_bytes(bad_auth))
    expect_error(
        "authorization must pin exact target positions",
        lambda: guard.validate_authorization(
            authorization_path=bad_auth_path,
            context=context,
            require_tracked=False,
        ),
    )

    bad_auth = dict(authorization)
    bad_auth["partial_transaction_permitted"] = True
    bad_auth_path = root / "bad-auth-partial.json"
    bad_auth_path.write_bytes(guard.pretty_json_bytes(bad_auth))
    expect_error(
        "authorization cannot permit partial transaction",
        lambda: guard.validate_authorization(
            authorization_path=bad_auth_path,
            context=context,
            require_tracked=False,
        ),
    )

    bad_auth = dict(authorization)
    bad_auth["positions_outside_target_authorized"] = True
    bad_auth_path = root / "bad-auth-scope.json"
    bad_auth_path.write_bytes(guard.pretty_json_bytes(bad_auth))
    expect_error(
        "authorization cannot enable outside positions",
        lambda: guard.validate_authorization(
            authorization_path=bad_auth_path,
            context=context,
            require_tracked=False,
        ),
    )

    bad_auth = dict(authorization)
    bad_auth["proposal_sha256"] = "0" * 64
    bad_auth_path = root / "bad-auth-proposal-sha.json"
    bad_auth_path.write_bytes(guard.pretty_json_bytes(bad_auth))
    expect_error(
        "authorization proposal SHA must match reviewed proposal",
        lambda: guard.prepare_transaction(
            authorization_path=bad_auth_path,
            packet_path=packet_path,
            ledger_path=guard.DEFAULT_LEDGER,
            context=context,
            require_tracked_authorization=False,
        ),
    )

    bad_auth = dict(authorization)
    bad_auth["projected_post_ledger_sha256"] = "0" * 64
    bad_auth_path = root / "bad-auth-projected-sha.json"
    bad_auth_path.write_bytes(guard.pretty_json_bytes(bad_auth))
    expect_error(
        "authorization projected ledger SHA must match deterministic candidate",
        lambda: guard.prepare_transaction(
            authorization_path=bad_auth_path,
            packet_path=packet_path,
            ledger_path=guard.DEFAULT_LEDGER,
            context=context,
            require_tracked_authorization=False,
        ),
    )

    # Real production must reject untracked synthetic authorization.
    expect_error(
        "real production requires tracked current-HEAD authorization",
        lambda: guard.execute_transaction(
            authorization_path=authorization_path,
            packet_path=packet_path,
            ledger_path=guard.DEFAULT_LEDGER,
            receipt_root=guard.RECEIPT_ROOT,
            context=context,
            require_tracked_authorization=True,
        ),
    )

    final_real_checkpoint = guard.RECEIPT_ROOT / runtime["transaction_id"]
    assert not final_real_checkpoint.exists()
    assert guard.DEFAULT_LEDGER.read_bytes() == real_ledger_before
    print("PASS | untracked authorization cannot mutate real production")

    # Complete 25-event transaction on temporary production copies.
    temp_ledger = root / "temp-event-ledger.tsv"
    temp_ledger.write_bytes(real_ledger_before)
    temp_receipts = root / "temp-receipts"
    temp_receipts.mkdir()

    executed = guard.execute_transaction(
        authorization_path=authorization_path,
        packet_path=packet_path,
        ledger_path=temp_ledger,
        receipt_root=temp_receipts,
        context=context,
        require_tracked_authorization=False,
    )
    assert executed["status"] == "T000006_EXECUTION_COMPLETE"

    final_checkpoint = temp_receipts / "T000006"
    assert final_checkpoint.is_dir()
    assert {path.name for path in final_checkpoint.iterdir()} == {
        "authorization.json",
        "proposal.tsv",
        "receipt.json",
    }

    ledger_validation = appender.validate_current_ledger(
        ledger_path=temp_ledger,
        context=context["appender_context"],
    )
    assert ledger_validation["event_count"] == 47
    assert ledger_validation["derived_state_counts"] == {
        "awaiting_source_escalation": 25,
        "blocked_metadata": 484,
        "complete": 11,
        "ready": 94586,
    }

    checkpoint_validation = guard.validate_checkpoint(
        checkpoint_dir=final_checkpoint,
        ledger_path=temp_ledger,
        context=context,
    )
    assert checkpoint_validation["status"] == "T000006_CHECKPOINT_VALID"
    assert checkpoint_validation["new_event_count"] == 25

    print("PASS | temporary generic 25-event execution completes")
    print("PASS | exact three-file checkpoint created")
    print("PASS | temporary post-ledger validation passes")

    expect_error(
        "generic one-use replay prohibited",
        lambda: guard.execute_transaction(
            authorization_path=authorization_path,
            packet_path=packet_path,
            ledger_path=temp_ledger,
            receipt_root=temp_receipts,
            context=context,
            require_tracked_authorization=False,
        ),
    )

    # Recovery simulation after successful append but before checkpoint finish.
    recovery_ledger = root / "recovery-ledger.tsv"
    recovery_ledger.write_bytes(real_ledger_before)
    recovery_receipts = root / "recovery-receipts"
    recovery_receipts.mkdir()

    try:
        guard.execute_transaction(
            authorization_path=authorization_path,
            packet_path=packet_path,
            ledger_path=recovery_ledger,
            receipt_root=recovery_receipts,
            context=context,
            require_tracked_authorization=False,
            _test_fail_after_append=True,
        )
    except guard.RecoveryRequiredError:
        pass
    else:
        raise AssertionError("Expected generic recovery-required failure")

    recovery_validation = appender.validate_current_ledger(
        ledger_path=recovery_ledger,
        context=context["appender_context"],
    )
    assert recovery_validation["event_count"] == 47

    staged = [
        path
        for path in recovery_receipts.iterdir()
        if path.name.startswith(".T000006.tmp.")
    ]
    assert len(staged) == 1
    assert (staged[0] / "authorization.json").is_file()
    assert (staged[0] / "proposal.tsv").is_file()

    recovery_state = guard.detect_recovery_state(
        ledger_path=recovery_ledger,
        receipt_root=recovery_receipts,
        context=context,
    )
    assert recovery_state["status"] == "RECOVERY_REQUIRED"

    print("PASS | post-append checkpoint failure enters recovery state")
    print("PASS | staged recovery evidence preserved")

    expect_error(
        "recovery state blocks retry",
        lambda: guard.execute_transaction(
            authorization_path=authorization_path,
            packet_path=packet_path,
            ledger_path=recovery_ledger,
            receipt_root=recovery_receipts,
            context=context,
            require_tracked_authorization=False,
        ),
    )

assert guard.DEFAULT_LEDGER.read_bytes() == real_ledger_before
assert guard.DEFAULT_REVIEW_PACKET.read_bytes() == real_packet_before
assert not (guard.RECEIPT_ROOT / runtime["transaction_id"]).exists()

print("PASS | real production ledger remained unchanged throughout tests")
print("PASS | real review packet remained unchanged throughout tests")
print("PASS | real T000006 checkpoint remained absent throughout tests")
print("PASS | hostile generic post-pilot tranche-guard tests complete")
