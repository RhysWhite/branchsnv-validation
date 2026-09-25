#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import time
import uuid


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

RESULTS_ROOT = (
    REPO_ROOT
    / "results"
    / "07_comparative_landscape"
)

PRODUCTION_ROOT = (
    RESULTS_ROOT
    / "t000002_authoritative_source_retrieval"
)

ASR000001_ROOT = (
    PRODUCTION_ROOT
    / "ASR000001"
)

ASR000002_ROOT = (
    PRODUCTION_ROOT
    / "ASR000002"
)

TRANSPORT_PATH = (
    HERE
    / "t000002_authoritative_source_network_transport.py"
)

CONTINUATION_DESIGN = (
    HERE
    / "asr000001_production_completion_and_continuation_design.json"
)

CONTINUATION_DESIGN_SUMS = (
    HERE
    / "asr000001_production_completion_and_continuation_design.sha256"
)

GUARD_IMPLEMENTATION_SUMS = (
    HERE
    / "asr000002_validated_address_failover_and_continuation_guard.sha256"
)

LIVE_AUTHORIZATION = (
    HERE
    / "asr000002_continuation_authorization.json"
)

DEFAULT_LEDGER = (
    RESULTS_ROOT
    / "baseline_scientific_screening_execution"
    / "event_ledger.tsv"
)

DEFAULT_REVIEW_PACKET = (
    RESULTS_ROOT
    / "baseline_scientific_screening_review_work"
    / "B000001"
    / "review_packet.tsv"
)

RUN_ID = "ASR000002"
SOURCE_RUN_ID = "ASR000001"

EXPECTED_CONTINUATION_QUEUE_SHA256 = (
    "d0a50b1610f0dcc5f61412cb2285b233"
    "91c38dd527890e1542c1b25ade7b3ca2"
)

EXPECTED_LEDGER_SHA256 = (
    "fb90d762d4fe9e81410816fe9403c735"
    "de138fe1614c11cb83993b40f2c63dff"
)

EXPECTED_REVIEW_PACKET_SHA256 = (
    "09e08a25873e9a628a2c7900b82f384f"
    "7b5838bb166b89d412759fe92a9101d6"
)

EXPECTED_QUEUE_IDS = [
    "RQ000001",
    "RQ000002",
    "RQ000004",
    "RQ000005",
    "RQ000007",
    "RQ000008",
    "RQ000010",
    "RQ000011",
    "RQ000013",
    "RQ000014",
    "RQ000016",
    "RQ000017",
    "RQ000019",
    "RQ000020",
    "RQ000022",
    "RQ000023",
]

AUTH_FIELDS = [
    "status",
    "schema_version",
    "parent_commit",
    "guard_implementation_freeze_sha256",
    "continuation_design_freeze_sha256",
    "source_run_id",
    "continuation_run_id",
    "continuation_queue_sha256",
    "continuation_task_count",
    "authorized_queue_ids",
    "authorized_route_codes",
    "source_final_status_required",
    "reissue_reason",
    "operator_id",
    "operator_type",
    "expected_pre_ledger_sha256",
    "expected_pre_review_packet_sha256",
    "successful_response_required_for_every_task",
    "dynamic_child_route_execution_authorized",
    "scientific_decisions_authorized",
    "event_ledger_mutation_authorized",
    "review_packet_mutation_authorized",
    "one_use",
]


class ContinuationError(
    RuntimeError
):
    pass


class ContinuationAuthorizationError(
    ContinuationError
):
    pass


class ContinuationRecoveryRequiredError(
    ContinuationError
):
    pass


def sha256_bytes(
    payload: bytes,
) -> str:
    return hashlib.sha256(
        payload
    ).hexdigest()


def sha256_file(
    path: Path,
) -> str:
    return sha256_bytes(
        path.read_bytes()
    )


def pretty_json_bytes(
    value: Any,
) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode(
        "utf-8"
    )


