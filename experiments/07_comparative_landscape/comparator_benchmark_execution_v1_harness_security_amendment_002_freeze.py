#!/usr/bin/env python3
"""Independent freeze validation for harness Security Amendment 002."""

from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]

BASE = "10981a2c4e34ebfc14350f74b84b35d5775216d0"

EXPECTED_JSON_SHA256 = "fab751b5ae6fe52a07eecef6d5491d9b87f43a27c807b9aff0ce9962895330d6"
EXPECTED_RECORD_SHA256 = "d85fa41cac747fb134ead69f3996d0d10d170d5f495c9e387413c376cf505be8"

FILES = {
    "original_authorization": (
        "comparator_benchmark_execution_v1_"
        "harness_implementation_authorization.json",
        "934bf529136b34b5d39c1f22816aed19dedcd4b4c1aeddd34d1341e54e752cb5",
    ),
    "original_design": (
        "comparator_benchmark_execution_v1_design.json",
        "1306af08f69d27a80990203bd7d803d2c907a1cdeb56bfd2fe0174bf4a416cde",
    ),
    "timeout_amendment_001": (
        "comparator_benchmark_execution_v1_"
        "harness_timeout_amendment_001.json",
        "c1f3e01988d2535085618f33f1131f2238cfb8ebbe21ee4af53989a1a9081a81",
    ),
    "scenario_matrix": (
        "comparator_benchmark_execution_v1_scenario_matrix.tsv",
        "8e569a6fbad769de0aed087e882410f6f1dd7114cb060e13a956159ae0b39398",
    ),
    "frozen_runner": (
        "comparator_benchmark_execution_v1_runner.py",
        "63a5e45a4082a5709e385e57f3af389769bc4520b5e2a4310bb20fb86e964a33",
    ),
}

JSON_NAME = (
    "comparator_benchmark_execution_v1_"
    "harness_security_amendment_002.json"
)
RECORD_NAME = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "HARNESS_SECURITY_AMENDMENT_002.md"
)
FREEZE_NAME = (
    "comparator_benchmark_execution_v1_"
    "harness_security_amendment_002_freeze.py"
)
MANIFEST_NAME = (
    "comparator_benchmark_execution_v1_"
    "harness_security_amendment_002.sha256"
)


def require(condition, message):
    if not condition:
        raise SystemExit("FAIL | " + message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


require(
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "HEAD"],
        cwd=REPO,
        check=False,
    ).returncode == 0,
    "Amendment 002 base commit is not an ancestor",
)

print("PASS | amendment authorization base is an ancestor")


for label, (name, expected) in FILES.items():
    require(
        sha256(ROOT / name) == expected,
        "frozen dependency identity differs: " + label,
    )

print("PASS | original authorization, design, runner and matrix unchanged")
print("PASS | timeout Amendment 001 unchanged")


require(
    sha256(ROOT / JSON_NAME) == EXPECTED_JSON_SHA256,
    "Amendment 002 JSON identity differs",
)

require(
    sha256(ROOT / RECORD_NAME) == EXPECTED_RECORD_SHA256,
    "Amendment 002 explanatory record identity differs",
)

data = json.loads((ROOT / JSON_NAME).read_text())

require(
    data["amendment_id"] ==
    "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_SECURITY_AMENDMENT_002"
    and data["status"] == "FROZEN_SCOPE_PRE_IMPLEMENTATION"
    and data["authorization_parent_commit"] == BASE,
    "Amendment 002 identity/status differs",
)

original = json.loads(
    (ROOT / FILES["original_authorization"][0]).read_text()
)

required = original["sandbox_contract"]["required_arguments"]

require(
    required[:2] == [
        "--ro-bind / /",
        "--bind RESULT_ROOT RESULT_ROOT",
    ],
    "original superseded sandbox clauses differ",
)

require(
    data["superseded_original_sandbox_clauses"] == [
        "$.sandbox_contract.host_root_read_only",
        "$.sandbox_contract.required_arguments[0]",
        "$.sandbox_contract.required_arguments[1]",
    ],
    "Amendment 002 supersession scope differs",
)

print("PASS | exact original sandbox conflict and supersession verified")


dependencies = data["frozen_dependencies"]

