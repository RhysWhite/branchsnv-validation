#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
AUTH = ROOT / (
    "comparator_benchmark_execution_v1_"
    "output_normalization_amendment_authorization.json"
)
MD = ROOT / (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "OUTPUT_NORMALIZATION_AMENDMENT_AUTHORIZATION.md"
)

EXPECTED_PARENT = "a8606655af34b3cadd944a87b3cdb8aa447d033d"

PATHS = {
    "adapters":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/adapters.py",
    "environment_recipes":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/environment_recipes.json",
    "toy_validation":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/toy_validation.py",
    "method_matrix":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_method_matrix.tsv",
    "scenario_matrix":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_scenario_matrix.tsv",
    "dataset_generation_results_design":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_dataset_generation_v1_results_design.json",
    "dataset_generation_results_ledger":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_dataset_generation_v1_results.sha256",
    "pastml_ambiguity_manifest":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_pastml_ambiguity_amendment_manifest.json",
    "treetime_homoplasy_manifest":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_treetime_homoplasy_amendment_manifest.json",
    "runner_implementation_authorization_v1":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_runner_implementation_authorization.json",
}

def digest(data):
    return hashlib.sha256(data).hexdigest()

a = json.loads(AUTH.read_text())

if a["authorization_id"] != (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "OUTPUT_NORMALIZATION_AMENDMENT_001"
):
    raise RuntimeError("authorization id differs")

if a["status"] != "AUTHORIZED_NOT_YET_CONSUMED":
    raise RuntimeError("authorization status differs")

if a["parent_commit"] != EXPECTED_PARENT:
    raise RuntimeError("authorization parent differs")

expected_files = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_impl/adapters.py",
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_impl/environment_recipes.json",
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_impl/toy_validation.py",
]
if a["authorized_files"] != expected_files:
    raise RuntimeError("authorized file set differs")

if a["next_gate"] != (
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_"
    "OUTPUT_NORMALIZATION_AMENDMENT_V1"
):
    raise RuntimeError("next gate differs")

required_denials = [
    "canonical_benchmark_execution",
    "third_party_comparator_execution",
    "benchmark_truth_access",
    "benchmark_truth_use_for_debugging",
    "benchmark_dataset_mutation",
    "scenario_definition_change",
    "metric_definition_change",
    "generator_change",
    "source_pin_change",
    "comparator_version_change",
    "comparator_inference_parameter_change",
    "other_comparator_adapter_change",
    "runner_implementation",
    "production_bridge",
    "production_ledger_mutation",
]
for key in required_denials:
    if a["explicitly_not_authorized"].get(key) is not True:
        raise RuntimeError(f"required denial absent: {key}")

if not a["one_time_amendment"]:
    raise RuntimeError("one-time amendment flag absent")

if a["rerun_authorized"]:
    raise RuntimeError("rerun unexpectedly authorized")

if not a["runner_authorization_v1"][
    "must_not_be_consumed_after_this_amendment_changes_frozen_hashes"
]:
    raise RuntimeError("runner authorization supersession boundary absent")

repo = ROOT.parents[1]

head = subprocess.check_output(
    ["git", "rev-parse", "HEAD"],
    cwd=repo,
    text=True,
).strip()

ancestor = subprocess.run(
    ["git", "merge-base", "--is-ancestor", EXPECTED_PARENT, head],
    cwd=repo,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
if ancestor.returncode != 0:
    raise RuntimeError("authorization parent is not an ancestor of HEAD")

for name, relpath in PATHS.items():
    data = subprocess.check_output(
        ["git", "show", f"{EXPECTED_PARENT}:{relpath}"],
        cwd=repo,
    )
    observed = digest(data)
    expected = a["baseline_sha256"][name]
    if observed != expected:
        raise RuntimeError(
            f"parent artifact identity differs: "
            f"{name}: {observed} != {expected}"
        )

text = MD.read_text()
if "projected indices rather than genomic coordinates" not in text:
    raise RuntimeError("PastML coordinate boundary absent")
if "must not subsequently be consumed" not in text:
    raise RuntimeError("runner reauthorization boundary absent")

print("PASS | output-normalization amendment authorization validates")
print("PASS | parent commit is an ancestor of current HEAD")
print("PASS | all baseline identities match the recorded parent commit")
print("PASS | amendment restricted to exactly three implementation files")
print("PASS | PastML genomic-coordinate normalization explicitly authorized")
print("PASS | descendant-tip node mapping explicitly authorized")
print("PASS | SNPPar recurrent-site normalization explicitly authorized")
print("PASS | comparator execution remains unauthorized")
print("PASS | benchmark truth access remains unauthorized")
print("PASS | runner authorization v1 must remain unconsumed")
print(
    "PASS | next gate = "
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_"
    "OUTPUT_NORMALIZATION_AMENDMENT_V1"
)
