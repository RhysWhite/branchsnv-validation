#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
import csv
import hashlib
import json
import os
import resource
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]

IMPL = (
    ROOT
    / "comparator_benchmark_execution_v1_impl"
)

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )

if str(IMPL) not in sys.path:
    sys.path.insert(
        0,
        str(IMPL),
    )


import comparator_benchmark_execution_v1_runner as runner
import adapters
import generator


AUTH_PATH = (
    ROOT
    / "comparator_benchmark_execution_v1_"
      "harness_implementation_authorization.json"
)

FROZEN_SCENARIO_MATRIX = (
    ROOT
    / "comparator_benchmark_execution_v1_"
      "scenario_matrix.tsv"
)

EXPECTED_AUTHORIZATION_ID = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_"
    "HARNESS_IMPLEMENTATION_001"
)

EXPECTED_IMPLEMENTATION_BASE = (
    "6dd22db80ea0f34fad868d196e65b3847749e403"
)

EXPECTED_NEXT_GATE = (
    "IMPLEMENT_AND_FREEZE_COMPARATOR_BENCHMARK_"
    "EXECUTION_HARNESS_V1"
)

AUTHORIZED_HARNESS_FILES = (
    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_harness.py",

    "experiments/07_comparative_landscape/"
    "comparator_benchmark_execution_v1_harness_validation.py",

    "experiments/07_comparative_landscape/"
    "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_IMPLEMENTATION.md",
)


class HarnessError(RuntimeError):
    """Fail-closed harness contract violation."""


@dataclass(frozen=True)
class Invocation:
    ordinal: int
    scenario_index: int
    method_index: int
    scenario_id: str
    method: str
    scenario_seed: int
    input_dir: Path
    plan_root: Path


def sha256_file(
    path: Path,
) -> str:
    h = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


def load_authorization() -> dict[str, object]:
    if not AUTH_PATH.is_file():
        raise HarnessError(
            "harness implementation authorization is absent"
        )

    try:
        value = json.loads(
            AUTH_PATH.read_text()
        )
    except json.JSONDecodeError as exc:
        raise HarnessError(
            "harness implementation authorization is malformed"
        ) from exc

    if not isinstance(
        value,
        dict,
    ):
        raise HarnessError(
            "harness implementation authorization must be an object"
        )

    return value


def _require_mapping(
    value: object,
    *,
    label: str,
) -> Mapping[str, object]:
    if not isinstance(
        value,
        dict,
    ):
        raise HarnessError(
            f"{label} must be an object"
        )

    return value


def verify_authorization_contract() -> dict[str, object]:
    authorization = load_authorization()

    if authorization.get(
        "authorization_id"
    ) != EXPECTED_AUTHORIZATION_ID:
        raise HarnessError(
            "harness authorization identity differs"
        )

    if authorization.get(
        "status"
    ) != "AUTHORIZED_NOT_YET_CONSUMED":
        raise HarnessError(
            "harness authorization status differs"
        )

    if authorization.get(
        "authorized_files"
    ) != list(
        AUTHORIZED_HARNESS_FILES
    ):
        raise HarnessError(
            "authorized harness file set differs"
        )

    if authorization.get(
        "next_gate"
    ) != EXPECTED_NEXT_GATE:
        raise HarnessError(
            "harness authorization next gate differs"
        )

    if authorization.get(
        "one_time_harness_implementation_authorization"
    ) is not True:
        raise HarnessError(
            "one-time harness implementation authorization absent"
        )

    if authorization.get(
        "rerun_authorized"
    ) is not False:
        raise HarnessError(
            "harness implementation rerun unexpectedly authorized"
        )

    explicitly_not_authorized = _require_mapping(
        authorization.get(
            "explicitly_not_authorized"
        ),
        label="explicitly_not_authorized",
    )

    for boundary in (
        "canonical_benchmark_execution",
        "third_party_comparator_execution",
        "benchmark_truth_access",
        "benchmark_scoring",
        "canonical_result_root_creation",
        "runner_mutation",
        "adapter_mutation",
        "generator_mutation",
        "metric_mutation",
    ):
        if explicitly_not_authorized.get(
            boundary
        ) is not True:
            raise HarnessError(
                "authorization boundary differs: "
                f"{boundary}"
            )

    scenario_contract = _require_mapping(
        authorization.get(
            "scenario_contract"
        ),
        label="scenario_contract",
    )

    if scenario_contract.get(
        "scenario_count"
    ) != 150:
        raise HarnessError(
            "frozen scenario count differs"
        )

    if scenario_contract.get(
        "total_invocations"
    ) != 1200:
        raise HarnessError(
            "frozen invocation count differs"
        )

    method_order = scenario_contract.get(
        "method_order"
    )

    if method_order != list(
        runner.METHODS
    ):
        raise HarnessError(
            "authorization method order differs "
            "from frozen runner"
        )

    if scenario_contract.get(
        "master_seed"
    ) != generator.MASTER_SEED:
        raise HarnessError(
            "authorization master seed differs "
            "from frozen generator"
        )

    if scenario_contract.get(
        "scenario_seed_source"
    ) != "frozen generator.scenario_seed":
        raise HarnessError(
            "scenario-seed source contract differs"
        )

    # Reuse the frozen runner's own scientific-identity validator.
    runner.verify_frozen_identities()

    runtime_files = _require_mapping(
        authorization.get(
            "runtime_files"
        ),
        label="runtime_files",
    )

    for name, raw_record in runtime_files.items():
        record = _require_mapping(
            raw_record,
            label=f"runtime_files.{name}",
        )

        raw_path = record.get(
            "path"
        )
        expected_sha256 = record.get(
            "sha256"
        )

        if not isinstance(
            raw_path,
            str,
        ):
            raise HarnessError(
                f"runtime path is malformed: {name}"
            )

        if not isinstance(
            expected_sha256,
            str,
        ):
            raise HarnessError(
                f"runtime SHA-256 is malformed: {name}"
            )

        path = Path(
            raw_path
        )

        if not path.exists():
            raise HarnessError(
                f"runtime file is absent: {name}: {path}"
            )

        observed_sha256 = sha256_file(
            path
        )

        if observed_sha256 != expected_sha256:
            raise HarnessError(
                "runtime file identity differs: "
                f"{name}: {observed_sha256} "
                f"!= {expected_sha256}"
            )

    _verify_timeout_amendment_contract(authorization)

    return authorization


def authorized_method_order() -> tuple[str, ...]:
    authorization = verify_authorization_contract()

    scenario_contract = _require_mapping(
        authorization[
            "scenario_contract"
        ],
        label="scenario_contract",
    )

    raw_methods = scenario_contract[
        "method_order"
    ]

    if not isinstance(
        raw_methods,
        list,
    ):
        raise HarnessError(
            "authorized method order is malformed"
        )

    methods = tuple(
        raw_methods
    )

    if methods != tuple(
        runner.METHODS
    ):
        raise HarnessError(
            "authorized method order differs"
        )

    return methods


