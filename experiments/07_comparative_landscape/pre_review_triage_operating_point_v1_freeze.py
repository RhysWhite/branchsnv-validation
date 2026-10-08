from __future__ import annotations

from collections import Counter
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics
import subprocess


EXPECTED_PARENT = (
    "f91eb31b0014fe7fd99a00ecb2874b5533ffb673"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_v1_design.json"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_v1_freeze.py"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_OPERATING_POINT_V1.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_v1.sha256"
)

SCORES_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_evaluator_v1/"
    "development_evaluation_v1/"
    "outer_scores.tsv"
)

FREEZE_PATHS = {
    DESIGN_REL,
    FREEZE_REL,
    DOC_REL,
    SUMS_REL,
}

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


class FreezeError(RuntimeError):
    pass


def repo_root():

    return Path(
        subprocess.check_output(
            [
                "git",
                "rev-parse",
                "--show-toplevel",
            ],
            text=True,
        ).strip()
    ).resolve()


def sha(path):

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def repository_position():

    repo = repo_root()

    head = subprocess.check_output(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        cwd=repo,
        text=True,
    ).strip()

    if head == EXPECTED_PARENT:
        return "PRE_COMMIT_PARENT"

    result = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            EXPECTED_PARENT,
            "HEAD",
        ],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if result.returncode != 0:
        raise FreezeError(
            "Development-result freeze is not ancestor of HEAD"
        )

    for relative in FREEZE_PATHS:

        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--error-unmatch",
                relative,
            ],
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if result.returncode != 0:
            raise FreezeError(
                "Operating-point freeze artifact not tracked: "
                + relative
            )

    return "COMMITTED_FREEZE_OR_DESCENDANT"


