from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path("experiments/07_comparative_landscape")

RESULTS = Path(
    "results/07_comparative_landscape"
)

OUTROOT = (
    RESULTS
    / "pre_review_triage_future_review_queue_v1"
)

EXPECTED_PARENT = "9ea56ec4cee7cf84215fc094666e2722f6494bce"

AUTH = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "generation_authorization.json"
)

FREEZE = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "generation_authorization_freeze.py"
)

DESIGN = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "generation_authorization_design.json"
)

DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_"
    "GENERATION_AUTHORIZATION.md"
)

SUMS = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "generation_authorization.sha256"
)

IMPL_SUMS = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_implementation.sha256"
)

QUEUE_DESIGN_SUMS = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_design.sha256"
)

SCORING_RESULTS_SUMS = (
    ROOT
    / "pre_review_triage_future_scoring_results_v1.sha256"
)

EXPECTED_IMPL_SUMS_SHA = "f7b3eca45cee5b49e2ee63e4a2ddc778dc1f46291346c0c855ea737e2bd0793d"
EXPECTED_QUEUE_DESIGN_SUMS_SHA = "319ce18f144b97acc1d6c5b277420bd7b9f66fce0e99b2b8207a657559ea1e26"
EXPECTED_SCORING_RESULTS_SUMS_SHA = "8be5645fb71f557306be11ae132f1d655013d6a6d573beb50380399cad9bc939"

EXPECTED_AUTH_SHA = "f6b018056fdf4ffb9e7a404dcc08ae1f6993ca8ad73b008be67aa2c503b05018"
EXPECTED_DESIGN_SHA = "3c3d5be977a9f7fdc5dad1a0449e3410f044f640a0d88bcd20f602adeb6a2e59"
EXPECTED_DOC_SHA = "bee108547a0b512c2315de33962e0815924f5042a74e5b1e7c612a738a2635e8"

EXPECTED_CONFIRMATION = "GENERATE-FROZEN-FUTURE-REVIEW-QUEUE-V1"

EXPECTED_COMMIT_PATHS = {'experiments/07_comparative_landscape/PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_AUTHORIZATION.md', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_generation_authorization.sha256', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_generation_authorization_freeze.py', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_generation_authorization_design.json', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_generation_authorization.json'}


def sha(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def git(*args):
    return subprocess.check_output(
        ["git", *args],
        text=True,
    ).strip()


def repository_position():
    head = git(
        "rev-parse",
        "HEAD",
    )

    if head == EXPECTED_PARENT:
        return "PRE_COMMIT_PARENT"

    if git(
        "rev-parse",
        "HEAD^",
    ) != EXPECTED_PARENT:
        raise RuntimeError(
            "Unexpected generation-authorization repository position"
        )

    changed = set(
        line
        for line in git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).splitlines()
        if line
    )

    if changed != EXPECTED_COMMIT_PATHS:
        raise RuntimeError(
            "Generation-authorization commit path set differs"
        )

    return "COMMITTED_FREEZE"


def validate():
    position = repository_position()

    if sha(
        IMPL_SUMS
    ) != EXPECTED_IMPL_SUMS_SHA:
        raise RuntimeError(
            "Queue implementation identity changed"
        )

    if sha(
        QUEUE_DESIGN_SUMS
    ) != EXPECTED_QUEUE_DESIGN_SUMS_SHA:
        raise RuntimeError(
            "Queue design identity changed"
        )

    if sha(
        SCORING_RESULTS_SUMS
    ) != EXPECTED_SCORING_RESULTS_SUMS_SHA:
        raise RuntimeError(
            "Scoring-result identity changed"
        )

    if sha(
        AUTH
    ) != EXPECTED_AUTH_SHA:
        raise RuntimeError(
            "Generation authorization payload changed"
        )

    if sha(
        DESIGN
    ) != EXPECTED_DESIGN_SHA:
        raise RuntimeError(
            "Generation authorization design changed"
        )

    if sha(
        DOC
    ) != EXPECTED_DOC_SHA:
        raise RuntimeError(
            "Generation authorization document changed"
        )

    value = json.loads(
        AUTH.read_text(
            encoding="utf-8"
        )
    )

    expected = {
        "schema_version":
            1,

        "status":
            "AUTHORIZED_ONE_USE",

        "authorization_id":
            "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_001",

        "generation_authorized":
            True,

        "one_use":
            True,

        "design_checksum_manifest_sha256":
            EXPECTED_QUEUE_DESIGN_SUMS_SHA,

        "expected_priority_scored_rows":
            5483,

        "expected_residual_scored_rows":
            6422,

        "expected_unscored_manual_review_rows":
            257,

        "expected_total_human_review_rows":
            12162,

        "output_root":
            "results/07_comparative_landscape/"
            "pre_review_triage_future_review_queue_v1",

        "scientific_decision_authorized":
            False,

        "blind_validation_content_use_authorized":
            False,

        "future_label_use_authorized":
            False,

        "confirmation":
            EXPECTED_CONFIRMATION,
    }

    if value != expected:
        raise RuntimeError(
            "Generation authorization semantics changed"
        )

    design = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if design[
        "status"
    ] != "FROZEN_ONE_USE_GENERATION_AUTHORIZATION_PRE_EXECUTION":
        raise RuntimeError(
            "Generation authorization status changed"
        )

    if design[
        "freeze_parent_commit"
    ] != EXPECTED_PARENT:
        raise RuntimeError(
            "Generation authorization parent changed"
        )

    if design[
        "implementation_checksum_manifest_sha256"
    ] != EXPECTED_IMPL_SUMS_SHA:
        raise RuntimeError(
            "Generation authorization implementation binding changed"
        )

    if OUTROOT.exists():
        raise RuntimeError(
            "Queue output exists before generation"
        )

    for line in SUMS.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        digest, rel = line.split(
            "  ",
            1,
        )

        if sha(
            Path(rel)
        ) != digest:
            raise RuntimeError(
                "Generation authorization checksum mismatch: "
                + rel
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | exact one-use queue-generation authorization validates"
    )

    print(
        "PASS | exact frozen implementation identity bound"
    )

    print(
        "PASS | 5,483 + 6,422 + 257 generation authority"
    )

    print(
        "PASS | scientific-decision/blind/future-label authority remains false"
    )

    print(
        "PASS | canonical queue output remains absent"
    )


if __name__ == "__main__":
    validate()
