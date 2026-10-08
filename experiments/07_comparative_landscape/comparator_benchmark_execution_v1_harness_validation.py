#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


import comparator_benchmark_execution_v1_harness as harness


EXPECTED_HEAD = (
    "c7ebf2c031d93991b22100ad3553e3c8c5f9cf45"
)

EXPECTED_AUTH_SHA256 = (
    "934bf529136b34b5d39c1f22816aed19dedcd4b4c1aeddd34d1341e54e752cb5"
)


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(
            message
        )


def expect_failure(
    function,
    *,
    contains: str,
) -> None:
    try:
        function()

    except harness.HarnessError as exc:
        require(
            contains in str(
                exc
            ),
            "failure message differs: "
            f"{exc!s}",
        )

    else:
        raise AssertionError(
            "expected harness failure did not occur"
        )


def sha256(
    path: Path,
) -> str:
    h = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


head = subprocess.check_output(
    [
        "git",
        "rev-parse",
        "HEAD",
    ],
    cwd=REPO,
    text=True,
).strip()

require(
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_HEAD, "HEAD"],
        cwd=REPO, check=False,
    ).returncode == 0,
    f"Amendment 002 commit is not an ancestor of validator HEAD: {head}",
)

require(
    sha256(
        harness.AUTH_PATH
    )
    == EXPECTED_AUTH_SHA256,
    "harness authorization identity differs",
)

print(
    "PASS | exact harness authorization base validates"
)


authorization = harness.verify_authorization_contract()

require(
    authorization[
        "authorization_id"
    ]
    == harness.EXPECTED_AUTHORIZATION_ID,
    "authorization identity differs",
)

require(
    tuple(
        authorization[
            "scenario_contract"
        ][
            "method_order"
        ]
    )
    == harness.authorized_method_order(),
    "authorized method order differs",
)

print(
    "PASS | authorization, frozen runner and runtime identities validate"
)


with tempfile.TemporaryDirectory(
    prefix="branchsnv_harness_stage1_"
) as raw:
    work = Path(
        raw
    )

    matrix = (
        work
        / "synthetic_scenarios.tsv"
    )

    matrix.write_text(
        "scenario_id\tn_tips\n"
        "T001\t4\n"
        "T002\t8\n"
    )

    scenario_ids = harness.read_scenario_ids(
        matrix
    )

    require(
        scenario_ids
        == (
            "T001",
            "T002",
        ),
        "synthetic scenario order differs",
    )

    methods = harness.authorized_method_order()

    input_root = (
        work
        / "inputs"
    )

    result_root = (
        work
        / "results"
    )

    invocations = harness.enumerate_invocations(
        scenario_ids=scenario_ids,
        methods=methods,
        input_root=input_root,
        result_root=result_root,
    )

    require(
        len(
            invocations
        )
        == 16,
        "synthetic invocation count differs",
    )

    require(
        invocations[
            0
        ].ordinal
        == 1
        and invocations[
            0
        ].scenario_id
        == "T001"
        and invocations[
            0
        ].method
        == "ARPIP",
        "first synthetic invocation differs",
    )

    require(
        invocations[
            7
        ].scenario_id
        == "T001"
        and invocations[
            7
        ].method
        == "TreeTime",
        "first synthetic scenario method ordering differs",
    )

    require(
        invocations[
            8
        ].scenario_id
        == "T002"
        and invocations[
            8
        ].method
        == "ARPIP",
        "second synthetic scenario boundary differs",
    )

    require(
        invocations[
            -1
        ].ordinal
        == 16
        and invocations[
            -1
        ].scenario_id
        == "T002"
        and invocations[
            -1
        ].method
        == "TreeTime",
        "last synthetic invocation differs",
    )

    seed_1 = harness.scenario_seed(
        "T001"
    )

    seed_2 = harness.scenario_seed(
        "T002"
    )

    require(
        all(
            invocation.scenario_seed
            == seed_1

            for invocation
            in invocations[:8]
        ),
        "T001 seed differs across methods",
    )

    require(
        all(
            invocation.scenario_seed
            == seed_2

            for invocation
            in invocations[8:]
        ),
        "T002 seed differs across methods",
    )

    require(
        seed_1
        != seed_2,
        "synthetic scenario seeds unexpectedly collide",
    )

    require(
        len(
            {
                invocation.plan_root
                for invocation
                in invocations
            }
        )
        == len(
            invocations
        ),
        "synthetic plan roots are not unique",
    )

    require(
        not input_root.exists(),
        "enumeration unexpectedly created synthetic input root",
    )

    require(
        not result_root.exists(),
        "enumeration unexpectedly created synthetic result root",
    )

    duplicate_matrix = (
        work
        / "duplicate.tsv"
    )

    duplicate_matrix.write_text(
        "scenario_id\n"
        "T001\n"
        "T001\n"
    )

    expect_failure(
        lambda:
            harness.read_scenario_ids(
                duplicate_matrix
            ),
        contains="duplicate",
    )

    missing_column = (
        work
        / "missing_column.tsv"
    )

    missing_column.write_text(
        "identifier\n"
        "T001\n"
    )

    expect_failure(
        lambda:
            harness.read_scenario_ids(
                missing_column
            ),
        contains="scenario_id",
    )

    expect_failure(
        lambda:
            harness.enumerate_invocations(
                scenario_ids=(
                    "T001",
                    "T001",
                ),
                methods=methods,
                input_root=input_root,
                result_root=result_root,
            ),
        contains="duplicates",
    )

    expect_failure(
        lambda:
            harness.enumerate_invocations(
                scenario_ids=(
                    "T001",
                ),
                methods=tuple(
                    reversed(
                        methods
                    )
                ),
                input_root=input_root,
                result_root=result_root,
            ),
        contains="method sequence",
    )

    expect_failure(
        lambda:
            harness.enumerate_invocations(
                scenario_ids=(
                    "T001",
                ),
                methods=methods,
                input_root=input_root,
                result_root=input_root,
            ),
        contains="must differ",
    )

print(
    "PASS | synthetic matrix parsing preserves row order"
)
print(
    "PASS | scenario-major and frozen method-major ordering validates"
)
print(
    "PASS | frozen generator supplies one deterministic seed per scenario"
)
print(
    "PASS | invocation plan paths are unique and enumeration is side-effect free"
)
print(
    "PASS | duplicate, malformed and reordered orchestration inputs fail closed"
)


source = (
    ROOT
    / "comparator_benchmark_execution_v1_harness.py"
).read_text()

