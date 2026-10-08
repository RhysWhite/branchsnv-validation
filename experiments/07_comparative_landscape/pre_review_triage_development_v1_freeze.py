from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED_PARENT = (
    "bbbda0a27c5aa7c92f1bf632261e356a8955a863"
)

ROOT_REL = (
    "experiments/07_comparative_landscape"
)

FREEZE_REL = (
    ROOT_REL
    + "/pre_review_triage_development_v1_freeze.py"
)

DESIGN_REL = (
    ROOT_REL
    + "/pre_review_triage_development_v1_design.json"
)

DOC_REL = (
    ROOT_REL
    + "/PRE_REVIEW_TRIAGE_DEVELOPMENT_V1.md"
)

SUMS_REL = (
    ROOT_REL
    + "/pre_review_triage_development_v1.sha256"
)

EXPECTED_COMMIT_PATHS = {
    FREEZE_REL,
    DESIGN_REL,
    DOC_REL,
    SUMS_REL,
}

EXPECTED_CANONICAL_HASHES = {
    "reconciled_resolution.tsv":
        "cb2a5d32d6eabcde6ba7aa5db52bfcc813fc52e45a897cac7ec13a632ce016d5",

    "reconciled_normalized_text.tsv":
        "8c897444fe1a4d26226c8ecb798cd9d08bd3acc362aead972fdbee80d326785b",

    "reconciliation_summary.json":
        "c43385e506a7d37c5290fdb3842c2991c0398efcf944f57be68ffadd51d5c802",

    "reconciliation_outputs.sha256":
        "62aa1bed45d5bfc77b190247d94a1a9e4bb7be772d14fb55f2cbf03f3ab3f5cf",
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

    head = git_output(
        "rev-parse",
        "HEAD",
    )

    if head == EXPECTED_PARENT:
        return "PRE_COMMIT_PARENT"

    parent = git_output(
        "rev-parse",
        "HEAD^",
    )

    if parent != EXPECTED_PARENT:
        raise FreezeError(
            "HEAD is neither expected parent nor direct freeze child"
        )

    changed = {
        line
        for line in git_output(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).splitlines()
        if line
    }

    if changed != EXPECTED_COMMIT_PATHS:
        raise FreezeError(
            "Committed path set differs from four-file design freeze"
        )

    return "COMMITTED_FREEZE"


def validate():

    repo = repo_root()

    position = repository_position()

    design_path = (
        repo
        / DESIGN_REL
    )

    if not design_path.is_file():
        raise FreezeError(
            "Design JSON missing"
        )

    design = json.loads(
        design_path.read_text(
            encoding="utf-8"
        )
    )

    if (
        design["status"]
        != "FROZEN_PRE_MODEL_CANDIDATE_SELECTION"
    ):
        raise FreezeError(
            "Design status changed"
        )

    if (
        design["freeze_parent_commit"]
        != EXPECTED_PARENT
    ):
        raise FreezeError(
            "Freeze parent changed"
        )

    population = design[
        "development_population"
    ]

    expected_population = {
        "expanded_development_records":
            4500,

        "final_label_counts": {
            "exclude":
                4297,

            "retain_for_method_assessment":
                203,
        },

        "retrieval_lane_records":
            4499,

        "protected_identity_records":
            1,

        "protected_identity_label":
            "exclude",

        "protected_identity_attention_status":
            "identifier_conflict_hold",

        "text_bearing_records":
            4190,

        "text_bearing_label_counts": {
            "exclude":
                4022,

            "retain_for_method_assessment":
                168,
        },

        "abstract_absent_records":
            309,

        "abstract_absent_label_counts": {
            "exclude":
                274,

            "retain_for_method_assessment":
                35,
        },
    }

    if population != expected_population:
        raise FreezeError(
            "Frozen development population changed"
        )

    label_contract = design[
        "label_contract"
    ]

    if (
        label_contract[
            "positive_class"
        ]
        != "retain_for_method_assessment"
    ):
        raise FreezeError(
            "Positive class changed"
        )

    if (
        label_contract[
            "negative_class"
        ]
        != "exclude"
    ):
        raise FreezeError(
            "Negative class changed"
        )

    allowed = (
        design[
            "model_development_lane"
        ][
            "allowed_predictive_text_fields"
        ]
    )

    if allowed != [
        "title_text",
        "abstract_text",
    ]:
        raise FreezeError(
            "Predictive text authority changed"
        )

    protected = design[
        "protected_review_lanes"
    ]

    if (
        protected[
            "abstract_absent"
        ][
            "model_training_permitted"
        ]
        is not False
    ):
        raise FreezeError(
            "Abstract-absent training unexpectedly authorized"
        )

    if (
        protected[
            "abstract_absent"
        ][
            "model_scoring_permitted"
        ]
        is not False
    ):
        raise FreezeError(
            "Abstract-absent scoring unexpectedly authorized"
        )

    if (
        protected[
            "abstract_absent"
        ][
            "absence_may_be_used_as_negative_evidence"
        ]
        is not False
    ):
        raise FreezeError(
            "Abstract absence converted to negative evidence"
        )

    validation = design[
        "validation_contract"
    ]

    required_false = [
        "row_random_split_permitted",
        "blind_validation_content_may_be_used_for_model_development",
        "blind_validation_labels_may_be_used_for_model_selection",
        "blind_validation_labels_may_be_used_for_threshold_selection",
        "current_design_selects_model_family",
        "current_design_selects_hyperparameters",
        "current_design_selects_score_threshold",
        "current_design_selects_recall_acceptance_threshold",
        "prior_sampling_minimum_positive_rule_adopted_as_model_acceptance_rule",
    ]

    for field in required_false:

        if validation[field] is not False:
            raise FreezeError(
                "Validation authority broadened: "
                + field
            )

    if (
        validation[
            "whole_batch_validation_required"
        ]
        is not True
    ):
        raise FreezeError(
            "Whole-batch validation requirement changed"
        )

    authority = design[
        "scientific_authority"
    ]

    for field in (
        "autonomous_model_scientific_decision_permitted",
        "production_auto_exclusion_permitted",
        "production_ledger_write_permitted",
        "production_queue_mutation_permitted",
        "future_scoring_authorized_by_this_design",
    ):

        if authority[field] is not False:
            raise FreezeError(
                "Scientific authority broadened: "
                + field
            )

    if (
        design[
            "canonical_reconciliation_sha256"
        ]
        != EXPECTED_CANONICAL_HASHES
    ):
        raise FreezeError(
            "Canonical reconciliation hash authority changed"
        )

    for relative, expected in (
        design[
            "source_hashes"
        ].items()
    ):

        path = (
            repo
            / relative
        )

        if not path.is_file():
            raise FreezeError(
                "Bound source missing: "
                + relative
            )

        if sha(path) != expected:
            raise FreezeError(
                "Bound source hash mismatch: "
                + relative
            )

    checksum_path = (
        repo
        / SUMS_REL
    )

    if not checksum_path.is_file():
        raise FreezeError(
            "Design checksum manifest missing"
        )

    checks = {}

    for line in checksum_path.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        digest, relative = line.split(
            None,
            1,
        )

        relative = relative.strip()

        if relative in checks:
            raise FreezeError(
                "Duplicate checksum target"
            )

        checks[
            relative
        ] = digest

    expected_targets = {
        FREEZE_REL,
        DESIGN_REL,
        DOC_REL,
    }

    if set(checks) != expected_targets:
        raise FreezeError(
            "Design checksum target set changed"
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
                "Design checksum mismatch: "
                + relative
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | pre-review triage development v1 validates"
    )

    print(
        "PASS | model family not selected"
    )

    print(
        "PASS | score/recall threshold not selected"
    )

    print(
        "PASS | no future scoring authority"
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
