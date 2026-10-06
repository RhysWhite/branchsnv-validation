#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess

EXP = Path("experiments/07_comparative_landscape")

AUTH = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "homoplasyfinder_cli_amendment_authorization.json"
)

AUTH_ID = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "HOMOPLASYFINDER_CLI_AMENDMENT_001"
)

EXPECTED_BEFORE = (
    "java -jar homoplasyFinder.jar "
    "-fasta {alignment_fasta} "
    "-tree {tree_newick}"
)

EXPECTED_AFTER = (
    "java -jar homoplasyFinder.jar "
    "--fasta {alignment_fasta} "
    "--tree {tree_newick}"
)


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

    head = git("rev-parse", "HEAD")
    parent = a["parent_commit"]

    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", parent, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError(
            "repository is not descended from authorization parent"
        )

    if a["authorization_id"] != AUTH_ID:
        raise RuntimeError("authorization id differs")

    if a["status"] not in {
        "AUTHORIZED_NOT_YET_CONSUMED",
        "AUTHORIZED_CONSUMED",
    }:
        raise RuntimeError("authorization status differs")

    recipe_path = a["recipe_path"]

    frozen = git_bytes(
        "show",
        f"{parent}:{recipe_path}",
    )

    digest = hashlib.sha256(frozen).hexdigest()

    if digest != a["recipe_before_sha256"]:
        raise RuntimeError(
            "authorization baseline recipe hash differs"
        )

    c = a["authorized_change"]

    if c["method"] != "HomoplasyFinder":
        raise RuntimeError("authorized method differs")

    if c["field"] != "run_contract":
        raise RuntimeError("authorized field differs")

    if c["before"] != EXPECTED_BEFORE:
        raise RuntimeError("pre-amendment command differs")

    if c["after"] != EXPECTED_AFTER:
        raise RuntimeError("post-amendment command differs")

    if (
        a["source_pin"]
        != "faed16f2ff1602a2a939663a942e0b8640b9bc50"
    ):
        raise RuntimeError("source pin differs")

    if not all(
        a["explicitly_not_authorized"].values()
    ):
        raise RuntimeError(
            "one or more prohibited changes not blocked"
        )

    if a["one_time_amendment"] is not True:
        raise RuntimeError("one-time policy absent")

    if a["rerun_authorized"] is not False:
        raise RuntimeError(
            "rerun unexpectedly authorized"
        )

    if a["next_gate"] != (
        "IMPLEMENT_AND_FREEZE_"
        "HOMOPLASYFINDER_CLI_AMENDMENT_V1"
    ):
        raise RuntimeError("next gate differs")

    print("PASS | HomoplasyFinder CLI amendment authorized")
    print("PASS | only run_contract may change")
    print("PASS | correction restricted to double-dash CLI flags")
    print("PASS | source pin and repository JAR remain frozen")
    print("PASS | output contract remains unchanged")
    print("PASS | other comparator recipes remain frozen")
    print("PASS | full benchmark execution remains unauthorized")
    print(
        "PASS | next gate = "
        "IMPLEMENT_AND_FREEZE_HOMOPLASYFINDER_CLI_AMENDMENT_V1"
    )


if __name__ == "__main__":
    main()