for prohibited in (
    "runner.default_executor(",
    "subprocess.Popen(",
    "normalized_predictions.json",
):
    require(
        prohibited not in source,
        "harness unexpectedly contains unauthorized execution pathway: "
        f"{prohibited}",
    )

require(
    source.count(
        "runner.execute_command_plan("
    )
    == 2,
    "Stage 4 and 5C frozen-runner execution-call count differs",
)

require(
    "executor=_stage4_mock_executor"
    in source,
    "Stage 4 frozen-runner call is not pinned to mock executor",
)

require(
    "metrics" not in source.lower(),
    "harness unexpectedly references metrics",
)

require(
    source.count(
        "subprocess.run("
    )
    == 7,
    "Stage 4 through Stage 5F subprocess-call count differs",
)

require(
    source.count(
        "runner.execute_command_plan("
    )
    == 2,
    "Stage 4 and 5C runner integration call count differs",
)

require(
    "executor=_stage4_mock_executor"
    in source,
    "Stage 4 runner call is not pinned to mock executor",
)

require(
    "runner.default_executor("
    not in source,
    "Stage 4 unexpectedly calls default comparator executor",
)

print(
    "PASS | Stage 4 contains one frozen-runner call pinned to mock executor"
)


canonical_result_root = (
    REPO
    / "results/07_comparative_landscape/"
      "comparator_benchmark_execution_v1"
)

require(
    not canonical_result_root.exists(),
    "canonical execution result root unexpectedly exists",
)

print(
    "PASS | canonical execution result root remains absent"
)


changed = {
    line[
        3:
    ]
    for line
    in subprocess.check_output(
        [
            "git",
            "status",
            "--short",
        ],
        cwd=REPO,
        text=True,
    ).splitlines()
    if line.strip()
}

expected_changed = {
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_harness.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_harness_validation.py",

    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_IMPLEMENTATION.md",
}

require(
    changed == expected_changed or changed == set(),
    "changed-file boundary differs: " + repr(sorted(changed)),
)
if not changed:
    tracked = subprocess.check_output(
        ["git", "ls-files", "--", *sorted(expected_changed)],
        cwd=REPO, text=True,
    ).splitlines()
    require(set(tracked) == expected_changed,
            "post-freeze tracked harness file set differs")
    print("PASS | three frozen implementation files tracked; tree clean")
else:
    print("PASS | exactly three authorized harness implementation artifacts changed")

print(
    "HARNESS_STAGE1_VALIDATION=PASS"
)


# ---------------------------------------------------------------------------
# Stage 2 fresh-worker validation.
# ---------------------------------------------------------------------------

worker_one = harness.run_stage2_mock_worker(
    scenario_id="T001",
    method="ARPIP",
    allocation_bytes=24 * 1024 * 1024,
)

worker_two = harness.run_stage2_mock_worker(
    scenario_id="T001",
    method="ARPIP",
    allocation_bytes=32 * 1024 * 1024,
)

require(
    worker_one.worker_pid
    != worker_two.worker_pid,
    "Stage 2 worker process was unexpectedly reused",
)

require(
    worker_one.scenario_seed
    == harness.scenario_seed(
        "T001"
    )
    == worker_two.scenario_seed,
    "Stage 2 fresh-worker seed differs",
)

for result in (
    worker_one,
    worker_two,
):
    require(
        result.child_peak_rss_kib
        > 0,
        "Stage 2 worker recorded no child peak RSS",
    )

    require(
        result.comparator_executed
        is False,
        "Stage 2 mock worker claims comparator execution",
    )

    require(
        result.canonical_input_accessed
        is False,
        "Stage 2 mock worker claims canonical input access",
    )

    require(
        result.benchmark_truth_accessed
        is False,
        "Stage 2 mock worker claims truth access",
    )

require(
    worker_two.child_peak_rss_kib
    >= worker_one.child_peak_rss_kib,
    "larger synthetic allocation unexpectedly produced smaller peak RSS",
)

expect_failure(
    lambda:
        harness.run_stage2_mock_worker(
            scenario_id="S001",
            method="ARPIP",
        ),
    contains="canonical benchmark scenario",
)

expect_failure(
    lambda:
        harness.run_stage2_mock_worker(
            scenario_id="T001",
            method="NOT_A_METHOD",
        ),
    contains="unknown Stage 2",
)

expect_failure(
    lambda:
        harness.run_stage2_mock_worker(
            scenario_id="T001",
            method="ARPIP",
            allocation_bytes=128,
        ),
    contains="between 1 MiB and 64 MiB",
)

canonical_result_root = (
    REPO
    / "results/07_comparative_landscape/"
      "comparator_benchmark_execution_v1"
)

require(
    not canonical_result_root.exists(),
    "Stage 2 unexpectedly created canonical result root",
)

print(
    "PASS | fresh Python worker process is created per synthetic invocation"
)
print(
    "PASS | fresh worker records child peak RSS via RUSAGE_CHILDREN"
)
print(
    "PASS | Stage 2 mock worker is explicitly incapable of canonical S001-S150 use"
)
print(
    "PASS | Stage 2 mock worker executes no comparator and accesses no canonical input/truth"
)
print(
    "PASS | canonical result root remains absent after Stage 2 validation"
)

print(
    "HARNESS_STAGE2_VALIDATION=PASS"
)


# ---------------------------------------------------------------------------
# Stage 3 strict bubblewrap validation.
# ---------------------------------------------------------------------------

with tempfile.TemporaryDirectory(
    prefix=".branchsnv_stage3_command_",
    dir=Path.home(),
) as raw:
    synthetic_root = Path(
        raw
    )

    command = harness.build_stage3_bwrap_command(
        writable_root=synthetic_root,
        child_argv=(
            sys.executable,
            "-c",
            "print('synthetic')",
        ),
    )

    require(
        command[
            0
        ]
        == "/usr/bin/bwrap",
        "Stage 3 bubblewrap executable differs",
    )

    required_tokens = (
        "--ro-bind",
        "--bind",
        "--tmpfs",
        "--dev",
        "--proc",
        "--unshare-net",
        "--die-with-parent",
        "--chdir",
    )

    for token in required_tokens:
        require(
            token in command,
            f"Stage 3 bubblewrap command lacks {token}",
        )

with tempfile.TemporaryDirectory(
    prefix="branchsnv_stage3_tmp_reject_",
    dir="/tmp",
) as raw:
    expect_failure(
        lambda:
            harness.build_stage3_bwrap_command(
                writable_root=Path(
                    raw
                ),
                child_argv=(
                    sys.executable,
                    "-c",
                    "pass",
                ),
            ),
        contains="may not be under /tmp",
    )


