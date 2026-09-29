from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess


ROOT_REL = "experiments/07_comparative_landscape"

INPUT_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_evaluator_v1/"
    "development_evaluation_v1/"
    "outer_scores.tsv"
)

EXPECTED_INPUT_SHA256 = (
    "1da5b38902d893a91cb99b7d9965f179717667c42b66ff80f63313ac50251c47"
)

OUTPUT_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1"
)

SELECTED_FAMILY = "linear_svc_balanced_l2_v1"

BATCHES = (
    "B000001",
    "B000002",
    "B000003",
    "B000004",
    "B000005",
    "B000006",
    "B000007",
    "B000008",
    "B000009",
)

EXPECTED_BATCH_COUNTS = {
    "B000001": 454,
    "B000002": 380,
    "B000003": 423,
    "B000004": 471,
    "B000005": 475,
    "B000006": 491,
    "B000007": 497,
    "B000008": 499,
    "B000009": 500,
}

EXPECTED_BATCH_POSITIVES = {
    "B000001": 67,
    "B000002": 7,
    "B000003": 6,
    "B000004": 9,
    "B000005": 5,
    "B000006": 10,
    "B000007": 3,
    "B000008": 6,
    "B000009": 55,
}


class CurveError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScoreRecord:
    screening_entity_id: str
    batch_id: str
    label_numeric: int
    continuous_score: float


def repo_root() -> Path:
    return Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()
    ).resolve()


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def read_scores() -> list[ScoreRecord]:
    path = repo_root() / INPUT_REL

    if not path.is_file():
        raise CurveError(
            "Frozen development OOF score artifact missing"
        )

    if sha256(path) != EXPECTED_INPUT_SHA256:
        raise CurveError(
            "Frozen development OOF score artifact hash changed"
        )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    if len(rows) != 4190:
        raise CurveError(
            "Development OOF record count changed"
        )

    records = []

    for row in rows:
        entity = row["screening_entity_id"]
        batch = row["batch_id"]

        if batch not in BATCHES:
            raise CurveError(
                "Unexpected development batch: "
                + batch
            )

        if row["selected_candidate_id"] != SELECTED_FAMILY:
            raise CurveError(
                "Unexpected selected candidate family"
            )

        try:
            label = int(
                row["label_numeric"]
            )
        except ValueError as exc:
            raise CurveError(
                "Invalid numeric label"
            ) from exc

        if label not in (0, 1):
            raise CurveError(
                "Unexpected numeric label"
            )

        try:
            score = float(
                row["continuous_score"]
            )
        except ValueError as exc:
            raise CurveError(
                "Invalid continuous score"
            ) from exc

        if not math.isfinite(score):
            raise CurveError(
                "Non-finite continuous score"
            )

        records.append(
            ScoreRecord(
                screening_entity_id=entity,
                batch_id=batch,
                label_numeric=label,
                continuous_score=score,
            )
        )

    ids = [
        record.screening_entity_id
        for record in records
    ]

    if len(set(ids)) != len(ids):
        raise CurveError(
            "Duplicate screening entity ID"
        )

    if Counter(
        record.label_numeric
        for record in records
    ) != {
        0: 4022,
        1: 168,
    }:
        raise CurveError(
            "Development class counts changed"
        )

    batch_counts = Counter(
        record.batch_id
        for record in records
    )

    if batch_counts != EXPECTED_BATCH_COUNTS:
        raise CurveError(
            "Development batch counts changed"
        )

    positive_counts = Counter(
        record.batch_id
        for record in records
        if record.label_numeric == 1
    )

    if positive_counts != EXPECTED_BATCH_POSITIVES:
        raise CurveError(
            "Development positive counts changed"
        )

    return records


def rank_batch(
    records: list[ScoreRecord],
) -> list[ScoreRecord]:

    if not records:
        raise CurveError(
            "Cannot rank empty batch"
        )

    batch_ids = {
        record.batch_id
        for record in records
    }

    if len(batch_ids) != 1:
        raise CurveError(
            "rank_batch received multiple batches"
        )

    ids = [
        record.screening_entity_id
        for record in records
    ]

    if len(set(ids)) != len(ids):
        raise CurveError(
            "Duplicate screening entity ID in batch"
        )

    return sorted(
        records,
        key=lambda record: (
            -record.continuous_score,
            record.screening_entity_id,
        ),
    )


