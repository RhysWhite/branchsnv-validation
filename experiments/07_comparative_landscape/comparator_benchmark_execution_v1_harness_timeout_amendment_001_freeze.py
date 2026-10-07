#!/usr/bin/env python3
"""Validate the independently approved harness timeout amendment."""

import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]

STEM = "comparator_benchmark_execution_v1_harness_timeout_amendment_001"

AMENDMENT = ROOT / f"{STEM}.json"
DOCUMENT = ROOT / "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_TIMEOUT_AMENDMENT_001.md"
SCRIPT = ROOT / f"{STEM}_freeze.py"
MANIFEST = ROOT / f"{STEM}.sha256"

ORIGINAL = ROOT / "comparator_benchmark_execution_v1_harness_implementation_authorization.json"
DESIGN = ROOT / "comparator_benchmark_execution_v1_design.json"
MATRIX = ROOT / "comparator_benchmark_execution_v1_scenario_matrix.tsv"

EXPECTED_ORIGINAL_SHA = (
    "934bf529136b34b5d39c1f22816aed19dedcd4b4c1aeddd34d1341e54e752cb5"
)
EXPECTED_DESIGN_SHA = (
    "1306af08f69d27a80990203bd7d803d2c907a1cdeb56bfd2fe0174bf4a416cde"
)
EXPECTED_MATRIX_SHA = (
    "8e569a6fbad769de0aed087e882410f6f1dd7114cb060e13a956159ae0b39398"
)
BASE_COMMIT = "6dd22db80ea0f34fad868d196e65b3847749e403"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    value = json.loads(path.read_text())
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def validate():
    require(
        not (
            REPO
            / "results/07_comparative_landscape/comparator_benchmark_execution_v1"
        ).exists(),
        "canonical result root must remain absent",
    )

    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"],
        cwd=REPO,
        check=True,
    )

    print("PASS | amendment base commit is an ancestor")

    for path, expected in (
        (ORIGINAL, EXPECTED_ORIGINAL_SHA),
        (DESIGN, EXPECTED_DESIGN_SHA),
        (MATRIX, EXPECTED_MATRIX_SHA),
    ):
        require(
            sha256(path) == expected,
            f"frozen source identity differs: {path.name}",
        )

    print("PASS | original authorization, design and matrix identities unchanged")

    original = read_json(ORIGINAL)
    design = read_json(DESIGN)
    amendment = read_json(AMENDMENT)

    require(
        original.get("authorization_id")
        == "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_IMPLEMENTATION_001",
        "original authorization ID differs",
    )

    require(
        original["resource_contract"]["timeout_seconds_per_invocation"]
        == 86400,
        "original historical timeout differs",
    )

    require(
        design["resource_and_failure_policy"]["core_timeout_seconds"]
        == 3600,
        "frozen core timeout differs",
    )

    require(
        design["resource_and_failure_policy"]["scale_timeout_seconds"]
        == 14400,
        "frozen scale timeout differs",
    )

    require(
        amendment["amendment_id"]
        == "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_TIMEOUT_AMENDMENT_001",
        "amendment identity differs",
    )

    require(
        amendment["status"] == "APPROVED_FOR_IMPLEMENTATION_NOT_EXECUTION",
        "amendment status differs",
    )

    require(
        amendment["authorization_parent_commit"] == BASE_COMMIT,
        "amendment parent differs",
    )

    for key, expected in (
        ("original_authorization_sha256", EXPECTED_ORIGINAL_SHA),
        ("frozen_execution_design_sha256", EXPECTED_DESIGN_SHA),
        ("frozen_scenario_matrix_sha256", EXPECTED_MATRIX_SHA),
    ):
        require(amendment.get(key) == expected, f"amendment {key} differs")

    require(
        amendment["superseded_clause"]["field"]
        == "resource_contract.timeout_seconds_per_invocation",
        "supersession field differs",
    )

    require(
        amendment["superseded_clause"]["original_value"] == 86400,
        "supersession original value differs",
    )

    policy = amendment["effective_policy"]

    require(
        policy["core_timeout_seconds"] == 3600
        and policy["scale_timeout_seconds"] == 14400
        and policy["core_tip_counts"] == [32, 128]
        and policy["scale_tip_counts"] == [512]
        and policy["classification_status"] == "NEWLY_APPROVED_INTERPRETATION"
        and policy["selection_source"] == "tip_count column in the frozen scenario matrix",
        "effective timeout policy differs",
    )

    print("PASS | newly approved classification and original frozen timeouts agree")

    with MATRIX.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require(
            reader.fieldnames is not None
            and {"scenario_id", "tip_count"}.issubset(reader.fieldnames),
            "matrix columns differ",
        )
        rows = list(reader)

    require(len(rows) == 150, "scenario count differs")

    observed_counts = Counter()
    expected_ranges = {
        32: ("S001", "S050"),
        128: ("S051", "S100"),
        512: ("S101", "S150"),
    }

    for index, row in enumerate(rows, start=1):
        expected_id = f"S{index:03d}"
        require(
            row["scenario_id"] == expected_id,
            f"scenario order differs: {expected_id}",
        )

        tip_count = int(row["tip_count"])
        require(
            tip_count in expected_ranges,
            f"unexpected tip count: {tip_count}",
        )
        observed_counts[tip_count] += 1

    require(
        observed_counts == Counter({32: 50, 128: 50, 512: 50}),
        "scenario-group cardinalities differ",
    )

    expected_groups = {
        "S001-S050": (32, "core", 3600),
        "S051-S100": (128, "core", 3600),
        "S101-S150": (512, "scale", 14400),
    }

    groups = amendment["scenario_groups"]
    require(
        set(groups) == set(expected_groups),
        "scenario-group key set differs",
    )

    for key, (tips, group, timeout) in expected_groups.items():
        record = groups[key]
        require(
            record == {
                "tip_count": tips,
                "class": group,
                "timeout_seconds": timeout,
            },
            f"scenario-group contract differs: {key}",
        )

    print("PASS | all 150 frozen scenarios map uniquely to approved timeouts")

    scope = amendment["amendment_scope"]

    for key in (
        "supersedes_only_original_timeout_clause",
        "original_authorization_must_remain_unchanged",
        "frozen_design_must_remain_unchanged",
        "frozen_runner_must_remain_unchanged",
        "frozen_scenario_matrix_must_remain_unchanged",
        "harness_implementation_only",
    ):
        require(scope.get(key) is True, f"required boundary differs: {key}")

    for key in (
        "canonical_execution_authorized",
        "third_party_comparator_execution_authorized",
        "benchmark_truth_access_authorized",
        "scoring_authorized",
        "automatic_comparator_rerun_authorized",
    ):
        require(scope.get(key) is False, f"prohibited authority differs: {key}")

    require(
        amendment["next_gate"]
        == "APPLY_APPROVED_TIMEOUT_POLICY_AND_FREEZE_COMPARATOR_BENCHMARK_EXECUTION_HARNESS_V1",
        "next gate differs",
    )

    print("PASS | amendment scope preserves all execution/truth/scoring prohibitions")

    expected_files = {
        str(path.relative_to(REPO)): path
        for path in (AMENDMENT, DOCUMENT, SCRIPT)
    }

    entries = {}

    for line in MANIFEST.read_text().splitlines():
        parts = line.split(None, 1)
        require(len(parts) == 2, "malformed checksum manifest line")
        digest, filename = parts
        require(filename not in entries, "duplicate checksum entry")
        entries[filename] = digest

    require(
        set(entries) == set(expected_files),
        "amendment checksum file set differs",
    )

    for filename, path in expected_files.items():
        require(
            sha256(path) == entries[filename],
            f"amendment checksum differs: {filename}",
        )

    print("PASS | amendment JSON, record and validator are checksummed")
    print("PASS | canonical result root remains absent")
    print("TIMEOUT_AMENDMENT_001_VALIDATION=PASS")


if __name__ == "__main__":
    validate()
