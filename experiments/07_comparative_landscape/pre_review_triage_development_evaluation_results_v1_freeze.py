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
    "a354aea5baf6cefb2d8e3aa45d20c19db79594c5"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

RESULT_ROOT_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_evaluator_v1/"
    "development_evaluation_v1"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_development_evaluation_results_v1_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_development_evaluation_results_v1_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_DEVELOPMENT_EVALUATION_RESULTS_V1.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_development_evaluation_results_v1.sha256"
)

RESULT_FILES = {
    RESULT_ROOT_REL
    + "/execution_claim.json":
        "237920630d50e436ef7b5b390b091f0bcbe86ec9c80495409e8c37865c21cec5",

    RESULT_ROOT_REL
    + "/inner_metrics.tsv":
        "835a822048479a7ece99a5184bb7480e60119426179aefb0d6bf0364f2200ff1",

    RESULT_ROOT_REL
    + "/outer_metrics.tsv":
        "49a71cd13bafd0f11308e7a51b42a2c4f4dcf176c8fdc886fe2608169829ee81",

    RESULT_ROOT_REL
    + "/outer_scores.tsv":
        "1da5b38902d893a91cb99b7d9965f179717667c42b66ff80f63313ac50251c47",

    RESULT_ROOT_REL
    + "/final_candidate_batch_metrics.tsv":
        "dacfaf079b33d20e95ec95021b7b6bb481ed9e4117d3e0de7a25793e98f253ec",

    RESULT_ROOT_REL
    + "/summary.json":
        "dc44be6039cdef5b473dfaf4f619fb214e875f5b928ea4673463437fce5604d8",

    RESULT_ROOT_REL
    + "/execution_completion.json":
        "61341cbb2bf36dd9c62d9de533bcda5d323cc05cc77a023e7b43e1eed68b38e3",
}

FREEZE_PATHS = (
    set(
        RESULT_FILES
    )
    | {
        FREEZE_REL,
        DESIGN_REL,
        DOC_REL,
        SUMS_REL,
    }
)

CANDIDATES = (
    "logistic_regression_balanced_l2_v1",
    "linear_svc_balanced_l2_v1",
    "complement_nb_v1",
)

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


def git_output(*args):

    return subprocess.check_output(
        [
            "git",
            *args,
        ],
        cwd=repo_root(),
        text=True,
    ).strip()


def sha(path):

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def read_tsv(path):

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


def parse_sums(path):

    values = {}

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        digest, relative = line.split(
            None,
            1,
        )

        relative = relative.strip()

        if relative in values:
            raise FreezeError(
                "Duplicate checksum target: "
                + relative
            )

        values[
            relative
        ] = digest

    return values


