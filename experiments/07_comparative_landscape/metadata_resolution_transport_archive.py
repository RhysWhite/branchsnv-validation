#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

import retrieve_metadata_resolution_queue as transport


ACCEPTED_TERMINAL = {
    "success",
    "not_found",
}

FAILURE_TERMINAL = {
    "retry_exhausted",
    "transport_failure",
    "redirect_failure",
    "authentication_failure",
    "response_integrity_failure",
}

RETRYABLE_ATTEMPT_OUTCOMES = {
    "retryable_http_status",
    "retryable_transport_failure",
    "interrupted_transport_attempt",
}


def canonical_json_bytes(
    value,
) -> bytes:
    return transport.canonical_json_bytes(
        value
    )


def sha256_file(
    path: Path,
) -> str:
    return transport.sha256_file(
        path
    )


def utc_timestamp(
    now_fn: Callable[
        [],
        datetime,
    ],
) -> str:
    return transport.utc_timestamp(
        now_fn
    )


def lookup_directory_name(
    logical_lookup_id: str,
) -> str:
    if not logical_lookup_id:
        raise ValueError(
            "Empty logical lookup ID"
        )

    value = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        logical_lookup_id,
    )

    if not value:
        raise ValueError(
            "Unsafe logical lookup ID"
        )

    return value


def lookup_root(
    archive_root: Path,
    logical_lookup_id: str,
) -> Path:
    return (
        archive_root
        / "raw"
        / lookup_directory_name(
            logical_lookup_id
        )
    )


def read_json(
    path: Path,
) -> dict:
    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        value,
        dict,
    ):
        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return value


def attempt_directories(
    root: Path,
) -> list[
    tuple[int, Path]
]:
    if not root.exists():
        return []

    output = []

    pattern = re.compile(
        r"^attempt_(\d{2})$"
    )

    for path in root.iterdir():
        if not path.is_dir():
            continue

        match = pattern.fullmatch(
            path.name
        )

        if not match:
            continue

        output.append(
            (
                int(
                    match.group(1)
                ),
                path,
            )
        )

    output.sort()

    numbers = [
        number
        for number, _path
        in output
    ]

    if numbers != list(
        range(
            1,
            len(numbers) + 1,
        )
    ):
        raise RuntimeError(
            "Attempt directories are not "
            "a sequential prefix"
        )

    if len(numbers) > transport.MAX_ATTEMPTS:
        raise RuntimeError(
            "Attempt count exceeds frozen ceiling"
        )

    return output


def load_attempt_records(
    root: Path,
) -> list[dict]:
    output = []

    for number, directory in (
        attempt_directories(
            root
        )
    ):
        attempt_path = (
            directory
            / "attempt.json"
        )

        request_path = (
            directory
            / "request.json"
        )

        if attempt_path.exists():
            record = read_json(
                attempt_path
            )

            if int(
                record[
                    "attempt_number"
                ]
            ) != number:
                raise RuntimeError(
                    "Attempt record number mismatch"
                )

            output.append(
                record
            )

            continue

        # A process may have died after initiating the
        # attempt but before writing attempt.json.
        #
        # Preserve that attempt number rather than
        # overwriting its directory during resume.
        if request_path.exists():
            output.append({
                "attempt_number":
                    number,

                "outcome":
                    "interrupted_transport_attempt",
            })

            continue

        raise RuntimeError(
            "Attempt directory contains neither "
            "attempt.json nor request.json"
        )

    return output


def verify_terminal_for_row(
    archive_root: Path,
    row: dict,
) -> dict:
    root = lookup_root(
        archive_root,
        row[
            "logical_lookup_id"
        ],
    )

    terminal = (
        transport.verify_terminal_archive(
            root
        )
    )

    expected = {
        "logical_lookup_id":
            row[
                "logical_lookup_id"
            ],

        "provider":
            row["provider"],

        "route":
            row["route"],

        "identifier_namespace":
            row[
                "identifier_namespace"
            ],

        "identifier":
            row["identifier"],
    }

    for key, value in (
        expected.items()
    ):
        if terminal.get(key) != value:
            raise RuntimeError(
                "Terminal archive identity mismatch "
                f"for {key}: "
                f"{terminal.get(key)!r} != "
                f"{value!r}"
            )

    if terminal.get(
        "terminal_status"
    ) not in ACCEPTED_TERMINAL:
        raise RuntimeError(
            "Terminal archive contains "
            "non-accepted status"
        )

    return terminal


def failure_path(
    archive_root: Path,
    logical_lookup_id: str,
) -> Path:
    return (
        lookup_root(
            archive_root,
            logical_lookup_id,
        )
        / "failure.json"
    )


def write_failure(
    archive_root: Path,
    row: dict,
    result: dict,
) -> None:
    status = result[
        "terminal_status"
    ]

    if status not in FAILURE_TERMINAL:
        raise ValueError(
            "Cannot persist non-failure "
            f"status as failure: {status}"
        )

    root = lookup_root(
        archive_root,
        row[
            "logical_lookup_id"
        ],
    )

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = {
        "logical_lookup_id":
            row[
                "logical_lookup_id"
            ],

        "provider":
            row["provider"],

        "route":
            row["route"],

        "identifier_namespace":
            row[
                "identifier_namespace"
            ],

        "identifier":
            row["identifier"],

        "terminal_status":
            status,

        "attempt_count":
            int(
                result[
                    "attempt_count"
                ]
            ),
    }

    path = failure_path(
        archive_root,
        row[
            "logical_lookup_id"
        ],
    )

    path.write_bytes(
        canonical_json_bytes(
            record
        )
    )


