#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess
import sys

EXP = Path("experiments/07_comparative_landscape")
IMPL = EXP / "comparator_benchmark_execution_v1_impl"

AUTH_COMMIT = (
    "86eb4cc4529ad378ab1577e164e84574cdc55421"
)

AUTH_BASELINE = (
    "6c18db058b7e4b9f71f3e499fdf08d094ca5e1d8"
)

AUTH = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "snppar_reference_fixture_amendment_authorization.json"
)

MANIFEST = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "snppar_reference_fixture_amendment_manifest.json"
)

AUTH_VALIDATOR = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "snppar_reference_fixture_amendment_authorization_freeze.py"
)

AUTH_PATHS = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "snppar_reference_fixture_amendment_authorization.json",

    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "SNPPAR_REFERENCE_FIXTURE_AMENDMENT_AUTHORIZATION.md",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "snppar_reference_fixture_amendment_authorization_freeze.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "snppar_reference_fixture_amendment_authorization.sha256",
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
    head = git("rev-parse", "HEAD")

    if subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            AUTH_COMMIT,
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
            f"{AUTH_COMMIT}:{path}",
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
            "reference-fixture authorization no longer validates:\n"
            + cp.stdout
        )

    auth = json.loads(
        AUTH.read_text(encoding="utf-8")
    )

    if auth["parent_commit"] != AUTH_BASELINE:
        raise RuntimeError(
            "authorization baseline parent differs"
        )

    m = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )

    if m["status"] != "FROZEN_AMENDMENT_V1":
        raise RuntimeError("manifest status differs")

    if m["parent_authorization_commit"] != AUTH_COMMIT:
        raise RuntimeError(
            "manifest authorization commit differs"
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
            f"{AUTH_COMMIT}:{path}",
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
        "variable_positions_required": True,
        "synthetic_cds_count": 1,
        "synthetic_cds_length_bp": 3,
        "placement_rule":
            "first consecutive three-base interval containing no variable site",
        "locus_tag": "SYNTH_CDS_001",
        "variable_site_overlap_forbidden": True,
        "reference_sequence_preserved": True,
    }

    if m["fixture_contract"] != expected_contract:
        raise RuntimeError(
            "fixture contract differs"
        )

    if (
        m["snppar_source_pin"]
        != "0386df8edcff26faf242bc268c5f8865b09c9de9"
    ):
        raise RuntimeError(
            "SNPPar source pin differs"
        )

    forbidden = (
        "snppar_source_changed",
        "snppar_environment_changed",
        "snppar_run_contract_changed",
        "snppar_inference_settings_changed",
        "snppar_output_parser_changed",
        "root_sequence_generation_changed",
        "variable_positions_changed",
        "event_truth_changed",
        "tree_generation_changed",
        "metrics_changed",
        "benchmark_scenarios_changed",
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
        "RERUN_SNPPAR_TOY_SMOKE_WITH_"
        "FROZEN_REFERENCE_FIXTURE_V1"
    ):
        raise RuntimeError(
            "next gate differs"
        )

    print("PASS | SNPPar reference-fixture amendment v1 validates")
    print("PASS | authorization commit distinguished from its baseline parent")
    print("PASS | change restricted to adapter and toy validation")
    print("PASS | one synthetic three-base CDS required")
    print("PASS | CDS placement excludes all variable positions")
    print("PASS | reference sequence remains unchanged")
    print("PASS | SNPPar source and environment remain unchanged")
    print("PASS | benchmark truth, trees and metrics remain unchanged")
    print("PASS | focused toy validation passes")
    print(
        "PASS | next gate = "
        "RERUN_SNPPAR_TOY_SMOKE_WITH_FROZEN_REFERENCE_FIXTURE_V1"
    )


if __name__ == "__main__":
    main()
