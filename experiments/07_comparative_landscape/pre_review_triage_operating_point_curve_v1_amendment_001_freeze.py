from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "78ad4d356bc7aa972b8f5e9b4f81921c4ad4dae8"
)

EXPECTED_BASE_SHA = (
    "bc0b44961ba6e1c5c8e022979d97d7df961ab68c79bc6c2815be6d72cac8db65"
)

EXPECTED_PARTIAL_SHA = (
    "743ebdcfd7fb6896655c863c8b593f9dca8db1c0347a2f8fe2735f7062acc95b"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

BASE_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curve_v1.py"
)

AMENDED_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curve_v1_amendment_001.py"
)

TEST_REL = (
    ROOT_REL
    + "/test_pre_review_triage_operating_point_curve_v1_amendment_001.py"
)

HOSTILE_REL = (
    ROOT_REL
    + "/test_pre_review_triage_operating_point_curve_v1_amendment_001_hostile.py"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curve_v1_amendment_001_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curve_v1_amendment_001_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_OPERATING_POINT_CURVE_V1_AMENDMENT_001.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curve_v1_amendment_001.sha256"
)

FAIL_PARTIAL_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1_failed_attempt_001/"
    "per_batch_prefix_curve.tsv.partial"
)

FAIL_RECEIPT_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1_failed_attempt_001/"
    "failure_receipt.json"
)

CANONICAL_PARTIAL_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1/"
    "per_batch_prefix_curve.tsv"
)

FREEZE_PATHS = {
    AMENDED_REL,
    TEST_REL,
    HOSTILE_REL,
    FREEZE_REL,
    DESIGN_REL,
    DOC_REL,
    SUMS_REL,
    FAIL_PARTIAL_REL,
    FAIL_RECEIPT_REL,
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
            "Base implementation freeze is not ancestor of HEAD"
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
                "Amendment freeze artifact not tracked: "
                + relative
            )

    return "COMMITTED_FREEZE_OR_DESCENDANT"


def parse_manifest(path):

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


def validate():

    repo = repo_root()

    position = repository_position()

    if sha(
        repo
        / BASE_REL
    ) != EXPECTED_BASE_SHA:
        raise FreezeError(
            "Frozen base implementation changed"
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
        != "FROZEN_SERIALIZATION_AMENDMENT_001_PRE_REGENERATION"
    ):
        raise FreezeError(
            "Amendment status changed"
        )

    if (
        design[
            "freeze_parent_commit"
        ]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Amendment parent changed"
        )

    failure = design[
        "failure_evidence"
    ]

    if sha(
        repo
        / FAIL_PARTIAL_REL
    ) != EXPECTED_PARTIAL_SHA:
        raise FreezeError(
            "Archived failed partial changed"
        )

    if failure[
        "archived_partial_sha256"
    ] != EXPECTED_PARTIAL_SHA:
        raise FreezeError(
            "Failed partial hash contract changed"
        )

    archived_lines = (
        repo
        / FAIL_PARTIAL_REL
    ).read_text(
        encoding="utf-8"
    ).splitlines()

    if len(
        archived_lines
    ) != 1:
        raise FreezeError(
            "Archived failed partial is not header-only"
        )

    receipt = json.loads(
        (
            repo
            / FAIL_RECEIPT_REL
        ).read_text(
            encoding="utf-8"
        )
    )

    if (
        receipt[
            "status"
        ]
        != "FAILED_CURVE_GENERATION_ATTEMPT_001_PRESERVED"
    ):
        raise FreezeError(
            "Failed-attempt receipt status changed"
        )

    if (
        receipt[
            "partial_sha256"
        ]
        != EXPECTED_PARTIAL_SHA
    ):
        raise FreezeError(
            "Failed-attempt receipt partial hash changed"
        )

    if receipt[
        "partial_contains_data_rows"
    ] is not False:
        raise FreezeError(
            "Failed attempt unexpectedly contains data rows"
        )

    if position == "PRE_COMMIT_PARENT":

        canonical = (
            repo
            / CANONICAL_PARTIAL_REL
        )

        if not canonical.is_file():
            raise FreezeError(
                "Canonical failed partial missing before amendment commit"
            )

        if sha(
            canonical
        ) != EXPECTED_PARTIAL_SHA:
            raise FreezeError(
                "Canonical failed partial changed before archive commit"
            )

    amendment = design[
        "amendment_contract"
    ]

    if (
        amendment[
            "scope"
        ]
        != "serialization_string_passthrough_only"
    ):
        raise FreezeError(
            "Amendment scope changed"
        )

    for field in (
        "ranking_changed",
        "fraction_grid_changed",
        "batch_review_count_rule_changed",
        "curve_metric_arithmetic_changed",
        "selection_policy_changed",
        "base_file_modified",
    ):

        if amendment[
            field
        ] is not False:
            raise FreezeError(
                "Amendment scope broadened: "
                + field
            )

    expected_artifacts = {
        AMENDED_REL:
            amendment[
                "amended_executable_sha256"
            ],

        TEST_REL:
            amendment[
                "standard_test_sha256"
            ],

        HOSTILE_REL:
            amendment[
                "hostile_test_sha256"
            ],
    }

    for relative, expected in expected_artifacts.items():

        if sha(
            repo
            / relative
        ) != expected:
            raise FreezeError(
                "Amendment implementation artifact changed: "
                + relative
            )

    source = (
        repo
        / AMENDED_REL
    ).read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    forbidden = {
        "fit",
        "fit_transform",
        "predict",
        "predict_proba",
        "decision_function",
    }

    observed = []

    for node in ast.walk(
        tree
    ):

        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        func = node.func

        if (
            isinstance(
                func,
                ast.Attribute,
            )
            and func.attr in forbidden
        ):
            observed.append(
                (
                    func.attr,
                    node.lineno,
                )
            )

    if observed:
        raise FreezeError(
            "Fit/predict surface introduced: "
            + repr(
                observed
            )
        )

    if (
        "BASE.format_number = format_number"
        not in source
    ):
        raise FreezeError(
            "Runtime serializer replacement missing"
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

        if sha(
            repo
            / relative
        ) != expected:
            raise FreezeError(
                "Bound prior freeze changed: "
                + relative
            )

    manifest = parse_manifest(
        repo
        / SUMS_REL
    )

    expected_targets = {
        AMENDED_REL,
        TEST_REL,
        HOSTILE_REL,
        FREEZE_REL,
        DESIGN_REL,
        DOC_REL,
        FAIL_PARTIAL_REL,
        FAIL_RECEIPT_REL,
    }

    if set(
        manifest
    ) != expected_targets:
        raise FreezeError(
            "Amendment checksum target set changed"
        )

    for relative, expected in manifest.items():

        if sha(
            repo
            / relative
        ) != expected:
            raise FreezeError(
                "Amendment checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | frozen base implementation remains byte-exact"
    )

    print(
        "PASS | failed generation attempt preserved byte-for-byte"
    )

    print(
        "PASS | serialization Amendment 001 validates"
    )

    print(
        "PASS | amendment scope is string serialization only"
    )

    print(
        "PASS | mathematical curve contract unchanged"
    )

    print(
        "PASS | no fit/selection/future/blind/scientific/production authority"
    )


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