def infer_lookup_state(
    archive_root: Path,
    row: dict,
) -> dict:
    root = lookup_root(
        archive_root,
        row[
            "logical_lookup_id"
        ],
    )

    validate_lookup_raw_evidence(
        archive_root,
        row,
    )

    terminal_path = (
        root
        / "terminal.json"
    )

    failure = failure_path(
        archive_root,
        row[
            "logical_lookup_id"
        ],
    )

    if (
        terminal_path.exists()
        and failure.exists()
    ):
        raise RuntimeError(
            "Lookup has both terminal.json "
            "and failure.json"
        )

    if terminal_path.exists():
        terminal = (
            verify_terminal_for_row(
                archive_root,
                row,
            )
        )

        return {
            "state":
                "accepted",

            "terminal_status":
                terminal[
                    "terminal_status"
                ],

            "attempt_count":
                int(
                    terminal[
                        "attempt_count"
                    ]
                ),

            "start_attempt_number":
                None,

            "prior_attempts":
                terminal[
                    "attempts"
                ],
        }

    if failure.exists():
        record = read_json(
            failure
        )

        for key in (
            "logical_lookup_id",
            "provider",
            "route",
            "identifier_namespace",
            "identifier",
        ):
            if (
                record.get(key)
                != row.get(key)
            ):
                raise RuntimeError(
                    "Failure archive identity mismatch"
                )

        status = record.get(
            "terminal_status"
        )

        if status not in FAILURE_TERMINAL:
            raise RuntimeError(
                "Unknown archived failure status"
            )

        return {
            "state":
                "failure",

            "terminal_status":
                status,

            "attempt_count":
                int(
                    record[
                        "attempt_count"
                    ]
                ),

            "start_attempt_number":
                None,

            "prior_attempts":
                load_attempt_records(
                    root
                ),
        }

    attempts = load_attempt_records(
        root
    )

    if not attempts:
        return {
            "state":
                "pending",

            "terminal_status":
                "pending",

            "attempt_count":
                0,

            "start_attempt_number":
                1,

            "prior_attempts":
                [],
        }

    last = attempts[-1]

    outcome = last.get(
        "outcome"
    )

    count = len(attempts)

    if outcome in {
        "redirect_failure",
        "authentication_failure",
        "response_integrity_failure",
    }:
        return {
            "state":
                "failure",

            "terminal_status":
                outcome,

            "attempt_count":
                count,

            "start_attempt_number":
                None,

            "prior_attempts":
                attempts,
        }

    if outcome in RETRYABLE_ATTEMPT_OUTCOMES:
        if count >= transport.MAX_ATTEMPTS:
            return {
                "state":
                    "failure",

                "terminal_status":
                    "retry_exhausted",

                "attempt_count":
                    count,

                "start_attempt_number":
                    None,

                "prior_attempts":
                    attempts,
            }

        return {
            "state":
                "pending",

            "terminal_status":
                "pending",

            "attempt_count":
                count,

            "start_attempt_number":
                count + 1,

            "prior_attempts":
                attempts,
        }

    if outcome in ACCEPTED_TERMINAL:
        return {
            "state":
                "accepted_unfinalized",

            "terminal_status":
                outcome,

            "attempt_count":
                count,

            "start_attempt_number":
                None,

            "prior_attempts":
                attempts,
        }

    raise RuntimeError(
        "Unknown final attempt outcome: "
        + repr(outcome)
    )


def finalize_accepted_attempt(
    archive_root: Path,
    row: dict,
    state: dict,
) -> dict:
    attempts = state[
        "prior_attempts"
    ]

    if not attempts:
        raise RuntimeError(
            "Cannot finalise accepted lookup "
            "without attempt evidence"
        )

    last = attempts[-1]

    status = last.get(
        "outcome"
    )

    if status not in ACCEPTED_TERMINAL:
        raise RuntimeError(
            "Cannot finalise non-accepted attempt"
        )

    body_sha = last.get(
        "final_body_sha256"
    )

    if (
        not isinstance(
            body_sha,
            str,
        )
        or not body_sha
    ):
        raise RuntimeError(
            "Accepted attempt lacks final-body checksum"
        )

    terminal = {
        "logical_lookup_id":
            row[
                "logical_lookup_id"
            ],

        "provider":
            row["provider"],

        "route":
            row["route"],

        "identifier_namespace":
            row[
                "identifier_namespace"
            ],

        "identifier":
            row["identifier"],

        "terminal_status":
            status,

        "provider_identifier":
            last.get(
                "provider_identifier"
            ),

        "attempt_count":
            int(
                state[
                    "attempt_count"
                ]
            ),

        "attempts":
            attempts,

        "terminal_body_sha256":
            body_sha,
    }

    root = lookup_root(
        archive_root,
        row[
            "logical_lookup_id"
        ],
    )

    (
        root
        / "terminal.json"
    ).write_bytes(
        canonical_json_bytes(
            terminal
        )
    )

    verified = verify_terminal_for_row(
        archive_root,
        row,
    )

    return verified


