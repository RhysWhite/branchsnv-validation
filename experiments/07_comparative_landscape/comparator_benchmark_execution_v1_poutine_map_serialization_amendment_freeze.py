#!/usr/bin/env python3

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
IMPL = ROOT / "comparator_benchmark_execution_v1_impl"

AUTH_COMMIT = "91063725b4a9ab5bb20461bd90c3200020f440fe"

AUTH = ROOT / (
    "comparator_benchmark_execution_v1_"
    "poutine_map_serialization_amendment_authorization.json"
)

MANIFEST = ROOT / (
    "comparator_benchmark_execution_v1_"
    "poutine_map_serialization_amendment_manifest.json"
)

MD = ROOT / (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "POUTINE_MAP_SERIALIZATION_AMENDMENT.md"
)

IMPLEMENTATION_REL = {
    "adapters":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/adapters.py",
    "toy_validation":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/toy_validation.py",
}

FREEZE_REL = {
    "manifest":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "poutine_map_serialization_amendment_manifest.json",
    "documentation":
        "experiments/07_comparative_landscape/"
        "COMPARATOR_BENCHMARK_EXECUTION_V1_"
        "POUTINE_MAP_SERIALIZATION_AMENDMENT.md",
    "freeze_validator":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "poutine_map_serialization_amendment_freeze.py",
    "checksum_ledger":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "poutine_map_serialization_amendment.sha256",
}

EXPECTED_AFTER = {
    "adapters":
        "5c4e8d95fa104882952116e35c060df0f6bff87547fc9cae7c838b7247eaa49d",
    "toy_validation":
        "7058dd7f8a490274cb49c49109b892923613f59916f77d7fa736926d92b5eb03",
}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def current_bytes(relpath: str) -> bytes:
    return (REPO / relpath).read_bytes()

def commit_bytes(commit: str, relpath: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{relpath}"],
        cwd=REPO,
    )

def first_commit_after(parent: str, head: str) -> str | None:
    commits = subprocess.check_output(
        ["git", "rev-list", "--reverse", f"{parent}..{head}"],
        cwd=REPO,
        text=True,
    ).splitlines()
    return commits[0] if commits else None

auth = json.loads(AUTH.read_text())
manifest = json.loads(MANIFEST.read_text())

if auth["authorization_id"] != (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "POUTINE_MAP_SERIALIZATION_AMENDMENT_001"
):
    raise RuntimeError("authorization id differs")

if manifest["freeze_id"] != (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "POUTINE_MAP_SERIALIZATION_AMENDMENT_V1"
):
    raise RuntimeError("freeze id differs")

if manifest["status"] != "FROZEN_AMENDMENT_V1":
    raise RuntimeError("freeze status differs")

if manifest["parent_authorization_commit"] != AUTH_COMMIT:
    raise RuntimeError("freeze parent differs")

if not manifest["authorization_consumed"]:
    raise RuntimeError("authorization not recorded as consumed")

if manifest["next_gate"] != (
    "REAUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V3"
):
    raise RuntimeError("next gate differs")

runner = manifest["runner_v2_authorization"]

if runner["consumed"]:
    raise RuntimeError("runner-v2 authorization unexpectedly consumed")

if not runner["must_not_be_consumed"]:
    raise RuntimeError("runner-v2 supersession boundary absent")

for key, expected in EXPECTED_AFTER.items():
    if manifest["implementation_after_sha256"][key] != expected:
        raise RuntimeError(f"manifest after-hash differs: {key}")

# Authorization baseline must correspond exactly to the authorization commit.
for key, relpath in IMPLEMENTATION_REL.items():
    observed = digest(commit_bytes(AUTH_COMMIT, relpath))
    expected = auth["baseline_sha256"][key]
    if observed != expected:
        raise RuntimeError(
            f"authorization baseline differs for {key}: "
            f"{observed} != {expected}"
        )

head = subprocess.check_output(
    ["git", "rev-parse", "HEAD"],
    cwd=REPO,
    text=True,
).strip()

