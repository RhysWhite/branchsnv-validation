#!/usr/bin/env python3

from pathlib import Path
import json
import subprocess

EXP = Path("experiments/07_comparative_landscape")

AUTH = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "snppar_environment_amendment_authorization.json"
)

AUTH_ID = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "SNPPAR_ENVIRONMENT_AMENDMENT_001"
)

PREVIOUS_FREEZE_COMMIT = (
    "2d05249319fe976a373f1142672dbbfdf3bf48b3"
)

PREVIOUS_FROZEN_PATHS = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_impl/adapters.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "pastml_ambiguity_amendment_test.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "pastml_ambiguity_amendment_manifest.json",

    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "PASTML_AMBIGUITY_ADAPTER_AMENDMENT.md",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "pastml_ambiguity_amendment_freeze.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "pastml_ambiguity_amendment.sha256",
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
    head = git("rev-parse", "HEAD")

    if subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            PREVIOUS_FREEZE_COMMIT,
            head,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError(
            "repository is not descended from the preceding frozen amendment"
        )

    for path in PREVIOUS_FROZEN_PATHS:
        frozen = git_bytes(
            "show",
            f"{PREVIOUS_FREEZE_COMMIT}:{path}",
        )

        current = Path(path).read_bytes()

        if frozen != current:
            raise RuntimeError(
                f"preceding frozen artifact changed: {path}"
            )

    a = json.loads(
        AUTH.read_text(encoding="utf-8")
    )

    if a["authorization_id"] != AUTH_ID:
        raise RuntimeError("authorization id differs")

    if a["status"] not in {
        "AUTHORIZED_NOT_YET_CONSUMED",
        "AUTHORIZED_CONSUMED",
    }:
        raise RuntimeError("authorization status differs")

    if a["parent_commit"] != PREVIOUS_FREEZE_COMMIT:
        raise RuntimeError("authorization parent differs")

    change = a["authorized_change"]

    expected_file = (
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/"
        "environment_recipes.json"
    )

    if change["file"] != expected_file:
        raise RuntimeError("authorized file differs")

    if change["section"] != "methods.SNPPar":
        raise RuntimeError("authorized section differs")

    expected_env = {
        "python": "3.8.20",
        "biopython": "1.76",
        "phylo_treetime": "0.8.5",
        "ete3": "3.1.3",
        "disable_python_user_site": True,
    }

    if change["environment"] != expected_env:
        raise RuntimeError("authorized environment differs")

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
        "ENVIRONMENT_AMENDMENT_V1"
    ):
        raise RuntimeError("next gate differs")

    print("PASS | preceding PastML freeze remains byte-identical")
    print("PASS | SNPPar environment amendment authorized")
    print("PASS | change restricted to SNPPar environment recipe")
    print("PASS | Python 3.8.20 selected")
    print("PASS | Biopython 1.76 selected")
    print("PASS | TreeTime 0.8.5 retained")
    print("PASS | ETE3 3.1.3 selected")
    print("PASS | Python user-site packages must be disabled")
    print("PASS | SNPPar source revision remains frozen")
    print("PASS | full benchmark execution remains unauthorized")
    print(
        "PASS | next gate = "
        "IMPLEMENT_AND_FREEZE_SNPPAR_ENVIRONMENT_AMENDMENT_V1"
    )


if __name__ == "__main__":
    main()
