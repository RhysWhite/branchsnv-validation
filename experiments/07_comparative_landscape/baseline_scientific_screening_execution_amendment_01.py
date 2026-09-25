#!/usr/bin/env python3

"""
Experiment 07 baseline scientific-screening execution amendment 01.

Append-only adapter over the frozen execution engine.

Purpose:
- implement the frozen 8 historical anchors = 7 in-baseline
  carry-forwards + 1 out-of-baseline prior anchor contract;
- validate the frozen prior-anchor baseline-presence resolution;
- derive the exact active ready population;
- construct deterministic batch manifests in memory.

This module does NOT:
- alter the frozen baseline queue;
- alter the original frozen execution implementation;
- make record-level scientific decisions;
- create event-ledger rows;
- perform source escalation;
- perform method assessment;
- assign analytical roles or directness;
- select canonical publications;
- promote Wave 1 anchors;
- perform network access; or
- write production execution output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import csv
import hashlib
import importlib
import json


HERE = Path(__file__).resolve().parent

REPO_ROOT = HERE.parent.parent

RESULTS_ROOT = (
    REPO_ROOT
    / "results"
    / "07_comparative_landscape"
)

DEFAULT_QUEUE = (
    RESULTS_ROOT
    / "scientific_screening"
    / "baseline_screening_queue.tsv"
)

DEFAULT_RESOLUTION = (
    HERE
    / "prior_wave0_baseline_presence_resolution.tsv"
)

DEFAULT_AMENDMENT = (
    HERE
    / "baseline_scientific_screening_execution_contract_amendment_01.json"
)

FROZEN_BASE_SOURCE = (
    HERE
    / "baseline_scientific_screening_execution.py"
)

FROZEN_BASE_FREEZE = (
    HERE
    / "baseline_scientific_screening_execution_implementation.json"
)


EXPECTED_QUEUE_SHA256 = (
    "97575b71c4607c3dcad893d90210f913"
    "2a83d0ae2e299ac2f1aef7e94f527d58"
)

EXPECTED_HISTORICAL_ANCHORS = 8
EXPECTED_IN_BASELINE = 7
EXPECTED_OUT_OF_BASELINE = 1
EXPECTED_ACTIVE_READY = 94622
EXPECTED_BATCH_COUNT = 190
EXPECTED_MAX_BATCH_SIZE = 500

OUT_OF_BASELINE_ANCHOR_ID = "W0A06"
OUT_OF_BASELINE_TOOL = "kSNP3.0"
OUT_OF_BASELINE_DOI = "10.1093/bioinformatics/btv271"


RESOLUTION_FIELDS = [
    "anchor_id",
    "tool",
    "canonical_identifier_type",
    "canonical_identifier",
    "prior_anchor_decision",
    "prior_landscape_decision",
    "prior_confirmed_role",
    "baseline_presence_status",
    "screening_entity_id",
    "mapping_basis",
    "record_decision_projection",
    "candidate_method_flag_projection",
    "additional_same_doi_entity_count",
    "scientific_reassessment_performed",
]


class AmendmentValidationError(
    RuntimeError
):
    pass


def sha256_bytes(
    payload: bytes,
) -> str:
    return hashlib.sha256(
        payload
    ).hexdigest()


def sha256_file(
    path: Path,
) -> str:
    return sha256_bytes(
        path.read_bytes()
    )


def canonical_json_bytes(
    value: Any,
) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )


def read_tsv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        fields = list(
            reader.fieldnames
            or []
        )

        rows = list(
            reader
        )

    return fields, rows


def load_frozen_base_module():
    """
    Import the original engine only after verifying its frozen SHA.
    """
    freeze = json.loads(
        FROZEN_BASE_FREEZE.read_text(
            encoding="utf-8"
        )
    )

    expected = freeze[
        "implementation"
    ][
        "sha256"
    ]

    observed = sha256_file(
        FROZEN_BASE_SOURCE
    )

    if observed != expected:
        raise AmendmentValidationError(
            "Original frozen execution implementation changed"
        )

    module = importlib.import_module(
        "baseline_scientific_screening_execution"
    )

    return module


def load_contract_amendment(
    path: Path,
) -> dict:
    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if (
        value[
            "status"
        ]
        != "FROZEN_PRE_IMPLEMENTATION_AMENDMENT"
    ):
        raise AmendmentValidationError(
            "Contract amendment is not frozen "
            "pre-implementation"
        )

    if value[
        "immutable_baseline_queue_sha256"
    ] != EXPECTED_QUEUE_SHA256:
        raise AmendmentValidationError(
            "Contract amendment baseline SHA changed"
        )

    anchors = value[
        "historical_prior_anchors"
    ]

    if anchors != {
        "ambiguous": 0,
        "in_baseline": 7,
        "out_of_baseline": 1,
        "total": 8,
    }:
        raise AmendmentValidationError(
            "Frozen 8=7+1 anchor contract changed"
        )

    derived = value[
        "derived_execution_population"
    ]

    if derived != {
        "active_ready_entities": 94622,
        "batch_count": 190,
        "frozen_ready_entities": 94629,
        "in_baseline_carry_forwards": 7,
        "max_batch_size": 500,
    }:
        raise AmendmentValidationError(
            "Frozen amended execution population changed"
        )

    if value[
        "current_implementation_state"
    ][
        "batch_generation_authorized"
    ] is not False:
        raise AmendmentValidationError(
            "Frozen amendment unexpectedly authorised "
            "old implementation"
        )

    return value


def validate_resolution_rows(
    *,
    fields: list[str],
    rows: list[dict[str, str]],
    baseline,
) -> dict:
    if fields != RESOLUTION_FIELDS:
        raise AmendmentValidationError(
            "Prior-anchor resolution schema changed"
        )

    if len(rows) != EXPECTED_HISTORICAL_ANCHORS:
        raise AmendmentValidationError(
            "Prior-anchor resolution must contain "
            "exactly eight historical anchors"
        )

    anchor_ids = [
        row[
            "anchor_id"
        ]
        for row in rows
    ]

    if len(set(anchor_ids)) != len(anchor_ids):
        raise AmendmentValidationError(
            "Duplicate historical anchor ID"
        )

    expected_anchor_ids = {
        f"W0A{index:02d}"
        for index in range(
            1,
            9,
        )
    }

    if set(anchor_ids) != expected_anchor_ids:
        raise AmendmentValidationError(
            "Historical anchor ID set changed"
        )

    in_baseline = []
    out_of_baseline = []

    for row in rows:
        if row[
            "canonical_identifier_type"
        ] != "doi":
            raise AmendmentValidationError(
                "Prior anchor canonical identifier "
                "must remain DOI"
            )

        if row[
            "prior_anchor_decision"
        ] != "include_as_anchor":
            raise AmendmentValidationError(
                "Prior anchor adjudication changed"
            )

        if row[
            "prior_landscape_decision"
        ] != "include":
            raise AmendmentValidationError(
                "Prior landscape decision changed"
            )

        if row[
            "prior_confirmed_role"
        ] not in {
            "direct",
            "near_direct",
        }:
            raise AmendmentValidationError(
                "Prior confirmed role changed"
            )

        if row[
            "record_decision_projection"
        ] != "retain_for_method_assessment":
            raise AmendmentValidationError(
                "Prior record-decision projection changed"
            )

        if row[
            "candidate_method_flag_projection"
        ] != "true":
            raise AmendmentValidationError(
                "Prior candidate flag projection changed"
            )

        if row[
            "scientific_reassessment_performed"
        ] != "false":
            raise AmendmentValidationError(
                "Scientific reassessment is prohibited"
            )

        status = row[
            "baseline_presence_status"
        ]

        if status == "in_baseline":
            in_baseline.append(
                row
            )

        elif status == "out_of_baseline":
            out_of_baseline.append(
                row
            )

        else:
            raise AmendmentValidationError(
                "Unknown or ambiguous baseline-presence state"
            )

    if len(in_baseline) != EXPECTED_IN_BASELINE:
        raise AmendmentValidationError(
            "Resolution must contain exactly seven "
            "in-baseline anchors"
        )

    if len(out_of_baseline) != EXPECTED_OUT_OF_BASELINE:
        raise AmendmentValidationError(
            "Resolution must contain exactly one "
            "out-of-baseline anchor"
        )

    mapped_ids = []

    for row in in_baseline:
        entity_id = row[
            "screening_entity_id"
        ].strip()

        if not entity_id:
            raise AmendmentValidationError(
                "In-baseline prior anchor lacks "
                "screening entity ID"
            )

        if entity_id in mapped_ids:
            raise AmendmentValidationError(
                "Duplicate in-baseline carry-forward target"
            )

        mapped_ids.append(
            entity_id
        )

        baseline_row = baseline.by_id.get(
            entity_id
        )

        if baseline_row is None:
            raise AmendmentValidationError(
                "Carry-forward target outside baseline"
            )

        if baseline_row[
            "screening_state"
        ] != "ready":
            raise AmendmentValidationError(
                "Carry-forward target is not ready"
            )

        if baseline_row[
            "screening_entity_class"
        ] != "publication":
            raise AmendmentValidationError(
                "Carry-forward target is not publication"
            )

        doi = row[
            "canonical_identifier"
        ].strip().lower()

        doi_values = {
            item.strip().lower()
            for item
            in baseline_row[
                "doi"
            ].split(";")
            if item.strip()
        }

        if doi not in doi_values:
            raise AmendmentValidationError(
                "Carry-forward canonical DOI "
                "not present on mapped baseline row"
            )

        dedup_values = {
            item.strip().lower()
            for item
            in baseline_row[
                "database_dedup_keys"
            ].split(";")
            if item.strip()
        }

        if (
            "doi:"
            + doi
        ) not in dedup_values:
            raise AmendmentValidationError(
                "Carry-forward target lacks exact "
                "database DOI dedup key"
            )

        if row[
            "mapping_basis"
        ] != (
            "exact_canonical_doi_to_database_dedup_key"
        ):
            raise AmendmentValidationError(
                "In-baseline mapping basis changed"
            )

    out = out_of_baseline[0]

    if out[
        "anchor_id"
    ] != OUT_OF_BASELINE_ANCHOR_ID:
        raise AmendmentValidationError(
            "Unexpected out-of-baseline anchor"
        )

    if out[
        "tool"
    ] != OUT_OF_BASELINE_TOOL:
        raise AmendmentValidationError(
            "Unexpected out-of-baseline tool"
        )

    if (
        out[
            "canonical_identifier"
        ].strip().lower()
        != OUT_OF_BASELINE_DOI
    ):
        raise AmendmentValidationError(
            "Unexpected out-of-baseline canonical DOI"
        )

    if out[
        "screening_entity_id"
    ].strip():
        raise AmendmentValidationError(
            "Out-of-baseline anchor cannot map "
            "to baseline entity"
        )

    if out[
        "mapping_basis"
    ] != "canonical_doi_absent_from_baseline":
        raise AmendmentValidationError(
            "Out-of-baseline mapping basis changed"
        )

    # Fail closed if W0A06's canonical DOI appears anywhere in
    # the immutable baseline.
    for baseline_row in baseline.rows:
        doi_values = {
            item.strip().lower()
            for item
            in baseline_row[
                "doi"
            ].split(";")
            if item.strip()
        }

        if OUT_OF_BASELINE_DOI in doi_values:
            raise AmendmentValidationError(
                "W0A06 canonical DOI unexpectedly "
                "appears in frozen baseline"
            )

    return {
        "status":
            "COMPLETE_RESOLVED_8_EQ_7_PLUS_1",

        "historical_anchor_count":
            EXPECTED_HISTORICAL_ANCHORS,

        "in_baseline_count":
            EXPECTED_IN_BASELINE,

        "out_of_baseline_count":
            EXPECTED_OUT_OF_BASELINE,

        "mapped_screening_entity_ids":
            tuple(
                sorted(
                    mapped_ids
                )
            ),

        "out_of_baseline_anchor_id":
            OUT_OF_BASELINE_ANCHOR_ID,
    }


def load_resolution(
    *,
    path: Path,
    baseline,
) -> dict:
    fields, rows = read_tsv(
        path
    )

    return validate_resolution_rows(
        fields=fields,
        rows=rows,
        baseline=baseline,
    )


def build_compatibility_carry_forward(
    resolution: dict,
) -> dict:
    """
    Adapter for the already-frozen deterministic batch builder.

    The original builder needs only a COMPLETE_UNIQUE_MAPPING status
    and mapped baseline IDs. It does not itself require eight IDs.
    """
    if (
        resolution[
            "status"
        ]
        != "COMPLETE_RESOLVED_8_EQ_7_PLUS_1"
    ):
        raise AmendmentValidationError(
            "Prior-anchor resolution incomplete"
        )

    ids = tuple(
        resolution[
            "mapped_screening_entity_ids"
        ]
    )

    if len(ids) != EXPECTED_IN_BASELINE:
        raise AmendmentValidationError(
            "Compatibility carry-forward requires "
            "exactly seven mapped baseline IDs"
        )

    return {
        "status":
            "COMPLETE_UNIQUE_MAPPING",

        "anchor_count":
            EXPECTED_IN_BASELINE,

        "mapped_screening_entity_ids":
            ids,
    }


def batch_manifest_sha256(
    *,
    base,
    manifests: list[dict[str, str]],
) -> str:
    return sha256_bytes(
        base.tsv_bytes(
            fields=
                list(
                    base.BATCH_MANIFEST_FIELDS
                ),
            rows=manifests,
        )
    )


def active_ids_sha256(
    membership: dict[
        str,
        tuple[str, ...],
    ],
) -> str:
    ordered = [
        entity_id
        for batch_id in sorted(
            membership
        )
        for entity_id
        in membership[
            batch_id
        ]
    ]

    return sha256_bytes(
        canonical_json_bytes(
            ordered
        )
    )


def dry_run_summary(
    *,
    queue_path: Path,
    resolution_path: Path,
    amendment_path: Path,
) -> dict:
    amendment = load_contract_amendment(
        amendment_path
    )

    base = load_frozen_base_module()

    baseline = base.load_baseline(
        queue_path
    )

    resolution = load_resolution(
        path=resolution_path,
        baseline=baseline,
    )

    compatibility = (
        build_compatibility_carry_forward(
            resolution
        )
    )

    manifests, membership = (
        base.build_batch_manifests(
            baseline=baseline,
            carry_forward=
                compatibility,
            max_batch_size=
                amendment[
                    "derived_execution_population"
                ][
                    "max_batch_size"
                ],
        )
    )

    active_count = sum(
        len(ids)
        for ids in membership.values()
    )

    if active_count != EXPECTED_ACTIVE_READY:
        raise AmendmentValidationError(
            "Derived active ready population changed"
        )

    if len(manifests) != EXPECTED_BATCH_COUNT:
        raise AmendmentValidationError(
            "Derived batch count changed"
        )

    if not manifests:
        raise AmendmentValidationError(
            "No deterministic batches generated"
        )

    for row in manifests[:-1]:
        if int(
            row[
                "entity_count"
            ]
        ) != EXPECTED_MAX_BATCH_SIZE:
            raise AmendmentValidationError(
                "Non-terminal batch size changed"
            )

    if int(
        manifests[-1][
            "entity_count"
        ]
    ) != 122:
        raise AmendmentValidationError(
            "Final deterministic batch must contain 122 entities"
        )

    mapped_ids = set(
        resolution[
            "mapped_screening_entity_ids"
        ]
    )

    active_ids = {
        entity_id
        for ids in membership.values()
        for entity_id in ids
    }

    if mapped_ids & active_ids:
        raise AmendmentValidationError(
            "Historical carry-forward target leaked "
            "into active screening batches"
        )

    if len(active_ids) != EXPECTED_ACTIVE_READY:
        raise AmendmentValidationError(
            "Active batch membership not unique"
        )

    for entity_id in baseline.blocked_ids:
        if entity_id in active_ids:
            raise AmendmentValidationError(
                "blocked_metadata entity leaked "
                "into active batch membership"
            )

    return {
        "status":
            "AMENDMENT_01_IMPLEMENTATION_PRE_DECISION",

        "baseline_queue_sha256":
            sha256_file(
                queue_path
            ),

        "historical_prior_anchor_count":
            8,

        "in_baseline_carry_forward_count":
            7,

        "out_of_baseline_prior_anchor_count":
            1,

        "out_of_baseline_anchor_id":
            OUT_OF_BASELINE_ANCHOR_ID,

        "out_of_baseline_anchor_tool":
            OUT_OF_BASELINE_TOOL,

        "out_of_baseline_anchor_doi":
            OUT_OF_BASELINE_DOI,

        "frozen_ready_entity_count":
            len(
                baseline.ready_ids
            ),

        "blocked_metadata_count":
            len(
                baseline.blocked_ids
            ),

        "active_ready_entity_count":
            active_count,

        "max_batch_size":
            EXPECTED_MAX_BATCH_SIZE,

        "batch_count":
            len(
                manifests
            ),

        "first_batch_id":
            manifests[0][
                "batch_id"
            ],

        "last_batch_id":
            manifests[-1][
                "batch_id"
            ],

        "last_batch_entity_count":
            int(
                manifests[-1][
                    "entity_count"
                ]
            ),

        "batch_manifest_sha256":
            batch_manifest_sha256(
                base=base,
                manifests=manifests,
            ),

        "active_ordered_entity_ids_sha256":
            active_ids_sha256(
                membership
            ),

        "batch_generation_contract_validated":
            True,

        # Still dry-run only: no production batch files exist.
        "production_batches_created":
            0,

        "event_ledger_rows":
            0,

        "scientific_screening_decisions":
            0,

        "method_assessments":
            0,

        "role_assignments":
            0,

        "canonical_publication_decisions":
            0,

        "wave1_promotions":
            0,

        "network_access_performed":
            False,

        "execution_output_created":
            False,

        "implementation_may_make_scientific_decisions":
            False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--baseline-queue",
        type=Path,
        default=DEFAULT_QUEUE,
    )

    parser.add_argument(
        "--prior-anchor-resolution",
        type=Path,
        default=DEFAULT_RESOLUTION,
    )

    parser.add_argument(
        "--contract-amendment",
        type=Path,
        default=DEFAULT_AMENDMENT,
    )

    parser.add_argument(
        "--assert-amended-contract",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    result = dry_run_summary(
        queue_path=
            args.baseline_queue.resolve(),

        resolution_path=
            args.prior_anchor_resolution.resolve(),

        amendment_path=
            args.contract_amendment.resolve(),
    )

    if args.assert_amended_contract:
        if result[
            "active_ready_entity_count"
        ] != EXPECTED_ACTIVE_READY:
            raise AmendmentValidationError(
                "Amended active ready count failed"
            )

        if result[
            "batch_count"
        ] != EXPECTED_BATCH_COUNT:
            raise AmendmentValidationError(
                "Amended batch count failed"
            )

        if result[
            "production_batches_created"
        ] != 0:
            raise AmendmentValidationError(
                "Implementation gate created real batches"
            )

        if result[
            "scientific_screening_decisions"
        ] != 0:
            raise AmendmentValidationError(
                "Implementation gate made scientific decisions"
            )

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
