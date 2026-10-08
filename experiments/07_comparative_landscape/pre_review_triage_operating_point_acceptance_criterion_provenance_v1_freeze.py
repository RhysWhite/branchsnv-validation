from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "65d2ee36ff67784d3dd04aea39f0d7d465306040"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_acceptance_criterion_"
      "provenance_v1_design.json"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_acceptance_criterion_"
      "provenance_v1_freeze.py"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_OPERATING_POINT_ACCEPTANCE_CRITERION_"
      "PROVENANCE_V1.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_acceptance_criterion_"
      "provenance_v1.sha256"
)

FREEZE_PATHS = {
    DESIGN_REL,
    FREEZE_REL,
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
            "Frozen curve-result commit is not ancestor of HEAD"
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
                "Criterion-provenance freeze path not tracked: "
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
        != "FROZEN_NO_UPSTREAM_ACCEPTANCE_CRITERION_PRE_NEW_CRITERION"
    ):
        raise FreezeError(
            "Criterion provenance status changed"
        )

    if (
        design[
            "freeze_parent_commit"
        ]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Criterion provenance parent changed"
        )

    provenance = design[
        "provenance_classification"
    ]

    for field in (
        "upstream_acceptable_recall_target_existed",
        "upstream_workload_target_existed",
        "upstream_review_fraction_existed",
        "upstream_score_threshold_existed",
        "upstream_operating_point_existed",
        "upstream_model_acceptance_rule_existed",
    ):

        if provenance[
            field
        ] is not False:
            raise FreezeError(
                "Upstream criterion unexpectedly appeared: "
                + field
            )

    if (
        provenance[
            "new_acceptance_criterion_will_be_post_development_curve"
        ]
        is not True
    ):
        raise FreezeError(
            "Post-development provenance classification changed"
        )

    if (
        provenance[
            "new_acceptance_criterion_must_be_declared_before_curve_based_selection"
        ]
        is not True
    ):
        raise FreezeError(
            "Pre-selection declaration requirement changed"
        )

    sampling = design[
        "validation_sampling_rule_classification"
    ]

    if (
        sampling[
            "minimum_retained_positive_records"
        ]
        != 60
    ):
        raise FreezeError(
            "Validation sampling minimum changed"
        )

    for field in (
        "is_model_acceptance_rule",
        "is_score_threshold",
        "is_review_fraction",
        "is_recall_target",
        "may_be_repurposed_as_operating_point_criterion",
    ):

        if sampling[
            field
        ] is not False:
            raise FreezeError(
                "Validation sampling rule was improperly repurposed: "
                + field
            )

    evidence = design[
        "evidence_contract"
    ]

    for field, value in evidence.items():

        if value is not True:
            raise FreezeError(
                "Frozen provenance evidence changed: "
                + field
            )

    selection = design[
        "selection_boundary"
    ]

    for field, value in selection.items():

        if value is not False:
            raise FreezeError(
                "Selection authority unexpectedly broadened: "
                + field
            )

    blind = design[
        "blind_validation_boundary"
    ]

    for field, value in blind.items():

        if value is not False:
            raise FreezeError(
                "Blind-validation boundary changed: "
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
        DESIGN_REL,
        FREEZE_REL,
        DOC_REL,
    }

    if set(
        manifest
    ) != expected_targets:
        raise FreezeError(
            "Criterion-provenance checksum target set changed"
        )

    for relative, expected in manifest.items():

        if sha(
            repo
            / relative
        ) != expected:
            raise FreezeError(
                "Criterion-provenance checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | no upstream model-acceptance criterion existed"
    )

    print(
        "PASS | no upstream recall/workload/review-fraction/score cutoff existed"
    )

    print(
        "PASS | 60-positive rule remains validation-sample sufficiency only"
    )

    print(
        "PASS | new criterion must be prospectively declared before curve selection"
    )

    print(
        "PASS | no criterion or operating point selected"
    )

    print(
        "PASS | blind-validation content remains unused"
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
