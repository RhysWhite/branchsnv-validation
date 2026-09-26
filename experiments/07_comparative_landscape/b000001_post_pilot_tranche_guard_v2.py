#!/usr/bin/env python3

"""Generic Experiment 07 B000001 post-pilot tranche guard.

Consumes a separately frozen post-pilot tranche design and provides fail-closed
validation, deterministic proposal extraction, dry-run projection, tracked
one-use authorization validation, crash-safe checkpointing, replay protection,
and recovery-state detection.

The guard is tranche-generic: transaction identity, position scope, target
hashes, event IDs, pre-ledger state, checkpoint path, and review-packet boundary
are read from the frozen design rather than hard-coded for T000006.

This module does NOT:
- edit the review packet;
- make scientific decisions;
- create a live authorization;
- preselect scientific outcomes; or
- mutate the real production ledger without a separately tracked one-use
  authorization satisfying the frozen tranche design.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

RESULTS_ROOT = REPO_ROOT / "results" / "07_comparative_landscape"
SCREENING_ROOT = RESULTS_ROOT / "scientific_screening"
EXECUTION_ROOT = RESULTS_ROOT / "baseline_scientific_screening_execution"
RECEIPT_ROOT = RESULTS_ROOT / "baseline_scientific_screening_event_receipts"
REVIEW_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_review_work"
    / "B000001"
)

DEFAULT_QUEUE = SCREENING_ROOT / "baseline_screening_queue.tsv"
DEFAULT_LEDGER = EXECUTION_ROOT / "event_ledger.tsv"
DEFAULT_REVIEW_PACKET = REVIEW_ROOT / "review_packet.tsv"

DEFAULT_TRANCHE_DESIGN = (
    HERE / "b000001_t000006_post_pilot_continuation_design.json"
)
DEFAULT_TRANCHE_DESIGN_SUMS = (
    HERE / "b000001_t000006_post_pilot_continuation_design.sha256"
)

BASE_GUARD_SOURCE = (
    HERE / "b000001_live_event_entry_authorization_guard.py"
)

PROPOSED_FIELDS = [
    "proposed_event_type",
    "proposed_record_decision",
    "proposed_exclusion_reason_code",
    "proposed_candidate_method_flag",
    "proposed_evidence_basis",
    "proposed_evidence_source_locator",
    "proposed_evidence_escalation_status",
    "proposed_notes",
]

PROPOSAL_MAPPING = {
    "proposed_event_type": "event_type",
    "proposed_record_decision": "record_decision",
    "proposed_exclusion_reason_code": "exclusion_reason_code",
    "proposed_candidate_method_flag": "candidate_method_flag",
    "proposed_evidence_basis": "evidence_basis",
    "proposed_evidence_source_locator": "evidence_source_locator",
    "proposed_evidence_escalation_status": "evidence_escalation_status",
    "proposed_notes": "notes",
}

AUTHORIZATION_FIELDS = {
    "status",
    "schema_version",
    "parent_commit",
    "tranche_design_freeze_sha256",
    "post_pilot_tranche_guard_sha256",
    "event_appender_implementation_sha256",
    "event_appender_implementation_freeze_sha256",
    "event_entry_design_freeze_sha256",
    "target_identity",
    "batch_id",
    "authorized_positions",
    "expected_pre_ledger_sha256",
    "expected_pre_event_count",
    "authorized_event_count",
    "expected_assigned_event_ids",
    "operator_id",
    "operator_type",
    "permitted_initial_event_types",
    "receipt_checkpoint_contract",
    "positions_outside_target_authorized",
    "partial_transaction_permitted",
    "one_use",
    "proposal_sha256",
    "scientific_decisions_frozen_before_authorization",
    "authorization_does_not_modify_scientific_decisions",
    "transaction_timestamp_utc",
    "projected_post_ledger_sha256",
    "projected_post_state_counts",
    "event_ledger_mutation_authorized",
    "review_packet_mutation_authorized",
    "human_approval_text",
}

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
TRANSACTION_RE = re.compile(r"^T[0-9]{6}$")
EVENT_ID_RE = re.compile(r"^E[0-9]{9}$")


class TrancheGuardError(RuntimeError):
    pass


class RecoveryRequiredError(TrancheGuardError):
    pass


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def tsv_bytes(
    *,
    fields: list[str],
    rows: list[dict[str, str]],
) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(
        handle,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


def frozen_identity_tsv_bytes(
    *,
    fields: list[str],
    rows: list[dict[str, str]],
) -> bytes:
    """Reproduce the exact row-hashing serialization used by the frozen design.

    The T000006 design freeze hashed header/rows by literal tab-joining the
    already-parsed field values, rather than by re-encoding them through
    csv.DictWriter (which may add CSV quoting around embedded quote
    characters). This helper is deliberately restricted to frozen target
    identity reconstruction; proposal TSV generation continues to use the
    normal csv writer above.
    """
    lines = ["\t".join(fields)]
    for row in rows:
        extra = set(row) - set(fields)
        if extra:
            raise TrancheGuardError(
                "Frozen identity row contains unexpected fields: "
                + ", ".join(sorted(extra))
            )
        lines.append("\t".join(row[field] for field in fields))
    return ("\n".join(lines) + "\n").encode("utf-8")


def git(*args: str, cwd: Path = REPO_ROOT) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout


def load_base_guard():
    module_name = "b000001_base_guard_for_post_pilot_tranche"
    spec = importlib.util.spec_from_file_location(
        module_name,
        BASE_GUARD_SOURCE,
    )
    if spec is None or spec.loader is None:
        raise TrancheGuardError(
            "Unable to load frozen B000001 base guard"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def manifest_expected_sha(
    manifest_path: Path,
    target_path: Path,
) -> str:
    manifest_path = Path(manifest_path)
    target_path = Path(target_path)
    matches: list[str] = []
    for raw in manifest_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            expected, recorded = raw.split(None, 1)
        except ValueError as exc:
            raise TrancheGuardError(
                "Malformed tranche design checksum manifest"
            ) from exc
        recorded = recorded.strip()
        if recorded.startswith("*"):
            recorded = recorded[1:]
        if recorded == str(target_path) or recorded.endswith(
            "/" + target_path.name
        ):
            matches.append(expected)
    if len(matches) != 1:
        raise TrancheGuardError(
            "Tranche design manifest does not uniquely pin design JSON"
        )
    return matches[0]


def default_design_sums_for(design_path: Path) -> Path:
    design_path = Path(design_path)
    if design_path.resolve() == DEFAULT_TRANCHE_DESIGN.resolve():
        return DEFAULT_TRANCHE_DESIGN_SUMS
    candidate = design_path.with_suffix(".sha256")
    if not candidate.is_file():
        raise TrancheGuardError(
            "No tranche design checksum manifest supplied or inferable"
        )
    return candidate


def event_id(number: int) -> str:
    if number < 1:
        raise TrancheGuardError("Event number must be positive")
    return f"E{number:09d}"


def design_runtime(design: dict) -> dict:
    t = design["t000006"] if "t000006" in design else None
    if t is None:
        candidates = [
            value
            for key, value in design.items()
            if key.startswith("t")
            and len(key) == 7
            and isinstance(value, dict)
            and "transaction_id" in value
        ]
        if len(candidates) != 1:
            raise TrancheGuardError(
                "Unable to identify unique tranche transaction block"
            )
        t = candidates[0]

    transaction_id = t["transaction_id"]
    if not TRANSACTION_RE.fullmatch(transaction_id):
        raise TrancheGuardError("Malformed tranche transaction ID")

    positions = t["target_positions"]
    if not isinstance(positions, list) or not positions:
        raise TrancheGuardError("Tranche target positions missing")
    if any(type(value) is not int for value in positions):
        raise TrancheGuardError("Tranche target positions must be integers")
    if positions != list(range(positions[0], positions[-1] + 1)):
        raise TrancheGuardError("Tranche target positions must be contiguous")

    count = len(positions)
    if t["target_event_count"] != count:
        raise TrancheGuardError("Tranche target count mismatch")

    pre_count = t["expected_pre_event_count"]
    post_count = t["expected_post_event_count"]
    if post_count != pre_count + count:
        raise TrancheGuardError("Tranche event-count arithmetic changed")

    first_event = event_id(pre_count + 1)
    last_event = event_id(post_count)
    if t["expected_first_event_id"] != first_event:
        raise TrancheGuardError("Tranche first event ID mismatch")
    if t["expected_last_event_id"] != last_event:
        raise TrancheGuardError("Tranche last event ID mismatch")

    expected_ids = [
        event_id(value)
        for value in range(pre_count + 1, post_count + 1)
    ]

    return {
        "transaction_id": transaction_id,
        "batch_id": t["batch_id"],
        "positions": positions,
        "start": positions[0],
        "end": positions[-1],
        "count": count,
        "pre_event_count": pre_count,
        "post_event_count": post_count,
        "pre_ledger_sha256": t["expected_pre_ledger_sha256"],
        "first_event_id": first_event,
        "last_event_id": last_event,
        "expected_event_ids": expected_ids,
        "checkpoint_dir": (
            RECEIPT_ROOT / transaction_id
        ),
    }


def validate_design(
    *,
    design_path: Path,
    design_sums_path: Path,
) -> dict:
    design_path = Path(design_path)
    design_sums_path = Path(design_sums_path)

    if not design_path.is_file():
        raise TrancheGuardError("Tranche design JSON missing")
    if not design_sums_path.is_file():
        raise TrancheGuardError("Tranche design checksum manifest missing")

    expected_design_sha = manifest_expected_sha(
        design_sums_path,
        design_path,
    )
    if sha256_file(design_path) != expected_design_sha:
        raise TrancheGuardError("Tranche design JSON SHA mismatch")

    value = json.loads(design_path.read_text(encoding="utf-8"))

    if value.get("schema_version") != 1:
        raise TrancheGuardError("Tranche design schema version changed")
    if value.get("status") != "FROZEN_PRE_IMPLEMENTATION":
        raise TrancheGuardError("Tranche design status changed")
    if not str(value.get("design_id", "")).startswith(
        "B000001_"
    ) or not str(value["design_id"]).endswith(
        "_POST_PILOT_CONTINUATION_DESIGN"
    ):
        raise TrancheGuardError("Tranche design identity changed")

    parent = value.get("parent_commit", "")
    if not COMMIT_RE.fullmatch(parent):
        raise TrancheGuardError("Tranche design parent commit malformed")

    runtime = design_runtime(value)
    transaction_key = runtime["transaction_id"].lower()
    t = value.get(transaction_key)
    if (
        not isinstance(t, dict)
        or t.get("transaction_id") != runtime["transaction_id"]
    ):
        raise TrancheGuardError("Tranche transaction block missing")

    if runtime["batch_id"] != "B000001":
        raise TrancheGuardError("Generic guard currently supports B000001 only")
    if t.get("partial_transaction_permitted") is not False:
        raise TrancheGuardError("Partial tranche execution unexpectedly permitted")
    if t.get("initial_events_only") is not True:
        raise TrancheGuardError("Post-pilot tranche must use initial events only")
    if t.get("superseding_events_permitted") is not False:
        raise TrancheGuardError("Superseding events unexpectedly permitted")
    if t.get("scientific_decisions_preselected") is not False:
        raise TrancheGuardError("Scientific decisions unexpectedly preselected")
    if t.get("live_authorized_by_this_design") is not False:
        raise TrancheGuardError("Design unexpectedly grants live authority")
    if t.get("review_packet_edit_authorized_by_this_design") is not False:
        raise TrancheGuardError("Design unexpectedly grants review mutation")

    strategy = value.get("continuation_strategy", {})
    if strategy.get("automatic_scaling") is not False:
        raise TrancheGuardError("Automatic tranche scaling unexpectedly permitted")
    if strategy.get("further_tranche_authority") is not False:
        raise TrancheGuardError("Design unexpectedly grants future tranche authority")

    authority = value.get("authority_separation", {})
    required_true = [
        "design_itself_creates_no_authority",
        "review_work_and_live_production_authority_separate",
        "review_stage_must_precede_live_authorization",
        "scientific_proposal_must_be_frozen_before_live_authorization",
        "live_authorization_must_be_separately_tracked",
        "live_authorization_one_use",
        "live_authorization_must_pin_exact_target_identity",
        "live_authorization_must_pin_proposal_sha256",
        "live_authorization_must_pin_expected_pre_ledger_sha256",
        "live_authorization_must_pin_expected_pre_event_count",
        "live_authorization_must_pin_exact_event_ids",
        "live_authorization_must_pin_fixed_transaction_timestamp",
        "live_authorization_must_pin_projected_post_ledger_sha256",
        "no_intervening_tracked_commit_between_live_authorization_and_execution",
    ]
    for key in required_true:
        if authority.get(key) is not True:
            raise TrancheGuardError(
                f"Required authority-separation invariant changed: {key}"
            )

    review_contract = value.get("review_packet_contract", {})

    # Backward compatibility: the original T000006 design froze the true
    # historical fact that positions 12-500 were blank at that gate.
    legacy_initial_blank_contract = (
        review_contract.get("positions_12_to_500_currently_blank") is True
    )

    # Subsequent tranches use the genuinely generic contract: historical
    # proposal state is locked to the tranche's frozen pre-review snapshot,
    # the current target is blank before review, and all future positions
    # remain blank.
    generic_snapshot_contract = (
        review_contract.get(
            "historical_positions_locked_to_pre_review_snapshot"
        ) is True
        and review_contract.get(
            "target_positions_blank_before_review"
        ) is True
        and review_contract.get(
            "future_positions_blank_before_review"
        ) is True
    )

    if not (
        legacy_initial_blank_contract
        or generic_snapshot_contract
    ):
        raise TrancheGuardError(
            "Tranche review-packet boundary contract invalid"
        )

    if review_contract.get("software_preclassification") is not False:
        raise TrancheGuardError("Software preclassification unexpectedly permitted")
    if review_contract.get("model_preclassification") is not False:
        raise TrancheGuardError("Model preclassification unexpectedly permitted")

    checkpoint = value.get("checkpoint_contract", {})
    if checkpoint.get("transaction_id") != runtime["transaction_id"]:
        raise TrancheGuardError("Checkpoint transaction ID changed")
    if checkpoint.get("exact_three_file_checkpoint") is not True:
        raise TrancheGuardError("Three-file checkpoint requirement changed")
    if checkpoint.get("final_files") != [
        "authorization.json",
        "proposal.tsv",
        "receipt.json",
    ]:
        raise TrancheGuardError("Checkpoint artifact contract changed")
    if checkpoint.get("rollback_after_successful_append") is not False:
        raise TrancheGuardError("Rollback after append unexpectedly permitted")
    if checkpoint.get("retry_after_partial_completion") is not False:
        raise TrancheGuardError("Retry after partial completion unexpectedly permitted")

    identity = value.get("target_identity", {})
    if identity.get("target_event_count") != runtime["count"]:
        raise TrancheGuardError("Target identity count changed")
    if identity.get("target_position_start") != runtime["start"]:
        raise TrancheGuardError("Target identity start changed")
    if identity.get("target_position_end") != runtime["end"]:
        raise TrancheGuardError("Target identity end changed")
    if len(identity.get("entities", [])) != runtime["count"]:
        raise TrancheGuardError("Target entity list count changed")

    parent_state = value.get("parent_production_state", {})
    if parent_state.get("event_count") != runtime["pre_event_count"]:
        raise TrancheGuardError("Parent event count changed")
    if parent_state.get("ledger_sha256") != runtime["pre_ledger_sha256"]:
        raise TrancheGuardError("Parent ledger SHA changed")

    return value


def identity_summary(design: dict) -> dict:
    identity = design["target_identity"]
    return {
        "entity_count": identity["target_event_count"],
        "target_position_start": identity["target_position_start"],
        "target_position_end": identity["target_position_end"],
        "ordered_entity_ids_sha256": identity[
            "ordered_entity_ids_sha256"
        ],
        "canonical_membership_rows_sha256": identity[
            "canonical_membership_rows_sha256"
        ],
        "canonical_baseline_queue_rows_sha256": identity[
            "canonical_baseline_queue_rows_sha256"
        ],
        "canonical_target_identity_sha256": identity[
            "canonical_target_identity_sha256"
        ],
    }


def reconstruct_target(
    *,
    context: dict,
) -> dict:
    design = context["design"]
    runtime = context["runtime"]

    membership_fields, membership = read_tsv(
        context["execution_root"] / "batch_membership.tsv"
    )
    queue_fields, queue = read_tsv(context["queue_path"])

    target_membership = sorted(
        [
            row
            for row in membership
            if row["batch_id"] == runtime["batch_id"]
            and int(row["position_in_batch"]) in runtime["positions"]
        ],
        key=lambda row: int(row["position_in_batch"]),
    )

    if len(target_membership) != runtime["count"]:
        raise TrancheGuardError("Target membership count mismatch")
    if [
        int(row["position_in_batch"])
        for row in target_membership
    ] != runtime["positions"]:
        raise TrancheGuardError("Target membership ordering changed")

    target_ids = [
        row["screening_entity_id"]
        for row in target_membership
    ]
    if len(set(target_ids)) != runtime["count"]:
        raise TrancheGuardError("Duplicate target entity")

    queue_by_id = {
        row["screening_entity_id"]: row
        for row in queue
    }

    target_queue = []
    target_identity_rows = []
    for membership_row in target_membership:
        entity_id = membership_row["screening_entity_id"]
        if entity_id not in queue_by_id:
            raise TrancheGuardError("Target missing from baseline queue")
        qrow = queue_by_id[entity_id]
        if qrow["screening_state"] != "ready":
            raise TrancheGuardError(
                "Target entity not frozen baseline-ready"
            )
        target_queue.append(qrow)
        target_identity_rows.append({
            "position_in_batch": int(membership_row["position_in_batch"]),
            "global_active_index": int(membership_row["global_active_index"]),
            "screening_entity_id": entity_id,
            "baseline_row_sha256": membership_row["baseline_row_sha256"],
            "title_or_software_name": qrow["title_or_software_name"],
            "year": qrow["year"],
            "doi": qrow["doi"],
            "pmid": qrow["pmid"],
        })

    ordered_ids_sha = sha256_bytes(
        "".join(entity + "\n" for entity in target_ids).encode("utf-8")
    )
    membership_rows_sha = sha256_bytes(
        frozen_identity_tsv_bytes(
            fields=membership_fields,
            rows=target_membership,
        )
    )
    baseline_rows_sha = sha256_bytes(
        frozen_identity_tsv_bytes(
            fields=queue_fields,
            rows=target_queue,
        )
    )

    identity_core = {
        "batch_id": runtime["batch_id"],
        "target_position_start": runtime["start"],
        "target_position_end": runtime["end"],
        "target_event_count": runtime["count"],
        "ordered_entity_ids_sha256": ordered_ids_sha,
        "canonical_membership_rows_sha256": membership_rows_sha,
        "canonical_baseline_queue_rows_sha256": baseline_rows_sha,
    }
    identity_sha = sha256_bytes(canonical_json_bytes(identity_core))

    frozen = design["target_identity"]
    checks = {
        "ordered_entity_ids_sha256": ordered_ids_sha,
        "canonical_membership_rows_sha256": membership_rows_sha,
        "canonical_baseline_queue_rows_sha256": baseline_rows_sha,
        "canonical_target_identity_sha256": identity_sha,
    }
    for key, actual in checks.items():
        if frozen[key] != actual:
            raise TrancheGuardError(
                f"Independent target identity mismatch: {key}"
            )

    if target_identity_rows != frozen["entities"]:
        raise TrancheGuardError(
            "Target identity rows differ from frozen design"
        )

    return {
        "membership_fields": membership_fields,
        "membership_rows": target_membership,
        "queue_fields": queue_fields,
        "queue_rows": target_queue,
        "entity_ids": target_ids,
        "identity_rows": target_identity_rows,
        "identity_core": identity_core,
        "identity_sha256": identity_sha,
        "queue_by_id": queue_by_id,
    }


def load_context(
    *,
    design_path: Path = DEFAULT_TRANCHE_DESIGN,
    design_sums_path: Path | None = None,
    queue_path: Path = DEFAULT_QUEUE,
    execution_root: Path = EXECUTION_ROOT,
) -> dict:
    design_path = Path(design_path).resolve()
    if design_sums_path is None:
        design_sums_path = default_design_sums_for(design_path)
    design_sums_path = Path(design_sums_path).resolve()

    design = validate_design(
        design_path=design_path,
        design_sums_path=design_sums_path,
    )
    runtime = design_runtime(design)

    base_guard = load_base_guard()
    base_context = base_guard.load_guard_context(
        queue_path=Path(queue_path).resolve(),
        execution_root=Path(execution_root).resolve(),
    )

    context = {
        "base_guard": base_guard,
        "design": design,
        "design_path": design_path,
        "design_sums_path": design_sums_path,
        "design_freeze_sha256": sha256_file(design_sums_path),
        "runtime": runtime,
        "appender": base_context["appender"],
        "appender_context": base_context["appender_context"],
        "base_context": base_context,
        "queue_path": Path(queue_path).resolve(),
        "execution_root": Path(execution_root).resolve(),
    }
    context["target"] = reconstruct_target(context=context)
    return context


def blank_reference_rows(
    context: dict,
) -> tuple[list[str], list[dict[str, str]]]:
    base_guard = context["base_guard"]
    payload = base_guard.build_review_packet_bytes(
        scope=context["base_context"]["scope"],
        contract=context["base_context"]["contract"],
    )
    handle = io.StringIO(payload.decode("utf-8"), newline="")
    reader = csv.DictReader(handle, delimiter="\t")
    return list(reader.fieldnames or []), list(reader)


def design_review_packet_repo_path(design: dict) -> str:
    value = design["review_packet_contract"]["path"]
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise TrancheGuardError("Unsafe review-packet path in design")
    return path.as_posix()


def pre_review_snapshot_path(context: dict) -> Path:
    transaction_id = context["runtime"]["transaction_id"].lower()
    return HERE / f"{transaction_id}_pre_review_packet.tsv"


def frozen_pre_review_packet_bytes(context: dict) -> bytes:
    design = context["design"]
    contract = design["review_packet_contract"]
    runtime = context["runtime"]
    tx_key = runtime["transaction_id"].lower()
    sha_key = (
        "pre_tranche_sha256"
        if "pre_tranche_sha256" in contract
        else f"pre_{tx_key}_sha256"
    )
    bytes_key = (
        "pre_tranche_bytes"
        if "pre_tranche_bytes" in contract
        else f"pre_{tx_key}_bytes"
    )
    if sha_key not in contract or bytes_key not in contract:
        raise TrancheGuardError(
            "Tranche design does not pin pre-review packet identity"
        )

    snapshot = pre_review_snapshot_path(context)
    if not snapshot.is_file():
        raise TrancheGuardError(
            "Frozen pre-review packet snapshot missing: "
            + snapshot.name
        )

    payload = snapshot.read_bytes()
    if sha256_bytes(payload) != contract[sha_key]:
        raise TrancheGuardError("Frozen pre-review packet SHA mismatch")
    if len(payload) != contract[bytes_key]:
        raise TrancheGuardError("Frozen pre-review packet byte count mismatch")
    return payload


def parse_tsv_bytes(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    handle = io.StringIO(payload.decode("utf-8"), newline="")
    reader = csv.DictReader(handle, delimiter="\t")
    return list(reader.fieldnames or []), list(reader)


def validate_review_packet(
    *,
    packet_path: Path,
    context: dict,
    mode: str,
) -> list[dict[str, str]]:
    if mode not in {"pre_review", "transaction_ready"}:
        raise TrancheGuardError("Unknown review-packet validation mode")

    fields, rows = read_tsv(packet_path)
    reference_fields, reference_rows = blank_reference_rows(context)
    frozen_fields, frozen_rows = parse_tsv_bytes(
        frozen_pre_review_packet_bytes(context)
    )

    if fields != reference_fields or fields != frozen_fields:
        raise TrancheGuardError(
            "Review packet schema differs from frozen schema"
        )
    if len(rows) != 500 or len(reference_rows) != 500 or len(frozen_rows) != 500:
        raise TrancheGuardError("Review packet must contain 500 rows")

    immutable_fields = [
        field
        for field in fields
        if field not in PROPOSED_FIELDS
    ]
    base_guard = context["base_guard"]
    runtime = context["runtime"]

    for position, (row, reference) in enumerate(
        zip(rows, reference_rows),
        start=1,
    ):
        base_guard.validate_row_hygiene(row)
        if int(row["position_in_batch"]) != position:
            raise TrancheGuardError(
                "Review packet position ordering changed"
            )
        for field in immutable_fields:
            if row[field] != reference[field]:
                raise TrancheGuardError(
                    f"Immutable review value changed at position {position}: {field}"
                )

    # Everything before the current target is historical review state and is
    # locked byte-for-field to the design-parent snapshot.
    for position in range(1, runtime["start"]):
        row = rows[position - 1]
        frozen = frozen_rows[position - 1]
        for field in PROPOSED_FIELDS:
            if row[field] != frozen[field]:
                raise TrancheGuardError(
                    f"Historical proposed value changed at position {position}: {field}"
                )

    target_rows = [
        rows[position - 1]
        for position in runtime["positions"]
    ]

    if mode == "pre_review":
        for position, row in zip(runtime["positions"], target_rows):
            for field in PROPOSED_FIELDS:
                if row[field]:
                    raise TrancheGuardError(
                        f"Target position {position} must be proposal-blank before review"
                    )
    else:
        for position, row in zip(runtime["positions"], target_rows):
            if not row["proposed_event_type"]:
                raise TrancheGuardError(
                    f"Target position {position} lacks a proposed event"
                )

    # Future positions remain scientifically untouched by this tranche.
    for position in range(runtime["end"] + 1, 501):
        row = rows[position - 1]
        for field in PROPOSED_FIELDS:
            if row[field]:
                raise TrancheGuardError(
                    f"Future position {position} must remain proposal-blank"
                )

    target_ids = [row["screening_entity_id"] for row in target_rows]
    if target_ids != context["target"]["entity_ids"]:
        raise TrancheGuardError(
            "Review packet target identity differs from frozen target"
        )

    return rows


def expected_checkpoint_contract(context: dict) -> dict:
    transaction_id = context["runtime"]["transaction_id"]
    return {
        "transaction_id": transaction_id,
        "root": (
            "results/07_comparative_landscape/"
            "baseline_scientific_screening_event_receipts"
        ),
        "final_transaction_directory": (
            "results/07_comparative_landscape/"
            "baseline_scientific_screening_event_receipts/"
            + transaction_id
        ),
        "final_files": [
            "authorization.json",
            "proposal.tsv",
            "receipt.json",
        ],
    }


def authorization_status(context: dict) -> str:
    runtime = context["runtime"]
    return (
        f"AUTHORIZED_B000001_{runtime['transaction_id']}_"
        f"POSITIONS_{runtime['start']}_TO_{runtime['end']}_ONE_USE"
    )


def load_authorization(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(value) != AUTHORIZATION_FIELDS:
        missing = sorted(AUTHORIZATION_FIELDS - set(value))
        extra = sorted(set(value) - AUTHORIZATION_FIELDS)
        raise TrancheGuardError(
            f"Authorization schema mismatch; missing={missing}; extra={extra}"
        )
    return value


def ensure_tracked_authorization(
    *,
    authorization_path: Path,
    authorization: dict,
) -> str:
    authorization_path = Path(authorization_path).resolve()
    try:
        rel = authorization_path.relative_to(REPO_ROOT).as_posix()
    except ValueError as exc:
        raise TrancheGuardError(
            "Real authorization must be inside repository"
        ) from exc

    if git("status", "--porcelain", "--untracked-files=no").strip():
        raise TrancheGuardError(
            "Tracked worktree must be clean for real production authorization"
        )

    head = git("rev-parse", "HEAD").strip()
    parent = git("rev-parse", "HEAD^").strip()
    if authorization["parent_commit"] != parent:
        raise TrancheGuardError(
            "Authorization parent_commit is not current HEAD parent"
        )

    try:
        git("ls-files", "--error-unmatch", rel)
    except subprocess.CalledProcessError as exc:
        raise TrancheGuardError(
            "Real production authorization is not tracked"
        ) from exc

    last_commit = git("log", "-1", "--format=%H", "--", rel).strip()
    if last_commit != head:
        raise TrancheGuardError(
            "Authorization is not the current HEAD commit artifact"
        )

    if git("diff", "--name-only", "HEAD", "--", rel).strip():
        raise TrancheGuardError(
            "Authorization differs from tracked HEAD bytes"
        )

    return head


def validate_authorization(
    *,
    authorization_path: Path,
    context: dict,
    require_tracked: bool,
) -> dict:
    value = load_authorization(authorization_path)
    runtime = context["runtime"]
    base_guard = context["base_guard"]
    appender = context["appender"]

    if value["status"] != authorization_status(context):
        raise TrancheGuardError("Authorization status invalid")
    if value["schema_version"] != 1:
        raise TrancheGuardError("Authorization schema version invalid")
    if not COMMIT_RE.fullmatch(value["parent_commit"]):
        raise TrancheGuardError("Authorization parent commit malformed")

    if value["tranche_design_freeze_sha256"] != context[
        "design_freeze_sha256"
    ]:
        raise TrancheGuardError("Tranche design freeze SHA mismatch")
    if value["post_pilot_tranche_guard_sha256"] != sha256_file(
        Path(__file__).resolve()
    ):
        raise TrancheGuardError("Generic tranche guard source SHA mismatch")
    if value["event_appender_implementation_sha256"] != base_guard.EXPECTED_APPENDER_SHA256:
        raise TrancheGuardError("Frozen appender source SHA mismatch")
    if value["event_appender_implementation_freeze_sha256"] != sha256_file(
        base_guard.APPENDER_FREEZE_SUMS
    ):
        raise TrancheGuardError("Frozen appender freeze SHA mismatch")
    if value["event_entry_design_freeze_sha256"] != sha256_file(
        base_guard.EVENT_ENTRY_DESIGN_SUMS
    ):
        raise TrancheGuardError("Event-entry design freeze SHA mismatch")

    if value["target_identity"] != identity_summary(context["design"]):
        raise TrancheGuardError("Authorization target identity mismatch")
    if value["batch_id"] != runtime["batch_id"]:
        raise TrancheGuardError("Authorization batch mismatch")
    if value["authorized_positions"] != runtime["positions"]:
        raise TrancheGuardError("Authorization position scope mismatch")
    if value["expected_pre_ledger_sha256"] != runtime["pre_ledger_sha256"]:
        raise TrancheGuardError("Authorization pre-ledger SHA mismatch")
    if value["expected_pre_event_count"] != runtime["pre_event_count"]:
        raise TrancheGuardError("Authorization pre-event count mismatch")
    if value["authorized_event_count"] != runtime["count"]:
        raise TrancheGuardError("Authorization event count mismatch")
    if value["expected_assigned_event_ids"] != runtime["expected_event_ids"]:
        raise TrancheGuardError("Authorization event IDs mismatch")

    if not value["operator_id"].strip():
        raise TrancheGuardError("Authorization operator_id empty")
    base_guard.validate_field_hygiene(
        value["operator_id"],
        field_name="operator_id",
    )
    if value["operator_type"] not in set(
        appender.load_base_engine().OPERATOR_TYPES
    ):
        raise TrancheGuardError("Authorization operator_type invalid")

    if value["permitted_initial_event_types"] != [
        "record_decision",
        "source_escalation",
    ]:
        raise TrancheGuardError("Authorization event-type scope changed")
    if value["receipt_checkpoint_contract"] != expected_checkpoint_contract(context):
        raise TrancheGuardError("Authorization checkpoint contract mismatch")
    if value["positions_outside_target_authorized"] is not False:
        raise TrancheGuardError("Authorization illegally enables outside positions")
    if value["partial_transaction_permitted"] is not False:
        raise TrancheGuardError("Authorization illegally permits partial transaction")
    if value["one_use"] is not True:
        raise TrancheGuardError("Authorization must be one-use")
    if value["scientific_decisions_frozen_before_authorization"] is not True:
        raise TrancheGuardError("Scientific decisions must be frozen before authorization")
    if value["authorization_does_not_modify_scientific_decisions"] is not True:
        raise TrancheGuardError("Authorization scientific-boundary invariant changed")
    if value["event_ledger_mutation_authorized"] is not True:
        raise TrancheGuardError("Authorization does not permit ledger mutation")
    if value["review_packet_mutation_authorized"] is not False:
        raise TrancheGuardError("Authorization illegally permits review-packet mutation")
    if not value["human_approval_text"].strip():
        raise TrancheGuardError("Human approval text must be non-empty")

    appender.validate_transaction_timestamp(
        value["transaction_timestamp_utc"],
        base=appender.load_base_engine(),
    )
    if not re.fullmatch(r"[0-9a-f]{64}", value["proposal_sha256"]):
        raise TrancheGuardError("Authorization proposal SHA malformed")
    if not re.fullmatch(r"[0-9a-f]{64}", value["projected_post_ledger_sha256"]):
        raise TrancheGuardError("Authorization projected ledger SHA malformed")

    if require_tracked:
        authorization_commit = ensure_tracked_authorization(
            authorization_path=authorization_path,
            authorization=value,
        )
    else:
        authorization_commit = "UNTRACKED_TEST_AUTHORIZATION"

    return {
        "authorization": value,
        "authorization_sha256": sha256_file(authorization_path),
        "authorization_commit": authorization_commit,
    }


def extract_proposal_bytes(
    *,
    packet_path: Path,
    operator_id: str,
    operator_type: str,
    context: dict,
) -> bytes:
    rows = validate_review_packet(
        packet_path=packet_path,
        context=context,
        mode="transaction_ready",
    )
    appender = context["appender"]
    base_guard = context["base_guard"]
    runtime = context["runtime"]

    if not operator_id.strip():
        raise TrancheGuardError("Proposal operator_id empty")
    base_guard.validate_field_hygiene(operator_id, field_name="operator_id")
    if operator_type not in set(appender.load_base_engine().OPERATOR_TYPES):
        raise TrancheGuardError("Proposal operator_type invalid")

    proposals = []
    for position in runtime["positions"]:
        row = rows[position - 1]
        proposal = {
            "screening_entity_id": row["screening_entity_id"],
            "batch_id": runtime["batch_id"],
            "event_type": "",
            "record_decision": "",
            "exclusion_reason_code": "",
            "candidate_method_flag": "",
            "evidence_basis": "",
            "evidence_source_locator": "",
            "evidence_escalation_status": "",
            "supersedes_event_id": "",
            "operator_id": operator_id,
            "operator_type": operator_type,
            "notes": "",
        }
        for review_field, proposal_field in PROPOSAL_MAPPING.items():
            proposal[proposal_field] = row[review_field]
        base_guard.validate_row_hygiene(proposal)
        proposals.append(proposal)

    if len(proposals) != runtime["count"]:
        raise TrancheGuardError("Proposal event count mismatch")
    if [
        proposal["screening_entity_id"]
        for proposal in proposals
    ] != context["target"]["entity_ids"]:
        raise TrancheGuardError("Proposal target order differs from frozen tranche")
    if any(proposal["supersedes_event_id"] for proposal in proposals):
        raise TrancheGuardError("Initial tranche proposal unexpectedly supersedes events")

    return tsv_bytes(
        fields=list(appender.PROPOSAL_FIELDS),
        rows=proposals,
    )


def validate_pre_transaction_state(
    *,
    ledger_path: Path,
    context: dict,
) -> dict:
    runtime = context["runtime"]
    validation = context["appender"].validate_current_ledger(
        ledger_path=ledger_path,
        context=context["appender_context"],
    )
    if validation["event_count"] != runtime["pre_event_count"]:
        raise TrancheGuardError("Pre-transaction event count changed")
    if validation["ledger_sha256"] != runtime["pre_ledger_sha256"]:
        raise TrancheGuardError("Expected pre-ledger SHA mismatch")

    parent = context["design"]["parent_production_state"]
    expected_states = {
        "awaiting_source_escalation": parent["awaiting_source_escalation"],
        "blocked_metadata": parent["blocked_metadata"],
        "complete": parent["complete"],
        "ready": parent["ready"],
    }
    if validation["derived_state_counts"] != expected_states:
        raise TrancheGuardError("Expected pre-state counts changed")

    _, rows = read_tsv(ledger_path)
    historical_entities = {row["screening_entity_id"] for row in rows}
    overlap = sorted(
        set(context["target"]["entity_ids"]) & historical_entities
    )
    if overlap:
        raise TrancheGuardError(
            "Initial tranche target unexpectedly has historical events"
        )
    return validation


def detect_recovery_state(
    *,
    ledger_path: Path,
    receipt_root: Path,
    context: dict,
) -> dict:
    runtime = context["runtime"]
    transaction_id = runtime["transaction_id"]
    final_dir = Path(receipt_root) / transaction_id
    temp_prefix = f".{transaction_id}.tmp."
    temp_dirs = []
    if Path(receipt_root).exists():
        temp_dirs = sorted(
            path
            for path in Path(receipt_root).iterdir()
            if path.is_dir() and path.name.startswith(temp_prefix)
        )

    ledger_sha = sha256_file(ledger_path)
    if final_dir.exists():
        return {
            "status": "FINAL_CHECKPOINT_EXISTS",
            "ledger_sha256": ledger_sha,
            "temporary_checkpoint_count": len(temp_dirs),
        }
    if ledger_sha != runtime["pre_ledger_sha256"]:
        return {
            "status": "RECOVERY_REQUIRED",
            "ledger_sha256": ledger_sha,
            "temporary_checkpoint_count": len(temp_dirs),
        }
    if temp_dirs:
        return {
            "status": "UNEXPECTED_STAGED_CHECKPOINT_PRE_APPEND",
            "ledger_sha256": ledger_sha,
            "temporary_checkpoint_count": len(temp_dirs),
        }
    return {
        "status": f"PRE_{transaction_id}_READY",
        "ledger_sha256": ledger_sha,
        "temporary_checkpoint_count": 0,
    }


def prepare_transaction(
    *,
    authorization_path: Path,
    packet_path: Path,
    ledger_path: Path,
    context: dict,
    require_tracked_authorization: bool,
) -> dict:
    runtime = context["runtime"]
    validate_pre_transaction_state(
        ledger_path=ledger_path,
        context=context,
    )
    authorization_info = validate_authorization(
        authorization_path=authorization_path,
        context=context,
        require_tracked=require_tracked_authorization,
    )
    authorization = authorization_info["authorization"]

    proposal_bytes = extract_proposal_bytes(
        packet_path=packet_path,
        operator_id=authorization["operator_id"],
        operator_type=authorization["operator_type"],
        context=context,
    )
    proposal_sha = sha256_bytes(proposal_bytes)
    if proposal_sha != authorization["proposal_sha256"]:
        raise TrancheGuardError(
            "Authorization proposal SHA does not match reviewed proposal"
        )

    with tempfile.TemporaryDirectory(
        prefix=f"branchsnv-exp07-{runtime['transaction_id'].lower()}-dryrun-"
    ) as tmp:
        proposal_path = Path(tmp) / "proposal.tsv"
        proposal_path.write_bytes(proposal_bytes)
        prepared = context["appender"].prepare_transaction_from_files(
            ledger_path=ledger_path,
            proposal_path=proposal_path,
            expected_pre_ledger_sha256=runtime["pre_ledger_sha256"],
            context=context["appender_context"],
            transaction_timestamp_utc=authorization[
                "transaction_timestamp_utc"
            ],
        )

    receipt = dict(prepared["receipt"])
    if receipt["batch_id"] != runtime["batch_id"]:
        raise TrancheGuardError("Prepared batch changed")
    if receipt["new_event_count"] != runtime["count"]:
        raise TrancheGuardError("Prepared event count changed")
    if receipt["pre_append_event_count"] != runtime["pre_event_count"]:
        raise TrancheGuardError("Prepared pre-event count changed")
    if receipt["post_append_event_count"] != runtime["post_event_count"]:
        raise TrancheGuardError("Prepared post-event count changed")
    if receipt["first_assigned_event_id"] != runtime["first_event_id"]:
        raise TrancheGuardError("Prepared first event ID mismatch")
    if receipt["last_assigned_event_id"] != runtime["last_event_id"]:
        raise TrancheGuardError("Prepared last event ID mismatch")
    if receipt["published"] is not False:
        raise TrancheGuardError("Dry-run unexpectedly published")
    if receipt["strict_prefix_extension"] is not True:
        raise TrancheGuardError("Candidate is not strict ledger-prefix extension")
    if receipt["review_fields_blank"] is not True:
        raise TrancheGuardError("Appender-managed review fields unexpectedly populated")

    projected_sha = context["appender"].sha256_bytes(
        prepared["candidate_bytes"]
    )
    if projected_sha != authorization["projected_post_ledger_sha256"]:
        raise TrancheGuardError("Projected post-ledger SHA mismatch")
    if receipt["post_append_ledger_sha256"] != projected_sha:
        raise TrancheGuardError("Prepared receipt projected SHA mismatch")
    if receipt["derived_state_counts_after_append"] != authorization[
        "projected_post_state_counts"
    ]:
        raise TrancheGuardError("Projected post-state counts mismatch")

    return {
        "status": f"{runtime['transaction_id']}_DRY_RUN_VALID",
        "authorization": authorization,
        "authorization_sha256": authorization_info["authorization_sha256"],
        "authorization_commit": authorization_info["authorization_commit"],
        "proposal_bytes": proposal_bytes,
        "proposal_sha256": proposal_sha,
        "candidate_bytes": prepared["candidate_bytes"],
        "projected_post_ledger_sha256": projected_sha,
        "prepared_receipt": receipt,
    }


def fsync_file(path: Path) -> None:
    with Path(path).open("rb") as handle:
        os.fsync(handle.fileno())


def fsync_directory(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def validate_checkpoint(
    *,
    checkpoint_dir: Path,
    ledger_path: Path,
    context: dict,
) -> dict:
    runtime = context["runtime"]
    checkpoint_dir = Path(checkpoint_dir)
    if not checkpoint_dir.is_dir():
        raise TrancheGuardError("Checkpoint directory missing")
    children = list(checkpoint_dir.iterdir())
    if any(path.is_symlink() for path in children):
        raise TrancheGuardError("Checkpoint contains symlink")
    if any(not path.is_file() for path in children):
        raise TrancheGuardError("Checkpoint contains non-file artifact")
    if {path.name for path in children} != {
        "authorization.json",
        "proposal.tsv",
        "receipt.json",
    }:
        raise TrancheGuardError("Checkpoint artifact set mismatch")

    receipt = json.loads(
        (checkpoint_dir / "receipt.json").read_text(encoding="utf-8")
    )
    if receipt["transaction_id"] != runtime["transaction_id"]:
        raise TrancheGuardError("Checkpoint transaction ID mismatch")
    if receipt["proposal_sha256"] != sha256_file(
        checkpoint_dir / "proposal.tsv"
    ):
        raise TrancheGuardError("Checkpoint proposal SHA mismatch")
    if receipt["authorization_json_sha256"] != sha256_file(
        checkpoint_dir / "authorization.json"
    ):
        raise TrancheGuardError("Checkpoint authorization SHA mismatch")
    if receipt["validated_post_append_ledger_sha256"] != sha256_file(
        ledger_path
    ):
        raise TrancheGuardError("Checkpoint post-ledger SHA mismatch")
    if receipt["pre_append_event_count"] != runtime["pre_event_count"]:
        raise TrancheGuardError("Checkpoint pre-event count mismatch")
    if receipt["post_append_event_count"] != runtime["post_event_count"]:
        raise TrancheGuardError("Checkpoint post-event count mismatch")
    if receipt["new_event_count"] != runtime["count"]:
        raise TrancheGuardError("Checkpoint new-event count mismatch")
    if receipt["first_assigned_event_id"] != runtime["first_event_id"]:
        raise TrancheGuardError("Checkpoint first event ID mismatch")
    if receipt["last_assigned_event_id"] != runtime["last_event_id"]:
        raise TrancheGuardError("Checkpoint last event ID mismatch")
    if receipt["published"] is not True:
        raise TrancheGuardError("Checkpoint not marked published")
    if receipt["post_publication_validation_passed"] is not True:
        raise TrancheGuardError("Post-publication validation not recorded")
    if receipt["checkpoint_status"] != "COMPLETE":
        raise TrancheGuardError("Checkpoint status not COMPLETE")

    return {
        "status": f"{runtime['transaction_id']}_CHECKPOINT_VALID",
        "transaction_id": runtime["transaction_id"],
        "post_append_ledger_sha256": receipt[
            "validated_post_append_ledger_sha256"
        ],
        "proposal_sha256": receipt["proposal_sha256"],
        "new_event_count": receipt["new_event_count"],
    }


def execute_transaction(
    *,
    authorization_path: Path,
    packet_path: Path,
    ledger_path: Path,
    receipt_root: Path,
    context: dict,
    require_tracked_authorization: bool,
    _test_fail_after_append: bool = False,
) -> dict:
    runtime = context["runtime"]
    transaction_id = runtime["transaction_id"]
    ledger_path = Path(ledger_path).resolve()
    receipt_root = Path(receipt_root).resolve()

    is_real_production = ledger_path == DEFAULT_LEDGER.resolve()
    if is_real_production:
        if receipt_root != RECEIPT_ROOT.resolve():
            raise TrancheGuardError(
                "Real production ledger requires canonical receipt root"
            )
        if not require_tracked_authorization:
            raise TrancheGuardError(
                "Real production requires tracked one-use authorization"
            )

    recovery = detect_recovery_state(
        ledger_path=ledger_path,
        receipt_root=receipt_root,
        context=context,
    )
    expected_ready = f"PRE_{transaction_id}_READY"
    if recovery["status"] != expected_ready:
        raise RecoveryRequiredError(
            f"{transaction_id} cannot execute from state: {recovery['status']}"
        )

    prepared = prepare_transaction(
        authorization_path=authorization_path,
        packet_path=packet_path,
        ledger_path=ledger_path,
        context=context,
        require_tracked_authorization=require_tracked_authorization,
    )
    authorization = prepared["authorization"]

    if sha256_file(ledger_path) != runtime["pre_ledger_sha256"]:
        raise TrancheGuardError("Ledger changed after transaction preparation")

    final_dir = receipt_root / transaction_id
    if final_dir.exists():
        raise RecoveryRequiredError("Final checkpoint already exists")

    temp_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{transaction_id}.tmp.",
            dir=receipt_root,
        )
    )
    appended = False

    try:
        authorization_copy = temp_dir / "authorization.json"
        proposal_copy = temp_dir / "proposal.tsv"
        authorization_copy.write_bytes(Path(authorization_path).read_bytes())
        proposal_copy.write_bytes(prepared["proposal_bytes"])
        fsync_file(authorization_copy)
        fsync_file(proposal_copy)
        fsync_directory(temp_dir)
        fsync_directory(receipt_root)

        if sha256_file(ledger_path) != runtime["pre_ledger_sha256"]:
            raise TrancheGuardError(
                "Ledger changed immediately before publication"
            )

        receipt = context["appender"].append_transaction_atomic(
            ledger_path=ledger_path,
            proposal_path=proposal_copy,
            expected_pre_ledger_sha256=runtime["pre_ledger_sha256"],
            context=context["appender_context"],
            transaction_timestamp_utc=authorization[
                "transaction_timestamp_utc"
            ],
            allow_production=True,
        )
        appended = True

        if _test_fail_after_append:
            raise RuntimeError(
                f"SYNTHETIC_{transaction_id}_FAILURE_AFTER_LEDGER_APPEND"
            )

        post_validation = context["appender"].validate_current_ledger(
            ledger_path=ledger_path,
            context=context["appender_context"],
        )
        if post_validation["event_count"] != runtime["post_event_count"]:
            raise TrancheGuardError("Post-transaction event count mismatch")
        if post_validation["ledger_sha256"] != authorization[
            "projected_post_ledger_sha256"
        ]:
            raise TrancheGuardError("Published ledger SHA differs from authorization")
        if post_validation["derived_state_counts"] != authorization[
            "projected_post_state_counts"
        ]:
            raise TrancheGuardError("Published state counts differ from authorization")

        receipt = dict(receipt)
        receipt.update({
            "transaction_id": transaction_id,
            "target_positions": runtime["positions"],
            "target_identity": identity_summary(context["design"]),
            "authorization_commit": prepared["authorization_commit"],
            "authorization_json_sha256": prepared["authorization_sha256"],
            "tranche_design_freeze_sha256": context[
                "design_freeze_sha256"
            ],
            "post_pilot_tranche_guard_sha256": sha256_file(
                Path(__file__).resolve()
            ),
            "proposal_sha256": prepared["proposal_sha256"],
            "checkpoint_status": "COMPLETE",
            "post_publication_validation_passed": True,
        })

        receipt_path = temp_dir / "receipt.json"
        receipt_path.write_bytes(pretty_json_bytes(receipt))
        fsync_file(receipt_path)
        fsync_directory(temp_dir)

        if final_dir.exists():
            raise TrancheGuardError("Final checkpoint unexpectedly appeared")
        os.replace(temp_dir, final_dir)
        fsync_directory(receipt_root)

        checkpoint = validate_checkpoint(
            checkpoint_dir=final_dir,
            ledger_path=ledger_path,
            context=context,
        )
        return {
            "status": f"{transaction_id}_EXECUTION_COMPLETE",
            "transaction_id": transaction_id,
            "checkpoint": checkpoint,
            "receipt": receipt,
        }

    except Exception as exc:
        current_sha = sha256_file(ledger_path)
        if appended or current_sha != runtime["pre_ledger_sha256"]:
            raise RecoveryRequiredError(
                f"Ledger changed but {transaction_id} checkpoint did not finalize; "
                "preserve staged checkpoint and enter recovery workflow"
            ) from exc
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise


def describe_state(
    *,
    packet_path: Path,
    ledger_path: Path,
    receipt_root: Path,
    context: dict,
) -> dict:
    validate_pre_transaction_state(
        ledger_path=ledger_path,
        context=context,
    )
    rows = validate_review_packet(
        packet_path=packet_path,
        context=context,
        mode="pre_review",
    )
    recovery = detect_recovery_state(
        ledger_path=ledger_path,
        receipt_root=receipt_root,
        context=context,
    )
    runtime = context["runtime"]
    return {
        "status": f"{runtime['transaction_id']}_GENERIC_GUARD_READY_PRE_REVIEW",
        "transaction_id": runtime["transaction_id"],
        "batch_id": runtime["batch_id"],
        "target_positions": runtime["positions"],
        "target_event_count": runtime["count"],
        "target_entity_ids": context["target"]["entity_ids"],
        "target_identity": identity_summary(context["design"]),
        "expected_assigned_event_ids": runtime["expected_event_ids"],
        "pre_event_count": runtime["pre_event_count"],
        "expected_post_event_count": runtime["post_event_count"],
        "ledger_sha256": sha256_file(ledger_path),
        "review_packet_sha256": sha256_file(packet_path),
        "review_packet_bytes": Path(packet_path).stat().st_size,
        "historical_positions_locked": True,
        "target_positions_blank": all(
            not rows[position - 1][field]
            for position in runtime["positions"]
            for field in PROPOSED_FIELDS
        ),
        "future_positions_blank": all(
            not rows[position - 1][field]
            for position in range(runtime["end"] + 1, 501)
            for field in PROPOSED_FIELDS
        ),
        "checkpoint_state": recovery["status"],
        "authorization_created_by_guard": False,
        "review_packet_mutation_performed": False,
        "ledger_mutation_performed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--design-json",
        type=Path,
        default=DEFAULT_TRANCHE_DESIGN,
    )
    parser.add_argument(
        "--design-sums",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--baseline-queue",
        type=Path,
        default=DEFAULT_QUEUE,
    )
    parser.add_argument(
        "--execution-root",
        type=Path,
        default=EXECUTION_ROOT,
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
    )
    parser.add_argument(
        "--receipt-root",
        type=Path,
        default=RECEIPT_ROOT,
    )
    parser.add_argument(
        "--review-packet",
        type=Path,
        default=DEFAULT_REVIEW_PACKET,
    )
    parser.add_argument(
        "--authorization-json",
        type=Path,
        default=None,
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.dry_run and args.execute:
        raise TrancheGuardError("Choose only one tranche action")

    context = load_context(
        design_path=args.design_json.resolve(),
        design_sums_path=(
            args.design_sums.resolve()
            if args.design_sums is not None
            else None
        ),
        queue_path=args.baseline_queue.resolve(),
        execution_root=args.execution_root.resolve(),
    )
    ledger_path = args.ledger.resolve()
    receipt_root = args.receipt_root.resolve()
    packet_path = args.review_packet.resolve()

    if args.dry_run or args.execute:
        if args.authorization_json is None:
            raise TrancheGuardError(
                "Transaction action requires authorization JSON"
            )
        if args.execute:
            result = execute_transaction(
                authorization_path=args.authorization_json.resolve(),
                packet_path=packet_path,
                ledger_path=ledger_path,
                receipt_root=receipt_root,
                context=context,
                require_tracked_authorization=True,
            )
        else:
            prepared = prepare_transaction(
                authorization_path=args.authorization_json.resolve(),
                packet_path=packet_path,
                ledger_path=ledger_path,
                context=context,
                require_tracked_authorization=True,
            )
            result = {
                "status": prepared["status"],
                "authorization_commit": prepared["authorization_commit"],
                "authorization_sha256": prepared["authorization_sha256"],
                "proposal_sha256": prepared["proposal_sha256"],
                "projected_post_ledger_sha256": prepared[
                    "projected_post_ledger_sha256"
                ],
                "prepared_receipt": prepared["prepared_receipt"],
                "mutation_performed": False,
            }
    else:
        result = describe_state(
            packet_path=packet_path,
            ledger_path=ledger_path,
            receipt_root=receipt_root,
            context=context,
        )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
