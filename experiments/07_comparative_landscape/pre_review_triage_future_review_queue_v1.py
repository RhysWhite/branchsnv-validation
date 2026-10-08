#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import tempfile

from collections import Counter
from dataclasses import dataclass
from pathlib import Path


SELECTED_CANDIDATE = (
    "linear_svc_balanced_l2_v1"
)

QUEUE_DESIGN_SUMS_REL = Path(
    "experiments/07_comparative_landscape/"
    "pre_review_triage_future_review_queue_v1_design.sha256"
)

SCORING_RESULTS_SUMS_REL = Path(
    "experiments/07_comparative_landscape/"
    "pre_review_triage_future_scoring_results_v1.sha256"
)

SCORED_REL = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_scoring_v1/"
    "scored_records.tsv"
)

COVERAGE_REL = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_scoring_v1/"
    "coverage.tsv"
)

OUTPUT_REL = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_queue_v1"
)

AUTH_REL = Path(
    "experiments/07_comparative_landscape/"
    "pre_review_triage_future_review_queue_v1_"
    "generation_authorization.json"
)

EXPECTED_QUEUE_DESIGN_SUMS_SHA = (
    "319ce18f144b97acc1d6c5b277420bd7"
    "b9f66fce0e99b2b8207a657559ea1e26"
)

EXPECTED_SCORING_RESULTS_SUMS_SHA = (
    "8be5645fb71f557306be11ae132f1d655"
    "013d6a6d573beb50380399cad9bc939"
)

EXPECTED_SCORED_SHA = (
    "70164b0e345d2df0e0fa0c765a293e72"
    "5096ef50096c6bb1025ed72ca06f7d67"
)

EXPECTED_COVERAGE_SHA = (
    "8dde17ef13648cfee4bbec80322377202"
    "eb769cd11e5f3249d59de978e3824b7"
)

EXPECTED_SCOREABLE_ROWS = 11905
EXPECTED_PRIORITY_ROWS = 5483
EXPECTED_RESIDUAL_ROWS = 6422
EXPECTED_UNSCORED_ROWS = 257
EXPECTED_TOTAL_ROWS = 12162

REVIEW_FRACTION_NUMERATOR = 35
REVIEW_FRACTION_DENOMINATOR = 76

AUTHORIZATION_ID = (
    "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_"
    "GENERATION_002"
)

GENERATION_CONFIRMATION = (
    "GENERATE-FROZEN-FUTURE-REVIEW-QUEUE-V1"
)

PRIORITY_NAME = (
    "priority_scored_queue.tsv"
)

RESIDUAL_NAME = (
    "residual_scored_queue.tsv"
)

UNSCORED_NAME = (
    "unscored_manual_review_queue.tsv"
)

MANIFEST_NAME = (
    "queue_manifest.json"
)


class QueueError(
    RuntimeError
):
    pass


@dataclass(
    frozen=True
)
class ScoredRecord:
    retrieval_record_index: int
    screening_entity_id: str
    selected_candidate_id: str
    continuous_score: float
    continuous_score_text: str


@dataclass(
    frozen=True
)
class CoverageRecord:
    retrieval_record_index: int
    screening_entity_id: str
    abstract_status: str
    coverage_status: str


def repo_root() -> Path:
    return (
        Path(__file__)
        .resolve()
        .parents[2]
    )


OUTPUT_ROOT = (
    repo_root()
    / OUTPUT_REL
)


def sha256(
    path: Path,
) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def ceil_fraction_times_n(
    numerator: int,
    denominator: int,
    n: int,
) -> int:

    if denominator <= 0:
        raise QueueError(
            "Invalid fraction denominator"
        )

    if numerator < 0:
        raise QueueError(
            "Invalid fraction numerator"
        )

    if n < 0:
        raise QueueError(
            "Invalid population size"
        )

    return (
        numerator * n
        + denominator
        - 1
    ) // denominator


