from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "b0c068d7abd9853088ae3134249fdf89ffa79ba0"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

IMPL_REL = (
    ROOT_REL
    + "/pre_review_triage_evaluator_v1.py"
)

TEST_REL = (
    ROOT_REL
    + "/test_pre_review_triage_evaluator_v1.py"
)

HOSTILE_REL = (
    ROOT_REL
    + "/test_pre_review_triage_evaluator_hostile_v1.py"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_evaluator_v1_implementation_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_evaluator_v1_implementation_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_EVALUATOR_V1_IMPLEMENTATION.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_evaluator_v1_implementation.sha256"
)

FREEZE_PATHS = {
    IMPL_REL,
    TEST_REL,
    HOSTILE_REL,
    FREEZE_REL,
    DESIGN_REL,
    DOC_REL,
    SUMS_REL,
}


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
            "Resolved-environment-state parent is not ancestor of HEAD"
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
                "Evaluator implementation freeze file not tracked: "
                + relative
            )

    return "COMMITTED_FREEZE_OR_DESCENDANT"


def enclosing_function(
    tree,
    node,
):

    enclosing = None

    for candidate in ast.walk(
        tree
    ):

        if not isinstance(
            candidate,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        if (
            hasattr(
                candidate,
                "end_lineno",
            )
            and candidate.lineno
            <= node.lineno
            <= candidate.end_lineno
        ):

            if (
                enclosing is None
                or candidate.lineno
                >= enclosing.lineno
            ):
                enclosing = candidate

    return enclosing


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
        design["status"]
        != "FROZEN_IMPLEMENTATION_PRE_DEVELOPMENT_EVALUATION"
    ):
        raise FreezeError(
            "Evaluator implementation status changed"
        )

    if (
        design["freeze_parent_commit"]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Evaluator freeze parent changed"
        )

    contract = design[
        "implementation_contract"
    ]

    expected_artifacts = {
        IMPL_REL:
            contract[
                "implementation_sha256"
            ],

        TEST_REL:
            contract[
                "standard_test_sha256"
            ],

        HOSTILE_REL:
            contract[
                "hostile_test_sha256"
            ],
    }

    for relative, expected in expected_artifacts.items():

        path = repo / relative

        if (
            not path.is_file()
            or sha(path) != expected
        ):
            raise FreezeError(
                "Evaluator implementation artifact changed: "
                + relative
            )

    if contract[
        "validated_no_fit_test_count"
    ] != 21:
        raise FreezeError(
            "Validated no-fit test count changed"
        )

    development = design[
        "development_contract"
    ]

    if (
        development["records"] != 4190
        or development["positive_records"] != 168
        or development["negative_records"] != 4022
    ):
        raise FreezeError(
            "Development population changed"
        )

    expected_batch_counts = {
        "B000001": {
            "records": 454,
            "positive": 67,
            "negative": 387,
        },
        "B000002": {
            "records": 380,
            "positive": 7,
            "negative": 373,
        },
        "B000003": {
            "records": 423,
            "positive": 6,
            "negative": 417,
        },
        "B000004": {
            "records": 471,
            "positive": 9,
            "negative": 462,
        },
        "B000005": {
            "records": 475,
            "positive": 5,
            "negative": 470,
        },
        "B000006": {
            "records": 491,
            "positive": 10,
            "negative": 481,
        },
        "B000007": {
            "records": 497,
            "positive": 3,
            "negative": 494,
        },
        "B000008": {
            "records": 499,
            "positive": 6,
            "negative": 493,
        },
        "B000009": {
            "records": 500,
            "positive": 55,
            "negative": 445,
        },
    }

    if (
        development[
            "batch_counts"
        ]
        != expected_batch_counts
    ):
        raise FreezeError(
            "Development batch counts changed"
        )

    candidate = design[
        "candidate_contract"
    ]

    if candidate[
        "candidate_order"
    ] != [
        "logistic_regression_balanced_l2_v1",
        "linear_svc_balanced_l2_v1",
        "complement_nb_v1",
    ]:
        raise FreezeError(
            "Frozen candidate order changed"
        )

    if candidate[
        "candidate_count"
    ] != 3:
        raise FreezeError(
            "Candidate count changed"
        )

    nested = design[
        "nested_validation_contract"
    ]

    if nested[
        "outer_fold_count"
    ] != 9:
        raise FreezeError(
            "Outer fold count changed"
        )

    if nested[
        "inner_fold_count_per_outer"
    ] != 8:
        raise FreezeError(
            "Inner fold count changed"
        )

    if nested[
        "candidate_selection_tie_break_order"
    ] != [
        "higher_macro_mean_average_precision",
        "higher_minimum_average_precision",
        "higher_median_average_precision",
        "frozen_candidate_order",
    ]:
        raise FreezeError(
            "Tie-break order changed"
        )

    if (
        nested[
            "floating_point_comparison"
        ]
        != "raw_python_float_tuple_comparison"
    ):
        raise FreezeError(
            "Floating-point comparison contract changed"
        )

    if nested[
        "comparison_rounding"
    ] is not False:
        raise FreezeError(
            "Metric rounding unexpectedly enabled"
        )

    if nested[
        "comparison_tolerance"
    ] is not None:
        raise FreezeError(
            "Metric tolerance unexpectedly introduced"
        )

    for field in (
        "threshold_selected",
        "hard_predictions_generated",
    ):

        if nested[field] is not False:
            raise FreezeError(
                "Nested-evaluation authority broadened: "
                + field
            )

    score = design[
        "score_orientation_contract"
    ]

    if score[
        "positive_class"
    ] != 1:
        raise FreezeError(
            "Positive class changed"
        )

    fit = design[
        "fit_surface_contract"
    ]

    if (
        fit[
            "fit_capable_function"
        ]
        != "fit_and_score_partition"
    ):
        raise FreezeError(
            "Fit-capable function changed"
        )

    if (
        fit[
            "fit_capable_function_self_authorization_gated"
        ]
        is not True
    ):
        raise FreezeError(
            "Direct fit authorization gate changed"
        )

    tree = ast.parse(
        (
            repo
            / IMPL_REL
        ).read_text(
            encoding="utf-8"
        )
    )

    fit_calls = []

    fit_function = None

    for node in ast.walk(
        tree
    ):

        if (
            isinstance(
                node,
                ast.FunctionDef,
            )
            and node.name
            == "fit_and_score_partition"
        ):
            fit_function = node

        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        func = node.func

        if not (
            isinstance(
                func,
                ast.Attribute,
            )
            and func.attr in {
                "fit",
                "fit_transform",
            }
        ):
            continue

        enclosing = enclosing_function(
            tree,
            node,
        )

        fit_calls.append(
            (
                func.attr,
                enclosing.name
                if enclosing is not None
                else "<module>",
            )
        )

    if not fit_calls:
        raise FreezeError(
            "No fit-capable calls found"
        )

    if {
        function
        for _, function in fit_calls
    } != {
        "fit_and_score_partition",
    }:
        raise FreezeError(
            "Fit calls escaped fit_and_score_partition"
        )

    if fit_function is None:
        raise FreezeError(
            "fit_and_score_partition missing"
        )

    direct_calls = [
        node.value
        for node in fit_function.body
        if isinstance(
            node,
            ast.Expr,
        )
        and isinstance(
            node.value,
            ast.Call,
        )
    ]

    if not direct_calls:
        raise FreezeError(
            "No direct call found at start of fit function"
        )

    first_function = direct_calls[
        0
    ].func

    if not (
        isinstance(
            first_function,
            ast.Name,
        )
        and first_function.id
        == "require_execution_authorization"
    ):
        raise FreezeError(
            "Fit function does not begin with execution authorization"
        )

    future_auth = design[
        "future_execution_authorization_contract"
    ]

    if (
        future_auth[
            "artifact_existed_at_implementation_freeze"
        ]
        is not False
    ):
        raise FreezeError(
            "Historical authorization-artifact state changed"
        )

    if (
        future_auth[
            "authorization_scope"
        ]
        != "ONE_TIME_FROZEN_DEVELOPMENT_EVALUATION"
    ):
        raise FreezeError(
            "Future authorization scope changed"
        )

    if (
        future_auth[
            "execution_id"
        ]
        != "TRIAGE-DEV-EVAL-V1-001"
    ):
        raise FreezeError(
            "Execution identity changed"
        )

    one_time = design[
        "one_time_execution_contract"
    ]

    if (
        one_time[
            "execution_claim_written_before_first_fit"
        ]
        is not True
    ):
        raise FreezeError(
            "Pre-fit execution claim requirement changed"
        )

    if (
        one_time[
            "overwrite_existing_output_directory"
        ]
        is not False
    ):
        raise FreezeError(
            "Output overwrite unexpectedly enabled"
        )

    if (
        one_time[
            "automatic_retry_after_claim"
        ]
        is not False
    ):
        raise FreezeError(
            "Automatic retry unexpectedly authorized"
        )

    outputs = design[
        "output_contract"
    ]

    if outputs[
        "files"
    ] != [
        "execution_claim.json",
        "inner_metrics.tsv",
        "outer_metrics.tsv",
        "outer_scores.tsv",
        "final_candidate_batch_metrics.tsv",
        "summary.json",
        "execution_completion.json",
    ]:
        raise FreezeError(
            "Frozen output set changed"
        )

    evidence = design[
        "validation_evidence"
    ]

    for field in (
        "no_fit_tests_passed",
        "exact_constructor_tests_passed",
        "score_orientation_tests_passed",
        "whole_batch_geometry_validated",
        "exact_batch_counts_validated",
        "direct_fit_authorization_guard_validated",
        "unauthorized_cli_execution_refused",
    ):

        if evidence[field] is not True:
            raise FreezeError(
                "Required validation evidence changed: "
                + field
            )

    for field in (
        "unauthorized_cli_created_output",
        "model_fit_performed",
        "vectorizer_fit_performed",
        "hyperparameter_selection_performed",
        "threshold_selection_performed",
        "future_scoring_performed",
        "blind_validation_content_used",
        "scientific_screening_decisions_made",
        "production_mutated",
    ):

        if evidence[field] is not False:
            raise FreezeError(
                "No-fit/no-production evidence changed: "
                + field
            )

    authority = design[
        "authority_at_this_freeze"
    ]

    for field, value in authority.items():

        if value is not False:
            raise FreezeError(
                "Authority unexpectedly broadened: "
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
            or sha(path) != expected
        ):
            raise FreezeError(
                "Bound prior freeze changed: "
                + relative
            )

    checks = parse_sums(
        repo
        / SUMS_REL
    )

    expected_targets = {
        IMPL_REL,
        TEST_REL,
        HOSTILE_REL,
        FREEZE_REL,
        DESIGN_REL,
        DOC_REL,
    }

    if set(
        checks
    ) != expected_targets:
        raise FreezeError(
            "Implementation checksum target set changed"
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
                "Implementation checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | exact corrected evaluator implementation validates"
    )

    print(
        "PASS | 4,190-record whole-batch development contract validates"
    )

    print(
        "PASS | all fit calls isolated and directly authorization-gated"
    )

    print(
        "PASS | raw-float deterministic tie contract validates"
    )

    print(
        "PASS | one-time claim/completion execution contract validates"
    )

    print(
        "PASS | development fitting is not authorized by this freeze"
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
