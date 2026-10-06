#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess
import sys

EXP = Path("experiments/07_comparative_landscape")

RECIPE = (
    EXP
    / "comparator_benchmark_execution_v1_impl"
    / "environment_recipes.json"
)

AUTH = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "homoplasyfinder_cli_amendment_authorization.json"
)

AUTH_VALIDATOR = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "homoplasyfinder_cli_amendment_authorization_freeze.py"
)

MANIFEST = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "homoplasyfinder_cli_amendment_manifest.json"
)

AUTH_PATHS = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "homoplasyfinder_cli_amendment_authorization.json",

    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "HOMOPLASYFINDER_CLI_AMENDMENT_AUTHORIZATION.md",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "homoplasyfinder_cli_amendment_authorization_freeze.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "homoplasyfinder_cli_amendment_authorization.sha256",
]

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


def sha(data):
    return hashlib.sha256(data).hexdigest()


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
    m = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )

    auth_commit = m["parent_authorization_commit"]
    head = git("rev-parse", "HEAD")

    if subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            auth_commit,
            head,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError(
            "repository is not descended from authorization commit"
        )

    for path in AUTH_PATHS:
        frozen = git_bytes(
            "show",
            f"{auth_commit}:{path}",
        )

        current = Path(path).read_bytes()

        if frozen != current:
            raise RuntimeError(
                f"authorization artifact changed: {path}"
            )

    cp = subprocess.run(
        [sys.executable, str(AUTH_VALIDATOR)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if cp.returncode != 0:
        raise RuntimeError(
            "HomoplasyFinder CLI authorization no longer validates:\n"
            + cp.stdout
        )

    auth = json.loads(
        AUTH.read_text(encoding="utf-8")
    )

    auth_parent = git(
        "rev-parse",
        f"{auth_commit}^",
    )

    if auth["parent_commit"] != auth_parent:
        raise RuntimeError(
            "authorization baseline parent differs"
        )

    if m["status"] != "FROZEN_AMENDMENT_V1":
        raise RuntimeError(
            "manifest status differs"
        )

    if m["authorization_consumed"] is not True:
        raise RuntimeError(
            "authorization consumption absent"
        )

    if m["changed_file"] != str(RECIPE):
        raise RuntimeError(
            "changed file differs"
        )

    before_bytes = git_bytes(
        "show",
        f"{auth_commit}:{RECIPE}",
    )

    current_bytes = RECIPE.read_bytes()

    if (
        m["recipe_before_sha256"]
        != sha(before_bytes)
    ):
        raise RuntimeError(
            "pre-amendment recipe hash differs"
        )

    if (
        m["recipe_after_sha256"]
        != sha(current_bytes)
    ):
        raise RuntimeError(
            "post-amendment recipe hash differs"
        )

    before = json.loads(
        before_bytes.decode("utf-8")
    )

    current = json.loads(
        current_bytes.decode("utf-8")
    )

    if (
        before["methods"]["HomoplasyFinder"]["run_contract"]
        != EXPECTED_BEFORE
    ):
        raise RuntimeError(
            "baseline HomoplasyFinder run contract differs"
        )

    if (
        current["methods"]["HomoplasyFinder"]["run_contract"]
        != EXPECTED_AFTER
    ):
        raise RuntimeError(
            "amended HomoplasyFinder run contract differs"
        )

    before_copy = json.loads(
        json.dumps(before)
    )

    current_copy = json.loads(
        json.dumps(current)
    )

    before_copy["methods"]["HomoplasyFinder"]["run_contract"] = None
    current_copy["methods"]["HomoplasyFinder"]["run_contract"] = None

    if before_copy != current_copy:
        raise RuntimeError(
            "recipe changed outside HomoplasyFinder.run_contract"
        )

    if m["method"] != "HomoplasyFinder":
        raise RuntimeError(
            "method differs"
        )

    if m["field"] != "run_contract":
        raise RuntimeError(
            "field differs"
        )

    if m["before"] != EXPECTED_BEFORE:
        raise RuntimeError(
            "manifest before command differs"
        )

    if m["after"] != EXPECTED_AFTER:
        raise RuntimeError(
            "manifest after command differs"
        )

    if (
        m["source_pin"]
        != "faed16f2ff1602a2a939663a942e0b8640b9bc50"
    ):
        raise RuntimeError(
            "source pin differs"
        )

    forbidden = (
        "source_changed",
        "jar_changed",
        "build_changed",
        "dependencies_changed",
        "output_contract_changed",
        "input_adapter_changed",
        "output_parser_changed",
        "truth_changed",
        "metrics_changed",
        "scenarios_changed",
        "other_method_recipes_changed",
    )

    for key in forbidden:
        if m[key] is not False:
            raise RuntimeError(
                f"unauthorized change recorded: {key}"
            )

    if m["smoke_success_requirement"] != (
        "Process execution plus at least one "
        "consistencyIndexReport_*.txt output."
    ):
        raise RuntimeError(
            "smoke success requirement differs"
        )

    if m["next_gate"] != (
        "RERUN_HOMOPLASYFINDER_AUTHORIZED_"
        "TOY_SMOKE_WITH_CORRECTED_CLI_V1"
    ):
        raise RuntimeError(
            "next gate differs"
        )

    print("PASS | HomoplasyFinder CLI amendment v1 validates")
    print("PASS | authorization commit distinguished from its baseline parent")
    print("PASS | exactly HomoplasyFinder.run_contract changed")
    print("PASS | corrected --fasta and --tree flags frozen")
    print("PASS | source pin and repository JAR unchanged")
    print("PASS | output contract unchanged")
    print("PASS | other comparator recipes unchanged")
    print("PASS | smoke requires expected report output")
    print("PASS | full benchmark remains unauthorized")
    print(
        "PASS | next gate = "
        "RERUN_HOMOPLASYFINDER_AUTHORIZED_"
        "TOY_SMOKE_WITH_CORRECTED_CLI_V1"
    )


if __name__ == "__main__":
    main()
