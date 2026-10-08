#!/usr/bin/env python3
"""
Source-forensic diagnostic for the frozen W0A07/PAML OpenCitations
independent-count mismatch.

This program is NOT the Wave 0 production retriever.

Frozen request sequence:
    citation-count -> unfiltered citations CSV -> citation-count

No scientific filtering or screening is performed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import io
import json
import os
import re
import subprocess
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


OPENCITATIONS_ROOT = (
    "https://api.opencitations.net/index/v2"
)

ANCHOR_ID = "W0A07"
ANCHOR_TOOL = "PAML"
ANCHOR_DOI = "10.1093/molbev/msm088"

OCI_RE = re.compile(
    r"^[0-9]+-[0-9]+$"
)

EXPECTED_ATTEMPT05_COUNT = 12846
EXPECTED_ATTEMPT05_UNIQUE_OCI = 12845
EXPECTED_ATTEMPT05_ROOT_LEAVES = 10

MAX_ATTEMPTS = 5
REQUEST_DELAY_SECONDS = 0.40
REQUEST_TIMEOUT_SECONDS = 180


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def sha256_bytes(
    data: bytes,
) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def sha256_file(
    path: Path,
) -> str:
    h = hashlib.sha256()

    with path.open("rb") as fh:
        for chunk in iter(
            lambda: fh.read(
                1024 * 1024
            ),
            b"",
        ):
            h.update(chunk)

    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            [
                "git",
                "rev-parse",
                "HEAD",
            ],
            text=True,
        ).strip()
    except Exception:
        return ""


def citation_count_url() -> str:
    identifier = urllib.parse.quote(
        f"doi:{ANCHOR_DOI}",
        safe=":",
    )

    return (
        f"{OPENCITATIONS_ROOT}/"
        f"citation-count/{identifier}"
    )


def citations_url() -> str:
    identifier = urllib.parse.quote(
        f"doi:{ANCHOR_DOI}",
        safe=":",
    )

    return (
        f"{OPENCITATIONS_ROOT}/"
        f"citations/{identifier}"
    )


def fetch_bytes(
    url: str,
    *,
    headers: dict[str, str],
    raw_path: Path,
    opener: Callable[..., Any] = (
        urllib.request.urlopen
    ),
    retries: int = MAX_ATTEMPTS,
    delay: float = REQUEST_DELAY_SECONDS,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[
    bytes,
    dict[str, Any],
]:
    if retries < 1:
        raise ValueError(
            "retries must be >= 1"
        )

    last_error: BaseException | None = None

    for attempt in range(
        1,
        retries + 1,
    ):
        request = urllib.request.Request(
            url,
            headers=headers,
        )

        try:
            with opener(
                request,
                timeout=timeout,
            ) as response:
                body = response.read()

                status = int(
                    getattr(
                        response,
                        "status",
                        200,
                    )
                    or 200
                )

                content_type = ""

                response_headers = getattr(
                    response,
                    "headers",
                    None,
                )

                if response_headers is not None:
                    try:
                        content_type = str(
                            response_headers.get(
                                "Content-Type",
                                "",
                            )
                            or ""
                        )
                    except Exception:
                        content_type = ""

        except urllib.error.HTTPError as exc:
            last_error = exc

            retryable = (
                exc.code == 429
                or 500 <= exc.code <= 599
            )

            if (
                not retryable
                or attempt == retries
            ):
                raise RuntimeError(
                    "Diagnostic request failed: "
                    f"HTTP {exc.code}: {url}"
                ) from exc

        except (
            urllib.error.URLError,
            TimeoutError,
            http.client.IncompleteRead,
        ) as exc:
            last_error = exc

            if attempt == retries:
                break

        else:
            raw_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            raw_path.write_bytes(
                body
            )

            return (
                body,
                {
                    "url": url,
                    "attempt":
                        attempt,
                    "http_status":
                        status,
                    "content_type":
                        content_type,
                    "bytes":
                        len(body),
                    "sha256":
                        sha256_bytes(
                            body
                        ),
                    "completed_at_utc":
                        utc_now(),
                },
            )

        if (
            attempt < retries
            and delay > 0
        ):
            sleep_fn(
                delay
            )

    raise RuntimeError(
        "Diagnostic request failed after "
        f"{retries} attempts: {url}"
    ) from last_error


def parse_count_body(
    body: bytes,
) -> int:
    try:
        payload = json.loads(
            body.decode(
                "utf-8"
            )
        )
    except Exception as exc:
        raise RuntimeError(
            "Invalid citation-count JSON response"
        ) from exc

    if (
        not isinstance(
            payload,
            list,
        )
        or len(payload) != 1
        or not isinstance(
            payload[0],
            dict,
        )
        or "count" not in payload[0]
    ):
        raise RuntimeError(
            "Unexpected citation-count response shape"
        )

    value = str(
        payload[0]["count"]
    ).strip()

    if not re.fullmatch(
        r"[0-9]+",
        value,
    ):
        raise RuntimeError(
            "Invalid citation-count value"
        )

    return int(
        value
    )


def parse_csv_body(
    body: bytes,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    try:
        text = body.decode(
            "utf-8-sig"
        )
    except UnicodeDecodeError as exc:
        raise RuntimeError(
            "OpenCitations CSV is not valid UTF-8"
        ) from exc

    reader = csv.DictReader(
        io.StringIO(
            text
        )
    )

    fieldnames = (
        reader.fieldnames
        or []
    )

    fieldnames = [
        str(name)
        for name in fieldnames
        if name is not None
    ]

    if not fieldnames:
        raise RuntimeError(
            "OpenCitations CSV has no header"
        )

    if len(fieldnames) != len(
        set(fieldnames)
    ):
        raise RuntimeError(
            "OpenCitations CSV contains duplicate header fields"
        )

    required = {
        "oci",
        "citing",
        "cited",
    }

    missing = sorted(
        required
        - set(fieldnames)
    )

    if missing:
        raise RuntimeError(
            "OpenCitations CSV missing required fields: "
            f"{missing}"
        )

    rows: list[
        dict[str, str]
    ] = []

    for index, raw_row in enumerate(
        reader,
        start=2,
    ):
        if None in raw_row:
            raise RuntimeError(
                "OpenCitations CSV row contains "
                f"unexpected extra columns at line {index}"
            )

        row = {
            field:
                str(
                    raw_row.get(
                        field,
                        "",
                    )
                    or ""
                )
            for field in fieldnames
        }

        rows.append(
            row
        )

    return (
        fieldnames,
        rows,
    )


def load_attempt05_oci_union(
    archive_path: Path,
) -> set[str]:
    if not archive_path.is_file():
        raise RuntimeError(
            f"Attempt-05 archive missing: {archive_path}"
        )

    marker = (
        "citation_wave_0/raw/opencitations/"
        "W0A07/forward_partitions/depth_00/"
        "digits_01_suffix_"
    )

    ocis: list[str] = []

    suffixes: set[str] = set()

    with tarfile.open(
        archive_path,
        "r:gz",
    ) as tf:
        members = [
            member
            for member in tf.getmembers()
            if (
                member.isfile()
                and marker
                in member.name
                and member.name.endswith(
                    ".json"
                )
            )
        ]

        if (
            len(members)
            != EXPECTED_ATTEMPT05_ROOT_LEAVES
        ):
            raise RuntimeError(
                "Attempt-05 archive does not contain "
                "exactly ten W0A07 forward root leaves"
            )

        for member in members:
            name_match = re.search(
                r"digits_01_suffix_([0-9])\.json$",
                member.name,
            )

            if not name_match:
                raise RuntimeError(
                    "Unexpected Attempt-05 root-leaf filename: "
                    f"{member.name}"
                )

            suffix = (
                name_match.group(1)
            )

            if suffix in suffixes:
                raise RuntimeError(
                    "Duplicate Attempt-05 root suffix: "
                    f"{suffix}"
                )

            suffixes.add(
                suffix
            )

            fh = tf.extractfile(
                member
            )

            if fh is None:
                raise RuntimeError(
                    f"Could not extract {member.name}"
                )

            payload = json.loads(
                fh.read().decode(
                    "utf-8"
                )
            )

            if (
                isinstance(
                    payload,
                    list,
                )
                and len(payload) == 1
                and isinstance(
                    payload[0],
                    list,
                )
            ):
                payload = (
                    payload[0]
                )

            if not isinstance(
                payload,
                list,
            ):
                raise RuntimeError(
                    "Unexpected Attempt-05 leaf shape: "
                    f"{member.name}"
                )

            for row in payload:
                if not isinstance(
                    row,
                    dict,
                ):
                    raise RuntimeError(
                        "Non-object row in Attempt-05 leaf"
                    )

                oci = str(
                    row.get(
                        "oci",
                    )
                    or ""
                ).strip()

                if not OCI_RE.fullmatch(
                    oci
                ):
                    raise RuntimeError(
                        "Malformed OCI in Attempt-05 archive: "
                        f"{oci!r}"
                    )

                citing_component = (
                    oci.split(
                        "-",
                        1,
                    )[0]
                )

                if (
                    citing_component[-1]
                    != suffix
                ):
                    raise RuntimeError(
                        "Attempt-05 OCI outside archived leaf: "
                        f"{oci}"
                    )

                ocis.append(
                    oci
                )

    if suffixes != set(
        "0123456789"
    ):
        raise RuntimeError(
            "Attempt-05 archive root suffix set is incomplete"
        )

    if len(ocis) != len(
        set(ocis)
    ):
        raise RuntimeError(
            "Attempt-05 archive contains duplicate OCI"
        )

    result = set(
        ocis
    )

    if (
        len(result)
        != EXPECTED_ATTEMPT05_UNIQUE_OCI
    ):
        raise RuntimeError(
            "Attempt-05 OCI-union identity mismatch: "
            f"{len(result)}"
        )

    return result


def analyse_csv_rows(
    rows: list[dict[str, str]],
    *,
    attempt05_ocis: set[str],
) -> dict[str, Any]:
    empty_rows: list[
        dict[str, str]
    ] = []

    nonconforming_rows: list[
        dict[str, str]
    ] = []

    valid_rows: list[
        dict[str, str]
    ] = []

    oci_counts: Counter[str] = Counter()

    for row in rows:
        oci = str(
            row.get(
                "oci",
                "",
            )
            or ""
        ).strip()

        if not oci:
            empty_rows.append(
                row
            )

            continue

        if not OCI_RE.fullmatch(
            oci
        ):
            nonconforming_rows.append(
                row
            )

            continue

        valid_rows.append(
            row
        )

        oci_counts[
            oci
        ] += 1

    csv_unique = set(
        oci_counts
    )

    duplicate_ocis = sorted(
        oci
        for oci, count
        in oci_counts.items()
        if count > 1
    )

    csv_only = sorted(
        csv_unique
        - attempt05_ocis
    )

    attempt_only = sorted(
        attempt05_ocis
        - csv_unique
    )

    csv_only_set = set(
        csv_only
    )

    csv_only_rows = [
        row
        for row in valid_rows
        if str(
            row.get(
                "oci",
                "",
            )
            or ""
        ).strip()
        in csv_only_set
    ]

    exceptional_rows = (
        empty_rows
        + nonconforming_rows
    )

    return {
        "csv_data_rows":
            len(rows),
        "empty_oci_rows":
            len(empty_rows),
        "nonconforming_oci_rows":
            len(nonconforming_rows),
        "valid_numeric_oci_rows":
            len(valid_rows),
        "unique_valid_numeric_ocis":
            len(csv_unique),
        "duplicate_valid_oci_count":
            len(duplicate_ocis),
        "duplicate_valid_ocis":
            duplicate_ocis,
        "attempt05_unique_ocis":
            len(
                attempt05_ocis
            ),
        "csv_only_oci_count":
            len(csv_only),
        "attempt05_only_oci_count":
            len(attempt_only),
        "csv_only_ocis":
            csv_only,
        "attempt05_only_ocis":
            attempt_only,
        "csv_only_rows":
            csv_only_rows,
        "exceptional_rows":
            exceptional_rows,
    }


def classify_result(
    *,
    pre_count: int,
    post_count: int,
    analysis: dict[str, Any],
) -> str:
    if pre_count != post_count:
        return (
            "COUNT_CHANGED_DURING_INTERVAL"
        )

    if (
        pre_count == 12846
        and post_count == 12846
        and analysis[
            "csv_data_rows"
        ] == 12846
        and analysis[
            "unique_valid_numeric_ocis"
        ] == 12846
        and analysis[
            "empty_oci_rows"
        ] == 0
        and analysis[
            "nonconforming_oci_rows"
        ] == 0
        and analysis[
            "duplicate_valid_oci_count"
        ] == 0
    ):
        return (
            "STABLE_COUNT_CSV_12846_UNIQUE_VALID"
        )

    if (
        pre_count == 12846
        and post_count == 12846
        and analysis[
            "csv_data_rows"
        ] == 12845
    ):
        return (
            "STABLE_COUNT_CSV_12845_ROWS"
        )

    if (
        pre_count == 12846
        and post_count == 12846
        and analysis[
            "csv_data_rows"
        ] == 12846
        and (
            analysis[
                "empty_oci_rows"
            ] > 0
            or analysis[
                "nonconforming_oci_rows"
            ] > 0
        )
    ):
        return (
            "STABLE_COUNT_NONCONFORMING_OCI"
        )

    return (
        "OTHER_UNRESOLVED"
    )


def write_csv_rows(
    path: Path,
    fieldnames: list[str],
    rows: list[
        dict[str, str]
    ],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
            lineterminator="\n",
            extrasaction="raise",
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


def write_single_column_tsv(
    path: Path,
    header: str,
    values: list[str],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        fh.write(
            f"{header}\n"
        )

        for value in values:
            fh.write(
                f"{value}\n"
            )


def run_diagnostic(
    *,
    output_root: Path,
    attempt05_archive: Path,
    token: str,
    opener: Callable[..., Any] = (
        urllib.request.urlopen
    ),
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    if output_root.exists():
        if any(
            output_root.iterdir()
        ):
            raise RuntimeError(
                "Diagnostic output directory already "
                "exists and is non-empty"
            )
    else:
        output_root.mkdir(
            parents=True,
        )

    attempt05_ocis = (
        load_attempt05_oci_union(
            attempt05_archive
        )
    )

    common_headers = {
        "User-Agent":
            "branchsnv-validation/"
            "experiment07-source-diagnostic",
    }

    if token:
        common_headers[
            "authorization"
        ] = token

    pre_headers = dict(
        common_headers
    )

    pre_headers[
        "Accept"
    ] = "application/json"

    pre_body, pre_meta = (
        fetch_bytes(
            citation_count_url(),
            headers=pre_headers,
            raw_path=(
                output_root
                / "count_pre.json"
            ),
            opener=opener,
            sleep_fn=sleep_fn,
        )
    )

    pre_count = (
        parse_count_body(
            pre_body
        )
    )

    csv_headers = dict(
        common_headers
    )

    csv_headers[
        "Accept"
    ] = "text/csv"

    csv_body, csv_meta = (
        fetch_bytes(
            citations_url(),
            headers=csv_headers,
            raw_path=(
                output_root
                / "citations_unfiltered.csv"
            ),
            opener=opener,
            sleep_fn=sleep_fn,
        )
    )

    (
        fieldnames,
        csv_rows,
    ) = parse_csv_body(
        csv_body
    )

    post_headers = dict(
        common_headers
    )

    post_headers[
        "Accept"
    ] = "application/json"

    post_body, post_meta = (
        fetch_bytes(
            citation_count_url(),
            headers=post_headers,
            raw_path=(
                output_root
                / "count_post.json"
            ),
            opener=opener,
            sleep_fn=sleep_fn,
        )
    )

    post_count = (
        parse_count_body(
            post_body
        )
    )

    analysis = analyse_csv_rows(
        csv_rows,
        attempt05_ocis=
            attempt05_ocis,
    )

    interpretation = (
        classify_result(
            pre_count=
                pre_count,
            post_count=
                post_count,
            analysis=
                analysis,
        )
    )

    write_csv_rows(
        output_root
        / "csv_only_rows.csv",
        fieldnames,
        analysis[
            "csv_only_rows"
        ],
    )

    write_csv_rows(
        output_root
        / "exceptional_oci_rows.csv",
        fieldnames,
        analysis[
            "exceptional_rows"
        ],
    )

    write_single_column_tsv(
        output_root
        / "csv_only_ocis.tsv",
        "oci",
        analysis[
            "csv_only_ocis"
        ],
    )

    write_single_column_tsv(
        output_root
        / "attempt05_only_ocis.tsv",
        "oci",
        analysis[
            "attempt05_only_ocis"
        ],
    )

    write_single_column_tsv(
        output_root
        / "duplicate_valid_ocis.tsv",
        "oci",
        analysis[
            "duplicate_valid_ocis"
        ],
    )

    summary = {
        "schema_version": 1,
        "status":
            "COMPLETE_DIAGNOSTIC",
        "scientific_screening":
            False,
        "production_corpus":
            False,
        "attempt_05_reclassified":
            False,
        "anchor_id":
            ANCHOR_ID,
        "anchor_tool":
            ANCHOR_TOOL,
        "anchor_doi":
            ANCHOR_DOI,
        "direction":
            "forward",
        "source":
            "OpenCitations Index v2",
        "request_sequence": [
            "citation-count-pre",
            "citations-unfiltered-csv",
            "citation-count-post",
        ],
        "pre_count":
            pre_count,
        "post_count":
            post_count,
        "bracketing_counts_equal":
            (
                pre_count
                == post_count
            ),
        "historical_attempt05_count":
            EXPECTED_ATTEMPT05_COUNT,
        "attempt05_unique_oci_count":
            len(
                attempt05_ocis
            ),
        "csv_data_rows":
            analysis[
                "csv_data_rows"
            ],
        "csv_empty_oci_rows":
            analysis[
                "empty_oci_rows"
            ],
        "csv_nonconforming_oci_rows":
            analysis[
                "nonconforming_oci_rows"
            ],
        "csv_valid_numeric_oci_rows":
            analysis[
                "valid_numeric_oci_rows"
            ],
        "csv_unique_valid_numeric_ocis":
            analysis[
                "unique_valid_numeric_ocis"
            ],
        "csv_duplicate_valid_oci_count":
            analysis[
                "duplicate_valid_oci_count"
            ],
        "csv_only_oci_count":
            analysis[
                "csv_only_oci_count"
            ],
        "attempt05_only_oci_count":
            analysis[
                "attempt05_only_oci_count"
            ],
        "interpretation_class":
            interpretation,
        "request_metadata": {
            "count_pre":
                pre_meta,
            "citations_csv":
                csv_meta,
            "count_post":
                post_meta,
        },
        "attempt05_archive_sha256":
            sha256_file(
                attempt05_archive
            ),
        "diagnostic_script_sha256":
            sha256_file(
                Path(
                    __file__
                )
            ),
        "git_head":
            git_head(),
        "completed_at_utc":
            utc_now(),
        "credential_values_written":
            False,
    }

    (
        output_root
        / "diagnostic_summary.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    checksum_files = sorted(
        path
        for path in (
            output_root
        ).iterdir()
        if (
            path.is_file()
            and path.name
            != "checksums.sha256"
        )
    )

    with (
        output_root
        / "checksums.sha256"
    ).open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        for path in checksum_files:
            fh.write(
                f"{sha256_file(path)}  "
                f"{path.name}\n"
            )

    return summary


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--attempt05-archive",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    token = os.environ.get(
        "OPENCITATIONS_ACCESS_TOKEN",
        "",
    ).strip()

    summary = run_diagnostic(
        output_root=args.output,
        attempt05_archive=
            args.attempt05_archive,
        token=token,
    )

    print(
        "PASS | diagnostic completed"
    )

    print(
        "PASS | pre-count =",
        summary["pre_count"],
    )

    print(
        "PASS | post-count =",
        summary["post_count"],
    )

    print(
        "PASS | CSV rows =",
        summary["csv_data_rows"],
    )

    print(
        "PASS | unique valid CSV OCIs =",
        summary[
            "csv_unique_valid_numeric_ocis"
        ],
    )

    print(
        "PASS | CSV-only OCIs =",
        summary[
            "csv_only_oci_count"
        ],
    )

    print(
        "PASS | Attempt-05-only OCIs =",
        summary[
            "attempt05_only_oci_count"
        ],
    )

    print(
        "PASS | interpretation =",
        summary[
            "interpretation_class"
        ],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
