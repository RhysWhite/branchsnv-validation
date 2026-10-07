#!/usr/bin/env python3

from pathlib import Path
import csv
import hashlib
import json
import subprocess
import sys

EXP = Path("experiments/07_comparative_landscape")
IMPL = EXP / "comparator_benchmark_execution_v1_impl"
OUT = Path(
    "results/07_comparative_landscape/"
    "comparator_benchmark_environment_smoke_v1"
)

FREEZE_PARENT = "5f92bceda58f5828d238007c1859b5c2636536fa"
BASE_IMPLEMENTATION_FREEZE = "f48bd14048866820c7a252d935ed2d26cb9407e5"
SMOKE_AUTH_COMMIT = "423d0b1b98a207c4287aadf56ab28c18e5003f96"

DESIGN = EXP / "comparator_benchmark_environment_smoke_v1_results_design.json"
RECORD = EXP / "COMPARATOR_BENCHMARK_ENVIRONMENT_SMOKE_V1_RESULTS.md"

EXPECTED_DESIGN_SHA = "070897f3adf7bc20db20af5aa259588c2ca2c0bf600def5cb3b51f3fe00d70e9"
EXPECTED_RECORD_SHA = "8e3e18246cc640f8c7c2abb96b4abc667fa36ab9ff6f0e88ac5170a9450bd357"

EXPECTED_RESULT_SHA = {
    "comparator_benchmark_environment_smoke_v1_manifest.json":
        "4acecf961ab98391b97e9ac73739c2e674984d5ff3831f43c7775e7c46da1c56",
    "implementation_amendment_chain.tsv":
        "d261a157950ecf05e3a9740f1f6650bca58fa6be673d9f06035a68fc40c51ed2",
    "checksums.sha256":
        "260a4da3417f261ec7478ee1b931ecc2219c60676430a268fa08e8029b94bcbc",
}

