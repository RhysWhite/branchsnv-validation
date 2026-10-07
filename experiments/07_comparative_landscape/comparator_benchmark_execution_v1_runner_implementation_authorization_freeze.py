#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
AUTH = ROOT / (
    "comparator_benchmark_execution_v1_runner_implementation_authorization.json"
)
MD = ROOT / (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION_AUTHORIZATION.md"
)

EXPECTED_PARENT = "78833297e429c21b210b2258c5157e4c3c450a20"

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

a = json.loads(AUTH.read_text())

if a["authorization_id"] != \
        "COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION_001":
    raise RuntimeError("authorization id differs")

if a["status"] != "AUTHORIZED_NOT_YET_CONSUMED":
    raise RuntimeError("authorization status differs")

if a["parent_commit"] != EXPECTED_PARENT:
    raise RuntimeError("authorization parent commit differs")

if a["triggering_gate"] != \
        "AUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V1":
    raise RuntimeError("triggering gate differs")

if a["next_gate"] != \
        "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_RUNNER_V1":
    raise RuntimeError("next gate differs")

expected_files = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_runner.py",
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_runner_validation.py",
    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION.md",
]
if a["authorized_implementation_files"] != expected_files:
    raise RuntimeError("authorized implementation file set differs")

required_denials = [
    "canonical_benchmark_execution",
    "third_party_comparator_execution",
    "benchmark_truth_access_for_runner_implementation",
    "benchmark_truth_use_for_debugging",
    "benchmark_dataset_mutation",
    "scenario_matrix_mutation",
    "method_matrix_mutation",
    "adapter_mutation",
    "environment_recipe_mutation",
    "metric_mutation",
    "source_pin_mutation",
    "comparator_version_change",
    "comparator_parameter_change",
    "production_bridge",
    "production_ledger_mutation",
]
for key in required_denials:
    if a["explicitly_not_authorized"].get(key) is not True:
        raise RuntimeError(f"required denial absent: {key}")

if not a["one_time_runner_implementation_authorization"]:
    raise RuntimeError("one-time authorization flag absent")

if a["rerun_authorized"]:
    raise RuntimeError("rerun unexpectedly authorized")

frozen = {
    "dataset_generation_results_design":
        ROOT / "comparator_benchmark_dataset_generation_v1_results_design.json",
    "dataset_generation_results_ledger":
        ROOT / "comparator_benchmark_dataset_generation_v1_results.sha256",
    "scenario_matrix":
        ROOT / "comparator_benchmark_execution_v1_scenario_matrix.tsv",
    "method_matrix":
        ROOT / "comparator_benchmark_execution_v1_method_matrix.tsv",
    "adapters":
        ROOT / "comparator_benchmark_execution_v1_impl/adapters.py",
    "environment_recipes":
        ROOT / "comparator_benchmark_execution_v1_impl/environment_recipes.json",
    "metrics":
        ROOT / "comparator_benchmark_execution_v1_impl/metrics.py",
    "source_pins":
        ROOT / "comparator_benchmark_execution_v1_impl/source_pins.tsv",
    "treetime_homoplasy_amendment_manifest":
        ROOT / "comparator_benchmark_execution_v1_treetime_homoplasy_amendment_manifest.json",
}

for name, path in frozen.items():
    expected = a["frozen_artifacts"][name + "_sha256"]
    observed = sha256(path)
    if observed != expected:
        raise RuntimeError(
            f"frozen artifact changed: {name}: {observed} != {expected}"
        )

head = subprocess.check_output(
    ["git", "rev-parse", "HEAD"],
    cwd=ROOT,
    text=True,
).strip()

ancestor_check = subprocess.run(
    ["git", "merge-base", "--is-ancestor", EXPECTED_PARENT, head],
    cwd=ROOT,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
if ancestor_check.returncode != 0:
    raise RuntimeError(
        f"authorization parent is not an ancestor of current HEAD: "
        f"{EXPECTED_PARENT} -> {head}"
    )

if "Truth may only be" not in MD.read_text():
    raise RuntimeError("authorization markdown truth boundary absent")

print("PASS | runner implementation authorization validates")
print("PASS | authorization parent commit is an ancestor of current HEAD")
print("PASS | frozen dataset/design/implementation identities match")
print("PASS | implementation restricted to three new runner artifacts")
print("PASS | canonical benchmark execution remains unauthorized")
print("PASS | third-party comparator execution remains unauthorized")
print("PASS | benchmark truth access remains unauthorized")
print("PASS | frozen scientific contracts remain immutable")
print(
    "PASS | next gate = "
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_RUNNER_V1"
)