def build_prefix_rows(
    records: list[ScoreRecord],
) -> tuple[
    list[dict],
    dict[str, list[dict]],
]:

    by_batch: dict[
        str,
        list[ScoreRecord],
    ] = {
        batch: []
        for batch in BATCHES
    }

    for record in records:
        by_batch[
            record.batch_id
        ].append(
            record
        )

    rows = []
    indexed = {}

    for batch in BATCHES:
        ranked = rank_batch(
            by_batch[
                batch
            ]
        )

        n = len(ranked)
        positives = sum(
            record.label_numeric
            for record in ranked
        )

        if n != EXPECTED_BATCH_COUNTS[
            batch
        ]:
            raise CurveError(
                "Unexpected batch size"
            )

        if positives != EXPECTED_BATCH_POSITIVES[
            batch
        ]:
            raise CurveError(
                "Unexpected batch positive count"
            )

        prefix_rows = []
        true_positives = 0

        for k in range(
            0,
            n + 1,
        ):
            if k > 0:
                true_positives += (
                    ranked[
                        k - 1
                    ].label_numeric
                )

            recall = (
                true_positives
                / positives
            )

            precision = (
                None
                if k == 0
                else true_positives
                / k
            )

            item = {
                "batch_id":
                    batch,

                "reviewed_count":
                    k,

                "batch_record_count":
                    n,

                "review_fraction_numerator":
                    k,

                "review_fraction_denominator":
                    n,

                "review_fraction":
                    k / n,

                "retained_positive_count":
                    positives,

                "retained_positive_reviewed":
                    true_positives,

                "recall":
                    recall,

                "precision":
                    precision,
            }

            rows.append(
                item
            )

            prefix_rows.append(
                item
            )

        if len(
            prefix_rows
        ) != n + 1:
            raise CurveError(
                "Prefix-curve length mismatch"
            )

        if prefix_rows[0]["recall"] != 0.0:
            raise CurveError(
                "Prefix curve does not begin at zero recall"
            )

        if prefix_rows[-1]["recall"] != 1.0:
            raise CurveError(
                "Prefix curve does not end at full recall"
            )

        indexed[
            batch
        ] = prefix_rows

    if len(rows) != 4199:
        raise CurveError(
            "Unexpected total prefix-row count"
        )

    return (
        rows,
        indexed,
    )


def exact_fraction_grid() -> list[Fraction]:
    fractions = set()

    for batch in BATCHES:
        n = EXPECTED_BATCH_COUNTS[
            batch
        ]

        for k in range(
            n + 1
        ):
            fractions.add(
                Fraction(
                    k,
                    n,
                )
            )

    grid = sorted(
        fractions
    )

    if not grid:
        raise CurveError(
            "Candidate fraction grid empty"
        )

    if grid[0] != Fraction(0, 1):
        raise CurveError(
            "Candidate fraction grid does not begin at zero"
        )

    if grid[-1] != Fraction(1, 1):
        raise CurveError(
            "Candidate fraction grid does not end at one"
        )

    return grid


def ceil_fraction_times_n(
    q: Fraction,
    n: int,
) -> int:

    if q < 0 or q > 1:
        raise CurveError(
            "Candidate review fraction outside [0,1]"
        )

    numerator = (
        q.numerator
        * n
    )

    denominator = (
        q.denominator
    )

    k = (
        numerator
        + denominator
        - 1
    ) // denominator

    if not (
        0
        <= k
        <= n
    ):
        raise CurveError(
            "Derived batch review count outside valid range"
        )

    return k


