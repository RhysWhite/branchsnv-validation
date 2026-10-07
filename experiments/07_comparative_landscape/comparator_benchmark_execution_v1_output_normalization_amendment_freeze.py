#!/usr/bin/env python3

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
IMPL = ROOT / "comparator_benchmark_execution_v1_impl"

AUTH_COMMIT = "ceb9472dc0b17b73262881ee49f3fa10f9f62a84"

AUTH = ROOT / (
    "comparator_benchmark_execution_v1_"
    "output_normalization_amendment_authorization.json"
)

MANIFEST = ROOT / (
    "comparator_benchmark_execution_v1_"
    "output_normalization_amendment_manifest.json"
)

MD = ROOT / (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "OUTPUT_NORMALIZATION_AMENDMENT.md"
)

IMPLEMENTATION_REL = {
    "adapters":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/adapters.py",
    "environment_recipes":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/environment_recipes.json",
    "toy_validation":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_impl/toy_validation.py",
}

FREEZE_REL = {
    "manifest":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "output_normalization_amendment_manifest.json",
    "documentation":
        "experiments/07_comparative_landscape/"
        "COMPARATOR_BENCHMARK_EXECUTION_V1_"
        "OUTPUT_NORMALIZATION_AMENDMENT.md",
    "freeze_validator":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "output_normalization_amendment_freeze.py",
    "checksum_ledger":
        "experiments/07_comparative_landscape/"
        "comparator_benchmark_execution_v1_"
        "output_normalization_amendment.sha256",
}

