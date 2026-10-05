#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import subprocess
import sys

PARENT = "1dabd7bd514dbb97b7eea523e4e5f0e45b7e32fb"
EXP = Path("experiments/07_comparative_landscape")
DESIGN_VALIDATOR = EXP / "comparator_benchmark_execution_v1_design_freeze.py"
DESIGN_JSON = EXP / "comparator_benchmark_execution_v1_design.json"
AUTH_JSON = EXP / "comparator_benchmark_execution_v1_implementation_authorization.json"

EXPECTED_DESIGN_JSON_SHA = "1306af08f69d27a80990203bd7d803d2c907a1cdeb56bfd2fe0174bf4a416cde"
AUTHORIZATION_ID = "COMPARATOR_BENCHMARK_EXECUTION_V1_IMPLEMENTATION_001"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

def main():
    head = git("rev-parse", "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PARENT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError("repository is not at/descended from implementation-authorization parent")

    subprocess.run([sys.executable, str(DESIGN_VALIDATOR)], check=True)

    if sha(DESIGN_JSON) != EXPECTED_DESIGN_JSON_SHA:
        raise RuntimeError("benchmark execution design JSON SHA differs")

    auth = json.loads(AUTH_JSON.read_text(encoding="utf-8"))

    if auth["authorization_id"] != AUTHORIZATION_ID:
        raise RuntimeError("authorization id differs")
    if auth["status"] not in {"AUTHORIZED_NOT_YET_CONSUMED", "AUTHORIZED_CONSUMED"}:
        raise RuntimeError("authorization status differs")
    if auth["scope"]["implementation_authorized"] is not True:
        raise RuntimeError("implementation authority absent")

    required = [
        "canonical_generator_implementation_authorized",
        "truth_blind_metric_engine_implementation_authorized",
        "input_adapter_implementation_authorized",
        "output_adapter_implementation_authorized",
        "environment_recipe_authoring_authorized",
        "exact_version_and_source_pin_research_authorized",
        "noncanonical_toy_fixture_generation_authorized",
        "unit_test_authoring_authorized",
        "static_validation_authorized",
    ]
    for key in required:
        if auth["scope"][key] is not True:
            raise RuntimeError(f"required implementation authority false: {key}")

    if not all(auth["explicitly_not_authorized"].values()):
        raise RuntimeError("one or more forbidden execution activities not explicitly blocked")

    if auth["one_time_implementation_freeze"] is not True:
        raise RuntimeError("one-time implementation-freeze policy absent")
    if auth["rerun_authorized"] is not False:
        raise RuntimeError("rerun unexpectedly authorized")

    print("PASS | comparator benchmark execution implementation authorization validates")
    print("PASS | implementation of generator/adapters/metrics/recipes authorized")
    print("PASS | exact-version/source-pin research authorized")
    print("PASS | noncanonical toy fixtures + unit tests authorized")
    print("PASS | third-party install/execution remains unauthorized")
    print("PASS | canonical 150-scenario generation remains unauthorized")
    print("PASS | canonical benchmark execution remains unauthorized")
    print("PASS | production bridge remains unauthorized")

if __name__ == "__main__":
    main()
