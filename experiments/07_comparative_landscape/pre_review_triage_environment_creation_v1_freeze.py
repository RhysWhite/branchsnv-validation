from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "ea85f024d4251fd8eef9deb1e12015eecce86e3f"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_environment_creation_v1_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_environment_creation_v1_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_ENVIRONMENT_CREATION_V1.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_environment_creation_v1.sha256"
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
            "Expected Amendment 001 parent is not ancestor of HEAD"
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
                "Environment-creation freeze file not tracked: "
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
        != "FROZEN_ENVIRONMENT_CREATION_AUTHORIZATION_PRE_EXECUTION"
    ):
        raise FreezeError(
            "Environment-creation freeze status changed"
        )

    if (
        design["freeze_parent_commit"]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Freeze parent changed"
        )

    identity = design[
        "environment_identity"
    ]

    if identity[
        "name"
    ] != "branchsnv-triage-v1":
        raise FreezeError(
            "Environment name changed"
        )

    if identity[
        "expected_prefix"
    ] != "$HOME/.conda/envs/branchsnv-triage-v1":
        raise FreezeError(
            "Environment prefix changed"
        )

    if identity[
        "must_be_absent_before_creation"
    ] is not True:
        raise FreezeError(
            "Pre-creation absence requirement changed"
        )

    if identity[
        "existing_environment_may_be_deleted_or_overwritten"
    ] is not False:
        raise FreezeError(
            "Environment overwrite unexpectedly authorized"
        )

    cache = design[
        "package_cache_contract"
    ]

    if (
        cache["CONDA_PKGS_DIRS"]
        != "$HOME/.conda/pkgs"
    ):
        raise FreezeError(
            "Package cache target changed"
        )

    if cache[
        "user_local_cache_required"
    ] is not True:
        raise FreezeError(
            "User-local package cache requirement changed"
        )

    solver = design[
        "solver_contract"
    ]

    expected_argv = [
        "mamba",
        "create",
        "-y",
        "-n",
        "branchsnv-triage-v1",
        "--override-channels",
        "-c",
        "conda-forge",
        "--strict-channel-priority",
        "python=3.11",
        "numpy=1.26.4",
        "scipy=1.12.0",
        "scikit-learn=1.9.0",
    ]

    if solver[
        "creation_argv"
    ] != expected_argv:
        raise FreezeError(
            "Frozen mamba creation command changed"
        )

    if solver[
        "requested_specs"
    ] != [
        "python=3.11",
        "numpy=1.26.4",
        "scipy=1.12.0",
        "scikit-learn=1.9.0",
    ]:
        raise FreezeError(
            "Requested package specification changed"
        )

    if solver[
        "channels"
    ] != [
        "conda-forge",
    ]:
        raise FreezeError(
            "Channel set changed"
        )

    if solver[
        "override_channels"
    ] is not True:
        raise FreezeError(
            "Channel override requirement changed"
        )

    if solver[
        "strict_channel_priority"
    ] is not True:
        raise FreezeError(
            "Strict channel priority changed"
        )

    validation = design[
        "post_creation_validation"
    ]

    expected_versions = {
        "python_major_minor":
            "3.11",

        "numpy":
            "1.26.4",

        "scipy":
            "1.12.0",

        "scikit_learn":
            "1.9.0",
    }

    for field, expected in expected_versions.items():

        if validation[field] != expected:
            raise FreezeError(
                "Post-creation version target changed: "
                + field
            )

    for field in (
        "candidate_import_validation_required",
        "candidate_constructor_validation_required",
        "capture_conda_list",
        "capture_conda_explicit_specification",
        "capture_conda_from_history",
        "resolved_environment_must_be_frozen_before_model_implementation",
    ):

        if validation[field] is not True:
            raise FreezeError(
                "Required post-creation validation changed: "
                + field
            )

    for field in (
        "model_fit_permitted_during_validation",
        "vectorizer_fit_permitted_during_validation",
    ):

        if validation[field] is not False:
            raise FreezeError(
                "Fit unexpectedly authorized during validation: "
                + field
            )

    authority = design[
        "execution_authority"
    ]

    if authority[
        "environment_creation_authorized"
    ] is not True:
        raise FreezeError(
            "Environment creation not authorized"
        )

    if authority[
        "package_installation_authorized"
    ] is not True:
        raise FreezeError(
            "Package installation not authorized"
        )

    for field in (
        "repository_mutation_during_environment_creation_authorized",
        "model_fit_authorized",
        "vectorizer_fit_authorized",
        "hyperparameter_selection_authorized",
        "threshold_selection_authorized",
        "future_scoring_authorized",
        "blind_validation_content_use_authorized",
        "scientific_screening_decisions_authorized",
        "production_mutation_authorized",
    ):

        if authority[field] is not False:
            raise FreezeError(
                "Execution authority broadened: "
                + field
            )

    failure = design[
        "failure_contract"
    ]

    if failure[
        "automatic_environment_deletion_permitted"
    ] is not False:
        raise FreezeError(
            "Automatic environment deletion authorized"
        )

    if failure[
        "automatic_retry_with_changed_versions_permitted"
    ] is not False:
        raise FreezeError(
            "Automatic version changes authorized"
        )

    if failure[
        "automatic_additional_channels_permitted"
    ] is not False:
        raise FreezeError(
            "Additional channels authorized"
        )

    if failure[
        "automatic_pip_fallback_permitted"
    ] is not False:
        raise FreezeError(
            "pip fallback authorized"
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
                "Environment-creation freeze checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | exact dedicated environment identity validates"
    )

    print(
        "PASS | exact conda-forge creation request validates"
    )

    print(
        "PASS | one environment creation is authorized"
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