def read_scenario_ids(
    path: Path,
) -> tuple[str, ...]:
    if not path.is_file():
        raise HarnessError(
            f"scenario matrix is absent: {path}"
        )

    with path.open(
        "r",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        if (
            reader.fieldnames is None
            or "scenario_id"
            not in reader.fieldnames
        ):
            raise HarnessError(
                "scenario matrix lacks scenario_id column"
            )

        scenario_ids: list[str] = []

        for row_index, row in enumerate(
            reader,
            start=2,
        ):
            scenario_id = row.get(
                "scenario_id"
            )

            if not isinstance(
                scenario_id,
                str,
            ):
                raise HarnessError(
                    "scenario matrix contains malformed "
                    f"scenario_id at row {row_index}"
                )

            scenario_id = scenario_id.strip()

            if not scenario_id:
                raise HarnessError(
                    "scenario matrix contains empty "
                    f"scenario_id at row {row_index}"
                )

            scenario_ids.append(
                scenario_id
            )

    if len(
        set(
            scenario_ids
        )
    ) != len(
        scenario_ids
    ):
        raise HarnessError(
            "scenario matrix contains duplicate scenario IDs"
        )

    return tuple(
        scenario_ids
    )


def frozen_scenario_ids() -> tuple[str, ...]:
    authorization = verify_authorization_contract()

    scenario_contract = _require_mapping(
        authorization[
            "scenario_contract"
        ],
        label="scenario_contract",
    )

    scenario_ids = read_scenario_ids(
        FROZEN_SCENARIO_MATRIX
    )

    expected_count = scenario_contract[
        "scenario_count"
    ]

    if len(
        scenario_ids
    ) != expected_count:
        raise HarnessError(
            "frozen scenario-matrix row count differs"
        )

    return scenario_ids


def scenario_seed(
    scenario_id: str,
) -> int:
    if not isinstance(
        scenario_id,
        str,
    ) or not scenario_id:
        raise HarnessError(
            "scenario ID must be a non-empty string"
        )

    # Scientific seed derivation remains owned by the frozen generator.
    return generator.scenario_seed(
        scenario_id
    )


def _resolved_without_requirement(
    path: Path,
) -> Path:
    return path.expanduser().resolve(
        strict=False
    )


def enumerate_invocations(
    *,
    scenario_ids: Iterable[str],
    methods: Iterable[str],
    input_root: Path,
    result_root: Path,
) -> tuple[Invocation, ...]:
    scenario_ids = tuple(
        scenario_ids
    )
    methods = tuple(
        methods
    )

    if not scenario_ids:
        raise HarnessError(
            "scenario sequence is empty"
        )

    if any(
        not isinstance(
            scenario_id,
            str,
        )
        or not scenario_id
        for scenario_id
        in scenario_ids
    ):
        raise HarnessError(
            "scenario sequence contains an invalid ID"
        )

    if len(
        set(
            scenario_ids
        )
    ) != len(
        scenario_ids
    ):
        raise HarnessError(
            "scenario sequence contains duplicates"
        )

    expected_methods = authorized_method_order()

    if methods != expected_methods:
        raise HarnessError(
            "method sequence differs from frozen authorization"
        )

    input_root = _resolved_without_requirement(
        Path(
            input_root
        )
    )

    result_root = _resolved_without_requirement(
        Path(
            result_root
        )
    )

    if input_root == result_root:
        raise HarnessError(
            "input and result roots must differ"
        )

    if (
        input_root == result_root
        or input_root in result_root.parents
    ):
        raise HarnessError(
            "result root may not be inside the input root"
        )

    invocations: list[Invocation] = []

    ordinal = 0

    for scenario_index, scenario_id in enumerate(
        scenario_ids,
        start=1,
    ):
        seed = scenario_seed(
            scenario_id
        )

        for method_index, method in enumerate(
            methods,
            start=1,
        ):
            ordinal += 1

            invocations.append(
                Invocation(
                    ordinal=ordinal,
                    scenario_index=scenario_index,
                    method_index=method_index,
                    scenario_id=scenario_id,
                    method=method,
                    scenario_seed=seed,
                    input_dir=(
                        input_root
                        / scenario_id
                    ),
                    plan_root=(
                        result_root
                        / scenario_id
                        / method
                    ),
                )
            )

    return tuple(
        invocations
    )


def frozen_invocation_plan() -> tuple[Invocation, ...]:
    authorization = verify_authorization_contract()

    scenario_contract = _require_mapping(
        authorization[
            "scenario_contract"
        ],
        label="scenario_contract",
    )

    raw_input_root = authorization.get(
        "canonical_input_root"
    )
    raw_result_root = authorization.get(
        "canonical_result_root"
    )

    if not isinstance(
        raw_input_root,
        str,
    ):
        raise HarnessError(
            "canonical input root is malformed"
        )

    if not isinstance(
        raw_result_root,
        str,
    ):
        raise HarnessError(
            "canonical result root is malformed"
        )

    invocations = enumerate_invocations(
        scenario_ids=frozen_scenario_ids(),
        methods=authorized_method_order(),
        input_root=REPO / raw_input_root,
        result_root=REPO / raw_result_root,
    )

    if len(
        invocations
    ) != scenario_contract[
        "total_invocations"
    ]:
        raise HarnessError(
            "frozen invocation-plan size differs"
        )

    return invocations


# ---------------------------------------------------------------------------
# Stage 2: fresh synthetic worker-process and peak-RSS infrastructure.
#
# This stage is deliberately incapable of comparator execution.  The only
# child process permitted here is a synthetic Python memory-allocation probe
# used to validate invocation-specific RUSAGE_CHILDREN accounting.
# ---------------------------------------------------------------------------

STAGE2_MOCK_WORKER_MODE = (
    "STAGE2_SYNTHETIC_MOCK_ONLY"
)


@dataclass(frozen=True)
class MockWorkerResult:
    scenario_id: str
    method: str
    scenario_seed: int
    worker_pid: int
    child_peak_rss_before_kib: int
    child_peak_rss_kib: int
    comparator_executed: bool
    canonical_input_accessed: bool
    benchmark_truth_accessed: bool


def _validate_stage2_mock_identity(
    *,
    scenario_id: str,
    method: str,
    scenario_seed_value: int,
) -> None:
    if not isinstance(
        scenario_id,
        str,
    ) or not scenario_id:
        raise HarnessError(
            "mock-worker scenario ID must be a non-empty string"
        )

    # Canonical S001-S150 scenarios are explicitly forbidden during
    # harness implementation/validation.
    if (
        len(scenario_id) == 4
        and scenario_id.startswith("S")
        and scenario_id[1:].isdigit()
        and 1 <= int(scenario_id[1:]) <= 150
    ):
        raise HarnessError(
            "canonical benchmark scenario is forbidden "
            "in Stage 2 mock worker"
        )

    if method not in runner.METHODS:
        raise HarnessError(
            f"unknown Stage 2 mock-worker method: {method}"
        )

    if (
        isinstance(
            scenario_seed_value,
            bool,
        )
        or not isinstance(
            scenario_seed_value,
            int,
        )
        or scenario_seed_value < 0
    ):
        raise HarnessError(
            "mock-worker scenario seed must be "
            "a non-negative integer"
        )


def _run_synthetic_memory_child(
    allocation_bytes: int,
) -> tuple[int, int]:
    if (
        isinstance(
            allocation_bytes,
            bool,
        )
        or not isinstance(
            allocation_bytes,
            int,
        )
        or allocation_bytes < 1024 * 1024
        or allocation_bytes > 64 * 1024 * 1024
    ):
        raise HarnessError(
            "synthetic allocation must be between "
            "1 MiB and 64 MiB"
        )

    before = resource.getrusage(
        resource.RUSAGE_CHILDREN
    ).ru_maxrss

    code = (
        "import sys\n"
        "n = int(sys.argv[1])\n"
        "x = bytearray(n)\n"
        "for i in range(0, n, 4096):\n"
        "    x[i] = 1\n"
        "print(len(x))\n"
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(
                allocation_bytes
            ),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
    )

    if completed.returncode != 0:
        raise HarnessError(
            "synthetic memory child failed: "
            + completed.stderr.strip()
        )

    after = resource.getrusage(
        resource.RUSAGE_CHILDREN
    ).ru_maxrss

    if after <= 0:
        raise HarnessError(
            "RUSAGE_CHILDREN did not report peak RSS"
        )

    return (
        int(
            before
        ),
        int(
            after
        ),
    )


def _stage2_mock_worker(
    request: Mapping[str, object],
) -> dict[str, object]:
    required = {
        "mode",
        "scenario_id",
        "method",
        "scenario_seed",
        "allocation_bytes",
    }

    if set(
        request
    ) != required:
        raise HarnessError(
            "Stage 2 mock-worker request keys differ"
        )

    if request[
        "mode"
    ] != STAGE2_MOCK_WORKER_MODE:
        raise HarnessError(
            "Stage 2 mock-worker mode differs"
        )

    scenario_id = request[
        "scenario_id"
    ]
    method = request[
        "method"
    ]
    scenario_seed_value = request[
        "scenario_seed"
    ]
    allocation_bytes = request[
        "allocation_bytes"
    ]

    if not isinstance(
        scenario_id,
        str,
    ):
        raise HarnessError(
            "Stage 2 scenario ID is malformed"
        )

    if not isinstance(
        method,
        str,
    ):
        raise HarnessError(
            "Stage 2 method is malformed"
        )

    _validate_stage2_mock_identity(
        scenario_id=scenario_id,
        method=method,
        scenario_seed_value=scenario_seed_value,
    )

    if not isinstance(
        allocation_bytes,
        int,
    ):
        raise HarnessError(
            "Stage 2 allocation is malformed"
        )

    before, after = (
        _run_synthetic_memory_child(
            allocation_bytes
        )
    )

    return {
        "schema_version":
            1,

        "worker_mode":
            STAGE2_MOCK_WORKER_MODE,

        "scenario_id":
            scenario_id,

        "method":
            method,

        "scenario_seed":
            scenario_seed_value,

        "worker_pid":
            os.getpid(),

        "child_peak_rss_before_kib":
            before,

        "child_peak_rss_kib":
            after,

        "comparator_executed":
            False,

        "canonical_input_accessed":
            False,

        "benchmark_truth_accessed":
            False,

        "scoring_performed":
            False,
    }


def _stage2_mock_worker_file_entry(
    request_path: Path,
    response_path: Path,
) -> None:
    if response_path.exists():
        raise HarnessError(
            "Stage 2 mock-worker response already exists"
        )

    try:
        raw = json.loads(
            request_path.read_text()
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise HarnessError(
            "Stage 2 mock-worker request is unreadable"
        ) from exc

    if not isinstance(
        raw,
        dict,
    ):
        raise HarnessError(
            "Stage 2 mock-worker request must be an object"
        )

    response = _stage2_mock_worker(
        raw
    )

    response_path.write_text(
        json.dumps(
            response,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def run_stage2_mock_worker(
    *,
    scenario_id: str,
    method: str,
    allocation_bytes: int = 24 * 1024 * 1024,
) -> MockWorkerResult:
    seed = scenario_seed(
        scenario_id
    )

    _validate_stage2_mock_identity(
        scenario_id=scenario_id,
        method=method,
        scenario_seed_value=seed,
    )

    request = {
        "mode":
            STAGE2_MOCK_WORKER_MODE,

        "scenario_id":
            scenario_id,

        "method":
            method,

        "scenario_seed":
            seed,

        "allocation_bytes":
            allocation_bytes,
    }

    with tempfile.TemporaryDirectory(
        prefix="branchsnv_stage2_worker_"
    ) as raw:
        work = Path(
            raw
        )

        request_path = (
            work
            / "request.json"
        )

        response_path = (
            work
            / "response.json"
        )

        request_path.write_text(
            json.dumps(
                request,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(
                    Path(
                        __file__
                    ).resolve()
                ),
                "--stage2-mock-worker",
                str(
                    request_path
                ),
                str(
                    response_path
                ),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )

        if completed.returncode != 0:
            raise HarnessError(
                "fresh Stage 2 worker failed: "
                + completed.stderr.strip()
            )

        if not response_path.is_file():
            raise HarnessError(
                "fresh Stage 2 worker produced no response"
            )

        try:
            response = json.loads(
                response_path.read_text()
            )
        except json.JSONDecodeError as exc:
            raise HarnessError(
                "fresh Stage 2 worker response is malformed"
            ) from exc

    if not isinstance(
        response,
        dict,
    ):
        raise HarnessError(
            "fresh Stage 2 worker response must be an object"
        )

    if response.get(
        "worker_mode"
    ) != STAGE2_MOCK_WORKER_MODE:
        raise HarnessError(
            "fresh Stage 2 worker mode differs"
        )

    if response.get(
        "scenario_id"
    ) != scenario_id:
        raise HarnessError(
            "fresh Stage 2 worker scenario differs"
        )

    if response.get(
        "method"
    ) != method:
        raise HarnessError(
            "fresh Stage 2 worker method differs"
        )

    if response.get(
        "scenario_seed"
    ) != seed:
        raise HarnessError(
            "fresh Stage 2 worker seed differs"
        )

    for forbidden_true in (
        "comparator_executed",
        "canonical_input_accessed",
        "benchmark_truth_accessed",
        "scoring_performed",
    ):
        if response.get(
            forbidden_true
        ) is not False:
            raise HarnessError(
                "Stage 2 mock worker crossed forbidden boundary: "
                f"{forbidden_true}"
            )

    worker_pid = response.get(
        "worker_pid"
    )
    before = response.get(
        "child_peak_rss_before_kib"
    )
    peak = response.get(
        "child_peak_rss_kib"
    )

    for label, value in (
        (
            "worker_pid",
            worker_pid,
        ),
        (
            "child_peak_rss_before_kib",
            before,
        ),
        (
            "child_peak_rss_kib",
            peak,
        ),
    ):
        if (
            isinstance(
                value,
                bool,
            )
            or not isinstance(
                value,
                int,
            )
            or value < 0
        ):
            raise HarnessError(
                f"Stage 2 worker {label} is malformed"
            )

    if peak <= 0:
        raise HarnessError(
            "fresh Stage 2 worker recorded no child peak RSS"
        )

    return MockWorkerResult(
        scenario_id=scenario_id,
        method=method,
        scenario_seed=seed,
        worker_pid=worker_pid,
        child_peak_rss_before_kib=before,
        child_peak_rss_kib=peak,
        comparator_executed=False,
        canonical_input_accessed=False,
        benchmark_truth_accessed=False,
    )



# ---------------------------------------------------------------------------
# Stage 3: strict bubblewrap sandbox infrastructure.
#
# This stage remains synthetic-only.  It proves the exact isolation envelope
# required for later canonical comparator execution, but does not call any
# frozen runner execution function and cannot execute a comparator.
# ---------------------------------------------------------------------------

STAGE3_SANDBOX_WORKER_MODE = (
    "STAGE3_SYNTHETIC_SANDBOX_ONLY"
)

BWRAP = Path(
    "/usr/bin/bwrap"
)


@dataclass(frozen=True)
class SandboxedMockWorkerResult:
    scenario_id: str
    method: str
    scenario_seed: int
    worker_pid: int
    child_peak_rss_kib: int
    parent_network_namespace: str
    worker_network_namespace: str
    network_namespace_unshared: bool
    host_root_read_only: bool
    designated_root_writable: bool
    private_tmp: bool
    comparator_executed: bool
    canonical_input_accessed: bool
    benchmark_truth_accessed: bool


def _network_namespace_identity() -> str:
    path = Path(
        "/proc/self/ns/net"
    )

    try:
        return os.readlink(
            path
        )
    except OSError as exc:
        raise HarnessError(
            "network namespace identity is unavailable"
        ) from exc


def _validate_stage3_writable_root(
    path: Path,
) -> Path:
    if not isinstance(path, Path):
        raise HarnessError(
            "Stage 3 writable root must be a Path"
        )

    if not path.is_absolute():
        raise HarnessError(
            "Stage 3 writable root must be absolute"
        )

    try:
        resolved = path.resolve(
            strict=True
        )
    except (FileNotFoundError, OSError) as exc:
        raise HarnessError(
            "Stage 3 writable root does not exist or cannot be resolved"
        ) from exc

    if not resolved.is_dir():
        raise HarnessError(
            "Stage 3 writable root is not a directory"
        )

    tmp = Path("/tmp")

    if (
        resolved == tmp
        or tmp in resolved.parents
    ):
        raise HarnessError(
            "Stage 3 writable root may not be under /tmp "
            "because /tmp is replaced by a private tmpfs"
        )

    home = Path.home().resolve(
        strict=True
    )

    # A writable bind of /, HOME, a repository, or an ancestor
    # would undermine the read-only filesystem boundary.
    #
    # TemporaryDirectory(dir=Path.home()) creates a private
    # direct child of HOME. Never authorize broader roots.
    if resolved.parent != home:
        raise HarnessError(
            "Stage 3 writable root must be a dedicated "
            "direct child of HOME"
        )

    if path.is_symlink() or path.name != resolved.name:
        raise HarnessError(
            "Stage 3 writable root must not be a symlink"
        )

    approved_prefixes = (
        ".branchsnv_stage3_",
        ".branchsnv_stage4_",
        ".branchsnv_stage5_",
        "branchsnv_stage3_",
        "branchsnv_stage4_",
        "branchsnv_stage5_",
    )

    matching_prefixes = [
        prefix
        for prefix in approved_prefixes
        if resolved.name.startswith(prefix)
    ]

    if len(matching_prefixes) != 1:
        raise HarnessError(
            "Stage 3 writable root lacks a dedicated "
            "harness-workspace prefix"
        )

    suffix = resolved.name[
        len(matching_prefixes[0]):
    ]

    if (
        len(suffix) < 8
        or any(
            not (
                character.islower()
                or character.isdigit()
                or character == "_"
            )
            for character in suffix
        )
    ):
        raise HarnessError(
            "Stage 3 writable root workspace name is malformed"
        )

    metadata = resolved.stat()

    if metadata.st_uid != os.getuid():
        raise HarnessError(
            "Stage 3 writable root must belong to the current user"
        )

    if metadata.st_mode & 0o777 != 0o700:
        raise HarnessError(
            "Stage 3 writable root must have private 0700 permissions"
        )

    return resolved


def build_stage3_bwrap_command(
    *,
    writable_root: Path,
    child_argv: tuple[str, ...],
) -> tuple[str, ...]:
    verify_authorization_contract()

    if not BWRAP.is_file():
        raise HarnessError(
            "authorized bubblewrap executable is absent"
        )

    writable_root = (
        _validate_stage3_writable_root(
            writable_root
        )
    )

    if (
        not isinstance(
            child_argv,
            tuple,
        )
        or not child_argv
        or any(
            not isinstance(
                item,
                str,
            )
            or not item
            for item
            in child_argv
        )
    ):
        raise HarnessError(
            "Stage 3 child argv must be a non-empty tuple of strings"
        )

    return (
        str(
            BWRAP
        ),
        "--ro-bind",
        "/",
        "/",
        "--bind",
        str(
            writable_root
        ),
        str(
            writable_root
        ),
        "--tmpfs",
        "/tmp",
        "--dev",
        "/dev",
        "--proc",
        "/proc",
        "--unshare-net",
        "--die-with-parent",
        "--chdir",
        str(
            writable_root
        ),
        "--setenv",
        "PYTHONDONTWRITEBYTECODE",
        "1",
        "--setenv",
        "BRANCHSNV_STAGE3_SANDBOX",
        "1",
        "--",
        *child_argv,
    )


def _stage3_sandbox_worker(
    request: Mapping[str, object],
) -> dict[str, object]:
    required = {
        "mode",
        "scenario_id",
        "method",
        "scenario_seed",
        "allocation_bytes",
        "writable_root",
        "host_tmp_sentinel",
        "parent_network_namespace",
    }

    if set(
        request
    ) != required:
        raise HarnessError(
            "Stage 3 sandbox-worker request keys differ"
        )

    if request[
        "mode"
    ] != STAGE3_SANDBOX_WORKER_MODE:
        raise HarnessError(
            "Stage 3 sandbox-worker mode differs"
        )

    if os.environ.get(
        "BRANCHSNV_STAGE3_SANDBOX"
    ) != "1":
        raise HarnessError(
            "Stage 3 worker is not inside authorized sandbox"
        )

    scenario_id = request[
        "scenario_id"
    ]
    method = request[
        "method"
    ]
    seed = request[
        "scenario_seed"
    ]
    allocation_bytes = request[
        "allocation_bytes"
    ]
    raw_writable_root = request[
        "writable_root"
    ]
    raw_host_tmp_sentinel = request[
        "host_tmp_sentinel"
    ]
    parent_network_namespace = request[
        "parent_network_namespace"
    ]

    if not isinstance(
        scenario_id,
        str,
    ):
        raise HarnessError(
            "Stage 3 scenario ID is malformed"
        )

    if not isinstance(
        method,
        str,
    ):
        raise HarnessError(
            "Stage 3 method is malformed"
        )

    _validate_stage2_mock_identity(
        scenario_id=scenario_id,
        method=method,
        scenario_seed_value=seed,
    )

    if not isinstance(
        allocation_bytes,
        int,
    ):
        raise HarnessError(
            "Stage 3 allocation is malformed"
        )

    if not isinstance(
        raw_writable_root,
        str,
    ):
        raise HarnessError(
            "Stage 3 writable root is malformed"
        )

    if not isinstance(
        raw_host_tmp_sentinel,
        str,
    ):
        raise HarnessError(
            "Stage 3 host tmp sentinel is malformed"
        )

    if not isinstance(
        parent_network_namespace,
        str,
    ):
        raise HarnessError(
            "Stage 3 parent network namespace is malformed"
        )

    writable_root = Path(
        raw_writable_root
    ).resolve(
        strict=True
    )

    if Path.cwd().resolve() != writable_root:
        raise HarnessError(
            "Stage 3 sandbox cwd differs from designated writable root"
        )

    worker_network_namespace = (
        _network_namespace_identity()
    )

    if (
        worker_network_namespace
        == parent_network_namespace
    ):
        raise HarnessError(
            "Stage 3 network namespace was not unshared"
        )

    # The host-side /tmp sentinel must disappear behind the sandbox's
    # private tmpfs.
    if Path(
        raw_host_tmp_sentinel
    ).exists():
        raise HarnessError(
            "Stage 3 private /tmp did not hide host sentinel"
        )

    private_tmp_probe = Path(
        "/tmp/branchsnv_stage3_private_probe"
    )

    private_tmp_probe.write_text(
        "private\n"
    )

    if not private_tmp_probe.is_file():
        raise HarnessError(
            "Stage 3 private /tmp is not writable"
        )

    private_tmp_probe.unlink()

    designated_probe = (
        writable_root
        / "stage3_designated_write_probe.txt"
    )

    designated_probe.write_text(
        "writable\n"
    )

    if not designated_probe.is_file():
        raise HarnessError(
            "Stage 3 designated root is not writable"
        )

    designated_probe.unlink()

    # An ordinary path elsewhere in the repository must remain read-only.
    root_probe = (
        ROOT
        / ".branchsnv_stage3_read_only_probe"
    )

    if root_probe.exists():
        raise HarnessError(
            "Stage 3 read-only probe unexpectedly pre-exists"
        )

    host_root_read_only = False

    try:
        root_probe.write_text(
            "must-fail\n"
        )

    except OSError:
        host_root_read_only = True

    else:
        try:
            root_probe.unlink()
        finally:
            raise HarnessError(
                "Stage 3 host root was unexpectedly writable"
            )

    before, peak = (
        _run_synthetic_memory_child(
            allocation_bytes
        )
    )

    return {
        "schema_version":
            1,

        "worker_mode":
            STAGE3_SANDBOX_WORKER_MODE,

        "scenario_id":
            scenario_id,

        "method":
            method,

        "scenario_seed":
            seed,

        "worker_pid":
            os.getpid(),

        "child_peak_rss_before_kib":
            before,

        "child_peak_rss_kib":
            peak,

        "parent_network_namespace":
            parent_network_namespace,

        "worker_network_namespace":
            worker_network_namespace,

        "network_namespace_unshared":
            True,

        "host_root_read_only":
            host_root_read_only,

        "designated_root_writable":
            True,

        "private_tmp":
            True,

        "comparator_executed":
            False,

        "canonical_input_accessed":
            False,

        "benchmark_truth_accessed":
            False,

        "scoring_performed":
            False,
    }


def _stage3_sandbox_worker_file_entry(
    request_path: Path,
    response_path: Path,
) -> None:
    if response_path.exists():
        raise HarnessError(
            "Stage 3 sandbox-worker response already exists"
        )

    try:
        raw = json.loads(
            request_path.read_text()
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise HarnessError(
            "Stage 3 sandbox-worker request is unreadable"
        ) from exc

    if not isinstance(
        raw,
        dict,
    ):
        raise HarnessError(
            "Stage 3 sandbox-worker request must be an object"
        )

    response = _stage3_sandbox_worker(
        raw
    )

    response_path.write_text(
        json.dumps(
            response,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def run_stage3_sandboxed_mock_worker(
    *,
    scenario_id: str,
    method: str,
    allocation_bytes: int = 24 * 1024 * 1024,
) -> SandboxedMockWorkerResult:
    authorization = (
        verify_authorization_contract()
    )

    sandbox_contract = _require_mapping(
        authorization[
            "sandbox_contract"
        ],
        label="sandbox_contract",
    )

    if sandbox_contract.get(
        "tool"
    ) != str(
        BWRAP
    ):
        raise HarnessError(
            "authorized bubblewrap path differs"
        )

    if sandbox_contract.get(
        "network_disabled"
    ) is not True:
        raise HarnessError(
            "authorized network-isolation contract differs"
        )

    seed = scenario_seed(
        scenario_id
    )

    _validate_stage2_mock_identity(
        scenario_id=scenario_id,
        method=method,
        scenario_seed_value=seed,
    )

    parent_network_namespace = (
        _network_namespace_identity()
    )

    sentinel_handle = tempfile.NamedTemporaryFile(
        mode="w",
        prefix="branchsnv_stage3_host_tmp_",
        dir="/tmp",
        delete=False,
    )

    try:
        sentinel_handle.write(
            "host tmp sentinel\n"
        )
        sentinel_handle.close()

        sentinel_path = Path(
            sentinel_handle.name
        )

        with tempfile.TemporaryDirectory(
            prefix=".branchsnv_stage3_worker_",
            dir=Path.home(),
        ) as raw:
            work = Path(
                raw
            ).resolve()

            request_path = (
                work
                / "request.json"
            )

            response_path = (
                work
                / "response.json"
            )

            request = {
                "mode":
                    STAGE3_SANDBOX_WORKER_MODE,

                "scenario_id":
                    scenario_id,

                "method":
                    method,

                "scenario_seed":
                    seed,

                "allocation_bytes":
                    allocation_bytes,

                "writable_root":
                    str(
                        work
                    ),

                "host_tmp_sentinel":
                    str(
                        sentinel_path
                    ),

                "parent_network_namespace":
                    parent_network_namespace,
            }

            request_path.write_text(
                json.dumps(
                    request,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )

            child_argv = (
                sys.executable,
                str(
                    Path(
                        __file__
                    ).resolve()
                ),
                "--stage3-sandbox-worker",
                str(
                    request_path
                ),
                str(
                    response_path
                ),
            )

            command = build_stage3_bwrap_command(
                writable_root=work,
                child_argv=child_argv,
            )

            completed = subprocess.run(
                command,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=180,
            )

            if completed.returncode != 0:
                raise HarnessError(
                    "Stage 3 bubblewrap worker failed: "
                    + completed.stderr.strip()
                )

            if not response_path.is_file():
                raise HarnessError(
                    "Stage 3 bubblewrap worker produced no response"
                )

            try:
                response = json.loads(
                    response_path.read_text()
                )
            except json.JSONDecodeError as exc:
                raise HarnessError(
                    "Stage 3 bubblewrap worker response is malformed"
                ) from exc

    finally:
        try:
            sentinel_handle.close()
        except Exception:
            pass

        try:
            Path(
                sentinel_handle.name
            ).unlink()
        except FileNotFoundError:
            pass

    if not isinstance(
        response,
        dict,
    ):
        raise HarnessError(
            "Stage 3 response must be an object"
        )

    expected_identity = {
        "worker_mode":
            STAGE3_SANDBOX_WORKER_MODE,

        "scenario_id":
            scenario_id,

        "method":
            method,

        "scenario_seed":
            seed,

        "parent_network_namespace":
            parent_network_namespace,
    }

    for key, expected in expected_identity.items():
        if response.get(
            key
        ) != expected:
            raise HarnessError(
                f"Stage 3 response identity differs: {key}"
            )

    for required_true in (
        "network_namespace_unshared",
        "host_root_read_only",
        "designated_root_writable",
        "private_tmp",
    ):
        if response.get(
            required_true
        ) is not True:
            raise HarnessError(
                "Stage 3 sandbox invariant failed: "
                f"{required_true}"
            )

    for forbidden_true in (
        "comparator_executed",
        "canonical_input_accessed",
        "benchmark_truth_accessed",
        "scoring_performed",
    ):
        if response.get(
            forbidden_true
        ) is not False:
            raise HarnessError(
                "Stage 3 crossed forbidden boundary: "
                f"{forbidden_true}"
            )

    worker_pid = response.get(
        "worker_pid"
    )

    peak = response.get(
        "child_peak_rss_kib"
    )

    worker_network_namespace = response.get(
        "worker_network_namespace"
    )

    if (
        isinstance(
            worker_pid,
            bool,
        )
        or not isinstance(
            worker_pid,
            int,
        )
        or worker_pid <= 0
    ):
        raise HarnessError(
            "Stage 3 worker PID is malformed"
        )

    if (
        isinstance(
            peak,
            bool,
        )
        or not isinstance(
            peak,
            int,
        )
        or peak <= 0
    ):
        raise HarnessError(
            "Stage 3 peak RSS is malformed"
        )

    if not isinstance(
        worker_network_namespace,
        str,
    ):
        raise HarnessError(
            "Stage 3 worker network namespace is malformed"
        )

    if (
        worker_network_namespace
        == parent_network_namespace
    ):
        raise HarnessError(
            "Stage 3 worker network namespace equals parent"
        )

    return SandboxedMockWorkerResult(
        scenario_id=scenario_id,
        method=method,
        scenario_seed=seed,
        worker_pid=worker_pid,
        child_peak_rss_kib=peak,
        parent_network_namespace=parent_network_namespace,
        worker_network_namespace=worker_network_namespace,
        network_namespace_unshared=True,
        host_root_read_only=True,
        designated_root_writable=True,
        private_tmp=True,
        comparator_executed=False,
        canonical_input_accessed=False,
        benchmark_truth_accessed=False,
    )




# ---------------------------------------------------------------------------
# Stage 4: frozen-runner integration using a mock executor.
#
# This stage calls the real frozen runner command-building/execution-record
# pathway inside the Stage 3 sandbox, but the supplied executor returns a
# synthetic non-zero result and launches no comparator process.
# ---------------------------------------------------------------------------

STAGE4_RUNNER_MOCK_MODE = (
    "STAGE4_FROZEN_RUNNER_MOCK_ONLY"
)

STAGE4_METHOD = (
    "HomoplasyFinder"
)

STAGE4_SCENARIO_ID = (
    "TOY"
)


@dataclass(frozen=True)
class RunnerMockIntegrationResult:
    scenario_id: str
    method: str
    scenario_seed: int
    worker_pid: int
    status: str
    failure_type: str
    exit_code: int
    timed_out: bool
    normalized_predictions_finalized: bool
    scoring_performed: bool
    execution_json_sha256: str
    stdout_text: str
    stderr_text: str
    planned_argv: tuple[str, ...]
    network_namespace_unshared: bool
    comparator_executed: bool
    canonical_input_accessed: bool
    benchmark_truth_accessed: bool


def authorized_runtime_config(
) -> dict[str, dict[str, str]]:
    authorization = (
        verify_authorization_contract()
    )

    raw = _require_mapping(
        authorization[
            "runtime_config"
        ],
        label="runtime_config",
    )

    if set(
        raw
    ) != set(
        runner.METHODS
    ):
        raise HarnessError(
            "authorized runtime-config method set differs"
        )

    normalized: dict[
        str,
        dict[str, str],
    ] = {}

    for method in runner.METHODS:
        method_raw = _require_mapping(
            raw[
                method
            ],
            label=f"runtime_config.{method}",
        )

        config: dict[str, str] = {}

        for key, value in method_raw.items():
            if not isinstance(
                key,
                str,
            ):
                raise HarnessError(
                    f"runtime-config key is malformed: {method}"
                )

            if not isinstance(
                value,
                str,
            ):
                raise HarnessError(
                    "runtime-config value is malformed: "
                    f"{method}.{key}"
                )

            config[
                key
            ] = value

        normalized[
            method
        ] = config

    return normalized


def _write_stage4_synthetic_fixture(
    directory: Path,
) -> None:
    if directory.exists():
        raise HarnessError(
            "Stage 4 synthetic fixture directory already exists"
        )

    directory.mkdir()

    root_sequence = (
        "AAAAAAAAAAAA"
    )

    mutated_sequence = (
        root_sequence[:9]
        + "C"
        + root_sequence[10:]
    )

    sequences = {
        "tipA":
            root_sequence,

        "tipB":
            mutated_sequence,

        "tipC":
            root_sequence,

        "tipD":
            mutated_sequence,
    }

    variable_positions = [
        10,
    ]

    (
        directory
        / "alignment.fasta"
    ).write_text(
        adapters.fasta_text(
            sequences
        )
    )

    (
        directory
        / "tree.nwk"
    ).write_text(
        "((tipA:1,tipB:1):1,(tipC:1,tipD:1):1);\n"
    )

    (
        directory
        / "reference.gb"
    ).write_text(
        adapters.minimal_genbank_text(
            root_sequence,
            variable_positions,
            locus="TOYREF",
        )
    )

    (
        directory
        / "variable_positions.txt"
    ).write_text(
        adapters.positions_text(
            variable_positions
        )
    )


def _stage4_mock_executor(
    plan: runner.CommandPlan,
    environment: Mapping[str, str],
    timeout_seconds: float,
) -> runner.ExecutionOutcome:
    if plan.method != STAGE4_METHOD:
        raise HarnessError(
            "Stage 4 mock executor received unexpected method"
        )

    if plan.scenario_id != STAGE4_SCENARIO_ID:
        raise HarnessError(
            "Stage 4 mock executor received unexpected scenario"
        )

    if timeout_seconds != 30.0:
        raise HarnessError(
            "Stage 4 mock timeout differs"
        )

    if not environment:
        raise HarnessError(
            "Stage 4 runner environment is unexpectedly empty"
        )

    return runner.ExecutionOutcome(
        returncode=23,
        stdout=(
            "stage4 synthetic mock stdout\n"
        ),
        stderr=(
            "stage4 synthetic mock stderr\n"
        ),
        timed_out=False,
    )


def _stage4_runner_worker(
    request: Mapping[str, object],
) -> dict[str, object]:
    required = {
        "mode",
        "scenario_id",
        "method",
        "scenario_seed",
        "input_dir",
        "result_parent",
        "parent_network_namespace",
    }

    if set(
        request
    ) != required:
        raise HarnessError(
            "Stage 4 runner-worker request keys differ"
        )

    if request[
        "mode"
    ] != STAGE4_RUNNER_MOCK_MODE:
        raise HarnessError(
            "Stage 4 runner-worker mode differs"
        )

    if os.environ.get(
        "BRANCHSNV_STAGE3_SANDBOX"
    ) != "1":
        raise HarnessError(
            "Stage 4 runner worker is outside sandbox"
        )

    scenario_id = request[
        "scenario_id"
    ]
    method = request[
        "method"
    ]
    seed = request[
        "scenario_seed"
    ]
    raw_input_dir = request[
        "input_dir"
    ]
    raw_result_parent = request[
        "result_parent"
    ]
    parent_network_namespace = request[
        "parent_network_namespace"
    ]

    if scenario_id != STAGE4_SCENARIO_ID:
        raise HarnessError(
            "Stage 4 synthetic scenario differs"
        )

    if method != STAGE4_METHOD:
        raise HarnessError(
            "Stage 4 synthetic method differs"
        )

    _validate_stage2_mock_identity(
        scenario_id=scenario_id,
        method=method,
        scenario_seed_value=seed,
    )

    if not isinstance(
        raw_input_dir,
        str,
    ):
        raise HarnessError(
            "Stage 4 synthetic input path is malformed"
        )

    if not isinstance(
        raw_result_parent,
        str,
    ):
        raise HarnessError(
            "Stage 4 synthetic result parent is malformed"
        )

    if not isinstance(
        parent_network_namespace,
        str,
    ):
        raise HarnessError(
            "Stage 4 parent network namespace is malformed"
        )

    worker_network_namespace = (
        _network_namespace_identity()
    )

    if (
        worker_network_namespace
        == parent_network_namespace
    ):
        raise HarnessError(
            "Stage 4 network namespace was not unshared"
        )

    input_dir = Path(
        raw_input_dir
    ).resolve(
        strict=True
    )

    result_parent = Path(
        raw_result_parent
    ).resolve(
        strict=True
    )

    runtime_config = (
        authorized_runtime_config()
    )

    inputs = (
        runner.scenario_inputs_from_directory(
            scenario_id,
            input_dir,
        )
    )

    seed_expected = scenario_seed(
        scenario_id
    )

    if seed != seed_expected:
        raise HarnessError(
            "Stage 4 request seed differs from frozen generator"
        )

    plan_root = (
        result_parent
        / "runner_plan"
    )

    plan = runner.build_command_plan(
        method=method,
        inputs=inputs,
        runtime_config=runtime_config,
        plan_root=plan_root,
        scenario_seed=seed,
    )

    record = runner.execute_command_plan(
        plan=plan,
        inputs=inputs,
        runtime_config=runtime_config,
        timeout_seconds=30,
        executor=_stage4_mock_executor,
    )

    if record.get(
        "status"
    ) != "FAILED":
        raise HarnessError(
            "Stage 4 runner mock did not preserve failure state"
        )

    if record.get(
        "failure_type"
    ) != "nonzero_exit":
        raise HarnessError(
            "Stage 4 runner failure type differs"
        )

    if record.get(
        "exit_code"
    ) != 23:
        raise HarnessError(
            "Stage 4 runner exit code differs"
        )

    if record.get(
        "timed_out"
    ) is not False:
        raise HarnessError(
            "Stage 4 mock run unexpectedly timed out"
        )

    if record.get(
        "normalized_predictions_finalized"
    ) is not False:
        raise HarnessError(
            "Stage 4 failure unexpectedly finalized predictions"
        )

    if record.get(
        "scoring_performed"
    ) is not False:
        raise HarnessError(
            "Stage 4 failure unexpectedly performed scoring"
        )

    execution_json = (
        plan.plan_root
        / "execution.json"
    )

    stdout_path = (
        plan.plan_root
        / "stdout.txt"
    )

    stderr_path = (
        plan.plan_root
        / "stderr.txt"
    )

    for required_path in (
        execution_json,
        stdout_path,
        stderr_path,
    ):
        if not required_path.is_file():
            raise HarnessError(
                "Stage 4 runner provenance output is absent: "
                f"{required_path.name}"
            )

    stdout_text = (
        stdout_path.read_text()
    )
    stderr_text = (
        stderr_path.read_text()
    )

    if stdout_text != (
        "stage4 synthetic mock stdout\n"
    ):
        raise HarnessError(
            "Stage 4 runner stdout preservation differs"
        )

    if stderr_text != (
        "stage4 synthetic mock stderr\n"
    ):
        raise HarnessError(
            "Stage 4 runner stderr preservation differs"
        )

    return {
        "schema_version":
            1,

        "worker_mode":
            STAGE4_RUNNER_MOCK_MODE,

        "scenario_id":
            scenario_id,

        "method":
            method,

        "scenario_seed":
            seed,

        "worker_pid":
            os.getpid(),

        "status":
            record[
                "status"
            ],

        "failure_type":
            record[
                "failure_type"
            ],

        "exit_code":
            record[
                "exit_code"
            ],

        "timed_out":
            record[
                "timed_out"
            ],

        "normalized_predictions_finalized":
            record[
                "normalized_predictions_finalized"
            ],

        "scoring_performed":
            record[
                "scoring_performed"
            ],

        "execution_json_sha256":
            sha256_file(
                execution_json
            ),

        "stdout_text":
            stdout_text,

        "stderr_text":
            stderr_text,

        "planned_argv":
            list(
                plan.argv
            ),

        "parent_network_namespace":
            parent_network_namespace,

        "worker_network_namespace":
            worker_network_namespace,

        "network_namespace_unshared":
            True,

        "mock_executor_used":
            True,

        "comparator_executed":
            False,

        "canonical_input_accessed":
            False,

        "benchmark_truth_accessed":
            False,
    }


def _stage4_runner_worker_file_entry(
    request_path: Path,
    response_path: Path,
) -> None:
    if response_path.exists():
        raise HarnessError(
            "Stage 4 response already exists"
        )

    try:
        request = json.loads(
            request_path.read_text()
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise HarnessError(
            "Stage 4 request is unreadable"
        ) from exc

    if not isinstance(
        request,
        dict,
    ):
        raise HarnessError(
            "Stage 4 request must be an object"
        )

    response = _stage4_runner_worker(
        request
    )

    response_path.write_text(
        json.dumps(
            response,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def run_stage4_runner_mock_integration(
) -> RunnerMockIntegrationResult:
    verify_authorization_contract()

    parent_network_namespace = (
        _network_namespace_identity()
    )

    with tempfile.TemporaryDirectory(
        prefix=".branchsnv_stage4_runner_",
        dir=Path.home(),
    ) as raw:
        work = Path(
            raw
        ).resolve()

        input_dir = (
            work
            / "synthetic_input"
        )

        result_parent = (
            work
            / "synthetic_results"
        )

        result_parent.mkdir()

        _write_stage4_synthetic_fixture(
            input_dir
        )

        request_path = (
            work
            / "request.json"
        )

        response_path = (
            work
            / "response.json"
        )

        seed = scenario_seed(
            STAGE4_SCENARIO_ID
        )

        request = {
            "mode":
                STAGE4_RUNNER_MOCK_MODE,

            "scenario_id":
                STAGE4_SCENARIO_ID,

            "method":
                STAGE4_METHOD,

            "scenario_seed":
                seed,

            "input_dir":
                str(
                    input_dir
                ),

            "result_parent":
                str(
                    result_parent
                ),

            "parent_network_namespace":
                parent_network_namespace,
        }

        request_path.write_text(
            json.dumps(
                request,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        child_argv = (
            sys.executable,
            str(
                Path(
                    __file__
                ).resolve()
            ),
            "--stage4-runner-mock-worker",
            str(
                request_path
            ),
            str(
                response_path
            ),
        )

        command = build_stage3_bwrap_command(
            writable_root=work,
            child_argv=child_argv,
        )

        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180,
        )

        if completed.returncode != 0:
            raise HarnessError(
                "Stage 4 sandboxed runner worker failed: "
                + completed.stderr.strip()
            )

        if not response_path.is_file():
            raise HarnessError(
                "Stage 4 sandboxed runner worker produced no response"
            )

        try:
            response = json.loads(
                response_path.read_text()
            )
        except json.JSONDecodeError as exc:
            raise HarnessError(
                "Stage 4 response is malformed"
            ) from exc

    if not isinstance(
        response,
        dict,
    ):
        raise HarnessError(
            "Stage 4 response must be an object"
        )

    for key, expected in (
        (
            "worker_mode",
            STAGE4_RUNNER_MOCK_MODE,
        ),
        (
            "scenario_id",
            STAGE4_SCENARIO_ID,
        ),
        (
            "method",
            STAGE4_METHOD,
        ),
        (
            "scenario_seed",
            scenario_seed(
                STAGE4_SCENARIO_ID
            ),
        ),
        (
            "status",
            "FAILED",
        ),
        (
            "failure_type",
            "nonzero_exit",
        ),
        (
            "exit_code",
            23,
        ),
        (
            "timed_out",
            False,
        ),
        (
            "normalized_predictions_finalized",
            False,
        ),
        (
            "scoring_performed",
            False,
        ),
        (
            "network_namespace_unshared",
            True,
        ),
        (
            "mock_executor_used",
            True,
        ),
        (
            "comparator_executed",
            False,
        ),
        (
            "canonical_input_accessed",
            False,
        ),
        (
            "benchmark_truth_accessed",
            False,
        ),
    ):
        if response.get(
            key
        ) != expected:
            raise HarnessError(
                f"Stage 4 response differs: {key}"
            )

    planned_argv = response.get(
        "planned_argv"
    )

    if not isinstance(
        planned_argv,
        list,
    ) or not all(
        isinstance(
            item,
            str,
        )
        for item
        in planned_argv
    ):
        raise HarnessError(
            "Stage 4 planned argv is malformed"
        )

    execution_json_sha256 = response.get(
        "execution_json_sha256"
    )

    if (
        not isinstance(
            execution_json_sha256,
            str,
        )
        or len(
            execution_json_sha256
        )
        != 64
    ):
        raise HarnessError(
            "Stage 4 execution JSON checksum is malformed"
        )

    worker_pid = response.get(
        "worker_pid"
    )

    if (
        isinstance(
            worker_pid,
            bool,
        )
        or not isinstance(
            worker_pid,
            int,
        )
        or worker_pid <= 0
    ):
        raise HarnessError(
            "Stage 4 worker PID is malformed"
        )

    return RunnerMockIntegrationResult(
        scenario_id=STAGE4_SCENARIO_ID,
        method=STAGE4_METHOD,
        scenario_seed=scenario_seed(
            STAGE4_SCENARIO_ID
        ),
        worker_pid=worker_pid,
        status="FAILED",
        failure_type="nonzero_exit",
        exit_code=23,
        timed_out=False,
        normalized_predictions_finalized=False,
        scoring_performed=False,
        execution_json_sha256=execution_json_sha256,
        stdout_text=response[
            "stdout_text"
        ],
        stderr_text=response[
            "stderr_text"
        ],
        planned_argv=tuple(
            planned_argv
        ),
        network_namespace_unshared=True,
        comparator_executed=False,
        canonical_input_accessed=False,
        benchmark_truth_accessed=False,
    )




# ---------------------------------------------------------------------------
# Stage 4.5: committed timeout amendment.
#
# The original authorization is preserved. Its 86400-second field
# is historical evidence, superseded only by amendment 001.
#
# This code reads frozen metadata, not canonical comparator inputs.
# ---------------------------------------------------------------------------

TIMEOUT_AMENDMENT_ROOT = Path(__file__).resolve().parent

TIMEOUT_AMENDMENT_JSON = (
    TIMEOUT_AMENDMENT_ROOT
    / "comparator_benchmark_execution_v1_harness_timeout_amendment_001.json"
)

TIMEOUT_AMENDMENT_MD = (
    TIMEOUT_AMENDMENT_ROOT
    / "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_TIMEOUT_AMENDMENT_001.md"
)

TIMEOUT_AMENDMENT_FREEZE = (
    TIMEOUT_AMENDMENT_ROOT
    / "comparator_benchmark_execution_v1_harness_timeout_amendment_001_freeze.py"
)

TIMEOUT_AMENDMENT_MANIFEST = (
    TIMEOUT_AMENDMENT_ROOT
    / "comparator_benchmark_execution_v1_harness_timeout_amendment_001.sha256"
)

TIMEOUT_FROZEN_DESIGN = (
    TIMEOUT_AMENDMENT_ROOT
    / "comparator_benchmark_execution_v1_design.json"
)

EXPECTED_TIMEOUT_AMENDMENT_SHA256 = (
    "c1f3e01988d2535085618f33f1131f2238cfb8ebbe21ee4af53989a1a9081a81"
)

EXPECTED_TIMEOUT_DESIGN_SHA256 = (
    "1306af08f69d27a80990203bd7d803d2c907a1cdeb56bfd2fe0174bf4a416cde"
)

EXPECTED_TIMEOUT_MATRIX_SHA256 = (
    "8e569a6fbad769de0aed087e882410f6f1dd7114cb060e13a956159ae0b39398"
)

EXPECTED_TIMEOUT_ORIGINAL_AUTH_SHA256 = (
    "934bf529136b34b5d39c1f22816aed19dedcd4b4c1aeddd34d1341e54e752cb5"
)

TIMEOUT_AMENDMENT_ID = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_TIMEOUT_AMENDMENT_001"
)

TIMEOUT_APPROVED_GROUPS = (
    ("S001-S050", 32, "core", 3600),
    ("S051-S100", 128, "core", 3600),
    ("S101-S150", 512, "scale", 14400),
)


def _verify_timeout_amendment_contract(
    authorization: Mapping[str, object],
) -> dict[str, object]:
    if sha256_file(AUTH_PATH) != EXPECTED_TIMEOUT_ORIGINAL_AUTH_SHA256:
        raise HarnessError(
            "original authorization identity differs from timeout amendment"
        )

    original_resource = _require_mapping(
        authorization.get("resource_contract"),
        label="resource_contract",
    )

    if original_resource.get(
        "timeout_seconds_per_invocation"
    ) != 86400:
        raise HarnessError(
            "original timeout clause differs from historical authorization"
        )

    if sha256_file(
        TIMEOUT_AMENDMENT_JSON
    ) != EXPECTED_TIMEOUT_AMENDMENT_SHA256:
        raise HarnessError(
            "committed timeout amendment identity differs"
        )

    if sha256_file(
        TIMEOUT_FROZEN_DESIGN
    ) != EXPECTED_TIMEOUT_DESIGN_SHA256:
        raise HarnessError(
            "frozen execution design identity differs"
        )

    if sha256_file(
        FROZEN_SCENARIO_MATRIX
    ) != EXPECTED_TIMEOUT_MATRIX_SHA256:
        raise HarnessError(
            "frozen scenario matrix identity differs"
        )

    expected_manifest_files = {
        str(path.relative_to(REPO)): path
        for path in (
            TIMEOUT_AMENDMENT_JSON,
            TIMEOUT_AMENDMENT_MD,
            TIMEOUT_AMENDMENT_FREEZE,
        )
    }

    manifest_entries: dict[str, str] = {}

    for line in TIMEOUT_AMENDMENT_MANIFEST.read_text().splitlines():
        parts = line.split(None, 1)

        if len(parts) != 2:
            raise HarnessError(
                "timeout amendment manifest is malformed"
            )

        digest, filename = parts

        if filename in manifest_entries:
            raise HarnessError(
                "timeout amendment manifest has duplicate entry"
            )

        manifest_entries[filename] = digest

    if set(manifest_entries) != set(expected_manifest_files):
        raise HarnessError(
            "timeout amendment manifest file set differs"
        )

    for filename, path in expected_manifest_files.items():
        if sha256_file(path) != manifest_entries[filename]:
            raise HarnessError(
                f"timeout amendment artifact differs: {filename}"
            )

    try:
        amendment = json.loads(
            TIMEOUT_AMENDMENT_JSON.read_text()
        )

        design = json.loads(
            TIMEOUT_FROZEN_DESIGN.read_text()
        )

    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError(
            "timeout amendment or frozen design is unreadable"
        ) from exc

    if not isinstance(amendment, dict):
        raise HarnessError(
            "timeout amendment is not an object"
        )

    if amendment.get("amendment_id") != TIMEOUT_AMENDMENT_ID:
        raise HarnessError(
            "timeout amendment identity differs"
        )

    if amendment.get("status") != (
        "APPROVED_FOR_IMPLEMENTATION_NOT_EXECUTION"
    ):
        raise HarnessError(
            "timeout amendment authorization status differs"
        )

    if amendment.get("authorization_parent_commit") != (
        "6dd22db80ea0f34fad868d196e65b3847749e403"
    ):
        raise HarnessError(
            "timeout amendment authorization parent differs"
        )

    if amendment.get("original_authorization_id") != (
        EXPECTED_AUTHORIZATION_ID
    ):
        raise HarnessError(
            "timeout amendment parent authorization ID differs"
        )

    for key, expected in (
        (
            "original_authorization_sha256",
            EXPECTED_TIMEOUT_ORIGINAL_AUTH_SHA256,
        ),
        (
            "frozen_execution_design_sha256",
            EXPECTED_TIMEOUT_DESIGN_SHA256,
        ),
        (
            "frozen_scenario_matrix_sha256",
            EXPECTED_TIMEOUT_MATRIX_SHA256,
        ),
    ):
        if amendment.get(key) != expected:
            raise HarnessError(
                f"timeout amendment frozen identity differs: {key}"
            )

    if amendment.get("superseded_clause", {}).get(
        "field"
    ) != "resource_contract.timeout_seconds_per_invocation":
        raise HarnessError(
            "timeout amendment supersession field differs"
        )

    if amendment["superseded_clause"].get(
        "original_value"
    ) != 86400:
        raise HarnessError(
            "timeout amendment superseded value differs"
        )

    policy = _require_mapping(
        amendment.get("effective_policy"),
        label="effective_policy",
    )

    frozen_resource = _require_mapping(
        design.get("resource_and_failure_policy"),
        label="resource_and_failure_policy",
    )

    if frozen_resource.get("core_timeout_seconds") != 3600:
        raise HarnessError(
            "frozen core timeout differs"
        )

    if frozen_resource.get("scale_timeout_seconds") != 14400:
        raise HarnessError(
            "frozen scale timeout differs"
        )

    expected_policy = {
        "core_timeout_seconds": 3600,
        "scale_timeout_seconds": 14400,
        "core_tip_counts": [32, 128],
        "scale_tip_counts": [512],
        "classification_status": "NEWLY_APPROVED_INTERPRETATION",
        "classification_approval":
            "Explicit user approval in the BRANCHSNV project conversation",
        "selection_source":
            "tip_count column in the frozen scenario matrix",
        "applicability":
            "All eight frozen comparator methods for each scenario",
    }

    if dict(policy) != expected_policy:
        raise HarnessError(
            "effective timeout policy differs from approved amendment"
        )

    expected_groups = {
        name: {
            "tip_count": tips,
            "class": group,
            "timeout_seconds": timeout,
        }
        for name, tips, group, timeout in TIMEOUT_APPROVED_GROUPS
    }

    if amendment.get("scenario_groups") != expected_groups:
        raise HarnessError(
            "approved timeout scenario groups differ"
        )

    scope = _require_mapping(
        amendment.get("amendment_scope"),
        label="amendment_scope",
    )

    required_true = (
        "supersedes_only_original_timeout_clause",
        "original_authorization_must_remain_unchanged",
        "frozen_design_must_remain_unchanged",
        "frozen_runner_must_remain_unchanged",
        "frozen_scenario_matrix_must_remain_unchanged",
        "harness_implementation_only",
    )

    required_false = (
        "canonical_execution_authorized",
        "third_party_comparator_execution_authorized",
        "benchmark_truth_access_authorized",
        "scoring_authorized",
        "automatic_comparator_rerun_authorized",
    )

    if set(scope) != set(required_true) | set(required_false):
        raise HarnessError(
            "timeout amendment scope fields differ"
        )

    for key in required_true:
        if scope[key] is not True:
            raise HarnessError(
                f"timeout amendment permission boundary differs: {key}"
            )

    for key in required_false:
        if scope[key] is not False:
            raise HarnessError(
                f"timeout amendment prohibition differs: {key}"
            )

    if amendment.get("next_gate") != (
        "APPLY_APPROVED_TIMEOUT_POLICY_AND_FREEZE_COMPARATOR_BENCHMARK_EXECUTION_HARNESS_V1"
    ):
        raise HarnessError(
            "timeout amendment next gate differs"
        )

    if (
        REPO
        / "results/07_comparative_landscape/comparator_benchmark_execution_v1"
    ).exists():
        raise HarnessError(
            "canonical execution result root must remain absent"
        )

    return amendment


def frozen_timeout_map() -> dict[str, int]:
    # This call validates both the original authorization and its
    # committed timeout amendment before reading matrix metadata.
    authorization = verify_authorization_contract()

    # Keep the authorization result actively part of this boundary.
    resource = _require_mapping(
        authorization["resource_contract"],
        label="resource_contract",
    )

    if resource.get("timeout_seconds_per_invocation") != 86400:
        raise HarnessError(
            "historical authorization timeout differs"
        )

    with FROZEN_SCENARIO_MATRIX.open(
        "r",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        if (
            reader.fieldnames is None
            or "scenario_id" not in reader.fieldnames
            or "tip_count" not in reader.fieldnames
        ):
            raise HarnessError(
                "frozen scenario matrix lacks timeout selection columns"
            )

        rows = list(reader)

    if len(rows) != 150:
        raise HarnessError(
            "timeout selection scenario count differs"
        )

    selected: dict[str, int] = {}

    for index, row in enumerate(rows, start=1):
        scenario_id = f"S{index:03d}"

        if row.get("scenario_id") != scenario_id:
            raise HarnessError(
                f"timeout selection scenario order differs: {scenario_id}"
            )

        group_index = (index - 1) // 50

        (
            _group_name,
            expected_tip_count,
            _classification,
            timeout_seconds,
        ) = TIMEOUT_APPROVED_GROUPS[group_index]

        if row.get("tip_count") != str(expected_tip_count):
            raise HarnessError(
                f"timeout selection tip-count group differs: {scenario_id}"
            )

        selected[scenario_id] = timeout_seconds

    if len(selected) != 150:
        raise HarnessError(
            "timeout selection coverage differs"
        )

    return selected


def timeout_for_scenario(
    scenario_id: str,
) -> int:
    selected = frozen_timeout_map()

    if (
        not isinstance(scenario_id, str)
        or scenario_id not in selected
    ):
        raise HarnessError(
            "unknown scenario ID for timeout selection"
        )

    return selected[scenario_id]




# ---------------------------------------------------------------------------
# Stage 5B: synthetic-only frozen-executor and RSS validation.
#
# No canonical scenario or comparator is accepted here. No production
# execution pathway is enabled by this stage.
# ---------------------------------------------------------------------------

STAGE5B_MODE = "BRANCHSNV_STAGE5B_SYNTHETIC_ONLY_001"

STAGE5B_PROGRAMS = {
    "success": (
        "import os,sys\n"
        "if os.getcwd() != sys.argv[1]: sys.exit(71)\n"
        "if os.environ.get('BRANCHSNV_STAGE5B_ENV') != 'synthetic-value': sys.exit(72)\n"
        "data = bytearray(24 * 1024 * 1024)\n"
        "for i in range(0, len(data), 4096): data[i] = 1\n"
        "sys.stdout.write('stage5b stdout\\n')\n"
        "sys.stderr.write('stage5b stderr\\n')\n"
    ),
    "nonzero": (
        "import sys\n"
        "sys.stdout.write('partial stdout\\n')\n"
        "sys.stderr.write('expected failure\\n')\n"
        "sys.exit(23)\n"
    ),
    "timeout": (
        "import os,sys,time\n"
        "pid = os.fork()\n"
        "if pid == 0:\n"
        "    time.sleep(20)\n"
        "    os._exit(0)\n"
        "sys.stdout.write('grandchild_pid=' + str(pid) + '\\n')\n"
        "sys.stdout.flush()\n"
        "sys.stderr.write('timeout stderr\\n')\n"
        "sys.stderr.flush()\n"
        "time.sleep(20)\n"
    ),
}


def _stage5b_measured_synthetic_executor(
    plan,
    environment: Mapping[str, str],
    timeout_seconds: float,
) -> tuple[runner.ExecutionOutcome, int, int]:
    if os.environ.get("BRANCHSNV_STAGE3_SANDBOX") != "1":
        raise HarnessError(
            "Stage 5B measured executor requires isolated sandbox"
        )

    argv = tuple(plan.argv)

    if (
        len(argv) not in (3, 4)
        or argv[0] != sys.executable
        or argv[1] != "-c"
        or argv[2] not in STAGE5B_PROGRAMS.values()
    ):
        raise HarnessError(
            "Stage 5B refuses non-synthetic subprocess argv"
        )

    if Path(plan.cwd).resolve() != Path.cwd().resolve():
        raise HarnessError(
            "Stage 5B subprocess cwd differs from isolated workspace"
        )

    if timeout_seconds not in (1.0, 15.0):
        raise HarnessError(
            "Stage 5B synthetic timeout differs"
        )

    if environment.get("BRANCHSNV_STAGE5B_ENV") != "synthetic-value":
        raise HarnessError(
            "Stage 5B synthetic subprocess environment differs"
        )

    before = resource.getrusage(
        resource.RUSAGE_CHILDREN
    ).ru_maxrss

    # Reuse the frozen subprocess implementation. Its process-group,
    # stdout/stderr, cwd, env and timeout behavior remains authoritative.
    frozen_execute = runner.default_executor

    outcome = frozen_execute(
        plan,
        environment,
        timeout_seconds,
    )

    after = resource.getrusage(
        resource.RUSAGE_CHILDREN
    ).ru_maxrss

    if (
        not isinstance(before, int)
        or not isinstance(after, int)
        or before < 0
        or after <= 0
        or after < before
    ):
        raise HarnessError(
            "Stage 5B child peak RSS accounting is invalid"
        )

    return outcome, before, after


def _stage5b_grandchild_stopped(
    pid: int,
) -> bool:
    import time

    if pid <= 0:
        return False

    for _ in range(30):
        stat_path = Path(
            f"/proc/{pid}/stat"
        )

        try:
            stat_text = stat_path.read_text()
        except FileNotFoundError:
            return True

        try:
            state = stat_text.rsplit(")", 1)[1].strip().split()[0]
        except (IndexError, ValueError):
            return False

        # A zombie is no longer executing. Reaping is the
        # responsibility of its parent or the host init process.
        if state in ("Z", "X", "x"):
            return True

        time.sleep(0.1)

    return False


def _stage5b_synthetic_worker(
    request: Mapping[str, object],
) -> dict[str, object]:
    from types import SimpleNamespace

    verify_authorization_contract()

    if set(request) != {
        "mode",
        "case",
        "parent_network_namespace",
    }:
        raise HarnessError(
            "Stage 5B synthetic request keys differ"
        )

    if request["mode"] != STAGE5B_MODE:
        raise HarnessError(
            "Stage 5B synthetic mode differs"
        )

    case = request["case"]

    if (
        not isinstance(case, str)
        or case not in STAGE5B_PROGRAMS
    ):
        raise HarnessError(
            "Stage 5B refuses unknown synthetic test case"
        )

    if os.environ.get("BRANCHSNV_STAGE3_SANDBOX") != "1":
        raise HarnessError(
            "Stage 5B worker is outside sandbox"
        )

    work = _validate_stage3_writable_root(
        Path.cwd()
    )

    parent_network = request["parent_network_namespace"]
    worker_network = _network_namespace_identity()

    if (
        not isinstance(parent_network, str)
        or not parent_network
        or worker_network == parent_network
    ):
        raise HarnessError(
            "Stage 5B network namespace was not isolated"
        )

    argv = (
        sys.executable,
        "-c",
        STAGE5B_PROGRAMS[case],
    )

    if case == "success":
        argv = (
            *argv,
            str(work),
        )

    timeout_seconds = (
        1.0 if case == "timeout" else 15.0
    )

    environment = {
        "PATH": os.environ.get("PATH", ""),
        "LANG": "C",
        "HOME": str(work),
        "TMPDIR": "/tmp",
        "PYTHONDONTWRITEBYTECODE": "1",
        "BRANCHSNV_STAGE5B_ENV": "synthetic-value",
    }

    plan = SimpleNamespace(
        argv=argv,
        cwd=work,
    )

    outcome, before, peak = (
        _stage5b_measured_synthetic_executor(
            plan,
            environment,
            timeout_seconds,
        )
    )

    if case == "success":
        if (
            outcome.returncode != 0
            or outcome.timed_out
            or outcome.stdout != "stage5b stdout\n"
            or outcome.stderr != "stage5b stderr\n"
        ):
            raise HarnessError(
                "Stage 5B successful subprocess behavior differs"
            )

        if peak < 24 * 1024:
            raise HarnessError(
                "Stage 5B synthetic allocation did not register in peak RSS"
            )

    elif case == "nonzero":
        if (
            outcome.returncode != 23
            or outcome.timed_out
            or outcome.stdout != "partial stdout\n"
            or outcome.stderr != "expected failure\n"
        ):
            raise HarnessError(
                "Stage 5B non-zero subprocess behavior differs"
            )

    elif case == "timeout":
        if (
            not outcome.timed_out
            or outcome.returncode is None
            or outcome.stderr != "timeout stderr\n"
            or not outcome.stdout.startswith("grandchild_pid=")
        ):
            raise HarnessError(
                "Stage 5B timeout subprocess behavior differs"
            )

        try:
            grandchild_pid = int(
                outcome.stdout.strip().split("=", 1)[1]
            )
        except (ValueError, IndexError) as exc:
            raise HarnessError(
                "Stage 5B grandchild identity is malformed"
            ) from exc

        if not _stage5b_grandchild_stopped(grandchild_pid):
            raise HarnessError(
                "Stage 5B timeout left a running process-group descendant"
            )

    return {
        "worker_mode": STAGE5B_MODE,
        "case": case,
        "worker_pid": os.getpid(),
        "parent_network_namespace": parent_network,
        "worker_network_namespace": worker_network,
        "network_namespace_unshared": True,
        "returncode": outcome.returncode,
        "stdout": outcome.stdout,
        "stderr": outcome.stderr,
        "timed_out": outcome.timed_out,
        "child_peak_rss_before_kib": before,
        "child_peak_rss_kib": peak,
        "synthetic_subprocess_executed": True,
        "comparator_executed": False,
        "canonical_input_accessed": False,
        "benchmark_truth_accessed": False,
        "scoring_performed": False,
    }


def _stage5b_synthetic_worker_file_entry(
    request_path: Path,
    response_path: Path,
) -> None:
    work = _validate_stage3_writable_root(
        Path.cwd()
    )

    if (
        request_path != work / "request.json"
        or response_path != work / "response.json"
        or response_path.exists()
    ):
        raise HarnessError(
            "Stage 5B synthetic request/response paths differ"
        )

    try:
        request = json.loads(
            request_path.read_text()
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError(
            "Stage 5B synthetic request unreadable"
        ) from exc

    if not isinstance(request, dict):
        raise HarnessError(
            "Stage 5B synthetic request is not an object"
        )

    response = _stage5b_synthetic_worker(
        request
    )

    response_path.write_text(
        json.dumps(
            response,
            indent=2,
            sort_keys=True,
        ) + "\n"
    )


def run_stage5b_synthetic_probe(
    case: str,
) -> dict[str, object]:
    verify_authorization_contract()

    if (
        not isinstance(case, str)
        or case not in STAGE5B_PROGRAMS
    ):
        raise HarnessError(
            "Stage 5B refuses unknown synthetic test case"
        )

    with tempfile.TemporaryDirectory(
        prefix=".branchsnv_stage5_executor_",
        dir=Path.home(),
    ) as raw:
        work = _validate_stage3_writable_root(
            Path(raw)
        )

        request_path = work / "request.json"
        response_path = work / "response.json"

        request = {
            "mode": STAGE5B_MODE,
            "case": case,
            "parent_network_namespace":
                _network_namespace_identity(),
        }

        request_path.write_text(
            json.dumps(
                request,
                indent=2,
                sort_keys=True,
            ) + "\n"
        )

        child_argv = (
            sys.executable,
            str(Path(__file__).resolve()),
            "--stage5b-synthetic-worker",
            str(request_path),
            str(response_path),
        )

        command = build_stage3_bwrap_command(
            writable_root=work,
            child_argv=child_argv,
        )

        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=90,
        )

        if completed.returncode != 0:
            raise HarnessError(
                "Stage 5B isolated synthetic worker failed: "
                + completed.stderr.strip()
            )

        if not response_path.is_file():
            raise HarnessError(
                "Stage 5B isolated worker produced no response"
            )

        try:
            response = json.loads(
                response_path.read_text()
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise HarnessError(
                "Stage 5B synthetic response is unreadable"
            ) from exc

        if (
            not isinstance(response, dict)
            or response.get("case") != case
            or response.get("worker_mode") != STAGE5B_MODE
            or response.get("network_namespace_unshared") is not True
            or response.get("comparator_executed") is not False
            or response.get("canonical_input_accessed") is not False
            or response.get("benchmark_truth_accessed") is not False
            or response.get("scoring_performed") is not False
        ):
            raise HarnessError(
                "Stage 5B synthetic response contract differs"
            )

        return response




# ---------------------------------------------------------------------------
# Stage 5C: frozen runner + synthetic measured executor.
#
# The frozen runner builds the actual method command and provenance.
# The explicitly supplied executor NEVER launches that command.
# Only an immutable synthetic Python program can be executed.
# ---------------------------------------------------------------------------

STAGE5C_MODE = "BRANCHSNV_STAGE5C_SYNTHETIC_RUNNER_ONLY_001"

STAGE5C_CASES = (
    "success",
    "nonzero",
    "timeout",
)

STAGE5C_SUCCESS_PROGRAM = (
    "import os,sys\n"
    "if os.getcwd() != sys.argv[1]: sys.exit(71)\n"
    "if os.environ.get('PATH', '') != sys.argv[2]: sys.exit(72)\n"
    "data = bytearray(24 * 1024 * 1024)\n"
    "for i in range(0, len(data), 4096): data[i] = 1\n"
    "sys.stdout.write('stage5c stdout\\n')\n"
    "sys.stderr.write('stage5c stderr\\n')\n"
)


def _stage5c_synthetic_runner_worker(
    request: Mapping[str, object],
) -> dict[str, object]:
    from types import SimpleNamespace

    verify_authorization_contract()

    if set(request) != {
        "mode",
        "case",
        "parent_network_namespace",
    }:
        raise HarnessError(
            "Stage 5C request keys differ"
        )

    if request["mode"] != STAGE5C_MODE:
        raise HarnessError(
            "Stage 5C worker mode differs"
        )

    case = request["case"]

    if not isinstance(case, str) or case not in STAGE5C_CASES:
        raise HarnessError(
            "Stage 5C refuses unknown synthetic test case"
        )

    if os.environ.get("BRANCHSNV_STAGE3_SANDBOX") != "1":
        raise HarnessError(
            "Stage 5C worker is outside sandbox"
        )

    work = _validate_stage3_writable_root(
        Path.cwd()
    )

    parent_network = request["parent_network_namespace"]
    worker_network = _network_namespace_identity()

    if (
        not isinstance(parent_network, str)
        or not parent_network
        or worker_network == parent_network
    ):
        raise HarnessError(
            "Stage 5C network namespace was not isolated"
        )

    if STAGE4_SCENARIO_ID in frozen_scenario_ids():
        raise HarnessError(
            "Stage 5C synthetic scenario overlaps canonical matrix"
        )

    input_dir = work / "synthetic_input"
    result_parent = work / "synthetic_results"

    if not input_dir.is_dir() or not result_parent.is_dir():
        raise HarnessError(
            "Stage 5C synthetic fixture directories absent"
        )

    runtime_config = authorized_runtime_config()

    inputs = runner.scenario_inputs_from_directory(
        STAGE4_SCENARIO_ID,
        input_dir,
    )

    plan = runner.build_command_plan(
        method=STAGE4_METHOD,
        inputs=inputs,
        runtime_config=runtime_config,
        plan_root=result_parent / "runner_plan",
        scenario_seed=scenario_seed(STAGE4_SCENARIO_ID),
    )

    if (
        plan.scenario_id != STAGE4_SCENARIO_ID
        or plan.method != STAGE4_METHOD
    ):
        raise HarnessError(
            "Stage 5C frozen command identity differs"
        )

    planned_cwd = Path(plan.cwd).resolve(strict=True)

    if (
        not planned_cwd.is_dir()
        or work not in planned_cwd.parents
    ):
        raise HarnessError(
            "Stage 5C command working directory escapes workspace"
        )

    if tuple(plan.argv[:2]) == (sys.executable, "-c"):
        raise HarnessError(
            "Stage 5C frozen command unexpectedly looks synthetic"
        )

    deadline = (
        1.0 if case == "timeout" else 15.0
    )

    measurement: dict[str, object] = {}

    def synthetic_executor(
        received_plan,
        environment,
        timeout_seconds,
    ):
        if measurement:
            raise HarnessError(
                "Stage 5C executor called more than once"
            )

        if (
            received_plan is not plan
            or float(timeout_seconds) != deadline
            or Path(received_plan.cwd).resolve(strict=True) != planned_cwd
        ):
            raise HarnessError(
                "Stage 5C runner callback contract differs"
            )

        if not isinstance(environment, Mapping):
            raise HarnessError(
                "Stage 5C runner environment is malformed"
            )

        if any(
            "truth" in key.lower()
            for key in environment
        ):
            raise HarnessError(
                "Stage 5C refuses truth-like environment keys"
            )

        if case == "success":
            synthetic_argv = (
                sys.executable,
                "-c",
                STAGE5C_SUCCESS_PROGRAM,
                str(planned_cwd),
                environment.get("PATH", ""),
            )

        else:
            synthetic_argv = (
                sys.executable,
                "-c",
                STAGE5B_PROGRAMS[case],
            )

        # Critical boundary: received_plan.argv is never executed.
        # Only the locally constructed, predefined synthetic argv
        # is passed to the frozen subprocess executor.
        synthetic_plan = SimpleNamespace(
            argv=synthetic_argv,
            cwd=planned_cwd,
        )

        before = resource.getrusage(
            resource.RUSAGE_CHILDREN
        ).ru_maxrss

        frozen_execute = runner.default_executor

        outcome = frozen_execute(
            synthetic_plan,
            environment,
            timeout_seconds,
        )

        after = resource.getrusage(
            resource.RUSAGE_CHILDREN
        ).ru_maxrss

        if (
            not isinstance(before, int)
            or not isinstance(after, int)
            or before < 0
            or after <= 0
            or after < before
        ):
            raise HarnessError(
                "Stage 5C measured child RSS is invalid"
            )

        measurement.update(
            before_kib=before,
            peak_kib=after,
            returncode=outcome.returncode,
            timed_out=outcome.timed_out,
            stdout=outcome.stdout,
            stderr=outcome.stderr,
            callback_count=1,
        )

        return outcome

    record = runner.execute_command_plan(
        plan=plan,
        inputs=inputs,
        runtime_config=runtime_config,
        timeout_seconds=deadline,
        executor=synthetic_executor,
    )

    if measurement.get("callback_count") != 1:
        raise HarnessError(
            "Stage 5C measured callback was not invoked exactly once"
        )

    if record.get("status") != "FAILED":
        raise HarnessError(
            "Stage 5C synthetic test unexpectedly completed predictions"
        )

    if (
        record.get("normalized_predictions_finalized") is not False
        or record.get("scoring_performed") is not False
    ):
        raise HarnessError(
            "Stage 5C scientific completion boundary differs"
        )

    if (
        record.get("exit_code") != measurement["returncode"]
        or record.get("timed_out") != measurement["timed_out"]
    ):
        raise HarnessError(
            "Stage 5C runner execution status differs from subprocess"
        )

    expected_streams = {
        "success": (
            "stage5c stdout\n",
            "stage5c stderr\n",
        ),
        "nonzero": (
            "partial stdout\n",
            "expected failure\n",
        ),
    }

    if case in expected_streams:
        if (
            measurement["stdout"],
            measurement["stderr"],
        ) != expected_streams[case]:
            raise HarnessError(
                "Stage 5C synthetic streams differ"
            )

    if case == "success":
        if (
            measurement["returncode"] != 0
            or measurement["timed_out"] is not False
            or measurement["peak_kib"] < 24 * 1024
            or record.get("failure_type") in (
                "nonzero_exit",
                "timeout",
                "launch_error",
            )
        ):
            raise HarnessError(
                "Stage 5C missing-native-output failure differs"
            )

    elif case == "nonzero":
        if (
            record.get("failure_type") != "nonzero_exit"
            or record.get("exit_code") != 23
            or record.get("timed_out") is not False
        ):
            raise HarnessError(
                "Stage 5C nonzero failure classification differs"
            )

    elif case == "timeout":
        if (
            record.get("failure_type") != "timeout"
            or record.get("timed_out") is not True
            or measurement["stderr"] != "timeout stderr\n"
            or not measurement["stdout"].startswith(
                "grandchild_pid="
            )
        ):
            raise HarnessError(
                "Stage 5C timeout classification differs"
            )

        try:
            grandchild_pid = int(
                measurement["stdout"].strip().split("=", 1)[1]
            )
        except (ValueError, IndexError) as exc:
            raise HarnessError(
                "Stage 5C timeout descendant PID is malformed"
            ) from exc

        if not _stage5b_grandchild_stopped(grandchild_pid):
            raise HarnessError(
                "Stage 5C timeout left running process-group descendant"
            )

    execution_path = plan.plan_root / "execution.json"
    stdout_path = plan.plan_root / "stdout.txt"
    stderr_path = plan.plan_root / "stderr.txt"

    for required in (
        execution_path,
        stdout_path,
        stderr_path,
    ):
        if not required.is_file():
            raise HarnessError(
                "Stage 5C runner provenance file absent: "
                + required.name
            )

    if (
        stdout_path.read_text() != measurement["stdout"]
        or stderr_path.read_text() != measurement["stderr"]
    ):
        raise HarnessError(
            "Stage 5C runner did not preserve subprocess streams"
        )

    execution_record = json.loads(
        execution_path.read_text()
    )

    for key in (
        "status",
        "failure_type",
        "exit_code",
        "timed_out",
        "normalized_predictions_finalized",
        "scoring_performed",
    ):
        if execution_record.get(key) != record.get(key):
            raise HarnessError(
                "Stage 5C persisted execution metadata differs: "
                + key
            )

    return {
        "mode": STAGE5C_MODE,
        "case": case,
        "worker_pid": os.getpid(),
        "network_namespace_unshared": True,
        "parent_network_namespace": parent_network,
        "worker_network_namespace": worker_network,
        "status": record["status"],
        "failure_type": record["failure_type"],
        "exit_code": record["exit_code"],
        "timed_out": record["timed_out"],
        "normalized_predictions_finalized":
            record["normalized_predictions_finalized"],
        "scoring_performed": record["scoring_performed"],
        "stdout": measurement["stdout"],
        "stderr": measurement["stderr"],
        "child_peak_rss_before_kib": measurement["before_kib"],
        "child_peak_rss_kib": measurement["peak_kib"],
        "runner_elapsed_seconds": record["elapsed_seconds"],
        "runner_execution_record": execution_record,
        "execution_json_sha256": sha256_file(execution_path),
        "runner_callback_count": measurement["callback_count"],
        "original_command_executed": False,
        "synthetic_subprocess_executed": True,
        "comparator_executed": False,
        "canonical_input_accessed": False,
        "benchmark_truth_accessed": False,
    }


def _stage5c_synthetic_runner_file_entry(
    request_path: Path,
    response_path: Path,
) -> None:
    work = _validate_stage3_writable_root(
        Path.cwd()
    )

    if (
        request_path != work / "request.json"
        or response_path != work / "response.json"
        or response_path.exists()
    ):
        raise HarnessError(
            "Stage 5C request/response paths differ"
        )

    try:
        request = json.loads(request_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError(
            "Stage 5C synthetic request unreadable"
        ) from exc

    if not isinstance(request, dict):
        raise HarnessError(
            "Stage 5C request must be an object"
        )

    response = _stage5c_synthetic_runner_worker(
        request
    )

    response_path.write_text(
        json.dumps(
            response,
            indent=2,
            sort_keys=True,
        ) + "\n"
    )


def run_stage5c_synthetic_runner_probe(
    case: str,
) -> dict[str, object]:
    verify_authorization_contract()

    if not isinstance(case, str) or case not in STAGE5C_CASES:
        raise HarnessError(
            "Stage 5C refuses unknown synthetic test case"
        )

    with tempfile.TemporaryDirectory(
        prefix=".branchsnv_stage5_runner_",
        dir=Path.home(),
    ) as raw:
        work = _validate_stage3_writable_root(
            Path(raw)
        )

        input_dir = work / "synthetic_input"
        result_parent = work / "synthetic_results"

        result_parent.mkdir()

        _write_stage4_synthetic_fixture(
            input_dir
        )

        request_path = work / "request.json"
        response_path = work / "response.json"

        request = {
            "mode": STAGE5C_MODE,
            "case": case,
            "parent_network_namespace":
                _network_namespace_identity(),
        }

        request_path.write_text(
            json.dumps(
                request,
                indent=2,
                sort_keys=True,
            ) + "\n"
        )

        command = build_stage3_bwrap_command(
            writable_root=work,
            child_argv=(
                sys.executable,
                str(Path(__file__).resolve()),
                "--stage5c-synthetic-runner-worker",
                str(request_path),
                str(response_path),
            ),
        )

        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=90,
        )

        if completed.returncode != 0:
            raise HarnessError(
                "Stage 5C isolated synthetic worker failed: "
                + completed.stderr.strip()
            )

        if not response_path.is_file():
            raise HarnessError(
                "Stage 5C synthetic runner response absent"
            )

        try:
            response = json.loads(response_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise HarnessError(
                "Stage 5C response unreadable"
            ) from exc

        if not isinstance(response, dict):
            raise HarnessError(
                "Stage 5C response must be an object"
            )

        if (
            response.get("case") != case
            or response.get("mode") != STAGE5C_MODE
            or response.get("status") != "FAILED"
            or response.get("runner_callback_count") != 1
            or response.get("network_namespace_unshared") is not True
            or response.get("original_command_executed") is not False
            or response.get("synthetic_subprocess_executed") is not True
            or response.get("comparator_executed") is not False
            or response.get("canonical_input_accessed") is not False
            or response.get("benchmark_truth_accessed") is not False
            or response.get("scoring_performed") is not False
            or response.get("normalized_predictions_finalized") is not False
        ):
            raise HarnessError(
                "Stage 5C response boundary differs"
            )

        return response




# ---------------------------------------------------------------------------
# Stage 5D: frozen metadata-only dispatch contract.
#
# This prepares no command, launches no process, opens no canonical
# scenario input and creates no canonical output directory.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FrozenDispatchEntry:
    ordinal: int
    scenario_index: int
    method_index: int
    scenario_id: str
    method: str
    scenario_seed: int
    timeout_seconds: int
    input_dir: Path
    plan_root: Path


def frozen_dispatch_contract() -> tuple[FrozenDispatchEntry, ...]:
    verify_authorization_contract()

    invocations = frozen_invocation_plan()
    timeouts = frozen_timeout_map()
    scenarios = frozen_scenario_ids()
    methods = authorized_method_order()

    if (
        len(invocations) != 1200
        or len(scenarios) != 150
        or len(methods) != 8
    ):
        raise HarnessError(
            "Stage 5D frozen dispatch dimensions differ"
        )

    if set(timeouts) != set(scenarios):
        raise HarnessError(
            "Stage 5D timeout coverage differs"
        )

    if set(timeouts.values()) != {3600, 14400}:
        raise HarnessError(
            "Stage 5D timeout values differ"
        )

    expected_pairs = {
        (scenario_id, method)
        for scenario_id in scenarios
        for method in methods
    }

    seen_pairs: set[tuple[str, str]] = set()
    seen_ordinals: set[int] = set()
    seen_roots: set[Path] = set()

    dispatch: list[FrozenDispatchEntry] = []

    for invocation in invocations:
        pair = (
            invocation.scenario_id,
            invocation.method,
        )

        if pair in seen_pairs:
            raise HarnessError(
                "Stage 5D duplicate comparator-scenario invocation"
            )

        if invocation.ordinal in seen_ordinals:
            raise HarnessError(
                "Stage 5D duplicate invocation ordinal"
            )

        if invocation.plan_root in seen_roots:
            raise HarnessError(
                "Stage 5D duplicate invocation result root"
            )

        if pair not in expected_pairs:
            raise HarnessError(
                "Stage 5D unexpected comparator-scenario pair"
            )

        expected_seed = scenario_seed(
            invocation.scenario_id
        )

        if invocation.scenario_seed != expected_seed:
            raise HarnessError(
                "Stage 5D invocation seed differs"
            )

        if (
            not invocation.input_dir.is_absolute()
            or not invocation.plan_root.is_absolute()
            or not invocation.input_dir.is_relative_to(REPO)
            or not invocation.plan_root.is_relative_to(REPO)
        ):
            raise HarnessError(
                "Stage 5D invocation path escapes repository"
            )

        timeout = timeouts[
            invocation.scenario_id
        ]

        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, int)
            or timeout not in (3600, 14400)
        ):
            raise HarnessError(
                "Stage 5D invocation timeout differs"
            )

        seen_pairs.add(pair)
        seen_ordinals.add(invocation.ordinal)
        seen_roots.add(invocation.plan_root)

        dispatch.append(
            FrozenDispatchEntry(
                ordinal=invocation.ordinal,
                scenario_index=invocation.scenario_index,
                method_index=invocation.method_index,
                scenario_id=invocation.scenario_id,
                method=invocation.method,
                scenario_seed=invocation.scenario_seed,
                timeout_seconds=timeout,
                input_dir=invocation.input_dir,
                plan_root=invocation.plan_root,
            )
        )

    if (
        seen_pairs != expected_pairs
        or len(seen_ordinals) != 1200
        or len(seen_roots) != 1200
    ):
        raise HarnessError(
            "Stage 5D dispatch coverage is incomplete"
        )

    if (
        REPO
        / "results/07_comparative_landscape/"
          "comparator_benchmark_execution_v1"
    ).exists():
        raise HarnessError(
            "Stage 5D canonical result root must remain absent"
        )

    return tuple(dispatch)




# ---------------------------------------------------------------------------
# Stage 5E: durable synthetic execution ledger.
#
# This validates persistence and continuation semantics using Stage 5C
# synthetic probes only. It never dispatches canonical invocations.
# ---------------------------------------------------------------------------

STAGE5E_SCHEMA = (
    "BRANCHSNV_SYNTHETIC_EXECUTION_LEDGER_V1"
)

STAGE5E_FAILURE_TYPES = {
    "success": "native_output_failure",
    "nonzero": "nonzero_exit",
    "timeout": "timeout",
}


def _stage5e_atomic_json_create(
    path: Path,
    payload: Mapping[str, object],
) -> None:
    if (
        not path.parent.is_dir()
        or path.exists()
        or path.is_symlink()
        or path.suffix != ".json"
    ):
        raise HarnessError(
            "Stage 5E refuses existing or invalid ledger target"
        )

    pending = path.with_name(
        "." + path.name + ".pending"
    )

    encoded = (
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        ) + "\n"
    ).encode("utf-8")

    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | os.O_NOFOLLOW
    )

    try:
        descriptor = os.open(
            pending,
            flags,
            0o600,
        )

        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())

        # Hard-link creation is no-clobber: an existing
        # destination fails rather than being overwritten.
        os.link(
            pending,
            path,
            follow_symlinks=False,
        )

    except (OSError, ValueError, TypeError) as exc:
        raise HarnessError(
            "Stage 5E durable JSON write failed"
        ) from exc

    finally:
        pending.unlink(
            missing_ok=True
        )

    directory_fd = os.open(
        path.parent,
        os.O_RDONLY | os.O_DIRECTORY,
    )

    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def run_stage5e_synthetic_ledger(
    ledger_root: Path,
) -> dict[str, object]:
    import math

    verify_authorization_contract()

    root = _validate_stage3_writable_root(
        ledger_root
    )

    if any(root.iterdir()):
        raise HarnessError(
            "Stage 5E ledger root must be empty; "
            "existing records cannot be rerun or overwritten"
        )

    entry_root = root / "entries"

    entry_root.mkdir(
        mode=0o700
    )

    manifest_entries: list[dict[str, object]] = []

    for ordinal, case in enumerate(
        STAGE5C_CASES,
        start=1,
    ):
        if case not in STAGE5E_FAILURE_TYPES:
            raise HarnessError(
                "Stage 5E synthetic case is not approved"
            )

        # This is the only execution function called here.
        # It refuses comparator names and canonical scenarios.
        response = run_stage5c_synthetic_runner_probe(
            case
        )

        if (
            response.get("case") != case
            or response.get("mode") != STAGE5C_MODE
            or response.get("status") != "FAILED"
            or response.get("failure_type")
                != STAGE5E_FAILURE_TYPES[case]
            or response.get("original_command_executed") is not False
            or response.get("synthetic_subprocess_executed") is not True
            or response.get("comparator_executed") is not False
            or response.get("canonical_input_accessed") is not False
            or response.get("benchmark_truth_accessed") is not False
            or response.get("scoring_performed") is not False
            or response.get("normalized_predictions_finalized") is not False
            or response.get("runner_callback_count") != 1
        ):
            raise HarnessError(
                "Stage 5E refuses invalid synthetic execution response"
            )

        rss_kib = response.get(
            "child_peak_rss_kib"
        )

        elapsed = response.get(
            "runner_elapsed_seconds"
        )

        if (
            isinstance(rss_kib, bool)
            or not isinstance(rss_kib, int)
            or rss_kib <= 0
            or isinstance(elapsed, bool)
            or not isinstance(elapsed, (int, float))
            or not math.isfinite(elapsed)
            or elapsed < 0
        ):
            raise HarnessError(
                "Stage 5E resource measurements are invalid"
            )

        execution_record = response.get(
            "runner_execution_record"
        )

        if not isinstance(execution_record, dict):
            raise HarnessError(
                "Stage 5E frozen runner provenance is absent"
            )

        for key in (
            "status",
            "failure_type",
            "exit_code",
            "timed_out",
            "normalized_predictions_finalized",
            "scoring_performed",
        ):
            if execution_record.get(key) != response.get(key):
                raise HarnessError(
                    "Stage 5E frozen runner provenance differs: "
                    + key
                )

        record = {
            "schema": STAGE5E_SCHEMA,
            "execution_scope": "SYNTHETIC_VALIDATION_ONLY",
            "ordinal": ordinal,
            "synthetic_case": case,
            "synthetic_scenario_id": STAGE4_SCENARIO_ID,
            "synthetic_method": STAGE4_METHOD,
            "status": response["status"],
            "failure_type": response["failure_type"],
            "exit_code": response["exit_code"],
            "timed_out": response["timed_out"],
            "runner_elapsed_seconds": elapsed,
            "peak_child_rss_kib": rss_kib,
            "peak_child_rss_bytes": rss_kib * 1024,
            "rss_measurement": (
                "Linux RUSAGE_CHILDREN.ru_maxrss; "
                "maximum child RSS, not concurrent process-tree total"
            ),
            "stdout": response["stdout"],
            "stderr": response["stderr"],
            "runner_execution_json_sha256":
                response["execution_json_sha256"],
            "runner_execution_record": execution_record,
            "synthetic_subprocess_executed": True,
            "original_comparator_command_executed": False,
            "canonical_input_accessed": False,
            "benchmark_truth_accessed": False,
            "normalized_predictions_finalized": False,
            "scoring_performed": False,
        }

        filename = (
            f"{ordinal:03d}_{case}.json"
        )

        entry_path = entry_root / filename

        _stage5e_atomic_json_create(
            entry_path,
            record,
        )

        manifest_entries.append({
            "ordinal": ordinal,
            "synthetic_case": case,
            "status": "FAILED",
            "failure_type": response["failure_type"],
            "path": "entries/" + filename,
            "sha256": sha256_file(entry_path),
        })

    if (
        len(manifest_entries) != 3
        or tuple(
            row["synthetic_case"]
            for row in manifest_entries
        ) != STAGE5C_CASES
    ):
        raise HarnessError(
            "Stage 5E synthetic continuation coverage differs"
        )

    manifest = {
        "schema": STAGE5E_SCHEMA,
        "execution_scope": "SYNTHETIC_VALIDATION_ONLY",
        "invocation_count": 3,
        "completion_failure_count": 3,
        "scientific_success_count": 0,
        "automatic_reruns": 0,
        "canonical_execution_authorized": False,
        "scoring_performed": False,
        "entries": manifest_entries,
    }

    _stage5e_atomic_json_create(
        root / "manifest.json",
        manifest,
    )

    return {
        "manifest": manifest,
        "manifest_sha256": sha256_file(
            root / "manifest.json"
        ),
        "root": str(root),
    }




# ---------------------------------------------------------------------------
# Security Amendment 002: sealed private-root isolation + 1,200-entry
# production-shaped dry-run. There is deliberately NO runnable production
# comparator path. A future independent execution authorization is required.
# ---------------------------------------------------------------------------

SECURITY_002_JSON = ROOT / (
    "comparator_benchmark_execution_v1_harness_security_amendment_002.json"
)
SECURITY_002_MANIFEST = ROOT / (
    "comparator_benchmark_execution_v1_harness_security_amendment_002.sha256"
)
SECURITY_002_SHA256 = (
    "fab751b5ae6fe52a07eecef6d5491d9b87f43a27c807b9aff0ce9962895330d6"
)
SECURITY_002_MANIFEST_SHA256 = (
    "1590c5bca73bdc8c1a2a5d2e29c19d729168c48ecd910e52d28fc239fd548300"
)
SECURITY_002_ID = (
    "COMPARATOR_BENCHMARK_EXECUTION_V1_HARNESS_SECURITY_AMENDMENT_002"
)


def verify_security_amendment_002() -> dict[str, object]:
    if (sha256_file(SECURITY_002_JSON) != SECURITY_002_SHA256
            or sha256_file(SECURITY_002_MANIFEST)
            != SECURITY_002_MANIFEST_SHA256):
        raise HarnessError("Security Amendment 002 identity differs")
    try:
        contract = json.loads(SECURITY_002_JSON.read_text())
    except (ValueError, OSError) as exc:
        raise HarnessError("Security Amendment 002 is unreadable") from exc
    if (
        contract.get("amendment_id") != SECURITY_002_ID
        or contract.get("status") != "FROZEN_SCOPE_PRE_IMPLEMENTATION"
        or contract.get("future_execution_gate")
        != "SEPARATE_EXPLICIT_CANONICAL_EXECUTION_AUTHORIZATION_REQUIRED"
        or any(contract.get("explicit_prohibitions", {}).values())
        or set(contract.get("explicit_prohibitions", {})) != {
            "automatic_comparator_rerun_authorized",
            "benchmark_truth_access_authorized",
            "canonical_benchmark_execution_authorized",
            "canonical_input_access_authorized",
            "canonical_result_root_creation_authorized",
            "scoring_authorized",
            "third_party_comparator_execution_authorized",
        }
    ):
        raise HarnessError("Security Amendment 002 authorization differs")
    return contract


@dataclass(frozen=True)
class PrivateReadOnlyFile:
    """One content-pinned host OS file; never a broad directory bind."""
    source: Path
    destination: Path
    sha256: str


_STAGE5F_SYSTEM_PATH_ROOTS = (
    Path("/bin"), Path("/usr/bin"), Path("/lib"),
    Path("/lib64"), Path("/usr/lib"), Path("/usr/lib64"),
)
_STAGE5F_WORK_DEST = Path("/run/branchsnv/work")
_STAGE5F_INPUT_DEST = Path("/run/branchsnv/input")


def _stage5f_safe_mount_path(path: Path) -> Path:
    if (not isinstance(path, Path) or not path.is_absolute()
            or ".." in path.parts or "." in path.parts
            or str(path) == "/"):
        raise HarnessError("private-root mount destination is invalid")
    return path


def _stage5f_input_tree_safe(root: Path) -> None:
    """Check synthetic input view; canonical input inspection is prohibited."""
    import stat
    if root.is_symlink() or not root.is_dir():
        raise HarnessError("private-root input must be a real directory")
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in (*dirs, *files):
            entry = Path(base) / name
            st = entry.lstat()
            if stat.S_ISLNK(st.st_mode):
                raise HarnessError("private-root input symlink rejected")
            if stat.S_ISREG(st.st_mode) and st.st_nlink != 1:
                raise HarnessError("private-root input hardlink rejected")
            if not (stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode)):
                raise HarnessError("private-root input special file rejected")


def build_stage5f_private_root_command(
    *,
    work: Path,
    public_input: Path,
    system_files: tuple[PrivateReadOnlyFile, ...],
    child_argv: tuple[str, ...],
) -> tuple[str, ...]:
    """Build only. Host-root and arbitrary runtime directory binds banned.

    This function has no production execution capability. The system-file
    closure must be independently pinned in a future execution freeze.
    """
    verify_security_amendment_002()
    if not BWRAP.is_file():
        raise HarnessError("pinned bubblewrap executable is absent")
    work = _validate_stage3_writable_root(work)
    if not isinstance(public_input, Path) or not public_input.is_absolute():
        raise HarnessError("private-root input path must be absolute")
    if public_input.is_symlink():
        raise HarnessError("private-root input symlink rejected")
    public_input = public_input.resolve(strict=True)
    if (public_input.parent != work or public_input == work
            or public_input.name != "public_input"):
        raise HarnessError("private-root input escapes dedicated workspace")
    _stage5f_input_tree_safe(public_input)
    if (not isinstance(system_files, tuple) or not system_files
            or not isinstance(child_argv, tuple) or not child_argv
            or any(not isinstance(a, str) or not a for a in child_argv)):
        raise HarnessError("private-root file manifest or child argv malformed")

    seen = {_STAGE5F_INPUT_DEST, _STAGE5F_WORK_DEST}
    # Private destination tree; no host-root overlay and no host HOME mount.
    # Older pinned bubblewrap builds have no --clearenv switch.  The
    # absolute, root-owned env launcher clears inherited variables BEFORE
    # bubblewrap starts; --setenv below supplies only the approved values.
    env_launcher = Path("/usr/bin/env")
    try:
        env_metadata = env_launcher.stat()
    except OSError as exc:
        raise HarnessError("private-root clean-environment launcher absent") from exc
    if (not env_launcher.is_file() or env_metadata.st_uid != 0
            or env_metadata.st_mode & 0o022):
        raise HarnessError("private-root clean-environment launcher is unsafe")
    command = [str(env_launcher), "-i", str(BWRAP), "--tmpfs", "/"]
    validated = []
    for entry in system_files:
        if not isinstance(entry, PrivateReadOnlyFile):
            raise HarnessError("private-root system-file specification malformed")
        dest = _stage5f_safe_mount_path(entry.destination)
        if (dest in seen or any(
            dest in x.parents or x in dest.parents for x in seen
        )):
            raise HarnessError("private-root mount destination overlap")
        source = entry.source
        if not isinstance(source, Path) or not source.is_absolute():
            raise HarnessError("private-root OS file source is invalid")
        try:
            resolved = source.resolve(strict=True)
        except OSError as exc:
            raise HarnessError("private-root OS dependency missing") from exc
        if (not resolved.is_file() or not any(
            resolved == p or p in resolved.parents
            for p in _STAGE5F_SYSTEM_PATH_ROOTS
        ) or not any(
            dest == p or p in dest.parents
            for p in _STAGE5F_SYSTEM_PATH_ROOTS
        )):
            raise HarnessError("private-root unapproved runtime mount")
        if (not isinstance(entry.sha256, str)
                or len(entry.sha256) != 64
                or sha256_file(resolved) != entry.sha256):
            raise HarnessError("private-root OS dependency identity changed")
        seen.add(dest)
        validated.append((resolved, dest))

    # Mount only pinned files (never /, /home, repository, /usr or /lib
    # themselves). mkdir creates empty destination ancestors in private root.
    dirs = {Path("/tmp"), Path("/dev"), Path("/proc"),
            _STAGE5F_INPUT_DEST, _STAGE5F_WORK_DEST}
    for _, dest in validated:
        dirs.add(dest.parent)
    parents = set(dirs)
    for dest in tuple(dirs):
        parents.update(p for p in dest.parents if p != Path("/"))
    for dest in sorted(parents, key=lambda p: (len(p.parts), str(p))):
        command.extend(("--dir", str(dest)))
    for source, dest in validated:
        command.extend(("--ro-bind", str(source), str(dest)))
    command.extend((
        "--ro-bind", str(public_input), str(_STAGE5F_INPUT_DEST),
        "--bind", str(work), str(_STAGE5F_WORK_DEST),
        # Hide the host input directory's writable alias inside work.
        "--tmpfs", str(_STAGE5F_WORK_DEST / "public_input"),
        "--tmpfs", "/tmp", "--dev", "/dev", "--proc", "/proc",
        "--unshare-pid", "--unshare-net", "--unshare-ipc", "--unshare-uts",
        "--die-with-parent", "--new-session",
        "--setenv", "PATH", "/bin:/usr/bin",
        "--setenv", "HOME", str(_STAGE5F_WORK_DEST),
        "--setenv", "LANG", "C", "--chdir", str(_STAGE5F_WORK_DEST),
        "--", *child_argv,
    ))
    if command.count("--tmpfs") != 3 or "--ro-bind" not in command:
        raise HarnessError("private-root mount specification malformed")
    return tuple(command)


def stage5f_production_execution(*args, **kwargs) -> None:
    """Hard gate. An implementation freeze is NOT an execution approval."""
    raise HarnessError(
        "canonical execution prohibited: separate frozen execution authorization required"
    )


STAGE5F_DRY_SCHEMA = "BRANCHSNV_DISPATCH_DRY_RUN_V1"


def run_stage5f_dispatch_dry_run(
    ledger_root: Path,
    *,
    synthetic_interrupt_ordinal: int | None = None,
) -> dict[str, object]:
    """Journal all frozen dispatch metadata, never opening scenario inputs."""
    verify_authorization_contract()
    verify_security_amendment_002()
    root = _validate_stage3_writable_root(ledger_root)
    if any(root.iterdir()):
        raise HarnessError("Stage 5F ledger root must be empty")
    if (synthetic_interrupt_ordinal is not None and (
        isinstance(synthetic_interrupt_ordinal, bool)
        or not isinstance(synthetic_interrupt_ordinal, int)
        or synthetic_interrupt_ordinal < 1
        or synthetic_interrupt_ordinal > 1200
    )):
        raise HarnessError("Stage 5F synthetic interruption is malformed")

    entries = frozen_dispatch_contract()
    if len(entries) != 1200:
        raise HarnessError("Stage 5F dispatch coverage differs")
    (root / "entries").mkdir(mode=0o700)
    digest_rows = []
    for expected_ordinal, entry in enumerate(entries, start=1):
        if entry.ordinal != expected_ordinal:
            raise HarnessError("Stage 5F dispatch ordering differs")
        if synthetic_interrupt_ordinal == expected_ordinal:
            raise HarnessError("Stage 5F injected infrastructure stop")
        name = f"{entry.ordinal:04d}.json"
        path = root / "entries" / name
        record = {
            "schema": STAGE5F_DRY_SCHEMA,
            "execution_scope": "METADATA_ONLY_NOT_EXECUTED",
            "ordinal": entry.ordinal,
            "scenario_id": entry.scenario_id,
            "method": entry.method,
            "scenario_seed": entry.scenario_seed,
            "timeout_seconds": entry.timeout_seconds,
            "status": "NOT_EXECUTED",
            "comparator_executed": False,
            "canonical_input_accessed": False,
            "benchmark_truth_accessed": False,
            "scoring_performed": False,
            "automatic_rerun": False,
        }
        _stage5e_atomic_json_create(path, record)
        digest_rows.append({"ordinal": entry.ordinal, "path":
                            "entries/" + name, "sha256": sha256_file(path)})
    manifest = {
        "schema": STAGE5F_DRY_SCHEMA,
        "execution_scope": "METADATA_ONLY_NOT_EXECUTED",
        "planned_count": len(entries),
        "executed_count": 0,
        "core_count": sum(e.timeout_seconds == 3600 for e in entries),
        "scale_count": sum(e.timeout_seconds == 14400 for e in entries),
        "scoring_performed": False,
        "entries": digest_rows,
    }
    _stage5e_atomic_json_create(root / "manifest.json", manifest)
    return manifest


def run_stage5f_synthetic_isolation_probe(
    *,
    system_files: tuple[PrivateReadOnlyFile, ...],
    shell: Path,
) -> dict[str, object]:
    """Probe a private mount namespace using synthetic truth only.

    `shell` is a pinned OS file from system_files. Only this built-in
    synthetic test invokes the newly constructed namespace command.
    """
    with tempfile.TemporaryDirectory(
        prefix=".branchsnv_stage5_private_", dir=Path.home()
    ) as raw:
        work = _validate_stage3_writable_root(Path(raw))
        public = work / "public_input"
        public.mkdir(mode=0o700)
        (public / "test_input.txt").write_text("synthetic public input\n")
        with tempfile.TemporaryDirectory(
            prefix=".branchsnv_stage5_hidden_", dir=Path.home()
        ) as hidden:
            sentinel = Path(hidden) / "truth_sentinel.txt"
            sentinel.write_text("synthetic confidential truth\n")
            # Reject symlink escape instead of resolving it inside the mount.
            link = public / "leak"
            link.symlink_to(sentinel)
            try:
                try:
                    build_stage5f_private_root_command(
                        work=work, public_input=public,
                        system_files=system_files, child_argv=(str(shell), "-c", ":")
                    )
                except HarnessError as exc:
                    if "symlink" not in str(exc):
                        raise
                else:
                    raise HarnessError("synthetic truth symlink was accepted")
            finally:
                link.unlink()

            # A deliberately held host FD must not survive across exec.
            import fcntl
            original_fd = os.open(sentinel, os.O_RDONLY | os.O_NOFOLLOW)
            inherited_fd = fcntl.fcntl(original_fd, fcntl.F_DUPFD, 220)
            os.close(original_fd)
            script = (
                'test -r /run/branchsnv/input/test_input.txt || exit 61\n'
                'test ! -e "' + str(sentinel) + '" || exit 62\n'
                'test ! -e "' + str(sentinel.parent) + '" || exit 63\n'
                'test ! -e /run/branchsnv/input/leak || exit 64\n'
                'test ! -e /proc/self/fd/' + str(inherited_fd) + ' || exit 65\n'
                'test ! -e /proc/1/root' + str(sentinel) + ' || exit 66\n'
                'test ! -e /proc/1/root' + str(sentinel.parent) + ' || exit 67\n'
                'test ! -e /run/branchsnv/work/truth_sentinel.txt || exit 68\n'
                'test ! -e /run/branchsnv/work/public_input/test_input.txt || exit 69\n'
                'printf "STAGE5F_PRIVATE_ROOT_OK\\n"\n'
            )
            try:
                command = build_stage5f_private_root_command(
                    work=work, public_input=public,
                    system_files=system_files,
                    child_argv=(str(shell), "-c", script),
                )
                # Close all host descriptors. No comparator argv is accepted.
                completed = subprocess.run(
                    command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, timeout=30, close_fds=True,
                )
            finally:
                os.close(inherited_fd)
            if (completed.returncode != 0
                    or completed.stdout != "STAGE5F_PRIVATE_ROOT_OK\n"):
                raise HarnessError(
                    "Stage 5F private-root synthetic probe failed: "
                    + completed.stderr[-1200:]
                    + " (exit " + str(completed.returncode) + ")"
                )
            return {
                "sandbox_isolated": True,
                "synthetic_truth_inaccessible": True,
                "synthetic_input_visible": True,
                "comparator_executed": False,
                "canonical_input_accessed": False,
                "benchmark_truth_accessed": False,
            }


def _stage2_cli(
    argv: list[str],
) -> int:
    if (
        len(
            argv
        )
        == 4
        and argv[
            1
        ]
        == "--stage2-mock-worker"
    ):
        _stage2_mock_worker_file_entry(
            Path(
                argv[
                    2
                ]
            ),
            Path(
                argv[
                    3
                ]
            ),
        )

        return 0

    if (
        len(
            argv
        )
        == 4
        and argv[
            1
        ]
        == "--stage3-sandbox-worker"
    ):
        _stage3_sandbox_worker_file_entry(
            Path(
                argv[
                    2
                ]
            ),
            Path(
                argv[
                    3
                ]
            ),
        )

        return 0

    if (
        len(
            argv
        )
        == 4
        and argv[
            1
        ]
        == "--stage4-runner-mock-worker"
    ):
        _stage4_runner_worker_file_entry(
            Path(
                argv[
                    2
                ]
            ),
            Path(
                argv[
                    3
                ]
            ),
        )

        return 0

    if (
        len(argv) == 4
        and argv[1] == "--stage5b-synthetic-worker"
    ):
        _stage5b_synthetic_worker_file_entry(
            Path(argv[2]),
            Path(argv[3]),
        )
        return 0

    if (
        len(argv) == 4
        and argv[1] == "--stage5c-synthetic-runner-worker"
    ):
        _stage5c_synthetic_runner_file_entry(
            Path(argv[2]),
            Path(argv[3]),
        )
        return 0

    raise HarnessError(
        "no executable canonical harness CLI is authorized"
    )


if __name__ == "__main__":
    try:
        raise SystemExit(
            _stage2_cli(
                sys.argv
            )
        )

    except HarnessError as exc:
        print(
            f"HARNESS_ERROR: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(
            2
        )
