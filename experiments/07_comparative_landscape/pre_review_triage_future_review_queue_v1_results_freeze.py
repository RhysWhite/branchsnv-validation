from pathlib import Path
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import csv
import hashlib
import json
import subprocess

ROOT = Path("experiments/07_comparative_landscape")
OUT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_review_queue_v1"
)
SCORE = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_scoring_v1"
)

DESIGN = ROOT / "pre_review_triage_future_review_queue_v1_results_design.json"
DOC = ROOT / "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_RESULTS.md"
FREEZE = ROOT / "pre_review_triage_future_review_queue_v1_results_freeze.py"
SUMS = ROOT / "pre_review_triage_future_review_queue_v1_results.sha256"

AUTH_SUMS = ROOT / (
    "pre_review_triage_future_review_queue_v1_"
    "generation_authorization_002.sha256"
)
AMEND_SUMS = ROOT / (
    "pre_review_triage_future_review_queue_v1_"
    "amendment_001.sha256"
)
IMPL = ROOT / "pre_review_triage_future_review_queue_v1.py"

SCORED = SCORE / "scored_records.tsv"
COVERAGE = SCORE / "coverage.tsv"

PRIORITY = OUT / "priority_scored_queue.tsv"
RESIDUAL = OUT / "residual_scored_queue.tsv"
MANUAL = OUT / "unscored_manual_review_queue.tsv"
MANIFEST = OUT / "queue_manifest.json"

EXPECTED_PARENT = (
    "8250212715a5d105113cd5891caf42794789d451"
)
EXPECTED_BUILDER_SHA = (
    "7eea07f6a2214915ff84d6bd2bfc961"
    "8380934fee54684f118cbcdf065df3916"
)

EXPECTED_COMMIT_PATHS = {
    str(DESIGN),
    str(DOC),
    str(FREEZE),
    str(SUMS),
    str(PRIORITY),
    str(RESIDUAL),
    str(MANUAL),
    str(MANIFEST),
}


def sha(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def git(*args):
    return subprocess.check_output(
        ["git", *args],
        text=True,
    ).strip()


def read_tsv(path):
    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )
        if reader.fieldnames is None:
            raise RuntimeError(
                "Missing TSV header: " + str(path)
            )
        return reader.fieldnames, list(reader)


def identity(row):
    return (
        row["retrieval_record_index"],
        row["screening_entity_id"],
    )


def repository_position():
    head = git("rev-parse", "HEAD")

    if head == EXPECTED_PARENT:
        return "PRE_COMMIT_PARENT"

    if git("rev-parse", "HEAD^") != EXPECTED_PARENT:
        raise RuntimeError(
            "Unexpected review-queue result-freeze repository position"
        )

    changed = {
        x
        for x in git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).splitlines()
        if x
    }

    if changed != EXPECTED_COMMIT_PATHS:
        raise RuntimeError(
            "Review-queue result-freeze commit path set differs"
        )

    return "COMMITTED_FREEZE"


