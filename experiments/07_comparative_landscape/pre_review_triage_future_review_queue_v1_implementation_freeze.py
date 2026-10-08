from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path("experiments/07_comparative_landscape")

RESULTS = Path(
    "results/07_comparative_landscape"
)

EXPECTED_PARENT = "6ae258b80df39eca49ea58ce5ba8237eed10fea7"

BUILDER = ROOT / "pre_review_triage_future_review_queue_v1.py"
TEST = ROOT / "test_pre_review_triage_future_review_queue_v1.py"
HOSTILE = ROOT / "test_pre_review_triage_future_review_queue_hostile_v1.py"

FREEZE = ROOT / "pre_review_triage_future_review_queue_v1_implementation_freeze.py"
DESIGN = ROOT / "pre_review_triage_future_review_queue_v1_implementation_design.json"
DOC = ROOT / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_IMPLEMENTATION.md"
SUMS = ROOT / "pre_review_triage_future_review_queue_v1_implementation.sha256"

QUEUE_DESIGN_SUMS = ROOT / "pre_review_triage_future_review_queue_v1_design.sha256"
SCORING_RESULTS_SUMS = ROOT / "pre_review_triage_future_scoring_results_v1.sha256"

OUTROOT = RESULTS / "pre_review_triage_future_review_queue_v1"

AUTH = (
    ROOT
    / "pre_review_triage_future_review_queue_v1_generation_authorization.json"
)

EXPECTED_QUEUE_DESIGN_SUMS_SHA = "319ce18f144b97acc1d6c5b277420bd7b9f66fce0e99b2b8207a657559ea1e26"
EXPECTED_SCORING_RESULTS_SUMS_SHA = "8be5645fb71f557306be11ae132f1d655013d6a6d573beb50380399cad9bc939"

EXPECTED_HASHES = {
    str(BUILDER): "795f7ae9bb72262f5568feec5dcd2ad23c2cf7dfa7c3f09181d82f845261bfa9",
    str(TEST): "b457921b7ab05eda1b9ac2c72dda907411b729f4bdfdde7cf028295ff59f690e",
    str(HOSTILE): "ef5862c011f44bcd8cd4b999b92071321cc7d4c6242f8f0dd30ace3cdf98bfaa",
    str(DESIGN): "1d2319d9999c573fbdbeafad8841d99a2d5a63daf163555fe1b34dc9da48bb00",
    str(DOC): "ad80ecb35a29d268a92c69a70b5e97a50ef8f15139f2636f9550ee539ae4ccd0",
}

EXPECTED_COMMIT_PATHS = {'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1.py', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_implementation_freeze.py', 'experiments/07_comparative_landscape/test_pre_review_triage_future_review_queue_v1.py', 'experiments/07_comparative_landscape/PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_IMPLEMENTATION.md', 'experiments/07_comparative_landscape/test_pre_review_triage_future_review_queue_hostile_v1.py', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_implementation_design.json', 'experiments/07_comparative_landscape/pre_review_triage_future_review_queue_v1_implementation.sha256'}


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
            "Unexpected queue-implementation repository position"
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
            "Queue-implementation commit path set differs"
        )

    return "COMMITTED_FREEZE"


def validate():
    position = repository_position()

    if sha(
        QUEUE_DESIGN_SUMS
    ) != EXPECTED_QUEUE_DESIGN_SUMS_SHA:
        raise RuntimeError(
            "Queue-design identity changed"
        )

    if sha(
        SCORING_RESULTS_SUMS
    ) != EXPECTED_SCORING_RESULTS_SUMS_SHA:
        raise RuntimeError(
            "Scoring-result identity changed"
        )

    for name, expected in EXPECTED_HASHES.items():
        if sha(Path(name)) != expected:
            raise RuntimeError(
                "Frozen queue implementation changed: "
                + name
            )

    value = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if value["status"] != (
        "FROZEN_IMPLEMENTATION_PRE_GENERATION_AUTHORIZATION"
    ):
        raise RuntimeError(
            "Queue implementation status changed"
        )

    if value["freeze_parent_commit"] != EXPECTED_PARENT:
        raise RuntimeError(
            "Queue implementation parent changed"
        )

    if value["queue_contract"]["priority_scored_rows"] != 5483:
        raise RuntimeError(
            "Priority count changed"
        )

    if value["queue_contract"]["residual_scored_rows"] != 6422:
        raise RuntimeError(
            "Residual count changed"
        )

    if value["queue_contract"]["unscored_manual_review_rows"] != 257:
        raise RuntimeError(
            "Manual-review count changed"
        )

    if value["validation_evidence"]["total_test_count"] != 20:
        raise RuntimeError(
            "Test-count contract changed"
        )

    if value["generation_boundary"]["generation_authorized"] is not False:
        raise RuntimeError(
            "Generation unexpectedly authorized"
        )

    if value["generation_boundary"]["queue_generated"] is not False:
        raise RuntimeError(
            "Queue unexpectedly recorded generated"
        )

    if AUTH.exists():
        raise RuntimeError(
            "Generation authorization exists before next gate"
        )

    if OUTROOT.exists():
        raise RuntimeError(
            "Canonical queue output exists before authorization"
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
                "Queue implementation checksum mismatch: "
                + rel
            )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | future review-queue implementation freeze validates"
    )

    print(
        "PASS | 5,483 + 6,422 + 257 lane contract exact"
    )

    print(
        "PASS | 20-test validation bound"
    )

    print(
        "PASS | generation remains unauthorized and unperformed"
    )

    print(
        "PASS | no scientific decision authority"
    )


if __name__ == "__main__":
    validate()
