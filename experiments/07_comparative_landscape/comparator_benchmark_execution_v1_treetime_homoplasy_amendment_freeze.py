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
      "treetime_homoplasy_amendment_authorization.json"
)

AUTH_VALIDATOR = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "treetime_homoplasy_amendment_authorization_freeze.py"
)

MANIFEST = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "treetime_homoplasy_amendment_manifest.json"
)

AUTH_PATHS = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "treetime_homoplasy_amendment_authorization.json",

    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "TREETIME_HOMOPLASY_AMENDMENT_AUTHORIZATION.md",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "treetime_homoplasy_amendment_authorization_freeze.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "treetime_homoplasy_amendment_authorization.sha256",
]

TARGETS = {
    "environment_recipes":
        IMPL / "environment_recipes.json",

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
        ["git", "merge-base", "--is-ancestor", auth_commit, head],
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
            "TreeTime amendment authorization no longer validates:\n"
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
        str(TARGETS["environment_recipes"]),
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
        "function":
            "treetime_recurrent_sites_from_branch_events",
        "scored_source":
            "normalized branch changes from the frozen "
            "TreeTime ancestral reconstruction output",
        "homoplasy_cli_scored": False,
        "recurrent_site_minimum_branch_changes": 2,
        "group_by_genomic_position": True,
        "transition_identity_required_to_match": False,
        "reported_recurrence_count_if_available":
            "number of normalized reconstructed branch "
            "changes at the position",
    }

    if m["treetime_homoplasy_contract"] != expected_contract:
        raise RuntimeError(
            "TreeTime homoplasy contract differs"
        )

    forbidden = (
        "benchmark_executed",
        "benchmark_dataset_changed",
        "benchmark_truth_accessed_for_implementation",
        "comparator_version_changed",
        "metric_changed",
        "scenario_changed",
        "source_pin_changed",
        "treetime_ancestral_parameter_changed",
        "treetime_executable_changed",
        "other_comparator_changed",
        "other_parser_changed",
        "production_bridge",
    )

    for key in forbidden:
        if m[key] is not False:
            raise RuntimeError(
                f"unauthorized change recorded: {key}"
            )

    recipes = json.loads(
        TARGETS["environment_recipes"].read_text(
            encoding="utf-8"
        )
    )
    tt = recipes["methods"]["TreeTime"]

    if "run_contract_homoplasy" in tt:
        raise RuntimeError(
            "TreeTime homoplasy execution contract remains present"
        )

    if tt["source_pin"] != (
        "17da461f9299706b99a90e622183772f00c5076d"
    ):
        raise RuntimeError(
            "TreeTime source pin differs"
        )

    if tt["run_contract_branch"] != (
        "treetime ancestral --aln {alignment_fasta} "
        "--tree {tree_newick} --gtr JC69 "
        "--method-anc probabilistic "
        "--rng-seed {scenario_seed} --outdir {out_dir}"
    ):
        raise RuntimeError(
            "TreeTime ancestral run contract differs"
        )

    if tt["output_contract"] != [
        "ancestral_sequences.fasta",
        "annotated_tree.nexus",
        "recurrent-site calls derived from normalized ancestral branch events",
    ]:
        raise RuntimeError(
            "TreeTime output contract differs"
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
        "AUTHORIZE_COMPARATOR_BENCHMARK_"
        "RUNNER_IMPLEMENTATION_V1"
    ):
        raise RuntimeError(
            "next gate differs"
        )

    print("PASS | TreeTime homoplasy amendment v1 validates")
    print("PASS | authorization artifacts remain frozen")
    print("PASS | exactly three authorized implementation files changed")
    print("PASS | pre- and post-amendment identities match")
    print("PASS | recurrent sites derive from normalized ancestral branch changes")
    print("PASS | recurrence is grouped by genomic position")
    print("PASS | TreeTime executable, source pin and ancestral parameters unchanged")
    print("PASS | benchmark truth, scenarios and metrics unchanged")
    print("PASS | focused toy validation passes")
    print("PASS | full benchmark execution remains unauthorized")
    print(
        "PASS | next gate = "
        "AUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V1"
    )


if __name__ == "__main__":
    main()