sandboxed = (
    harness.run_stage3_sandboxed_mock_worker(
        scenario_id="T003",
        method="TreeTime",
        allocation_bytes=28 * 1024 * 1024,
    )
)

require(
    sandboxed.network_namespace_unshared
    is True,
    "Stage 3 network namespace was not unshared",
)

require(
    sandboxed.worker_network_namespace
    != sandboxed.parent_network_namespace,
    "Stage 3 worker retained parent network namespace",
)

require(
    sandboxed.host_root_read_only
    is True,
    "Stage 3 host root was not read-only",
)

require(
    sandboxed.designated_root_writable
    is True,
    "Stage 3 designated root was not writable",
)

require(
    sandboxed.private_tmp
    is True,
    "Stage 3 private /tmp was not established",
)

require(
    sandboxed.child_peak_rss_kib
    > 0,
    "Stage 3 sandbox worker recorded no child peak RSS",
)

require(
    sandboxed.comparator_executed
    is False,
    "Stage 3 sandbox unexpectedly executed comparator",
)

require(
    sandboxed.canonical_input_accessed
    is False,
    "Stage 3 sandbox unexpectedly accessed canonical input",
)

require(
    sandboxed.benchmark_truth_accessed
    is False,
    "Stage 3 sandbox unexpectedly accessed truth",
)

expect_failure(
    lambda:
        harness.run_stage3_sandboxed_mock_worker(
            scenario_id="S150",
            method="TreeTime",
        ),
    contains="canonical benchmark scenario",
)

canonical_result_root = (
    REPO
    / "results/07_comparative_landscape/"
      "comparator_benchmark_execution_v1"
)

require(
    not canonical_result_root.exists(),
    "Stage 3 unexpectedly created canonical result root",
)

print(
    "PASS | exact bubblewrap isolation command constructs"
)
print(
    "PASS | writable root under /tmp fails closed"
)
print(
    "PASS | sandboxed worker runs in a distinct network namespace"
)
print(
    "PASS | sandbox host root is read-only and designated root is writable"
)
print(
    "PASS | sandbox /tmp is private and hides host /tmp sentinel"
)
print(
    "PASS | sandboxed fresh worker records child peak RSS"
)
print(
    "PASS | Stage 3 sandbox executes no comparator and accesses no canonical input/truth"
)
print(
    "PASS | canonical result root remains absent after Stage 3 validation"
)

print(
    "HARNESS_STAGE3_VALIDATION=PASS"
)


# ---------------------------------------------------------------------------
# Stage 4 frozen runner + mock executor integration.
# ---------------------------------------------------------------------------

runner_mock = (
    harness.run_stage4_runner_mock_integration()
)

require(
    runner_mock.scenario_id
    == "TOY",
    "Stage 4 synthetic runner scenario differs",
)

require(
    runner_mock.method
    == "HomoplasyFinder",
    "Stage 4 synthetic runner method differs",
)

require(
    runner_mock.status
    == "FAILED",
    "Stage 4 runner failure state differs",
)

require(
    runner_mock.failure_type
    == "nonzero_exit",
    "Stage 4 runner failure type differs",
)

require(
    runner_mock.exit_code
    == 23,
    "Stage 4 runner exit code differs",
)

require(
    runner_mock.timed_out
    is False,
    "Stage 4 mock runner unexpectedly timed out",
)

require(
    runner_mock.normalized_predictions_finalized
    is False,
    "Stage 4 failure unexpectedly finalized predictions",
)

require(
    runner_mock.scoring_performed
    is False,
    "Stage 4 failure unexpectedly performed scoring",
)

require(
    runner_mock.stdout_text
    == "stage4 synthetic mock stdout\n",
    "Stage 4 stdout preservation differs",
)

require(
    runner_mock.stderr_text
    == "stage4 synthetic mock stderr\n",
    "Stage 4 stderr preservation differs",
)

require(
    len(
        runner_mock.execution_json_sha256
    )
    == 64,
    "Stage 4 execution record checksum differs",
)

require(
    runner_mock.network_namespace_unshared
    is True,
    "Stage 4 runner worker was not network isolated",
)

require(
    runner_mock.comparator_executed
    is False,
    "Stage 4 unexpectedly executed a comparator",
)

require(
    runner_mock.canonical_input_accessed
    is False,
    "Stage 4 unexpectedly accessed canonical input",
)

require(
    runner_mock.benchmark_truth_accessed
    is False,
    "Stage 4 unexpectedly accessed benchmark truth",
)

require(
    runner_mock.planned_argv[
        0
    ]
    == (
        "/usr/lib/jvm/"
        "java-1.8.0-openjdk-1.8.0.504.b01-1.1.el8_10.x86_64/"
        "jre/bin/java"
    ),
    "Stage 4 frozen HomoplasyFinder Java command differs",
)

require(
    "-jar"
    in runner_mock.planned_argv,
    "Stage 4 frozen HomoplasyFinder command lacks -jar",
)

require(
    (
        "/home/rwhite/branchsnv-comparator-src/"
        "homoplasyfinder-smoke/inst/java/"
        "HomoplasyFinder.jar"
    )
    in runner_mock.planned_argv,
    "Stage 4 frozen HomoplasyFinder jar differs",
)

canonical_result_root = (
    REPO
    / "results/07_comparative_landscape/"
      "comparator_benchmark_execution_v1"
)

require(
    not canonical_result_root.exists(),
    "Stage 4 unexpectedly created canonical result root",
)

print(
    "PASS | synthetic comparator-facing fixture passes through frozen runner"
)
print(
    "PASS | frozen runner constructs authorized HomoplasyFinder command"
)
print(
    "PASS | custom mock executor prevents third-party comparator launch"
)
print(
    "PASS | frozen runner preserves mock stdout/stderr and explicit non-zero failure"
)
print(
    "PASS | failed mocked invocation finalizes no predictions and performs no scoring"
)
print(
    "PASS | frozen runner integration occurs inside network-isolated sandbox"
)
print(
    "PASS | no canonical input or benchmark truth accessed"
)
print(
    "PASS | canonical result root remains absent after Stage 4 validation"
)

print(
    "HARNESS_STAGE4_VALIDATION=PASS"
)


# ---------------------------------------------------------------------------
# Stage 4.5 committed timeout amendment and frozen matrix selection.
# ---------------------------------------------------------------------------

amended_authorization = (
    harness.verify_authorization_contract()
)

require(
    amended_authorization[
        "resource_contract"
    ][
        "timeout_seconds_per_invocation"
    ]
    == 86400,
    "original historical timeout clause unexpectedly modified",
)