def load_module(
    path: Path,
    name: str,
):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise ContinuationError(
            f"Cannot import {path}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        name
    ] = module

    spec.loader.exec_module(
        module
    )

    return module


TRANSPORT_MODULE_NAME = "asr000002_frozen_transport"


def load_transport():
    """
    Return one process-wide instance of the frozen transport module.

    Exception classes must retain object identity across the guard, injected
    test adapters and transport retry machinery. Re-importing the same source
    file into distinct module objects would create distinct exception-class
    objects and break exception matching.
    """

    existing = sys.modules.get(
        TRANSPORT_MODULE_NAME
    )

    if existing is not None:
        return existing

    return load_module(
        TRANSPORT_PATH,
        TRANSPORT_MODULE_NAME,
    )


def load_continuation_design() -> dict:
    value = json.loads(
        CONTINUATION_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        value[
            "status"
        ]
        != "ASR000001_COMPLETE_CONTINUATION_REQUIRED"
    ):
        raise ContinuationError(
            "ASR000001 continuation design status changed"
        )

    continuation = value[
        "continuation"
    ]

    if (
        continuation[
            "run_id"
        ]
        != RUN_ID
    ):
        raise ContinuationError(
            "Continuation run ID changed"
        )

    if (
        continuation[
            "queue_sha256"
        ]
        != EXPECTED_CONTINUATION_QUEUE_SHA256
    ):
        raise ContinuationError(
            "Continuation queue identity changed"
        )

    if (
        continuation[
            "queue_ids"
        ]
        != EXPECTED_QUEUE_IDS
    ):
        raise ContinuationError(
            "Continuation queue IDs changed"
        )

    if (
        continuation[
            "authorized_task_count"
        ]
        != 16
    ):
        raise ContinuationError(
            "Continuation task count changed"
        )

    if continuation[
        "live_execution_authorized"
    ]:
        raise ContinuationError(
            "Continuation design unexpectedly grants live authority"
        )

    return value


def validate_asr000001() -> None:
    if not ASR000001_ROOT.is_dir():
        raise ContinuationError(
            "ASR000001 production evidence is absent"
        )

    checksums = (
        ASR000001_ROOT
        / "checksums.sha256"
    )

    for line in checksums.read_text(
        encoding="utf-8"
    ).splitlines():
        digest, relative = line.split(
            "  ",
            1,
        )

        path = (
            ASR000001_ROOT
            / relative
        )

        if (
            sha256_file(
                path
            )
            != digest
        ):
            raise ContinuationError(
                f"ASR000001 checksum mismatch: {relative}"
            )


def continuation_queue_context(
    *,
    ledger_path: Path,
    review_packet_path: Path,
) -> dict:
    transport = load_transport()

    transport.validate_scientific_state(
        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,
    )

    full = transport.seed_queue_context(
        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,
    )

    rows_by_id = {
        row[
            "queue_id"
        ]:
            row
        for row in full[
            "rows"
        ]
    }

    rows = [
        rows_by_id[
            queue_id
        ]
        for queue_id in EXPECTED_QUEUE_IDS
    ]

    if any(
        row[
            "route_code"
        ]
        not in {
            "pubmed_record",
            "pubmed_pmc_link_discovery",
        }
        for row in rows
    ):
        raise ContinuationError(
            "ASR000002 contains a non-NCBI route"
        )

    runner = full[
        "runner"
    ]

    payload = runner.tsv_bytes(
        fields=
            runner.QUEUE_FIELDS,

        rows=
            rows,
    )

    if (
        sha256_bytes(
            payload
        )
        != EXPECTED_CONTINUATION_QUEUE_SHA256
    ):
        raise ContinuationError(
            "Continuation queue bytes changed"
        )

    if len(
        rows
    ) != 16:
        raise ContinuationError(
            "Expected exactly 16 continuation tasks"
        )

    return {
        "transport":
            transport,

        "runner":
            runner,

        "rows":
            rows,

        "payload":
            payload,
    }


