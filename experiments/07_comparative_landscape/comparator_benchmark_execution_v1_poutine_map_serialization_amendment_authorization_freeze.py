#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]

AUTH = ROOT / (
    "comparator_benchmark_execution_v1_"
    "poutine_map_serialization_amendment_authorization.json"
)

MD = ROOT / (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "POUTINE_MAP_SERIALIZATION_AMENDMENT_AUTHORIZATION.md"
)

EXPECTED_PARENT = "8c7c68715e2d2caa26e4115e9c4f315825d0932f"

PATHS = {
    "adapters":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/adapters.py",
    "toy_validation":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/toy_validation.py",
    "environment_recipes":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/environment_recipes.json",
    "output_normalization_manifest":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "output_normalization_amendment_manifest.json",
    "poutine_run_contract_authorization":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "poutine_run_contract_amendment_authorization.json",
    "runner_v2_authorization":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "runner_implementation_v2_authorization.json",
}

EXPECTED_FILES = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_impl/adapters.py",
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_impl/toy_validation.py",
]

def digest(data):
    return hashlib.sha256(data).hexdigest()

a = json.loads(AUTH.read_text())

if a["authorization_id"] != (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "POUTINE_MAP_SERIALIZATION_AMENDMENT_001"
):
    raise RuntimeError("authorization id differs")

if a["status"] != "AUTHORIZED_NOT_YET_CONSUMED":
    raise RuntimeError("authorization status differs")

if a["parent_commit"] != EXPECTED_PARENT:
    raise RuntimeError("authorization parent differs")

if a["authorized_files"] != EXPECTED_FILES:
    raise RuntimeError("authorized implementation file set differs")

if a["next_gate"] != (
    "IMPLEMENT_AND_FREEZE_POUTINE_MAP_SERIALIZATION_AMENDMENT_V1"
):
    raise RuntimeError("next gate differs")

if not a["one_time_amendment"]:
    raise RuntimeError("one-time amendment flag absent")

if a["rerun_authorized"]:
    raise RuntimeError("rerun unexpectedly authorized")

runner = a["runner_v2_authorization"]

if runner["authorization_id"] != (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "RUNNER_IMPLEMENTATION_V2_001"
):
    raise RuntimeError("runner-v2 authorization id differs")

if runner["consumed"]:
    raise RuntimeError("runner-v2 authorization recorded as consumed")

if not runner[
    "must_not_be_consumed_after_this_amendment_changes_frozen_hashes"
]:
    raise RuntimeError("runner-v2 supersession boundary absent")

required_denials = [
    "canonical_benchmark_execution",
    "third_party_comparator_execution",
    "benchmark_truth_access",
    "benchmark_truth_debugging",
    "environment_recipe_change",
    "method_matrix_change",
    "scenario_matrix_change",
    "metric_change",
    "source_pin_change",
    "comparator_version_change",
    "comparator_parameter_change",
    "runner_implementation",
    "production_bridge",
    "production_ledger_mutation",
]

for key in required_denials:
    if a["explicitly_not_authorized"].get(key) is not True:
        raise RuntimeError(f"required denial absent: {key}")

head = subprocess.check_output(
    ["git", "rev-parse", "HEAD"],
    cwd=REPO,
    text=True,
).strip()

ancestor = subprocess.run(
    ["git", "merge-base", "--is-ancestor", EXPECTED_PARENT, head],
    cwd=REPO,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

if ancestor.returncode != 0:
    raise RuntimeError(
        "authorization parent is not an ancestor of current HEAD"
    )

for name, relpath in PATHS.items():
    data = subprocess.check_output(
        ["git", "show", f"{EXPECTED_PARENT}:{relpath}"],
        cwd=REPO,
    )
    observed = digest(data)
    expected = a["baseline_sha256"][name]
    if observed != expected:
        raise RuntimeError(
            f"parent artifact identity differs: "
            f"{name}: {observed} != {expected}"
        )

smoke = a["successful_smoke_evidence"]

expected_text = (
    "1\tmarker1\t0\t10\n"
    "1\tmarker2\t0\t20\n"
    "1\tmarker3\t0\t30\n"
    "1\tmarker4\t0\t40\n"
)

if smoke["exact_text"] != expected_text:
    raise RuntimeError("recorded smoke-map serialization differs")

smoke_path = REPO / smoke["path"]

if not smoke_path.is_file():
    raise RuntimeError("successful frozen POUTINE smoke map absent")

if digest(smoke_path.read_bytes()) != smoke["sha256"]:
    raise RuntimeError("successful frozen POUTINE smoke map hash differs")

if smoke_path.read_text() != expected_text:
    raise RuntimeError("successful frozen POUTINE smoke map text differs")

text = MD.read_text()

for required in (
    "poutine_physical_positions_map_text()",
    "1<TAB>markerN<TAB>0<TAB>GENOMIC_POSITION",
    "Runner implementation v2 remains unconsumed",
    "IMPLEMENT_AND_FREEZE_POUTINE_MAP_SERIALIZATION_AMENDMENT_V1",
):
    if required not in text:
        raise RuntimeError(
            f"authorization documentation missing: {required}"
        )

print("PASS | POUTINE map-serialization amendment authorization validates")
print("PASS | parent commit is an ancestor of current HEAD")
print("PASS | all frozen baseline identities match")
print("PASS | successful POUTINE smoke map identity matches")
print("PASS | exact four-column map serialization recorded")
print("PASS | amendment restricted to adapters.py and toy_validation.py")
print("PASS | POUTINE run/version/parameter/scoring contracts immutable")
print("PASS | comparator execution remains unauthorized")
print("PASS | benchmark truth access remains unauthorized")
print("PASS | runner-v2 authorization remains unconsumed and will be superseded")
print(
    "PASS | next gate = "
    "IMPLEMENT_AND_FREEZE_POUTINE_MAP_SERIALIZATION_AMENDMENT_V1"
)
