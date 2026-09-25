#!/usr/bin/env python3

"""
Experiment 07 pre-decision execution-production writer and validator.

This implementation constructs the frozen eight-artifact genesis package for
controlled baseline scientific-screening execution.

Default invocation is dry-run only.

It does NOT:
- make scientific screening decisions;
- create scientific event rows;
- authorise event entry;
- modify the frozen baseline;
- modify historical anchor adjudications;
- perform method assessment;
- assign roles/directness;
- select canonical publications;
- promote Wave 1 anchors;
- perform network access.

A write operation is permitted only to a new, safe output directory. The
writer constructs the package in a temporary sibling directory, validates it,
and atomically publishes the directory only after all checks pass.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import csv
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

RESULTS_ROOT = (
    REPO_ROOT
    / "results"
    / "07_comparative_landscape"
)

SCREENING_ROOT = (
    RESULTS_ROOT
    / "scientific_screening"
)

DEFAULT_EXECUTION_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_execution"
)

DEFAULT_QUEUE = (
    SCREENING_ROOT
    / "baseline_screening_queue.tsv"
)

DEFAULT_RESOLUTION = (
    HERE
    / "prior_wave0_baseline_presence_resolution.tsv"
)

DEFAULT_CONTRACT = (
    HERE
    / "baseline_scientific_screening_execution_contract_amendment_01.json"
)

DEFAULT_DESIGN = (
    HERE
    / "pre_decision_execution_production_artifact_design.json"
)

AMENDMENT_SOURCE = (
    HERE
    / "baseline_scientific_screening_execution_amendment_01.py"
)

AMENDMENT_FREEZE = (
    HERE
    / "baseline_scientific_screening_execution_amendment_01_implementation.json"
)

DESIGN_CHECKSUM_FREEZE = (
    HERE
    / "pre_decision_execution_production_artifact_design.sha256"
)


EXPECTED_QUEUE_SHA256 = (
    "97575b71c4607c3dcad893d90210f913"
    "2a83d0ae2e299ac2f1aef7e94f527d58"
)

EXPECTED_BATCH_MANIFEST_SHA256 = (
    "f2cc2c7ccaf230a56f9aa27f991b128"
    "85b600338b68b81d660af895f48adbfe0"
)

EXPECTED_ACTIVE_IDS_SHA256 = (
    "d0970cbd5a582ce05585926bc1e81acb"
    "a502b01a96acc4b84ab8db454a0ea4c1"
)

EXPECTED_LEDGER_GENESIS_SHA256 = (
    "d3ff9be1efe2b1237f616f25e702275c"
    "cc608577fa0ff8b301401a72900eb55f"
)

EXPECTED_LEDGER_GENESIS_BYTES = 338

EXPECTED_ACTIVE_COUNT = 94622
EXPECTED_BATCH_COUNT = 190
EXPECTED_CARRY_FORWARD_COUNT = 7
EXPECTED_OUT_OF_BASELINE_COUNT = 1
EXPECTED_BLOCKED_COUNT = 484

OUT_OF_BASELINE_ANCHOR_ID = "W0A06"
OUT_OF_BASELINE_TOOL = "kSNP3.0"
OUT_OF_BASELINE_DOI = "10.1093/bioinformatics/btv271"


BATCH_MEMBERSHIP_FIELDS = [
    "batch_id",
    "batch_index",
    "position_in_batch",
    "global_active_index",
    "screening_entity_id",
    "baseline_row_sha256",
]


CARRY_FORWARD_FIELDS = [
    "anchor_id",
    "tool",
    "canonical_doi",
    "screening_entity_id",
    "baseline_row_sha256",
    "prior_anchor_decision",
    "prior_landscape_decision",
    "prior_confirmed_role",
    "record_decision",
    "candidate_method_flag",
    "mapping_basis",
    "source_resolution_sha256",
    "scientific_reassessment_performed",
]


OUT_OF_BASELINE_FIELDS = [
    "anchor_id",
    "tool",
    "canonical_doi",
    "prior_anchor_decision",
    "prior_landscape_decision",
    "prior_confirmed_role",
    "baseline_presence_status",
    "screening_entity_id",
    "preservation_status",
    "source_resolution_sha256",
    "scientific_reassessment_performed",
]


GENESIS_ARTIFACT_NAMES = {
    "batch_manifest.tsv",
    "batch_membership.tsv",
    "prior_anchor_carry_forwards.tsv",
    "out_of_baseline_prior_anchor.tsv",
    "event_ledger.tsv",
    "event_ledger_genesis.json",
    "manifest.json",
    "immutable_checksums.sha256",
}


IMMUTABLE_CHECKSUM_NAMES = [
    "batch_manifest.tsv",
    "batch_membership.tsv",
    "prior_anchor_carry_forwards.tsv",
    "out_of_baseline_prior_anchor.tsv",
    "event_ledger_genesis.json",
    "manifest.json",
]


class ProductionWriterError(
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


def pretty_json_bytes(
    value: Any,
) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    ).encode(
        "utf-8"
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


def load_frozen_amendment_module():
    freeze = json.loads(
        AMENDMENT_FREEZE.read_text(
            encoding="utf-8"
        )
    )

    expected = freeze[
        "implementation"
    ][
        "sha256"
    ]

    observed = sha256_file(
        AMENDMENT_SOURCE
    )

    if observed != expected:
        raise ProductionWriterError(
            "Frozen amendment implementation SHA mismatch"
        )

    module_name = (
        "baseline_scientific_screening_execution_"
        "amendment_01_for_production_writer"
    )

    spec = importlib.util.spec_from_file_location(
        module_name,
        AMENDMENT_SOURCE,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise ProductionWriterError(
            "Unable to load frozen amendment implementation"
        )

    if str(HERE) not in sys.path:
        sys.path.insert(
            0,
            str(HERE),
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        module_name
    ] = module

    spec.loader.exec_module(
        module
    )

    return module


def load_design(
    path: Path,
) -> dict:
    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if value[
        "status"
    ] != "FROZEN_PRE_IMPLEMENTATION":
        raise ProductionWriterError(
            "Production-artifact design not frozen "
            "pre-implementation"
        )

    if value[
        "artifact_count_at_genesis"
    ] != 8:
        raise ProductionWriterError(
            "Genesis artifact count changed"
        )

    if set(
        value[
            "artifacts"
        ]
    ) != GENESIS_ARTIFACT_NAMES:
        raise ProductionWriterError(
            "Genesis artifact set changed"
        )

    if value[
        "immutable_baseline"
    ][
        "queue_sha256"
    ] != EXPECTED_QUEUE_SHA256:
        raise ProductionWriterError(
            "Design baseline queue SHA changed"
        )

    batch = value[
        "batch_contract"
    ]

    if batch[
        "active_ready_entities"
    ] != EXPECTED_ACTIVE_COUNT:
        raise ProductionWriterError(
            "Design active entity count changed"
        )

    if batch[
        "batch_count"
    ] != EXPECTED_BATCH_COUNT:
        raise ProductionWriterError(
            "Design batch count changed"
        )

    if batch[
        "batch_manifest_sha256"
    ] != EXPECTED_BATCH_MANIFEST_SHA256:
        raise ProductionWriterError(
            "Design batch-manifest SHA changed"
        )

    if batch[
        "active_ordered_entity_ids_sha256"
    ] != EXPECTED_ACTIVE_IDS_SHA256:
        raise ProductionWriterError(
            "Design ordered active-ID SHA changed"
        )

    ledger = value[
        "artifacts"
    ][
        "event_ledger.tsv"
    ]

    if ledger[
        "genesis_sha256"
    ] != EXPECTED_LEDGER_GENESIS_SHA256:
        raise ProductionWriterError(
            "Design ledger genesis SHA changed"
        )

    if ledger[
        "genesis_bytes"
    ] != EXPECTED_LEDGER_GENESIS_BYTES:
        raise ProductionWriterError(
            "Design ledger genesis size changed"
        )

    if value[
        "event_entry_authorized"
    ] is not False:
        raise ProductionWriterError(
            "Design unexpectedly authorises event entry"
        )

    return value


def ensure_within(
    child: Path,
    parent: Path,
) -> bool:
    try:
        child.relative_to(
            parent
        )

        return True

    except ValueError:
        return False


def validate_output_destination(
    path: Path,
) -> None:
    resolved = path.resolve()

    screening = SCREENING_ROOT.resolve()
    experiment_sources = HERE.resolve()

    if (
        resolved == screening
        or ensure_within(
            resolved,
            screening,
        )
    ):
        raise ProductionWriterError(
            "Execution output cannot overwrite or "
            "live inside frozen scientific-screening production"
        )

    if (
        resolved == experiment_sources
        or ensure_within(
            resolved,
            experiment_sources,
        )
    ):
        raise ProductionWriterError(
            "Execution output cannot overwrite or "
            "live inside tracked experiment sources"
        )

    if resolved.exists():
        raise ProductionWriterError(
            "Output destination already exists"
        )

    if not resolved.parent.is_dir():
        raise ProductionWriterError(
            "Output parent directory does not exist"
        )


def reconstruct_execution_state(
    *,
    queue_path: Path,
    resolution_path: Path,
    contract_path: Path,
    design_path: Path,
):
    design = load_design(
        design_path
    )

    amend = load_frozen_amendment_module()

    base = amend.load_frozen_base_module()

    baseline = base.load_baseline(
        queue_path
    )

    contract = amend.load_contract_amendment(
        contract_path
    )

    resolution = amend.load_resolution(
        path=resolution_path,
        baseline=baseline,
    )

    compatibility = (
        amend.build_compatibility_carry_forward(
            resolution
        )
    )

    manifests, membership = (
        base.build_batch_manifests(
            baseline=baseline,
            carry_forward=
                compatibility,
            max_batch_size=
                design[
                    "batch_contract"
                ][
                    "max_batch_size"
                ],
        )
    )

    manifest_bytes = base.tsv_bytes(
        fields=
            list(
                base.BATCH_MANIFEST_FIELDS
            ),
        rows=manifests,
    )

    if sha256_bytes(
        manifest_bytes
    ) != EXPECTED_BATCH_MANIFEST_SHA256:
        raise ProductionWriterError(
            "Reconstructed batch-manifest SHA mismatch"
        )

    active_ids_hash = amend.active_ids_sha256(
        membership
    )

    if (
        active_ids_hash
        != EXPECTED_ACTIVE_IDS_SHA256
    ):
        raise ProductionWriterError(
            "Reconstructed ordered active-ID SHA mismatch"
        )

    active_count = sum(
        len(ids)
        for ids in membership.values()
    )

    if active_count != EXPECTED_ACTIVE_COUNT:
        raise ProductionWriterError(
            "Reconstructed active entity count mismatch"
        )

    if len(
        manifests
    ) != EXPECTED_BATCH_COUNT:
        raise ProductionWriterError(
            "Reconstructed batch count mismatch"
        )

    return {
        "design":
            design,

        "amend":
            amend,

        "base":
            base,

        "baseline":
            baseline,

        "contract":
            contract,

        "resolution":
            resolution,

        "manifests":
            manifests,

        "membership":
            membership,

        "batch_manifest_bytes":
            manifest_bytes,
    }


def build_membership_rows(
    *,
    state: dict,
) -> list[dict[str, str]]:
    baseline = state[
        "baseline"
    ]

    manifests = state[
        "manifests"
    ]

    membership = state[
        "membership"
    ]

    rows = []

    global_index = 0

    for manifest in manifests:
        batch_id = manifest[
            "batch_id"
        ]

        batch_index = int(
            manifest[
                "batch_index"
            ]
        )

        ids = membership[
            batch_id
        ]

        if len(
            ids
        ) != int(
            manifest[
                "entity_count"
            ]
        ):
            raise ProductionWriterError(
                "Batch membership count mismatch"
            )

        for position, entity_id in enumerate(
            ids,
            start=1,
        ):
            global_index += 1

            rows.append({
                "batch_id":
                    batch_id,

                "batch_index":
                    str(
                        batch_index
                    ),

                "position_in_batch":
                    str(
                        position
                    ),

                "global_active_index":
                    str(
                        global_index
                    ),

                "screening_entity_id":
                    entity_id,

                "baseline_row_sha256":
                    baseline.row_sha256[
                        entity_id
                    ],
            })

    if global_index != EXPECTED_ACTIVE_COUNT:
        raise ProductionWriterError(
            "Membership table row count mismatch"
        )

    entity_ids = [
        row[
            "screening_entity_id"
        ]
        for row in rows
    ]

    if len(
        set(
            entity_ids
        )
    ) != EXPECTED_ACTIVE_COUNT:
        raise ProductionWriterError(
            "Duplicate active entity in membership table"
        )

    semantic_hash = sha256_bytes(
        canonical_json_bytes(
            entity_ids
        )
    )

    if (
        semantic_hash
        != EXPECTED_ACTIVE_IDS_SHA256
    ):
        raise ProductionWriterError(
            "Membership semantic ordered-ID SHA mismatch"
        )

    return rows


def build_anchor_rows(
    *,
    state: dict,
    resolution_path: Path,
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
]:
    baseline = state[
        "baseline"
    ]

    _, raw_rows = read_tsv(
        resolution_path
    )

    resolution_sha = sha256_file(
        resolution_path
    )

    in_baseline = sorted(
        [
            row
            for row in raw_rows
            if row[
                "baseline_presence_status"
            ] == "in_baseline"
        ],
        key=lambda row:
            row[
                "anchor_id"
            ],
    )

    out_of_baseline = [
        row
        for row in raw_rows
        if row[
            "baseline_presence_status"
        ] == "out_of_baseline"
    ]

    if len(
        in_baseline
    ) != EXPECTED_CARRY_FORWARD_COUNT:
        raise ProductionWriterError(
            "Carry-forward row count changed"
        )

    if len(
        out_of_baseline
    ) != EXPECTED_OUT_OF_BASELINE_COUNT:
        raise ProductionWriterError(
            "Out-of-baseline anchor count changed"
        )

    carry_rows = []

    for row in in_baseline:
        entity_id = row[
            "screening_entity_id"
        ]

        carry_rows.append({
            "anchor_id":
                row[
                    "anchor_id"
                ],

            "tool":
                row[
                    "tool"
                ],

            "canonical_doi":
                row[
                    "canonical_identifier"
                ],

            "screening_entity_id":
                entity_id,

            "baseline_row_sha256":
                baseline.row_sha256[
                    entity_id
                ],

            "prior_anchor_decision":
                row[
                    "prior_anchor_decision"
                ],

            "prior_landscape_decision":
                row[
                    "prior_landscape_decision"
                ],

            "prior_confirmed_role":
                row[
                    "prior_confirmed_role"
                ],

            "record_decision":
                row[
                    "record_decision_projection"
                ],

            "candidate_method_flag":
                row[
                    "candidate_method_flag_projection"
                ],

            "mapping_basis":
                row[
                    "mapping_basis"
                ],

            "source_resolution_sha256":
                resolution_sha,

            "scientific_reassessment_performed":
                row[
                    "scientific_reassessment_performed"
                ],
        })

    out = out_of_baseline[
        0
    ]

    if (
        out[
            "anchor_id"
        ]
        != OUT_OF_BASELINE_ANCHOR_ID
        or out[
            "tool"
        ]
        != OUT_OF_BASELINE_TOOL
        or out[
            "canonical_identifier"
        ].lower()
        != OUT_OF_BASELINE_DOI
        or out[
            "screening_entity_id"
        ]
    ):
        raise ProductionWriterError(
            "Out-of-baseline W0A06 identity changed"
        )

    out_rows = [{
        "anchor_id":
            out[
                "anchor_id"
            ],

        "tool":
            out[
                "tool"
            ],

        "canonical_doi":
            out[
                "canonical_identifier"
            ],

        "prior_anchor_decision":
            out[
                "prior_anchor_decision"
            ],

        "prior_landscape_decision":
            out[
                "prior_landscape_decision"
            ],

        "prior_confirmed_role":
            out[
                "prior_confirmed_role"
            ],

        "baseline_presence_status":
            out[
                "baseline_presence_status"
            ],

        "screening_entity_id":
            "",

        "preservation_status":
            (
                "prior_adjudication_preserved_"
                "without_baseline_row"
            ),

        "source_resolution_sha256":
            resolution_sha,

        "scientific_reassessment_performed":
            out[
                "scientific_reassessment_performed"
            ],
    }]

    return (
        carry_rows,
        out_rows,
    )


def build_package_bytes(
    *,
    queue_path: Path,
    resolution_path: Path,
    contract_path: Path,
    design_path: Path,
) -> tuple[
    dict[str, bytes],
    dict,
]:
    state = reconstruct_execution_state(
        queue_path=queue_path,
        resolution_path=
            resolution_path,
        contract_path=
            contract_path,
        design_path=
            design_path,
    )

    design = state[
        "design"
    ]

    base = state[
        "base"
    ]

    membership_rows = (
        build_membership_rows(
            state=state
        )
    )

    carry_rows, out_rows = (
        build_anchor_rows(
            state=state,
            resolution_path=
                resolution_path,
        )
    )

    batch_manifest_bytes = state[
        "batch_manifest_bytes"
    ]

    membership_bytes = base.tsv_bytes(
        fields=
            BATCH_MEMBERSHIP_FIELDS,
        rows=
            membership_rows,
    )

    carry_bytes = base.tsv_bytes(
        fields=
            CARRY_FORWARD_FIELDS,
        rows=
            carry_rows,
    )

    out_bytes = base.tsv_bytes(
        fields=
            OUT_OF_BASELINE_FIELDS,
        rows=
            out_rows,
    )

    event_ledger_bytes = base.tsv_bytes(
        fields=
            list(
                base.EVENT_FIELDS
            ),
        rows=[],
    )

    if len(
        event_ledger_bytes
    ) != EXPECTED_LEDGER_GENESIS_BYTES:
        raise ProductionWriterError(
            "Event-ledger genesis byte count mismatch"
        )

    if sha256_bytes(
        event_ledger_bytes
    ) != EXPECTED_LEDGER_GENESIS_SHA256:
        raise ProductionWriterError(
            "Event-ledger genesis SHA mismatch"
        )

    event_genesis = {
        "status":
            "EVENT_LEDGER_GENESIS",

        "schema_version":
            1,

        "event_fields":
            list(
                base.EVENT_FIELDS
            ),

        "genesis_event_row_count":
            0,

        "genesis_bytes":
            EXPECTED_LEDGER_GENESIS_BYTES,

        "genesis_sha256":
            EXPECTED_LEDGER_GENESIS_SHA256,

        "baseline_queue_sha256":
            EXPECTED_QUEUE_SHA256,

        "amendment_implementation_commit":
            design[
                "parent_amendment_implementation_commit"
            ],

        "append_only_after_genesis":
            True,

        "event_entry_authorized":
            False,

        "scientific_screening_decisions":
            0,
    }

    event_genesis_bytes = pretty_json_bytes(
        event_genesis
    )

    immutable_payloads = {
        "batch_manifest.tsv":
            batch_manifest_bytes,

        "batch_membership.tsv":
            membership_bytes,

        "prior_anchor_carry_forwards.tsv":
            carry_bytes,

        "out_of_baseline_prior_anchor.tsv":
            out_bytes,

        "event_ledger_genesis.json":
            event_genesis_bytes,
    }

    immutable_payload_sha = {
        name:
            sha256_bytes(
                payload
            )
        for name, payload
        in immutable_payloads.items()
    }

    manifest = {
        "status":
            "PRE_DECISION_EXECUTION_PRODUCTION",

        "schema_version":
            1,

        "baseline_queue_sha256":
            EXPECTED_QUEUE_SHA256,

        "upstream_freeze_sha256":
            {
                **design[
                    "immutable_dependencies"
                ],

                "production_artifact_design_json_sha256":
                    sha256_file(
                        design_path
                    ),

                "production_artifact_design_checksum_manifest_sha256":
                    sha256_file(
                        DESIGN_CHECKSUM_FREEZE
                    ),
            },

        "historical_prior_anchor_count":
            8,

        "in_baseline_carry_forward_count":
            7,

        "out_of_baseline_prior_anchor_count":
            1,

        "blocked_metadata_count":
            EXPECTED_BLOCKED_COUNT,

        "active_screening_entity_count":
            EXPECTED_ACTIVE_COUNT,

        "max_batch_size":
            500,

        "batch_count":
            EXPECTED_BATCH_COUNT,

        "first_batch_id":
            "B000001",

        "last_batch_id":
            "B000190",

        "last_batch_entity_count":
            122,

        "batch_manifest_sha256":
            EXPECTED_BATCH_MANIFEST_SHA256,

        "active_ordered_entity_ids_sha256":
            EXPECTED_ACTIVE_IDS_SHA256,

        "immutable_payload_sha256":
            immutable_payload_sha,

        "event_ledger": {
            "row_count":
                0,

            "genesis_sha256":
                EXPECTED_LEDGER_GENESIS_SHA256,

            "genesis_bytes":
                EXPECTED_LEDGER_GENESIS_BYTES,

            "append_only_after_future_authorisation":
                True,

            "event_entry_authorized":
                False,
        },

        "scientific_boundary": {
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
        },

        "network_access_performed":
            False,

        "current_state_is_derived_projection":
            True,

        "authoritative_membership_source":
            "batch_membership.tsv",

        "immutable_checksum_coverage":
            list(
                IMMUTABLE_CHECKSUM_NAMES
            ),
    }

    manifest_bytes = pretty_json_bytes(
        manifest
    )

    payloads = {
        **immutable_payloads,

        "event_ledger.tsv":
            event_ledger_bytes,

        "manifest.json":
            manifest_bytes,
    }

    checksum_lines = []

    for name in IMMUTABLE_CHECKSUM_NAMES:
        payload = payloads[
            name
        ]

        checksum_lines.append(
            f"{sha256_bytes(payload)}  {name}\n"
        )

    checksum_bytes = "".join(
        checksum_lines
    ).encode(
        "utf-8"
    )

    payloads[
        "immutable_checksums.sha256"
    ] = checksum_bytes

    if set(
        payloads
    ) != GENESIS_ARTIFACT_NAMES:
        raise ProductionWriterError(
            "Built artifact set differs from frozen design"
        )

    artifact_hashes = {
        name:
            sha256_bytes(
                payload
            )
        for name, payload
        in sorted(
            payloads.items()
        )
    }

    package_identity = sha256_bytes(
        canonical_json_bytes(
            artifact_hashes
        )
    )

    summary = {
        "status":
            "PRE_DECISION_EXECUTION_PACKAGE_DRY_RUN",

        "artifact_count":
            len(
                payloads
            ),

        "artifact_sha256":
            artifact_hashes,

        "package_identity_sha256":
            package_identity,

        "batch_manifest_sha256":
            artifact_hashes[
                "batch_manifest.tsv"
            ],

        "active_ordered_entity_ids_sha256":
            EXPECTED_ACTIVE_IDS_SHA256,

        "batch_membership_rows":
            len(
                membership_rows
            ),

        "batch_count":
            len(
                state[
                    "manifests"
                ]
            ),

        "carry_forward_rows":
            len(
                carry_rows
            ),

        "out_of_baseline_anchor_rows":
            len(
                out_rows
            ),

        "event_ledger_rows":
            0,

        "event_ledger_genesis_sha256":
            sha256_bytes(
                event_ledger_bytes
            ),

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
    }

    if (
        summary[
            "batch_manifest_sha256"
        ]
        != EXPECTED_BATCH_MANIFEST_SHA256
    ):
        raise ProductionWriterError(
            "Final batch-manifest file SHA mismatch"
        )

    if (
        summary[
            "batch_membership_rows"
        ]
        != EXPECTED_ACTIVE_COUNT
    ):
        raise ProductionWriterError(
            "Final membership row count mismatch"
        )

    if (
        summary[
            "batch_count"
        ]
        != EXPECTED_BATCH_COUNT
    ):
        raise ProductionWriterError(
            "Final batch count mismatch"
        )

    return (
        payloads,
        summary,
    )


def validate_checksum_ledger(
    *,
    root: Path,
) -> None:
    checksum_path = (
        root
        / "immutable_checksums.sha256"
    )

    lines = checksum_path.read_text(
        encoding="utf-8"
    ).splitlines()

    if len(
        lines
    ) != len(
        IMMUTABLE_CHECKSUM_NAMES
    ):
        raise ProductionWriterError(
            "Immutable checksum ledger row count mismatch"
        )

    observed_names = []

    for line in lines:
        parts = line.split(
            "  ",
            1,
        )

        if len(
            parts
        ) != 2:
            raise ProductionWriterError(
                "Malformed immutable checksum ledger"
            )

        expected_sha, name = parts

        observed_names.append(
            name
        )

        path = root / name

        if not path.is_file():
            raise ProductionWriterError(
                "Immutable checksum target missing"
            )

        if sha256_file(
            path
        ) != expected_sha:
            raise ProductionWriterError(
                f"Immutable checksum failure: {name}"
            )

    if (
        observed_names
        != IMMUTABLE_CHECKSUM_NAMES
    ):
        raise ProductionWriterError(
            "Immutable checksum coverage/order changed"
        )


def validate_package_directory(
    *,
    root: Path,
    queue_path: Path,
    resolution_path: Path,
    contract_path: Path,
    design_path: Path,
) -> dict:
    if not root.is_dir():
        raise ProductionWriterError(
            "Execution package root does not exist"
        )

    paths = list(
        root.iterdir()
    )

    if any(
        path.is_symlink()
        for path in paths
    ):
        raise ProductionWriterError(
            "Execution package cannot contain symlinks"
        )

    if any(
        not path.is_file()
        for path in paths
    ):
        raise ProductionWriterError(
            "Execution package may contain files only"
        )

    observed_names = {
        path.name
        for path in paths
    }

    if (
        observed_names
        != GENESIS_ARTIFACT_NAMES
    ):
        raise ProductionWriterError(
            "Execution package artifact set mismatch"
        )

    expected_payloads, expected_summary = (
        build_package_bytes(
            queue_path=queue_path,
            resolution_path=
                resolution_path,
            contract_path=
                contract_path,
            design_path=
                design_path,
        )
    )

    for name, expected_bytes in (
        expected_payloads.items()
    ):
        observed = (
            root
            / name
        ).read_bytes()

        if observed != expected_bytes:
            raise ProductionWriterError(
                f"Execution package byte mismatch: {name}"
            )

    validate_checksum_ledger(
        root=root
    )

    fields, event_rows = read_tsv(
        root
        / "event_ledger.tsv"
    )

    amendment = (
        load_frozen_amendment_module()
    )

    base = (
        amendment.load_frozen_base_module()
    )

    if fields != list(
        base.EVENT_FIELDS
    ):
        raise ProductionWriterError(
            "Event-ledger schema mismatch"
        )

    if event_rows:
        raise ProductionWriterError(
            "Pre-decision event ledger must be header-only"
        )

    if sha256_file(
        root
        / "event_ledger.tsv"
    ) != EXPECTED_LEDGER_GENESIS_SHA256:
        raise ProductionWriterError(
            "Event-ledger genesis SHA mismatch"
        )

    manifest = json.loads(
        (
            root
            / "manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    if manifest[
        "status"
    ] != "PRE_DECISION_EXECUTION_PRODUCTION":
        raise ProductionWriterError(
            "Execution manifest status mismatch"
        )

    if manifest[
        "active_screening_entity_count"
    ] != EXPECTED_ACTIVE_COUNT:
        raise ProductionWriterError(
            "Execution manifest active count mismatch"
        )

    if manifest[
        "batch_count"
    ] != EXPECTED_BATCH_COUNT:
        raise ProductionWriterError(
            "Execution manifest batch count mismatch"
        )

    if manifest[
        "event_ledger"
    ][
        "row_count"
    ] != 0:
        raise ProductionWriterError(
            "Execution manifest event row count non-zero"
        )

    if manifest[
        "event_ledger"
    ][
        "event_entry_authorized"
    ] is not False:
        raise ProductionWriterError(
            "Execution manifest authorises events"
        )

    if any(
        value != 0
        for value in manifest[
            "scientific_boundary"
        ].values()
    ):
        raise ProductionWriterError(
            "Execution manifest scientific boundary non-zero"
        )

    result = dict(
        expected_summary
    )

    result[
        "status"
    ] = "PRE_DECISION_EXECUTION_PACKAGE_VALID"

    result[
        "execution_output_created"
    ] = True

    result[
        "validated_output_root"
    ] = str(
        root.resolve()
    )

    return result


def write_package_atomic(
    *,
    output_root: Path,
    queue_path: Path,
    resolution_path: Path,
    contract_path: Path,
    design_path: Path,
) -> dict:
    validate_output_destination(
        output_root
    )

    payloads, _ = build_package_bytes(
        queue_path=queue_path,
        resolution_path=
            resolution_path,
        contract_path=
            contract_path,
        design_path=
            design_path,
    )

    parent = output_root.resolve().parent

    temp_root = Path(
        tempfile.mkdtemp(
            prefix=(
                "."
                + output_root.name
                + ".tmp."
            ),
            dir=parent,
        )
    )

    published = False

    try:
        for name in sorted(
            payloads
        ):
            (
                temp_root
                / name
            ).write_bytes(
                payloads[
                    name
                ]
            )

        validate_package_directory(
            root=temp_root,
            queue_path=queue_path,
            resolution_path=
                resolution_path,
            contract_path=
                contract_path,
            design_path=
                design_path,
        )

        os.replace(
            temp_root,
            output_root.resolve(),
        )

        published = True

        result = (
            validate_package_directory(
                root=output_root.resolve(),
                queue_path=queue_path,
                resolution_path=
                    resolution_path,
                contract_path=
                    contract_path,
                design_path=
                    design_path,
            )
        )

        result[
            "atomic_publication_performed"
        ] = True

        return result

    finally:
        if (
            not published
            and temp_root.exists()
        ):
            shutil.rmtree(
                temp_root
            )


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
        default=DEFAULT_CONTRACT,
    )

    parser.add_argument(
        "--design",
        type=Path,
        default=DEFAULT_DESIGN,
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--write-output-root",
        type=Path,
        default=None,
    )

    group.add_argument(
        "--validate-output-root",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--assert-frozen-contract",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    queue_path = (
        args.baseline_queue.resolve()
    )

    resolution_path = (
        args.prior_anchor_resolution.resolve()
    )

    contract_path = (
        args.contract_amendment.resolve()
    )

    design_path = (
        args.design.resolve()
    )

    if args.write_output_root is not None:
        result = write_package_atomic(
            output_root=
                args.write_output_root,
            queue_path=queue_path,
            resolution_path=
                resolution_path,
            contract_path=
                contract_path,
            design_path=
                design_path,
        )

    elif args.validate_output_root is not None:
        result = validate_package_directory(
            root=
                args.validate_output_root.resolve(),
            queue_path=queue_path,
            resolution_path=
                resolution_path,
            contract_path=
                contract_path,
            design_path=
                design_path,
        )

    else:
        _, result = build_package_bytes(
            queue_path=queue_path,
            resolution_path=
                resolution_path,
            contract_path=
                contract_path,
            design_path=
                design_path,
        )

    if args.assert_frozen_contract:
        if result[
            "batch_manifest_sha256"
        ] != EXPECTED_BATCH_MANIFEST_SHA256:
            raise ProductionWriterError(
                "Frozen batch-manifest SHA assertion failed"
            )

        if result[
            "active_ordered_entity_ids_sha256"
        ] != EXPECTED_ACTIVE_IDS_SHA256:
            raise ProductionWriterError(
                "Frozen ordered active-ID SHA assertion failed"
            )

        if result[
            "batch_membership_rows"
        ] != EXPECTED_ACTIVE_COUNT:
            raise ProductionWriterError(
                "Frozen active membership count assertion failed"
            )

        if result[
            "batch_count"
        ] != EXPECTED_BATCH_COUNT:
            raise ProductionWriterError(
                "Frozen batch count assertion failed"
            )

        if result[
            "event_ledger_rows"
        ] != 0:
            raise ProductionWriterError(
                "Pre-decision event ledger is not empty"
            )

        if result[
            "scientific_screening_decisions"
        ] != 0:
            raise ProductionWriterError(
                "Scientific decision count is not zero"
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