def validate():
    position = repository_position()

    if git("status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError(
            "Tracked working tree is not clean"
        )

    subprocess.run(
        [
            "sha256sum",
            "--check",
            str(AUTH_SUMS),
        ],
        check=True,
    )

    subprocess.run(
        [
            "sha256sum",
            "--check",
            str(AMEND_SUMS),
        ],
        check=True,
    )

    if sha(IMPL) != EXPECTED_BUILDER_SHA:
        raise RuntimeError(
            "Active queue builder changed"
        )

    value = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        value["status"]
        != "FROZEN_FUTURE_REVIEW_QUEUE_V1_RESULTS"
    ):
        raise RuntimeError(
            "Result-freeze status changed"
        )

    if value["freeze_parent_commit"] != EXPECTED_PARENT:
        raise RuntimeError(
            "Result-freeze parent changed"
        )

    generation = value["generation"]

    if (
        generation["authorization_id"]
        != "PRE_REVIEW_TRIAGE_FUTURE_REVIEW_QUEUE_V1_GENERATION_002"
    ):
        raise RuntimeError(
            "Generation authorization ID changed"
        )

    if generation["one_time_generation_consumed"] is not True:
        raise RuntimeError(
            "One-use generation is not recorded consumed"
        )

    if generation["rerun_authorized"] is not False:
        raise RuntimeError(
            "Rerun unexpectedly authorized"
        )

    if (
        generation["active_builder_sha256"]
        != EXPECTED_BUILDER_SHA
    ):
        raise RuntimeError(
            "Recorded builder identity changed"
        )

    manifest = json.loads(
        MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    if (
        manifest["status"]
        != "FUTURE_REVIEW_QUEUE_GENERATED_PRE_REVIEW"
    ):
        raise RuntimeError(
            "Queue manifest status changed"
        )

    for name, meta in value[
        "production_artifacts"
    ].items():
        path = Path(name)

        if not path.is_file():
            raise RuntimeError(
                "Frozen result artifact missing: " + name
            )

        if path.stat().st_size != meta["bytes"]:
            raise RuntimeError(
                "Frozen result artifact size changed: " + name
            )

        if sha(path) != meta["sha256"]:
            raise RuntimeError(
                "Frozen result artifact changed: " + name
            )

    for filename in (
        "priority_scored_queue.tsv",
        "residual_scored_queue.tsv",
        "unscored_manual_review_queue.tsv",
    ):
        if (
            sha(OUT / filename)
            != manifest["artifact_sha256"][filename]
        ):
            raise RuntimeError(
                "Queue manifest artifact hash mismatch: "
                + filename
            )

    source = manifest["source_identity"]

    if sha(SCORED) != source["scored_records_sha256"]:
        raise RuntimeError(
            "Scored-record source changed"
        )

    if sha(COVERAGE) != source["coverage_sha256"]:
        raise RuntimeError(
            "Coverage source changed"
        )

    pf, priority = read_tsv(PRIORITY)
    rf, residual = read_tsv(RESIDUAL)
    mf, manual = read_tsv(MANUAL)
    sf, scored = read_tsv(SCORED)
    cf, coverage = read_tsv(COVERAGE)

    if len(priority) != 5483:
        raise RuntimeError(
            "Priority row count changed"
        )

    if len(residual) != 6422:
        raise RuntimeError(
            "Residual row count changed"
        )

    if len(manual) != 257:
        raise RuntimeError(
            "Manual row count changed"
        )

    if len(scored) != 11905:
        raise RuntimeError(
            "Scored source row count changed"
        )

    if len(coverage) != 12162:
        raise RuntimeError(
            "Coverage source row count changed"
        )

    def unique_ids(name, rows):
        ids = [
            identity(row)
            for row in rows
        ]
        if len(ids) != len(set(ids)):
            raise RuntimeError(
                "Duplicate identity in " + name
            )
        return set(ids)

    p_ids = unique_ids(
        "priority", priority
    )
    r_ids = unique_ids(
        "residual", residual
    )
    m_ids = unique_ids(
        "manual", manual
    )
    s_ids = unique_ids(
        "scored", scored
    )
    c_ids = unique_ids(
        "coverage", coverage
    )

    if p_ids & r_ids:
        raise RuntimeError(
            "Priority/residual overlap"
        )

    if p_ids & m_ids:
        raise RuntimeError(
            "Priority/manual overlap"
        )

    if r_ids & m_ids:
        raise RuntimeError(
            "Residual/manual overlap"
        )

    if (p_ids | r_ids | m_ids) != c_ids:
        raise RuntimeError(
            "Queue union differs from coverage universe"
        )

    if (p_ids | r_ids) != s_ids:
        raise RuntimeError(
            "Scored lanes differ from scored source universe"
        )

    if m_ids != (c_ids - s_ids):
        raise RuntimeError(
            "Manual lane differs from unscored universe"
        )

    source_scored = {
        identity(row): row
        for row in scored
    }

    for rows in (
        priority,
        residual,
    ):
        for row in rows:
            src = source_scored[
                identity(row)
            ]

            if (
                row["selected_candidate_id"]
                != src["selected_candidate_id"]
            ):
                raise RuntimeError(
                    "Selected candidate changed"
                )

            if (
                row["continuous_score"]
                != src["continuous_score"]
            ):
                raise RuntimeError(
                    "Continuous score changed"
                )

    for name, rows in (
        ("priority", priority),
        ("residual", residual),
        ("manual", manual),
    ):
        observed = [
            int(row["queue_position"])
            for row in rows
        ]
        expected = list(
            range(
                1,
                len(rows) + 1,
            )
        )

        if observed != expected:
            raise RuntimeError(
                name
                + " queue_position changed"
            )

    combined = (
        priority
        + residual
    )

    def score(row):
        try:
            value = Decimal(
                row["continuous_score"]
            )
        except InvalidOperation as exc:
            raise RuntimeError(
                "Invalid continuous score"
            ) from exc

        if not value.is_finite():
            raise RuntimeError(
                "Non-finite continuous score"
            )

        return value

    expected_order = sorted(
        combined,
        key=lambda row: (
            -score(row),
            row["screening_entity_id"],
        ),
    )

    if (
        [
            identity(row)
            for row in combined
        ]
        != [
            identity(row)
            for row in expected_order
        ]
    ):
        raise RuntimeError(
            "Scored queue ordering changed"
        )

    fraction = Fraction(
        35,
        76,
    )

    expected_prefix = (
        len(combined)
        * fraction.numerator
        + fraction.denominator
        - 1
    ) // fraction.denominator

    if expected_prefix != 5483:
        raise RuntimeError(
            "Prefix calculation changed"
        )

    if priority != combined[:expected_prefix]:
        raise RuntimeError(
            "Priority lane is not exact score prefix"
        )

    if residual != combined[expected_prefix:]:
        raise RuntimeError(
            "Residual lane is not exact score suffix"
        )

    manual_indices = [
        int(
            row["retrieval_record_index"]
        )
        for row in manual
    ]

    if manual_indices != sorted(
        manual_indices
    ):
        raise RuntimeError(
            "Manual ordering changed"
        )

    coverage_by_id = {
        identity(row): row
        for row in coverage
    }

    for row in manual:
        src = coverage_by_id[
            identity(row)
        ]

        for col in (
            "abstract_status",
            "coverage_status",
        ):
            if row[col] != src[col]:
                raise RuntimeError(
                    "Manual metadata changed: "
                    + col
                )

    boundary = manifest[
        "scientific_boundary"
    ]

    for key in (
        "automatic_scientific_exclusion",
        "automatic_scientific_inclusion",
        "blind_validation_content_used",
        "future_labels_used",
        "hard_prediction",
        "production_ledger_mutated",
        "raw_score_threshold",
    ):
        if boundary.get(key) is not False:
            raise RuntimeError(
                "Scientific boundary changed: "
                + key
            )

    if manifest[
        "cross_lane_priority_defined"
    ] is not False:
        raise RuntimeError(
            "Cross-lane priority unexpectedly defined"
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
        "PASS | future review-queue result freeze validates"
    )
    print(
        "PASS | exact four production artifacts bound"
    )
    print(
        "PASS | one-use GENERATION_002 consumed; rerun unauthorized"
    )
    print(
        "PASS | 12,162-record human-review universe exact"
    )
    print(
        "PASS | 5,483 / 6,422 / 257 lane partition exact"
    )
    print(
        "PASS | scored ranking and 35/76 prefix exact"
    )
    print(
        "PASS | manual-review lane exact"
    )
    print(
        "PASS | scientific boundary remains non-decisional"
    )
    print(
        "PASS | downstream gate remains unresolved"
    )


if __name__ == "__main__":
    validate()
