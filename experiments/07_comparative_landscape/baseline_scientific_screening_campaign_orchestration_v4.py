#!/usr/bin/env python3
"""
Experiment 07 baseline scientific-screening campaign orchestration v4.

This implementation covers the non-production campaign review layer only.

It:
- validates a frozen campaign design;
- reconstructs each constituent frozen batch through guard v3;
- generates blank per-batch review packets;
- generates immutable pre-review snapshots;
- generates one combined campaign review bundle;
- validates a materialized review workspace.

It deliberately does NOT:
- construct live authorizations;
- project or append production events;
- call execute_transaction;
- mutate the production event ledger;
- create event-receipt checkpoints.

Live authorization/execution is a later gate after the campaign's
scientific decisions have been frozen.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

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

CANONICAL_REVIEW_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_review_work"
)

DEFAULT_DESIGN = (
    HERE
    / "baseline_scientific_screening_campaign_orchestration_v4_design.json"
)

GUARD_PATH = (
    HERE
    / "baseline_scientific_screening_tranche_guard_v3.py"
)

CAMPAIGN_ID = "C000001"

EXPECTED_BATCH_IDS = [
    "B000005",
    "B000006",
    "B000007",
    "B000008",
    "B000009",
]

EXPECTED_TRANSACTION_IDS = [
    "T000014",
    "T000015",
    "T000016",
    "T000017",
    "T000018",
]


class CampaignV4Error(RuntimeError):
    """Fail-closed campaign-orchestration error."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def event_count(path: Path) -> int:
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        count = sum(1 for _ in handle)

    if count < 1:
        raise CampaignV4Error(
            f"Ledger has no header: {path}"
        )

    return count - 1