def execute_queue(
    queue_rows: list[dict],
    *,
    archive_root: Path,
    executor,
    pacer: transport.ProviderPacer,
    retry_sleeper,
    environ: dict[str, str] | None = None,
    now_fn: Callable[
        [],
        datetime,
    ] | None = None,
) -> list[dict]:
    archive_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        archive_root
        / "raw"
    ).mkdir(
        parents=True,
        exist_ok=True,
    )

    if now_fn is None:
        now_fn = lambda: datetime.now(
            timezone.utc
        )

    results = []

    def paced_executor(
        request: transport.RequestSpec,
    ):
        pacer.wait(
            request.provider
        )

        return executor(
            request
        )

    for row in queue_rows:
        state = infer_lookup_state(
            archive_root,
            row,
        )

        if state[
            "state"
        ] == "accepted":
            results.append({
                "logical_lookup_id":
                    row[
                        "logical_lookup_id"
                    ],

                "terminal_status":
                    state[
                        "terminal_status"
                    ],

                "attempt_count":
                    state[
                        "attempt_count"
                    ],

                "resume_action":
                    "reused_terminal",
            })

            continue

        if state[
            "state"
        ] == "accepted_unfinalized":
            terminal = (
                finalize_accepted_attempt(
                    archive_root,
                    row,
                    state,
                )
            )

            results.append({
                "logical_lookup_id":
                    row[
                        "logical_lookup_id"
                    ],

                "terminal_status":
                    terminal[
                        "terminal_status"
                    ],

                "attempt_count":
                    terminal[
                        "attempt_count"
                    ],

                "resume_action":
                    "finalized_existing_terminal",
            })

            continue

        if state[
            "state"
        ] == "failure":
            failure = failure_path(
                archive_root,
                row[
                    "logical_lookup_id"
                ],
            )

            if not failure.exists():
                write_failure(
                    archive_root,
                    row,
                    {
                        "terminal_status":
                            state[
                                "terminal_status"
                            ],

                        "attempt_count":
                            state[
                                "attempt_count"
                            ],
                    },
                )

            results.append({
                "logical_lookup_id":
                    row[
                        "logical_lookup_id"
                    ],

                "terminal_status":
                    state[
                        "terminal_status"
                    ],

                "attempt_count":
                    state[
                        "attempt_count"
                    ],

                "resume_action":
                    "retained_failure",
            })

            continue

        result = transport.transport_lookup(
            row,
            archive_root=archive_root,
            executor=paced_executor,
            sleeper=retry_sleeper,
            environ=environ,
            now_fn=now_fn,
            start_attempt_number=state[
                "start_attempt_number"
            ],
            prior_attempts=state[
                "prior_attempts"
            ],
        )

        if (
            result[
                "terminal_status"
            ]
            in FAILURE_TERMINAL
        ):
            write_failure(
                archive_root,
                row,
                result,
            )

        results.append(
            result
        )

    return results


