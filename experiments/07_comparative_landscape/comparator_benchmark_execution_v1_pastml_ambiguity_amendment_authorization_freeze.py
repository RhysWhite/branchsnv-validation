#!/usr/bin/env python3

from pathlib import Path
import json
import subprocess
import sys

PARENT = "423d0b1b98a207c4287aadf56ab28c18e5003f96"

EXP = Path("experiments/07_comparative_landscape")

SMOKE_AUTH_VALIDATOR = (
    EXP /
    "comparator_benchmark_execution_v1_"
    "environment_smoke_authorization_freeze.py"
)

AUTH = (
    EXP /
    "comparator_benchmark_execution_v1_"
    "pastml_ambiguity_amendment_authorization.json"
)

AUTH_ID = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "PASTML_AMBIGUITY_AMENDMENT_001"
)


def git(*args):
    return subprocess.check_output(
        ["git", *args],
        text=True
    ).strip()


def main():
    head = git("rev-parse", "HEAD")

    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PARENT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError(
            "repository is not descended from smoke authorization commit"
        )

    subprocess.run(
        [sys.executable, str(SMOKE_AUTH_VALIDATOR)],
        check=True
    )

    a = json.loads(AUTH.read_text(encoding="utf-8"))

    if a["authorization_id"] != AUTH_ID:
        raise RuntimeError("authorization id differs")

    if a["status"] not in {
        "AUTHORIZED_NOT_YET_CONSUMED",
        "AUTHORIZED_CONSUMED",
    }:
        raise RuntimeError("authorization status differs")

    if (
        a["parent_environment_smoke_authorization_commit"]
        != PARENT
    ):
        raise RuntimeError("authorization parent differs")

    change = a["authorized_change"]

    expected_file = (
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/adapters.py"
    )

    if change["file"] != expected_file:
        raise RuntimeError("authorized file differs")

    if change["function"] != "parse_tabular_node_states":
        raise RuntimeError("authorized function differs")

    rule = change["rule"]

    for phrase in (
        "Aggregate all rows by node and site",
        "exactly one distinct A/C/G/T state",
        "Encode the cell as N",
    ):
        if phrase not in rule:
            raise RuntimeError(
                f"required ambiguity rule absent: {phrase}"
            )

    if not all(a["explicitly_not_authorized"].values()):
        raise RuntimeError(
            "one or more prohibited activities not blocked"
        )

    if a["one_time_amendment"] is not True:
        raise RuntimeError("one-time amendment policy absent")

    if a["rerun_authorized"] is not False:
        raise RuntimeError("amendment rerun unexpectedly authorized")

    if a["next_gate"] != (
        "IMPLEMENT_AND_FREEZE_PASTML_"
        "AMBIGUITY_ADAPTER_AMENDMENT_V1"
    ):
        raise RuntimeError("next gate differs")

    print("PASS | PastML ambiguity-adapter amendment authorized")
    print("PASS | change restricted to parse_tabular_node_states")
    print("PASS | singleton nucleotide states retained")
    print("PASS | multi-state or absent calls must become N")
    print("PASS | no metric/truth/scenario changes authorized")
    print("PASS | PastML source/version/settings remain frozen")
    print("PASS | full benchmark execution remains unauthorized")
    print(
        "PASS | next gate = "
        "IMPLEMENT_AND_FREEZE_PASTML_AMBIGUITY_ADAPTER_AMENDMENT_V1"
    )


if __name__ == "__main__":
    main()
