#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]

AUTH = ROOT / (
    "comparator_benchmark_execution_v1_"
    "runner_implementation_v3_authorization.json"
)

MD = ROOT / (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "RUNNER_IMPLEMENTATION_V3_AUTHORIZATION.md"
)

EXPECTED_PARENT = "7cc3cac6bd7a70843f494354c262eedba5e4ab66"

EXPECTED_ADAPTERS = (
    "5c4e8d95fa104882952116e35c060df0f6bff87547fc9cae7c838b7247eaa49d"
)

EXPECTED_TOY = (
    "7058dd7f8a490274cb49c49109b892923613f59916f77d7fa736926d92b5eb03"
)

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
        "comparator_benchmark_execution_v1_"
        "treetime_homoplasy_amendment_manifest.json",

    "output_normalization_manifest":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "output_normalization_amendment_manifest.json",

    "output_normalization_freeze":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "output_normalization_amendment_freeze.py",

    "poutine_map_serialization_manifest":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "poutine_map_serialization_amendment_manifest.json",

    "poutine_map_serialization_freeze":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "poutine_map_serialization_amendment_freeze.py",
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
    "RUNNER_IMPLEMENTATION_V3_001"
):
    raise RuntimeError("authorization id differs")

if a["status"] != "AUTHORIZED_NOT_YET_CONSUMED":
    raise RuntimeError("authorization status differs")

if a["parent_commit"] != EXPECTED_PARENT:
    raise RuntimeError("authorization parent differs")

if a["triggering_gate"] != (
    "REAUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V3"
):
    raise RuntimeError("triggering gate differs")

if a["authorized_files"] != EXPECTED_FILES:
    raise RuntimeError("authorized runner file set differs")

if a["next_gate"] != (
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_RUNNER_V3"
):
    raise RuntimeError("next gate differs")

if not a["one_time_runner_implementation_authorization"]:
    raise RuntimeError("one-time authorization flag absent")

if a["rerun_authorized"]:
    raise RuntimeError("runner rerun unexpectedly authorized")

superseded = a["superseded_unconsumed_runner_authorizations"]

if len(superseded) != 2:
    raise RuntimeError("superseded runner authorization count differs")

expected_superseded = {
    (
        "COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION_001",
        "a8606655af34b3cadd944a87b3cdb8aa447d033d",
    ),
    (
        "COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION_V2_001",
        "8c7c68715e2d2caa26e4115e9c4f315825d0932f",
    ),
}

observed_superseded = {
    (x["authorization_id"], x["commit"])
    for x in superseded
}

if observed_superseded != expected_superseded:
    raise RuntimeError("superseded authorization identities differ")

for item in superseded:
    if item["consumed"]:
        raise RuntimeError(
            f"superseded runner authorization consumed: "
            f"{item['authorization_id']}"
        )

    if not item["must_not_be_consumed"]:
        raise RuntimeError(
            f"supersession boundary absent: "
            f"{item['authorization_id']}"
        )

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

if a["baseline_sha256"]["adapters"] != EXPECTED_ADAPTERS:
    raise RuntimeError("final adapters hash differs")

if a["baseline_sha256"]["toy_validation"] != EXPECTED_TOY:
    raise RuntimeError("final toy-validation hash differs")

required = a["required_final_identities"]

if required["adapters"] != EXPECTED_ADAPTERS:
    raise RuntimeError("required final adapters identity differs")

if required["toy_validation"] != EXPECTED_TOY:
    raise RuntimeError("required final toy-validation identity differs")

if required["poutine_map_serialization_freeze_commit"] != EXPECTED_PARENT:
    raise RuntimeError("POUTINE map freeze commit identity differs")

norm = a["frozen_normalization_contracts"]

if norm["PastML"]["node_mapping"] != (
    "map_node_sequences_by_descendant_tips"
):
    raise RuntimeError("PastML node mapping contract differs")

if norm["PastML"]["event_normalization"] != (
    "events_from_projected_node_sequences"
):
    raise RuntimeError("PastML event normalization contract differs")

if norm["POUTINE"]["physical_positions_map"] != (
    "poutine_physical_positions_map_text"
):
    raise RuntimeError("POUTINE map adapter contract differs")

if norm["POUTINE"]["physical_positions_map_format"] != (
    "1<TAB>markerN<TAB>0<TAB>GENOMIC_POSITION"
):
    raise RuntimeError("POUTINE map format differs")

if norm["POUTINE"]["output_parser"] != "parse_poutine_result":
    raise RuntimeError("POUTINE output-parser contract differs")

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

for required_text in (
    "Runner implementation authorizations v1 and v2 were never consumed",
    "poutine_physical_positions_map_text()",
    "No canonical benchmark truth may be read",
    "No third-party comparator may be executed",
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_RUNNER_V3",
):
    if required_text not in text:
        raise RuntimeError(
            f"authorization documentation missing: {required_text}"
        )

print("PASS | runner implementation v3 authorization validates")
print("PASS | authorization parent commit is an ancestor of current HEAD")
print("PASS | complete frozen dataset/design identities match")
print("PASS | final adapters identity pinned")
print("PASS | POUTINE map-serialization freeze identity pinned")
print("PASS | output-normalization identities pinned")
print("PASS | runner-v1 remains unconsumed and superseded")
print("PASS | runner-v2 remains unconsumed and superseded")
print("PASS | implementation restricted to three new runner artifacts")
print("PASS | canonical benchmark execution remains unauthorized")
print("PASS | third-party comparator execution remains unauthorized")
print("PASS | benchmark truth access remains unauthorized")
print("PASS | scientific adapter and metric contracts remain immutable")
print(
    "PASS | next gate = "
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_RUNNER_V3"
)
