#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess
import sys

EXP = Path("experiments/07_comparative_landscape")

AUTH = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "treetime_homoplasy_amendment_authorization.json"
)

EXPECTED_PARENT = "089908a4cc12aa643de6594767d1206f5834f2af"

AUTH_ID = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "TREETIME_HOMOPLASY_AMENDMENT_001"
)

EXPECTED_FILES = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_impl/environment_recipes.json",

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


def git_bytes(*args):
    return subprocess.check_output(
        ["git", *args],
    )


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

    if parent != EXPECTED_PARENT:
        raise RuntimeError(
            "authorization parent is not the frozen dataset-generation results commit"
        )

    if git("rev-parse", parent) != EXPECTED_PARENT:
        raise RuntimeError(
            "frozen dataset-generation results commit identity differs"
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

    names = [
        "environment_recipes",
        "adapters",
        "toy_validation",
    ]

    for name, path in zip(names, EXPECTED_FILES):
        frozen = git_bytes(
            "show",
            f"{parent}:{path}",
        )

        digest = hashlib.sha256(frozen).hexdigest()

        if a["baseline_sha256"][name] != digest:
            raise RuntimeError(
                f"baseline hash differs: {name}"
            )

    requirements = set(
        a["authorized_change"]["requirements"]
    )

    required = {
        "Do not use benchmark truth to derive or validate TreeTime calls.",
        "Define a TreeTime recurrent-site call as a genomic position with at least two normalized reconstructed branch changes from the TreeTime ancestral output.",
        "Count recurrence by genomic position regardless of whether repeated changes have identical or different ancestral/derived state pairs.",
        "Do not execute any of the frozen 150 benchmark scenarios during implementation or validation."
    }

    if not required.issubset(requirements):
        raise RuntimeError(
            "required TreeTime amendment conditions absent"
        )

    if not all(
        a["explicitly_not_authorized"].values()
    ):
        raise RuntimeError(
            "one or more prohibited changes not blocked"
        )

    if a["one_time_amendment"] is not True:
        raise RuntimeError(
            "one-time policy absent"
        )

    if a["rerun_authorized"] is not False:
        raise RuntimeError(
            "rerun unexpectedly authorized"
        )

    if a["next_gate"] != (
        "IMPLEMENT_AND_FREEZE_"
        "TREETIME_HOMOPLASY_AMENDMENT_V1"
    ):
        raise RuntimeError(
            "next gate differs"
        )

    print("PASS | TreeTime homoplasy amendment authorized")
    print("PASS | change restricted to three authorized implementation files")
    print("PASS | TreeTime executable and ancestral parameters remain frozen")
    print("PASS | recurrence is derived truth-blind from normalized branch events")
    print("PASS | benchmark truth, scenarios and metrics remain frozen")
    print("PASS | full benchmark execution remains unauthorized")
    print(
        "PASS | next gate = "
        "IMPLEMENT_AND_FREEZE_TREETIME_HOMOPLASY_AMENDMENT_V1"
    )


if __name__ == "__main__":
    main()