def load_guard():
    spec = importlib.util.spec_from_file_location(
        "branchsnv_campaign_v4_guard",
        GUARD_PATH,
    )

    if spec is None or spec.loader is None:
        raise CampaignV4Error(
            "Unable to load tranche guard v3"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(module)

    return module


def load_design(
    path: Path = DEFAULT_DESIGN,
) -> dict[str, Any]:

    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(value, dict):
        raise CampaignV4Error(
            "Campaign design must be a JSON object"
        )

    return value


def _batch_plans(
    design: dict[str, Any],
) -> list[dict[str, Any]]:

    try:
        batches = design[
            "first_campaign"
        ][
            "batches"
        ]
    except (KeyError, TypeError) as exc:
        raise CampaignV4Error(
            "Campaign design lacks first_campaign.batches"
        ) from exc

    if not isinstance(batches, list):
        raise CampaignV4Error(
            "first_campaign.batches must be a list"
        )

    return batches


def validate_campaign_design(
    design: dict[str, Any],
) -> dict[str, Any]:

    if design.get("status") != (
        "FROZEN_PRE_IMPLEMENTATION"
    ):
        raise CampaignV4Error(
            "Unexpected campaign design status"
        )

    if design.get("design_id") != (
        "BASELINE_SCIENTIFIC_SCREENING_"
        "CAMPAIGN_ORCHESTRATION_V4"
    ):
        raise CampaignV4Error(
            "Unexpected campaign design ID"
        )

    first = design.get(
        "first_campaign"
    )

    if not isinstance(first, dict):
        raise CampaignV4Error(
            "Missing first_campaign"
        )

    expected_first = {
        "campaign_id":
            CAMPAIGN_ID,

        "batch_start":
            "B000005",

        "batch_end":
            "B000009",

        "transaction_start":
            "T000014",

        "transaction_end":
            "T000018",

        "record_count":
            2500,

        "pre_campaign_event_count":
            2011,

        "expected_event_count_if_all_five_initial_transactions_publish":
            4511,

        "global_active_index_start":
            2001,

        "global_active_index_end":
            4500,
    }

    for key, expected in expected_first.items():

        if first.get(key) != expected:
            raise CampaignV4Error(
                f"Campaign design mismatch for {key}: "
                f"{first.get(key)!r} != {expected!r}"
            )

    policy = design.get(
        "campaign_policy",
        {},
    )

    if policy.get(
        "initial_campaign_width_batches"
    ) != 5:
        raise CampaignV4Error(
            "Initial campaign width must be five batches"
        )

    if policy.get(
        "initial_campaign_capacity_records"
    ) != 2500:
        raise CampaignV4Error(
            "Initial campaign capacity must be 2500"
        )

    if policy.get(
        "campaign_width_auto_scaling"
    ) is not False:
        raise CampaignV4Error(
            "Automatic campaign scaling must remain disabled"
        )

    transaction_contract = design.get(
        "transaction_contract",
        {},
    )

    if transaction_contract.get(
        "cross_batch_transaction_permitted"
    ) is not False:
        raise CampaignV4Error(
            "Cross-batch transactions must remain prohibited"
        )

    if transaction_contract.get(
        "one_transaction_per_batch"
    ) is not True:
        raise CampaignV4Error(
            "One transaction per batch is required"
        )

    human = design.get(
        "human_gate_model",
        {},
    )

    if human.get(
        "required_explicit_human_gates_per_campaign"
    ) != [
        "APPROVE_CAMPAIGN_REVIEW",
        "AUTHORIZE_CAMPAIGN",
        "EXECUTE_CAMPAIGN",
    ]:
        raise CampaignV4Error(
            "Unexpected campaign human-gate model"
        )

    if human.get(
        "per_batch_human_gate_repetition_required"
    ) is not False:
        raise CampaignV4Error(
            "Per-batch human gate repetition must be disabled"
        )

    batches = _batch_plans(
        design
    )

    if len(batches) != 5:
        raise CampaignV4Error(
            "First campaign must contain exactly five batches"
        )

    if [
        row.get("batch_id")
        for row in batches
    ] != EXPECTED_BATCH_IDS:
        raise CampaignV4Error(
            "Unexpected campaign batch order"
        )

    if [
        row.get("transaction_id")
        for row in batches
    ] != EXPECTED_TRANSACTION_IDS:
        raise CampaignV4Error(
            "Unexpected campaign transaction order"
        )

    expected_globals = [
        (2001, 2500),
        (2501, 3000),
        (3001, 3500),
        (3501, 4000),
        (4001, 4500),
    ]

    expected_events = [
        ("E000002012", "E000002511"),
        ("E000002512", "E000003011"),
        ("E000003012", "E000003511"),
        ("E000003512", "E000004011"),
        ("E000004012", "E000004511"),
    ]

    guard = load_guard()

    all_entity_ids: list[str] = []

    for index, plan in enumerate(
        batches
    ):

        if plan.get(
            "record_count"
        ) != 500:
            raise CampaignV4Error(
                "Each initial campaign batch must contain 500 records"
            )

        if plan.get(
            "positions"
        ) != [1, 500]:
            raise CampaignV4Error(
                "Each initial campaign batch must target positions 1-500"
            )

        start, end = expected_globals[
            index
        ]

        if (
            plan.get("global_start"),
            plan.get("global_end"),
        ) != (
            start,
            end,
        ):
            raise CampaignV4Error(
                f"Global range mismatch for {plan.get('batch_id')}"
            )

        event_start, event_end = (
            expected_events[
                index
            ]
        )

        if (
            plan.get("event_start"),
            plan.get("event_end"),
        ) != (
            event_start,
            event_end,
        ):
            raise CampaignV4Error(
                f"Event range mismatch for {plan.get('batch_id')}"
            )

        if plan.get(
            "cross_batch_event_transaction_permitted"
        ) is not False:
            raise CampaignV4Error(
                "Batch plan permits a cross-batch transaction"
            )

        scope = guard.reconstruct_batch_scope(
            batch_id=plan["batch_id"],
            queue_path=QUEUE,
            execution_root=EXECUTION_ROOT,
        )

        if scope["count"] != 500:
            raise CampaignV4Error(
                f"{plan['batch_id']} is not a 500-record batch"
            )

        rows = scope[
            "membership_rows"
        ]

        positions = [
            int(
                row[
                    "position_in_batch"
                ]
            )
            for row in rows
        ]

        globals_ = [
            int(
                row[
                    "global_active_index"
                ]
            )
            for row in rows
        ]

        entity_ids = [
            row[
                "screening_entity_id"
            ]
            for row in rows
        ]

        if positions != list(
            range(1, 501)
        ):
            raise CampaignV4Error(
                f"Position ordering mismatch for {plan['batch_id']}"
            )

        if globals_ != list(
            range(
                start,
                end + 1,
            )
        ):
            raise CampaignV4Error(
                f"Global-index ordering mismatch for {plan['batch_id']}"
            )

        if len(
            set(entity_ids)
        ) != 500:
            raise CampaignV4Error(
                f"Duplicate entity in {plan['batch_id']}"
            )

        ordered_sha = sha256_bytes(
            "".join(
                entity_id + "\n"
                for entity_id
                in entity_ids
            ).encode("utf-8")
        )

        if ordered_sha != plan.get(
            "ordered_screening_entity_ids_sha256"
        ):
            raise CampaignV4Error(
                f"Frozen entity identity mismatch for {plan['batch_id']}"
            )

        all_entity_ids.extend(
            entity_ids
        )

    if len(
        all_entity_ids
    ) != 2500:
        raise CampaignV4Error(
            "Campaign does not reconstruct to 2500 records"
        )

    if len(
        set(all_entity_ids)
    ) != 2500:
        raise CampaignV4Error(
            "Entity identity overlaps between campaign batches"
        )

    campaign_sha = sha256_bytes(
        "".join(
            entity_id + "\n"
            for entity_id
            in all_entity_ids
        ).encode("utf-8")
    )

    if campaign_sha != first.get(
        "campaign_ordered_screening_entity_ids_sha256"
    ):
        raise CampaignV4Error(
            "Frozen campaign entity identity mismatch"
        )

    return {
        "campaign_id":
            CAMPAIGN_ID,

        "batch_count":
            5,

        "record_count":
            2500,

        "campaign_ordered_screening_entity_ids_sha256":
            campaign_sha,
    }


def validate_production_boundary(
    design: dict[str, Any],
) -> dict[str, Any]:

    expected = design.get(
        "production_state_at_design",
        {},
    )

    expected_sha = expected.get(
        "ledger_sha256"
    )

    expected_count = expected.get(
        "event_count"
    )

    if expected_sha != sha256_file(
        LEDGER
    ):
        raise CampaignV4Error(
            "Production ledger SHA differs from frozen campaign design"
        )

    if expected_count != event_count(
        LEDGER
    ):
        raise CampaignV4Error(
            "Production event count differs from frozen campaign design"
        )

    return {
        "ledger_sha256":
            expected_sha,

        "event_count":
            expected_count,
    }


def _plan_by_batch(
    design: dict[str, Any],
) -> dict[str, dict[str, Any]]:

    return {
        row["batch_id"]: row
        for row in _batch_plans(
            design
        )
    }


def blank_review_packet_bytes(
    *,
    batch_id: str,
    design: dict[str, Any],
) -> bytes:

    plans = _plan_by_batch(
        design
    )

    if batch_id not in plans:
        raise CampaignV4Error(
            f"Batch is outside campaign: {batch_id}"
        )

    guard = load_guard()

    payload = (
        guard.build_blank_batch_review_packet_bytes(
            batch_id=batch_id,
            queue_path=QUEUE,
            execution_root=EXECUTION_ROOT,
        )
    )

    fields, rows = (
        guard.parse_tsv_bytes(
            payload
        )
    )

    plan = plans[
        batch_id
    ]

    if len(rows) != plan[
        "record_count"
    ]:
        raise CampaignV4Error(
            f"Unexpected packet size for {batch_id}"
        )

    if [
        int(
            row[
                "position_in_batch"
            ]
        )
        for row in rows
    ] != list(
        range(1, 501)
    ):
        raise CampaignV4Error(
            f"Packet positions invalid for {batch_id}"
        )

    if [
        int(
            row[
                "global_active_index"
            ]
        )
        for row in rows
    ] != list(
        range(
            plan["global_start"],
            plan["global_end"] + 1,
        )
    ):
        raise CampaignV4Error(
            f"Packet global indices invalid for {batch_id}"
        )

    if any(
        row[
            "batch_id"
        ] != batch_id
        for row in rows
    ):
        raise CampaignV4Error(
            f"Packet contains another batch: {batch_id}"
        )

    if any(
        row[field]
        for row in rows
        for field
        in guard.PROPOSED_FIELDS
    ):
        raise CampaignV4Error(
            f"Pre-review packet is not blank: {batch_id}"
        )

    if not fields:
        raise CampaignV4Error(
            f"Packet lacks fields: {batch_id}"
        )

    return payload


def campaign_review_bundle_bytes(
    design: dict[str, Any],
) -> bytes:

    guard = load_guard()

    fieldnames: list[str] | None = None
    all_rows: list[dict[str, str]] = []

    for plan in _batch_plans(
        design
    ):

        payload = blank_review_packet_bytes(
            batch_id=plan[
                "batch_id"
            ],
            design=design,
        )

        fields, rows = (
            guard.parse_tsv_bytes(
                payload
            )
        )

        if fieldnames is None:
            fieldnames = list(
                fields
            )

        elif list(
            fields
        ) != fieldnames:
            raise CampaignV4Error(
                "Campaign review packets have inconsistent schemas"
            )

        all_rows.extend(
            rows
        )

    if fieldnames is None:
        raise CampaignV4Error(
            "Campaign contains no review rows"
        )

    if len(
        all_rows
    ) != 2500:
        raise CampaignV4Error(
            "Campaign review bundle must contain exactly 2500 rows"
        )

    if len({
        row[
            "screening_entity_id"
        ]
        for row
        in all_rows
    }) != 2500:
        raise CampaignV4Error(
            "Campaign review bundle contains duplicate entities"
        )

    if [
        int(
            row[
                "global_active_index"
            ]
        )
        for row in all_rows
    ] != list(
        range(
            2001,
            4501,
        )
    ):
        raise CampaignV4Error(
            "Campaign review bundle global order is invalid"
        )

    if any(
        row[field]
        for row in all_rows
        for field
        in guard.PROPOSED_FIELDS
    ):
        raise CampaignV4Error(
            "Campaign review bundle contains proposed decisions"
        )

    stream = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        stream,
        fieldnames=fieldnames,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )

    writer.writeheader()
    writer.writerows(
        all_rows
    )

    return stream.getvalue().encode(
        "utf-8"
    )


