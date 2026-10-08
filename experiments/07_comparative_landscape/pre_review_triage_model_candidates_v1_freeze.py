from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "970a6048d9c18050084ade44d8c346f00a450732"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_model_candidates_v1_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_model_candidates_v1_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_MODEL_CANDIDATES_V1.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_model_candidates_v1.sha256"
)

FREEZE_PATHS = {
    FREEZE_REL,
    DESIGN_REL,
    DOC_REL,
    SUMS_REL,
}

CANONICAL_TEXT_REL = (
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1/"
    "reconciled_normalized_text.tsv"
)

EXPECTED_TEXT_SHA = (
    "8c897444fe1a4d26226c8ecb798cd9d08bd3acc362aead972fdbee80d326785b"
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
            "Expected triage-development parent is not ancestor of HEAD"
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
                "Freeze file is not tracked: "
                + relative
            )

    return "COMMITTED_FREEZE_OR_DESCENDANT"


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
                "Duplicate checksum target"
            )

        values[
            relative
        ] = digest

    return values


def validate():

    repo = repo_root()

    position = repository_position()

    design_path = (
        repo
        / DESIGN_REL
    )

    if not design_path.is_file():
        raise FreezeError(
            "Model-candidate design missing"
        )

    design = json.loads(
        design_path.read_text(
            encoding="utf-8"
        )
    )

    if (
        design["status"]
        != "FROZEN_PRE_MODEL_IMPLEMENTATION"
    ):
        raise FreezeError(
            "Model-candidate status changed"
        )

    if (
        design["freeze_parent_commit"]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Freeze parent changed"
        )

    development = design[
        "development_contract"
    ]

    if development != {
        "records":
            4190,

        "negative_records":
            4022,

        "positive_records":
            168,

        "negative_label":
            "exclude",

        "positive_label":
            "retain_for_method_assessment",

        "negative_numeric_encoding":
            0,

        "positive_numeric_encoding":
            1,

        "batch_ids": [
            "B000001",
            "B000002",
            "B000003",
            "B000004",
            "B000005",
            "B000006",
            "B000007",
            "B000008",
            "B000009",
        ],
    }:
        raise FreezeError(
            "Development contract changed"
        )

    text = design[
        "text_representation"
    ]

    if (
        text[
            "source_sha256"
        ]
        != EXPECTED_TEXT_SHA
    ):
        raise FreezeError(
            "Canonical text hash changed"
        )

    if (
        sha(
            repo
            / CANONICAL_TEXT_REL
        )
        != EXPECTED_TEXT_SHA
    ):
        raise FreezeError(
            "Canonical normalized text no longer matches frozen hash"
        )

    if (
        text[
            "input_fields"
        ]
        != [
            "title_text",
            "abstract_text",
        ]
    ):
        raise FreezeError(
            "Predictive text field set changed"
        )

    if (
        text[
            "vectorizer"
        ][
            "fit_scope"
        ]
        != "training_partition_only"
    ):
        raise FreezeError(
            "Vectorizer fit scope changed"
        )

    candidates = design[
        "candidate_models"
    ]

    ids = [
        candidate[
            "candidate_id"
        ]
        for candidate in candidates
    ]

    if ids != [
        "logistic_regression_balanced_l2_v1",
        "linear_svc_balanced_l2_v1",
        "complement_nb_v1",
    ]:
        raise FreezeError(
            "Candidate family set/order changed"
        )

    boundary = design[
        "candidate_set_boundary"
    ]

    if boundary[
        "candidate_count"
    ] != 3:
        raise FreezeError(
            "Candidate count changed"
        )

    for field in (
        "grid_search_permitted",
        "hyperparameter_search_permitted",
        "additional_model_family_permitted_without_amendment",
        "character_ngram_candidate_permitted",
        "embedding_candidate_permitted",
        "transformer_candidate_permitted",
    ):

        if boundary[field] is not False:
            raise FreezeError(
                "Candidate-search authority broadened: "
                + field
            )

    nested = design[
        "nested_validation"
    ]

    if (
        nested[
            "outer_scheme"
        ]
        != "leave_one_whole_batch_out"
    ):
        raise FreezeError(
            "Outer validation scheme changed"
        )

    if nested[
        "outer_fold_count"
    ] != 9:
        raise FreezeError(
            "Outer fold count changed"
        )

    if (
        nested[
            "inner_scheme"
        ]
        != "leave_one_whole_batch_out_within_outer_training_batches"
    ):
        raise FreezeError(
            "Inner validation scheme changed"
        )

    if (
        nested[
            "inner_fold_count_per_outer_fold"
        ]
        != 8
    ):
        raise FreezeError(
            "Inner fold count changed"
        )

    if (
        nested[
            "inner_candidate_selection_metric"
        ]
        != "macro_mean_batch_average_precision"
    ):
        raise FreezeError(
            "Inner candidate-selection metric changed"
        )

    metric = design[
        "metric_contract"
    ]

    if (
        metric[
            "primary_ranking_metric"
        ]
        != "average_precision"
    ):
        raise FreezeError(
            "Primary ranking metric changed"
        )

    for field in (
        "hard_predictions_generated",
        "default_model_decision_boundary_used",
        "precision_at_threshold_computed",
        "recall_at_threshold_computed",
        "threshold_optimization_permitted",
        "acceptable_recall_threshold_defined",
    ):

        if metric[field] is not False:
            raise FreezeError(
                "Threshold authority broadened: "
                + field
            )

    environment = design[
        "environment_contract"
    ]

    if environment[
        "api_reference_versions"
    ] != {
        "python_major_minor":
            "3.10",

        "scikit_learn":
            "1.9.0",

        "numpy":
            "1.26.4",

        "scipy":
            "1.12.0",
    }:
        raise FreezeError(
            "Reference environment versions changed"
        )

    if (
        environment[
            "existing_mixed_sample_environment_may_be_used_for_model_fit"
        ]
        is not False
    ):
        raise FreezeError(
            "Unrelated environment unexpectedly authorized"
        )

    if (
        environment[
            "dedicated_branchsnv_environment_required"
        ]
        is not True
    ):
        raise FreezeError(
            "Dedicated environment requirement changed"
        )

    authority = design[
        "scientific_authority"
    ]

    for field in (
        "model_fit_authorized_by_this_freeze",
        "vectorizer_fit_authorized_by_this_freeze",
        "threshold_selection_authorized_by_this_freeze",
        "future_scoring_authorized_by_this_freeze",
        "blind_validation_content_use_authorized",
        "scientific_screening_decisions_authorized",
        "production_auto_exclusion_authorized",
        "production_ledger_write_authorized",
    ):

        if authority[field] is not False:
            raise FreezeError(
                "Authority broadened: "
                + field
            )

    for relative, expected in (
        design[
            "parent_development_freeze_hashes"
        ].items()
    ):

        path = (
            repo
            / relative
        )

        if (
            not path.is_file()
            or sha(path) != expected
        ):
            raise FreezeError(
                "Parent development freeze changed: "
                + relative
            )

    parent_design_path = (
        repo
        / "experiments/07_comparative_landscape/"
          "pre_review_triage_development_v1_design.json"
    )

    parent_design = json.loads(
        parent_design_path.read_text(
            encoding="utf-8"
        )
    )

    for relative, expected in (
        parent_design[
            "source_hashes"
        ].items()
    ):

        path = repo / relative

        if (
            not path.is_file()
            or sha(path) != expected
        ):
            raise FreezeError(
                "Parent-bound scientific source changed: "
                + relative
            )

    checksum_path = (
        repo
        / SUMS_REL
    )

    checks = parse_sums(
        checksum_path
    )

    expected_targets = {
        FREEZE_REL,
        DESIGN_REL,
        DOC_REL,
    }

    if set(checks) != expected_targets:
        raise FreezeError(
            "Checksum target set changed"
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
                "Model-candidate checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | exact three-candidate set validates"
    )

    print(
        "PASS | nested whole-batch protocol validates"
    )

    print(
        "PASS | threshold selection remains unauthorized"
    )

    print(
        "PASS | model/vectorizer fitting remains unauthorized"
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