def repository_position():

    repo = repo_root()

    head = git_output(
        "rev-parse",
        "HEAD",
    )

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
            "Authorization commit is not ancestor of HEAD"
        )

    for relative in FREEZE_PATHS:

        tracked = subprocess.run(
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

        if tracked.returncode != 0:
            raise FreezeError(
                "Frozen result path not tracked: "
                + relative
            )

    return "COMMITTED_FREEZE_OR_DESCENDANT"


def aggregate(
    candidate,
    values,
):

    return {
        "candidate_id":
            candidate,

        "macro_mean_ap":
            statistics.fmean(
                values
            ),

        "minimum_ap":
            min(
                values
            ),

        "median_ap":
            statistics.median(
                values
            ),
    }


def validate():

    repo = repo_root()

    position = repository_position()

    for relative, expected in RESULT_FILES.items():

        path = repo / relative

        if not path.is_file():
            raise FreezeError(
                "Frozen result artifact missing: "
                + relative
            )

        observed = sha(
            path
        )

        if observed != expected:
            raise FreezeError(
                "Frozen result artifact changed: "
                + relative
            )

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
        != "FROZEN_DEVELOPMENT_EVALUATION_RESULTS_V1"
    ):
        raise FreezeError(
            "Result-freeze status changed"
        )

    if (
        design[
            "freeze_parent_commit"
        ]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Result-freeze parent changed"
        )

    execution = design[
        "execution_identity"
    ]

    if (
        execution[
            "execution_id"
        ]
        != "TRIAGE-DEV-EVAL-V1-001"
    ):
        raise FreezeError(
            "Execution identity changed"
        )

    if (
        execution[
            "one_time_execution_consumed"
        ]
        is not True
    ):
        raise FreezeError(
            "One-time execution state changed"
        )

    if (
        execution[
            "rerun_authorized"
        ]
        is not False
    ):
        raise FreezeError(
            "Rerun unexpectedly authorized"
        )

    artifact_contract = design[
        "artifact_contract"
    ]

    if (
        artifact_contract[
            "artifact_count"
        ]
        != 7
    ):
        raise FreezeError(
            "Result artifact count changed"
        )

    if (
        artifact_contract[
            "artifact_sha256"
        ]
        != RESULT_FILES
    ):
        raise FreezeError(
            "Result artifact hash contract changed"
        )

    result_root = (
        repo
        / RESULT_ROOT_REL
    )

    inner = read_tsv(
        result_root
        / "inner_metrics.tsv"
    )

    outer = read_tsv(
        result_root
        / "outer_metrics.tsv"
    )

    scores = read_tsv(
        result_root
        / "outer_scores.tsv"
    )

    final_metrics = read_tsv(
        result_root
        / "final_candidate_batch_metrics.tsv"
    )

    summary = json.loads(
        (
            result_root
            / "summary.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    completion = json.loads(
        (
            result_root
            / "execution_completion.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    claim = json.loads(
        (
            result_root
            / "execution_claim.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    if len(inner) != 216:
        raise FreezeError(
            "Inner metric count changed"
        )

    if len(outer) != 9:
        raise FreezeError(
            "Outer metric count changed"
        )

    if len(scores) != 4190:
        raise FreezeError(
            "Outer score count changed"
        )

    if len(final_metrics) != 27:
        raise FreezeError(
            "Fixed candidate metric count changed"
        )

    if len({
        row[
            "screening_entity_id"
        ]
        for row in scores
    }) != 4190:
        raise FreezeError(
            "Outer score IDs are not unique"
        )

    if Counter(
        row[
            "label_numeric"
        ]
        for row in scores
    ) != {
        "0": 4022,
        "1": 168,
    }:
        raise FreezeError(
            "Development class counts changed"
        )

    if (
        claim[
            "status"
        ]
        != "CLAIMED_BEFORE_FIRST_FIT"
    ):
        raise FreezeError(
            "Execution claim changed"
        )

    if (
        completion[
            "status"
        ]
        != "DEVELOPMENT_EVALUATION_COMPLETED"
    ):
        raise FreezeError(
            "Execution completion changed"
        )

    if (
        summary[
            "status"
        ]
        != "DEVELOPMENT_EVALUATION_COMPLETE"
    ):
        raise FreezeError(
            "Evaluation summary changed"
        )

    aggregates = []

    for candidate in CANDIDATES:

        by_batch = {
            row[
                "held_out_batch"
            ]:
                float(
                    row[
                        "average_precision"
                    ]
                )

            for row in final_metrics

            if row[
                "candidate_id"
            ] == candidate
        }

        if set(
            by_batch
        ) != set(
            BATCHES
        ):
            raise FreezeError(
                "Fixed candidate batch coverage changed"
            )

        aggregates.append(
            aggregate(
                candidate,
                [
                    by_batch[
                        batch
                    ]
                    for batch in BATCHES
                ],
            )
        )

    order = {
        candidate:
            index
        for index, candidate in enumerate(
            CANDIDATES
        )
    }

    selected = max(
        aggregates,
        key=lambda item: (
            item[
                "macro_mean_ap"
            ],
            item[
                "minimum_ap"
            ],
            item[
                "median_ap"
            ],
            -order[
                item[
                    "candidate_id"
                ]
            ],
        ),
    )

    if (
        selected[
            "candidate_id"
        ]
        != "linear_svc_balanced_l2_v1"
    ):
        raise FreezeError(
            "Independent selected family changed"
        )

    if (
        summary[
            "final_selected_candidate_id"
        ]
        != selected[
            "candidate_id"
        ]
    ):
        raise FreezeError(
            "Summary selected family mismatch"
        )

    if (
        completion[
            "final_selected_candidate_id"
        ]
        != selected[
            "candidate_id"
        ]
    ):
        raise FreezeError(
            "Completion selected family mismatch"
        )

    candidate_result = design[
        "candidate_result"
    ]

    if (
        candidate_result[
            "candidate_aggregates"
        ]
        != aggregates
    ):
        raise FreezeError(
            "Frozen candidate aggregates changed"
        )

    if (
        candidate_result[
            "selected_candidate_id"
        ]
        != "linear_svc_balanced_l2_v1"
    ):
        raise FreezeError(
            "Frozen selected family changed"
        )

    if (
        candidate_result[
            "all_nine_outer_folds_selected_final_family"
        ]
        is not True
    ):
        raise FreezeError(
            "Outer-family consistency flag changed"
        )

    outer_selected = {
        row[
            "outer_held_out_batch"
        ]:
            row[
                "selected_candidate_id"
            ]

        for row in outer
    }

    if set(
        outer_selected
    ) != set(
        BATCHES
    ):
        raise FreezeError(
            "Outer batch set changed"
        )

    if any(
        candidate
        != "linear_svc_balanced_l2_v1"

        for candidate in outer_selected.values()
    ):
        raise FreezeError(
            "Not all outer folds selected frozen final family"
        )

    boundary = design[
        "scientific_boundary"
    ]

    if (
        boundary[
            "development_evidence_only"
        ]
        is not True
    ):
        raise FreezeError(
            "Development-evidence boundary changed"
        )

    if (
        boundary[
            "selected_family_establishes_future_performance"
        ]
        is not False
    ):
        raise FreezeError(
            "Future-performance authority broadened"
        )

    for field in (
        "threshold_selected",
        "hard_predictions_generated",
        "future_scoring_performed",
        "blind_validation_content_used",
        "scientific_screening_decisions_made",
        "production_mutated",
    ):

        if boundary[
            field
        ] is not False:
            raise FreezeError(
                "Scientific boundary broadened: "
                + field
            )

    audit = design[
        "independent_audit"
    ]

    for field, value in audit.items():

        if value is not True:
            raise FreezeError(
                "Independent audit evidence changed: "
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

    checks = parse_sums(
        repo
        / SUMS_REL
    )

    expected_targets = (
        set(
            RESULT_FILES
        )
        | {
            FREEZE_REL,
            DESIGN_REL,
            DOC_REL,
        }
    )

    if set(
        checks
    ) != expected_targets:
        raise FreezeError(
            "Result-freeze checksum target set changed"
        )

    for relative, expected in checks.items():

        if (
            sha(
                repo
                / relative
            )
            != expected
        ):
            raise FreezeError(
                "Result-freeze checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | exact seven one-time evaluation artifacts validate"
    )

    print(
        "PASS | 4,190-row development result structure validates"
    )

    print(
        "PASS | fixed-family aggregates independently reproduce"
    )

    print(
        "PASS | selected family = linear_svc_balanced_l2_v1"
    )

    print(
        "PASS | all nine outer folds selected LinearSVC"
    )

    print(
        "PASS | no threshold/future/blind/scientific/production authority"
    )

    print(
        "PASS | one-time evaluation is consumed and rerun unauthorized"
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