def write_tsv(
    path: Path,
    rows: list[dict],
    columns: list[str],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=columns,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow({
                column:
                    row.get(
                        column,
                        "",
                    )
                for column in columns
            })


def collect_lookup_status(
    queue_rows: list[dict],
    archive_root: Path,
) -> list[dict]:
    output = []

    for row in queue_rows:
        state = infer_lookup_state(
            archive_root,
            row,
        )

        output.append({
            "logical_lookup_id":
                row[
                    "logical_lookup_id"
                ],

            "provider":
                row["provider"],

            "route":
                row["route"],

            "identifier_namespace":
                row[
                    "identifier_namespace"
                ],

            "identifier":
                row["identifier"],

            "status":
                state[
                    "terminal_status"
                ],

            "attempt_count":
                state[
                    "attempt_count"
                ],
        })

    return output


def collect_attempt_rows(
    queue_rows: list[dict],
    archive_root: Path,
) -> list[dict]:
    output = []

    for row in queue_rows:
        root = lookup_root(
            archive_root,
            row[
                "logical_lookup_id"
            ],
        )

        for number, directory in (
            attempt_directories(
                root
            )
        ):
            request_path = (
                directory
                / "request.json"
            )

            attempt_path = (
                directory
                / "attempt.json"
            )

            request = (
                read_json(
                    request_path
                )
                if request_path.exists()
                else {}
            )

            if attempt_path.exists():
                attempt = read_json(
                    attempt_path
                )
            else:
                attempt = {
                    "attempt_number":
                        number,

                    "outcome":
                        "interrupted_transport_attempt",
                }

            output.append({
                "logical_lookup_id":
                    row[
                        "logical_lookup_id"
                    ],

                "provider":
                    row["provider"],

                "route":
                    row["route"],

                "identifier_namespace":
                    row[
                        "identifier_namespace"
                    ],

                "identifier":
                    row["identifier"],

                "attempt_number":
                    number,

                "timestamp_utc":
                    request.get(
                        "timestamp_utc",
                        "",
                    ),

                "outcome":
                    attempt.get(
                        "outcome",
                        "",
                    ),

                "http_status":
                    attempt.get(
                        "http_status",
                        "",
                    ),

                "provider_identifier":
                    attempt.get(
                        "provider_identifier",
                        "",
                    ),

                "redirect_hops":
                    attempt.get(
                        "redirect_hops",
                        "",
                    ),

                "final_body_sha256":
                    attempt.get(
                        "final_body_sha256",
                        "",
                    ),

                "error_type":
                    attempt.get(
                        "error_type",
                        "",
                    ),

                "error":
                    attempt.get(
                        "error",
                        "",
                    ),
            })

    return output


def response_header_value(
    response_record: dict,
    name: str,
) -> str:
    for key, value in (
        response_record.get(
            "response_headers",
            []
        )
    ):
        if key.lower() == name.lower():
            return value

    return ""


def collect_redirect_rows(
    queue_rows: list[dict],
    archive_root: Path,
) -> list[dict]:
    output = []

    for row in queue_rows:
        root = lookup_root(
            archive_root,
            row[
                "logical_lookup_id"
            ],
        )

        for number, directory in (
            attempt_directories(
                root
            )
        ):
            response_paths = sorted(
                directory.glob(
                    "hop_*_response.json"
                )
            )

            for response_path in (
                response_paths
            ):
                record = read_json(
                    response_path
                )

                status = int(
                    record[
                        "response_status"
                    ]
                )

                if (
                    status
                    not in transport.REDIRECT_STATUSES
                ):
                    continue

                output.append({
                    "logical_lookup_id":
                        row[
                            "logical_lookup_id"
                        ],

                    "provider":
                        row["provider"],

                    "attempt_number":
                        number,

                    "hop_number":
                        int(
                            record[
                                "hop_number"
                            ]
                        ),

                    "status":
                        status,

                    "request_url":
                        record[
                            "request_url"
                        ],

                    "response_url":
                        record[
                            "response_url"
                        ],

                    "location":
                        response_header_value(
                            record,
                            "Location",
                        ),

                    "body_sha256":
                        record[
                            "body_sha256"
                        ],
                })

    return output


def queue_is_frozen_full_set(
    queue_rows: list[dict],
) -> bool:
    frozen = transport.read_queue()

    frozen_ids = [
        row[
            "logical_lookup_id"
        ]
        for row in frozen
    ]

    observed_ids = [
        row[
            "logical_lookup_id"
        ]
        for row in queue_rows
    ]

    return (
        len(queue_rows)
        == transport.EXPECTED_QUEUE_COUNT
        and observed_ids
        == frozen_ids
    )


def build_manifest(
    queue_rows: list[dict],
    lookup_status: list[dict],
    *,
    now_fn: Callable[
        [],
        datetime,
    ],
) -> dict:
    status_counts = Counter(
        row["status"]
        for row in lookup_status
    )

    full_frozen = (
        queue_is_frozen_full_set(
            queue_rows
        )
    )

    all_accepted = all(
        row["status"]
        in ACCEPTED_TERMINAL
        for row
        in lookup_status
    )

    complete = (
        full_frozen
        and all_accepted
        and len(
            lookup_status
        )
        == transport.EXPECTED_QUEUE_COUNT
    )

    return {
        "schema_version":
            1,

        "status":
            (
                "COMPLETE"
                if complete
                else "INCOMPLETE"
            ),

        "generated_at_utc":
            utc_timestamp(
                now_fn
            ),

        "frozen_queue_sha256":
            transport.EXPECTED_QUEUE_SHA256,

        "frozen_queue_count":
            transport.EXPECTED_QUEUE_COUNT,

        "archive_queue_count":
            len(queue_rows),

        "archive_is_exact_frozen_queue":
            full_frozen,

        "lookup_status_counts":
            dict(
                sorted(
                    status_counts.items()
                )
            ),

        "accepted_terminal_statuses":
            sorted(
                ACCEPTED_TERMINAL
            ),

        "component_merge_performed":
            False,

        "scientific_screening_performed":
            False,
    }


def write_checksums(
    archive_root: Path,
) -> None:
    checksum_path = (
        archive_root
        / "checksums.sha256"
    )

    paths = sorted(
        path
        for path
        in archive_root.rglob("*")
        if (
            path.is_file()
            and path != checksum_path
        )
    )

    lines = []

    for path in paths:
        relative = path.relative_to(
            archive_root
        ).as_posix()

        lines.append(
            f"{sha256_file(path)}  "
            f"{relative}"
        )

    checksum_path.write_text(
        "\n".join(lines)
        + (
            "\n"
            if lines
            else ""
        ),
        encoding="utf-8",
    )


def validate_checksums(
    archive_root: Path,
    *,
    require_exact_coverage: bool = True,
) -> None:
    path = (
        archive_root
        / "checksums.sha256"
    )

    if not path.exists():
        raise RuntimeError(
            "checksums.sha256 missing"
        )

    listed = set()

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():
        if not line:
            continue

        digest, relative = (
            line.split(
                "  ",
                1,
            )
        )

        if relative in listed:
            raise RuntimeError(
                "Duplicate checksum path: "
                + relative
            )

        listed.add(
            relative
        )

        target = (
            archive_root
            / relative
        )

        if not target.is_file():
            raise RuntimeError(
                "Checksummed file missing: "
                + relative
            )

        actual = sha256_file(
            target
        )

        if actual != digest:
            raise RuntimeError(
                "Checksum mismatch: "
                + relative
            )

    if require_exact_coverage:
        actual_paths = {
            item.relative_to(
                archive_root
            ).as_posix()
            for item
            in archive_root.rglob("*")
            if (
                item.is_file()
                and item.name
                != "checksums.sha256"
            )
        }

        if listed != actual_paths:
            raise RuntimeError(
                "Checksum manifest does not exactly "
                "cover archive files"
            )


def write_archive_state(
    queue_rows: list[dict],
    archive_root: Path,
    *,
    now_fn: Callable[
        [],
        datetime,
    ] | None = None,
) -> dict:
    if now_fn is None:
        now_fn = lambda: datetime.now(
            timezone.utc
        )

    archive_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    for row in queue_rows:
        validate_lookup_raw_evidence(
            archive_root,
            row,
        )

        state = infer_lookup_state(
            archive_root,
            row,
        )

        if (
            state[
                "state"
            ]
            == "accepted_unfinalized"
        ):
            raise RuntimeError(
                "Cannot write archive summary while "
                "accepted evidence lacks terminal.json"
            )

        if (
            state[
                "state"
            ]
            == "failure"
            and not failure_path(
                archive_root,
                row[
                    "logical_lookup_id"
                ],
            ).is_file()
        ):
            raise RuntimeError(
                "Cannot write archive summary while "
                "failure state lacks failure.json"
            )

    (
        archive_root
        / "raw"
    ).mkdir(
        parents=True,
        exist_ok=True,
    )

    lookup_status = (
        collect_lookup_status(
            queue_rows,
            archive_root,
        )
    )

    attempts = (
        collect_attempt_rows(
            queue_rows,
            archive_root,
        )
    )

    redirects = (
        collect_redirect_rows(
            queue_rows,
            archive_root,
        )
    )

    write_tsv(
        archive_root
        / "lookup_status.tsv",
        lookup_status,
        [
            "logical_lookup_id",
            "provider",
            "route",
            "identifier_namespace",
            "identifier",
            "status",
            "attempt_count",
        ],
    )

    write_tsv(
        archive_root
        / "attempts.tsv",
        attempts,
        [
            "logical_lookup_id",
            "provider",
            "route",
            "identifier_namespace",
            "identifier",
            "attempt_number",
            "timestamp_utc",
            "outcome",
            "http_status",
            "provider_identifier",
            "redirect_hops",
            "final_body_sha256",
            "error_type",
            "error",
        ],
    )

    write_tsv(
        archive_root
        / "redirects.tsv",
        redirects,
        [
            "logical_lookup_id",
            "provider",
            "attempt_number",
            "hop_number",
            "status",
            "request_url",
            "response_url",
            "location",
            "body_sha256",
        ],
    )

    manifest = build_manifest(
        queue_rows,
        lookup_status,
        now_fn=now_fn,
    )

    (
        archive_root
        / "manifest.json"
    ).write_bytes(
        canonical_json_bytes(
            manifest
        )
    )

    write_checksums(
        archive_root
    )

    return manifest


def read_tsv(
    path: Path,
) -> list[dict]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as fh:
        return list(
            csv.DictReader(
                fh,
                delimiter="\t",
            )
        )


LOOKUP_STATUS_COLUMNS = [
    "logical_lookup_id",
    "provider",
    "route",
    "identifier_namespace",
    "identifier",
    "status",
    "attempt_count",
]

ATTEMPT_COLUMNS = [
    "logical_lookup_id",
    "provider",
    "route",
    "identifier_namespace",
    "identifier",
    "attempt_number",
    "timestamp_utc",
    "outcome",
    "http_status",
    "provider_identifier",
    "redirect_hops",
    "final_body_sha256",
    "error_type",
    "error",
]

REDIRECT_COLUMNS = [
    "logical_lookup_id",
    "provider",
    "attempt_number",
    "hop_number",
    "status",
    "request_url",
    "response_url",
    "location",
    "body_sha256",
]


def normalized_tsv_rows(
    rows: list[dict],
    columns: list[str],
) -> list[dict]:
    output = []

    for row in rows:
        normalized = {}

        for column in columns:
            value = row.get(
                column,
                "",
            )

            if value is None:
                value = ""

            normalized[
                column
            ] = str(value)

        output.append(
            normalized
        )

    return output


def read_tsv_exact_schema(
    path: Path,
    columns: list[str],
) -> list[dict]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as fh:
        reader = csv.DictReader(
            fh,
            delimiter="\t",
        )

        if reader.fieldnames != columns:
            raise RuntimeError(
                "Derived-ledger schema mismatch: "
                f"{path.name}"
            )

        return list(
            reader
        )


def validate_derived_ledgers(
    queue_rows: list[dict],
    archive_root: Path,
) -> None:
    contracts = [
        (
            "lookup_status.tsv",
            LOOKUP_STATUS_COLUMNS,
            collect_lookup_status(
                queue_rows,
                archive_root,
            ),
        ),
        (
            "attempts.tsv",
            ATTEMPT_COLUMNS,
            collect_attempt_rows(
                queue_rows,
                archive_root,
            ),
        ),
        (
            "redirects.tsv",
            REDIRECT_COLUMNS,
            collect_redirect_rows(
                queue_rows,
                archive_root,
            ),
        ),
    ]

    for (
        filename,
        columns,
        expected_rows,
    ) in contracts:
        path = (
            archive_root
            / filename
        )

        if not path.is_file():
            raise RuntimeError(
                "Derived ledger missing: "
                + filename
            )

        actual = (
            read_tsv_exact_schema(
                path,
                columns,
            )
        )

        expected = (
            normalized_tsv_rows(
                expected_rows,
                columns,
            )
        )

        if actual != expected:
            raise RuntimeError(
                "Derived ledger does not "
                "reproduce from raw evidence: "
                + filename
            )


def validate_archive(
    queue_rows: list[dict],
    archive_root: Path,
    *,
    require_complete: bool,
) -> dict:
    required = [
        "manifest.json",
        "lookup_status.tsv",
        "attempts.tsv",
        "redirects.tsv",
        "checksums.sha256",
    ]

    for name in required:
        if not (
            archive_root
            / name
        ).is_file():
            raise RuntimeError(
                "Required production artifact "
                f"missing: {name}"
            )

    validate_checksums(
        archive_root,
        require_exact_coverage=True,
    )

    for row in queue_rows:
        validate_lookup_raw_evidence(
            archive_root,
            row,
        )

    validate_derived_ledgers(
        queue_rows,
        archive_root,
    )

    manifest = read_json(
        archive_root
        / "manifest.json"
    )

    lookup_status = read_tsv(
        archive_root
        / "lookup_status.tsv"
    )

    expected_ids = [
        row[
            "logical_lookup_id"
        ]
        for row in queue_rows
    ]

    observed_ids = [
        row[
            "logical_lookup_id"
        ]
        for row in lookup_status
    ]

    if observed_ids != expected_ids:
        raise RuntimeError(
            "lookup_status.tsv does not match "
            "queue order/identity"
        )

    if len(
        observed_ids
    ) != len(
        set(observed_ids)
    ):
        raise RuntimeError(
            "Duplicate lookup-status IDs"
        )

    for queue_row, status_row in zip(
        queue_rows,
        lookup_status,
        strict=True,
    ):
        for key in (
            "logical_lookup_id",
            "provider",
            "route",
            "identifier_namespace",
            "identifier",
        ):
            if (
                queue_row[key]
                != status_row[key]
            ):
                raise RuntimeError(
                    "lookup_status identity mismatch"
                )

        status = status_row[
            "status"
        ]

        if status in ACCEPTED_TERMINAL:
            terminal = (
                verify_terminal_for_row(
                    archive_root,
                    queue_row,
                )
            )

            if (
                terminal[
                    "terminal_status"
                ]
                != status
            ):
                raise RuntimeError(
                    "lookup_status differs "
                    "from terminal archive"
                )

        elif status in FAILURE_TERMINAL:
            failure = failure_path(
                archive_root,
                queue_row[
                    "logical_lookup_id"
                ],
            )

            if not failure.is_file():
                raise RuntimeError(
                    "Failure lookup_status lacks "
                    "failure.json"
                )

            value = read_json(
                failure
            )

            if (
                value[
                    "terminal_status"
                ]
                != status
            ):
                raise RuntimeError(
                    "lookup_status differs "
                    "from failure archive"
                )

        elif status != "pending":
            raise RuntimeError(
                "Unknown lookup status: "
                + status
            )

    rebuilt = build_manifest(
        queue_rows,
        [
            {
                **row,
                "attempt_count":
                    int(
                        row[
                            "attempt_count"
                        ]
                    ),
            }
            for row in lookup_status
        ],
        now_fn=lambda:
            datetime(
                2000,
                1,
                1,
                tzinfo=timezone.utc,
            ),
    )

    comparable_fields = (
        "status",
        "frozen_queue_sha256",
        "frozen_queue_count",
        "archive_queue_count",
        "archive_is_exact_frozen_queue",
        "lookup_status_counts",
        "accepted_terminal_statuses",
        "component_merge_performed",
        "scientific_screening_performed",
    )

    for key in comparable_fields:
        if (
            manifest.get(key)
            != rebuilt.get(key)
        ):
            raise RuntimeError(
                "Manifest does not reproduce "
                f"from archived state: {key}"
            )

    if require_complete:
        if manifest[
            "status"
        ] != "COMPLETE":
            raise RuntimeError(
                "Production archive is not COMPLETE"
            )

        if not manifest[
            "archive_is_exact_frozen_queue"
        ]:
            raise RuntimeError(
                "COMPLETE archive is not exact "
                "frozen queue"
            )

        if len(
            lookup_status
        ) != transport.EXPECTED_QUEUE_COUNT:
            raise RuntimeError(
                "COMPLETE archive lookup count drift"
            )

    return manifest


def scan_for_secret(
    root: Path,
    secret: str,
) -> bool:
    needle = secret.encode(
        "utf-8"
    )

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if needle in path.read_bytes():
            return True

    return False


# ------------------------------------------------------------
# Full raw-evidence integrity validation.
#
# This intentionally validates the per-response body hashes
# BEFORE write_checksums() can create a new archive-wide
# checksum snapshot.
# ------------------------------------------------------------

def validate_lookup_raw_evidence(
    archive_root: Path,
    row: dict,
) -> None:
    root = lookup_root(
        archive_root,
        row[
            "logical_lookup_id"
        ],
    )

    if not root.exists():
        return

    allowed_root_files = {
        "terminal.json",
        "failure.json",
    }

    for item in root.iterdir():
        if item.is_dir():
            if not re.fullmatch(
                r"attempt_\d{2}",
                item.name,
            ):
                raise RuntimeError(
                    "Unexpected lookup archive directory: "
                    + item.name
                )

        elif item.name not in allowed_root_files:
            raise RuntimeError(
                "Unexpected lookup archive file: "
                + item.name
            )

    expected_request = (
        transport.build_request(
            row,
            environ={},
        )
    )

    attempts = load_attempt_records(
        root
    )

    attempt_dirs = attempt_directories(
        root
    )

    sensitive = {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "api-key",
    }

    for (
        attempt_number,
        directory,
    ) in attempt_dirs:
        request_path = (
            directory
            / "request.json"
        )

        if not request_path.is_file():
            raise RuntimeError(
                "Attempt missing request.json"
            )

        request = read_json(
            request_path
        )

        expected_identity = {
            "logical_lookup_id":
                row[
                    "logical_lookup_id"
                ],

            "provider":
                row["provider"],

            "route":
                row["route"],

            "identifier_namespace":
                row[
                    "identifier_namespace"
                ],

            "identifier":
                row["identifier"],
        }

        for key, value in (
            expected_identity.items()
        ):
            if request.get(key) != value:
                raise RuntimeError(
                    "Archived request identity "
                    f"mismatch for {key}"
                )

        if int(
            request.get(
                "attempt_number",
                -1,
            )
        ) != attempt_number:
            raise RuntimeError(
                "Archived request attempt-number mismatch"
            )

        if request.get(
            "method"
        ) != "GET":
            raise RuntimeError(
                "Archived request method mismatch"
            )

        if request.get(
            "url"
        ) != transport.sanitized_url(
            expected_request.url
        ):
            raise RuntimeError(
                "Archived initial request URL mismatch"
            )

        for pair in request.get(
            "headers",
            []
        ):
            if (
                not isinstance(pair, list)
                or len(pair) != 2
            ):
                raise RuntimeError(
                    "Malformed archived request header"
                )

            key, value = pair

            if (
                str(key).lower()
                in sensitive
                and value
                != "<REDACTED>"
            ):
                raise RuntimeError(
                    "Sensitive request header "
                    "was not redacted"
                )

        response_paths = sorted(
            directory.glob(
                "hop_*_response.json"
            )
        )

        hop_numbers = []

        response_records = []

        for response_path in (
            response_paths
        ):
            match = re.fullmatch(
                r"hop_(\d{2})_response\.json",
                response_path.name,
            )

            if not match:
                raise RuntimeError(
                    "Malformed hop-response filename"
                )

            hop_numbers.append(
                int(
                    match.group(1)
                )
            )

            response_records.append(
                read_json(
                    response_path
                )
            )

        if hop_numbers != list(
            range(
                len(hop_numbers)
            )
        ):
            raise RuntimeError(
                "Redirect/response hop numbering "
                "is not sequential"
            )

        expected_url = (
            transport.sanitized_url(
                expected_request.url
            )
        )

        allowed_attempt_files = {
            "request.json",
            "attempt.json",
        }

        for index, record in enumerate(
            response_records
        ):
            if int(
                record.get(
                    "hop_number",
                    -1,
                )
            ) != index:
                raise RuntimeError(
                    "Hop metadata number mismatch"
                )

            if (
                record.get(
                    "request_url"
                )
                != expected_url
            ):
                raise RuntimeError(
                    "Archived redirect-chain "
                    "request URL mismatch"
                )

            body_name = record.get(
                "body_file"
            )

            expected_body_name = (
                f"hop_{index:02d}_body.bin"
            )

            if (
                body_name
                != expected_body_name
            ):
                raise RuntimeError(
                    "Unexpected archived body filename"
                )

            body_path = (
                directory
                / body_name
            )

            if not body_path.is_file():
                raise RuntimeError(
                    "Archived response body missing"
                )

            body = body_path.read_bytes()

            if len(
                body
            ) != int(
                record[
                    "body_length"
                ]
            ):
                raise RuntimeError(
                    "Archived response body-length mismatch"
                )

            if (
                transport.sha256_bytes(
                    body
                )
                != record[
                    "body_sha256"
                ]
            ):
                raise RuntimeError(
                    "Archived response body checksum mismatch"
                )

            allowed_attempt_files.add(
                f"hop_{index:02d}_response.json"
            )

            allowed_attempt_files.add(
                body_name
            )

            status = int(
                record[
                    "response_status"
                ]
            )

            if (
                index + 1
                < len(
                    response_records
                )
            ):
                if (
                    status
                    not in transport.REDIRECT_STATUSES
                ):
                    raise RuntimeError(
                        "Additional hop follows "
                        "non-redirect response"
                    )

                location = (
                    response_header_value(
                        record,
                        "Location",
                    )
                )

                if not location:
                    raise RuntimeError(
                        "Archived redirect hop lacks Location"
                    )

                target = (
                    transport.validate_redirect_target(
                        provider=
                            row["provider"],

                        current_url=
                            expected_url,

                        location=
                            location,
                    )
                )

                expected_url = (
                    transport.sanitized_url(
                        target
                    )
                )

        for item in directory.iterdir():
            if (
                item.is_file()
                and item.name
                not in allowed_attempt_files
            ):
                raise RuntimeError(
                    "Unexpected attempt archive file: "
                    + item.name
                )

        attempt_path = (
            directory
            / "attempt.json"
        )

        if attempt_path.exists():
            attempt = read_json(
                attempt_path
            )

            if int(
                attempt.get(
                    "attempt_number",
                    -1,
                )
            ) != attempt_number:
                raise RuntimeError(
                    "attempt.json number mismatch"
                )

            if (
                "http_status"
                in attempt
                and response_records
            ):
                if int(
                    attempt[
                        "http_status"
                    ]
                ) != int(
                    response_records[-1][
                        "response_status"
                    ]
                ):
                    raise RuntimeError(
                        "attempt.json HTTP status "
                        "differs from final hop"
                    )

            if (
                "final_body_sha256"
                in attempt
            ):
                if not response_records:
                    raise RuntimeError(
                        "Attempt has final-body checksum "
                        "without response evidence"
                    )

                if (
                    attempt[
                        "final_body_sha256"
                    ]
                    != response_records[-1][
                        "body_sha256"
                    ]
                ):
                    raise RuntimeError(
                        "Attempt final-body checksum "
                        "differs from archived response"
                    )

            if (
                "redirect_hops"
                in attempt
            ):
                if int(
                    attempt[
                        "redirect_hops"
                    ]
                ) != max(
                    0,
                    len(
                        response_records
                    )
                    - 1,
                ):
                    raise RuntimeError(
                        "Attempt redirect-hop count mismatch"
                    )

    terminal_path = (
        root
        / "terminal.json"
    )

    failure = (
        root
        / "failure.json"
    )

    if (
        terminal_path.exists()
        and failure.exists()
    ):
        raise RuntimeError(
            "Lookup archive has both terminal "
            "and failure records"
        )

    if terminal_path.exists():
        terminal = (
            transport.verify_terminal_archive(
                root
            )
        )

        expected_identity = {
            "logical_lookup_id":
                row[
                    "logical_lookup_id"
                ],

            "provider":
                row["provider"],

            "route":
                row["route"],

            "identifier_namespace":
                row[
                    "identifier_namespace"
                ],

            "identifier":
                row["identifier"],
        }

        for key, value in (
            expected_identity.items()
        ):
            if terminal.get(key) != value:
                raise RuntimeError(
                    "Terminal identity mismatch"
                )

        if terminal.get(
            "terminal_status"
        ) not in ACCEPTED_TERMINAL:
            raise RuntimeError(
                "terminal.json contains "
                "non-accepted status"
            )

        if int(
            terminal.get(
                "attempt_count",
                -1,
            )
        ) != len(attempts):
            raise RuntimeError(
                "Terminal attempt count mismatch"
            )

        if (
            terminal.get(
                "attempts"
            )
            != attempts
        ):
            raise RuntimeError(
                "Terminal attempt ledger differs "
                "from immutable attempt archive"
            )

        if (
            not attempts
            or attempts[-1].get(
                "outcome"
            )
            != terminal[
                "terminal_status"
            ]
        ):
            raise RuntimeError(
                "Terminal status differs from "
                "final attempt outcome"
            )

    elif failure.exists():
        value = read_json(
            failure
        )

        expected_identity = {
            "logical_lookup_id":
                row[
                    "logical_lookup_id"
                ],

            "provider":
                row["provider"],

            "route":
                row["route"],

            "identifier_namespace":
                row[
                    "identifier_namespace"
                ],

            "identifier":
                row["identifier"],
        }

        for key, expected in (
            expected_identity.items()
        ):
            if value.get(key) != expected:
                raise RuntimeError(
                    "Failure identity mismatch"
                )

        status = value.get(
            "terminal_status"
        )

        if status not in FAILURE_TERMINAL:
            raise RuntimeError(
                "failure.json contains "
                "unknown status"
            )

        if int(
            value.get(
                "attempt_count",
                -1,
            )
        ) != len(attempts):
            raise RuntimeError(
                "Failure attempt-count mismatch"
            )

        if (
            status
            == "retry_exhausted"
            and len(attempts)
            != transport.MAX_ATTEMPTS
        ):
            raise RuntimeError(
                "retry_exhausted without "
                "maximum attempt count"
            )


# ------------------------------------------------------------
# Frozen production runner.
#
# It is intentionally unreachable while the low-level module
# retains LIVE_EXECUTION_ENABLED = False.
# ------------------------------------------------------------

HERE = Path(__file__).resolve().parent

DEFAULT_ARCHIVE_ROOT = (
    HERE.parent.parent
    / "results"
    / "07_comparative_landscape"
    / "metadata_resolution_retrieval"
)


def run_frozen_queue_live(
    *,
    archive_root: Path,
    environ: dict[str, str] | None = None,
) -> dict:
    if environ is None:
        environ = dict(
            os.environ
        )

    # Gate BEFORE creating any result directory.
    transport.assert_live_execution_allowed(
        environ=environ
    )

    transport.verify_frozen_queue()

    queue_rows = (
        transport.read_queue()
    )

    if not queue_is_frozen_full_set(
        queue_rows
    ):
        raise RuntimeError(
            "Live runner queue differs from "
            "frozen 1,731-lookup manifest"
        )

    # If a prior snapshot exists, validate every file that
    # snapshot claimed before adding new resume evidence.
    checksum_path = (
        archive_root
        / "checksums.sha256"
    )

    if checksum_path.exists():
        validate_checksums(
            archive_root,
            require_exact_coverage=False,
        )

    for row in queue_rows:
        validate_lookup_raw_evidence(
            archive_root,
            row,
        )

    pacer = (
        transport.ProviderPacer()
    )

    execute_queue(
        queue_rows,
        archive_root=archive_root,
        executor=
            transport.default_http_executor,
        pacer=pacer,
        retry_sleeper=time.sleep,
        environ=environ,
    )

    manifest = (
        write_archive_state(
            queue_rows,
            archive_root,
        )
    )

    validate_archive(
        queue_rows,
        archive_root,
        require_complete=(
            manifest[
                "status"
            ]
            == "COMPLETE"
        ),
    )

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--execute-live",
        action="store_true",
    )

    parser.add_argument(
        "--archive-root",
        type=Path,
        default=
            DEFAULT_ARCHIVE_ROOT,
    )

    args = parser.parse_args()

    transport.verify_frozen_queue()

    if not args.execute_live:
        print(
            json.dumps(
                {
                    "status":
                        "DRY_RUN_ONLY",

                    "logical_lookup_count":
                        transport.EXPECTED_QUEUE_COUNT,

                    "live_execution_enabled":
                        transport.LIVE_EXECUTION_ENABLED,

                    "archive_root":
                        str(
                            args.archive_root
                        ),

                    "message":
                        "Archive runner loaded; "
                        "no network request executed.",
                },
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    manifest = run_frozen_queue_live(
        archive_root=
            args.archive_root,
    )

    print(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
    )

    return (
        0
        if manifest[
            "status"
        ] == "COMPLETE"
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
