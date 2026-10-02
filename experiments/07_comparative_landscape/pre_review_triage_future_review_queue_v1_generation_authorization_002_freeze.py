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

EXPECTED_PARENT = "08632ef628ef5eacdd965e8ce17f42f44b50e4e4"

AUTH = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "generation_authorization_002.json"
)

FREEZE = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "generation_authorization_002_freeze.py"
)

DESIGN = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "generation_authorization_002_design.json"
)

DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_"
    "GENERATION_AUTHORIZATION_002.md"
)

SUMS = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "generation_authorization_002.sha256"
)

AMEND_SUMS = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "amendment_001.sha256"
)

BUILDER = (
    ROOT
    / "pre_review_triage_future_review_queue_v1.py"
)

OLD_AUTH = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "generation_authorization.json"
)

OLD_AUTH_SUMS = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "generation_authorization.sha256"
)

EXPECTED_AMEND_SUMS_SHA = "5b75eb743aaf7d4cdbbad54275b21344652e321f2dd1c7880fd37e3a21bc7de2"
EXPECTED_BUILDER_SHA = "7eea07f6a2214915ff84d6bd2bfc9618380934fee54684f118cbcdf065df3916"
EXPECTED_QUEUE_DESIGN_SUMS_SHA = "319ce18f144b97acc1d6c5b277420bd7b9f66fce0e99b2b8207a657559ea1e26"
EXPECTED_SCORING_RESULTS_SUMS_SHA = "8be5645fb71f557306be11ae132f1d655013d6a6d573beb50380399cad9bc939"
EXPECTED_OLD_AUTH_SHA = "f6b018056fdf4ffb9e7a404dcc08ae1f6993ca8ad73b008be67aa2c503b05018"
EXPECTED_OLD_AUTH_SUMS_SHA = "b3e248e3e0841e68f0531e868dd40a0430a57eb5429cb8f51222e5845128ff13"

EXPECTED_AUTH_SHA = "6f9e37e10bcab07ee7d22d3ff52b64cf474f48b373c07c3fddbcfdea780fa9ab"
EXPECTED_DESIGN_SHA = "576e2f7bc680a0d70171fea160433af51e81b40c4b67e509de933d4691eb8e87"
EXPECTED_DOC_SHA = "0f28e8dc60b406ffc1e986e373b9d2f17f250b9ffeadcdcd95e1670e92b63cfc"

EXPECTED_CONFIRMATION = "GENERATE-FROZEN-FUTURE-REVIEW-QUEUE-V1"

EXPECTED_COMMIT_PATHS = {'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_generation_authorization_002.json', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_generation_authorization_002_freeze.py', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_generation_authorization_002.sha256', 'experiments/07_comparative_landscape/PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_AUTHORIZATION_002.md', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_generation_authorization_002_design.json'}


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
            "Unexpected GENERATION_002 authorization repository position"
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
            "GENERATION_002 authorization commit path set differs"
        )

    return "COMMITTED_FREEZE"


def validate():
    position = repository_position()

    for path, expected in {
        AMEND_SUMS:
            EXPECTED_AMEND_SUMS_SHA,

        BUILDER:
            EXPECTED_BUILDER_SHA,

        OLD_AUTH:
            EXPECTED_OLD_AUTH_SHA,

        OLD_AUTH_SUMS:
            EXPECTED_OLD_AUTH_SUMS_SHA,

        AUTH:
            EXPECTED_AUTH_SHA,

        DESIGN:
            EXPECTED_DESIGN_SHA,

        DOC:
            EXPECTED_DOC_SHA,
    }.items():

        if sha(path) != expected:
            raise RuntimeError(
                "GENERATION_002 bound identity changed: "
                + str(path)
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
            "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_002",

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
            "GENERATION_002 authorization semantics changed"
        )

    design = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if design[
        "status"
    ] != (
        "FROZEN_ONE_USE_GENERATION_AUTHORIZATION_002_PRE_EXECUTION"
    ):
        raise RuntimeError(
            "GENERATION_002 authorization status changed"
        )

    if design[
        "freeze_parent_commit"
    ] != EXPECTED_PARENT:
        raise RuntimeError(
            "GENERATION_002 parent changed"
        )

    if design[
        "consumed_generation_001"
    ][
        "consumed"
    ] is not True:
        raise RuntimeError(
            "GENERATION_001 consumption lost"
        )

    if design[
        "consumed_generation_001"
    ][
        "reuse_permitted"
    ] is not False:
        raise RuntimeError(
            "GENERATION_001 unexpectedly reusable"
        )

    if OUTROOT.exists():
        raise RuntimeError(
            "Canonical queue exists before GENERATION_002 execution"
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
                "GENERATION_002 authorization checksum mismatch: "
                + rel
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | exact one-use GENERATION_002 authorization validates"
    )

    print(
        "PASS | Amendment 001 identity bound"
    )

    print(
        "PASS | amended builder identity bound"
    )

    print(
        "PASS | GENERATION_001 remains consumed and non-reusable"
    )

    print(
        "PASS | 5,483 + 6,422 + 257 replacement generation authority"
    )

    print(
        "PASS | scientific-decision/blind/future-label authority remains false"
    )

    print(
        "PASS | canonical queue output remains absent"
    )


if __name__ == "__main__":
    validate()
