from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "c473ea381eaeaecea2f4f46996f184a5e996ffde"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

IMPL_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curve_v1.py"
)

TEST_REL = (
    ROOT_REL
    + "/test_pre_review_triage_operating_point_curve_v1.py"
)

HOSTILE_REL = (
    ROOT_REL
    + "/test_pre_review_triage_operating_point_curve_hostile_v1.py"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curve_v1_implementation_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curve_v1_implementation_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_OPERATING_POINT_CURVE_V1_IMPLEMENTATION.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_operating_point_curve_v1_implementation.sha256"
)

INPUT_REL = (
    "results/07_comparative_landscape/"
    "pre_review_triage_evaluator_v1/"
    "development_evaluation_v1/"
    "outer_scores.tsv"
)

EXPECTED_INPUT_SHA = (
    "1da5b38902d893a91cb99b7d9965f179717667c42b66ff80f63313ac50251c47"
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
            "Operating-point design freeze is not ancestor of HEAD"
        )

    for relative in FREEZE_PATHS:
        result = subprocess.run(
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

        if result.returncode != 0:
            raise FreezeError(
                "Curve implementation freeze file not tracked: "
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

        values[
            relative.strip()
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
        != "FROZEN_PRE_CURVE_GENERATION"
    ):
        raise FreezeError(
            "Curve implementation status changed"
        )

    if (
        design["freeze_parent_commit"]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Curve implementation parent changed"
        )

    implementation = design[
        "implementation_contract"
    ]

    expected = {
        IMPL_REL:
            implementation[
                "implementation_sha256"
            ],

        TEST_REL:
            implementation[
                "standard_test_sha256"
            ],

        HOSTILE_REL:
            implementation[
                "hostile_test_sha256"
            ],
    }

    for relative, digest in expected.items():
        if sha(
            repo
            / relative
        ) != digest:
            raise FreezeError(
                "Curve implementation artifact changed: "
                + relative
            )

    if sha(
        repo
        / INPUT_REL
    ) != EXPECTED_INPUT_SHA:
        raise FreezeError(
            "Frozen OOF input changed"
        )

    source = (
        repo
        / IMPL_REL
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

    calls = []

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
            calls.append(
                (
                    func.attr,
                    node.lineno,
                )
            )

    if calls:
        raise FreezeError(
            "Fit/predict surface introduced: "
            + repr(
                calls
            )
        )

    ranking = design[
        "ranking_contract"
    ]

    if (
        ranking["primary_sort"]
        != "continuous_score_descending"
    ):
        raise FreezeError(
            "Ranking primary sort changed"
        )

    if (
        ranking["tie_break"]
        != "screening_entity_id_ascending"
    ):
        raise FreezeError(
            "Ranking tie-break changed"
        )

    if ranking[
        "label_used_for_ranking"
    ] is not False:
        raise FreezeError(
            "Scientific label introduced into ranking"
        )

    cross = design[
        "cross_batch_contract"
    ]

    if (
        cross["fraction_arithmetic"]
        != "python_fractions_Fraction"
    ):
        raise FreezeError(
            "Exact fraction arithmetic changed"
        )

    if (
        cross["batch_review_count_rule"]
        != "ceil_exact_fraction_times_batch_size"
    ):
        raise FreezeError(
            "Batch review-count rule changed"
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

    scientific = design[
        "scientific_boundary"
    ]

    for field, value in scientific.items():
        if value is not False:
            raise FreezeError(
                "Scientific authority unexpectedly broadened: "
                + field
            )

    for relative, digest in (
        design[
            "bound_prior_freeze_hashes"
        ].items()
    ):
        if sha(
            repo
            / relative
        ) != digest:
            raise FreezeError(
                "Bound prior freeze changed: "
                + relative
            )

    manifest = parse_manifest(
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
        manifest
    ) != expected_targets:
        raise FreezeError(
            "Curve implementation checksum target set changed"
        )

    for relative, digest in manifest.items():
        if sha(
            repo
            / relative
        ) != digest:
            raise FreezeError(
                "Curve implementation checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | curve implementation v1 validates"
    )

    print(
        "PASS | exact Fraction-based review grid frozen"
    )

    print(
        "PASS | deterministic within-batch ranking frozen"
    )

    print(
        "PASS | no fit/predict/calibration call surface"
    )

    print(
        "PASS | no operating point or acceptance target selected"
    )

    print(
        "PASS | no future/blind/scientific/production authority"
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
