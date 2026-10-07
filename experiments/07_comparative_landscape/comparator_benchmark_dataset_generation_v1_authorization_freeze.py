#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

PARENT = "359e6881ef77485372579e90b59ca2ca527b5f38"

EXP = Path("experiments/07_comparative_landscape")
IMPL = EXP / "comparator_benchmark_execution_v1_impl"

AUTH_JSON = EXP / "comparator_benchmark_dataset_generation_v1_authorization.json"
AUTH_RECORD = EXP / "COMPARATOR_BENCHMARK_DATASET_GENERATION_V1_AUTHORIZATION.md"
HARNESS = EXP / "comparator_benchmark_dataset_generation_v1.py"

SMOKE_VALIDATOR = EXP / "comparator_benchmark_environment_smoke_v1_results_freeze.py"

DESIGN = EXP / "comparator_benchmark_execution_v1_design.json"
SCENARIOS = EXP / "comparator_benchmark_execution_v1_scenario_matrix.tsv"
GENERATOR = IMPL / "generator.py"
ADAPTERS = IMPL / "adapters.py"
SMOKE_ANCHOR = EXP / "comparator_benchmark_environment_smoke_v1_results.sha256"

AUTHORIZATION_ID = "COMPARATOR_BENCHMARK_DATASET_GENERATION_V1_001"

EXPECTED_SHA256 = {
    DESIGN: "1306af08f69d27a80990203bd7d803d2c907a1cdeb56bfd2fe0174bf4a416cde",
    SCENARIOS: "8e569a6fbad769de0aed087e882410f6f1dd7114cb060e13a956159ae0b39398",
    GENERATOR: "229ed49c541023d6d439967ca184dd82430a4b3592d42657131fac08c9f3f560",
    ADAPTERS: "c4d351b041c68d9d1a142e3f532d353042374b416f5d03da29378a79672779e5",
    HARNESS: "92d3558a56ae04341d2be65d20c76f9cdb1e69b2442d0df733eda0260905b9e4",
    SMOKE_ANCHOR: "1522ecb1b49bba2f09b960a74924c1d8b3e58a48ee9afcf9e1046b2d76e5882b",
    AUTH_JSON: "d3a25f9dc0f18037f064db0bf9dd8b4055190f5fc2ae3126cf4e3f1c029f7e1a",
    AUTH_RECORD: "319cedc62873a5c16c08755bb25a39a264a4e44fff2294bbea78970ba783ddf6",
}

EXPECTED_FROZEN_ARTIFACTS = {
    "benchmark_design_sha256": EXPECTED_SHA256[DESIGN],
    "scenario_matrix_sha256": EXPECTED_SHA256[SCENARIOS],
    "generator_sha256": EXPECTED_SHA256[GENERATOR],
    "adapters_sha256": EXPECTED_SHA256[ADAPTERS],
    "generation_harness_sha256": EXPECTED_SHA256[HARNESS],
    "environment_smoke_results_anchor_sha256": EXPECTED_SHA256[SMOKE_ANCHOR],
}

REQUIRED_SCOPE = {
    "dataset_generation_authorized",
    "generation_harness_execution_authorized",
    "frozen_generator_execution_authorized",
    "frozen_adapter_serialization_authorized",
    "dataset_manifest_writing_authorized",
    "dataset_checksum_writing_authorized",
    "required_generation_guard_tokens_authorized",
}

REQUIRED_BLOCKS = {
    "benchmark_execution",
    "third_party_comparator_execution",
    "parameter_tuning_against_benchmark_truth",
    "benchmark_truth_use_for_debugging_comparators",
    "frozen_benchmark_design_mutation",
    "frozen_scenario_matrix_mutation",
    "frozen_generator_mutation",
    "frozen_adapter_mutation",
    "frozen_source_pin_mutation",
    "generation_harness_mutation_after_authorization_freeze",
    "production_bridge",
    "production_ledger_mutation",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def main() -> None:
    head = git("rev-parse", "HEAD")

    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PARENT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError("repository does not descend from smoke-result freeze")

    subprocess.run(
        [sys.executable, str(SMOKE_VALIDATOR)],
        check=True,
        stdout=subprocess.DEVNULL,
    )

    for path, expected in EXPECTED_SHA256.items():
        if sha256(path) != expected:
            raise RuntimeError(f"artifact identity differs: {path}")

    auth = json.loads(AUTH_JSON.read_text(encoding="utf-8"))

    if auth["authorization_id"] != AUTHORIZATION_ID:
        raise RuntimeError("authorization id differs")

    if auth["status"] not in {
        "AUTHORIZED_NOT_YET_CONSUMED",
        "AUTHORIZED_CONSUMED",
    }:
        raise RuntimeError("authorization status differs")

    if auth["parent_environment_smoke_results_commit"] != PARENT:
        raise RuntimeError("authorization parent differs")

    if auth["frozen_artifacts"] != EXPECTED_FROZEN_ARTIFACTS:
        raise RuntimeError("frozen artifact identities differ")

    if set(auth["scope"]) != REQUIRED_SCOPE:
        raise RuntimeError("authorization scope key set differs")

    if not all(auth["scope"].values()):
        raise RuntimeError("one or more required generation authorities are false")

    if set(auth["explicitly_not_authorized"]) != REQUIRED_BLOCKS:
        raise RuntimeError("explicit prohibition key set differs")

    if not all(auth["explicitly_not_authorized"].values()):
        raise RuntimeError("one or more forbidden activities are not blocked")

    if auth["one_time_dataset_generation_authorization"] is not True:
        raise RuntimeError("one-use generation authorization absent")

    if auth["rerun_authorized"] is not False:
        raise RuntimeError("generation rerun unexpectedly authorized")

    if auth["next_gate_after_dataset_generation"] != \
       "FREEZE_COMPARATOR_BENCHMARK_DATASET_GENERATION_RESULTS_V1":
        raise RuntimeError("next gate differs")

    env = os.environ.copy()
    env.pop("BRANCHSNV_BENCHMARK_DATASET_GENERATION_V1_AUTHORIZED", None)

    blocked = subprocess.run(
        [sys.executable, str(HARNESS)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    if blocked.returncode == 0:
        raise RuntimeError("generation harness did not fail closed")

    if "benchmark dataset generation is not authorized" not in blocked.stderr:
        raise RuntimeError("generation harness failed for an unexpected reason")

    print("PASS | dataset-generation authorization parent validates")
    print("PASS | upstream environment and smoke-result freeze validates")
    print("PASS | frozen design, scenario matrix, generator and adapters unchanged")
    print("PASS | generation harness identity validates")
    print("PASS | authorization scope and explicit prohibitions validate")
    print("PASS | one-use generation authority; rerun blocked")
    print("PASS | generation harness fails closed without authorization")
    print("PASS | comparator execution remains unauthorized")
    print("PASS | next gate = FREEZE_COMPARATOR_BENCHMARK_DATASET_GENERATION_RESULTS_V1")


if __name__ == "__main__":
    main()
