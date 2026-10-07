#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]

AUTH = ROOT / (
    "comparator_benchmark_execution_v1_"
    "runner_implementation_v2_authorization.json"
)

MD = ROOT / (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "RUNNER_IMPLEMENTATION_V2_AUTHORIZATION.md"
)

EXPECTED_PARENT = "05312d6ddbb216731631fb203817d2e17f2e5204"

PATHS = {
    "dataset_results_design":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_dataset_generation_v1_results_design.json",
    "dataset_results_sha256":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_dataset_generation_v1_results.sha256",
    "adapters":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/adapters.py",
    "environment_recipes":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/environment_recipes.json",
    "toy_validation":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/toy_validation.py",
    "metrics":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/metrics.py",
    "scenario_matrix":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_scenario_matrix.tsv",
    "method_matrix":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_method_matrix.tsv",
    "source_pins":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/source_pins.tsv",
    "treetime_homoplasy_manifest":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_treetime_homoplasy_amendment_manifest.json",
    "output_normalization_manifest":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_output_normalization_amendment_manifest.json",
    "output_normalization_freeze":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_output_normalization_amendment_freeze.py",
}

EXPECTED_FILES = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_runner.py",
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_runner_validation.py",
    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION.md",
]

def digest(data):
    return hashlib.sha256(data).hexdigest()

a = json.loads(AUTH.read_text())

if a["authorization_id"] != (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "RUNNER_IMPLEMENTATION_V2_001"
):
    raise RuntimeError("authorization id differs")

if a["status"] != "AUTHORIZED_NOT_YET_CONSUMED":
    raise RuntimeError("authorization status differs")

if a["parent_commit"] != EXPECTED_PARENT:
    raise RuntimeError("authorization parent differs")

if a["triggering_gate"] != (
    "REAUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V2"
):
    raise RuntimeError("triggering gate differs")

if a["authorized_files"] != EXPECTED_FILES:
    raise RuntimeError("authorized runner file set differs")

if a["next_gate"] != (
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_RUNNER_V2"
):
    raise RuntimeError("next gate differs")

if not a["one_time_runner_implementation_authorization"]:
    raise RuntimeError("one-time authorization flag absent")

if a["rerun_authorized"]:
    raise RuntimeError("runner rerun unexpectedly authorized")

old = a["supersedes_unconsumed_authorization"]
if old["authorization_id"] != (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION_001"
):
    raise RuntimeError("superseded authorization id differs")

if old["consumed"]:
    raise RuntimeError("runner authorization v1 recorded as consumed")

if not old["must_not_be_consumed"]:
    raise RuntimeError("runner authorization v1 supersession absent")

required_denials = [
    "canonical_benchmark_execution",
    "third_party_comparator_execution",
    "benchmark_truth_access_for_runner_implementation",
    "benchmark_truth_debugging",
    "benchmark_dataset_mutation",
    "scenario_definition_change",
    "method_matrix_change",
    "adapter_change",
    "environment_recipe_change",
    "metric_change",
    "source_pin_change",
    "comparator_version_change",
    "comparator_parameter_change",
    "generator_change",
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
            f"frozen parent identity differs: "
            f"{name}: {observed} != {expected}"
        )

norm = a["frozen_normalization_contracts"]

if norm["PastML"]["node_mapping"] != (
    "map_node_sequences_by_descendant_tips"
):
    raise RuntimeError("PastML node-mapping contract differs")

if norm["PastML"]["event_normalization"] != (
    "events_from_projected_node_sequences"
):
    raise RuntimeError("PastML event-normalization contract differs")

if norm["SNPPar"]["recurrent_site_normalizer"] != (
    "snppar_recurrent_sites_from_branch_events"
):
    raise RuntimeError("SNPPar recurrence contract differs")

if norm["TreeTime"]["recurrent_site_normalizer"] != (
    "treetime_recurrent_sites_from_branch_events"
):
    raise RuntimeError("TreeTime recurrence contract differs")

if norm["TreeTime"]["homoplasy_cli_scored"] is not False:
    raise RuntimeError("TreeTime homoplasy CLI boundary differs")

text = MD.read_text()

for required in (
    "Runner implementation authorization v1 was never consumed",
    "No canonical benchmark truth may be read",
    "No third-party comparator may be executed",
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_RUNNER_V2",
):
    if required not in text:
        raise RuntimeError(
            f"authorization documentation missing: {required}"
        )

print("PASS | runner implementation v2 authorization validates")
print("PASS | authorization parent commit is an ancestor of current HEAD")
print("PASS | frozen dataset/design/implementation identities match")
print("PASS | output-normalization amendment identities pinned")
print("PASS | runner authorization v1 remains unconsumed and superseded")
print("PASS | implementation restricted to three new runner artifacts")
print("PASS | canonical benchmark execution remains unauthorized")
print("PASS | third-party comparator execution remains unauthorized")
print("PASS | benchmark truth access remains unauthorized")
print("PASS | frozen scientific contracts remain immutable")
print(
    "PASS | next gate = "
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_RUNNER_V2"
)