def read_scores(path):

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def validate():

    repo = repo_root()

    position = repository_position()

    design = json.loads(
        (
            repo
            / DESIGN_REL
        ).read_text(
            encoding="utf-8"
        )
    )

    if (
        design[
            "status"
        ]
        != "FROZEN_PRE_OPERATING_POINT_CURVE_IMPLEMENTATION"
    ):
        raise FreezeError(
            "Operating-point design status changed"
        )

    if (
        design[
            "freeze_parent_commit"
        ]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Operating-point design parent changed"
        )

    scores_path = (
        repo
        / SCORES_REL
    )

    if not scores_path.is_file():
        raise FreezeError(
            "Frozen OOF score artifact missing"
        )

    score_contract = design[
        "development_score_artifact"
    ]

    if (
        score_contract[
            "sha256"
        ]
        != sha(
            scores_path
        )
    ):
        raise FreezeError(
            "Frozen OOF score artifact changed"
        )

    rows = read_scores(
        scores_path
    )

    if len(rows) != 4190:
        raise FreezeError(
            "OOF development record count changed"
        )

    if Counter(
        row[
            "label_numeric"
        ]
        for row in rows
    ) != {
        "0": 4022,
        "1": 168,
    }:
        raise FreezeError(
            "Development labels changed"
        )

    if {
        row[
            "selected_candidate_id"
        ]
        for row in rows
    } != {
        "linear_svc_balanced_l2_v1"
    }:
        raise FreezeError(
            "Frozen score family changed"
        )

    reconstructed = {}

    for batch in BATCHES:

        batch_rows = [
            row
            for row in rows
            if row[
                "batch_id"
            ] == batch
        ]

        scores = [
            float(
                row[
                    "continuous_score"
                ]
            )
            for row in batch_rows
        ]

        positives = [
            float(
                row[
                    "continuous_score"
                ]
            )
            for row in batch_rows
            if row[
                "label_numeric"
            ] == "1"
        ]

        if not scores or not positives:
            raise FreezeError(
                "Development diagnostic batch incomplete"
            )

        minimum_positive = min(
            positives
        )

        reconstructed[
            batch
        ] = {
            "records":
                len(
                    batch_rows
                ),

            "positives":
                len(
                    positives
                ),

            "score_median":
                statistics.median(
                    scores
                ),

            "positive_minimum_score":
                minimum_positive,

            "recall_at_raw_score_zero":
                (
                    sum(
                        score >= 0
                        for score in positives
                    )
                    / len(
                        positives
                    )
                ),

            "review_fraction_at_raw_score_zero":
                (
                    sum(
                        score >= 0
                        for score in scores
                    )
                    / len(
                        scores
                    )
                ),

            "review_fraction_required_to_capture_all_observed_positives":
                (
                    sum(
                        score >= minimum_positive
                        for score in scores
                    )
                    / len(
                        scores
                    )
                ),
        }

    if (
        reconstructed
        != design[
            "score_scale_diagnostic"
        ][
            "per_batch"
        ]
    ):
        raise FreezeError(
            "Score-scale diagnostic changed"
        )

    policy = design[
        "operating_point_policy_family"
    ]

    if (
        policy[
            "authorized_family"
        ]
        != "within_batch_rank_review_fraction"
    ):
        raise FreezeError(
            "Operating-point family changed"
        )

    for field in (
        "raw_score_threshold_policy_authorized",
        "pooled_cross_fold_raw_score_threshold_authorized",
        "score_calibration_fit_authorized",
        "probability_calibration_authorized",
        "review_fraction_selected",
        "acceptable_recall_target_defined",
        "workload_target_defined",
    ):

        if policy[
            field
        ] is not False:
            raise FreezeError(
                "Operating-point scope broadened: "
                + field
            )

    ranking = design[
        "ranking_contract"
    ]

    if (
        ranking[
            "primary_sort"
        ]
        != "continuous_score_descending"
    ):
        raise FreezeError(
            "Ranking sort changed"
        )

    if (
        ranking[
            "deterministic_tie_break"
        ]
        != "screening_entity_id_ascending"
    ):
        raise FreezeError(
            "Ranking tie-break changed"
        )

    if ranking[
        "labels_used_to_construct_ranking"
    ] is not False:
        raise FreezeError(
            "Labels unexpectedly used for ranking"
        )

    curve = design[
        "curve_contract"
    ]

    if curve[
        "operating_point_selected_by_curve_generation"
    ] is not False:
        raise FreezeError(
            "Curve generation unexpectedly selects operating point"
        )

    routing = design[
        "routing_semantics"
    ]

    if routing[
        "model_output_is_routing_only"
    ] is not True:
        raise FreezeError(
            "Routing-only contract changed"
        )

    if routing[
        "records_below_boundary_scientifically_excluded"
    ] is not False:
        raise FreezeError(
            "Residual queue became scientific exclusion"
        )

    if routing[
        "terminal_scientific_decision_maker"
    ] != "human_review":
        raise FreezeError(
            "Human scientific decision contract changed"
        )

    selection = design[
        "future_selection_gate"
    ]

    if selection[
        "operating_point_may_be_selected_now"
    ] is not False:
        raise FreezeError(
            "Operating-point selection unexpectedly authorized"
        )

    if selection[
        "acceptable_recall_target_invented_by_design"
    ] is not False:
        raise FreezeError(
            "Recall target unexpectedly invented"
        )

    scientific = design[
        "scientific_boundary"
    ]

    for field, value in scientific.items():

        if value is not False:
            raise FreezeError(
                "Scientific authority broadened: "
                + field
            )

    for relative, expected in (
        design[
            "bound_prior_freeze_hashes"
        ].items()
    ):

        path = repo / relative

        if (
            not path.is_file()
            or sha(
                path
            ) != expected
        ):
            raise FreezeError(
                "Bound prior freeze changed: "
                + relative
            )

    manifest = {}

    for line in (
        repo
        / SUMS_REL
    ).read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        digest, relative = line.split(
            None,
            1,
        )

        manifest[
            relative.strip()
        ] = digest

    expected_targets = {
        DESIGN_REL,
        FREEZE_REL,
        DOC_REL,
    }

    if set(
        manifest
    ) != expected_targets:
        raise FreezeError(
            "Operating-point checksum target set changed"
        )

    for relative, expected in manifest.items():

        if sha(
            repo
            / relative
        ) != expected:
            raise FreezeError(
                "Operating-point checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | operating-point design v1 validates"
    )

    print(
        "PASS | selected family remains LinearSVC"
    )

    print(
        "PASS | raw-score threshold selection remains unauthorized"
    )

    print(
        "PASS | rank/review-fraction curve family frozen"
    )

    print(
        "PASS | no review fraction or acceptable recall target selected"
    )

    print(
        "PASS | residual records remain human-review candidates"
    )

    print(
        "PASS | no fit/future/blind/scientific/production authority"
    )

    return position


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--validate",
        action="store_true",
        required=True,
    )

    parser.parse_args()

    validate()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
