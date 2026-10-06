#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess
import sys

EXP = Path("experiments/07_comparative_landscape")
IMPL = EXP / "comparator_benchmark_execution_v1_impl"

AUTH = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "homoplasyfinder_parser_amendment_authorization.json"
)

AUTH_VALIDATOR = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "homoplasyfinder_parser_amendment_authorization_freeze.py"
)

MANIFEST = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "homoplasyfinder_parser_amendment_manifest.json"
)

AUTH_PATHS = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "homoplasyfinder_parser_amendment_authorization.json",

    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "HOMOPLASYFINDER_PARSER_AMENDMENT_AUTHORIZATION.md",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "homoplasyfinder_parser_amendment_authorization_freeze.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "homoplasyfinder_parser_amendment_authorization.sha256",
]

TARGETS = {
    "adapters":
        IMPL / "adapters.py",

    "toy_validation":
        IMPL / "toy_validation.py",
}


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
            "HomoplasyFinder parser authorization no longer validates:\n"
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

    expected_files = [
        str(TARGETS["adapters"]),
        str(TARGETS["toy_validation"]),
    ]

    if m["changed_files"] != expected_files:
        raise RuntimeError(
            "changed file set differs"
        )

    for name, path in TARGETS.items():
        before = git_bytes(
            "show",
            f"{auth_commit}:{path}",
        )

        current = path.read_bytes()

        if m["before_sha256"][name] != sha(before):
            raise RuntimeError(
                f"pre-amendment hash differs: {name}"
            )

        if m["after_sha256"][name] != sha(current):
            raise RuntimeError(
                f"post-amendment hash differs: {name}"
            )

    expected_contract = {
        "function": "parse_homoplasyfinder_report",
        "count_column": "MinimumNumberChangesOnTree",
        "preserve_numeric_count": True,
        "integer_count_normalized_to_integer_string": True,
        "absent_count_is_empty_string": True,
        "empty_count_is_empty_string": True,
        "invalid_non_numeric_count_fails": True,
        "non_integer_numeric_count_fails": True,
        "consistency_index_filtering_preserved": True,
    }

    if m["parser_contract"] != expected_contract:
        raise RuntimeError(
            "parser contract differs"
        )

    forbidden = (
        "homoplasyfinder_source_changed",
        "homoplasyfinder_jar_changed",
        "homoplasyfinder_recipe_changed",
        "homoplasyfinder_run_contract_changed",
        "homoplasyfinder_output_contract_changed",
        "input_adapter_changed",
        "metric_changed",
        "truth_changed",
        "scenario_changed",
        "other_parser_changed",
        "other_comparator_changed",
    )

    for key in forbidden:
        if m[key] is not False:
            raise RuntimeError(
                f"unauthorized change recorded: {key}"
            )

    cp = subprocess.run(
        [sys.executable, "toy_validation.py"],
        cwd=IMPL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if (
        cp.returncode != 0
        or "TOY_IMPLEMENTATION_VALIDATION=PASS"
        not in cp.stdout
    ):
        raise RuntimeError(
            "toy implementation validation failed:\n"
            + cp.stdout
        )

    if m["next_gate"] != (
        "CLOSE_HOMOPLASYFINDER_SMOKE_AND_PROCEED_TO_PAML"
    ):
        raise RuntimeError(
            "next gate differs"
        )

    print("PASS | HomoplasyFinder parser amendment v1 validates")
    print("PASS | authorization commit distinguished from its baseline parent")
    print("PASS | change restricted to parser and focused toy validation")
    print("PASS | available minimum-change counts preserved")
    print("PASS | missing counts retain empty-string representation")
    print("PASS | invalid counts fail closed")
    print("PASS | consistency-index filtering preserved")
    print("PASS | HomoplasyFinder executable and recipe unchanged")
    print("PASS | benchmark truth and metrics unchanged")
    print("PASS | focused toy validation passes")
    print(
        "PASS | next gate = "
        "CLOSE_HOMOPLASYFINDER_SMOKE_AND_PROCEED_TO_PAML"
    )


if __name__ == "__main__":
    main()