EXPECTED_METHODS = {
    "ARPIP", "FastML", "HomoplasyFinder", "PAML",
    "PastML", "POUTINE", "SNPPar", "TreeTime",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def main():
    head = git("rev-parse", "HEAD")

    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", FREEZE_PARENT, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        raise RuntimeError(
            "repository is not descended from final amended implementation"
        )

    if sha(DESIGN) != EXPECTED_DESIGN_SHA:
        raise RuntimeError("environment-smoke result design differs")

    if sha(RECORD) != EXPECTED_RECORD_SHA:
        raise RuntimeError("environment-smoke result record differs")

    for name, expected in EXPECTED_RESULT_SHA.items():
        path = OUT / name
        if not path.is_file() or sha(path) != expected:
            raise RuntimeError(f"environment-smoke result artifact differs: {name}")

    print("PASS | repository descends from final amended implementation")
    print("PASS | result design and freeze record identities match")
    print("PASS | three frozen result artifact identities match")

    manifest = json.loads(
        (OUT / "comparator_benchmark_environment_smoke_v1_manifest.json")
        .read_text(encoding="utf-8")
    )

    if manifest["freeze_id"] != \
       "COMPARATOR_BENCHMARK_ENVIRONMENT_AND_SMOKE_RESULTS_V1":
        raise RuntimeError("result freeze id differs")

    if manifest["status"] != "ENVIRONMENT_AND_SMOKE_COMPLETE":
        raise RuntimeError("result status differs")

    if set(manifest["methods"]) != EXPECTED_METHODS:
        raise RuntimeError("frozen method set differs")

    if manifest["completion"]["method_count"] != 8:
        raise RuntimeError("method count differs")

    if manifest["completion"]["all_eight_environment_smokes_closed"] is not True:
        raise RuntimeError("environment-smoke completion absent")

    if manifest["completion"]["final_toy_implementation_validation_passed"] is not True:
        raise RuntimeError("final toy-validation status differs")

    if manifest["completion"]["failed_and_remediated_attempts_preserved"] is not True:
        raise RuntimeError("failed-attempt preservation status differs")

    if any(manifest["execution_boundary"].values()):
        raise RuntimeError("post-smoke execution boundary violated")

    if manifest["next_gate"] != \
       "AUTHORIZE_COMPARATOR_BENCHMARK_DATASET_GENERATION_V1":
        raise RuntimeError("post-smoke next gate differs")

    checksum_lines = (
        OUT / "checksums.sha256"
    ).read_text(encoding="utf-8").splitlines()

    if len(checksum_lines) != 319:
        raise RuntimeError("result-tree checksum entry count differs")

    subprocess.run(
        ["sha256sum", "-c", str(OUT / "checksums.sha256")],
        check=True,
        stdout=subprocess.DEVNULL,
    )

    print("PASS | exact 8-method smoke-result manifest validates")
    print("PASS | canonical dataset and benchmark execution remain blocked")
    print("PASS | complete 319-entry result tree verifies")

    with (OUT / "implementation_amendment_chain.tsv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        amendments = list(csv.DictReader(handle, delimiter="\t"))

    if len(amendments) != 15:
        raise RuntimeError("authorized amendment count differs")

    for row in amendments:
        observed_parent = git("rev-parse", row["freeze_commit"] + "^")
        if observed_parent != row["authorization_commit"]:
            raise RuntimeError(
                "freeze commit does not directly follow authorization: "
                + row["freeze_commit"]
            )

    expected_impl_sha = {
        "IMPLEMENTATION.md":
            "55128020c7812698d005a9786bd745ae77f150c2b6926961b0326819720b6b07",
        "adapters.py":
            "c4d351b041c68d9d1a142e3f532d353042374b416f5d03da29378a79672779e5",
        "environment_recipes.json":
            "9a236919ac350dca7e2da48a1dd6aa4f1f15edfeaa7693a5207e33c5fe5b7b8a",
        "generator.py":
            "229ed49c541023d6d439967ca184dd82430a4b3592d42657131fac08c9f3f560",
        "implementation_manifest.json":
            "ef8338083aa53da20aa66e50d0183d40e69d2d2a8270d91e4eb4ae9e033f4c94",
        "metrics.py":
            "b6d3ca91702e79a8a1b2dc36591616fa1519f59bd342a005e9cf646c8e8475de",
        "source_pins.tsv":
            "b1f5d81a33ac407e9cdf3d15dfa6bcd6e45c676808e3f5232bab9d9c1dcf1365",
        "toy_validation.py":
            "7f087232c8beefbf6ca4351cd4e87d728a2b62838890275f60e8e26d9490f339",
    }

    for name, expected in expected_impl_sha.items():
        if sha(IMPL / name) != expected:
            raise RuntimeError(f"final implementation artifact differs: {name}")

    print("PASS | 15-step authorized amendment chain validates")
    print("PASS | final amended implementation identities match")

    smoke_auth_paths = [
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_environment_smoke_authorization.json",
        "experiments/07_comparative_landscape/"
        "COMPARATOR_BENCHMARK_EXECUTION_V1_ENVIRONMENT_SMOKE_AUTHORIZATION.md",
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_environment_smoke_authorization_freeze.py",
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_environment_smoke_authorization.sha256",
    ]

    for path in smoke_auth_paths:
        frozen = subprocess.check_output(
            ["git", "show", f"{SMOKE_AUTH_COMMIT}:{path}"]
        )
        current = Path(path).read_bytes()
        if frozen != current:
            raise RuntimeError(
                f"environment-smoke authorization artifact changed: {path}"
            )

    smoke_auth = json.loads(
        (
            EXP
            / "comparator_benchmark_execution_v1_environment_smoke_authorization.json"
        ).read_text(encoding="utf-8")
    )

    if smoke_auth["authorization_id"] != \
       "COMPARATOR_BENCHMARK_EXECUTION_V1_ENVIRONMENT_SMOKE_001":
        raise RuntimeError("environment-smoke authorization id differs")

    if smoke_auth["one_time_environment_smoke_authorization"] is not True:
        raise RuntimeError("one-use environment-smoke authorization absent")

    if smoke_auth["rerun_authorized"] is not False:
        raise RuntimeError("environment-smoke rerun unexpectedly authorized")

    print("PASS | original environment-smoke authorization artifacts unchanged")
    print("PASS | one-use smoke authorization consumed; rerun remains blocked")

    for row in amendments:
        auth_commit = row["authorization_commit"]
        freeze_commit = row["freeze_commit"]

        auth_commit_files = git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", auth_commit
        ).splitlines()

        auth_json_paths = [
            path for path in auth_commit_files
            if path.endswith("_authorization.json")
        ]

        if len(auth_json_paths) != 1:
            raise RuntimeError(
                f"expected exactly one amendment authorization JSON: {auth_commit}"
            )

        auth_path = auth_json_paths[0]
        frozen_auth = subprocess.check_output(
            ["git", "show", f"{auth_commit}:{auth_path}"]
        )

        if Path(auth_path).read_bytes() != frozen_auth:
            raise RuntimeError(
                f"amendment authorization artifact changed: {auth_path}"
            )

        auth = json.loads(frozen_auth.decode("utf-8"))

        if "parent_commit" in auth:
            recorded_parent = auth["parent_commit"]
        elif "parent_environment_smoke_authorization_commit" in auth:
            recorded_parent = auth["parent_environment_smoke_authorization_commit"]
        else:
            raise RuntimeError(
                f"authorization parent field absent: {auth_commit}"
            )

        if recorded_parent != git("rev-parse", auth_commit + "^"):
            raise RuntimeError(
                f"authorization baseline parent differs: {auth_commit}"
            )

        if "authorized_files" in auth:
            authorized_files = set(auth["authorized_files"])
        elif "file" in auth.get("authorized_change", {}):
            authorized_files = {auth["authorized_change"]["file"]}
        elif "recipe_path" in auth:
            authorized_files = {auth["recipe_path"]}
        else:
            raise RuntimeError(
                f"authorized implementation file set absent: {auth_commit}"
            )

        changed_files = set(
            git(
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                freeze_commit,
            ).splitlines()
        )

        changed_impl_files = {
            path for path in changed_files
            if path.startswith(
                "experiments/07_comparative_landscape/"
                "comparator_benchmark_execution_v1_impl/"
            )
        }

        if changed_impl_files != authorized_files:
            raise RuntimeError(
                f"implementation change set differs from authorization: "
                f"{freeze_commit}"
            )

    print("PASS | all 15 amendment authorizations remain byte-identical")
    print("PASS | every implementation change set exactly matches its authorization")

    design = json.loads(DESIGN.read_text(encoding="utf-8"))

    if design["freeze_id"] != \
       "COMPARATOR_BENCHMARK_ENVIRONMENT_AND_SMOKE_RESULTS_V1":
        raise RuntimeError("result-design freeze id differs")

    if design["freeze_parent_commit"] != FREEZE_PARENT:
        raise RuntimeError("result-design parent differs")

    if design["authorization_commit"] != SMOKE_AUTH_COMMIT:
        raise RuntimeError("result-design authorization commit differs")

    if design["authorization_consumed"] is not True:
        raise RuntimeError("authorization consumption absent")

    if design["rerun_authorized"] is not False:
        raise RuntimeError("rerun unexpectedly authorized")

    if design["method_count"] != 8:
        raise RuntimeError("result-design method count differs")

    if set(design["methods"]) != EXPECTED_METHODS:
        raise RuntimeError("result-design method set differs")

    if design["completion"]["result_tree_checksum_entry_count"] != 319:
        raise RuntimeError("result-design checksum count differs")

    if any(design["execution_boundary"].values()):
        raise RuntimeError("result-design execution boundary violated")

    if design["next_gate"] != \
       "AUTHORIZE_COMPARATOR_BENCHMARK_DATASET_GENERATION_V1":
        raise RuntimeError("result-design next gate differs")

    toy = subprocess.run(
        [sys.executable, "toy_validation.py"],
        cwd=IMPL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if (
        toy.returncode != 0
        or "TOY_IMPLEMENTATION_VALIDATION=PASS" not in toy.stdout
    ):
        raise RuntimeError(
            "final toy implementation validation failed:\n" + toy.stdout
        )

    print("PASS | result-design semantics validate")
    print("PASS | final toy implementation validation passes")
    print(
        "PASS | next gate = "
        "AUTHORIZE_COMPARATOR_BENCHMARK_DATASET_GENERATION_V1"
    )


if __name__ == "__main__":
    main()
