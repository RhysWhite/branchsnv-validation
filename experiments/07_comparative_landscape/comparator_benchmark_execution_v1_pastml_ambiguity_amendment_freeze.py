#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess
import sys

PARENT = 'c4d9b63c32c5760c61997e6ea709da8e65374300'

EXP = Path("experiments/07_comparative_landscape")

ADAPTER = (
    EXP
    / "comparator_benchmark_execution_v1_impl"
    / "adapters.py"
)

TEST = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "pastml_ambiguity_amendment_test.py"
)

MANIFEST = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "pastml_ambiguity_amendment_manifest.json"
)

AUTH_PATHS = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "pastml_ambiguity_amendment_authorization.json",

    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "PASTML_AMBIGUITY_AMENDMENT_AUTHORIZATION.md",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "pastml_ambiguity_amendment_authorization_freeze.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "pastml_ambiguity_amendment_authorization.sha256",
]

EXPECTED_BEFORE_SHA = 'b5b6dae15008d403d8e408ea44220651b390c12f24a3902dfb7c5312daa01b16'
EXPECTED_AFTER_SHA = '5745112944c348081a7260d57428fbf561c831b2615902a138fee0a42e839d42'
EXPECTED_TEST_SHA = 'c5f9c7c249fb8cc2c0f8b2d0e5f6862d339c0e64945a30c00ab71f4f37967e48'


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(path.read_bytes())


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
        ["git", "merge-base", "--is-ancestor", PARENT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError("repository is not descended from amendment authorization")

    for path in AUTH_PATHS:
        frozen = git_bytes("show", f"{PARENT}:{path}")
        current = Path(path).read_bytes()

        if frozen != current:
            raise RuntimeError(
                f"amendment authorization artifact changed: {path}"
            )

    base_adapter = git_bytes(
        "show",
        f"{PARENT}:"
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/adapters.py",
    )

    if sha_bytes(base_adapter) != EXPECTED_BEFORE_SHA:
        raise RuntimeError("pre-amendment adapter hash differs")

    if sha_file(ADAPTER) != EXPECTED_AFTER_SHA:
        raise RuntimeError("amended adapter hash differs")

    if sha_file(TEST) != EXPECTED_TEST_SHA:
        raise RuntimeError("focused test hash differs")

    manifest = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )

    if manifest["status"] != "FROZEN_AMENDMENT_V1":
        raise RuntimeError("amendment status differs")

    if manifest["parent_authorization_commit"] != PARENT:
        raise RuntimeError("amendment parent differs")

    if manifest["authorization_consumed"] is not True:
        raise RuntimeError("authorization consumption absent")

    if manifest["change"]["function"] != "parse_tabular_node_states":
        raise RuntimeError("amended function differs")

    if manifest["change"]["before_sha256"] != EXPECTED_BEFORE_SHA:
        raise RuntimeError("manifest before hash differs")

    if manifest["change"]["after_sha256"] != EXPECTED_AFTER_SHA:
        raise RuntimeError("manifest after hash differs")

    if manifest["focused_test"]["sha256"] != EXPECTED_TEST_SHA:
        raise RuntimeError("manifest test hash differs")

    blocked_change_flags = [
        "other_adapters_changed",
        "metrics_changed",
        "truth_generator_changed",
        "benchmark_scenarios_changed",
        "pastml_source_or_version_changed",
        "pastml_inference_settings_changed",
    ]

    for key in blocked_change_flags:
        if manifest[key] is not False:
            raise RuntimeError(
                f"unauthorized change recorded: {key}"
            )

    cp = subprocess.run(
        [sys.executable, str(TEST)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if (
        cp.returncode != 0
        or "PASTML_AMBIGUITY_AMENDMENT_TEST=PASS"
        not in cp.stdout
    ):
        raise RuntimeError("focused PastML amendment test failed")

    toy = subprocess.run(
        [
            sys.executable,
            str(
                EXP
                / "comparator_benchmark_execution_v1_impl"
                / "toy_validation.py"
            ),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if (
        toy.returncode != 0
        or "TOY_IMPLEMENTATION_VALIDATION=PASS"
        not in toy.stdout
    ):
        raise RuntimeError("existing toy validation failed")

    if head != PARENT:
        allowed = {
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
        }

        changed = set(
            subprocess.check_output(
                [
                    "git",
                    "diff",
                    "--name-only",
                    f"{PARENT}..{head}",
                ],
                text=True,
            ).splitlines()
        )

        if changed != allowed:
            raise RuntimeError(
                "amendment commit path set differs"
            )

    print("PASS | PastML ambiguity-adapter amendment v1 validates")
    print("PASS | change restricted to the authorized parser")
    print("PASS | singleton states retained")
    print("PASS | absent or multi-state calls encoded as N")
    print("PASS | uncertain endpoints do not emit discrete events")
    print("PASS | existing toy validation still passes")
    print(
        "PASS | next gate = "
        "RESUME_COMPARATOR_BENCHMARK_ENVIRONMENT_AND_SMOKE_TEST_V1"
    )


if __name__ == "__main__":
    main()
