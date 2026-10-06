#!/usr/bin/env python3

from pathlib import Path
import json
import subprocess
import sys

EXP = Path("experiments/07_comparative_landscape")

AUTH = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "snppar_reference_fixture_amendment_authorization.json"
)

PREVIOUS = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "snppar_environment_amendment_freeze.py"
)

AUTH_ID = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "SNPPAR_REFERENCE_FIXTURE_AMENDMENT_001"
)

EXPECTED_FILES = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_impl/adapters.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_impl/toy_validation.py",
]


def git(*args):
    return subprocess.check_output(
        ["git", *args],
        text=True,
    ).strip()


def main():
    a = json.loads(
        AUTH.read_text(encoding="utf-8")
    )

    parent = a["parent_commit"]
    head = git("rev-parse", "HEAD")

    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", parent, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError(
            "repository is not descended from authorization parent"
        )

    cp = subprocess.run(
        [sys.executable, str(PREVIOUS)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if cp.returncode != 0:
        raise RuntimeError(
            "preceding SNPPar environment amendment no longer validates:\n"
            + cp.stdout
        )

    if a["authorization_id"] != AUTH_ID:
        raise RuntimeError("authorization id differs")

    if a["status"] not in {
        "AUTHORIZED_NOT_YET_CONSUMED",
        "AUTHORIZED_CONSUMED",
    }:
        raise RuntimeError("authorization status differs")

    if a["authorized_files"] != EXPECTED_FILES:
        raise RuntimeError("authorized file set differs")

    change = a["authorized_change"]

    if change["adapter_function"] != "minimal_genbank_text":
        raise RuntimeError("authorized adapter function differs")

    required_phrases = (
        "Require the scenario variable positions as an input.",
        "Preserve the root nucleotide sequence exactly.",
        "Preserve all variable-site coordinates exactly.",
        "Emit exactly one synthetic CDS feature at that interval.",
        "Do not place any benchmark variable position inside the synthetic CDS.",
    )

    requirements = set(change["requirements"])

    for phrase in required_phrases:
        if phrase not in requirements:
            raise RuntimeError(
                f"required amendment condition absent: {phrase}"
            )

    dims = a["triggering_observations"]["benchmark_dimensions"]

    if dims != {
        "root_sequence_length_bp": 10000,
        "variable_positions_per_scenario": 40,
    }:
        raise RuntimeError("benchmark dimensions differ")

    if (
        a["triggering_observations"]["source_pin"]
        != "0386df8edcff26faf242bc268c5f8865b09c9de9"
    ):
        raise RuntimeError("SNPPar source pin differs")

    if not all(
        a["explicitly_not_authorized"].values()
    ):
        raise RuntimeError(
            "one or more prohibited changes not blocked"
        )

    if a["one_time_amendment"] is not True:
        raise RuntimeError("one-time policy absent")

    if a["rerun_authorized"] is not False:
        raise RuntimeError("rerun unexpectedly authorized")

    if a["next_gate"] != (
        "IMPLEMENT_AND_FREEZE_SNPPAR_"
        "REFERENCE_FIXTURE_AMENDMENT_V1"
    ):
        raise RuntimeError("next gate differs")

    print("PASS | preceding SNPPar environment amendment remains valid")
    print("PASS | SNPPar reference-fixture amendment authorized")
    print("PASS | change restricted to adapter and focused toy validation")
    print("PASS | root sequence must remain unchanged")
    print("PASS | variable-site coordinates must remain unchanged")
    print("PASS | synthetic CDS must avoid every variable position")
    print("PASS | SNPPar source and environment remain frozen")
    print("PASS | benchmark truth and metrics remain frozen")
    print("PASS | full benchmark execution remains unauthorized")
    print(
        "PASS | next gate = "
        "IMPLEMENT_AND_FREEZE_SNPPAR_REFERENCE_FIXTURE_AMENDMENT_V1"
    )


if __name__ == "__main__":
    main()
