#!/usr/bin/env python3

from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from typing import Any


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

RESULTS_ROOT = (
    REPO_ROOT
    / "results"
    / "07_comparative_landscape"
)

QUEUE = (
    RESULTS_ROOT
    / "scientific_screening"
    / "baseline_screening_queue.tsv"
)

EXECUTION_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_execution"
)

LEDGER = (
    EXECUTION_ROOT
    / "event_ledger.tsv"
)

REVIEW_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_review_work"
)

CANONICAL_RECEIPT_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_event_receipts"
)

GUARD_PATH = (
    HERE
    / "baseline_scientific_screening_tranche_guard_v3.py"
)

T13_DESIGN = (
    HERE
    / "b000004_t000013_baseline_screening_tranche_design.json"
)

CAMPAIGN_DESIGN = (
    HERE
    / "baseline_scientific_screening_campaign_orchestration_v4_design.json"
)

SCIENTIFIC_FREEZE = (
    HERE
    / "c000001_approved_scientific_decision_freeze.json"
)

EXPECTED_IMPLEMENTATION_PARENT = (
    "ffa0f368cd6de4bb76987d63ff598c992c2dcd35"
)

EXPECTED_PRODUCTION_LEDGER_SHA = (
    "f7175d03bb559a8996e7a2fb1aba3959abab87429b86adbd19df74f0f0cbf45e"
)

EXPECTED_PRODUCTION_EVENT_COUNT = 2011

OPERATOR_ID = "human-approved-c000001-review"
OPERATOR_TYPE = "human_with_assistance"

BATCHES = [
    {
        "batch_id": "B000005",
        "transaction_id": "T000014",
        "timestamp": "2026-09-27T05:00:00Z",
    },
    {
        "batch_id": "B000006",
        "transaction_id": "T000015",
        "timestamp": "2026-09-27T05:01:00Z",
    },
    {
        "batch_id": "B000007",
        "transaction_id": "T000016",
        "timestamp": "2026-09-27T05:02:00Z",
    },
    {
        "batch_id": "B000008",
        "transaction_id": "T000017",
        "timestamp": "2026-09-27T05:03:00Z",
    },
    {
        "batch_id": "B000009",
        "transaction_id": "T000018",
        "timestamp": "2026-09-27T05:04:00Z",
    },
]


