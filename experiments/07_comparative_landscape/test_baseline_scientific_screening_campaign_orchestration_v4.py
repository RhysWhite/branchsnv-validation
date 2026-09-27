#!/usr/bin/env python3

from __future__ import annotations

import copy
import csv
import importlib.util
import io
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent

IMPLEMENTATION = (
    HERE
    / "baseline_scientific_screening_campaign_orchestration_v4.py"
)


def load_module():

    spec = importlib.util.spec_from_file_location(
        "branchsnv_campaign_v4_under_test",
        IMPLEMENTATION,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


campaign = load_module()

design = campaign.load_design()

pre_ledger_sha = campaign.sha256_file(
    campaign.LEDGER
)

pre_event_count = campaign.event_count(
    campaign.LEDGER
)


print("===== CAMPAIGN DESIGN / PRODUCTION BOUNDARY =====")

info = campaign.validate_campaign_design(
    design
)

assert info["campaign_id"] == "C000001"
assert info["batch_count"] == 5
assert info["record_count"] == 2500

boundary = (
    campaign.validate_production_boundary(
        design
    )
)

assert boundary["event_count"] == 2011

assert boundary["ledger_sha256"] == (
    "f7175d03bb559a8996e7a2fb1aba3959abab87429b86adbd19df74f0f0cbf45e"
)

print("PASS | frozen campaign design validates")
print("PASS | production boundary exact")
print("PASS | 5 batches / 2500 records")


print()
print("===== IN-MEMORY PACKET RECONSTRUCTION =====")

for batch_id in campaign.EXPECTED_BATCH_IDS:

    payload = (
        campaign.blank_review_packet_bytes(
            batch_id=batch_id,
            design=design,
        )
    )

    guard = campaign.load_guard()

    fields, rows = (
        guard.parse_tsv_bytes(
            payload
        )
    )

    assert len(rows) == 500

    assert all(
        row["batch_id"] == batch_id
        for row in rows
    )

    assert all(
        not row[field]
        for row in rows
        for field in guard.PROPOSED_FIELDS
    )

    print(
        f"PASS | {batch_id} blank packet = 500 rows"
    )

bundle = (
    campaign.campaign_review_bundle_bytes(
        design
    )
)

with io.StringIO(
    bundle.decode("utf-8")
) as handle:

    rows = list(
        csv.DictReader(
            handle,
            delimiter="\t",
        )
    )

assert len(rows) == 2500

assert [
    int(
        row[
            "global_active_index"
        ]
    )
    for row in rows
] == list(
    range(
        2001,
        4501,
    )
)

assert len({
    row[
        "screening_entity_id"
    ]
    for row in rows
}) == 2500

assert [
    row[
        "batch_id"
    ]
    for row in rows[
        0::500
    ]
] == campaign.EXPECTED_BATCH_IDS

print("PASS | combined campaign bundle = 2500 rows")
print("PASS | global indices = 2001-4500")
print("PASS | 2500 unique screening entities")


print()
print("===== TEMPORARY WORKSPACE MATERIALIZATION =====")

with tempfile.TemporaryDirectory(
    prefix="branchsnv-campaign-v4-"
) as temp_dir:

    root = Path(
        temp_dir
    )

    review_root = (
        root
        / "review"
    )

    snapshot_root = (
        root
        / "snapshots"
    )

    result = (
        campaign.materialize_review_workspace(
            design=design,
            review_root=review_root,
            snapshot_root=snapshot_root,
            allow_write=True,
        )
    )

    assert result[
        "review_packets"
    ] == 5

    assert result[
        "snapshots"
    ] == 5

    assert result[
        "bundle_rows"
    ] == 2500

    validation = (
        campaign.validate_materialized_review_workspace(
            design=design,
            review_root=review_root,
            snapshot_root=snapshot_root,
        )
    )

    assert validation[
        "review_packets_valid"
    ] == 5

    assert validation[
        "pre_review_snapshots_valid"
    ] == 5

    assert validation[
        "bundle_rows"
    ] == 2500

    print("PASS | temporary review workspace materialized")
    print("PASS | five packet/snapshot pairs byte-exact")
    print("PASS | combined bundle deterministic")

    try:
        campaign.materialize_review_workspace(
            design=design,
            review_root=review_root,
            snapshot_root=snapshot_root,
            allow_write=True,
        )
    except campaign.CampaignV4Error:
        pass
    else:
        raise AssertionError(
            "Existing review artifacts were overwritten"
        )

    print("PASS | overwrite attempt prohibited")


print()
print("===== WRITE-AUTHORITY BARRIER =====")

with tempfile.TemporaryDirectory(
    prefix="branchsnv-campaign-v4-auth-"
) as temp_dir:

    root = Path(
        temp_dir
    )

    try:
        campaign.materialize_review_workspace(
            design=design,
            review_root=root / "review",
            snapshot_root=root / "snapshots",
            allow_write=False,
        )
    except campaign.CampaignV4Error:
        pass
    else:
        raise AssertionError(
            "Workspace wrote without explicit authority"
        )

print("PASS | review write requires explicit authority")


print()
print("===== HOSTILE DESIGN TAMPERING =====")

tampered = copy.deepcopy(
    design
)

tampered[
    "campaign_policy"
][
    "initial_campaign_width_batches"
] = 6

try:
    campaign.validate_campaign_design(
        tampered
    )
except campaign.CampaignV4Error:
    pass
else:
    raise AssertionError(
        "Tampered campaign width accepted"
    )

print("PASS | campaign-width tampering rejected")


tampered = copy.deepcopy(
    design
)

tampered[
    "first_campaign"
][
    "batches"
][
    0
][
    "batch_id"
] = "B000006"

try:
    campaign.validate_campaign_design(
        tampered
    )
except campaign.CampaignV4Error:
    pass
else:
    raise AssertionError(
        "Tampered batch ordering accepted"
    )

print("PASS | batch-order tampering rejected")


tampered = copy.deepcopy(
    design
)

tampered[
    "first_campaign"
][
    "batches"
][
    2
][
    "event_start"
] = "E999999999"

try:
    campaign.validate_campaign_design(
        tampered
    )
except campaign.CampaignV4Error:
    pass
else:
    raise AssertionError(
        "Tampered event range accepted"
    )

print("PASS | event-range tampering rejected")


tampered = copy.deepcopy(
    design
)

tampered[
    "transaction_contract"
][
    "cross_batch_transaction_permitted"
] = True

try:
    campaign.validate_campaign_design(
        tampered
    )
except campaign.CampaignV4Error:
    pass
else:
    raise AssertionError(
        "Cross-batch transaction permission accepted"
    )

print("PASS | cross-batch transaction permission rejected")


print()
print("===== FINAL PARTIAL BATCH REGRESSION =====")

guard = campaign.load_guard()

scope = guard.reconstruct_batch_scope(
    batch_id="B000190",
    queue_path=campaign.QUEUE,
    execution_root=campaign.EXECUTION_ROOT,
)

assert scope["count"] == 122

payload = (
    guard.build_blank_batch_review_packet_bytes(
        batch_id="B000190",
        queue_path=campaign.QUEUE,
        execution_root=campaign.EXECUTION_ROOT,
    )
)

_, rows = guard.parse_tsv_bytes(
    payload
)

assert len(rows) == 122

print("PASS | B000190 remains 122 records")
print("PASS | final partial batch remains supported")


print()
print("===== PRODUCTION-MUTATION SURFACE AUDIT =====")

source = IMPLEMENTATION.read_text(
    encoding="utf-8"
)

for forbidden in (
    "execute_transaction(",
    "prepare_transaction_from_files(",
    "atomic_append",
    "event_ledger_mutation_authorized",
    "git commit",
    "subprocess.",
):
    assert forbidden not in source, forbidden

print("PASS | implementation exposes no transaction execution call")
print("PASS | implementation exposes no production append call")
print("PASS | implementation exposes no Git mutation call")


print()
print("===== CANONICAL CAMPAIGN PATHS REMAIN ABSENT =====")

for batch_id in campaign.EXPECTED_BATCH_IDS:

    assert not (
        campaign.CANONICAL_REVIEW_ROOT
        / batch_id
        / "review_packet.tsv"
    ).exists()

for transaction_id in campaign.EXPECTED_TRANSACTION_IDS:

    assert not (
        campaign.HERE
        / (
            transaction_id.lower()
            + "_pre_review_packet.tsv"
        )
    ).exists()

assert not (
    campaign.CANONICAL_REVIEW_ROOT
    / "C000001"
    / "campaign_review_bundle.tsv"
).exists()

print("PASS | tests created no canonical campaign review artifacts")


print()
print("===== PRODUCTION LEDGER BYTE-INTEGRITY =====")

assert campaign.sha256_file(
    campaign.LEDGER
) == pre_ledger_sha

assert campaign.event_count(
    campaign.LEDGER
) == pre_event_count

assert pre_event_count == 2011

print("PASS | production ledger remained byte-identical")
print("PASS | production event count remains 2011")

print()
print("PASS | CAMPAIGN V4 HOSTILE TESTS COMPLETE")