def planned_review_paths(
    *,
    design: dict[str, Any],
    review_root: Path,
    snapshot_root: Path,
) -> dict[str, Path]:

    result: dict[str, Path] = {}

    for plan in _batch_plans(
        design
    ):

        batch_id = plan[
            "batch_id"
        ]

        transaction_id = plan[
            "transaction_id"
        ]

        result[
            f"{batch_id}:review"
        ] = (
            review_root
            / batch_id
            / "review_packet.tsv"
        )

        result[
            f"{transaction_id}:snapshot"
        ] = (
            snapshot_root
            / (
                transaction_id.lower()
                + "_pre_review_packet.tsv"
            )
        )

    result[
        "campaign:bundle"
    ] = (
        review_root
        / CAMPAIGN_ID
        / "campaign_review_bundle.tsv"
    )

    return result


def materialize_review_workspace(
    *,
    design: dict[str, Any],
    review_root: Path,
    snapshot_root: Path,
    allow_write: bool = False,
) -> dict[str, Any]:

    if allow_write is not True:
        raise CampaignV4Error(
            "Review workspace write requires explicit allow_write=True"
        )

    validate_campaign_design(
        design
    )

    validate_production_boundary(
        design
    )

    paths = planned_review_paths(
        design=design,
        review_root=review_root,
        snapshot_root=snapshot_root,
    )

    existing = [
        str(path)
        for path
        in paths.values()
        if path.exists()
    ]

    if existing:
        raise CampaignV4Error(
            "Refusing to overwrite existing review artifact(s): "
            + ", ".join(
                existing
            )
        )

    payloads: dict[Path, bytes] = {}

    for plan in _batch_plans(
        design
    ):

        batch_id = plan[
            "batch_id"
        ]

        transaction_id = plan[
            "transaction_id"
        ]

        packet = blank_review_packet_bytes(
            batch_id=batch_id,
            design=design,
        )

        payloads[
            paths[
                f"{batch_id}:review"
            ]
        ] = packet

        payloads[
            paths[
                f"{transaction_id}:snapshot"
            ]
        ] = packet

    payloads[
        paths[
            "campaign:bundle"
        ]
    ] = campaign_review_bundle_bytes(
        design
    )

    temp_paths: list[
        tuple[Path, Path]
    ] = []

    try:

        for target, payload in payloads.items():

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temp = target.with_name(
                target.name
                + ".tmp-campaign-v4"
            )

            if temp.exists():
                raise CampaignV4Error(
                    f"Temporary path already exists: {temp}"
                )

            with temp.open(
                "xb"
            ) as handle:
                handle.write(
                    payload
                )

                handle.flush()
                os.fsync(
                    handle.fileno()
                )

            temp_paths.append(
                (
                    temp,
                    target,
                )
            )

        for temp, target in temp_paths:
            os.replace(
                temp,
                target,
            )

    except Exception:

        for temp, _ in temp_paths:
            if temp.exists():
                temp.unlink()

        raise

    validate_materialized_review_workspace(
        design=design,
        review_root=review_root,
        snapshot_root=snapshot_root,
    )

    return {
        "campaign_id":
            CAMPAIGN_ID,

        "review_packets":
            5,

        "snapshots":
            5,

        "bundle_rows":
            2500,

        "bundle_path":
            str(
                paths[
                    "campaign:bundle"
                ]
            ),

        "bundle_sha256":
            sha256_file(
                paths[
                    "campaign:bundle"
                ]
            ),
    }