def build_cross_batch_rows(
    prefix_by_batch: dict[
        str,
        list[dict],
    ],
) -> list[dict]:

    grid = exact_fraction_grid()
    output = []

    total_positives = sum(
        EXPECTED_BATCH_POSITIVES.values()
    )

    total_records = sum(
        EXPECTED_BATCH_COUNTS.values()
    )

    previous_reviewed = -1
    previous_min_recall = -1.0
    previous_mean_recall = -1.0
    previous_pooled_recall = -1.0

    for q in grid:
        batch_recall = []
        batch_precision = []

        total_reviewed = 0
        total_positive_reviewed = 0

        for batch in BATCHES:
            n = EXPECTED_BATCH_COUNTS[
                batch
            ]

            k = ceil_fraction_times_n(
                q,
                n,
            )

            item = prefix_by_batch[
                batch
            ][
                k
            ]

            batch_recall.append(
                item[
                    "recall"
                ]
            )

            if item[
                "precision"
            ] is not None:
                batch_precision.append(
                    item[
                        "precision"
                    ]
                )

            total_reviewed += k

            total_positive_reviewed += (
                item[
                    "retained_positive_reviewed"
                ]
            )

        minimum_recall = min(
            batch_recall
        )

        median_recall = statistics.median(
            batch_recall
        )

        mean_recall = statistics.fmean(
            batch_recall
        )

        pooled_recall = (
            total_positive_reviewed
            / total_positives
        )

        mean_precision = (
            None
            if not batch_precision
            else statistics.fmean(
                batch_precision
            )
        )

        pooled_review_fraction = (
            total_reviewed
            / total_records
        )

        if total_reviewed < previous_reviewed:
            raise CurveError(
                "Cross-batch reviewed count decreased"
            )

        if minimum_recall < previous_min_recall:
            raise CurveError(
                "Cross-batch minimum recall decreased"
            )

        if mean_recall < previous_mean_recall:
            raise CurveError(
                "Cross-batch mean recall decreased"
            )

        if pooled_recall < previous_pooled_recall:
            raise CurveError(
                "Cross-batch pooled recall decreased"
            )

        previous_reviewed = total_reviewed
        previous_min_recall = minimum_recall
        previous_mean_recall = mean_recall
        previous_pooled_recall = pooled_recall

        output.append(
            {
                "candidate_fraction_numerator":
                    q.numerator,

                "candidate_fraction_denominator":
                    q.denominator,

                "candidate_review_fraction":
                    float(
                        q
                    ),

                "reviewed_record_count":
                    total_reviewed,

                "pooled_review_fraction":
                    pooled_review_fraction,

                "minimum_batch_recall":
                    minimum_recall,

                "median_batch_recall":
                    median_recall,

                "unweighted_mean_batch_recall":
                    mean_recall,

                "pooled_development_recall":
                    pooled_recall,

                "unweighted_mean_batch_precision":
                    mean_precision,
            }
        )

    if output[0][
        "reviewed_record_count"
    ] != 0:
        raise CurveError(
            "Cross-batch curve does not begin at zero workload"
        )

    if output[0][
        "pooled_development_recall"
    ] != 0.0:
        raise CurveError(
            "Cross-batch curve does not begin at zero recall"
        )

    final = output[-1]

    if final[
        "reviewed_record_count"
    ] != 4190:
        raise CurveError(
            "Cross-batch curve does not end at full workload"
        )

    for field in (
        "minimum_batch_recall",
        "median_batch_recall",
        "unweighted_mean_batch_recall",
        "pooled_development_recall",
    ):
        if final[field] != 1.0:
            raise CurveError(
                "Cross-batch curve does not end at full recall"
            )

    return output


def format_number(
    value,
) -> str:

    if value is None:
        return ""

    if isinstance(
        value,
        int,
    ):
        return str(
            value
        )

    return format(
        float(
            value
        ),
        ".17g",
    )


def write_tsv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict],
) -> None:

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    field:
                        format_number(
                            row[
                                field
                            ]
                        )

                    for field in fieldnames
                }
            )