timeout_amendment = (
    harness._verify_timeout_amendment_contract(
        amended_authorization
    )
)

require(
    timeout_amendment[
        "amendment_id"
    ]
    == (
        "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_TIMEOUT_AMENDMENT_001"
    ),
    "committed timeout amendment identity differs",
)

require(
    timeout_amendment[
        "status"
    ]
    == "APPROVED_FOR_IMPLEMENTATION_NOT_EXECUTION",
    "timeout amendment status differs",
)

print(
    "PASS | original authorization retained with explicit amendment supersession"
)

timeout_map = harness.frozen_timeout_map()

require(
    len(timeout_map) == 150,
    "timeout map must contain exactly 150 scenarios",
)

require(
    tuple(timeout_map)
    == tuple(
        f"S{i:03d}"
        for i in range(1, 151)
    ),
    "timeout map ordering differs",
)

for index in range(1, 151):
    scenario_id = f"S{index:03d}"

    expected_timeout = (
        3600
        if index <= 100
        else 14400
    )

    require(
        timeout_map[scenario_id]
        == expected_timeout,
        f"timeout selection differs: {scenario_id}",
    )

for scenario_id, expected in (
    ("S001", 3600),
    ("S050", 3600),
    ("S051", 3600),
    ("S100", 3600),
    ("S101", 14400),
    ("S150", 14400),
):
    require(
        harness.timeout_for_scenario(
            scenario_id
        )
        == expected,
        f"boundary timeout differs: {scenario_id}",
    )

print(
    "PASS | 150 frozen scenarios receive exact core/scale timeouts"
)
print(
    "PASS | S050/S051 and S100/S101 boundaries validate"
)

for invalid_id in (
    "TOY",
    "S000",
    "S151",
    "S001 ",
    "",
):
    expect_failure(
        lambda s=invalid_id:
            harness.timeout_for_scenario(s),
        contains="unknown scenario ID",
    )

print(
    "PASS | noncanonical and malformed timeout scenario IDs fail closed"
)

require(
    not (
        REPO
        / "results/07_comparative_landscape/"
          "comparator_benchmark_execution_v1"
    ).exists(),
    "timeout selector unexpectedly created canonical result root",
)

print(
    "PASS | timeout selection reads frozen metadata only"
)
print(
    "PASS | canonical result root remains absent"
)
print(
    "HARNESS_STAGE4_5_VALIDATION=PASS"
)



# ---------------------------------------------------------------------------
# Stage 5A: fail-closed writable-root boundary.
# Only construct bubblewrap argv; never execute a comparator.
# ---------------------------------------------------------------------------

print(
    "===== STAGE 5A WRITABLE-ROOT HARDENING ====="
)

for label, unsafe_root in (
    ("filesystem root", Path("/")),
    ("entire HOME", Path.home()),
    ("repository", REPO),
    ("repository parent", REPO.parent),
):
    expect_failure(
        lambda p=unsafe_root:
            harness.build_stage3_bwrap_command(
                writable_root=p,
                child_argv=(
                    sys.executable,
                    "-c",
                    "pass",
                ),
            ),
        contains="Stage 3 writable root",
    )

    print(
        f"PASS | {label} rejected as writable bind root"
    )


with tempfile.TemporaryDirectory(
    prefix=".branchsnv_stage3_hardening_",
    dir=Path.home(),
) as raw:
    work = Path(raw)

    command = harness.build_stage3_bwrap_command(
        writable_root=work,
        child_argv=(
            sys.executable,
            "-c",
            "pass",
        ),
    )

    bind_index = command.index("--bind")

    require(
        command[bind_index + 1]
        == str(work.resolve())
        and command[bind_index + 2]
        == str(work.resolve()),
        "dedicated writable workspace binding differs",
    )

    print(
        "PASS | private dedicated HOME workspace remains authorized"
    )

    nested = (
        work
        / ".branchsnv_stage3_nested_abcdefgh"
    )

    nested.mkdir(
        mode=0o700
    )

    expect_failure(
        lambda:
            harness.build_stage3_bwrap_command(
                writable_root=nested,
                child_argv=(
                    sys.executable,
                    "-c",
                    "pass",
                ),
            ),
        contains="dedicated direct child",
    )

    print(
        "PASS | nested writable workspace rejected"
    )

    alias = work.with_name(
        work.name + "_alias"
    )

    require(
        not alias.exists()
        and not alias.is_symlink(),
        "synthetic alias unexpectedly exists",
    )

    alias.symlink_to(
        work,
        target_is_directory=True,
    )

    try:
        expect_failure(
            lambda:
                harness.build_stage3_bwrap_command(
                    writable_root=alias,
                    child_argv=(
                        sys.executable,
                        "-c",
                        "pass",
                    ),
                ),
            contains="symlink",
        )
    finally:
        alias.unlink()

    print(
        "PASS | symlinked writable workspace rejected"
    )

    work.chmod(
        0o755
    )

    try:
        expect_failure(
            lambda:
                harness.build_stage3_bwrap_command(
                    writable_root=work,
                    child_argv=(
                        sys.executable,
                        "-c",
                        "pass",
                    ),
                ),
            contains="0700 permissions",
        )
    finally:
        work.chmod(
            0o700
        )

    print(
        "PASS | non-private writable workspace rejected"
    )


with tempfile.TemporaryDirectory(
    prefix="unrelated_directory_",
    dir=Path.home(),
) as raw:
    expect_failure(
        lambda:
            harness.build_stage3_bwrap_command(
                writable_root=Path(raw),
                child_argv=(
                    sys.executable,
                    "-c",
                    "pass",
                ),
            ),
        contains="harness-workspace prefix",
    )

print(
    "PASS | unrelated private HOME directory rejected"
)

require(
    not (
        REPO
        / "results/07_comparative_landscape/"
          "comparator_benchmark_execution_v1"
    ).exists(),
    "sandbox hardening created canonical result root",
)

print(
    "PASS | hardened builder constructs argv only"
)
print(
    "PASS | canonical execution result root remains absent"
)
print(
    "HARNESS_STAGE5A_VALIDATION=PASS"
)



# ---------------------------------------------------------------------------
# Stage 5B: synthetic measured frozen subprocess executor.
# ---------------------------------------------------------------------------

print(
    "===== STAGE 5B SYNTHETIC MEASURED EXECUTOR ====="
)

stage5b_results = {}

