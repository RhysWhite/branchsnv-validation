#!/usr/bin/env python3

from pathlib import Path
import hashlib
import importlib.util

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

GUARD_PATH = HERE / "b000001_post_pilot_tranche_guard_v2.py"
V1_PATH = HERE / "b000001_post_pilot_tranche_guard.py"

DESIGN = HERE / "b000001_t000007_post_pilot_continuation_design.json"
SUMS = HERE / "b000001_t000007_post_pilot_continuation_design.sha256"
SNAPSHOT = HERE / "t000007_pre_review_packet.tsv"

OLD_DESIGN = HERE / "b000001_t000006_post_pilot_continuation_design.json"
OLD_SUMS = HERE / "b000001_t000006_post_pilot_continuation_design.sha256"

RESULTS = REPO / "results" / "07_comparative_landscape"
REVIEW = (
    RESULTS
    / "baseline_scientific_screening_review_work"
    / "B000001"
    / "review_packet.tsv"
)
LEDGER = (
    RESULTS
    / "baseline_scientific_screening_execution"
    / "event_ledger.tsv"
)
RECEIPTS = (
    RESULTS
    / "baseline_scientific_screening_event_receipts"
)

EXPECTED_V1_SHA = (
    "598c14c595a4bc5c1faff6c5411cae1b7fe898dbfeb5227a15d707d76fea6575"
)
EXPECTED_LEDGER_SHA = (
    "dd83022eff2d2b069b80a6db495c90991e823fad03ece61010484e6fa839525b"
)
EXPECTED_REVIEW_SHA = (
    "d49d162191ba4737aeaecbf0934130a7a8816ad203504b2603a709ceec8a8b7a"
)

assert hashlib.sha256(V1_PATH.read_bytes()).hexdigest() == EXPECTED_V1_SHA
print("PASS | generic guard v1 remains byte-exact")

spec = importlib.util.spec_from_file_location(
    "branchsnv_post_pilot_guard_v2_test",
    GUARD_PATH,
)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)

# Backward compatibility: old T000006 design still parses through v2.
old = guard.validate_design(
    design_path=OLD_DESIGN,
    design_sums_path=OLD_SUMS,
)
assert old["design_id"] == "B000001_T000006_POST_PILOT_CONTINUATION_DESIGN"
print("PASS | v2 remains backward-compatible with frozen T000006 design")

context = guard.load_context(
    design_path=DESIGN,
    design_sums_path=SUMS,
)

runtime = context["runtime"]

assert runtime["transaction_id"] == "T000007"
assert runtime["batch_id"] == "B000001"
assert runtime["positions"] == list(range(37, 87))
assert runtime["count"] == 50
assert runtime["pre_event_count"] == 47
assert runtime["post_event_count"] == 97
assert runtime["first_event_id"] == "E000000048"
assert runtime["last_event_id"] == "E000000097"

print("PASS | exact frozen T000007 target reconstructed")
print("PASS | expected event IDs E000000048-E000000097")

assert hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest() == EXPECTED_REVIEW_SHA
assert SNAPSHOT.read_bytes() == REVIEW.read_bytes()
print("PASS | pre-review snapshot exact")

rows = guard.validate_review_packet(
    packet_path=REVIEW,
    context=context,
    mode="pre_review",
)

assert len(rows) == 500

# Historical rows 1-36 are whatever the exact frozen snapshot records.
# Current target and future rows must be blank.
for position in range(37, 87):
    assert all(
        not rows[position - 1][field]
        for field in guard.PROPOSED_FIELDS
    )

for position in range(87, 501):
    assert all(
        not rows[position - 1][field]
        for field in guard.PROPOSED_FIELDS
    )

print("PASS | historical positions 1-36 locked to snapshot")
print("PASS | positions 37-86 proposal-blank")
print("PASS | positions 87-500 proposal-blank")

validation = guard.validate_pre_transaction_state(
    ledger_path=LEDGER,
    context=context,
)

assert validation["event_count"] == 47
assert validation["ledger_sha256"] == EXPECTED_LEDGER_SHA
assert validation["derived_state_counts"] == {
    "awaiting_source_escalation": 0,
    "blocked_metadata": 484,
    "complete": 36,
    "ready": 94586,
}

print("PASS | exact post-T000006 production state validated")

recovery = guard.detect_recovery_state(
    ledger_path=LEDGER,
    receipt_root=RECEIPTS,
    context=context,
)

assert recovery["status"] == "PRE_T000007_READY"
assert recovery["temporary_checkpoint_count"] == 0

print("PASS | T000007 recovery state PRE_T000007_READY")
print("PASS | no production mutation performed")