def load_scored(
    path: Path,
    *,
    expected_count: int | None = None,
    verify_hash: bool = False,
) -> list[ScoredRecord]:

    if not path.is_file():
        raise QueueError(
            "Scored-record input missing"
        )

    if (
        verify_hash
        and sha256(path)
        != EXPECTED_SCORED_SHA
    ):
        raise QueueError(
            "Frozen scored-record identity changed"
        )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        expected_fields = [
            "retrieval_record_index",
            "screening_entity_id",
            "selected_candidate_id",
            "continuous_score",
        ]

        if reader.fieldnames != expected_fields:
            raise QueueError(
                "Scored-record schema changed"
            )

        rows = list(
            reader
        )

    if (
        expected_count is not None
        and len(rows) != expected_count
    ):
        raise QueueError(
            "Scored-record count changed"
        )

    records = []

    for row in rows:

        try:
            index = int(
                row[
                    "retrieval_record_index"
                ]
            )
        except ValueError as exc:
            raise QueueError(
                "Invalid retrieval record index"
            ) from exc

        entity = row[
            "screening_entity_id"
        ]

        if not entity:
            raise QueueError(
                "Blank screening entity ID"
            )

        candidate = row[
            "selected_candidate_id"
        ]

        if (
            candidate
            != SELECTED_CANDIDATE
        ):
            raise QueueError(
                "Selected candidate family drift"
            )

        score_text = row[
            "continuous_score"
        ]

        try:
            score = float(
                score_text
            )
        except ValueError as exc:
            raise QueueError(
                "Invalid continuous score"
            ) from exc

        if not math.isfinite(
            score
        ):
            raise QueueError(
                "Non-finite continuous score"
            )

        records.append(
            ScoredRecord(
                retrieval_record_index=index,
                screening_entity_id=entity,
                selected_candidate_id=candidate,
                continuous_score=score,
                continuous_score_text=score_text,
            )
        )

    ids = [
        record.screening_entity_id
        for record in records
    ]

    indices = [
        record.retrieval_record_index
        for record in records
    ]

    if len(set(ids)) != len(ids):
        raise QueueError(
            "Duplicate scored screening entity ID"
        )

    if (
        len(set(indices))
        != len(indices)
    ):
        raise QueueError(
            "Duplicate scored retrieval index"
        )

    return records


def load_coverage(
    path: Path,
    *,
    expected_count: int | None = None,
    verify_hash: bool = False,
) -> list[CoverageRecord]:

    if not path.is_file():
        raise QueueError(
            "Coverage input missing"
        )

    if (
        verify_hash
        and sha256(path)
        != EXPECTED_COVERAGE_SHA
    ):
        raise QueueError(
            "Frozen coverage identity changed"
        )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        expected_fields = [
            "retrieval_record_index",
            "screening_entity_id",
            "abstract_status",
            "coverage_status",
        ]

        if reader.fieldnames != expected_fields:
            raise QueueError(
                "Coverage schema changed"
            )

        rows = list(
            reader
        )

    if (
        expected_count is not None
        and len(rows) != expected_count
    ):
        raise QueueError(
            "Coverage row count changed"
        )

    records = []

    for row in rows:

        try:
            index = int(
                row[
                    "retrieval_record_index"
                ]
            )
        except ValueError as exc:
            raise QueueError(
                "Invalid coverage retrieval index"
            ) from exc

        entity = row[
            "screening_entity_id"
        ]

        if not entity:
            raise QueueError(
                "Blank coverage screening entity ID"
            )

        status = row[
            "coverage_status"
        ]

        if status not in {
            "scored",
            "no_normalized_text",
        }:
            raise QueueError(
                "Unexpected coverage status"
            )

        records.append(
            CoverageRecord(
                retrieval_record_index=index,
                screening_entity_id=entity,
                abstract_status=row[
                    "abstract_status"
                ],
                coverage_status=status,
            )
        )

    ids = [
        record.screening_entity_id
        for record in records
    ]

    indices = [
        record.retrieval_record_index
        for record in records
    ]

    if len(set(ids)) != len(ids):
        raise QueueError(
            "Duplicate coverage screening entity ID"
        )

    if (
        len(set(indices))
        != len(indices)
    ):
        raise QueueError(
            "Duplicate coverage retrieval index"
        )

    return records


def validate_cross_sets(
    scored: list[ScoredRecord],
    coverage: list[CoverageRecord],
) -> None:

    scored_ids = [
        record.screening_entity_id
        for record in scored
    ]

    coverage_ids = [
        record.screening_entity_id
        for record in coverage
    ]

    if (
        len(set(scored_ids))
        != len(scored_ids)
    ):
        raise QueueError(
            "Duplicate scored identity"
        )

    if (
        len(set(coverage_ids))
        != len(coverage_ids)
    ):
        raise QueueError(
            "Duplicate coverage identity"
        )

    coverage_scored_ids = {
        record.screening_entity_id
        for record in coverage
        if record.coverage_status
        == "scored"
    }

    if (
        set(scored_ids)
        != coverage_scored_ids
    ):
        raise QueueError(
            "Scored/coverage identity mismatch"
        )

    no_text_ids = {
        record.screening_entity_id
        for record in coverage
        if record.coverage_status
        == "no_normalized_text"
    }

    if (
        set(scored_ids)
        & no_text_ids
    ):
        raise QueueError(
            "No-text row entered scored population"
        )