for case in ("success", "nonzero", "timeout"):
    result = harness.run_stage5b_synthetic_probe(case)
    stage5b_results[case] = result

    require(
        result["synthetic_subprocess_executed"] is True
        and result["comparator_executed"] is False
        and result["canonical_input_accessed"] is False
        and result["benchmark_truth_accessed"] is False
        and result["scoring_performed"] is False,
        f"Stage 5B case violated scientific boundary: {case}",
    )

    require(
        result["child_peak_rss_kib"] > 0
        and result["child_peak_rss_kib"]
        >= result["child_peak_rss_before_kib"],
        f"Stage 5B resource accounting differs: {case}",
    )

    require(
        result["network_namespace_unshared"] is True
        and result["worker_network_namespace"]
        != result["parent_network_namespace"],
        f"Stage 5B network boundary differs: {case}",
    )

    print(
        "PASS | synthetic "
        + case
        + " | exit="
        + str(result["returncode"])
        + " | timeout="
        + str(result["timed_out"])
        + " | peak_rss_kib="
        + str(result["child_peak_rss_kib"])
    )

require(
    len(
        {
            stage5b_results[case]["worker_pid"]
            for case in stage5b_results
        }
    ) == 3,
    "Stage 5B cases did not use fresh worker PIDs",
)

print(
    "PASS | each synthetic invocation uses a fresh isolated worker"
)

success = stage5b_results["success"]
nonzero = stage5b_results["nonzero"]
timeout = stage5b_results["timeout"]

require(
    success["returncode"] == 0
    and success["stdout"] == "stage5b stdout\n"
    and success["stderr"] == "stage5b stderr\n"
    and success["timed_out"] is False,
    "Stage 5B success streams or exit differ",
)

require(
    nonzero["returncode"] == 23
    and nonzero["stdout"] == "partial stdout\n"
    and nonzero["stderr"] == "expected failure\n"
    and nonzero["timed_out"] is False,
    "Stage 5B nonzero streams or exit differ",
)

require(
    timeout["timed_out"] is True
    and timeout["stderr"] == "timeout stderr\n"
    and timeout["stdout"].startswith("grandchild_pid="),
    "Stage 5B timeout streams differ",
)

print(
    "PASS | frozen runner preserves environment, cwd, stdout and stderr"
)
print(
    "PASS | frozen runner preserves explicit nonzero exit"
)
print(
    "PASS | timeout terminates process-group descendant"
)

for invalid_case in (
    "ARPIP",
    "HomoplasyFinder",
    "S001",
    "production",
    "",
):
    expect_failure(
        lambda c=invalid_case:
            harness.run_stage5b_synthetic_probe(c),
        contains="unknown synthetic test case",
    )

print(
    "PASS | comparator names and canonical scenarios cannot enter Stage 5B"
)

require(
    not (
        REPO
        / "results/07_comparative_landscape/"
          "comparator_benchmark_execution_v1"
    ).exists(),
    "Stage 5B created canonical execution result root",
)

print(
    "PASS | canonical execution result root absent"
)
print(
    "HARNESS_STAGE5B_VALIDATION=PASS"
)



# ---------------------------------------------------------------------------
# Stage 5C: runner provenance + measured synthetic subprocess.
# ---------------------------------------------------------------------------

print(
    "===== STAGE 5C FROZEN-RUNNER INTEGRATION ====="
)

stage5c_results = {}

for case in ("success", "nonzero", "timeout"):
    result = harness.run_stage5c_synthetic_runner_probe(
        case
    )

    stage5c_results[case] = result

    require(
        result["status"] == "FAILED"
        and result["original_command_executed"] is False
        and result["comparator_executed"] is False
        and result["canonical_input_accessed"] is False
        and result["benchmark_truth_accessed"] is False
        and result["scoring_performed"] is False
        and result["normalized_predictions_finalized"] is False,
        "Stage 5C scientific boundary differs: " + case,
    )

    require(
        result["runner_callback_count"] == 1
        and result["child_peak_rss_kib"] > 0
        and result["child_peak_rss_kib"]
        >= result["child_peak_rss_before_kib"],
        "Stage 5C measurement/callback differs: " + case,
    )

    require(
        result["network_namespace_unshared"] is True
        and result["worker_network_namespace"]
        != result["parent_network_namespace"],
        "Stage 5C network isolation differs: " + case,
    )

    require(
        isinstance(result["execution_json_sha256"], str)
        and len(result["execution_json_sha256"]) == 64,
        "Stage 5C execution provenance digest malformed",
    )

    print(
        "PASS | case="
        + case
        + " | exit="
        + str(result["exit_code"])
        + " | failure="
        + str(result["failure_type"])
        + " | peak_rss_kib="
        + str(result["child_peak_rss_kib"])
    )


require(
    len({
        result["worker_pid"]
        for result in stage5c_results.values()
    }) == 3,
    "Stage 5C invocations did not use fresh workers",
)

print(
    "PASS | each runner integration case uses a fresh worker"
)

success = stage5c_results["success"]
nonzero = stage5c_results["nonzero"]
timeout = stage5c_results["timeout"]

require(
    success["exit_code"] == 0
    and success["timed_out"] is False
    and success["stdout"] == "stage5c stdout\n"
    and success["stderr"] == "stage5c stderr\n"
    and success["failure_type"] not in (
        "nonzero_exit",
        "timeout",
        "launch_error",
    ),
    "Stage 5C missing-native-output failure differs",
)

require(
    nonzero["exit_code"] == 23
    and nonzero["failure_type"] == "nonzero_exit"
    and nonzero["timed_out"] is False
    and nonzero["stdout"] == "partial stdout\n"
    and nonzero["stderr"] == "expected failure\n",
    "Stage 5C nonzero failure differs",
)

require(
    timeout["failure_type"] == "timeout"
    and timeout["timed_out"] is True
    and timeout["stdout"].startswith("grandchild_pid=")
    and timeout["stderr"] == "timeout stderr\n",
    "Stage 5C timeout failure differs",
)

print(
    "PASS | zero-exit process without native outputs cannot finalize predictions"
)
print(
    "PASS | nonzero and timeout failures retain frozen runner classification"
)
print(
    "PASS | frozen runner preserves synthetic subprocess streams"
)

for invalid_case in (
    "ARPIP",
    "HomoplasyFinder",
    "S001",
    "S150",
    "production",
    "",
):
    expect_failure(
        lambda c=invalid_case:
            harness.run_stage5c_synthetic_runner_probe(c),
        contains="unknown synthetic test case",
    )

print(
    "PASS | comparator names and canonical scenarios rejected"
)

source = (
    ROOT / "comparator_benchmark_execution_v1_harness.py"
).read_text()

require(
    source.count("runner.execute_command_plan(") == 2,
    "Stage 5C frozen runner integration count differs",
)

