from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path("experiments/07_comparative_landscape")

OUTROOT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_scoring_v1"
)

EXPECTED_PARENT = "5c3b636275d02e520d264478a5c11e6c5f1c72de"

FREEZE = ROOT / "pre_review_triage_future_scoring_results_v1_freeze.py"
DESIGN = ROOT / "pre_review_triage_future_scoring_results_v1_design.json"
DOC = ROOT / "PRE_REVIEW_TRIAGE_FUTURE_SCORING_RESULTS_V1.md"
SUMS = ROOT / "pre_review_triage_future_scoring_results_v1.sha256"

AUTH_SUMS = ROOT / "pre_review_triage_future_scoring_v1_execution_authorization.sha256"
IMPL_SUMS = ROOT / "pre_review_triage_future_scoring_v1_implementation.sha256"

SCORED = OUTROOT / "scored_records.tsv"
COVERAGE = OUTROOT / "coverage.tsv"
MANIFEST = OUTROOT / "execution_manifest.json"
OUTPUT_SUMS = OUTROOT / "checksums.sha256"
COMPLETION = OUTROOT / "execution_completion.json"

EXPECTED_AUTH_SUMS = "a32082da4ffb29eccfbb5df080ccb13b4be9577cbe596a2a9c9bc307879628da"
EXPECTED_IMPL_SUMS = "fc3110e70c0454d69743dd4371e41396644a784fca58d2230152efec01c49684"

EXPECTED_OUTPUTS = {'results/07_comparative_landscape/pre_review_triage_future_scoring_v1/scored_records.tsv': '70164b0e345d2df0e0fa0c765a293e725096ef50096c6bb1025ed72ca06f7d67', 'results/07_comparative_landscape/pre_review_triage_future_scoring_v1/coverage.tsv': '8dde17ef13648cfee4bbec80322377202eb769cd11e5f3249d59de978e3824b7', 'results/07_comparative_landscape/pre_review_triage_future_scoring_v1/execution_manifest.json': '49088e8648f2437da5d6766f6098461173a5230b9726ff081d0bd50e0282ed1f', 'results/07_comparative_landscape/pre_review_triage_future_scoring_v1/checksums.sha256': '6261fd2c8bd7dc324f7020cf2ddf7f3a74ab5289dfa1252eb0ea66eb1b9f0afc', 'results/07_comparative_landscape/pre_review_triage_future_scoring_v1/execution_completion.json': '7fb99ca772bfda6a391a36e094d0063ad9ec0f7cf8b51c4fcb2c884bbe870470'}

EXPECTED_DESIGN_SHA = "0324fb1ec8d92f086ff56ca4276da239188aac3c159aa0a51525c83dc9b91bf5"
EXPECTED_DOC_SHA = "274fb74f2d407ce132f567e95cd0e20fb15b418a53cbdac93a47831a34ffc862"

EXPECTED_COMMIT_PATHS = {'results/07_comparative_landscape/pre_review_triage_future_scoring_v1/checksums.sha256', 'results/07_comparative_landscape/pre_review_triage_future_scoring_v1/coverage.tsv', 'results/07_comparative_landscape/pre_review_triage_future_scoring_v1/scored_records.tsv', 'experiments/07_comparative_landscape/PRE_REVIEW_TRIAGE_FUTURE_SCORING_RESULTS_V1.md', 'experiments/07_comparative_landscape/pre_review_triage_future_scoring_results_v1_design.json', 'experiments/07_comparative_landscape/pre_review_triage_future_scoring_results_v1.sha256', 'results/07_comparative_landscape/pre_review_triage_future_scoring_v1/execution_completion.json', 'results/07_comparative_landscape/pre_review_triage_future_scoring_v1/execution_manifest.json', 'experiments/07_comparative_landscape/pre_review_triage_future_scoring_results_v1_freeze.py'}


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
    head = git("rev-parse", "HEAD")

    if head == EXPECTED_PARENT:
        return "PRE_COMMIT_PARENT"

    if git("rev-parse", "HEAD^") != EXPECTED_PARENT:
        raise RuntimeError(
            "Unexpected result-freeze repository position"
        )

    changed = set(
        x
        for x in git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).splitlines()
        if x
    )

    if changed != EXPECTED_COMMIT_PATHS:
        raise RuntimeError(
            "Result-freeze commit path set differs"
        )

    return "COMMITTED_FREEZE"


def validate():
    position = repository_position()

    if sha(AUTH_SUMS) != EXPECTED_AUTH_SUMS:
        raise RuntimeError(
            "Authorization freeze changed"
        )

    if sha(IMPL_SUMS) != EXPECTED_IMPL_SUMS:
        raise RuntimeError(
            "Implementation freeze changed"
        )

    for name, expected in EXPECTED_OUTPUTS.items():
        if sha(Path(name)) != expected:
            raise RuntimeError(
                "Frozen result artifact changed: "
                + name
            )

    if sha(DESIGN) != EXPECTED_DESIGN_SHA:
        raise RuntimeError(
            "Result-freeze design changed"
        )

    if sha(DOC) != EXPECTED_DOC_SHA:
        raise RuntimeError(
            "Result-freeze document changed"
        )

    value = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if value["status"] != "FROZEN_FUTURE_SCORING_RESULTS_V1":
        raise RuntimeError(
            "Result-freeze status changed"
        )

    if value["freeze_parent_commit"] != EXPECTED_PARENT:
        raise RuntimeError(
            "Result-freeze parent changed"
        )

    if value["authorization"]["one_time_execution_consumed"] is not True:
        raise RuntimeError(
            "One-use execution not recorded consumed"
        )

    if value["authorization"]["rerun_authorized"] is not False:
        raise RuntimeError(
            "Rerun unexpectedly authorized"
        )

    if value["result_contract"]["future_scored_rows"] != 11905:
        raise RuntimeError(
            "Scored-row count changed"
        )

    if value["result_contract"]["future_resolution_rows"] != 12162:
        raise RuntimeError(
            "Coverage population changed"
        )

    if value["result_contract"]["feature_count"] != 92151:
        raise RuntimeError(
            "Feature count changed"
        )

    for key, expected in {
        "threshold_selected": False,
        "hard_predictions_generated": False,
        "probability_calibration_performed": False,
        "review_fraction_selected": False,
    }.items():
        if value["decision_boundary"][key] is not expected:
            raise RuntimeError(
                "Decision-boundary state changed: "
                + key
            )

    for key in (
        "blind_validation_content_used",
        "future_labels_used",
        "unblinding_performed",
    ):
        if value["blind_validation_boundary"][key] is not False:
            raise RuntimeError(
                "Blind boundary changed: "
                + key
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

        if sha(Path(rel)) != digest:
            raise RuntimeError(
                "Result-freeze checksum mismatch: "
                + rel
            )

    print(
        "PASS | repository position =",
        position,
    )
    print(
        "PASS | future scoring result freeze validates"
    )
    print(
        "PASS | exact five production artifacts bound"
    )
    print(
        "PASS | one-use execution consumed; rerun unauthorized"
    )
    print(
        "PASS | 11,905 continuous scores frozen"
    )
    print(
        "PASS | threshold/hard-prediction state remains false"
    )
    print(
        "PASS | blind-validation content remains unused"
    )


if __name__ == "__main__":
    validate()
