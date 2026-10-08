from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "4fb3d05247c29125f2312f4c235c3b9d4d8c4ca9"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_model_candidates_v1_amendment_001_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_model_candidates_v1_amendment_001_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_MODEL_CANDIDATES_V1_AMENDMENT_001.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_model_candidates_v1_amendment_001.sha256"
)

FREEZE_PATHS = {
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
            "Expected candidate-freeze parent is not ancestor of HEAD"
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
                "Amendment file not tracked: "
                + relative
            )

    return "COMMITTED_AMENDMENT_OR_DESCENDANT"


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
        != "FROZEN_AMENDMENT_PRE_ENVIRONMENT_CREATION"
    ):
        raise FreezeError(
            "Amendment status changed"
        )

    if (
        design["freeze_parent_commit"]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Amendment parent changed"
        )

    if design[
        "original_environment_statement"
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
            "Original environment statement changed"
        )

    if design[
        "amended_environment_target"
    ] != {
        "python_major_minor":
            "3.11",

        "scikit_learn":
            "1.9.0",

        "numpy":
            "1.26.4",

        "scipy":
            "1.12.0",
    }:
        raise FreezeError(
            "Amended environment target changed"
        )

    unchanged = design[
        "unchanged_model_contract"
    ]

    if unchanged[
        "candidate_ids"
    ] != [
        "logistic_regression_balanced_l2_v1",
        "linear_svc_balanced_l2_v1",
        "complement_nb_v1",
    ]:
        raise FreezeError(
            "Candidate identities changed"
        )

    if unchanged[
        "candidate_count"
    ] != 3:
        raise FreezeError(
            "Candidate count changed"
        )

    for field in (
        "text_representation_changed",
        "candidate_parameters_changed",
        "nested_validation_changed",
        "primary_metric_changed",
        "tie_break_rules_changed",
        "development_population_changed",
        "scientific_authority_changed",
    ):

        if unchanged[field] is not False:
            raise FreezeError(
                "Scientific/model contract unexpectedly changed: "
                + field
            )

    evidence = design[
        "compatibility_evidence"
    ]

    if (
        evidence[
            "python_3_10_solver_result"
        ]
        != "UNSATISFIABLE_FOR_SCIKIT_LEARN_1_9_0"
    ):
        raise FreezeError(
            "Python 3.10 solver evidence changed"
        )

    if (
        evidence[
            "python_3_11_solver_result"
        ]
        != "SOLVES"
    ):
        raise FreezeError(
            "Python 3.11 solver evidence changed"
        )

    for field in (
        "python_3_11_runtime_import_validation_completed",
        "python_3_11_candidate_constructor_validation_completed",
        "dedicated_environment_created",
    ):

        if evidence[field] is not False:
            raise FreezeError(
                "Pre-creation evidence state changed: "
                + field
            )

    authority = design[
        "authority"
    ]

    for field in (
        "environment_creation_authorized_by_this_amendment",
        "package_installation_authorized_by_this_amendment",
        "model_fit_authorized",
        "vectorizer_fit_authorized",
        "threshold_selection_authorized",
        "future_scoring_authorized",
        "blind_validation_content_use_authorized",
        "scientific_screening_decisions_authorized",
        "production_mutation_authorized",
    ):

        if authority[field] is not False:
            raise FreezeError(
                "Authority unexpectedly broadened: "
                + field
            )

    for relative, expected in (
        design[
            "original_freeze_hashes"
        ].items()
    ):

        path = repo / relative

        if (
            not path.is_file()
            or sha(path) != expected
        ):
            raise FreezeError(
                "Original model-candidate freeze changed: "
                + relative
            )

    checks = parse_sums(
        repo
        / SUMS_REL
    )

    expected_targets = {
        FREEZE_REL,
        DESIGN_REL,
        DOC_REL,
    }

    if set(checks) != expected_targets:
        raise FreezeError(
            "Amendment checksum target set changed"
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
                "Amendment checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | Python target corrected 3.10 -> 3.11"
    )

    print(
        "PASS | frozen model/validation contract unchanged"
    )

    print(
        "PASS | environment creation remains unauthorized"
    )

    print(
        "PASS | model fitting remains unauthorized"
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