require(
    source.count("runner.build_command_plan(") == 2,
    "Stage 5C frozen plan construction count differs",
)

require(
    source.count("subprocess.run(") == 7,
    "Stage 5C subprocess infrastructure count differs",
)

require(
    "executor=synthetic_executor" in source,
    "Stage 5C frozen runner not pinned to synthetic executor",
)

require(
    "executor=_stage4_mock_executor" in source,
    "Stage 4 runner mock executor was modified",
)

require(
    "runner.default_executor(" not in source,
    "Stage 5C directly invokes an unguarded comparator executor",
)

require(
    not (
        REPO
        / "results/07_comparative_landscape/"
          "comparator_benchmark_execution_v1"
    ).exists(),
    "Stage 5C created canonical execution root",
)

print(
    "PASS | execution callbacks remain explicitly synthetic"
)
print(
    "PASS | canonical result root absent"
)
print(
    "HARNESS_STAGE5C_VALIDATION=PASS"
)


# ---------------------------------------------------------------------------
# Stage 5D: frozen dispatch schedule, no execution.
# ---------------------------------------------------------------------------

print(
    "===== STAGE 5D METADATA-ONLY DISPATCH ====="
)

from collections import Counter
from unittest.mock import patch

# Even accidentally reaching an execution function must fail.
with (
    patch.object(
        harness.runner,
        "execute_command_plan",
        side_effect=AssertionError(
            "execution prohibited during Stage 5D"
        ),
    ),
    patch.object(
        harness.runner,
        "default_executor",
        side_effect=AssertionError(
            "subprocess execution prohibited during Stage 5D"
        ),
    ),
):
    dispatch = harness.frozen_dispatch_contract()

require(
    len(dispatch) == 1200,
    "Stage 5D dispatch must contain 1200 invocations",
)

reference = harness.frozen_invocation_plan()
timeout_map = harness.frozen_timeout_map()

require(
    len(reference) == len(dispatch),
    "Stage 5D invocation/reference counts differ",
)

for planned, original in zip(dispatch, reference):
    require(
        (
            planned.ordinal,
            planned.scenario_index,
            planned.method_index,
            planned.scenario_id,
            planned.method,
            planned.scenario_seed,
            planned.input_dir,
            planned.plan_root,
        )
        ==
        (
            original.ordinal,
            original.scenario_index,
            original.method_index,
            original.scenario_id,
            original.method,
            original.scenario_seed,
            original.input_dir,
            original.plan_root,
        ),
        "Stage 5D changed frozen invocation ordering or identity",
    )

    require(
        planned.timeout_seconds
        == timeout_map[planned.scenario_id],
        "Stage 5D timeout differs from approved matrix policy",
    )

print(
    "PASS | dispatch preserves all 1200 frozen invocation identities and order"
)

pairs = [
    (entry.scenario_id, entry.method)
    for entry in dispatch
]

require(
    len(set(pairs)) == 1200,
    "Stage 5D duplicate method/scenario pair",
)

method_order = harness.authorized_method_order()
scenario_ids = harness.frozen_scenario_ids()

for scenario_id in scenario_ids:
    selected = {
        method
        for sid, method in pairs
        if sid == scenario_id
    }

    require(
        selected == set(method_order),
        "Stage 5D method coverage differs: " + scenario_id,
    )

print(
    "PASS | all eight frozen methods occur once for each scenario"
)

counts = Counter(
    entry.timeout_seconds
    for entry in dispatch
)

require(
    counts == Counter({
        3600: 800,
        14400: 400,
    }),
    "Stage 5D core/scale invocation totals differ",
)

print(
    "PASS | exactly 800 core and 400 scale invocations"
)

for scenario_id, expected in (
    ("S001", 3600),
    ("S050", 3600),
    ("S051", 3600),
    ("S100", 3600),
    ("S101", 14400),
    ("S150", 14400),
):
    matched = [
        entry
        for entry in dispatch
        if entry.scenario_id == scenario_id
    ]

    require(
        len(matched) == 8
        and all(
            entry.timeout_seconds == expected
            for entry in matched
        ),
        "Stage 5D scenario boundary differs: " + scenario_id,
    )

print(
    "PASS | core/scale boundaries apply consistently to all methods"
)

require(
    harness.frozen_dispatch_contract() == dispatch,
    "Stage 5D dispatch is not deterministic",
)

print(
    "PASS | repeated dispatch construction is deterministic"
)

with patch.object(
    harness,
    "frozen_timeout_map",
    return_value={"S001": 3600},
):
    expect_failure(
        harness.frozen_dispatch_contract,
        contains="timeout coverage differs",
    )

print(
    "PASS | missing timeout coverage rejected"
)

with patch.object(
    harness,
    "frozen_invocation_plan",
    return_value=(
        reference[0],
        reference[0],
        *reference[2:],
    ),
):
    expect_failure(
        harness.frozen_dispatch_contract,
        contains="duplicate comparator-scenario",
    )

print(
    "PASS | duplicated invocation rejected"
)

with patch.object(
    harness,
    "frozen_invocation_plan",
    return_value=reference[:-1],
):
    expect_failure(
        harness.frozen_dispatch_contract,
        contains="dispatch dimensions differ",
    )

print(
    "PASS | missing invocation rejected"
)

source = (
    ROOT / "comparator_benchmark_execution_v1_harness.py"
).read_text()

require(
    source.count("runner.execute_command_plan(") == 2
    and source.count("runner.build_command_plan(") == 2
    and source.count("subprocess.run(") == 7,
    "Stage 5D added an execution pathway",
)

require(
    "no executable canonical harness CLI is authorized"
    in source,
    "Stage 5D changed canonical execution prohibition",
)

require(
    not (
        REPO
        / "results/07_comparative_landscape/"
          "comparator_benchmark_execution_v1"
    ).exists(),
    "Stage 5D created canonical execution result root",
)

print(
    "PASS | production-shaped dispatch contains no execution pathway"
)
print(
    "PASS | canonical result root remains absent"
)
print(
    "HARNESS_STAGE5D_VALIDATION=PASS"
)


# ---------------------------------------------------------------------------
# Stage 5E: durable synthetic provenance and continuation.
# ---------------------------------------------------------------------------

print(
    "===== STAGE 5E DURABLE SYNTHETIC LEDGER ====="
)

from unittest.mock import patch as stage5e_patch

