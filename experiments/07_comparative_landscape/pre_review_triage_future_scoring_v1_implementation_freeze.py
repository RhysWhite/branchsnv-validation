from pathlib import Path
import ast
import hashlib
import json
import subprocess

ROOT = Path("experiments/07_comparative_landscape")

EXPECTED_PARENT = "f878fb6ed95ab11fbd52c66ea4753dd0aeefc969"

SCORER = ROOT / "pre_review_triage_future_scoring_v1.py"
TEST = ROOT / "test_pre_review_triage_future_scoring_v1.py"
HOSTILE = ROOT / "test_pre_review_triage_future_scoring_hostile_v1.py"

FREEZE = ROOT / "pre_review_triage_future_scoring_v1_implementation_freeze.py"
DESIGN = ROOT / "pre_review_triage_future_scoring_v1_implementation_design.json"
DOC = ROOT / "PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_IMPLEMENTATION.md"
SUMS = ROOT / "pre_review_triage_future_scoring_v1_implementation.sha256"

ORIG_SUMS = ROOT / "pre_review_triage_future_scoring_v1_design.sha256"
AMEND_SUMS = ROOT / "pre_review_triage_future_scoring_v1_design_amendment_001.sha256"

AUTH = ROOT / "pre_review_triage_future_scoring_v1_execution_authorization.json"

OUTROOT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_scoring_v1"
)

EXPECTED_DESIGN_SUMS_SHA = "f5c3548c370af87c5964a3eff1db590d0800d7b5655bf9076fee0d757d52eaba"
EXPECTED_AMEND_SUMS_SHA = "a81a90797ae05db3c8139cdade02069fc722d9abb7f815df2619f39f29e317c2"

EXPECTED_HASHES = {
    str(SCORER): "c25325097c4ea2d18e6a1bd2586af8a5fcd26b08fc4c470b476db0410f6d3a13",
    str(TEST): "f53ba41ba62aca6c70c1408b659afab7a5b8cbcb6199810ecbabd0de947ea807",
    str(HOSTILE): "eb30c66c445a2b68681664127135e9f0da1b0ffcf6dbbdc27d0083cc5655ef1e",
    str(DESIGN): "71acd7ea1d42c724868baf9017165aac07488dd14c47719764b099fca5dd9785",
    str(DOC): "d2526c6e72d843086a962835506fc3e94f4ba0d9a51df9c8d4d41a46e60115c6",
}

EXPECTED_COMMIT_PATHS = {'experiments/07_comparative_landscape/test_pre_review_triage_future_scoring_v1.py', 'experiments/07_comparative_landscape/pre_review_triage_future_scoring_v1_implementation_design.json', 'experiments/07_comparative_landscape/test_pre_review_triage_future_scoring_hostile_v1.py', 'experiments/07_comparative_landscape/pre_review_triage_future_scoring_v1_implementation_freeze.py', 'experiments/07_comparative_landscape/PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_IMPLEMENTATION.md', 'experiments/07_comparative_landscape/pre_review_triage_future_scoring_v1.py', 'experiments/07_comparative_landscape/pre_review_triage_future_scoring_v1_implementation.sha256'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(
        ["git", *args],
        text=True,
    ).strip()


def repository_position():
    head = git("rev-parse", "HEAD")

    if head == EXPECTED_PARENT:
        return "PRE_COMMIT_PARENT"

    if git("rev-parse", "HEAD^") != EXPECTED_PARENT:
        raise RuntimeError(
            "Unexpected implementation-freeze repository position"
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
            "Implementation-freeze commit path set differs"
        )

    return "COMMITTED_FREEZE"


def validate():
    position = repository_position()

    if sha(ORIG_SUMS) != EXPECTED_DESIGN_SUMS_SHA:
        raise RuntimeError("Original design identity changed")

    if sha(AMEND_SUMS) != EXPECTED_AMEND_SUMS_SHA:
        raise RuntimeError("Design-amendment identity changed")

    for name, expected in EXPECTED_HASHES.items():
        if sha(Path(name)) != expected:
            raise RuntimeError(
                "Frozen implementation hash changed: " + name
            )

    value = json.loads(
        DESIGN.read_text(encoding="utf-8")
    )

    if value["status"] != "FROZEN_IMPLEMENTATION_PRE_AUTHORIZATION":
        raise RuntimeError("Implementation status changed")

    if value["freeze_parent_commit"] != EXPECTED_PARENT:
        raise RuntimeError("Implementation parent changed")

    if value["selected_candidate"]["candidate_id"] != (
        "linear_svc_balanced_l2_v1"
    ):
        raise RuntimeError("Selected model family changed")

    if value["model_contract"]["tfidf"]["dtype"] != "numpy.float64":
        raise RuntimeError("TF-IDF dtype changed")

    if value["validation_evidence"]["total_test_count"] != 21:
        raise RuntimeError("Test-count contract changed")

    if value["execution_boundary"]["model_fit_performed"] is not False:
        raise RuntimeError("Model fit unexpectedly recorded")

    if value["execution_boundary"]["future_scoring_performed"] is not False:
        raise RuntimeError("Future scoring unexpectedly recorded")

    if value["execution_boundary"]["threshold_selection_performed"] is not False:
        raise RuntimeError("Threshold unexpectedly selected")

    if value["execution_boundary"]["blind_validation_content_used"] is not False:
        raise RuntimeError("Blind-validation boundary changed")

    if AUTH.exists():
        raise RuntimeError(
            "Execution authorization exists before authorization gate"
        )

    if OUTROOT.exists():
        raise RuntimeError(
            "Future-scoring production output exists before authorization"
        )

    for line in SUMS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        digest, rel = line.split("  ", 1)

        if sha(Path(rel)) != digest:
            raise RuntimeError(
                "Implementation checksum mismatch: " + rel
            )

    print("PASS | repository position =", position)
    print("PASS | future scoring implementation freeze validates")
    print("PASS | exact frozen runtime bound")
    print("PASS | exact evaluator constructors bound")
    print("PASS | 21-test validation bound")
    print("PASS | no real fit, future scoring or unblinding")


if __name__ == "__main__":
    validate()