ancestor = subprocess.run(
    ["git", "merge-base", "--is-ancestor", AUTH_COMMIT, head],
    cwd=REPO,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

if ancestor.returncode != 0:
    raise RuntimeError(
        "authorization commit is not an ancestor of current HEAD"
    )

freeze_commit = first_commit_after(AUTH_COMMIT, head)

expected_commit_files = (
    set(IMPLEMENTATION_REL.values())
    | set(FREEZE_REL.values())
)

if freeze_commit is None:
    status = subprocess.check_output(
        ["git", "status", "--short"],
        cwd=REPO,
        text=True,
    ).splitlines()

    observed_paths = {
        line[3:]
        for line in status
        if line.strip()
    }

    if observed_paths != expected_commit_files:
        raise RuntimeError(
            "pre-commit freeze file boundary differs: "
            f"{sorted(observed_paths)!r}"
        )

    for key, relpath in IMPLEMENTATION_REL.items():
        observed = digest(current_bytes(relpath))
        expected = EXPECTED_AFTER[key]
        if observed != expected:
            raise RuntimeError(
                f"working implementation hash differs for {key}: "
                f"{observed} != {expected}"
            )

    adapters_text = current_bytes(
        IMPLEMENTATION_REL["adapters"]
    ).decode()

else:
    changed = set(
        subprocess.check_output(
            [
                "git",
                "diff",
                "--name-only",
                AUTH_COMMIT,
                freeze_commit,
            ],
            cwd=REPO,
            text=True,
        ).splitlines()
    )

    if changed != expected_commit_files:
        raise RuntimeError(
            "freeze commit file boundary differs: "
            f"{sorted(changed)!r}"
        )

    for key, relpath in IMPLEMENTATION_REL.items():
        observed = digest(commit_bytes(freeze_commit, relpath))
        expected = EXPECTED_AFTER[key]
        if observed != expected:
            raise RuntimeError(
                f"frozen implementation hash differs for {key}: "
                f"{observed} != {expected}"
            )

    adapters_text = commit_bytes(
        freeze_commit,
        IMPLEMENTATION_REL["adapters"],
    ).decode()

# Existing top-level adapter functions must be unchanged and exactly one
# adapter function may have been added.
baseline_adapters = commit_bytes(
    AUTH_COMMIT,
    IMPLEMENTATION_REL["adapters"],
).decode()

before_tree = ast.parse(baseline_adapters)
after_tree = ast.parse(adapters_text)

before_funcs = {
    node.name: ast.dump(node, include_attributes=False)
    for node in before_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}

after_funcs = {
    node.name: ast.dump(node, include_attributes=False)
    for node in after_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}

added = set(after_funcs) - set(before_funcs)

if added != {"poutine_physical_positions_map_text"}:
    raise RuntimeError(
        f"adapter function addition set differs: {sorted(added)!r}"
    )

removed = set(before_funcs) - set(after_funcs)

if removed:
    raise RuntimeError(
        f"pre-existing adapter functions removed: {sorted(removed)!r}"
    )

for name, before_dump in before_funcs.items():
    if after_funcs[name] != before_dump:
        raise RuntimeError(
            f"pre-existing adapter function changed unexpectedly: {name}"
        )

change = manifest["change"]

if change["function"] != "poutine_physical_positions_map_text":
    raise RuntimeError("frozen function identity differs")

if change["serialization"] != (
    "1<TAB>markerN<TAB>0<TAB>GENOMIC_POSITION"
):
    raise RuntimeError("frozen map serialization differs")

for key in (
    "final_newline",
    "input_order_preserved",
    "duplicate_positions_rejected",
    "non_positive_positions_rejected",
):
    if change[key] is not True:
        raise RuntimeError(f"frozen map property differs: {key}")

for key, value in manifest["unchanged_contracts"].items():
    if value is not True:
        raise RuntimeError(f"unchanged-contract flag differs: {key}")

validation = manifest["validation"]

if validation["third_party_comparator_executed"] is not False:
    raise RuntimeError("comparator-execution boundary differs")

if validation["benchmark_truth_accessed"] is not False:
    raise RuntimeError("benchmark-truth boundary differs")

text = MD.read_text()

for required in (
    "poutine_physical_positions_map_text()",
    "reproduces the",
    "byte-for-byte",
    "Runner implementation authorization v2 remains unconsumed",
    "REAUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V3",
):
    if required not in text:
        raise RuntimeError(
            f"freeze documentation missing required text: {required}"
        )

# Re-run validation only while the freeze commit is pending.
if freeze_commit is None:
    toy = subprocess.run(
        [
            sys.executable,
            str(IMPL / "toy_validation.py"),
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if toy.returncode != 0:
        raise RuntimeError(
            "toy validation failed:\n"
            + toy.stdout
            + toy.stderr
        )

    if "TOY_IMPLEMENTATION_VALIDATION=PASS" not in toy.stdout:
        raise RuntimeError("toy validation PASS marker absent")

    if (
        "PASS | POUTINE physical-position map serialization contract"
        not in toy.stdout
    ):
        raise RuntimeError("POUTINE map validation PASS marker absent")

    sys.path.insert(0, str(IMPL))
    import adapters

    smoke_map = (
        REPO
        / auth["successful_smoke_evidence"]["path"]
    ).read_bytes()

    generated = adapters.poutine_physical_positions_map_text(
        [10, 20, 30, 40]
    ).encode()

    if generated != smoke_map:
        raise RuntimeError(
            "POUTINE map serializer differs from successful smoke evidence"
        )

    # Existing POUTINE parser contract must remain unchanged.
    poutine_output = (
        REPO
        / "results"
        / "07_comparative_landscape"
        / "comparator_benchmark_environment_smoke_v1"
        / "POUTINE"
        / "attempt_04_toy_smoke"
        / "output"
        / "poutine.out"
    )

    observed = adapters.parse_poutine_result(
        poutine_output.read_text()
    )

    expected = [
        {
            "position": "20",
            "reported_recurrence_count_if_available": "2",
        }
    ]

    if observed != expected:
        raise RuntimeError(
            f"POUTINE output-parser regression: {observed!r}"
        )

    pastml = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "comparator_benchmark_execution_v1_"
                "pastml_ambiguity_amendment_test.py"
            ),
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if pastml.returncode != 0:
        raise RuntimeError(
            "PastML ambiguity regression failed:\n"
            + pastml.stdout
            + pastml.stderr
        )

    if "PASTML_AMBIGUITY_AMENDMENT_TEST=PASS" not in pastml.stdout:
        raise RuntimeError(
            "PastML ambiguity regression PASS marker absent"
        )

print("PASS | POUTINE map-serialization amendment v1 validates")
print("PASS | authorization consumed exactly once")
print("PASS | exactly two authorized implementation files changed")
print("PASS | exactly one adapter function added")
print("PASS | all pre-existing adapter functions remain unchanged")
print("PASS | successful POUTINE smoke map reproduced byte-for-byte")
print("PASS | POUTINE output parser remains unchanged")
print("PASS | synthetic and regression validation evidence recorded")
print("PASS | third-party comparator execution remains false")
print("PASS | benchmark truth access remains false")
print("PASS | runner-v2 authorization remains unconsumed and superseded")
print(
    "PASS | next gate = "
    "REAUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V3"
)
