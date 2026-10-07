#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]

AUTH = (
    ROOT
    / "comparator_benchmark_execution_v1_"
      "harness_implementation_authorization.json"
)

MD = (
    ROOT
    / "COMPARATOR_BENCHMARK_EXECUTION_V1_"
      "HARNESS_IMPLEMENTATION_AUTHORIZATION.md"
)

EXPECTED_PARENT = (
    "f4417aed9cafd39c8a0d8c206f61f719b64a4a65"
)

EXPECTED_ID = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "HARNESS_IMPLEMENTATION_001"
)

EXPECTED_FILES = [
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_harness.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_harness_validation.py",

    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_IMPLEMENTATION.md",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


a = json.loads(
    AUTH.read_text()
)

if a["authorization_id"] != EXPECTED_ID:
    raise RuntimeError(
        "authorization id differs"
    )

if a["status"] != "AUTHORIZED_NOT_YET_CONSUMED":
    raise RuntimeError(
        "authorization status differs"
    )

if a["parent_commit"] != EXPECTED_PARENT:
    raise RuntimeError(
        "authorization parent differs"
    )

if a["authorized_files"] != EXPECTED_FILES:
    raise RuntimeError(
        "authorized future file set differs"
    )

if not a[
    "one_time_harness_implementation_authorization"
]:
    raise RuntimeError(
        "one-time authorization flag absent"
    )

if a["rerun_authorized"]:
    raise RuntimeError(
        "rerun unexpectedly authorized"
    )

if a["next_gate"] != (
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_"
    "EXECUTION_HARNESS_V1"
):
    raise RuntimeError(
        "next gate differs"
    )


explicit = a[
    "explicitly_not_authorized"
]

for key in (
    "canonical_benchmark_execution",
    "third_party_comparator_execution",
    "benchmark_truth_access",
    "benchmark_scoring",
    "canonical_result_root_creation",
    "runner_mutation",
    "metric_mutation",
):
    if explicit.get(key) is not True:
        raise RuntimeError(
            f"authorization boundary differs: {key}"
        )


frozen = {
    "dataset_generation_results_design":
        ROOT
        / "comparator_benchmark_dataset_generation_v1_results_design.json",

    "dataset_generation_results_ledger":
        ROOT
        / "comparator_benchmark_dataset_generation_v1_results.sha256",

    "benchmark_design":
        ROOT
        / "comparator_benchmark_execution_v1_design.json",

    "scenario_matrix":
        ROOT
        / "comparator_benchmark_execution_v1_scenario_matrix.tsv",

    "method_matrix":
        ROOT
        / "comparator_benchmark_execution_v1_method_matrix.tsv",

    "generator":
        ROOT
        / "comparator_benchmark_execution_v1_impl/generator.py",

    "adapters":
        ROOT
        / "comparator_benchmark_execution_v1_impl/adapters.py",

    "environment_recipes":
        ROOT
        / "comparator_benchmark_execution_v1_impl/environment_recipes.json",

    "source_pins":
        ROOT
        / "comparator_benchmark_execution_v1_impl/source_pins.tsv",

    "runner":
        ROOT
        / "comparator_benchmark_execution_v1_runner.py",

    "runner_validation":
        ROOT
        / "comparator_benchmark_execution_v1_runner_validation.py",

    "runner_implementation":
        ROOT
        / "COMPARATOR_BENCHMARK_EXECUTION_V1_RUNNER_IMPLEMENTATION.md",
}

for name, path in frozen.items():
    observed = sha256(
        path
    )

    expected = a[
        "frozen_artifacts"
    ][
        name + "_sha256"
    ]

    if observed != expected:
        raise RuntimeError(
            f"frozen artifact changed: {name}"
        )


for name, record in a[
    "runtime_files"
].items():
    path = Path(
        record[
            "path"
        ]
    )

    if not path.exists():
        raise RuntimeError(
            f"runtime file absent: {name}"
        )

    if sha256(path) != record[
        "sha256"
    ]:
        raise RuntimeError(
            f"runtime identity changed: {name}"
        )


source_roots = {
    "ARPIP":
        "/home/rwhite/branchsnv-comparator-src/arpip-smoke",

    "FastML":
        "/home/rwhite/branchsnv-comparator-src/fastml-smoke",

    "HomoplasyFinder":
        "/home/rwhite/branchsnv-comparator-src/homoplasyfinder-smoke",

    "PAML":
        "/home/rwhite/branchsnv-comparator-src/paml-smoke",

    "PastML":
        "/home/rwhite/branchsnv-comparator-src/pastml-1.9.51",

    "POUTINE":
        "/home/rwhite/branchsnv-comparator-src/poutine-smoke",

    "SNPPar":
        "/home/rwhite/branchsnv-comparator-src/snppar-v1.2",

    "TreeTime":
        "/home/rwhite/branchsnv-comparator-src/treetime-v0.12.1",
}

for method, directory in source_roots.items():
    observed = subprocess.check_output(
        [
            "git",
            "-C",
            directory,
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()

    expected = a[
        "source_commits"
    ][
        method
    ]

    if observed != expected:
        raise RuntimeError(
            f"source revision changed: {method}"
        )


if a[
    "scenario_contract"
][
    "scenario_count"
] != 150:
    raise RuntimeError(
        "scenario count differs"
    )

if a[
    "scenario_contract"
][
    "total_invocations"
] != 1200:
    raise RuntimeError(
        "invocation count differs"
    )


if subprocess.run(
    [
        "git",
        "merge-base",
        "--is-ancestor",
        EXPECTED_PARENT,
        "HEAD",
    ],
    cwd=REPO,
).returncode != 0:
    raise RuntimeError(
        "authorization parent is not an ancestor of HEAD"
    )


result_root = (
    REPO
    / "results/07_comparative_landscape/"
      "comparator_benchmark_execution_v1"
)

if result_root.exists():
    raise RuntimeError(
        "canonical result root unexpectedly exists"
    )


# Important: place this probe under HOME rather than /tmp, because
# the sandbox deliberately overlays /tmp with a private tmpfs.
with tempfile.TemporaryDirectory(
    prefix=".branchsnv-harness-auth-",
    dir=Path.home(),
) as raw:

    work = Path(
        raw
    ).resolve()

    subprocess.run(
        [
            "/usr/bin/bwrap",
            "--ro-bind",
            "/",
            "/",
            "--bind",
            str(work),
            str(work),
            "--tmpfs",
            "/tmp",
            "--dev",
            "/dev",
            "--proc",
            "/proc",
            "--unshare-net",
            "--die-with-parent",
            "--chdir",
            str(work),
            "--",
            "/bin/sh",
            "-c",
            (
                "printf x > probe && "
                "test -s probe && "
                "printf y > /tmp/private && "
                "test -s /tmp/private"
            ),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


text = MD.read_text()

for phrase in (
    "Authorized, not yet consumed.",
    "Canonical benchmark execution is still unauthorized.",
    "No canonical S001-S150 benchmark scenario may be executed",
    "Benchmark truth may not be read",
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_EXECUTION_HARNESS_V1",
):
    if phrase not in text:
        raise RuntimeError(
            f"authorization documentation differs: {phrase}"
        )


print(
    "PASS | harness implementation authorization validates"
)
print(
    "PASS | authorization parent is an ancestor of current HEAD"
)
print(
    "PASS | frozen repository identities match"
)
print(
    "PASS | exact runtime file identities match"
)
print(
    "PASS | exact eight source revisions match"
)
print(
    "PASS | strict bubblewrap sandbox contract works"
)
print(
    "PASS | canonical result root remains absent"
)
print(
    "PASS | exactly three future harness artifacts authorized"
)
print(
    "PASS | canonical benchmark execution remains unauthorized"
)
print(
    "PASS | benchmark truth and scoring remain unauthorized"
)
print(
    "PASS | next gate = "
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_EXECUTION_HARNESS_V1"
)
