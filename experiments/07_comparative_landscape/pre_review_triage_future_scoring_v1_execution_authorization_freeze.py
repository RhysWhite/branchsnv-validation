from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path("experiments/07_comparative_landscape")

OUTROOT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_scoring_v1"
)

EXPECTED_PARENT = "e9bb1f8aaa46f6039180bc2f100c6eeafe86c4cd"

AUTH = ROOT / "pre_review_triage_future_scoring_v1_execution_authorization.json"
FREEZE = ROOT / "pre_review_triage_future_scoring_v1_execution_authorization_freeze.py"
DESIGN = ROOT / "pre_review_triage_future_scoring_v1_execution_authorization_design.json"
DOC = ROOT / "PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_EXECUTION_AUTHORIZATION.md"
SUMS = ROOT / "pre_review_triage_future_scoring_v1_execution_authorization.sha256"

IMPL_SUMS = ROOT / "pre_review_triage_future_scoring_v1_implementation.sha256"

EXPECTED_IMPL_SUMS_SHA = "fc3110e70c0454d69743dd4371e41396644a784fca58d2230152efec01c49684"
EXPECTED_AUTH_SHA = "fea574377efe9a2c6fa8acb38face7da13f133dc0ace889b5c039d2c2131b3dc"
EXPECTED_DESIGN_SHA = "347053cab848dbd309a0472b9ecbe07ad8e747a30d82542d2ca8f254f28cf2a7"
EXPECTED_DOC_SHA = "d4af640fcfb37fe1cb04b056896fae0364df5c14cb8daee1dc5690a6b7193b30"

EXPECTED_COMMIT_PATHS = {'experiments/07_comparative_landscape/pre_review_triage_future_scoring_v1_execution_authorization_freeze.py', 'experiments/07_comparative_landscape/PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_EXECUTION_AUTHORIZATION.md', 'experiments/07_comparative_landscape/pre_review_triage_future_scoring_v1_execution_authorization_design.json', 'experiments/07_comparative_landscape/pre_review_triage_future_scoring_v1_execution_authorization.json', 'experiments/07_comparative_landscape/pre_review_triage_future_scoring_v1_execution_authorization.sha256'}

EXPECTED_CONFIRMATION = "EXECUTE-FROZEN-FUTURE-SCORING-V1"


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
            "Unexpected authorization repository position"
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
            "Authorization commit path set differs"
        )

    return "COMMITTED_FREEZE"


def validate():
    position = repository_position()

    if sha(
        IMPL_SUMS
    ) != EXPECTED_IMPL_SUMS_SHA:
        raise RuntimeError(
            "Implementation-freeze identity changed"
        )

    if sha(
        AUTH
    ) != EXPECTED_AUTH_SHA:
        raise RuntimeError(
            "Authorization payload changed"
        )

    if sha(
        DESIGN
    ) != EXPECTED_DESIGN_SHA:
        raise RuntimeError(
            "Authorization design changed"
        )

    if sha(
        DOC
    ) != EXPECTED_DOC_SHA:
        raise RuntimeError(
            "Authorization document changed"
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
            "PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_EXECUTION_001",

        "future_scoring_authorized":
            True,

        "final_deployment_fit_authorized":
            True,

        "one_use":
            True,

        "consumed_before_execution":
            False,

        "blind_validation_content_use_authorized":
            False,

        "threshold_selection_authorized":
            False,

        "hard_prediction_authorized":
            False,

        "probability_calibration_authorized":
            False,

        "selected_candidate_id":
            "linear_svc_balanced_l2_v1",

        "design_checksum_manifest_sha256":
            "f5c3548c370af87c5964a3eff1db590d0800d7b5655bf9076fee0d757d52eaba",

        "design_amendment_001_checksum_manifest_sha256":
            "a81a90797ae05db3c8139cdade02069fc722d9abb7f815df2619f39f29e317c2",

        "reconciliation_completion_sha256":
            "0798d80b10c6fa4beb53cf1074bef959283c2cb0ef2e2be998c6ead4bbc048b1",

        "implementation_freeze_sha256":
            EXPECTED_IMPL_SUMS_SHA,

        "expected_development_rows":
            4190,

        "expected_development_positive_rows":
            168,

        "expected_future_scored_rows":
            11905,

        "expected_future_coverage_rows":
            12162,

        "output_root":
            str(
                OUTROOT
            ),

        "confirmation":
            EXPECTED_CONFIRMATION,
    }

    if value != expected:
        raise RuntimeError(
            "Authorization semantics changed"
        )

    design = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if design[
        "status"
    ] != "FROZEN_ONE_USE_AUTHORIZATION_PRE_EXECUTION":
        raise RuntimeError(
            "Authorization design status changed"
        )

    if design[
        "freeze_parent_commit"
    ] != EXPECTED_PARENT:
        raise RuntimeError(
            "Authorization parent changed"
        )

    if OUTROOT.exists():
        raise RuntimeError(
            "Future-scoring output exists before execution"
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
            Path(
                rel
            )
        ) != digest:
            raise RuntimeError(
                "Authorization checksum mismatch: "
                + rel
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | exact one-use future-scoring authorization validates"
    )

    print(
        "PASS | implementation identity exact"
    )

    print(
        "PASS | fit + continuous future scoring authorized"
    )

    print(
        "PASS | threshold/hard-prediction/blind authority remains false"
    )

    print(
        "PASS | canonical future-scoring output remains absent"
    )


if __name__ == "__main__":
    validate()