def rank_scored(
    records: list[ScoredRecord],
) -> list[ScoredRecord]:

    return sorted(
        records,
        key=lambda record: (
            -record.continuous_score,
            record.screening_entity_id,
        ),
    )


def partition_ranked(
    ranked: list[ScoredRecord],
    priority_count: int,
) -> tuple[
    list[ScoredRecord],
    list[ScoredRecord],
]:

    if not (
        0
        <= priority_count
        <= len(ranked)
    ):
        raise QueueError(
            "Invalid priority prefix count"
        )

    return (
        ranked[
            :priority_count
        ],
        ranked[
            priority_count:
        ],
    )


def order_unscored(
    coverage: list[CoverageRecord],
) -> list[CoverageRecord]:

    return sorted(
        (
            record
            for record in coverage
            if record.coverage_status
            == "no_normalized_text"
        ),
        key=lambda record: (
            record.retrieval_record_index,
            record.screening_entity_id,
        ),
    )


def load_real_inputs() -> tuple[
    list[ScoredRecord],
    list[CoverageRecord],
]:

    root = repo_root()

    scored = load_scored(
        root / SCORED_REL,
        expected_count=(
            EXPECTED_SCOREABLE_ROWS
        ),
        verify_hash=True,
    )

    coverage = load_coverage(
        root / COVERAGE_REL,
        expected_count=(
            EXPECTED_TOTAL_ROWS
        ),
        verify_hash=True,
    )

    validate_cross_sets(
        scored,
        coverage,
    )

    statuses = Counter(
        record.coverage_status
        for record in coverage
    )

    if statuses != {
        "scored":
            EXPECTED_SCOREABLE_ROWS,

        "no_normalized_text":
            EXPECTED_UNSCORED_ROWS,
    }:
        raise QueueError(
            "Frozen coverage counts changed"
        )

    no_text_statuses = Counter(
        record.abstract_status
        for record in coverage
        if record.coverage_status
        == "no_normalized_text"
    )

    if no_text_statuses != {
        "abstract_absent": 246,
        "provider_not_found": 10,
        "openalex_position_gap": 1,
    }:
        raise QueueError(
            "No-text provenance counts changed"
        )

    return (
        scored,
        coverage,
    )


def build_real_queues(
    scored: list[ScoredRecord],
    coverage: list[CoverageRecord],
) -> tuple[
    list[ScoredRecord],
    list[ScoredRecord],
    list[CoverageRecord],
]:

    validate_cross_sets(
        scored,
        coverage,
    )

    if (
        len(scored)
        != EXPECTED_SCOREABLE_ROWS
    ):
        raise QueueError(
            "Unexpected scoreable population"
        )

    if (
        len(coverage)
        != EXPECTED_TOTAL_ROWS
    ):
        raise QueueError(
            "Unexpected future population"
        )

    expected_priority = (
        ceil_fraction_times_n(
            REVIEW_FRACTION_NUMERATOR,
            REVIEW_FRACTION_DENOMINATOR,
            len(scored),
        )
    )

    if (
        expected_priority
        != EXPECTED_PRIORITY_ROWS
    ):
        raise QueueError(
            "Frozen priority-prefix count changed"
        )

    ranked = rank_scored(
        scored
    )

    priority, residual = (
        partition_ranked(
            ranked,
            expected_priority,
        )
    )

    manual = order_unscored(
        coverage
    )

    if (
        len(priority)
        != EXPECTED_PRIORITY_ROWS
    ):
        raise QueueError(
            "Priority queue count changed"
        )

    if (
        len(residual)
        != EXPECTED_RESIDUAL_ROWS
    ):
        raise QueueError(
            "Residual queue count changed"
        )

    if (
        len(manual)
        != EXPECTED_UNSCORED_ROWS
    ):
        raise QueueError(
            "Manual-review count changed"
        )

    priority_ids = {
        record.screening_entity_id
        for record in priority
    }

    residual_ids = {
        record.screening_entity_id
        for record in residual
    }

    manual_ids = {
        record.screening_entity_id
        for record in manual
    }

    if (
        priority_ids
        & residual_ids
    ):
        raise QueueError(
            "Priority/residual overlap"
        )

    if (
        priority_ids
        & manual_ids
    ):
        raise QueueError(
            "Priority/manual overlap"
        )

    if (
        residual_ids
        & manual_ids
    ):
        raise QueueError(
            "Residual/manual overlap"
        )

    if (
        len(
            priority_ids
            | residual_ids
            | manual_ids
        )
        != EXPECTED_TOTAL_ROWS
    ):
        raise QueueError(
            "Review universe does not close"
        )

    return (
        priority,
        residual,
        manual,
    )


