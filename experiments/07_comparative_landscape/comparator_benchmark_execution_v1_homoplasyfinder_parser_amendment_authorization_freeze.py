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
      "homoplasyfinder_parser_amendment_authorization.json"
)

PREVIOUS = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "homoplasyfinder_cli_amendment_freeze.py"
)

AUTH_ID = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "HOMOPLASYFINDER_PARSER_AMENDMENT_001"
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

    cp = subprocess.run(
        [sys.executable, str(PREVIOUS)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if cp.returncode != 0:
        raise RuntimeError(
            "preceding HomoplasyFinder CLI amendment no longer validates:\n"
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

    for name, path in {
        "adapters": EXPECTED_FILES[0],
        "toy_validation": EXPECTED_FILES[1],
    }.items():
        frozen = git_bytes(
            "show",
            f"{parent}:{path}",
        )

        digest = hashlib.sha256(frozen).hexdigest()

        if a["baseline_sha256"][name] != digest:
            raise RuntimeError(
                f"baseline hash differs: {name}"
            )

    c = a["authorized_change"]

    if c["function"] != "parse_homoplasyfinder_report":
        raise RuntimeError(
            "authorized parser function differs"
        )

    required = {
        "Recognize the HomoplasyFinder MinimumNumberChangesOnTree column.",
        "Retain the existing ConsistencyIndex filtering behaviour.",
        "If the count column is absent or the value is empty, preserve "
        "the existing empty-string representation.",
    }

    observed = set(c["requirements"])

    if not required.issubset(observed):
        raise RuntimeError(
            "required parser conditions absent"
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
        "HOMOPLASYFINDER_PARSER_AMENDMENT_V1"
    ):
        raise RuntimeError(
            "next gate differs"
        )

    print("PASS | HomoplasyFinder parser amendment authorized")
    print("PASS | change restricted to parser and focused toy validation")
    print("PASS | reported minimum-change count must be preserved when available")
    print("PASS | existing consistency-index filtering remains frozen")
    print("PASS | HomoplasyFinder executable and recipe remain frozen")
    print("PASS | benchmark truth and metrics remain frozen")
    print("PASS | full benchmark execution remains unauthorized")
    print(
        "PASS | next gate = "
        "IMPLEMENT_AND_FREEZE_HOMOPLASYFINDER_PARSER_AMENDMENT_V1"
    )


if __name__ == "__main__":
    main()
