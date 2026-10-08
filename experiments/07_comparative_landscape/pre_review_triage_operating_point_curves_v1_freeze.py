from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "a33001f2cb2f4d333d841d125f409520e86afeac"
)

EXPECTED_AMENDED_SHA = (
    "6e2edf8e625d769d8de85c4e4957d708ea7774c23d160976fe0030a323f46acd"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

PREFIX_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1/"
    "per_batch_prefix_curve.tsv"
)

CROSS_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1/"
    "cross_batch_review_fraction_curve.tsv"
)

SUMMARY_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_operating_point_curve_v1/"
    "summary.json"
)

AMENDED_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curve_v1_amendment_001.py"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curves_v1_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curves_v1_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_OPERATING_POINT_CURVES_V1.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curves_v1.sha256"
)

EXPECTED_ARTIFACTS = {
    PREFIX_REL:
        "fc31fe946c3b41ccb197650e6c6434a74c379d2bb3221897e7e9af1d8c7da68b",

    CROSS_REL:
        "e6eeef6d8236c1062126c8d69a40f92c2c71e272840a653b9f14dca4505d4e1b",

    SUMMARY_REL:
        "70cc7bd3ae86e3996950cd11e8891c77c618e1ff33a9a80e5b62220412cd5310",
}

FREEZE_PATHS = (
    set(
        EXPECTED_ARTIFACTS
    )
    | {
        FREEZE_REL,
        DESIGN_REL,
        DOC_REL,
        SUMS_REL,
    }
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


def count_tsv(path):

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        return sum(
            1
            for _ in csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


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
            "Amendment 001 commit is not ancestor of HEAD"
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
                "Curve-result freeze path not tracked: "
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
        / AMENDED_REL
    ) != EXPECTED_AMENDED_SHA:
        raise FreezeError(
            "Amendment 001 executable changed"
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
        != "FROZEN_DEVELOPMENT_OPERATING_POINT_CURVES_NO_SELECTION"
    ):
        raise FreezeError(
            "Curve-result status changed"
        )

    if (
        design[
            "freeze_parent_commit"
        ]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Curve-result freeze parent changed"
        )

    if (
        design[
            "artifact_contract"
        ][
            "artifacts"
        ]
        != EXPECTED_ARTIFACTS
    ):
        raise FreezeError(
            "Frozen curve artifact contract changed"
        )

    for relative, expected in EXPECTED_ARTIFACTS.items():

        if sha(
            repo
            / relative
        ) != expected:
            raise FreezeError(
                "Frozen curve artifact changed: "
                + relative
            )

    if count_tsv(
        repo
        / PREFIX_REL
    ) != 4199:
        raise FreezeError(
            "Prefix-curve row count changed"
        )

    if count_tsv(
        repo
        / CROSS_REL
    ) != 4047:
        raise FreezeError(
            "Cross-batch curve row count changed"
        )

    summary = json.loads(
        (
            repo
            / SUMMARY_REL
        ).read_text(
            encoding="utf-8"
        )
    )

    if (
        summary[
            "status"
        ]
        != "OPERATING_POINT_CURVE_GENERATED_NO_SELECTION"
    ):
        raise FreezeError(
            "Generated curve summary status changed"
        )

    if summary[
        "development_records"
    ] != 4190:
        raise FreezeError(
            "Development record count changed"
        )

    if summary[
        "positive_records"
    ] != 168:
        raise FreezeError(
            "Development positive count changed"
        )

    if summary[
        "negative_records"
    ] != 4022:
        raise FreezeError(
            "Development negative count changed"
        )

    if summary[
        "per_batch_prefix_rows"
    ] != 4199:
        raise FreezeError(
            "Summary prefix-row count changed"
        )

    if summary[
        "cross_batch_exact_fraction_grid_rows"
    ] != 4047:
        raise FreezeError(
            "Summary exact-grid count changed"
        )

    if (
        summary[
            "selected_model_family"
        ]
        != "linear_svc_balanced_l2_v1"
    ):
        raise FreezeError(
            "Selected family changed"
        )

    generation = design[
        "generation_contract"
    ]

    if generation[
        "generator"
    ] != "AMENDMENT_001":
        raise FreezeError(
            "Curve generator provenance changed"
        )

    if generation[
        "base_implementation_modified"
    ] is not False:
        raise FreezeError(
            "Base implementation unexpectedly marked modified"
        )

    if generation[
        "failed_attempt_001_preserved"
    ] is not True:
        raise FreezeError(
            "Failed-attempt provenance changed"
        )

    if generation[
        "regeneration_after_successful_amended_generation"
    ] is not False:
        raise FreezeError(
            "Successful artifacts unexpectedly regenerated"
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

    selection = design[
        "selection_boundary"
    ]

    for field, value in selection.items():

        if value is not False:
            raise FreezeError(
                "Selection authority broadened: "
                + field
            )

    scientific = design[
        "scientific_boundary"
    ]

    if scientific[
        "development_evidence_only"
    ] is not True:
        raise FreezeError(
            "Development-only boundary changed"
        )

    for field in (
        "model_fit_performed",
        "vectorizer_fit_performed",
        "calibration_fit_performed",
        "future_scoring_performed",
        "blind_validation_content_used",
        "scientific_screening_decisions_made",
        "production_mutated",
    ):

        if scientific[
            field
        ] is not False:
            raise FreezeError(
                "Scientific boundary broadened: "
                + field
            )

    gate = design[
        "next_selection_gate"
    ]

    if gate[
        "curve_may_directly_choose_operating_point"
    ] is not False:
        raise FreezeError(
            "Curve unexpectedly authorized to choose operating point"
        )

    if gate[
        "acceptance_criterion_or_workload_constraint_required"
    ] is not True:
        raise FreezeError(
            "Acceptance-criterion requirement changed"
        )

    if gate[
        "criterion_must_be_frozen_before_selection"
    ] is not True:
        raise FreezeError(
            "Criterion freeze requirement changed"
        )

    if gate[
        "criterion_must_not_be_reverse_engineered_from_preferred_curve_point"
    ] is not True:
        raise FreezeError(
            "Post-hoc selection protection changed"
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

    expected_targets = (
        set(
            EXPECTED_ARTIFACTS
        )
        | {
            FREEZE_REL,
            DESIGN_REL,
            DOC_REL,
        }
    )

    if set(
        manifest
    ) != expected_targets:
        raise FreezeError(
            "Curve-result checksum target set changed"
        )

    for relative, expected in manifest.items():

        if sha(
            repo
            / relative
        ) != expected:
            raise FreezeError(
                "Curve-result checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | exact three Amendment 001 curve artifacts validate"
    )

    print(
        "PASS | 4,199 prefix rows validate"
    )

    print(
        "PASS | 4,047 exact-fraction rows validate"
    )

    print(
        "PASS | Amendment 001 provenance validates"
    )

    print(
        "PASS | successful outputs were not regenerated"
    )

    print(
        "PASS | independent-audit evidence frozen"
    )

    print(
        "PASS | no operating point or acceptance criterion selected"
    )

    print(
        "PASS | no fit/future/blind/scientific/production activity"
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