for label, (_, expected) in FILES.items():
    require(
        dependencies[label + "_sha256"] == expected,
        "Amendment 002 pinned dependency differs: " + label,
    )

isolation = data["truth_isolation_contract"]
sandbox = data["preserved_sandbox_properties"]

require(
    isolation["private_root_required"] is True
    and isolation["host_root_bind_prohibited"] is True
    and isolation["unrestricted_home_bind_prohibited"] is True
    and isolation["unrestricted_repository_bind_prohibited"] is True
    and isolation["unrestricted_dataset_parent_bind_prohibited"] is True
    and isolation["unrestricted_runtime_parent_bind_prohibited"] is True,
    "Amendment 002 truth-isolation requirements differ",
)

require(
    sandbox == {
        "network_disabled": True,
        "private_tmp": True,
        "process_lifetime_bound_to_parent": True,
        "only_authorized_invocation_workspace_writable": True,
        "host_root_must_not_be_mounted": True,
    },
    "Amendment 002 preserved sandbox properties differ",
)

require(
    len(isolation["negative_tests_required"]) >= 12
    and len(set(isolation["negative_tests_required"]))
        == len(isolation["negative_tests_required"]),
    "Amendment 002 negative-test coverage differs",
)

print("PASS | private-root and adversarial truth-isolation policy frozen")


plan = data["production_harness_contract"]

require(
    plan["planned_invocations"] == 1200
    and plan["scenario_count"] == 150
    and plan["method_count"] == 8
    and plan["dispatch_order"] == "frozen_method_major"
    and plan["core_invocations"] == 800
    and plan["scale_invocations"] == 400
    and plan["core_timeout_seconds"] == 3600
    and plan["scale_timeout_seconds"] == 14400,
    "Amendment 002 production orchestration dimensions differ",
)

print("PASS | frozen dispatch and Amendment 001 timeouts preserved")


scope = data["implementation_scope"]

expected_harness = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_harness.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_harness_validation.py",

    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_IMPLEMENTATION.md",
]

require(
    scope["authorized_existing_implementation_files"]
        == expected_harness,
    "Amendment 002 implementation file boundary differs",
)

for key, value in scope.items():
    if key.endswith("_unchanged"):
        require(
            value is True,
            "Amendment 002 frozen dependency protection differs: " + key,
        )

for key, value in data["explicit_prohibitions"].items():
    require(
        value is False,
        "Amendment 002 unexpectedly authorizes: " + key,
    )

require(
    data["future_execution_gate"]
    == "SEPARATE_EXPLICIT_CANONICAL_EXECUTION_AUTHORIZATION_REQUIRED",
    "separate execution authorization gate differs",
)

require(
    not (
        REPO
        / "results/07_comparative_landscape/"
          "comparator_benchmark_execution_v1"
    ).exists(),
    "canonical result root unexpectedly exists",
)

print("PASS | scientific and execution prohibitions retained")
print("PASS | exactly three implementation files remain authorized")
print("PASS | canonical result root absent")


manifest_lines = (
    ROOT / MANIFEST_NAME
).read_text().splitlines()

expected_manifest = {
    JSON_NAME,
    RECORD_NAME,
    FREEZE_NAME,
}

observed_manifest = {}

for line in manifest_lines:
    parts = line.split("  ", 1)

    require(
        len(parts) == 2,
        "Amendment 002 checksum manifest malformed",
    )

    expected_hash, name = parts

    require(
        name in expected_manifest
        and name not in observed_manifest
        and len(expected_hash) == 64,
        "Amendment 002 manifest path/hash differs",
    )

    observed_manifest[name] = expected_hash

require(
    set(observed_manifest) == expected_manifest,
    "Amendment 002 manifest coverage differs",
)

for name, expected_hash in observed_manifest.items():
    require(
        sha256(ROOT / name) == expected_hash,
        "Amendment 002 checksummed artifact differs: " + name,
    )

require(
    observed_manifest[JSON_NAME] == EXPECTED_JSON_SHA256
    and observed_manifest[RECORD_NAME] == EXPECTED_RECORD_SHA256,
    "Amendment 002 independent identities differ",
)

print("PASS | amendment JSON, record and validator checksummed")
print("SECURITY_AMENDMENT_002_VALIDATION=PASS")
