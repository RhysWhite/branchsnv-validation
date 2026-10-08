#!/usr/bin/env python3

from pathlib import Path
import hashlib
import importlib.util

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

GUARD = (
    HERE
    / "baseline_scientific_screening_tranche_guard_v3.py"
)

V2 = (
    HERE
    / "b000001_post_pilot_tranche_guard_v2.py"
)

DESIGN = (
    HERE
    / "b000002_t000011_baseline_screening_tranche_design.json"
)

SUMS = (
    HERE
    / "b000002_t000011_baseline_screening_tranche_design.sha256"
)

SNAPSHOT = (
    HERE
    / "t000011_pre_review_packet.tsv"
)

RESULTS = (
    REPO
    / "results"
    / "07_comparative_landscape"
)

QUEUE = (
    RESULTS
    / "scientific_screening"
    / "baseline_screening_queue.tsv"
)

EXECUTION = (
    RESULTS
    / "baseline_scientific_screening_execution"
)

LEDGER = (
    EXECUTION
    / "event_ledger.tsv"
)

REVIEW = (
    RESULTS
    / "baseline_scientific_screening_review_work"
    / "B000002"
    / "review_packet.tsv"
)

RECEIPTS = (
    RESULTS
    / "baseline_scientific_screening_event_receipts"
)

EXPECTED_V2_SHA = (
    "68cc5c501f89a389a842e0bc716e58801b56188a7621a887dcc2c349a8427ba5"
)

EXPECTED_LEDGER_SHA = (
    "080b60b63c46524fe3f97d7db37ca56aba255e8633170b8f709f648ab11cd413"
)


assert hashlib.sha256(
    V2.read_bytes()
).hexdigest() == EXPECTED_V2_SHA

print("PASS | frozen v2 remains byte-exact")


spec = importlib.util.spec_from_file_location(
    "branchsnv_cross_batch_guard_v3_test",
    GUARD,
)

guard = importlib.util.module_from_spec(spec)

assert spec.loader is not None
spec.loader.exec_module(guard)


context = guard.load_context(
    design_path=DESIGN,
    design_sums_path=SUMS,
)

runtime = context["runtime"]

assert runtime["transaction_id"] == "T000011"
assert runtime["batch_id"] == "B000002"
assert runtime["positions"] == list(range(1, 501))
assert runtime["count"] == 500
assert runtime["pre_event_count"] == 511
assert runtime["post_event_count"] == 1011
assert runtime["first_event_id"] == "E000000512"
assert runtime["last_event_id"] == "E000001011"

assert context["batch_scope"]["count"] == 500
assert context["batch_scope"]["batch_id"] == "B000002"

assert guard.authorization_status(context) == (
    "AUTHORIZED_B000002_T000011_"
    "POSITIONS_1_TO_500_ONE_USE"
)

assert SNAPSHOT.read_bytes() == REVIEW.read_bytes()

rows = guard.validate_review_packet(
    packet_path=REVIEW,
    context=context,
    mode="pre_review",
)

assert len(rows) == 500

assert all(
    row["batch_id"] == "B000002"
    for row in rows
)

assert all(
    not row[field]
    for row in rows
    for field in guard.PROPOSED_FIELDS
)

validation = guard.validate_pre_transaction_state(
    ledger_path=LEDGER,
    context=context,
)

assert validation["event_count"] == 511
assert validation["ledger_sha256"] == EXPECTED_LEDGER_SHA

assert validation["derived_state_counts"] == {
    "awaiting_source_escalation": 0,
    "blocked_metadata": 484,
    "complete": 500,
    "ready": 94122,
}

recovery = guard.detect_recovery_state(
    ledger_path=LEDGER,
    receipt_root=RECEIPTS,
    context=context,
)

assert recovery["status"] == "PRE_T000011_READY"
assert recovery["temporary_checkpoint_count"] == 0

print("PASS | B000002 T000011 contract valid")
print("PASS | B000002 review packet = 500 rows")
print("PASS | authorization status batch-derived")
print("PASS | exact post-B000001 state validated")
print("PASS | PRE_T000011_READY")


final_scope = guard.reconstruct_batch_scope(
    batch_id="B000190",
    queue_path=QUEUE,
    execution_root=EXECUTION,
)

assert final_scope["count"] == 122

assert [
    int(row["position_in_batch"])
    for row in final_scope["membership_rows"]
] == list(range(1, 123))

final_packet = guard.build_blank_batch_review_packet_bytes(
    batch_id="B000190",
    queue_path=QUEUE,
    execution_root=EXECUTION,
)

_, final_rows = guard.parse_tsv_bytes(
    final_packet
)

assert len(final_rows) == 122

assert all(
    row["batch_id"] == "B000190"
    for row in final_rows
)

assert all(
    not row[field]
    for row in final_rows
    for field in guard.PROPOSED_FIELDS
)

print("PASS | B000190 dynamic batch size = 122")
print("PASS | B000190 blank packet = 122 rows")
print("PASS | v3 not dependent on 500-row batches")
print("PASS | no production mutation performed")