def git_output(
    *args: str,
) -> str:
    return subprocess.check_output(
        [
            "git",
            *args,
        ],
        cwd=
            REPO_ROOT,
        text=True,
    ).strip()


def synthetic_authorization(
    *,
    parent_commit: str,
    guard_freeze_sha256: str,
) -> dict:
    return {
        "status":
            "AUTHORIZED_ASR000002_NCBI_CONTINUATION_ONE_USE",

        "schema_version":
            1,

        "parent_commit":
            parent_commit,

        "guard_implementation_freeze_sha256":
            guard_freeze_sha256,

        "continuation_design_freeze_sha256":
            sha256_file(
                CONTINUATION_DESIGN_SUMS
            ),

        "source_run_id":
            SOURCE_RUN_ID,

        "continuation_run_id":
            RUN_ID,

        "continuation_queue_sha256":
            EXPECTED_CONTINUATION_QUEUE_SHA256,

        "continuation_task_count":
            16,

        "authorized_queue_ids":
            list(
                EXPECTED_QUEUE_IDS
            ),

        "authorized_route_codes": [
            "pubmed_record",
            "pubmed_pmc_link_discovery",
        ],

        "source_final_status_required":
            "transient_transport_error",

        "reissue_reason":
            "transport_failure_only",

        "operator_id":
            "Rhys",

        "operator_type":
            "human_with_assistance",

        "expected_pre_ledger_sha256":
            EXPECTED_LEDGER_SHA256,

        "expected_pre_review_packet_sha256":
            EXPECTED_REVIEW_PACKET_SHA256,

        "successful_response_required_for_every_task":
            False,

        "dynamic_child_route_execution_authorized":
            False,

        "scientific_decisions_authorized":
            False,

        "event_ledger_mutation_authorized":
            False,

        "review_packet_mutation_authorized":
            False,

        "one_use":
            True,
    }


def validate_authorization(
    *,
    authorization_path: Path,
    require_tracked: bool,
    guard_freeze_sha256_override: str | None = None,
) -> dict:
    value = json.loads(
        authorization_path.read_text(
            encoding="utf-8"
        )
    )

    if set(
        value
    ) != set(
        AUTH_FIELDS
    ):
        raise ContinuationAuthorizationError(
            "ASR000002 authorization schema mismatch"
        )

    expected_guard_sha = (
        guard_freeze_sha256_override
    )

    if require_tracked:
        if not GUARD_IMPLEMENTATION_SUMS.is_file():
            raise ContinuationAuthorizationError(
                "ASR000002 guard freeze is absent"
            )

        expected_guard_sha = (
            sha256_file(
                GUARD_IMPLEMENTATION_SUMS
            )
        )

    if not expected_guard_sha:
        raise ContinuationAuthorizationError(
            "Guard freeze identity required"
        )

    expected = synthetic_authorization(
        parent_commit=
            value[
                "parent_commit"
            ],

        guard_freeze_sha256=
            expected_guard_sha,
    )

    for key in AUTH_FIELDS:
        if (
            key
            == "parent_commit"
        ):
            continue

        if (
            value[
                key
            ]
            != expected[
                key
            ]
        ):
            raise ContinuationAuthorizationError(
                f"ASR000002 authorization field mismatch: {key}"
            )

    parent = value[
        "parent_commit"
    ]

    if (
        not isinstance(
            parent,
            str,
        )
        or len(
            parent
        )
        != 40
    ):
        raise ContinuationAuthorizationError(
            "Invalid ASR000002 authorization parent"
        )

    authorization_commit = (
        "UNTRACKED_TEST_AUTHORIZATION"
    )

    if require_tracked:
        if (
            authorization_path.resolve()
            != LIVE_AUTHORIZATION.resolve()
        ):
            raise ContinuationAuthorizationError(
                "Tracked continuation authorization must use canonical path"
            )

        relative = (
            LIVE_AUTHORIZATION.relative_to(
                REPO_ROOT
            ).as_posix()
        )

        head = git_output(
            "rev-parse",
            "HEAD",
        )

        head_parent = git_output(
            "rev-parse",
            "HEAD^",
        )

        if parent != head_parent:
            raise ContinuationAuthorizationError(
                "ASR000002 authorization parent is not current HEAD parent"
            )

        try:
            git_output(
                "ls-files",
                "--error-unmatch",
                relative,
            )

        except subprocess.CalledProcessError as exc:
            raise ContinuationAuthorizationError(
                "ASR000002 authorization is not tracked"
            ) from exc

        introducing = git_output(
            "log",
            "-1",
            "--format=%H",
            "--",
            relative,
        )

        if introducing != head:
            raise ContinuationAuthorizationError(
                "ASR000002 authorization was not introduced by current HEAD"
            )

        changed = set(
            git_output(
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                "HEAD",
            ).splitlines()
        )

        if changed != {
            relative
        }:
            raise ContinuationAuthorizationError(
                "ASR000002 authorization commit must contain exactly one file"
            )

        committed = subprocess.check_output(
            [
                "git",
                "show",
                "HEAD:"
                + relative,
            ],
            cwd=
                REPO_ROOT,
        )

        if (
            committed
            != authorization_path.read_bytes()
        ):
            raise ContinuationAuthorizationError(
                "Working ASR000002 authorization differs from committed bytes"
            )

        authorization_commit = (
            head
        )

    return {
        "authorization":
            value,

        "authorization_commit":
            authorization_commit,

        "authorization_sha256":
            sha256_file(
                authorization_path
            ),
    }