EXPECTED_AFTER = {
    "adapters":
        "8d9726c58663f6e80299ff14c9e0c04878473770a8d92d398b902d3f6ddf49c1",
    "environment_recipes":
        "957ab67424610c774d2d863ef2e0ab0797cff715221232547dfcd49c53b58668",
    "toy_validation":
        "76d519a3476d690228136a38f430f0d6d474774623b533bffffe25fd4c3576de",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def current_bytes(relpath: str) -> bytes:
    return (REPO / relpath).read_bytes()


def commit_bytes(commit: str, relpath: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{relpath}"],
        cwd=REPO,
    )


def first_commit_after(parent: str, head: str) -> str | None:
    commits = subprocess.check_output(
        ["git", "rev-list", "--reverse", f"{parent}..{head}"],
        cwd=REPO,
        text=True,
    ).splitlines()
    return commits[0] if commits else None


auth = json.loads(AUTH.read_text())
manifest = json.loads(MANIFEST.read_text())

if auth["authorization_id"] != (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "OUTPUT_NORMALIZATION_AMENDMENT_001"
):
    raise RuntimeError("authorization id differs")

if manifest["freeze_id"] != (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "OUTPUT_NORMALIZATION_AMENDMENT_V1"
):
    raise RuntimeError("freeze id differs")

if manifest["status"] != "FROZEN_AMENDMENT_V1":
    raise RuntimeError("freeze status differs")

if manifest["parent_authorization_commit"] != AUTH_COMMIT:
    raise RuntimeError("freeze parent differs")

if not manifest["authorization_consumed"]:
    raise RuntimeError("authorization not recorded as consumed")

if manifest["next_gate"] != (
    "REAUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V2"
):
    raise RuntimeError("next gate differs")

if manifest["runner_authorization_v1"]["consumed"]:
    raise RuntimeError("runner authorization v1 unexpectedly consumed")

if not manifest["runner_authorization_v1"]["must_not_be_consumed"]:
    raise RuntimeError("runner-v1 supersession boundary absent")

for key, expected in EXPECTED_AFTER.items():
    if manifest["implementation_after_sha256"][key] != expected:
        raise RuntimeError(f"manifest after-hash differs: {key}")

# Baseline blobs at the authorization commit must equal the recorded
# pre-amendment identities.
for key, relpath in IMPLEMENTATION_REL.items():
    observed = digest(commit_bytes(AUTH_COMMIT, relpath))
    expected = auth["baseline_sha256"][key]
    if observed != expected:
        raise RuntimeError(
            f"authorization baseline differs for {key}: "
            f"{observed} != {expected}"
        )

head = subprocess.check_output(
    ["git", "rev-parse", "HEAD"],
    cwd=REPO,
    text=True,
).strip()

ancestor = subprocess.run(
    ["git", "merge-base", "--is-ancestor", AUTH_COMMIT, head],
    cwd=REPO,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

if ancestor.returncode != 0:
    raise RuntimeError(
        "authorization commit is not an ancestor of current HEAD"
    )

freeze_commit = first_commit_after(AUTH_COMMIT, head)

expected_commit_files = (
    set(IMPLEMENTATION_REL.values())
    | set(FREEZE_REL.values())
)

if freeze_commit is None:
    # Pre-commit validation: inspect the working tree.
    status = subprocess.check_output(
        ["git", "status", "--short"],
        cwd=REPO,
        text=True,
    ).splitlines()

    observed_paths = {
        line[3:]
        for line in status
        if line.strip()
    }

    if observed_paths != expected_commit_files:
        raise RuntimeError(
            "pre-commit freeze file boundary differs: "
            f"{sorted(observed_paths)!r}"
        )

    for key, relpath in IMPLEMENTATION_REL.items():
        observed = digest(current_bytes(relpath))
        expected = EXPECTED_AFTER[key]
        if observed != expected:
            raise RuntimeError(
                f"working implementation hash differs for {key}: "
                f"{observed} != {expected}"
            )

    adapters_text = current_bytes(
        IMPLEMENTATION_REL["adapters"]
    ).decode()
    recipes_text = current_bytes(
        IMPLEMENTATION_REL["environment_recipes"]
    ).decode()

else:
    # Post-commit and future validation: the first commit after the
    # authorization must be exactly the amendment freeze commit.
    changed = set(
        subprocess.check_output(
            [
                "git",
                "diff",
                "--name-only",
                AUTH_COMMIT,
                freeze_commit,
            ],
            cwd=REPO,
            text=True,
        ).splitlines()
    )

    if changed != expected_commit_files:
        raise RuntimeError(
            "freeze commit file boundary differs: "
            f"{sorted(changed)!r}"
        )

    for key, relpath in IMPLEMENTATION_REL.items():
        observed = digest(commit_bytes(freeze_commit, relpath))
        expected = EXPECTED_AFTER[key]
        if observed != expected:
            raise RuntimeError(
                f"frozen implementation hash differs for {key}: "
                f"{observed} != {expected}"
            )

    adapters_text = commit_bytes(
        freeze_commit,
        IMPLEMENTATION_REL["adapters"],
    ).decode()

    recipes_text = commit_bytes(
        freeze_commit,
        IMPLEMENTATION_REL["environment_recipes"],
    ).decode()

# Existing adapter functions must remain semantically unchanged;
# exactly three top-level adapter functions are added.
baseline_adapters = commit_bytes(
    AUTH_COMMIT,
    IMPLEMENTATION_REL["adapters"],
).decode()

before_tree = ast.parse(baseline_adapters)
after_tree = ast.parse(adapters_text)

before_funcs = {
    node.name: ast.dump(node, include_attributes=False)
    for node in before_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}

after_funcs = {
    node.name: ast.dump(node, include_attributes=False)
    for node in after_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}

added = set(after_funcs) - set(before_funcs)

expected_added = {
    "map_node_sequences_by_descendant_tips",
    "events_from_projected_node_sequences",
    "snppar_recurrent_sites_from_branch_events",
}

if added != expected_added:
    raise RuntimeError(
        f"adapter function addition set differs: {sorted(added)!r}"
    )

removed = set(before_funcs) - set(after_funcs)
if removed:
    raise RuntimeError(
        f"pre-existing adapter functions removed: {sorted(removed)!r}"
    )

for name, before_dump in before_funcs.items():
    if after_funcs[name] != before_dump:
        raise RuntimeError(
            f"pre-existing adapter function changed unexpectedly: {name}"
        )

# Environment recipe change must be exactly the PastML output-contract
# extension authorized by this amendment.
before_recipes = json.loads(
    commit_bytes(
        AUTH_COMMIT,
        IMPLEMENTATION_REL["environment_recipes"],
    )
)

after_recipes = json.loads(recipes_text)

expected_recipes = json.loads(json.dumps(before_recipes))
expected_recipes["methods"]["PastML"]["output_contract"] = [
    "reconstructed_states.tsv",
    "named.tree_tree.nwk",
]

if after_recipes != expected_recipes:
    raise RuntimeError(
        "environment recipes contain changes beyond the authorized "
        "PastML output-contract extension"
    )

for key, value in manifest["unchanged_contracts"].items():
    if value is not True:
        raise RuntimeError(f"unchanged-contract flag differs: {key}")

for key, value in manifest["execution_boundary"].items():
    if value is not False:
        raise RuntimeError(f"execution boundary differs: {key}")

if "runner implementation authorization v1 remains unconsumed" not in (
    MD.read_text().lower()
):
    raise RuntimeError("runner-v1 boundary absent from freeze documentation")

# Re-run the stronger validation while the freeze is still pending.
# After commit, immutable blob identities above are the historical proof.
if freeze_commit is None:
    toy = subprocess.run(
        [
            sys.executable,
            str(IMPL / "toy_validation.py"),
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if toy.returncode != 0:
        raise RuntimeError(
            "toy validation failed:\n"
            + toy.stdout
            + toy.stderr
        )

    if "TOY_IMPLEMENTATION_VALIDATION=PASS" not in toy.stdout:
        raise RuntimeError("toy validation PASS marker absent")

    pastml = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "comparator_benchmark_execution_v1_"
                "pastml_ambiguity_amendment_test.py"
            ),
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if pastml.returncode != 0:
        raise RuntimeError(
            "PastML ambiguity regression failed:\n"
            + pastml.stdout
            + pastml.stderr
        )

    if "PASTML_AMBIGUITY_AMENDMENT_TEST=PASS" not in pastml.stdout:
        raise RuntimeError(
            "PastML ambiguity regression PASS marker absent"
        )

    # Historical smoke-output integration validation.
    sys.path.insert(0, str(IMPL))
    import adapters

    smoke = (
        REPO
        / "results"
        / "07_comparative_landscape"
        / "comparator_benchmark_environment_smoke_v1"
    )

    # PastML historical schema bridge exists only in-memory here.
    p = smoke / "PastML" / "attempt_02_corrected_tsv"

    lines = (
        p
        / "smoke_output"
        / "reconstructed_states.tsv"
    ).read_text().splitlines()

    if lines[0] != "node\tsite1\tsite2":
        raise RuntimeError("historical PastML smoke schema differs")

    lines[0] = "node\tsite_1\tsite_2"

    states = adapters.parse_tabular_node_states(
        "\n".join(lines) + "\n",
        [1, 2],
    )

    source_tree = (
        p / "smoke_output" / "named.tree_tree.nwk"
    ).read_text()
    benchmark_tree = (
        p / "toy" / "tree.nwk"
    ).read_text()

    mapped = adapters.map_node_sequences_by_descendant_tips(
        source_tree,
        benchmark_tree,
        states,
    )

    events = adapters.events_from_projected_node_sequences(
        benchmark_tree,
        mapped,
        [1, 2],
        method="PastML",
        scenario_id="FREEZE_SMOKE_PASTML",
    )

    if events != []:
        raise RuntimeError(
            "historical ambiguous PastML smoke emitted events"
        )

    # SNPPar.
    s = (
        smoke
        / "SNPPar"
        / "attempt_05_paraphyletic_mapping"
        / "smoke_output"
    )

    sp_events = adapters.parse_snppar_mutation_events(
        (s / "homoplasic_events_all_calls.tsv").read_text(),
        (s / "node_labelled_newick.tre").read_text(),
        scenario_id="FREEZE_SMOKE_SNPPAR",
    )

    sp_sites = adapters.snppar_recurrent_sites_from_branch_events(
        sp_events
    )

    if sp_sites != [
        {
            "position": "20",
            "reported_recurrence_count_if_available": "2",
        }
    ]:
        raise RuntimeError(
            f"historical SNPPar smoke normalization differs: "
            f"{sp_sites!r}"
        )

    # TreeTime.
    t = smoke / "TreeTime"

    tt_sequences = adapters.read_fasta(
        t / "smoke_output" / "ancestral_sequences.fasta"
    )

    tt_source_tree = (
        t / "smoke_output" / "annotated_tree.nexus"
    ).read_text()

    tt_benchmark_tree = (
        t / "toy" / "tree.nwk"
    ).read_text()

    tt_mapped = adapters.map_node_sequences_by_descendant_tips(
        tt_source_tree,
        tt_benchmark_tree,
        tt_sequences,
    )

    tt_events = adapters.events_from_node_sequences(
        tt_benchmark_tree,
        tt_mapped,
        method="TreeTime",
        scenario_id="FREEZE_SMOKE_TREETIME",
    )

    if (
        len(tt_events) != 1
        or tt_events[0]["position"] != "20"
        or tt_events[0]["ancestral_state"] != "A"
        or tt_events[0]["derived_state"] != "G"
    ):
        raise RuntimeError(
            f"historical TreeTime smoke normalization differs: "
            f"{tt_events!r}"
        )

    if adapters.treetime_recurrent_sites_from_branch_events(
        tt_events
    ) != []:
        raise RuntimeError(
            "single historical TreeTime event called recurrent"
        )

print("PASS | output-normalization amendment v1 validates")
print("PASS | authorization consumed exactly once")
print("PASS | exactly three authorized implementation files changed")
print("PASS | all pre-existing adapter functions remain unchanged")
print("PASS | exactly three authorized adapter functions added")
print("PASS | PastML output-contract extension is exact")
print("PASS | PastML genomic-coordinate normalization frozen")
print("PASS | descendant-tip node normalization frozen")
print("PASS | SNPPar recurrent-site normalization frozen")
print("PASS | frozen synthetic and historical-smoke evidence recorded")
print("PASS | canonical benchmark execution remains false")
print("PASS | third-party comparator execution remains false")
print("PASS | benchmark truth access remains false")
print("PASS | runner authorization v1 remains unconsumed and superseded")
print(
    "PASS | next gate = "
    "REAUTHORIZE_COMPARATOR_BENCHMARK_RUNNER_IMPLEMENTATION_V2"
)