def development_plan() -> dict:
    records = read_scores()

    prefix_rows, prefix_by_batch = (
        build_prefix_rows(
            records
        )
    )

    grid = exact_fraction_grid()

    return {
        "status":
            "OPERATING_POINT_CURVE_PLAN_ONLY",

        "input_records":
            len(
                records
            ),

        "positive_records":
            sum(
                record.label_numeric
                for record in records
            ),

        "negative_records":
            sum(
                1
                for record in records
                if record.label_numeric == 0
            ),

        "selected_model_family":
            SELECTED_FAMILY,

        "whole_batches":
            len(
                BATCHES
            ),

        "per_batch_prefix_rows":
            len(
                prefix_rows
            ),

        "cross_batch_exact_fraction_grid_rows":
            len(
                grid
            ),

        "raw_score_threshold_selected":
            False,

        "review_fraction_selected":
            False,

        "acceptable_recall_target_defined":
            False,

        "model_fit_performed":
            False,

        "vectorizer_fit_performed":
            False,

        "calibration_fit_performed":
            False,

        "future_scoring_performed":
            False,

        "blind_validation_content_used":
            False,

        "scientific_screening_decisions_made":
            False,

        "production_mutated":
            False,
    }


def generate(
    output_dir: Path,
) -> dict:

    repo = repo_root()

    expected_output = (
        repo
        / OUTPUT_REL
    ).resolve()

    if output_dir.resolve() != expected_output:
        raise CurveError(
            "Output directory differs from frozen curve output path"
        )

    if output_dir.exists():
        raise CurveError(
            "Curve output directory already exists; refusing overwrite"
        )

    records = read_scores()

    prefix_rows, prefix_by_batch = (
        build_prefix_rows(
            records
        )
    )

    cross_rows = build_cross_batch_rows(
        prefix_by_batch
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    write_tsv(
        output_dir
        / "per_batch_prefix_curve.tsv",
        [
            "batch_id",
            "reviewed_count",
            "batch_record_count",
            "review_fraction_numerator",
            "review_fraction_denominator",
            "review_fraction",
            "retained_positive_count",
            "retained_positive_reviewed",
            "recall",
            "precision",
        ],
        prefix_rows,
    )

    write_tsv(
        output_dir
        / "cross_batch_review_fraction_curve.tsv",
        [
            "candidate_fraction_numerator",
            "candidate_fraction_denominator",
            "candidate_review_fraction",
            "reviewed_record_count",
            "pooled_review_fraction",
            "minimum_batch_recall",
            "median_batch_recall",
            "unweighted_mean_batch_recall",
            "pooled_development_recall",
            "unweighted_mean_batch_precision",
        ],
        cross_rows,
    )

    summary = {
        "schema_version":
            1,

        "status":
            "OPERATING_POINT_CURVE_GENERATED_NO_SELECTION",

        "input_sha256":
            EXPECTED_INPUT_SHA256,

        "selected_model_family":
            SELECTED_FAMILY,

        "development_records":
            4190,

        "positive_records":
            168,

        "negative_records":
            4022,

        "whole_batches":
            9,

        "per_batch_prefix_rows":
            len(
                prefix_rows
            ),

        "cross_batch_exact_fraction_grid_rows":
            len(
                cross_rows
            ),

        "ranking_policy":
            "continuous_score_descending_then_screening_entity_id_ascending",

        "cross_batch_review_count_rule":
            "ceil_exact_fraction_times_batch_size",

        "raw_score_threshold_selected":
            False,

        "review_fraction_selected":
            False,

        "acceptable_recall_target_defined":
            False,

        "model_fit_performed":
            False,

        "vectorizer_fit_performed":
            False,

        "calibration_fit_performed":
            False,

        "future_scoring_performed":
            False,

        "blind_validation_content_used":
            False,

        "scientific_screening_decisions_made":
            False,

        "production_mutated":
            False,
    }

    (
        output_dir
        / "summary.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return summary


def main() -> int:
    parser = argparse.ArgumentParser()

    action = parser.add_mutually_exclusive_group(
        required=True
    )

    action.add_argument(
        "--plan",
        action="store_true",
    )

    action.add_argument(
        "--generate",
        action="store_true",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
    )

    args = parser.parse_args()

    if args.plan:
        if args.output_dir is not None:
            raise CurveError(
                "--output-dir is invalid with --plan"
            )

        print(
            json.dumps(
                development_plan(),
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    if args.output_dir is None:
        raise CurveError(
            "--output-dir is required with --generate"
        )

    summary = generate(
        args.output_dir
    )

    print(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