def run_state(
    *,
    production_root: Path,
) -> dict:
    final = (
        production_root
        / RUN_ID
    )

    staging = sorted(
        production_root.glob(
            "."
            + RUN_ID
            + ".tmp.*"
        )
    ) if production_root.exists() else []

    if final.exists():
        return {
            "status":
                "FINAL_RUN_EXISTS",

            "staging":
                staging,
        }

    if staging:
        return {
            "status":
                "STAGING_RUN_EXISTS",

            "staging":
                staging,
        }

    return {
        "status":
            "NO_RUN",

        "staging":
            [],
    }


def assert_run_absent(
    *,
    production_root: Path,
) -> None:
    state = run_state(
        production_root=
            production_root,
    )

    if (
        state[
            "status"
        ]
        != "NO_RUN"
    ):
        raise ContinuationRecoveryRequiredError(
            "ASR000002 cannot start from "
            + state[
                "status"
            ]
        )


def execute_continuation(
    *,
    authorization_path: Path,
    ledger_path: Path,
    review_packet_path: Path,
    production_root: Path,
    adapter,
    resolver: Callable[[str], list[str]],
    timestamp: Callable[[], str],
    monotonic_clock: Callable[[], float],
    sleeper: Callable[[float], None],
    require_tracked_authorization: bool,
    guard_freeze_sha256_override: str | None = None,
    allow_noncanonical_root: bool = False,
) -> dict:
    validate_asr000001()

    auth = validate_authorization(
        authorization_path=
            authorization_path,

        require_tracked=
            require_tracked_authorization,

        guard_freeze_sha256_override=
            guard_freeze_sha256_override,
    )

    if (
        not allow_noncanonical_root
        and production_root.resolve()
        != PRODUCTION_ROOT.resolve()
    ):
        raise ContinuationError(
            "Real ASR000002 requires canonical production root"
        )

    if (
        allow_noncanonical_root
        and production_root.resolve()
        == PRODUCTION_ROOT.resolve()
    ):
        raise ContinuationError(
            "Test ASR000002 cannot target canonical production root"
        )

    queue = continuation_queue_context(
        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,
    )

    transport = queue[
        "transport"
    ]

    runner = queue[
        "runner"
    ]

    rows = queue[
        "rows"
    ]

    transport.validate_scientific_state(
        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,
    )

    assert_run_absent(
        production_root=
            production_root,
    )

    production_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    staging = (
        production_root
        / (
            "."
            + RUN_ID
            + ".tmp."
            + uuid.uuid4().hex
        )
    )

    staging.mkdir()

    (
        staging
        / "raw"
    ).mkdir()

    try:
        transport.write_bytes_atomic(
            staging
            / "authorization.json",

            authorization_path.read_bytes(),
        )

        transport.write_bytes_atomic(
            staging
            / "continuation_queue.tsv",

            queue[
                "payload"
            ],
        )

        policy = (
            transport.load_transport_design()[
                "network_policy"
            ]
        )

        pacer = transport.RequestPacer(
            minimum_interval_seconds=
                float(
                    policy[
                        "request_policy"
                    ][
                        "global_minimum_interval_seconds"
                    ]
                ),

            clock=
                monotonic_clock,

            sleeper=
                sleeper,
        )

        results = []
        manifest_rows = []
        discovered = []

        for row in rows:
            result = transport.execute_seed_task(
                row=
                    row,

                network_policy=
                    policy,

                adapter=
                    adapter,

                resolver=
                    resolver,

                pacer=
                    pacer,

                timestamp=
                    timestamp,

                sleeper=
                    sleeper,
            )

            results.append(
                result
            )

            part, raw_files = (
                transport.manifest_rows_for_result(
                    queue_row=
                        row,

                    result=
                        result,
                )
            )

            manifest_rows.extend(
                part
            )

            discovered.extend(
                result[
                    "discovered_routes"
                ]
            )

            for (
                relative,
                payload,
            ) in raw_files:
                transport.write_bytes_atomic(
                    staging
                    / relative,

                    payload,
                )

        if len(
            results
        ) != 16:
            raise ContinuationRecoveryRequiredError(
                "ASR000002 did not consider all 16 continuation tasks"
            )

        counts = {}

        for result in results:
            status = (
                result[
                    "final_status"
                ]
                or "unknown"
            )

            counts[
                status
            ] = (
                counts.get(
                    status,
                    0,
                )
                + 1
            )

        summary = {
            "status":
                "ASR000002_COMPLETE",

            "source_run_id":
                SOURCE_RUN_ID,

            "retrieval_run_id":
                RUN_ID,

            "authorization_commit":
                auth[
                    "authorization_commit"
                ],

            "authorization_sha256":
                auth[
                    "authorization_sha256"
                ],

            "continuation_queue_sha256":
                EXPECTED_CONTINUATION_QUEUE_SHA256,

            "continuation_task_count":
                16,

            "tasks_considered":
                len(
                    results
                ),

            "transport_attempt_count":
                sum(
                    len(
                        result[
                            "attempts"
                        ]
                    )
                    for result in results
                ),

            "final_transport_status_counts":
                dict(
                    sorted(
                        counts.items()
                    )
                ),

            "discovered_child_routes":
                discovered,

            "dynamic_child_routes_executed":
                False,

            "scientific_decisions_made":
                False,

            "event_ledger_mutated":
                False,

            "review_packet_mutated":
                False,
        }

        transport.write_bytes_atomic(
            staging
            / "retrieval_manifest.tsv",

            transport.tsv_bytes(
                fields=
                    runner.RETRIEVAL_MANIFEST_FIELDS,

                rows=
                    manifest_rows,
            ),
        )

        transport.write_bytes_atomic(
            staging
            / "retrieval_summary.json",

            transport.pretty_json_bytes(
                summary
            ),
        )

        transport.write_bytes_atomic(
            staging
            / "evidence_assessment.tsv",

            transport.tsv_bytes(
                fields=
                    runner.EVIDENCE_ASSESSMENT_FIELDS,

                rows=[],
            ),
        )

        relative_paths = [
            str(
                path.relative_to(
                    staging
                )
            )
            for path in staging.rglob(
                "*"
            )
            if (
                path.is_file()
                and path.name
                != "checksums.sha256"
            )
        ]

        transport.write_bytes_atomic(
            staging
            / "checksums.sha256",

            transport.checksum_manifest_bytes(
                root=
                    staging,

                relative_paths=
                    relative_paths,
            ),
        )

        transport.validate_scientific_state(
            ledger_path=
                ledger_path,

            review_packet_path=
                review_packet_path,
        )

        final = (
            production_root
            / RUN_ID
        )

        os.replace(
            staging,
            final,
        )

        return {
            "status":
                "ASR000002_EXECUTION_COMPLETE",

            "tasks_considered":
                16,

            "transport_attempt_count":
                summary[
                    "transport_attempt_count"
                ],

            "final_transport_status_counts":
                summary[
                    "final_transport_status_counts"
                ],

            "discovered_child_route_count":
                len(
                    discovered
                ),

            "scientific_decisions_made":
                False,

            "event_ledger_mutated":
                False,

            "review_packet_mutated":
                False,

            "final_run_directory":
                str(
                    final
                ),
        }

    except Exception as exc:
        raise ContinuationRecoveryRequiredError(
            "ASR000002 interrupted after authorization consumption; "
            f"staging evidence preserved at {staging}"
        ) from exc