with tempfile.TemporaryDirectory(
    prefix=".branchsnv_stage5_ledger_",
    dir=Path.home(),
) as raw:
    ledger_root = Path(raw)

    completed = harness.run_stage5e_synthetic_ledger(
        ledger_root
    )

    manifest = completed["manifest"]

    require(
        manifest["invocation_count"] == 3
        and manifest["completion_failure_count"] == 3
        and manifest["scientific_success_count"] == 0
        and manifest["automatic_reruns"] == 0,
        "Stage 5E continuation counts differ",
    )

    require(
        tuple(
            item["synthetic_case"]
            for item in manifest["entries"]
        ) == ("success", "nonzero", "timeout"),
        "Stage 5E continuation order differs",
    )

    for item in manifest["entries"]:
        entry_path = ledger_root / item["path"]

        require(
            entry_path.is_file()
            and harness.sha256_file(entry_path) == item["sha256"],
            "Stage 5E entry checksum differs",
        )

        entry = json.loads(
            entry_path.read_text()
        )

        require(
            entry["execution_scope"] == "SYNTHETIC_VALIDATION_ONLY"
            and entry["status"] == "FAILED"
            and entry["peak_child_rss_kib"] > 0
            and entry["peak_child_rss_bytes"]
                == 1024 * entry["peak_child_rss_kib"]
            and entry["runner_elapsed_seconds"] >= 0
            and entry["original_comparator_command_executed"] is False
            and entry["benchmark_truth_accessed"] is False
            and entry["scoring_performed"] is False,
            "Stage 5E durable entry contract differs",
        )

        require(
            isinstance(entry["runner_execution_record"], dict)
            and len(entry["runner_execution_json_sha256"]) == 64,
            "Stage 5E runner provenance is missing",
        )

    require(
        harness.sha256_file(ledger_root / "manifest.json")
        == completed["manifest_sha256"],
        "Stage 5E manifest checksum differs",
    )

    print(
        "PASS | all three failed synthetic invocations recorded durably"
    )
    print(
        "PASS | exact runner provenance, streams, elapsed time and RSS persisted"
    )
    print(
        "PASS | checksum manifest covers every invocation record"
    )

    expect_failure(
        lambda: harness.run_stage5e_synthetic_ledger(
            ledger_root
        ),
        contains="must be empty",
    )

    print(
        "PASS | automatic rerun and ledger overwrite rejected"
    )


with tempfile.TemporaryDirectory(
    prefix=".branchsnv_stage5_ledger_",
    dir=Path.home(),
) as raw:
    ledger_root = Path(raw)
    original_probe = harness.run_stage5c_synthetic_runner_probe
    observed = []

    def injected_probe(case):
        observed.append(case)

        if case == "nonzero":
            raise harness.HarnessError(
                "synthetic infrastructure stop"
            )

        return original_probe(case)

    with stage5e_patch.object(
        harness,
        "run_stage5c_synthetic_runner_probe",
        side_effect=injected_probe,
    ):
        expect_failure(
            lambda: harness.run_stage5e_synthetic_ledger(
                ledger_root
            ),
            contains="synthetic infrastructure stop",
        )

    require(
        observed == ["success", "nonzero"],
        "Stage 5E unexpected infrastructure failure did not stop dispatch",
    )

    require(
        (ledger_root / "entries/001_success.json").is_file()
        and not (ledger_root / "entries/002_nonzero.json").exists()
        and not (ledger_root / "manifest.json").exists(),
        "Stage 5E partial-ledger fail-closed state differs",
    )

    print(
        "PASS | unexpected harness failure stops subsequent invocations"
    )
    print(
        "PASS | partial records retained without false completion manifest"
    )


require(
    not (
        REPO
        / "results/07_comparative_landscape/"
          "comparator_benchmark_execution_v1"
    ).exists(),
    "Stage 5E created canonical benchmark result root",
)

print(
    "PASS | no canonical execution, benchmark truth access or scoring"
)
print(
    "HARNESS_STAGE5E_VALIDATION=PASS"
)


# ---------------------------------------------------------------------------
# Stage 5F: frozen Amendment 002, private mount root, and complete
# metadata-only dispatch journal. Synthetic-only, no comparator execution.
# ---------------------------------------------------------------------------

print("===== STAGE 5F ISOLATION AND DISPATCH =====")
import re
from unittest.mock import patch as stage5f_patch

security = harness.verify_security_amendment_002()
require(
    security["production_harness_contract"]["planned_invocations"] == 1200
    and security["truth_isolation_contract"]["private_root_required"] is True
    and not any(security["explicit_prohibitions"].values()),
    "Amendment 002 validation boundary differs",
)
print("PASS | Amendment 002 complete identity and prohibition check")

expect_failure(
    lambda: harness.stage5f_production_execution(),
    contains="canonical execution prohibited",
)
expect_failure(
    lambda: harness.stage5f_production_execution(
        authorization=True, scenario_id="S001"),
    contains="canonical execution prohibited",
)
print("PASS | comparator execution blocked even with forged authorization")

# Resolve only a small OS shell dependency closure for a synthetic probe.
# These per-host digests are captured and independently checked immediately
# before launch; they are not a production comparator runtime authorization.
result = subprocess.run(
    ["ldd", "/bin/sh"],
    check=True, capture_output=True, text=True, timeout=15,
)
require(result.returncode == 0, "synthetic shell dependency audit failed")
shell = Path("/bin/sh")
paths = [Path(x) for x in re.findall(r"(/[^\s()]+)", result.stdout)]
paths = list(dict.fromkeys(paths))
require(len(paths) >= 2, "synthetic shell dependency closure incomplete")
system_files = (
    harness.PrivateReadOnlyFile(shell, shell, harness.sha256_file(shell)),
    *(
        harness.PrivateReadOnlyFile(p, p, harness.sha256_file(p))
        for p in paths
    ),
)

