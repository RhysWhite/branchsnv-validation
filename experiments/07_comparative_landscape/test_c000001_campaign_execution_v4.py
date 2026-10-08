from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent

LAYER_PATH = (
    HERE
    / "c000001_campaign_execution_v4.py"
)

EXPECTED_SOURCE_SHA = (
    "ce072594dd4112560233361c8da056756b2f649e2526dde13365cceffcc0eb86"
)

EXPECTED_PRODUCTION_SHA = (
    "f7175d03bb559a8996e7a2fb1aba3959abab87429b86adbd19df74f0f0cbf45e"
)

EXPECTED_T000013_IDENTITY_SHA = (
    "f1c80ca4a77abde62bb8c2f8a744eca0282265b6a129639155764fafe34b4b1f"
)

EXPECTED_TRANSACTIONS = [
    {
        "batch_id": "B000005",
        "transaction_id": "T000014",
        "pre_event_count": 2011,
        "post_event_count": 2511,
        "first_event_id": "E000002012",
        "last_event_id": "E000002511",
        "pre_ledger_sha256":
            "f7175d03bb559a8996e7a2fb1aba3959abab87429b86adbd19df74f0f0cbf45e",
        "projected_post_ledger_sha256":
            "8b377eee33858eb42946721946e632729d5267275c841a8d8cbf16fe21c5adcd",
        "proposal_sha256":
            "596de8ff20ee370609341824eabb53b4a92d74241163b5bf6890b27448dfbf6e",
        "canonical_target_identity_sha256":
            "68e2461d2657f6609c297a83332b0f3cf8daff4c9f82db8c53f41c6bac87f098",
        "projected_post_state_counts": {
            "ready": 92122,
            "awaiting_source_escalation": 0,
            "complete": 2500,
            "blocked_metadata": 484,
        },
    },
    {
        "batch_id": "B000006",
        "transaction_id": "T000015",
        "pre_event_count": 2511,
        "post_event_count": 3011,
        "first_event_id": "E000002512",
        "last_event_id": "E000003011",
        "pre_ledger_sha256":
            "8b377eee33858eb42946721946e632729d5267275c841a8d8cbf16fe21c5adcd",
        "projected_post_ledger_sha256":
            "1799a7fd9f5435f025bc064db34e2e9fffbb01aeea102144c6bdf11a58388332",
        "proposal_sha256":
            "e8d40bfd966e2d06b08c7e56aab6dce546cf27b277588fec07d78a5241287ffb",
        "canonical_target_identity_sha256":
            "b314877d63f4699e50dceb6b1dc98cc33dd7ab9a1b8c9a0ce2454ee60a958bf2",
        "projected_post_state_counts": {
            "ready": 91622,
            "awaiting_source_escalation": 0,
            "complete": 3000,
            "blocked_metadata": 484,
        },
    },
    {
        "batch_id": "B000007",
        "transaction_id": "T000016",
        "pre_event_count": 3011,
        "post_event_count": 3511,
        "first_event_id": "E000003012",
        "last_event_id": "E000003511",
        "pre_ledger_sha256":
            "1799a7fd9f5435f025bc064db34e2e9fffbb01aeea102144c6bdf11a58388332",
        "projected_post_ledger_sha256":
            "6a015b2e328cea4abde454caa282f4a74843b39e2d18232b26b070ded91156eb",
        "proposal_sha256":
            "607082831e490b98ec247026b415f7bdb5614c6816f242fa7c76617442d3c6e5",
        "canonical_target_identity_sha256":
            "c405621d175ac75234d66a4c0f9c34c2c556ad5c32182472a3f1948093dd305d",
        "projected_post_state_counts": {
            "ready": 91122,
            "awaiting_source_escalation": 0,
            "complete": 3500,
            "blocked_metadata": 484,
        },
    },
    {
        "batch_id": "B000008",
        "transaction_id": "T000017",
        "pre_event_count": 3511,
        "post_event_count": 4011,
        "first_event_id": "E000003512",
        "last_event_id": "E000004011",
        "pre_ledger_sha256":
            "6a015b2e328cea4abde454caa282f4a74843b39e2d18232b26b070ded91156eb",
        "projected_post_ledger_sha256":
            "eae722e1cf28ee215b03c84e4c756899772354a895d1683a6e21800434bf2c8a",
        "proposal_sha256":
            "cab86529055e17722f1cd35fb9821b13b8616e5b21ccea538e56e003afddde1a",
        "canonical_target_identity_sha256":
            "754f38f4ee526ddca2fe1033f0fb4891bcb2da7711f55b8bd2b918ce217dcd10",
        "projected_post_state_counts": {
            "ready": 90622,
            "awaiting_source_escalation": 0,
            "complete": 4000,
            "blocked_metadata": 484,
        },
    },
    {
        "batch_id": "B000009",
        "transaction_id": "T000018",
        "pre_event_count": 4011,
        "post_event_count": 4511,
        "first_event_id": "E000004012",
        "last_event_id": "E000004511",
        "pre_ledger_sha256":
            "eae722e1cf28ee215b03c84e4c756899772354a895d1683a6e21800434bf2c8a",
        "projected_post_ledger_sha256":
            "8ec90dec5a8a78e4bb2ab21df69ba7e3bdd94f66b6acf3eb8410fa7a49e14aaa",
        "proposal_sha256":
            "3c6d45337b95be9f9784ffbab06f5a1d8dece06503d06aadbaab7aab521f9c38",
        "canonical_target_identity_sha256":
            "7448c52882d9105a65f5098d953aef8f3b178a2baea3661a84bf51e22f2c5808",
        "projected_post_state_counts": {
            "ready": 90122,
            "awaiting_source_escalation": 0,
            "complete": 4500,
            "blocked_metadata": 484,
        },
    },
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def load_layer():
    spec = importlib.util.spec_from_file_location(
        "c000001_campaign_execution_v4_tested",
        LAYER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def test_execution_layer_source_is_frozen():
    assert sha256_file(LAYER_PATH) == EXPECTED_SOURCE_SHA


def test_t000013_identity_regression():
    m = load_layer()

    m.verify_identity_algorithm()

    guard = m.load_guard()

    identity = m.build_target_identity(
        guard=guard,
        batch_id="B000004",
    )

    assert (
        identity["canonical_target_identity_sha256"]
        == EXPECTED_T000013_IDENTITY_SHA
    )

    assert len(identity["entities"]) == 500


def test_c000001_scientific_freeze_exact():
    m = load_layer()

    result = m.validate_scientific_freeze()

    assert result["campaign_id"] == "C000001"
    assert result["record_count"] == 2500

    assert result["decision_counts"] == {
        "exclude": 2419,
        "record_decision": 2500,
        "retain_for_method_assessment": 81,
        "source_escalation": 0,
    }

    assert result["exclusion_reason_counts"] == {
        "application_only_no_reusable_method": 2419,
        "duplicate_record_same_method_no_distinct_capability": 0,
        "unrelated_variant_or_data_type": 0,
        "unsupported_by_primary_or_stable_authoritative_source": 0,
    }


def test_t000014_projection_is_exact_and_nonpublishing():
    m = load_layer()

    before = m.LEDGER.read_bytes()

    guard = m.load_guard()

    parent = m.validate_ledger_state(
        guard=guard,
        ledger_path=m.LEDGER,
    )

    design = m.build_tranche_design(
        guard=guard,
        batch_id="B000005",
        transaction_id="T000014",
        parent_commit=m.EXPECTED_IMPLEMENTATION_PARENT,
        parent_state=parent,
    )

    result = m.project_transaction_without_authorization(
        guard=guard,
        design=design,
        ledger_path=m.LEDGER,
        transaction_timestamp_utc="2026-09-27T05:00:00Z",
    )

    receipt = result["receipt"]

    assert result["proposal_sha256"] == (
        EXPECTED_TRANSACTIONS[0]["proposal_sha256"]
    )

    assert result["projected_post_ledger_sha256"] == (
        EXPECTED_TRANSACTIONS[0]["projected_post_ledger_sha256"]
    )

    assert receipt["pre_append_event_count"] == 2011
    assert receipt["post_append_event_count"] == 2511
    assert receipt["first_assigned_event_id"] == "E000002012"
    assert receipt["last_assigned_event_id"] == "E000002511"
    assert receipt["published"] is False
    assert receipt["strict_prefix_extension"] is True

    assert m.LEDGER.read_bytes() == before


def test_full_campaign_projection_exact_and_nonmutating():
    m = load_layer()

    before = m.LEDGER.read_bytes()

    result = m.project_campaign_without_authorization()

    assert result["production_before"] == {
        "ledger_sha256": EXPECTED_PRODUCTION_SHA,
        "event_count": 2011,
    }

    assert result["production_after"] == (
        result["production_before"]
    )

    assert len(result["transactions"]) == 5

    for observed, expected in zip(
        result["transactions"],
        EXPECTED_TRANSACTIONS,
        strict=True,
    ):
        for field in (
            "batch_id",
            "transaction_id",
            "pre_event_count",
            "post_event_count",
            "first_event_id",
            "last_event_id",
            "pre_ledger_sha256",
            "projected_post_ledger_sha256",
            "proposal_sha256",
            "canonical_target_identity_sha256",
            "projected_post_state_counts",
        ):
            assert observed[field] == expected[field]

    assert result["projected_final_state"] == {
        "awaiting_source_escalation": 0,
        "blocked_metadata": 484,
        "complete": 4500,
        "ready": 90122,
        "event_count": 4511,
        "ledger_sha256":
            "8ec90dec5a8a78e4bb2ab21df69ba7e3bdd94f66b6acf3eb8410fa7a49e14aaa",
    }

    assert m.LEDGER.read_bytes() == before


def test_no_c000001_live_artifacts_exist():
    m = load_layer()

    for spec in m.BATCHES:
        transaction_id = spec["transaction_id"]

        authorization = (
            m.HERE
            / (
                transaction_id.lower()
                + "_live_event_authorization.json"
            )
        )

        checkpoint = (
            m.CANONICAL_RECEIPT_ROOT
            / transaction_id
        )

        assert not authorization.exists()
        assert not checkpoint.exists()


def test_production_boundary_remains_frozen():
    m = load_layer()

    assert m.validate_production_boundary() == {
        "ledger_sha256": EXPECTED_PRODUCTION_SHA,
        "event_count": 2011,
    }