def scored_queue_rows(
    records: list[ScoredRecord],
) -> list[dict[str, str]]:

    return [
        {
            "queue_position":
                str(position),

            "retrieval_record_index":
                str(
                    record.retrieval_record_index
                ),

            "screening_entity_id":
                record.screening_entity_id,

            "selected_candidate_id":
                record.selected_candidate_id,

            "continuous_score":
                record.continuous_score_text,
        }
        for position, record
        in enumerate(
            records,
            start=1,
        )
    ]


def manual_queue_rows(
    records: list[CoverageRecord],
) -> list[dict[str, str]]:

    return [
        {
            "queue_position":
                str(position),

            "retrieval_record_index":
                str(
                    record.retrieval_record_index
                ),

            "screening_entity_id":
                record.screening_entity_id,

            "abstract_status":
                record.abstract_status,

            "coverage_status":
                record.coverage_status,
        }
        for position, record
        in enumerate(
            records,
            start=1,
        )
    ]


def write_tsv(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


def build_manifest(
    priority: list[ScoredRecord],
    residual: list[ScoredRecord],
    manual: list[CoverageRecord],
) -> dict:

    return {
        "schema_version":
            1,

        "status":
            "FUTURE_REVIEW_QUEUE_GENERATED_PRE_REVIEW",

        "selected_candidate_id":
            SELECTED_CANDIDATE,

        "operating_point": {
            "candidate_fraction_numerator":
                REVIEW_FRACTION_NUMERATOR,

            "candidate_fraction_denominator":
                REVIEW_FRACTION_DENOMINATOR,

            "prefix_count_rule":
                "ceil_exact_fraction_times_scoreable_population",

            "raw_score_threshold_selected":
                False,
        },

        "ranking_policy":
            (
                "continuous_score_descending_"
                "then_screening_entity_id_ascending"
            ),

        "lanes": {
            "priority_scored_queue":
                len(priority),

            "residual_scored_queue":
                len(residual),

            "unscored_manual_review_queue":
                len(manual),

            "total_human_review_universe":
                (
                    len(priority)
                    + len(residual)
                    + len(manual)
                ),
        },

        "unscored_ordering":
            "retrieval_record_index_ascending",

        "cross_lane_priority_defined":
            False,

        "scientific_boundary": {
            "automatic_scientific_inclusion":
                False,

            "automatic_scientific_exclusion":
                False,

            "hard_prediction":
                False,

            "raw_score_threshold":
                False,

            "blind_validation_content_used":
                False,

            "future_labels_used":
                False,

            "production_ledger_mutated":
                False,
        },

        "source_identity": {
            "queue_design_checksum_manifest_sha256":
                EXPECTED_QUEUE_DESIGN_SUMS_SHA,

            "future_scoring_results_checksum_manifest_sha256":
                EXPECTED_SCORING_RESULTS_SUMS_SHA,

            "scored_records_sha256":
                EXPECTED_SCORED_SHA,

            "coverage_sha256":
                EXPECTED_COVERAGE_SHA,
        },
    }


def write_outputs(
    root: Path,
    priority: list[ScoredRecord],
    residual: list[ScoredRecord],
    manual: list[CoverageRecord],
) -> None:

    root.mkdir(
        parents=True,
        exist_ok=False,
    )

    priority_path = (
        root
        / PRIORITY_NAME
    )

    residual_path = (
        root
        / RESIDUAL_NAME
    )

    manual_path = (
        root
        / UNSCORED_NAME
    )

    write_tsv(
        priority_path,
        [
            "queue_position",
            "retrieval_record_index",
            "screening_entity_id",
            "selected_candidate_id",
            "continuous_score",
        ],
        scored_queue_rows(
            priority
        ),
    )

    write_tsv(
        residual_path,
        [
            "queue_position",
            "retrieval_record_index",
            "screening_entity_id",
            "selected_candidate_id",
            "continuous_score",
        ],
        scored_queue_rows(
            residual
        ),
    )

    write_tsv(
        manual_path,
        [
            "queue_position",
            "retrieval_record_index",
            "screening_entity_id",
            "abstract_status",
            "coverage_status",
        ],
        manual_queue_rows(
            manual
        ),
    )

    manifest = build_manifest(
        priority,
        residual,
        manual,
    )

    manifest[
        "artifact_sha256"
    ] = {
        PRIORITY_NAME:
            sha256(
                priority_path
            ),

        RESIDUAL_NAME:
            sha256(
                residual_path
            ),

        UNSCORED_NAME:
            sha256(
                manual_path
            ),
    }

    (
        root
        / MANIFEST_NAME
    ).write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def verify_dependencies() -> None:

    root = repo_root()

    exact = {
        QUEUE_DESIGN_SUMS_REL:
            EXPECTED_QUEUE_DESIGN_SUMS_SHA,

        SCORING_RESULTS_SUMS_REL:
            EXPECTED_SCORING_RESULTS_SUMS_SHA,

        SCORED_REL:
            EXPECTED_SCORED_SHA,

        COVERAGE_REL:
            EXPECTED_COVERAGE_SHA,
    }

    for rel, expected in exact.items():

        path = root / rel

        if not path.is_file():
            raise QueueError(
                "Frozen dependency missing: "
                + str(rel)
            )

        if sha256(path) != expected:
            raise QueueError(
                "Frozen dependency changed: "
                + str(rel)
            )


def expected_authorization_payload() -> dict:

    return {
        "schema_version":
            1,

        "status":
            "AUTHORIZED_ONE_USE",

        "authorization_id":
            AUTHORIZATION_ID,

        "generation_authorized":
            True,

        "one_use":
            True,

        "design_checksum_manifest_sha256":
            EXPECTED_QUEUE_DESIGN_SUMS_SHA,

        "expected_priority_scored_rows":
            EXPECTED_PRIORITY_ROWS,

        "expected_residual_scored_rows":
            EXPECTED_RESIDUAL_ROWS,

        "expected_unscored_manual_review_rows":
            EXPECTED_UNSCORED_ROWS,

        "expected_total_human_review_rows":
            EXPECTED_TOTAL_ROWS,

        "output_root":
            str(
                OUTPUT_REL
            ),

        "scientific_decision_authorized":
            False,

        "blind_validation_content_use_authorized":
            False,

        "future_label_use_authorized":
            False,

        "confirmation":
            GENERATION_CONFIRMATION,
    }


def validate_generation_authorization(
    path: Path,
    confirmation: str,
) -> None:

    if confirmation != GENERATION_CONFIRMATION:
        raise QueueError(
            "Exact generation confirmation required"
        )

    if not path.is_file():
        raise QueueError(
            "Generation authorization missing"
        )

    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError as exc:
        raise QueueError(
            "Generation authorization is invalid JSON"
        ) from exc

    if (
        value
        != expected_authorization_payload()
    ):
        raise QueueError(
            "Generation authorization payload mismatch"
        )


def execute_authorized(
    authorization_path: Path,
    confirmation: str,
) -> None:

    validate_generation_authorization(
        authorization_path,
        confirmation,
    )

    verify_dependencies()

    if OUTPUT_ROOT.exists():
        raise QueueError(
            "Canonical review-queue output already exists"
        )

    scored, coverage = (
        load_real_inputs()
    )

    priority, residual, manual = (
        build_real_queues(
            scored,
            coverage,
        )
    )

    parent = OUTPUT_ROOT.parent

    parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    staging_parent = Path(
        tempfile.mkdtemp(
            prefix=(
                ".pre_review_triage_"
                "future_review_queue_v1."
            ),
            dir=parent,
        )
    )

    payload = (
        staging_parent
        / "payload"
    )

    try:
        write_outputs(
            payload,
            priority,
            residual,
            manual,
        )

        produced = {
            path.name
            for path in payload.iterdir()
            if path.is_file()
        }

        expected = {
            PRIORITY_NAME,
            RESIDUAL_NAME,
            UNSCORED_NAME,
            MANIFEST_NAME,
        }

        if produced != expected:
            raise QueueError(
                "Generated artifact set changed"
            )

        os.replace(
            payload,
            OUTPUT_ROOT,
        )

    finally:
        if staging_parent.exists():
            shutil.rmtree(
                staging_parent
            )


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--authorization",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--confirm",
        required=True,
    )

    args = parser.parse_args()

    execute_authorized(
        args.authorization,
        args.confirm,
    )

    print(
        json.dumps(
            json.loads(
                (
                    OUTPUT_ROOT
                    / MANIFEST_NAME
                ).read_text(
                    encoding="utf-8"
                )
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