with tempfile.TemporaryDirectory(
    prefix=".branchsnv_stage5_private_", dir=Path.home()
) as raw:
    work = Path(raw)
    public = work / "public_input"
    public.mkdir(mode=0o700)
    (public / "test_input.txt").write_text("synthetic public input\n")
    command = harness.build_stage5f_private_root_command(
        work=work, public_input=public, system_files=system_files,
        child_argv=(str(shell), "-c", ":"),
    )
    require(command[:5] == ("/usr/bin/env", "-i", str(harness.BWRAP),
                            "--tmpfs", "/"),
            "private-root command must clear the environment before empty-root bwrap")
    require("--unshare-pid" in command and "--unshare-net" in command,
            "private process/network namespace is missing")
    require("--clearenv" not in command and "--proc" in command
            and command.count("--setenv") == 3,
            "clean launcher or private process/environment boundary missing")
    require("--ro-bind" in command and "--bind" in command,
            "private root has no permitted input/work mounts")
    require(not any(command[i:i+3] == ("--ro-bind", "/", "/")
                    for i in range(len(command)-2)),
            "private root improperly exposes host root")
    require(not any(command[i:i+3] == ("--bind", "/", "/")
                    for i in range(len(command)-2)),
            "private root improperly binds writable host root")

    negative = (
        # Host root, broad system directories and runtime parent mounts.
        (harness.PrivateReadOnlyFile(Path("/"), Path("/"), "0"*64),
         "private-root mount destination is invalid"),
        (harness.PrivateReadOnlyFile(Path.home(), Path("/home"), "0"*64),
         "private-root unapproved runtime mount"),
        (harness.PrivateReadOnlyFile(harness.REPO, Path("/opt/repo"), "0"*64),
         "private-root unapproved runtime mount"),
        (harness.PrivateReadOnlyFile(shell, Path("/run/branchsnv/work"),
                                     harness.sha256_file(shell)),
         "private-root mount destination overlap"),
        (harness.PrivateReadOnlyFile(shell, Path("/run"),
                                     harness.sha256_file(shell)),
         "private-root mount destination overlap"),
        (harness.PrivateReadOnlyFile(shell, Path("/bin/stage5f_wrong_hash"), "f"*64),
         "private-root OS dependency identity changed"),
        (harness.PrivateReadOnlyFile(shell, Path("/tmp/sh"),
                                     harness.sha256_file(shell)),
         "private-root unapproved runtime mount"),
    )
    for bad, reason in negative:
        expect_failure(
            lambda b=bad: harness.build_stage5f_private_root_command(
                work=work, public_input=public,
                system_files=(*system_files, b),
                child_argv=(str(shell), "-c", ":"),
            ), contains=reason,
        )

    expect_failure(
        lambda: harness.build_stage5f_private_root_command(
            work=harness.REPO, public_input=public,
            system_files=system_files, child_argv=(str(shell), "-c", ":"),
        ), contains="dedicated direct child",
    )
    expect_failure(
        lambda: harness.build_stage5f_private_root_command(
            work=work, public_input=work,
            system_files=system_files, child_argv=(str(shell), "-c", ":"),
        ), contains="input escapes",
    )
    second = harness.PrivateReadOnlyFile(shell, shell, harness.sha256_file(shell))
    expect_failure(
        lambda: harness.build_stage5f_private_root_command(
            work=work, public_input=public,
            system_files=(*system_files, second),
            child_argv=(str(shell), "-c", ":"),
        ), contains="destination overlap",
    )
    alias = public / "symlink"
    alias.symlink_to(Path.home() / "synthetic_truth_that_must_not_be_read")
    try:
        expect_failure(
            lambda: harness.build_stage5f_private_root_command(
                work=work, public_input=public, system_files=system_files,
                child_argv=(str(shell), "-c", ":"),
            ), contains="input symlink",
        )
    finally:
        alias.unlink()

    source_file = public / "test_input.txt"
    linked_file = public / "linked_input.txt"
    linked_file.hardlink_to(source_file)
    try:
        expect_failure(
            lambda: harness.build_stage5f_private_root_command(
                work=work, public_input=public, system_files=system_files,
                child_argv=(str(shell), "-c", ":"),
            ), contains="input hardlink",
        )
    finally:
        linked_file.unlink()

print("PASS | host-root, repository, mount overlap and path escapes rejected")
print("PASS | pinned OS files only; input symlinks and hardlinks rejected")

isolation_result = harness.run_stage5f_synthetic_isolation_probe(
    system_files=system_files, shell=shell,
)
require(isolation_result == {
    "sandbox_isolated": True,
    "synthetic_truth_inaccessible": True,
    "synthetic_input_visible": True,
    "comparator_executed": False,
    "canonical_input_accessed": False,
    "benchmark_truth_accessed": False,
}, "Stage 5F private root synthetic isolation failed")
print("PASS | private root hides synthetic truth, host fd and host proc")
print("PASS | explicitly mounted public input remains readable")

with tempfile.TemporaryDirectory(
    prefix=".branchsnv_stage5_dispatch_", dir=Path.home()
) as raw:
    with (
        stage5f_patch.object(
            harness.runner, "execute_command_plan",
            side_effect=AssertionError("canonical execution blocked")),
        stage5f_patch.object(
            harness.runner, "build_command_plan",
            side_effect=AssertionError("command construction blocked")),
    ):
        manifest = harness.run_stage5f_dispatch_dry_run(Path(raw))
    require(
        manifest["planned_count"] == 1200
        and manifest["executed_count"] == 0
        and manifest["core_count"] == 800
        and manifest["scale_count"] == 400
        and len(manifest["entries"]) == 1200,
        "Stage 5F dispatch ledger coverage differs",
    )
    for row in manifest["entries"]:
        path = Path(raw) / row["path"]
        require(path.is_file() and harness.sha256_file(path) == row["sha256"],
                "Stage 5F dispatch ledger checksum differs")
    require((Path(raw)/"manifest.json").is_file(),
            "Stage 5F dispatch completion manifest missing")
    expect_failure(
        lambda: harness.run_stage5f_dispatch_dry_run(Path(raw)),
        contains="ledger root must be empty",
    )
print("PASS | all 1200 dry-run records durable, checksummed and no-clobber")

with tempfile.TemporaryDirectory(
    prefix=".branchsnv_stage5_dispatch_", dir=Path.home()
) as raw:
    expect_failure(
        lambda: harness.run_stage5f_dispatch_dry_run(
            Path(raw), synthetic_interrupt_ordinal=3),
        contains="injected infrastructure stop",
    )
    require((Path(raw)/"entries/0001.json").is_file()
            and (Path(raw)/"entries/0002.json").is_file()
            and not (Path(raw)/"entries/0003.json").exists()
            and not (Path(raw)/"manifest.json").exists(),
            "Stage 5F partial failure journal is incorrect")
print("PASS | fail-closed interruption preserves partial records, no manifest")

source = (ROOT / "comparator_benchmark_execution_v1_harness.py").read_text()
require(source.count("runner.execute_command_plan(") == 2
        and source.count("runner.build_command_plan(") == 2
        and source.count("subprocess.run(") == 7,
        "Stage 5F modified frozen runner dispatch pathways")
require(not (REPO / "results/07_comparative_landscape/"
             "comparator_benchmark_execution_v1").exists(),
        "Stage 5F unexpectedly created canonical result root")
print("PASS | only synthetic subprocess and metadata-only dispatch enabled")
print("PASS | canonical input, truth, scoring and execution blocked")
print("HARNESS_STAGE5F_VALIDATION=PASS")
