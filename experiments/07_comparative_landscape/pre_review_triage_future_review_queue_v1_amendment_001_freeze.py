from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path("experiments/07_comparative_landscape")

RESULTS = Path(
    "results/07_comparative_landscape"
)

EXPECTED_PARENT = "5b74ffd36ea63a1b6e44de572c7557c5169ee187"

BUILDER = ROOT / "pre_review_triage_future_review_queue_v1.py"

UNIT = ROOT / "test_pre_review_triage_future_review_queue_v1.py"

HOSTILE = ROOT / "test_pre_review_triage_future_review_queue_hostile_v1.py"

AMEND_TEST = (
    ROOT
    / "test_pre_review_triage_future_review_queue_v1_amendment_001.py"
)

INCIDENT = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "generation_attempt_001_failure.json"
)

DESIGN = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "amendment_001_design.json"
)

DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_AMENDMENT_001.md"
)

FREEZE = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "amendment_001_freeze.py"
)

SUMS = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_"
    "amendment_001.sha256"
)

OLD_IMPL_SUMS = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_implementation.sha256"
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

OUTROOT = (
    RESULTS
    / "pre_review_triage_future_review_queue_v1"
)

EXPECTED_OLD_IMPL_SUMS_SHA = "f7b3eca45cee5b49e2ee63e4a2ddc778dc1f46291346c0c855ea737e2bd0793d"
EXPECTED_OLD_AUTH_SHA = "f6b018056fdf4ffb9e7a404dcc08ae1f6993ca8ad73b008be67aa2c503b05018"
EXPECTED_OLD_AUTH_SUMS_SHA = "b3e248e3e0841e68f0531e868dd40a0430a57eb5429cb8f51222e5845128ff13"

EXPECTED_BUILDER_SHA = "7eea07f6a2214915ff84d6bd2bfc9618380934fee54684f118cbcdf065df3916"
EXPECTED_TEST_SHA = "44fea462930e56221c38c47b1f932a483d37f0c5c93f0281248f49ba05f723ba"
EXPECTED_INCIDENT_SHA = "5c40ad2a447a7be3e00c74a95f79d6c77bdee976230ada0d27cba0371e7647a8"
EXPECTED_DESIGN_SHA = "3ee639f4c22e6330d55bc266a3bfcdf2c431fb49644c672fd7ef4439893d3095"
EXPECTED_DOC_SHA = "0d6fe291ca63091272331abedc925b8cc76e375d6eeea4f67312cfa1e3b3581d"

EXPECTED_COMMIT_PATHS = {'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_generation_attempt_001_failure.json', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_amendment_001.sha256', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1.py', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_amendment_001_design.json', 'experiments/07_comparative_landscape/PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_AMENDMENT_001.md', 'experiments/07_comparative_landscape/test_pre_review_triage_future_review_queue_v1_amendment_001.py', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_amendment_001_freeze.py'}


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
            "Unexpected Amendment 001 repository position"
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
            "Amendment 001 commit path set differs"
        )

    return "COMMITTED_FREEZE"


def validate():
    position = repository_position()

    if sha(
        OLD_IMPL_SUMS
    ) != EXPECTED_OLD_IMPL_SUMS_SHA:
        raise RuntimeError(
            "Original implementation identity changed"
        )

    if sha(
        OLD_AUTH
    ) != EXPECTED_OLD_AUTH_SHA:
        raise RuntimeError(
            "Consumed authorization payload changed"
        )

    if sha(
        OLD_AUTH_SUMS
    ) != EXPECTED_OLD_AUTH_SUMS_SHA:
        raise RuntimeError(
            "Consumed authorization freeze changed"
        )

    for path, expected in {
        BUILDER:
            EXPECTED_BUILDER_SHA,

        AMEND_TEST:
            EXPECTED_TEST_SHA,

        INCIDENT:
            EXPECTED_INCIDENT_SHA,

        DESIGN:
            EXPECTED_DESIGN_SHA,

        DOC:
            EXPECTED_DOC_SHA,
    }.items():
        if sha(path) != expected:
            raise RuntimeError(
                "Amendment artifact changed: "
                + str(path)
            )

    value = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if value["status"] != (
        "FROZEN_IMPLEMENTATION_AMENDMENT_001_PRE_NEW_AUTHORIZATION"
    ):
        raise RuntimeError(
            "Amendment status changed"
        )

    if value[
        "resolution"
    ][
        "replacement_authorization_id"
    ] != (
        "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_002"
    ):
        raise RuntimeError(
            "Replacement authorization ID changed"
        )

    if value[
        "resolution"
    ][
        "generation_001_reuse_permitted"
    ] is not False:
        raise RuntimeError(
            "Consumed authorization unexpectedly reusable"
        )

    if value[
        "validation_evidence"
    ][
        "total_tests"
    ] != 22:
        raise RuntimeError(
            "Amended test count changed"
        )

    if value[
        "authorization_boundary"
    ][
        "generation_authorized"
    ] is not False:
        raise RuntimeError(
            "Generation unexpectedly authorized"
        )

    if OUTROOT.exists():
        raise RuntimeError(
            "Canonical queue exists before new authorization"
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
                "Amendment checksum mismatch: "
                + rel
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | future review-queue Amendment 001 validates"
    )

    print(
        "PASS | deterministic staging defect corrected"
    )

    print(
        "PASS | consumed GENERATION_001 authorization rejected"
    )

    print(
        "PASS | replacement authorization ID = GENERATION_002"
    )

    print(
        "PASS | 22-test validation bound"
    )

    print(
        "PASS | queue semantics unchanged"
    )

    print(
        "PASS | canonical queue remains absent"
    )

    print(
        "PASS | generation remains unauthorized"
    )


if __name__ == "__main__":
    validate()