def validate_materialized_review_workspace(
    *,
    design: dict[str, Any],
    review_root: Path,
    snapshot_root: Path,
) -> dict[str, Any]:

    validate_campaign_design(
        design
    )

    paths = planned_review_paths(
        design=design,
        review_root=review_root,
        snapshot_root=snapshot_root,
    )

    for plan in _batch_plans(
        design
    ):

        batch_id = plan[
            "batch_id"
        ]

        transaction_id = plan[
            "transaction_id"
        ]

        review_path = paths[
            f"{batch_id}:review"
        ]

        snapshot_path = paths[
            f"{transaction_id}:snapshot"
        ]

        if not review_path.is_file():
            raise CampaignV4Error(
                f"Missing review packet: {review_path}"
            )

        if not snapshot_path.is_file():
            raise CampaignV4Error(
                f"Missing pre-review snapshot: {snapshot_path}"
            )

        expected = blank_review_packet_bytes(
            batch_id=batch_id,
            design=design,
        )

        if review_path.read_bytes() != expected:
            raise CampaignV4Error(
                f"Canonical review packet differs from frozen source: {batch_id}"
            )

        if snapshot_path.read_bytes() != expected:
            raise CampaignV4Error(
                f"Pre-review snapshot differs from frozen source: {transaction_id}"
            )

        if (
            review_path.read_bytes()
            != snapshot_path.read_bytes()
        ):
            raise CampaignV4Error(
                f"Review/snapshot mismatch: {batch_id}"
            )

    bundle_path = paths[
        "campaign:bundle"
    ]

    expected_bundle = (
        campaign_review_bundle_bytes(
            design
        )
    )

    if not bundle_path.is_file():
        raise CampaignV4Error(
            f"Missing campaign review bundle: {bundle_path}"
        )

    if (
        bundle_path.read_bytes()
        != expected_bundle
    ):
        raise CampaignV4Error(
            "Campaign review bundle differs from deterministic reconstruction"
        )

    return {
        "campaign_id":
            CAMPAIGN_ID,

        "review_packets_valid":
            5,

        "pre_review_snapshots_valid":
            5,

        "bundle_rows":
            2500,

        "bundle_sha256":
            sha256_bytes(
                expected_bundle
            ),
    }


