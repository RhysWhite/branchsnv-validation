#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess
import sys

PARENT = "f48bd14048866820c7a252d935ed2d26cb9407e5"

EXP = Path("experiments/07_comparative_landscape")
IMPL_VALIDATOR = EXP / "comparator_benchmark_execution_v1_implementation_freeze.py"
AUTH_JSON = EXP / "comparator_benchmark_execution_v1_environment_smoke_authorization.json"

AUTHORIZATION_ID = "COMPARATOR_BENCHMARK_EXECUTION_V1_ENVIRONMENT_SMOKE_001"

METHODS = {
    "ARPIP",
    "FastML",
    "HomoplasyFinder",
    "PAML",
    "POUTINE",
    "PastML",
    "SNPPar",
    "TreeTime",
}

REQUIRED_SCOPE = {
    "environment_build_authorized",
    "exact_pinned_source_checkout_authorized",
    "networked_dependency_install_authorized",
    "third_party_software_installation_authorized",
    "noncanonical_smoke_execution_authorized",
    "third_party_software_execution_noncanonical_smoke_only",
    "cli_help_capture_authorized",
    "environment_metadata_capture_authorized",
    "command_stdout_stderr_capture_authorized",
    "input_output_adapter_smoke_validation_authorized",
    "poutine_cli_resolution_authorized",
    "pastml_machine_readable_output_resolution_authorized",
}

REQUIRED_BLOCKS = {
    "canonical_150_scenario_dataset_generation",
    "canonical_benchmark_execution",
    "canonical_truth_unblinding_for_tuning",
    "parameter_tuning_against_canonical_truth",
    "frozen_benchmark_design_mutation",
    "frozen_source_pin_mutation",
    "production_bridge",
    "production_ledger_mutation",
    "third_party_source_or_binary_redistribution",
    "third_party_source_patching_without_separate_amendment",
}


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def main():
    head = git("rev-parse", "HEAD")

    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PARENT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError(
            "repository is not at or descended from frozen implementation HEAD"
        )

    subprocess.run(
        [sys.executable, str(IMPL_VALIDATOR)],
        check=True
    )

    auth = json.loads(AUTH_JSON.read_text(encoding="utf-8"))

    if auth["authorization_id"] != AUTHORIZATION_ID:
        raise RuntimeError("authorization id differs")

    if auth["status"] not in {
        "AUTHORIZED_NOT_YET_CONSUMED",
        "AUTHORIZED_CONSUMED",
    }:
        raise RuntimeError("authorization status differs")

    if auth["parent_implementation_freeze_commit"] != PARENT:
        raise RuntimeError("authorization parent differs")

    if set(auth["method_universe"]) != METHODS:
        raise RuntimeError("authorized method universe differs")

    if set(auth["scope"]) != REQUIRED_SCOPE:
        raise RuntimeError("authorization scope key set differs")

    if not all(auth["scope"].values()):
        raise RuntimeError("one or more required smoke authorities are false")

    if set(auth["explicitly_not_authorized"]) != REQUIRED_BLOCKS:
        raise RuntimeError("explicit prohibition key set differs")

    if not all(auth["explicitly_not_authorized"].values()):
        raise RuntimeError("one or more forbidden activities not blocked")

    if auth["one_time_environment_smoke_authorization"] is not True:
        raise RuntimeError("one-use smoke authorization absent")

    if auth["rerun_authorized"] is not False:
        raise RuntimeError("smoke rerun unexpectedly authorized")

    if auth["next_gate_after_environment_smoke"] != \
       "FREEZE_COMPARATOR_BENCHMARK_ENVIRONMENT_AND_SMOKE_RESULTS_V1":
        raise RuntimeError("next gate differs")

    req = "\n".join(auth["requirements"])

    for phrase in (
        "noncanonical toy",
        "canonical 150-scenario",
        "POUTINE",
        "PastML",
        "stdout",
        "stderr",
        "separately frozen",
    ):
        if phrase not in req:
            raise RuntimeError(
                f"required authorization safeguard absent: {phrase}"
            )

    print("PASS | comparator environment-build + smoke authorization validates")
    print("PASS | exact 8-method frozen universe")
    print("PASS | isolated environment construction authorized")
    print("PASS | pinned-source/dependency network retrieval authorized")
    print("PASS | third-party execution restricted to noncanonical smoke fixtures")
    print("PASS | POUTINE CLI resolution authorized")
    print("PASS | PastML machine-readable output resolution authorized")
    print("PASS | canonical 150-scenario generation remains unauthorized")
    print("PASS | canonical benchmark execution remains unauthorized")
    print("PASS | frozen design and source pins remain immutable")
    print("PASS | production bridge remains unauthorized")
    print(
        "PASS | next gate = "
        "FREEZE_COMPARATOR_BENCHMARK_ENVIRONMENT_AND_SMOKE_RESULTS_V1"
    )


if __name__ == "__main__":
    main()
