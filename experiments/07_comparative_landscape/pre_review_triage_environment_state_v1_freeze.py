from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "73b529bf89b5fb108f43cb2c1aeaa39fa76b2c0f"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

STATE_REL = (
    ROOT_REL
    + "/pre_review_triage_environment_state_v1"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_environment_state_v1_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_environment_state_v1_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_ENVIRONMENT_STATE_V1.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_environment_state_v1.sha256"
)

STATE_FILES = {
    STATE_REL + "/conda-list.txt",
    STATE_REL + "/conda-list.json",
    STATE_REL + "/conda-explicit.txt",
    STATE_REL + "/conda-from-history.yml",
    STATE_REL + "/runtime.json",
    STATE_REL + "/creation-contract.txt",
    STATE_REL + "/resolved-state.sha256",
}

FREEZE_PATHS = (
    STATE_FILES
    | {
        FREEZE_REL,
        DESIGN_REL,
        DOC_REL,
        SUMS_REL,
    }
)

EXPECTED_EXECUTION_HASHES = {
    "conda-list.txt":
        "8bf535c087fc75b3532363b40fd35d127362bc361125d371feae29a2db7a3fec",

    "conda-list.json":
        "dec296fbacdd35a17db9035be774930a17b98a2d5e90d048f3387b9011f1524e",

    "conda-explicit.txt":
        "d1d88b51ed4ea51dafbd1cb6d70bdf0a6e2412c2cdfb55bd658c064758deaca7",

    "conda-from-history.yml":
        "c6705fccae1612e41694d41e66e13722b720de329759e64141a89af0b125dd81",

    "runtime.json":
        "0e5af26720d09b004532eaaebbe919883daec78e74766170c09ea583304b6ffd",

    "creation-contract.txt":
        "d8c1f0531869a4bcfcca086303b122f6e07c0dcc1291c1e322971d047e28e09a",
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
            "Environment-creation authorization commit "
            "is not ancestor of HEAD"
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
                "Resolved-state freeze file is not tracked: "
                + relative
            )

    return "COMMITTED_FREEZE_OR_DESCENDANT"


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
        != "FROZEN_RESOLVED_ENVIRONMENT_STATE_PRE_MODEL_IMPLEMENTATION"
    ):
        raise FreezeError(
            "Resolved environment status changed"
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
            "Environment identity changed"
        )

    if identity[
        "runtime_python_major_minor"
    ] != "3.11":
        raise FreezeError(
            "Python major/minor changed"
        )

    if identity[
        "core_packages"
    ] != {
        "numpy":
            "1.26.4",

        "scipy":
            "1.12.0",

        "scikit-learn":
            "1.9.0",
    }:
        raise FreezeError(
            "Core package contract changed"
        )

    state_root = (
        repo
        / STATE_REL
    )

    for name, expected in EXPECTED_EXECUTION_HASHES.items():

        path = (
            state_root
            / name
        )

        if (
            not path.is_file()
            or sha(path) != expected
        ):
            raise FreezeError(
                "Resolved execution artifact changed: "
                + name
            )

    execution_manifest = parse_sums(
        state_root
        / "resolved-state.sha256"
    )

    if set(
        execution_manifest
    ) != set(
        EXPECTED_EXECUTION_HASHES
    ):
        raise FreezeError(
            "Execution checksum target set changed"
        )

    for name, expected in execution_manifest.items():

        if (
            sha(
                state_root
                / name
            )
            != expected
        ):
            raise FreezeError(
                "Execution manifest mismatch: "
                + name
            )

    runtime = json.loads(
        (
            state_root
            / "runtime.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    if runtime[
        "python_major_minor"
    ] != "3.11":
        raise FreezeError(
            "Captured runtime Python changed"
        )

    if runtime[
        "packages"
    ] != {
        "numpy":
            "1.26.4",

        "scikit-learn":
            "1.9.0",

        "scipy":
            "1.12.0",
    }:
        raise FreezeError(
            "Captured runtime packages changed"
        )

    explicit_lines = [
        line.strip()
        for line in (
            state_root
            / "conda-explicit.txt"
        ).read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    if "@EXPLICIT" not in explicit_lines:
        raise FreezeError(
            "Explicit conda marker missing"
        )

    urls = [
        line
        for line in explicit_lines
        if not line.startswith("#")
        and line != "@EXPLICIT"
    ]

    if not urls:
        raise FreezeError(
            "Explicit specification contains no packages"
        )

    if not all(
        line.startswith(
            "https://conda.anaconda.org/conda-forge/"
        )
        for line in urls
    ):
        raise FreezeError(
            "Resolved explicit package source is not conda-forge only"
        )

    artifacts = design[
        "resolved_state_artifacts"
    ]

    if (
        artifacts[
            "conda_explicit_is_authoritative_resolved_package_specification"
        ]
        is not True
    ):
        raise FreezeError(
            "Explicit package authority changed"
        )

    if (
        artifacts[
            "conda_from_history_is_package_origin_authority"
        ]
        is not False
    ):
        raise FreezeError(
            "from-history export incorrectly became package-origin authority"
        )

    if artifacts[
        "observed_from_history_channels"
    ] != [
        "bioconda",
        "conda-forge",
    ]:
        raise FreezeError(
            "Observed history-channel metadata changed"
        )

    evidence = design[
        "validation_evidence"
    ]

    required_true = (
        "live_environment_byte_matched_captured_state_before_freeze",
        "core_versions_validated",
        "candidate_imports_validated",
        "candidate_constructors_validated_without_fit",
    )

    for field in required_true:

        if evidence[field] is not True:
            raise FreezeError(
                "Required validation evidence changed: "
                + field
            )

    required_false = (
        "model_fit_performed",
        "vectorizer_fit_performed",
        "threshold_selection_performed",
        "future_scoring_performed",
        "blind_validation_content_used",
        "scientific_screening_decisions_made",
        "production_mutated",
    )

    for field in required_false:

        if evidence[field] is not False:
            raise FreezeError(
                "Execution boundary changed: "
                + field
            )

    mutation = design[
        "environment_mutation_boundary"
    ]

    for field in (
        "environment_may_be_modified_before_model_implementation",
        "additional_package_installation_permitted_without_amendment",
        "package_upgrade_permitted_without_amendment",
        "package_downgrade_permitted_without_amendment",
        "pip_install_permitted_without_amendment",
        "environment_recreation_permitted_without_amendment",
    ):

        if mutation[field] is not False:
            raise FreezeError(
                "Environment mutation unexpectedly authorized: "
                + field
            )

    if (
        mutation[
            "resolved_environment_state_must_remain_fixed_for_evaluator_implementation"
        ]
        is not True
    ):
        raise FreezeError(
            "Environment immutability requirement changed"
        )

    authority = design[
        "scientific_authority"
    ]

    for field in (
        "evaluator_implementation_authorized_by_this_freeze",
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
            or sha(path) != expected
        ):
            raise FreezeError(
                "Bound prior freeze changed: "
                + relative
            )

    freeze_checks = parse_sums(
        repo
        / SUMS_REL
    )

    expected_freeze_targets = (
        STATE_FILES
        | {
            FREEZE_REL,
            DESIGN_REL,
            DOC_REL,
        }
    )

    if set(
        freeze_checks
    ) != expected_freeze_targets:
        raise FreezeError(
            "Resolved-state freeze checksum target set changed"
        )

    for relative, expected in freeze_checks.items():

        if (
            sha(
                repo
                / relative
            )
            != expected
        ):
            raise FreezeError(
                "Resolved-state freeze checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | exact resolved environment state validates"
    )

    print(
        "PASS | explicit package provenance = conda-forge"
    )

    print(
        "PASS | from-history channel metadata remains non-authoritative"
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