def _cli() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Experiment 07 baseline-screening campaign v4 "
            "non-production review controller"
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "inspect",
    )

    build = subparsers.add_parser(
        "build-review-workspace",
    )

    build.add_argument(
        "--allow-review-write",
        action="store_true",
    )

    subparsers.add_parser(
        "validate-review-workspace",
    )

    args = parser.parse_args()

    design = load_design()

    design_info = (
        validate_campaign_design(
            design
        )
    )

    production = (
        validate_production_boundary(
            design
        )
    )

    if args.command == "inspect":

        print(
            json.dumps(
                {
                    **design_info,
                    **production,
                    "status":
                        "CAMPAIGN_V4_REVIEW_LAYER_VALID",
                    "production_mutation_available":
                        False,
                },
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    if args.command == (
        "build-review-workspace"
    ):

        if not args.allow_review_write:
            raise CampaignV4Error(
                "--allow-review-write is required"
            )

        result = (
            materialize_review_workspace(
                design=design,
                review_root=CANONICAL_REVIEW_ROOT,
                snapshot_root=HERE,
                allow_write=True,
            )
        )

        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    if args.command == (
        "validate-review-workspace"
    ):

        result = (
            validate_materialized_review_workspace(
                design=design,
                review_root=CANONICAL_REVIEW_ROOT,
                snapshot_root=HERE,
            )
        )

        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    raise CampaignV4Error(
        f"Unhandled command: {args.command}"
    )


if __name__ == "__main__":
    raise SystemExit(
        _cli()
    )
