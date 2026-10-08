from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path("experiments/07_comparative_landscape")
SROOT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_scoring_v1"
)

EXPECTED_PARENT = "1ca9f45403c329efd6fc857886894df1a955ac50"

ORIG_DESIGN = ROOT / "pre_review_triage_future_scoring_v1_design.json"
ORIG_DOC = ROOT / "PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_DESIGN.md"
ORIG_SUMS = ROOT / "pre_review_triage_future_scoring_v1_design.sha256"

DESIGN = ROOT / "pre_review_triage_future_scoring_v1_design_amendment_001.json"
DOC = ROOT / "PRE_REVIEW_TRIAGE_FUTURE_SCORING_V1_DESIGN_AMENDMENT_001.md"
FREEZE = ROOT / "pre_review_triage_future_scoring_v1_design_amendment_001_freeze.py"
SUMS = ROOT / "pre_review_triage_future_scoring_v1_design_amendment_001.sha256"

EXPECTED_ORIG_DESIGN_SHA = "9809d5811123062c1580ec44a49c63b54bfcef45d9fe4a4aa1f86f6b6d183a03"
EXPECTED_ORIG_DOC_SHA = "ffaa0b9a343ce894e4b193a7dcdffc45063cda526f4a3e06b190d47f57b3d23a"
EXPECTED_ORIG_SUMS_SHA = "f5c3548c370af87c5964a3eff1db590d0800d7b5655bf9076fee0d757d52eaba"

EXPECTED_COMMIT_PATHS = {
    str(DESIGN),
    str(DOC),
    str(FREEZE),
    str(SUMS),
}

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
        raise RuntimeError("Unexpected amendment repository position")

    changed = set(
        x for x in git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).splitlines()
        if x
    )

    if changed != EXPECTED_COMMIT_PATHS:
        raise RuntimeError("Amendment commit path set differs")

    return "COMMITTED_FREEZE"

def validate():
    position = repository_position()

    if sha(ORIG_DESIGN) != EXPECTED_ORIG_DESIGN_SHA:
        raise RuntimeError("Original design SHA changed")

    if sha(ORIG_DOC) != EXPECTED_ORIG_DOC_SHA:
        raise RuntimeError("Original design document SHA changed")

    if sha(ORIG_SUMS) != EXPECTED_ORIG_SUMS_SHA:
        raise RuntimeError("Original design checksum SHA changed")

    value = json.loads(DESIGN.read_text(encoding="utf-8"))

    if value["status"] != "FROZEN_PRE_IMPLEMENTATION_AMENDMENT":
        raise RuntimeError("Amendment status changed")

    if value["design_parent_commit"] != EXPECTED_PARENT:
        raise RuntimeError("Amendment parent changed")

    corrected = value["corrected_scoring_contract"]

    if corrected["selected_candidate_family"] != "linear_svc_balanced_l2_v1":
        raise RuntimeError("Selected family changed")

    if corrected["future_output_type"] != "continuous_score_only":
        raise RuntimeError("Future output is not continuous-score-only")

    if corrected["hard_prediction_output_permitted"] is not False:
        raise RuntimeError("Hard prediction unexpectedly permitted")

    if corrected["raw_score_threshold_exists"] is not False:
        raise RuntimeError("A threshold was unexpectedly introduced")

    fit = value["final_deployment_fit_contract"]

    if fit["training_record_count"] != 4190:
        raise RuntimeError("Development fit population changed")

    if fit["positive_record_count"] != 168:
        raise RuntimeError("Development positive count changed")

    if fit["future_text_may_enter_fit"] is not False:
        raise RuntimeError("Future text unexpectedly permitted in fit")

    if fit["future_labels_may_enter_fit"] is not False:
        raise RuntimeError("Future labels unexpectedly permitted in fit")

    if SROOT.exists():
        raise RuntimeError("Future scoring output exists before implementation")

    lines = [
        line.strip()
        for line in SUMS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    for line in lines:
        digest, rel = line.split("  ", 1)
        path = Path(rel)
        if sha(path) != digest:
            raise RuntimeError("Checksum mismatch: " + rel)

    print("PASS | repository position =", position)
    print("PASS | future scoring design amendment 001 validates")
    print("PASS | no future scoring output exists")

if __name__ == "__main__":
    validate()
