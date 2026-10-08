from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "38f2934b48bef39f62657cbb3360e2daf61e17e2"
)

EXPECTED_IMPLEMENTATION_SHA = (
    "bd5520bbbb7bad1bc33cab131d21ce90701815a927076fee159ede3045843a10"
)

EXPECTED_CANONICAL_TEXT_SHA = (
    "8c897444fe1a4d26226c8ecb798cd9d08bd3acc362aead972fdbee80d326785b"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

AUTH_REL = (
    ROOT_REL
    + "/pre_review_triage_evaluator_v1_execution_authorization.json"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_evaluator_v1_execution_authorization_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_evaluator_v1_execution_authorization_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_EVALUATOR_V1_EXECUTION_AUTHORIZATION.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_evaluator_v1_execution_authorization.sha256"
)

IMPL_REL = (
    ROOT_REL
    + "/pre_review_triage_evaluator_v1.py"
)

ENVIRONMENT_DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_environment_state_v1_design.json"
)

CANONICAL_TEXT_REL = (
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1/"
    "reconciled_normalized_text.tsv"
)

OUTPUT_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_evaluator_v1/"
    "development_evaluation_v1"
)

FREEZE_PATHS = {
    AUTH_REL,
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
            "Evaluator implementation freeze is not ancestor of HEAD"
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
                "Authorization freeze file not tracked: "
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

    authorization = json.loads(
        (
            repo
            / AUTH_REL
        ).read_text(
            encoding="utf-8"
        )
    )

    if (
        design["status"]
        != "FROZEN_ONE_TIME_DEVELOPMENT_EVALUATION_AUTHORIZATION_PRE_FIRST_FIT"
    ):
        raise FreezeError(
            "Authorization freeze status changed"
        )

    if (
        design["freeze_parent_commit"]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Authorization parent changed"
        )

    environment_design_sha = sha(
        repo
        / ENVIRONMENT_DESIGN_REL
    )

    expected_authorization = {
        "schema_version":
            1,

        "authorization_status":
            "AUTHORIZED_DEVELOPMENT_EVALUATION",

        "authorization_scope":
            "ONE_TIME_FROZEN_DEVELOPMENT_EVALUATION",

        "execution_id":
            "TRIAGE-DEV-EVAL-V1-001",

        "authorized_output_rel":
            OUTPUT_REL,

        "implementation_freeze_commit":
            EXPECTED_PARENT,

        "implementation_sha256":
            EXPECTED_IMPLEMENTATION_SHA,

        "environment_state_design_sha256":
            environment_design_sha,

        "canonical_text_sha256":
            EXPECTED_CANONICAL_TEXT_SHA,

        "model_fit_authorized":
            True,

        "vectorizer_fit_authorized":
            True,

        "hyperparameter_selection_authorized":
            False,

        "threshold_selection_authorized":
            False,

        "future_scoring_authorized":
            False,

        "blind_validation_content_use_authorized":
            False,

        "scientific_screening_decisions_authorized":
            False,

        "production_mutation_authorized":
            False,
    }

    if authorization != expected_authorization:
        raise FreezeError(
            "Authorization payload differs from exact frozen contract"
        )

    if (
        sha(
            repo
            / IMPL_REL
        )
        != EXPECTED_IMPLEMENTATION_SHA
    ):
        raise FreezeError(
            "Evaluator implementation changed"
        )

    if (
        sha(
            repo
            / CANONICAL_TEXT_REL
        )
        != EXPECTED_CANONICAL_TEXT_SHA
    ):
        raise FreezeError(
            "Canonical development text changed"
        )

    artifact = design[
        "authorization_artifact"
    ]

    if (
        artifact["sha256"]
        != sha(
            repo
            / AUTH_REL
        )
    ):
        raise FreezeError(
            "Authorization artifact hash changed"
        )

    if (
        artifact["execution_id"]
        != "TRIAGE-DEV-EVAL-V1-001"
    ):
        raise FreezeError(
            "Execution identity changed"
        )

    bound = design[
        "bound_execution_state"
    ]

    if (
        bound["implementation_freeze_commit"]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Bound implementation freeze changed"
        )

    if (
        bound["implementation_sha256"]
        != EXPECTED_IMPLEMENTATION_SHA
    ):
        raise FreezeError(
            "Bound implementation hash changed"
        )

    if (
        bound["environment_state_design_sha256"]
        != environment_design_sha
    ):
        raise FreezeError(
            "Bound environment-state hash changed"
        )

    if (
        bound["canonical_text_sha256"]
        != EXPECTED_CANONICAL_TEXT_SHA
    ):
        raise FreezeError(
            "Bound canonical-text hash changed"
        )

    authority = design[
        "execution_authority"
    ]

    if authority[
        "model_fit_authorized"
    ] is not True:
        raise FreezeError(
            "Model-fit authority changed"
        )

    if authority[
        "vectorizer_fit_authorized"
    ] is not True:
        raise FreezeError(
            "Vectorizer-fit authority changed"
        )

    for field in (
        "hyperparameter_selection_authorized",
        "threshold_selection_authorized",
        "future_scoring_authorized",
        "blind_validation_content_use_authorized",
        "scientific_screening_decisions_authorized",
        "production_mutation_authorized",
    ):

        if authority[field] is not False:
            raise FreezeError(
                "Authorization scope broadened: "
                + field
            )

    one_time = design[
        "one_time_execution_contract"
    ]

    if (
        one_time[
            "exact_authorization_commit_required_for_execution"
        ]
        is not True
    ):
        raise FreezeError(
            "Exact-authorization-commit requirement changed"
        )

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
            "automatic_cleanup_after_failure"
        ]
        is not False
    ):
        raise FreezeError(
            "Automatic cleanup unexpectedly authorized"
        )

    if (
        one_time[
            "automatic_retry_after_failure"
        ]
        is not False
    ):
        raise FreezeError(
            "Automatic retry unexpectedly authorized"
        )

    development = design[
        "development_evaluation_contract"
    ]

    if development[
        "expected_fit_partitions"
    ] != 252:
        raise FreezeError(
            "Expected fit-partition count changed"
        )

    for field in (
        "threshold_selected",
        "hard_predictions_generated",
    ):

        if development[field] is not False:
            raise FreezeError(
                "Development evaluation scope broadened"
            )

    pre = design[
        "pre_authorization_execution_state"
    ]

    for field, value in pre.items():

        if value is not False:
            raise FreezeError(
                "Pre-authorization no-fit state changed: "
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

    if position == "PRE_COMMIT_PARENT":

        if (
            repo
            / OUTPUT_REL
        ).exists():
            raise FreezeError(
                "Canonical execution output already exists before authorization commit"
            )

    checks = parse_sums(
        repo
        / SUMS_REL
    )

    expected_targets = {
        AUTH_REL,
        FREEZE_REL,
        DESIGN_REL,
        DOC_REL,
    }

    if set(
        checks
    ) != expected_targets:
        raise FreezeError(
            "Authorization checksum target set changed"
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
                "Authorization checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | exact one-time development-evaluation authorization validates"
    )

    print(
        "PASS | evaluator implementation + environment + canonical text bindings validate"
    )

    print(
        "PASS | exactly 252 frozen development fit partitions authorized"
    )

    print(
        "PASS | threshold/future/blind/scientific/production authority remains false"
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
