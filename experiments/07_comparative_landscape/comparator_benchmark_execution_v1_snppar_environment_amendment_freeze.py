#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess

EXP = Path("experiments/07_comparative_landscape")

PARENT = "73305654e20a7d2e9b62a73166bb5c7de8c25a54"

RECIPE = (
    EXP
    / "comparator_benchmark_execution_v1_impl"
    / "environment_recipes.json"
)

MANIFEST = (
    EXP
    / "comparator_benchmark_execution_v1_"
      "snppar_environment_amendment_manifest.json"
)

AUTH_PATHS = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "snppar_environment_amendment_authorization.json",

    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "SNPPAR_ENVIRONMENT_AMENDMENT_AUTHORIZATION.md",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "snppar_environment_amendment_authorization_freeze.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_"
    "snppar_environment_amendment_authorization.sha256",
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


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    head = git("rev-parse", "HEAD")

    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", PARENT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError(
            "repository is not descended from authorization commit"
        )

    for path in AUTH_PATHS:
        frozen = git_bytes("show", f"{PARENT}:{path}")
        current = Path(path).read_bytes()

        if frozen != current:
            raise RuntimeError(
                f"authorization artifact changed: {path}"
            )

    before_bytes = git_bytes(
        "show",
        f"{PARENT}:"
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/"
        "environment_recipes.json",
    )

    before = json.loads(before_bytes)
    after = json.loads(RECIPE.read_text(encoding="utf-8"))

    expected = {
        "build_recipe": [
            "clone exact release tag/commit",
            "create isolated Python 3.8.20 environment",
            "set PYTHONNOUSERSITE=1 for installation and execution",
            "install biopython==1.76",
            "install phylo-treetime==0.8.5",
            "install ete3==3.1.3",
            "pip install . --no-deps from exact frozen SNPPar source",
        ],
        "build_status": "READY_FOR_AUTHORIZED_SMOKE_BUILD",
        "dependencies": [
            "Python ==3.8.20",
            "BioPython ==1.76",
            "ETE3 ==3.1.3",
            "phylo-treetime ==0.8.5",
        ],
        "environment": {
            "PYTHONNOUSERSITE": "1",
        },
        "output_contract": [
            "all mutation events TSV",
            "homoplasic mutation events TSV",
            "labelled output tree",
        ],
        "release": "v1.2",
        "run_contract":
            "snppar -m {snp_mfasta} -l {snp_positions} "
            "-t {tree_newick} -g {reference_genbank} "
            "-d {out_dir} -A -i",
        "source_pin":
            "0386df8edcff26faf242bc268c5f8865b09c9de9",
    }

    if after["methods"]["SNPPar"] != expected:
        raise RuntimeError("amended SNPPar recipe differs")

    if before["global_policy"] != after["global_policy"]:
        raise RuntimeError("global policy changed")

    if before["recipe_schema"] != after["recipe_schema"]:
        raise RuntimeError("recipe schema changed")

    if before["status"] != after["status"]:
        raise RuntimeError("recipe status changed")

    for method in before["methods"]:
        if method == "SNPPar":
            continue

        if before["methods"][method] != after["methods"][method]:
            raise RuntimeError(
                f"other comparator recipe changed: {method}"
            )

    if (
        before["methods"]["SNPPar"]["source_pin"]
        != after["methods"]["SNPPar"]["source_pin"]
    ):
        raise RuntimeError("SNPPar source pin changed")

    if (
        before["methods"]["SNPPar"]["run_contract"]
        != after["methods"]["SNPPar"]["run_contract"]
    ):
        raise RuntimeError("SNPPar run contract changed")

    if (
        before["methods"]["SNPPar"]["output_contract"]
        != after["methods"]["SNPPar"]["output_contract"]
    ):
        raise RuntimeError("SNPPar output contract changed")

    m = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )

    if m["status"] != "FROZEN_AMENDMENT_V1":
        raise RuntimeError("manifest status differs")

    if m["parent_authorization_commit"] != PARENT:
        raise RuntimeError("manifest parent differs")

    if m["authorization_consumed"] is not True:
        raise RuntimeError("authorization consumption absent")

    if m["changed_section"] != "methods.SNPPar":
        raise RuntimeError("changed section differs")

    if m["recipe_before_sha256"] != sha(before_bytes):
        raise RuntimeError("pre-amendment recipe hash differs")

    if m["recipe_after_sha256"] != sha(RECIPE.read_bytes()):
        raise RuntimeError("post-amendment recipe hash differs")

    for key in (
        "source_changed",
        "run_contract_changed",
        "output_contract_changed",
        "other_comparator_recipes_changed",
        "metrics_changed",
        "truth_generator_changed",
        "benchmark_scenarios_changed",
    ):
        if m[key] is not False:
            raise RuntimeError(
                f"unauthorized change recorded: {key}"
            )

    if not all(m["semantic_checks"].values()):
        raise RuntimeError(
            "one or more semantic integrity checks failed"
        )

    if m["next_gate"] != (
        "RERUN_SNPPAR_AUTHORIZED_TOY_SMOKE_"
        "WITH_FROZEN_ENVIRONMENT_V1"
    ):
        raise RuntimeError("next gate differs")

    print("PASS | SNPPar environment amendment v1 validates")
    print("PASS | only methods.SNPPar changed")
    print("PASS | Python 3.8.20 frozen")
    print("PASS | Biopython 1.76 frozen")
    print("PASS | TreeTime 0.8.5 frozen")
    print("PASS | ETE3 3.1.3 frozen")
    print("PASS | PYTHONNOUSERSITE=1 required")
    print("PASS | source pin unchanged")
    print("PASS | run and output contracts unchanged")
    print("PASS | other seven comparator recipes unchanged")
    print(
        "PASS | next gate = "
        "RERUN_SNPPAR_AUTHORIZED_TOY_SMOKE_WITH_FROZEN_ENVIRONMENT_V1"
    )


if __name__ == "__main__":
    main()