def execute_live(
    *,
    authorization_path: Path,
    ledger_path: Path,
    review_packet_path: Path,
) -> dict:
    transport = load_transport()

    validate_authorization(
        authorization_path=
            authorization_path,

        require_tracked=
            True,
    )

    assert_run_absent(
        production_root=
            PRODUCTION_ROOT,
    )

    return execute_continuation(
        authorization_path=
            authorization_path,

        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,

        production_root=
            PRODUCTION_ROOT,

        adapter=
            transport.PinnedHTTPSAdapter(),

        resolver=
            transport.default_resolver,

        timestamp=
            transport.utc_now,

        monotonic_clock=
            time.monotonic,

        sleeper=
            time.sleep,

        require_tracked_authorization=
            True,

        allow_noncanonical_root=
            False,
    )


def describe_status(
    *,
    ledger_path: Path,
    review_packet_path: Path,
) -> dict:
    validate_asr000001()

    queue = continuation_queue_context(
        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,
    )

    return {
        "status":
            "ASR000002_CONTINUATION_GUARD_READY_PRE_AUTHORIZATION",

        "source_run_id":
            SOURCE_RUN_ID,

        "continuation_run_id":
            RUN_ID,

        "continuation_queue_sha256":
            sha256_bytes(
                queue[
                    "payload"
                ]
            ),

        "continuation_task_count":
            len(
                queue[
                    "rows"
                ]
            ),

        "authorized_route_codes": [
            "pubmed_record",
            "pubmed_pmc_link_discovery",
        ],

        "validated_address_failover_implemented":
            True,

        "attempted_resolved_address_recorded":
            True,

        "production_run_state":
            run_state(
                production_root=
                    PRODUCTION_ROOT,
            )[
                "status"
            ],

        "live_authorization_present":
            LIVE_AUTHORIZATION.exists(),

        "live_execution_authorized":
            False,

        "scientific_decisions_allowed":
            False,

        "event_ledger_mutation_allowed":
            False,

        "review_packet_mutation_allowed":
            False,
    }


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
    )

    parser.add_argument(
        "--review-packet",
        type=Path,
        default=DEFAULT_REVIEW_PACKET,
    )

    parser.add_argument(
        "--authorization-json",
        type=Path,
    )

    parser.add_argument(
        "--execute-live",
        action="store_true",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.execute_live:
        if args.authorization_json is None:
            raise ContinuationAuthorizationError(
                "ASR000002 live execution requires separate tracked authorization"
            )

        value = execute_live(
            authorization_path=
                args.authorization_json.resolve(),

            ledger_path=
                args.ledger.resolve(),

            review_packet_path=
                args.review_packet.resolve(),
        )

    else:
        value = describe_status(
            ledger_path=
                args.ledger.resolve(),

            review_packet_path=
                args.review_packet.resolve(),
        )

    print(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
