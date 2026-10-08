#!/usr/bin/env python3

"""
Experiment 07 controlled baseline scientific-screening execution machinery.

This module implements operational infrastructure only.

It does NOT:
- make scientific screening decisions;
- automatically classify records;
- resolve metadata blockers;
- infer prior Wave 0 anchor mappings;
- perform network requests;
- select canonical publications;
- perform method-level assessment;
- assign analytical roles or directness;
- promote Wave 1 anchors;
- claim screening completion or saturation; or
- write production execution output from its default CLI.

The immutable scientific-screening baseline remains the previously frozen
production queue.

Real batch generation is fail-closed until all eight prior Wave 0 anchor
adjudications have been uniquely mapped to frozen baseline entities.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
import argparse
import csv
import hashlib
import io
import json
import re


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

DEFAULT_DESIGN = (
    HERE
    / "baseline_scientific_screening_execution_design.json"
)

DEFAULT_EXECUTION_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_execution"
)


EXPECTED_QUEUE_SHA256 = (
    "97575b71c4607c3dcad893d90210f913"
    "2a83d0ae2e299ac2f1aef7e94f527d58"
)

EXPECTED_SCREENING_ENTITY_COUNT = 95113
EXPECTED_READY_COUNT = 94629
EXPECTED_BLOCKED_COUNT = 484
EXPECTED_PRIOR_ANCHOR_COUNT = 8

DEFAULT_MAX_BATCH_SIZE = 500


QUEUE_FIELDS = [
    "screening_entity_id",
    "screening_entity_class",
    "publication_reconciliation_key",
    "database_dedup_keys",
    "biotools_id",
    "citation_provenance_ids",
    "discovery_stages",
    "citation_wave_provenance",
    "title_or_software_name",
    "title_variants",
    "year",
    "doi",
    "pmid",
    "openalex_id",
    "omid",
    "identity_attention_status",
    "metadata_screenability",
    "screening_state",
    "record_decision",
    "exclusion_reason_code",
    "candidate_method_flag",
    "evidence_escalation_status",
    "operator",
    "decision_batch",
    "notes",
]


CARRY_FORWARD_FIELDS = [
    "anchor_id",
    "prior_adjudication_source_id",
    "prior_adjudication_source_sha256",
    "screening_entity_id",
    "mapping_basis",
    "record_decision",
    "exclusion_reason_code",
    "candidate_method_flag",
    "notes",
]


BATCH_MANIFEST_FIELDS = [
    "batch_id",
    "batch_index",
    "entity_count",
    "first_screening_entity_id",
    "last_screening_entity_id",
    "ordered_entity_ids_sha256",
]


EVENT_FIELDS = [
    "event_id",
    "event_type",
    "screening_entity_id",
    "baseline_queue_sha256",
    "baseline_row_sha256",
    "batch_id",
    "record_decision",
    "exclusion_reason_code",
    "candidate_method_flag",
    "evidence_basis",
    "evidence_source_locator",
    "evidence_escalation_status",
    "operator_id",
    "operator_type",
    "decision_timestamp_utc",
    "supersedes_event_id",
    "reviewer_id",
    "review_status",
    "adjudication_status",
    "notes",
]


TERMINAL_DECISIONS = {
    "exclude",
    "retain_for_method_assessment",
}


EXCLUSION_REASONS = {
    "application_only_no_reusable_method",
    "duplicate_record_same_method_no_distinct_capability",
    "unrelated_variant_or_data_type",
    "unsupported_by_primary_or_stable_authoritative_source",
}


EVENT_TYPES = {
    "record_decision",
    "source_escalation",
    "superseding_record_decision",
}


OPERATOR_TYPES = {
    "human",
    "human_with_assistance",
}


HEX64 = re.compile(
    r"^[0-9a-f]{64}$"
)


class ExecutionValidationError(
    RuntimeError
):
    pass


@dataclass(
    frozen=True
)
class Baseline:
    fields: list[str]
    rows: list[dict[str, str]]
    by_id: dict[str, dict[str, str]]
    row_sha256: dict[str, str]
    ready_ids: tuple[str, ...]
    blocked_ids: tuple[str, ...]


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
    value,
    *,
    newline: bool = True,
) -> bytes:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    if newline:
        rendered += "\n"

    return rendered.encode(
        "utf-8"
    )


def canonical_row_sha256(
    row: dict[str, str],
) -> str:
    """
    Deterministic provenance hash for one immutable baseline row.

    Field names participate through canonical sorted JSON.
    """
    return sha256_bytes(
        canonical_json_bytes(
            row,
            newline=False,
        )
    )


def ordered_ids_sha256(
    values: Iterable[str],
) -> str:
    """
    Hash ordered batch membership without ambiguity.
    """
    return sha256_bytes(
        canonical_json_bytes(
            list(
                values
            ),
            newline=False,
        )
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


def tsv_bytes(
    *,
    fields: list[str],
    rows: list[dict[str, str]],
) -> bytes:
    stream = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        stream,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )

    writer.writeheader()

    for row in rows:
        if set(
            row
        ) != set(
            fields
        ):
            raise ExecutionValidationError(
                "TSV row schema mismatch"
            )

        writer.writerow(
            row
        )

    return stream.getvalue().encode(
        "utf-8"
    )


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
        raise ExecutionValidationError(
            "Execution design is not "
            "FROZEN_PRE_IMPLEMENTATION"
        )

    if value[
        "immutable_baseline"
    ][
        "queue_sha256"
    ] != EXPECTED_QUEUE_SHA256:
        raise ExecutionValidationError(
            "Frozen queue SHA changed in design"
        )

    if value[
        "baseline_population"
    ][
        "screening_entities"
    ] != EXPECTED_SCREENING_ENTITY_COUNT:
        raise ExecutionValidationError(
            "Frozen baseline count changed"
        )

    if value[
        "baseline_population"
    ][
        "ready"
    ] != EXPECTED_READY_COUNT:
        raise ExecutionValidationError(
            "Frozen ready count changed"
        )

    if value[
        "baseline_population"
    ][
        "blocked_metadata"
    ] != EXPECTED_BLOCKED_COUNT:
        raise ExecutionValidationError(
            "Frozen blocked count changed"
        )

    if value[
        "implementation_may_make_scientific_decisions"
    ] is not False:
        raise ExecutionValidationError(
            "Execution design authorises "
            "implementation decisions"
        )

    return value


def load_baseline(
    path: Path,
) -> Baseline:
    if sha256_file(
        path
    ) != EXPECTED_QUEUE_SHA256:
        raise ExecutionValidationError(
            "Baseline queue SHA mismatch"
        )

    fields, rows = read_tsv(
        path
    )

    if fields != QUEUE_FIELDS:
        raise ExecutionValidationError(
            "Baseline queue schema changed"
        )

    if len(
        rows
    ) != EXPECTED_SCREENING_ENTITY_COUNT:
        raise ExecutionValidationError(
            "Baseline row count changed"
        )

    ids = [
        row[
            "screening_entity_id"
        ]
        for row in rows
    ]

    if ids != sorted(
        ids
    ):
        raise ExecutionValidationError(
            "Baseline queue ordering changed"
        )

    if len(
        set(
            ids
        )
    ) != len(
        ids
    ):
        raise ExecutionValidationError(
            "Duplicate baseline entity ID"
        )

    states = Counter(
        row[
            "screening_state"
        ]
        for row in rows
    )

    if states != Counter({
        "ready":
            EXPECTED_READY_COUNT,

        "blocked_metadata":
            EXPECTED_BLOCKED_COUNT,
    }):
        raise ExecutionValidationError(
            "Baseline screening-state counts changed"
        )

    scientific_fields = [
        "record_decision",
        "exclusion_reason_code",
        "candidate_method_flag",
        "evidence_escalation_status",
        "operator",
        "decision_batch",
        "notes",
    ]

    for row in rows:
        for field in scientific_fields:
            if row[
                field
            ]:
                raise ExecutionValidationError(
                    "Immutable baseline already contains "
                    "scientific decision data"
                )

    by_id = {
        row[
            "screening_entity_id"
        ]:
            row
        for row in rows
    }

    hashes = {
        entity_id:
            canonical_row_sha256(
                row
            )
        for entity_id, row
        in by_id.items()
    }

    ready_ids = tuple(
        row[
            "screening_entity_id"
        ]
        for row in rows
        if row[
            "screening_state"
        ] == "ready"
    )

    blocked_ids = tuple(
        row[
            "screening_entity_id"
        ]
        for row in rows
        if row[
            "screening_state"
        ] == "blocked_metadata"
    )

    return Baseline(
        fields=fields,
        rows=rows,
        by_id=by_id,
        row_sha256=hashes,
        ready_ids=ready_ids,
        blocked_ids=blocked_ids,
    )


def validate_terminal_fields(
    *,
    record_decision: str,
    exclusion_reason_code: str,
    candidate_method_flag: str,
) -> None:
    if (
        record_decision
        not in TERMINAL_DECISIONS
    ):
        raise ExecutionValidationError(
            "Unknown terminal record decision"
        )

    if (
        record_decision
        == "retain_for_method_assessment"
    ):
        if (
            candidate_method_flag
            != "true"
        ):
            raise ExecutionValidationError(
                "Retained record must have "
                "candidate_method_flag=true"
            )

        if exclusion_reason_code:
            raise ExecutionValidationError(
                "Retained record cannot have "
                "exclusion reason"
            )

        return

    if (
        candidate_method_flag
        != "false"
    ):
        raise ExecutionValidationError(
            "Excluded record must have "
            "candidate_method_flag=false"
        )

    if (
        exclusion_reason_code
        not in EXCLUSION_REASONS
    ):
        raise ExecutionValidationError(
            "Excluded record requires one "
            "frozen exclusion reason"
        )


def validate_carry_forward_rows(
    *,
    fields: list[str],
    rows: list[dict[str, str]],
    baseline: Baseline,
) -> dict:
    if fields != CARRY_FORWARD_FIELDS:
        raise ExecutionValidationError(
            "Prior-adjudication mapping schema changed"
        )

    if len(
        rows
    ) != EXPECTED_PRIOR_ANCHOR_COUNT:
        raise ExecutionValidationError(
            "Prior-adjudication mapping must "
            "contain exactly eight anchors"
        )

    anchors = set()
    entities = set()

    for row in rows:
        anchor_id = row[
            "anchor_id"
        ].strip()

        entity_id = row[
            "screening_entity_id"
        ].strip()

        source_id = row[
            "prior_adjudication_source_id"
        ].strip()

        source_sha = row[
            "prior_adjudication_source_sha256"
        ].strip()

        mapping_basis = row[
            "mapping_basis"
        ].strip()

        if not anchor_id:
            raise ExecutionValidationError(
                "Carry-forward anchor ID empty"
            )

        if anchor_id in anchors:
            raise ExecutionValidationError(
                "Duplicate carry-forward anchor"
            )

        anchors.add(
            anchor_id
        )

        if entity_id in entities:
            raise ExecutionValidationError(
                "Multiple anchors map to same "
                "baseline screening entity"
            )

        entities.add(
            entity_id
        )

        if entity_id not in baseline.by_id:
            raise ExecutionValidationError(
                "Carry-forward maps outside baseline"
            )

        if (
            baseline.by_id[
                entity_id
            ][
                "screening_state"
            ]
            != "ready"
        ):
            raise ExecutionValidationError(
                "Carry-forward cannot map to "
                "blocked_metadata entity"
            )

        if not source_id:
            raise ExecutionValidationError(
                "Carry-forward lacks prior source ID"
            )

        if not HEX64.fullmatch(
            source_sha
        ):
            raise ExecutionValidationError(
                "Carry-forward prior source SHA "
                "is not SHA-256"
            )

        if not mapping_basis:
            raise ExecutionValidationError(
                "Carry-forward mapping basis empty"
            )

        lowered = mapping_basis.lower()

        for forbidden in [
            "fuzzy",
            "semantic",
            "title_similarity",
            "title-only",
            "title_only",
        ]:
            if forbidden in lowered:
                raise ExecutionValidationError(
                    "Carry-forward uses prohibited "
                    "non-exact mapping basis"
                )

        validate_terminal_fields(
            record_decision=
                row[
                    "record_decision"
                ],

            exclusion_reason_code=
                row[
                    "exclusion_reason_code"
                ],

            candidate_method_flag=
                row[
                    "candidate_method_flag"
                ],
        )

    return {
        "status":
            "COMPLETE_UNIQUE_MAPPING",

        "anchor_count":
            len(
                anchors
            ),

        "mapped_screening_entity_ids":
            tuple(
                sorted(
                    entities
                )
            ),
    }


def load_carry_forward_map(
    *,
    path: Path | None,
    baseline: Baseline,
) -> dict:
    if path is None:
        return {
            "status":
                "PENDING_FROZEN_MAPPING",

            "anchor_count":
                0,

            "mapped_screening_entity_ids":
                tuple(),
        }

    fields, rows = read_tsv(
        path
    )

    return validate_carry_forward_rows(
        fields=fields,
        rows=rows,
        baseline=baseline,
    )


def build_batch_manifests(
    *,
    baseline: Baseline,
    carry_forward: dict,
    max_batch_size: int = DEFAULT_MAX_BATCH_SIZE,
) -> tuple[
    list[dict[str, str]],
    dict[str, tuple[str, ...]],
]:
    if (
        carry_forward[
            "status"
        ]
        != "COMPLETE_UNIQUE_MAPPING"
    ):
        raise ExecutionValidationError(
            "Real batch generation prohibited "
            "until prior Wave 0 carry-forward "
            "mapping is complete"
        )

    if max_batch_size < 1:
        raise ExecutionValidationError(
            "Batch size must be positive"
        )

    carried = set(
        carry_forward[
            "mapped_screening_entity_ids"
        ]
    )

    active = [
        entity_id
        for entity_id
        in baseline.ready_ids
        if entity_id
        not in carried
    ]

    if active != sorted(
        active
    ):
        raise ExecutionValidationError(
            "Active screening population "
            "not deterministically ordered"
        )

    manifests = []
    membership = {}

    for offset in range(
        0,
        len(active),
        max_batch_size,
    ):
        batch_index = (
            len(
                manifests
            )
            + 1
        )

        batch_id = (
            f"B{batch_index:06d}"
        )

        ids = tuple(
            active[
                offset:
                offset
                + max_batch_size
            ]
        )

        membership[
            batch_id
        ] = ids

        manifests.append({
            "batch_id":
                batch_id,

            "batch_index":
                str(
                    batch_index
                ),

            "entity_count":
                str(
                    len(ids)
                ),

            "first_screening_entity_id":
                ids[0],

            "last_screening_entity_id":
                ids[-1],

            "ordered_entity_ids_sha256":
                ordered_ids_sha256(
                    ids
                ),
        })

    covered = [
        entity_id
        for batch_id in sorted(
            membership
        )
        for entity_id
        in membership[
            batch_id
        ]
    ]

    if covered != active:
        raise ExecutionValidationError(
            "Batch membership lost or reordered "
            "active entities"
        )

    return manifests, membership


def validate_utc_timestamp(
    value: str,
) -> None:
    if not value.endswith(
        "Z"
    ):
        raise ExecutionValidationError(
            "Decision timestamp must be UTC Z"
        )

    try:
        datetime.fromisoformat(
            value[
                :-1
            ]
            + "+00:00"
        )

    except ValueError as exc:
        raise ExecutionValidationError(
            "Invalid decision timestamp"
        ) from exc


def validate_event_row(
    *,
    row: dict[str, str],
    baseline: Baseline,
    batch_membership: dict[
        str,
        tuple[str, ...],
    ],
    existing_event_ids: set[str],
    prior_events_by_id: dict[
        str,
        dict[str, str],
    ],
) -> None:
    if set(
        row
    ) != set(
        EVENT_FIELDS
    ):
        raise ExecutionValidationError(
            "Event schema mismatch"
        )

    event_id = row[
        "event_id"
    ].strip()

    if not event_id:
        raise ExecutionValidationError(
            "Event ID empty"
        )

    if event_id in existing_event_ids:
        raise ExecutionValidationError(
            "Duplicate event ID"
        )

    event_type = row[
        "event_type"
    ].strip()

    if event_type not in EVENT_TYPES:
        raise ExecutionValidationError(
            "Unknown event type"
        )

    entity_id = row[
        "screening_entity_id"
    ].strip()

    if entity_id not in baseline.by_id:
        raise ExecutionValidationError(
            "Event entity outside baseline"
        )

    baseline_row = baseline.by_id[
        entity_id
    ]

    if (
        baseline_row[
            "screening_state"
        ]
        == "blocked_metadata"
    ):
        raise ExecutionValidationError(
            "blocked_metadata entity cannot "
            "receive scientific event"
        )

    if (
        row[
            "baseline_queue_sha256"
        ]
        != EXPECTED_QUEUE_SHA256
    ):
        raise ExecutionValidationError(
            "Event baseline queue SHA mismatch"
        )

    if (
        row[
            "baseline_row_sha256"
        ]
        != baseline.row_sha256[
            entity_id
        ]
    ):
        raise ExecutionValidationError(
            "Event baseline row SHA mismatch"
        )

    batch_id = row[
        "batch_id"
    ].strip()

    if batch_id not in batch_membership:
        raise ExecutionValidationError(
            "Event batch ID unknown"
        )

    if (
        entity_id
        not in batch_membership[
            batch_id
        ]
    ):
        raise ExecutionValidationError(
            "Event entity not a member "
            "of declared batch"
        )

    if (
        row[
            "operator_type"
        ]
        not in OPERATOR_TYPES
    ):
        raise ExecutionValidationError(
            "Unknown operator type"
        )

    if not row[
        "operator_id"
    ].strip():
        raise ExecutionValidationError(
            "Operator ID empty"
        )

    validate_utc_timestamp(
        row[
            "decision_timestamp_utc"
        ]
    )

    supersedes = row[
        "supersedes_event_id"
    ].strip()

    if supersedes:
        prior = prior_events_by_id.get(
            supersedes
        )

        if prior is None:
            raise ExecutionValidationError(
                "Superseded event does not exist"
            )

        if (
            prior[
                "screening_entity_id"
            ]
            != entity_id
        ):
            raise ExecutionValidationError(
                "Supersession crosses entities"
            )

        if (
            event_type
            != "superseding_record_decision"
        ):
            raise ExecutionValidationError(
                "Only superseding event type may "
                "reference supersedes_event_id"
            )

    elif (
        event_type
        == "superseding_record_decision"
    ):
        raise ExecutionValidationError(
            "Superseding event lacks prior event"
        )

    if (
        event_type
        == "source_escalation"
    ):
        if row[
            "record_decision"
        ]:
            raise ExecutionValidationError(
                "Source escalation cannot "
                "contain terminal decision"
            )

        if row[
            "candidate_method_flag"
        ]:
            raise ExecutionValidationError(
                "Source escalation cannot "
                "contain candidate flag"
            )

        if row[
            "exclusion_reason_code"
        ]:
            raise ExecutionValidationError(
                "Source escalation cannot "
                "contain exclusion reason"
            )

        if (
            row[
                "evidence_escalation_status"
            ]
            != "awaiting_source_escalation"
        ):
            raise ExecutionValidationError(
                "Source escalation event must "
                "be awaiting_source_escalation"
            )

    else:
        validate_terminal_fields(
            record_decision=
                row[
                    "record_decision"
                ],

            exclusion_reason_code=
                row[
                    "exclusion_reason_code"
                ],

            candidate_method_flag=
                row[
                    "candidate_method_flag"
                ],
        )

        if (
            row[
                "evidence_escalation_status"
            ]
            not in {
                "",
                "resolved",
            }
        ):
            raise ExecutionValidationError(
                "Terminal decision has invalid "
                "evidence escalation status"
            )


def validate_event_ledger(
    *,
    fields: list[str],
    rows: list[dict[str, str]],
    baseline: Baseline,
    batch_membership: dict[
        str,
        tuple[str, ...],
    ],
) -> dict:
    if fields != EVENT_FIELDS:
        raise ExecutionValidationError(
            "Event ledger schema changed"
        )

    event_ids = set()
    by_id = {}

    for row in rows:
        validate_event_row(
            row=row,
            baseline=baseline,
            batch_membership=
                batch_membership,
            existing_event_ids=
                event_ids,
            prior_events_by_id=
                by_id,
        )

        event_id = row[
            "event_id"
        ]

        event_ids.add(
            event_id
        )

        by_id[
            event_id
        ] = row

    superseded = {
        row[
            "supersedes_event_id"
        ]
        for row in rows
        if row[
            "supersedes_event_id"
        ]
    }

    current_events = [
        row
        for row in rows
        if row[
            "event_id"
        ]
        not in superseded
    ]

    by_entity = {}

    for row in current_events:
        by_entity.setdefault(
            row[
                "screening_entity_id"
            ],
            []
        ).append(
            row
        )

    state_counts = Counter()

    for entity_id in baseline.ready_ids:
        events = by_entity.get(
            entity_id,
            [],
        )

        terminal = [
            row
            for row in events
            if row[
                "record_decision"
            ]
            in TERMINAL_DECISIONS
        ]

        escalations = [
            row
            for row in events
            if row[
                "event_type"
            ]
            == "source_escalation"
        ]

        if len(
            terminal
        ) > 1:
            raise ExecutionValidationError(
                "Conflicting unsuperseded "
                "terminal events"
            )

        if terminal:
            state_counts[
                "complete"
            ] += 1

        elif escalations:
            state_counts[
                "awaiting_source_escalation"
            ] += 1

        else:
            state_counts[
                "ready"
            ] += 1

    state_counts[
        "blocked_metadata"
    ] = len(
        baseline.blocked_ids
    )

    return {
        "event_count":
            len(
                rows
            ),

        "current_event_count":
            len(
                current_events
            ),

        "state_counts":
            dict(
                sorted(
                    state_counts.items()
                )
            ),
    }


def dry_run_summary(
    *,
    design_path: Path,
    queue_path: Path,
    carry_forward_path: Path | None,
) -> dict:
    design = load_design(
        design_path
    )

    baseline = load_baseline(
        queue_path
    )

    carry_forward = (
        load_carry_forward_map(
            path=carry_forward_path,
            baseline=baseline,
        )
    )

    batch_generation_authorized = (
        carry_forward[
            "status"
        ]
        == "COMPLETE_UNIQUE_MAPPING"
    )

    batch_count = None
    active_ready_count = None

    if batch_generation_authorized:
        manifests, membership = (
            build_batch_manifests(
                baseline=baseline,
                carry_forward=
                    carry_forward,
                max_batch_size=
                    design[
                        "batching"
                    ][
                        "default_max_batch_size"
                    ],
            )
        )

        batch_count = len(
            manifests
        )

        active_ready_count = sum(
            len(ids)
            for ids
            in membership.values()
        )

    return {
        "status":
            "EXECUTION_IMPLEMENTATION_PRE_DECISION",

        "baseline_queue_sha256":
            sha256_file(
                queue_path
            ),

        "screening_entity_count":
            len(
                baseline.rows
            ),

        "ready_entity_count":
            len(
                baseline.ready_ids
            ),

        "blocked_metadata_count":
            len(
                baseline.blocked_ids
            ),

        "prior_adjudication_mapping_status":
            carry_forward[
                "status"
            ],

        "prior_adjudication_mapped_count":
            carry_forward[
                "anchor_count"
            ],

        "batch_generation_authorized":
            batch_generation_authorized,

        "active_ready_entity_count":
            active_ready_count,

        "batch_count":
            batch_count,

        "default_max_batch_size":
            DEFAULT_MAX_BATCH_SIZE,

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

        "execution_output_created":
            False,

        "network_access_performed":
            False,

        "implementation_may_make_scientific_decisions":
            False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--design",
        type=Path,
        default=DEFAULT_DESIGN,
    )

    parser.add_argument(
        "--baseline-queue",
        type=Path,
        default=DEFAULT_QUEUE,
    )

    parser.add_argument(
        "--prior-carry-forward-map",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--assert-frozen-baseline",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    result = dry_run_summary(
        design_path=
            args.design.resolve(),

        queue_path=
            args.baseline_queue.resolve(),

        carry_forward_path=(
            args.prior_carry_forward_map.resolve()
            if args.prior_carry_forward_map
            is not None
            else None
        ),
    )

    if args.assert_frozen_baseline:
        if (
            result[
                "screening_entity_count"
            ]
            != EXPECTED_SCREENING_ENTITY_COUNT
        ):
            raise ExecutionValidationError(
                "Frozen entity count failed"
            )

        if (
            result[
                "ready_entity_count"
            ]
            != EXPECTED_READY_COUNT
        ):
            raise ExecutionValidationError(
                "Frozen ready count failed"
            )

        if (
            result[
                "blocked_metadata_count"
            ]
            != EXPECTED_BLOCKED_COUNT
        ):
            raise ExecutionValidationError(
                "Frozen blocked count failed"
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