class CampaignExecutionV4Error(RuntimeError):
    pass


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(
        name,
        path.resolve(),
    )

    if spec is None or spec.loader is None:
        raise CampaignExecutionV4Error(
            f"Unable to load module: {path}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def load_guard():
    return load_module(
        GUARD_PATH,
        "branchsnv_c000001_execution_guard",
    )


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(value, dict):
        raise CampaignExecutionV4Error(
            f"Expected JSON object: {path}"
        )

    return value


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def validate_production_boundary() -> dict[str, Any]:
    payload = LEDGER.read_bytes()

    observed_sha = sha256_bytes(payload)

    if observed_sha != EXPECTED_PRODUCTION_LEDGER_SHA:
        raise CampaignExecutionV4Error(
            "Production ledger SHA differs from frozen C000001 boundary"
        )

    event_count = len(payload.splitlines()) - 1

    if event_count != EXPECTED_PRODUCTION_EVENT_COUNT:
        raise CampaignExecutionV4Error(
            "Production event count differs from frozen C000001 boundary"
        )

    return {
        "ledger_sha256":
            observed_sha,

        "event_count":
            event_count,
    }


def build_target_identity(
    *,
    guard,
    batch_id: str,
) -> dict[str, Any]:

    membership_fields, membership = guard.read_tsv(
        EXECUTION_ROOT
        / "batch_membership.tsv"
    )

    queue_fields, queue = guard.read_tsv(
        QUEUE
    )

    target_membership = sorted(
        [
            row
            for row in membership
            if row["batch_id"] == batch_id
        ],
        key=lambda row: int(
            row["position_in_batch"]
        ),
    )

    if len(target_membership) != 500:
        raise CampaignExecutionV4Error(
            f"{batch_id} is not a 500-row campaign batch"
        )

    positions = [
        int(row["position_in_batch"])
        for row in target_membership
    ]

    if positions != list(range(1, 501)):
        raise CampaignExecutionV4Error(
            f"{batch_id} position ordering changed"
        )

    target_ids = [
        row["screening_entity_id"]
        for row in target_membership
    ]

    if len(set(target_ids)) != 500:
        raise CampaignExecutionV4Error(
            f"{batch_id} contains duplicate entities"
        )

    queue_by_id = {
        row["screening_entity_id"]: row
        for row in queue
    }

    target_queue = []
    identity_rows = []

    for membership_row in target_membership:

        entity_id = membership_row[
            "screening_entity_id"
        ]

        if entity_id not in queue_by_id:
            raise CampaignExecutionV4Error(
                f"{batch_id} entity missing from baseline queue"
            )

        qrow = queue_by_id[entity_id]

        if qrow["screening_state"] != "ready":
            raise CampaignExecutionV4Error(
                f"{batch_id} baseline entity is not frozen-ready"
            )

        target_queue.append(qrow)

        identity_rows.append({
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

    ordered_ids_sha = guard.sha256_bytes(
        "".join(
            entity_id + "\n"
            for entity_id in target_ids
        ).encode("utf-8")
    )

    membership_rows_sha = guard.sha256_bytes(
        guard.frozen_identity_tsv_bytes(
            fields=membership_fields,
            rows=target_membership,
        )
    )

    baseline_rows_sha = guard.sha256_bytes(
        guard.frozen_identity_tsv_bytes(
            fields=queue_fields,
            rows=target_queue,
        )
    )

    identity_core = {
        "batch_id":
            batch_id,

        "target_position_start":
            1,

        "target_position_end":
            500,

        "target_event_count":
            500,

        "ordered_entity_ids_sha256":
            ordered_ids_sha,

        "canonical_membership_rows_sha256":
            membership_rows_sha,

        "canonical_baseline_queue_rows_sha256":
            baseline_rows_sha,
    }

    identity_sha = guard.sha256_bytes(
        guard.canonical_json_bytes(
            identity_core
        )
    )

    return {
        **identity_core,

        "canonical_target_identity_sha256":
            identity_sha,

        "entities":
            identity_rows,
    }


def verify_identity_algorithm() -> None:

    guard = load_guard()

    frozen = load_json(
        T13_DESIGN
    )[
        "target_identity"
    ]

    reconstructed = build_target_identity(
        guard=guard,
        batch_id="B000004",
    )

    if reconstructed != frozen:
        raise CampaignExecutionV4Error(
            "Target-identity reconstruction does not reproduce frozen T000013"
        )


def review_packet_path(
    batch_id: str,
) -> Path:

    return (
        REVIEW_ROOT
        / batch_id
        / "review_packet.tsv"
    )


def proposal_path(
    batch_id: str,
    transaction_id: str,
) -> Path:

    return (
        REVIEW_ROOT
        / batch_id
        / (
            transaction_id
            + "_c000001_approved_decisions"
        )
        / "proposal.tsv"
    )


def decision_summary_path(
    batch_id: str,
    transaction_id: str,
) -> Path:

    return (
        REVIEW_ROOT
        / batch_id
        / (
            transaction_id
            + "_c000001_approved_decisions"
        )
        / "decision_summary.json"
    )


def snapshot_path(
    transaction_id: str,
) -> Path:

    return (
        HERE
        / (
            transaction_id.lower()
            + "_pre_review_packet.tsv"
        )
    )


def validate_scientific_freeze() -> dict[str, Any]:

    verify_identity_algorithm()

    guard = load_guard()
    freeze = load_json(
        SCIENTIFIC_FREEZE
    )

    if freeze.get("campaign_id") != "C000001":
        raise CampaignExecutionV4Error(
            "Unexpected scientific-freeze campaign ID"
        )

    if freeze.get("status") != (
        "FROZEN_APPROVED_CAMPAIGN_SCIENTIFIC_DECISIONS"
    ):
        raise CampaignExecutionV4Error(
            "C000001 scientific freeze is not in approved frozen state"
        )

    if freeze.get(
        "scientific_decisions_frozen_before_live_authorization"
    ) is not True:
        raise CampaignExecutionV4Error(
            "Scientific decisions are not marked frozen before authorization"
        )

    if freeze.get("live_authorization_created") is not False:
        raise CampaignExecutionV4Error(
            "C000001 freeze unexpectedly records live authorization"
        )

    if freeze.get("transaction_checkpoints_created") is not False:
        raise CampaignExecutionV4Error(
            "C000001 freeze unexpectedly records transaction checkpoints"
        )

    frozen_batches = freeze.get("batches")

    if not isinstance(frozen_batches, list):
        raise CampaignExecutionV4Error(
            "C000001 batches must be a list"
        )

    if len(frozen_batches) != len(BATCHES):
        raise CampaignExecutionV4Error(
            "C000001 frozen batch count differs from execution definition"
        )

    expected_pairs = [
        (
            spec["batch_id"],
            spec["transaction_id"],
        )
        for spec in BATCHES
    ]

    frozen_pairs = [
        (
            item.get("batch_id"),
            item.get("transaction_id"),
        )
        for item in frozen_batches
        if isinstance(item, dict)
    ]

    if frozen_pairs != expected_pairs:
        raise CampaignExecutionV4Error(
            "Frozen C000001 batch/transaction ordering changed"
        )

    global_decisions: Counter[str] = Counter()
    global_exclusion_reasons: Counter[str] = Counter()

    validated_batches = []
    total_records = 0

    for spec, frozen_batch in zip(
        BATCHES,
        frozen_batches,
        strict=True,
    ):

        if not isinstance(frozen_batch, dict):
            raise CampaignExecutionV4Error(
                "Malformed C000001 batch entry"
            )

        batch_id = spec["batch_id"]
        transaction_id = spec["transaction_id"]

        packet = review_packet_path(
            batch_id
        )

        proposal = proposal_path(
            batch_id,
            transaction_id,
        )

        summary = decision_summary_path(
            batch_id,
            transaction_id,
        )

        snapshot = snapshot_path(
            transaction_id
        )

        for path in (
            packet,
            proposal,
            summary,
            snapshot,
        ):
            if not path.is_file():
                raise CampaignExecutionV4Error(
                    f"Missing frozen C000001 artifact: {path}"
                )

        observed_packet_sha = sha256_file(
            packet
        )

        observed_proposal_sha = sha256_file(
            proposal
        )

        observed_summary_sha = sha256_file(
            summary
        )

        if observed_packet_sha != frozen_batch.get(
            "review_packet_sha256"
        ):
            raise CampaignExecutionV4Error(
                f"{batch_id} review-packet SHA differs from C000001 freeze"
            )

        if observed_proposal_sha != frozen_batch.get(
            "proposal_sha256"
        ):
            raise CampaignExecutionV4Error(
                f"{batch_id} proposal SHA differs from C000001 freeze"
            )

        if observed_summary_sha != frozen_batch.get(
            "decision_summary_sha256"
        ):
            raise CampaignExecutionV4Error(
                f"{batch_id} decision-summary SHA differs from C000001 freeze"
            )

        identity = build_target_identity(
            guard=guard,
            batch_id=batch_id,
        )

        identity_ids = [
            row["screening_entity_id"]
            for row in identity["entities"]
        ]

        packet_fields, packet_rows = guard.read_tsv(
            packet
        )

        if len(packet_rows) != 500:
            raise CampaignExecutionV4Error(
                f"{batch_id} review packet does not contain 500 records"
            )

        if "screening_entity_id" in packet_fields:

            packet_ids = [
                row["screening_entity_id"]
                for row in packet_rows
            ]

            if packet_ids != identity_ids:
                raise CampaignExecutionV4Error(
                    f"{batch_id} review packet does not match target identity"
                )

        proposal_fields, proposal_rows = guard.read_tsv(
            proposal
        )

        required_proposal_fields = {
            "screening_entity_id",
            "batch_id",
            "event_type",
            "record_decision",
            "exclusion_reason_code",
            "candidate_method_flag",
            "operator_id",
            "operator_type",
        }

        missing_fields = (
            required_proposal_fields
            - set(proposal_fields)
        )

        if missing_fields:
            raise CampaignExecutionV4Error(
                f"{batch_id} proposal missing fields: "
                + ", ".join(sorted(missing_fields))
            )

        if len(proposal_rows) != 500:
            raise CampaignExecutionV4Error(
                f"{batch_id} proposal does not contain 500 records"
            )

        proposal_ids = [
            row["screening_entity_id"]
            for row in proposal_rows
        ]

        if proposal_ids != identity_ids:
            raise CampaignExecutionV4Error(
                f"{batch_id} approved proposal ordering differs from target identity"
            )

        if len(set(proposal_ids)) != 500:
            raise CampaignExecutionV4Error(
                f"{batch_id} proposal contains duplicate entities"
            )

        for row in proposal_rows:

            if row["batch_id"] != batch_id:
                raise CampaignExecutionV4Error(
                    f"{batch_id} proposal contains incorrect batch ID"
                )

            if row["event_type"] != "record_decision":
                raise CampaignExecutionV4Error(
                    f"{batch_id} proposal contains unexpected event type"
                )

            if row["operator_id"] != OPERATOR_ID:
                raise CampaignExecutionV4Error(
                    f"{batch_id} proposal operator ID changed"
                )

            if row["operator_type"] != OPERATOR_TYPE:
                raise CampaignExecutionV4Error(
                    f"{batch_id} proposal operator type changed"
                )

            decision = row["record_decision"]

            if decision not in {
                "retain_for_method_assessment",
                "exclude",
            }:
                raise CampaignExecutionV4Error(
                    f"{batch_id} proposal contains unsupported decision: "
                    f"{decision!r}"
                )

            if decision == "retain_for_method_assessment":

                if row["candidate_method_flag"] != "true":
                    raise CampaignExecutionV4Error(
                        f"{batch_id} retained method-assessment record "
                        "does not carry candidate_method_flag=true"
                    )

                if row["exclusion_reason_code"]:
                    raise CampaignExecutionV4Error(
                        f"{batch_id} retained method-assessment record "
                        "unexpectedly carries an exclusion reason"
                    )

            elif decision == "exclude":

                if row["candidate_method_flag"] != "false":
                    raise CampaignExecutionV4Error(
                        f"{batch_id} excluded record "
                        "does not carry candidate_method_flag=false"
                    )

                if not row["exclusion_reason_code"]:
                    raise CampaignExecutionV4Error(
                        f"{batch_id} excluded record "
                        "is missing its exclusion reason"
                    )

        decision_counts = Counter(
            row["record_decision"]
            for row in proposal_rows
        )

        retain_positions = [
            index
            for index, row in enumerate(
                proposal_rows,
                start=1,
            )
            if row["record_decision"] == "retain_for_method_assessment"
        ]

        retain_count = decision_counts[
            "retain_for_method_assessment"
        ]

        exclude_count = decision_counts[
            "exclude"
        ]

        if retain_count + exclude_count != 500:
            raise CampaignExecutionV4Error(
                f"{batch_id} scientific decisions do not total 500"
            )

        if retain_count != frozen_batch.get(
            "retain_count"
        ):
            raise CampaignExecutionV4Error(
                f"{batch_id} retain count differs from C000001 freeze"
            )

        if exclude_count != frozen_batch.get(
            "exclude_count"
        ):
            raise CampaignExecutionV4Error(
                f"{batch_id} exclude count differs from C000001 freeze"
            )

        frozen_retain_positions = frozen_batch.get(
            "retain_positions"
        )

        if retain_positions != frozen_retain_positions:
            raise CampaignExecutionV4Error(
                f"{batch_id} retained positions differ from C000001 freeze"
            )

        if frozen_batch.get("record_count") != 500:
            raise CampaignExecutionV4Error(
                f"{batch_id} frozen record count is not 500"
            )

        global_decisions.update(
            row["event_type"]
            for row in proposal_rows
        )

        global_decisions.update(
            decision_counts
        )

        global_exclusion_reasons.update(
            row["exclusion_reason_code"]
            for row in proposal_rows
            if (
                row["record_decision"] == "exclude"
                and row["exclusion_reason_code"]
            )
        )

        total_records += len(
            proposal_rows
        )

        validated_batches.append({
            "batch_id":
                batch_id,

            "transaction_id":
                transaction_id,

            "record_count":
                len(proposal_rows),

            "retain_count":
                retain_count,

            "exclude_count":
                exclude_count,

            "canonical_target_identity_sha256":
                identity[
                    "canonical_target_identity_sha256"
                ],

            "review_packet_sha256":
                observed_packet_sha,

            "proposal_sha256":
                observed_proposal_sha,

            "decision_summary_sha256":
                observed_summary_sha,
        })

    if total_records != freeze.get(
        "campaign_record_count"
    ):
        raise CampaignExecutionV4Error(
            "C000001 campaign record count differs from frozen campaign"
        )

    if total_records != 2500:
        raise CampaignExecutionV4Error(
            "C000001 campaign does not contain exactly 2500 records"
        )

    frozen_decision_counts = freeze.get(
        "decision_counts"
    )

    if not isinstance(
        frozen_decision_counts,
        dict,
    ):
        raise CampaignExecutionV4Error(
            "Malformed frozen campaign decision counts"
        )

    decision_keys = (
        set(global_decisions)
        | set(frozen_decision_counts)
    )

    normalized_decision_counts = {
        key:
            global_decisions.get(key, 0)
        for key in sorted(decision_keys)
    }

    normalized_frozen_decision_counts = {
        key:
            frozen_decision_counts.get(key, 0)
        for key in sorted(decision_keys)
    }

    if (
        normalized_decision_counts
        != normalized_frozen_decision_counts
    ):
        raise CampaignExecutionV4Error(
            "Campaign decision counts differ from C000001 freeze"
        )

    frozen_exclusion_counts = freeze.get(
        "exclusion_reason_counts"
    )

    if not isinstance(
        frozen_exclusion_counts,
        dict,
    ):
        raise CampaignExecutionV4Error(
            "Malformed frozen exclusion-reason counts"
        )

    exclusion_keys = (
        set(global_exclusion_reasons)
        | set(frozen_exclusion_counts)
    )

    normalized_exclusion_counts = {
        key:
            global_exclusion_reasons.get(key, 0)
        for key in sorted(exclusion_keys)
    }

    normalized_frozen_exclusion_counts = {
        key:
            frozen_exclusion_counts.get(key, 0)
        for key in sorted(exclusion_keys)
    }

    if (
        normalized_exclusion_counts
        != normalized_frozen_exclusion_counts
    ):
        raise CampaignExecutionV4Error(
            "Campaign exclusion-reason counts differ from C000001 freeze"
        )

    return {
        "campaign_id":
            "C000001",

        "record_count":
            total_records,

        "decision_counts":
            normalized_decision_counts,

        "exclusion_reason_counts":
            normalized_exclusion_counts,

        "batches":
            validated_batches,
    }


def validate_ledger_state(
    *,
    guard,
    ledger_path: Path,
) -> dict[str, Any]:

    base_guard = guard.load_base_guard()

    base_context = base_guard.load_guard_context(
        queue_path=QUEUE.resolve(),
        execution_root=EXECUTION_ROOT.resolve(),
    )

    validation = base_context[
        "appender"
    ].validate_current_ledger(
        ledger_path=Path(ledger_path).resolve(),
        context=base_context[
            "appender_context"
        ],
    )

    counts = validation[
        "derived_state_counts"
    ]

    return {
        "awaiting_source_escalation":
            counts["awaiting_source_escalation"],

        "blocked_metadata":
            counts["blocked_metadata"],

        "complete":
            counts["complete"],

        "ready":
            counts["ready"],

        "event_count":
            validation["event_count"],

        "ledger_sha256":
            validation["ledger_sha256"],
    }


def build_tranche_design(
    *,
    guard,
    batch_id: str,
    transaction_id: str,
    parent_commit: str,
    parent_state: dict[str, Any],
) -> dict[str, Any]:

    pre_event_count = int(
        parent_state["event_count"]
    )

    pre_ledger_sha256 = str(
        parent_state["ledger_sha256"]
    )

    post_event_count = (
        pre_event_count
        + 500
    )

    snapshot = snapshot_path(
        transaction_id
    )

    if not snapshot.is_file():
        raise CampaignExecutionV4Error(
            f"Missing frozen pre-review snapshot: {snapshot}"
        )

    snapshot_bytes = snapshot.read_bytes()

    target_identity = build_target_identity(
        guard=guard,
        batch_id=batch_id,
    )

    transaction_key = (
        transaction_id.lower()
    )

    design = {
        "schema_version":
            1,

        "status":
            "FROZEN_PRE_IMPLEMENTATION",

        "design_id":
            (
                f"{batch_id}_{transaction_id}_"
                "BASELINE_SCREENING_TRANCHE_DESIGN"
            ),

        "parent_commit":
            parent_commit,

        "purpose":
            (
                "Define a v3-compatible whole-batch execution boundary "
                f"for {batch_id}/{transaction_id} under the frozen "
                "C000001 scientific campaign decisions. This design "
                "freezes identity and operational boundaries only and "
                "creates no live production authority."
            ),

        "continuation_strategy": {
            "automatic_scaling":
                False,

            "further_tranche_authority":
                False,

            "post_transaction_reconciliation_required":
                True,

            "strategy":
                "campaign_v4_sequential_whole_batch_execution",
        },

        "authority_separation": {
            "design_itself_creates_no_authority":
                True,

            "live_authorization_must_be_separately_tracked":
                True,

            "live_authorization_must_pin_exact_event_ids":
                True,

            "live_authorization_must_pin_exact_target_identity":
                True,

            "live_authorization_must_pin_expected_pre_event_count":
                True,

            "live_authorization_must_pin_expected_pre_ledger_sha256":
                True,

            "live_authorization_must_pin_fixed_transaction_timestamp":
                True,

            "live_authorization_must_pin_projected_post_ledger_sha256":
                True,

            "live_authorization_must_pin_proposal_sha256":
                True,

            "live_authorization_one_use":
                True,

            "no_intervening_tracked_commit_between_live_authorization_and_execution":
                True,

            "review_stage_must_precede_live_authorization":
                True,

            "review_work_and_live_production_authority_separate":
                True,

            "scientific_proposal_must_be_frozen_before_live_authorization":
                True,
        },

        "parent_production_state": {
            "awaiting_source_escalation":
                parent_state[
                    "awaiting_source_escalation"
                ],

            "blocked_metadata":
                parent_state[
                    "blocked_metadata"
                ],

            "complete":
                parent_state[
                    "complete"
                ],

            "event_count":
                pre_event_count,

            "ledger_sha256":
                pre_ledger_sha256,

            "ready":
                parent_state[
                    "ready"
                ],
        },

        "review_packet_contract": {
            "future_position_end":
                500,

            "future_position_start":
                501,

            "future_positions_blank_before_review":
                True,

            "historical_position_end":
                0,

            "historical_position_start":
                1,

            "historical_positions_locked_to_pre_review_snapshot":
                True,

            "model_preclassification":
                False,

            "path":
                (
                    "results/07_comparative_landscape/"
                    "baseline_scientific_screening_review_work/"
                    f"{batch_id}/review_packet.tsv"
                ),

            "pre_tranche_bytes":
                len(snapshot_bytes),

            "pre_tranche_sha256":
                sha256_bytes(
                    snapshot_bytes
                ),

            "software_preclassification":
                False,

            "target_position_end":
                500,

            "target_position_start":
                1,

            "target_positions_blank_before_review":
                True,
        },

        "checkpoint_contract": {
            "append_success_checkpoint_failure_requires_recovery":
                True,

            "exact_three_file_checkpoint":
                True,

            "final_files": [
                "authorization.json",
                "proposal.tsv",
                "receipt.json",
            ],

            "final_transaction_directory":
                (
                    "results/07_comparative_landscape/"
                    "baseline_scientific_screening_event_receipts/"
                    f"{transaction_id}"
                ),

            "retry_after_partial_completion":
                False,

            "rollback_after_successful_append":
                False,

            "root":
                (
                    "results/07_comparative_landscape/"
                    "baseline_scientific_screening_event_receipts"
                ),

            "transaction_id":
                transaction_id,
        },

        "next_gate":
            (
                f"CREATE_SEPARATELY_TRACKED_{transaction_id}_"
                "LIVE_AUTHORIZATION"
            ),

        transaction_key: {
            "batch_id":
                batch_id,

            "expected_first_event_id":
                guard.event_id(
                    pre_event_count + 1
                ),

            "expected_last_event_id":
                guard.event_id(
                    post_event_count
                ),

            "expected_post_event_count":
                post_event_count,

            "expected_pre_event_count":
                pre_event_count,

            "expected_pre_ledger_sha256":
                pre_ledger_sha256,

            "initial_events_only":
                True,

            "live_authorized_by_this_design":
                False,

            "partial_transaction_permitted":
                False,

            "review_packet_edit_authorized_by_this_design":
                False,

            "scientific_decisions_preselected":
                False,

            "superseding_events_permitted":
                False,

            "target_event_count":
                500,

            "target_positions":
                list(range(1, 501)),

            "transaction_id":
                transaction_id,
        },

        "target_identity":
            target_identity,
    }

    return design


def project_transaction_without_authorization(
    *,
    guard,
    design: dict[str, Any],
    ledger_path: Path,
    transaction_timestamp_utc: str,
) -> dict[str, Any]:

    runtime = guard.design_runtime(
        design
    )

    batch_id = runtime["batch_id"]
    transaction_id = runtime[
        "transaction_id"
    ]

    with tempfile.TemporaryDirectory(
        prefix=(
            "branchsnv-c000001-"
            + transaction_id.lower()
            + "-design-"
        )
    ) as tmp:

        tmp_root = Path(tmp)

        design_path = (
            tmp_root
            / (
                batch_id.lower()
                + "_"
                + transaction_id.lower()
                + "_baseline_screening_tranche_design.json"
            )
        )

        sums_path = (
            design_path.with_suffix(
                ".sha256"
            )
        )

        design_path.write_bytes(
            pretty_json_bytes(
                design
            )
        )

        design_sha = sha256_file(
            design_path
        )

        sums_path.write_text(
            (
                design_sha
                + "  "
                + str(design_path.resolve())
                + "\n"
            ),
            encoding="utf-8",
        )

        context = guard.load_context(
            design_path=design_path,
            design_sums_path=sums_path,
            queue_path=QUEUE,
            execution_root=EXECUTION_ROOT,
        )

        packet = review_packet_path(
            batch_id
        )

        frozen_proposal = proposal_path(
            batch_id,
            transaction_id,
        )

        extracted_proposal_bytes = (
            guard.extract_proposal_bytes(
                packet_path=packet,
                operator_id=OPERATOR_ID,
                operator_type=OPERATOR_TYPE,
                context=context,
            )
        )

        frozen_proposal_bytes = (
            frozen_proposal.read_bytes()
        )

        if (
            extracted_proposal_bytes
            != frozen_proposal_bytes
        ):
            raise CampaignExecutionV4Error(
                f"{transaction_id} regenerated proposal "
                "is not byte-identical to frozen C000001 proposal"
            )

        prepared = context[
            "appender"
        ].prepare_transaction_from_files(
            ledger_path=Path(
                ledger_path
            ).resolve(),
            proposal_path=frozen_proposal,
            expected_pre_ledger_sha256=runtime[
                "pre_ledger_sha256"
            ],
            context=context[
                "appender_context"
            ],
            transaction_timestamp_utc=
                transaction_timestamp_utc,
        )

        receipt = dict(
            prepared["receipt"]
        )

        if receipt[
            "batch_id"
        ] != batch_id:
            raise CampaignExecutionV4Error(
                f"{transaction_id} prepared batch changed"
            )

        if receipt[
            "new_event_count"
        ] != 500:
            raise CampaignExecutionV4Error(
                f"{transaction_id} prepared event count changed"
            )

        if receipt[
            "pre_append_event_count"
        ] != runtime[
            "pre_event_count"
        ]:
            raise CampaignExecutionV4Error(
                f"{transaction_id} prepared pre-event count changed"
            )

        if receipt[
            "post_append_event_count"
        ] != runtime[
            "post_event_count"
        ]:
            raise CampaignExecutionV4Error(
                f"{transaction_id} prepared post-event count changed"
            )

        if receipt[
            "first_assigned_event_id"
        ] != runtime[
            "first_event_id"
        ]:
            raise CampaignExecutionV4Error(
                f"{transaction_id} first event ID changed"
            )

        if receipt[
            "last_assigned_event_id"
        ] != runtime[
            "last_event_id"
        ]:
            raise CampaignExecutionV4Error(
                f"{transaction_id} last event ID changed"
            )

        if receipt[
            "published"
        ] is not False:
            raise CampaignExecutionV4Error(
                f"{transaction_id} dry-run unexpectedly published"
            )

        if receipt[
            "strict_prefix_extension"
        ] is not True:
            raise CampaignExecutionV4Error(
                f"{transaction_id} candidate is not a strict prefix extension"
            )

        candidate_bytes = prepared[
            "candidate_bytes"
        ]

        projected_sha = sha256_bytes(
            candidate_bytes
        )

        if receipt[
            "post_append_ledger_sha256"
        ] != projected_sha:
            raise CampaignExecutionV4Error(
                f"{transaction_id} receipt/candidate SHA mismatch"
            )

        return {
            "design":
                design,

            "design_sha256":
                design_sha,

            "proposal_sha256":
                sha256_bytes(
                    frozen_proposal_bytes
                ),

            "candidate_bytes":
                candidate_bytes,

            "projected_post_ledger_sha256":
                projected_sha,

            "projected_post_state_counts":
                receipt[
                    "derived_state_counts_after_append"
                ],

            "receipt":
                receipt,
        }


def project_campaign_without_authorization() -> dict[str, Any]:

    guard = load_guard()

    scientific = validate_scientific_freeze()

    production_before = (
        validate_production_boundary()
    )

    frozen_batches = {
        batch["batch_id"]: batch
        for batch in load_json(
            SCIENTIFIC_FREEZE
        )["batches"]
    }

    projections = []

    with tempfile.TemporaryDirectory(
        prefix="branchsnv-c000001-campaign-dryrun-"
    ) as tmp:

        tmp_root = Path(tmp)

        projected_ledger = (
            tmp_root
            / "event_ledger.tsv"
        )

        production_bytes = (
            LEDGER.read_bytes()
        )

        projected_ledger.write_bytes(
            production_bytes
        )

        if (
            projected_ledger.resolve()
            == LEDGER.resolve()
        ):
            raise CampaignExecutionV4Error(
                "Campaign projection ledger unexpectedly resolves "
                "to production ledger"
            )

        parent_state = validate_ledger_state(
            guard=guard,
            ledger_path=projected_ledger,
        )

        if parent_state != {
            "awaiting_source_escalation":
                0,

            "blocked_metadata":
                484,

            "complete":
                2000,

            "ready":
                92622,

            "event_count":
                EXPECTED_PRODUCTION_EVENT_COUNT,

            "ledger_sha256":
                EXPECTED_PRODUCTION_LEDGER_SHA,
        }:
            raise CampaignExecutionV4Error(
                "Temporary campaign ledger does not begin at "
                "the frozen C000001 production boundary"
            )

        for index, spec in enumerate(
            BATCHES,
            start=1,
        ):

            batch_id = spec[
                "batch_id"
            ]

            transaction_id = spec[
                "transaction_id"
            ]

            timestamp = spec[
                "timestamp"
            ]

            frozen_batch = frozen_batches[
                batch_id
            ]

            pre_bytes = (
                projected_ledger.read_bytes()
            )

            observed_pre_sha = (
                sha256_bytes(
                    pre_bytes
                )
            )

            if (
                observed_pre_sha
                != parent_state[
                    "ledger_sha256"
                ]
            ):
                raise CampaignExecutionV4Error(
                    f"{transaction_id} temporary "
                    "pre-ledger SHA changed"
                )

            design = build_tranche_design(
                guard=guard,
                batch_id=batch_id,
                transaction_id=transaction_id,
                parent_commit=
                    EXPECTED_IMPLEMENTATION_PARENT,
                parent_state=parent_state,
            )

            runtime = guard.design_runtime(
                design
            )

            if (
                runtime["pre_event_count"]
                != parent_state[
                    "event_count"
                ]
            ):
                raise CampaignExecutionV4Error(
                    f"{transaction_id} pre-event "
                    "count is not chained"
                )

            if (
                runtime["pre_ledger_sha256"]
                != parent_state[
                    "ledger_sha256"
                ]
            ):
                raise CampaignExecutionV4Error(
                    f"{transaction_id} pre-ledger "
                    "SHA is not chained"
                )

            projection = (
                project_transaction_without_authorization(
                    guard=guard,
                    design=design,
                    ledger_path=
                        projected_ledger,
                    transaction_timestamp_utc=
                        timestamp,
                )
            )

            if (
                projection[
                    "proposal_sha256"
                ]
                != frozen_batch[
                    "proposal_sha256"
                ]
            ):
                raise CampaignExecutionV4Error(
                    f"{transaction_id} proposal "
                    "SHA differs from scientific freeze"
                )

            candidate_bytes = projection[
                "candidate_bytes"
            ]

            if not candidate_bytes.startswith(
                pre_bytes
            ):
                raise CampaignExecutionV4Error(
                    f"{transaction_id} candidate "
                    "is not byte-prefix extension "
                    "of its projected parent ledger"
                )

            projected_sha = (
                sha256_bytes(
                    candidate_bytes
                )
            )

            if (
                projected_sha
                != projection[
                    "projected_post_ledger_sha256"
                ]
            ):
                raise CampaignExecutionV4Error(
                    f"{transaction_id} candidate "
                    "SHA changed after projection"
                )

            projected_ledger.write_bytes(
                candidate_bytes
            )

            observed_post = (
                validate_ledger_state(
                    guard=guard,
                    ledger_path=
                        projected_ledger,
                )
            )

            if (
                observed_post[
                    "ledger_sha256"
                ]
                != projected_sha
            ):
                raise CampaignExecutionV4Error(
                    f"{transaction_id} projected "
                    "ledger SHA failed revalidation"
                )

            if (
                observed_post[
                    "event_count"
                ]
                != runtime[
                    "post_event_count"
                ]
            ):
                raise CampaignExecutionV4Error(
                    f"{transaction_id} projected "
                    "event count failed revalidation"
                )

            projected_counts = {
                "ready":
                    observed_post[
                        "ready"
                    ],

                "awaiting_source_escalation":
                    observed_post[
                        "awaiting_source_escalation"
                    ],

                "complete":
                    observed_post[
                        "complete"
                    ],

                "blocked_metadata":
                    observed_post[
                        "blocked_metadata"
                    ],
            }

            if (
                projected_counts
                != projection[
                    "projected_post_state_counts"
                ]
            ):
                raise CampaignExecutionV4Error(
                    f"{transaction_id} projected "
                    "state counts failed revalidation"
                )

            if (
                projection[
                    "receipt"
                ]["published"]
                is not False
            ):
                raise CampaignExecutionV4Error(
                    f"{transaction_id} campaign "
                    "projection unexpectedly published"
                )

            if (
                sha256_file(
                    LEDGER
                )
                != EXPECTED_PRODUCTION_LEDGER_SHA
            ):
                raise CampaignExecutionV4Error(
                    "Real production ledger changed "
                    "during campaign projection"
                )

            projections.append({
                "sequence":
                    index,

                "batch_id":
                    batch_id,

                "transaction_id":
                    transaction_id,

                "timestamp":
                    timestamp,

                "design_sha256":
                    projection[
                        "design_sha256"
                    ],

                "proposal_sha256":
                    projection[
                        "proposal_sha256"
                    ],

                "canonical_target_identity_sha256":
                    design[
                        "target_identity"
                    ][
                        "canonical_target_identity_sha256"
                    ],

                "pre_event_count":
                    runtime[
                        "pre_event_count"
                    ],

                "post_event_count":
                    runtime[
                        "post_event_count"
                    ],

                "first_event_id":
                    runtime[
                        "first_event_id"
                    ],

                "last_event_id":
                    runtime[
                        "last_event_id"
                    ],

                "pre_ledger_sha256":
                    runtime[
                        "pre_ledger_sha256"
                    ],

                "projected_post_ledger_sha256":
                    projected_sha,

                "projected_post_state_counts":
                    projected_counts,
            })

            parent_state = (
                observed_post
            )

        final_state = dict(
            parent_state
        )

    production_after = (
        validate_production_boundary()
    )

    if (
        production_after
        != production_before
    ):
        raise CampaignExecutionV4Error(
            "Production boundary changed during "
            "campaign projection"
        )

    if len(projections) != 5:
        raise CampaignExecutionV4Error(
            "Campaign projection did not contain "
            "exactly five transactions"
        )

    if final_state[
        "event_count"
    ] != 4511:
        raise CampaignExecutionV4Error(
            "Projected campaign does not end at "
            "4511 events"
        )

    if final_state[
        "complete"
    ] != 4500:
        raise CampaignExecutionV4Error(
            "Projected campaign complete-state "
            "count is not 4500"
        )

    if final_state[
        "ready"
    ] != 90122:
        raise CampaignExecutionV4Error(
            "Projected campaign ready-state "
            "count is not 90122"
        )

    if final_state[
        "blocked_metadata"
    ] != 484:
        raise CampaignExecutionV4Error(
            "Projected campaign blocked-metadata "
            "count changed"
        )

    if final_state[
        "awaiting_source_escalation"
    ] != 0:
        raise CampaignExecutionV4Error(
            "Projected campaign unexpectedly "
            "contains source-escalation state"
        )

    return {
        "campaign_id":
            scientific[
                "campaign_id"
            ],

        "production_before":
            production_before,

        "transactions":
            projections,

        "projected_final_state":
            final_state,

        "production_after":
            production_after,
    }
