#!/usr/bin/env python3
"""
OCI-independent OpenCitations source-forensic diagnostic.

Target:
    W0A07 / PAML / 10.1093/molbev/msm088 / forward citations

Frozen sequence:
    citation-count
    creation-string partitioned citations
    citation-count

This is NOT the Wave 0 production retriever.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
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

EXPECTED_ATTEMPT05_ROWS = 12845
EXPECTED_ATTEMPT05_OCI_COUNT = 12845
EXPECTED_ATTEMPT05_COUNT = 12846

EXPECTED_ATTEMPT05_ROW_MULTISET_SHA256 = (
    "82e2992dda9fe3f3d5a18cb417343edb"
    "47ba1af617832aec3b2f241d5500e928"
)

OCI_RE = re.compile(
    r"^[0-9]+-[0-9]+$"
)

MAX_PREFIX_CHARACTERS = 32
MAX_ATTEMPTS = 5
REQUEST_DELAY_SECONDS = 0.40
REQUEST_TIMEOUT_SECONDS = 180

LEAF_FIELDS = [
    "leaf_order",
    "recursion_depth",
    "partition_kind",
    "literal_prefix",
    "leaf_regex",
    "request_sha256",
    "raw_file",
    "row_count",
]


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


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


def sha256_bytes(
    value: bytes,
) -> str:
    return hashlib.sha256(
        value
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


def build_url(
    base: str,
    params: dict[str, str],
) -> str:
    return (
        base
        + "?"
        + urllib.parse.urlencode(
            params
        )
    )


def citation_count_url() -> str:
    identifier = urllib.parse.quote(
        f"doi:{ANCHOR_DOI}",
        safe=":",
    )

    return (
        f"{OPENCITATIONS_ROOT}/"
        f"citation-count/{identifier}"
    )


def citations_url(
    creation_regex: str,
) -> str:
    identifier = urllib.parse.quote(
        f"doi:{ANCHOR_DOI}",
        safe=":",
    )

    base = (
        f"{OPENCITATIONS_ROOT}/"
        f"citations/{identifier}"
    )

    return build_url(
        base,
        {
            "filter":
                f"creation:{creation_regex}",
        },
    )


def fetch_json(
    url: str,
    *,
    headers: dict[str, str],
    raw_path: Path,
    retries: int = MAX_ATTEMPTS,
    delay: float = REQUEST_DELAY_SECONDS,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
    opener: Callable[..., Any] = (
        urllib.request.urlopen
    ),
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[
    Any,
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
        if delay > 0:
            sleep_fn(
                delay
            )

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

                response_headers = getattr(
                    response,
                    "headers",
                    None,
                )

                content_type = ""

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

            payload = json.loads(
                body.decode(
                    "utf-8"
                )
            )

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
            UnicodeDecodeError,
            json.JSONDecodeError,
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
                payload,
                {
                    "url":
                        url,
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

    raise RuntimeError(
        "Diagnostic request failed after "
        f"{retries} attempts: {url}"
    ) from last_error


def caused_by_incomplete_read(
    exc: BaseException,
) -> bool:
    current: BaseException | None = exc
    seen: set[int] = set()

    while current is not None:
        identity = id(
            current
        )

        if identity in seen:
            break

        seen.add(
            identity
        )

        if isinstance(
            current,
            http.client.IncompleteRead,
        ):
            return True

        next_exc = current.__cause__

        if (
            next_exc is None
            and not current.__suppress_context__
        ):
            next_exc = current.__context__

        current = next_exc

    return False


def parse_count_payload(
    payload: Any,
) -> int:
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


def flatten_rows(
    payload: Any,
) -> list[dict[str, Any]]:
    if (
        isinstance(payload, list)
        and len(payload) == 1
        and isinstance(
            payload[0],
            list,
        )
    ):
        payload = payload[0]

    if not isinstance(
        payload,
        list,
    ):
        raise RuntimeError(
            "Unexpected OpenCitations citation-data shape"
        )

    rows: list[
        dict[str, Any]
    ] = []

    for item in payload:
        if not isinstance(
            item,
            dict,
        ):
            raise RuntimeError(
                "OpenCitations citation-data row is not an object"
            )

        rows.append(
            item
        )

    return rows


def canonical_row_signature(
    row: dict[str, Any],
) -> str:
    return json.dumps(
        row,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def load_attempt05_rows(
    archive_path: Path,
) -> tuple[
    list[dict[str, Any]],
    set[str],
]:
    marker = (
        "citation_wave_0/raw/opencitations/"
        "W0A07/forward_partitions/depth_00/"
        "digits_01_suffix_"
    )

    rows: list[
        dict[str, Any]
    ] = []

    suffixes: set[str] = set()

    with tarfile.open(
        archive_path,
        "r:gz",
    ) as tf:
        members = sorted(
            [
                member
                for member in tf.getmembers()
                if (
                    member.isfile()
                    and marker in member.name
                    and member.name.endswith(
                        ".json"
                    )
                )
            ],
            key=lambda member: member.name,
        )

        if len(members) != 10:
            raise RuntimeError(
                "Attempt-05 archive does not contain "
                "ten W0A07 forward root leaves"
            )

        for member in members:
            match = re.search(
                r"digits_01_suffix_([0-9])\.json$",
                member.name,
            )

            if match is None:
                raise RuntimeError(
                    "Unexpected Attempt-05 leaf name"
                )

            suffix = match.group(1)

            if suffix in suffixes:
                raise RuntimeError(
                    "Duplicate Attempt-05 suffix"
                )

            suffixes.add(
                suffix
            )

            fh = tf.extractfile(
                member
            )

            if fh is None:
                raise RuntimeError(
                    f"Cannot extract {member.name}"
                )

            payload = json.loads(
                fh.read().decode(
                    "utf-8"
                )
            )

            leaf_rows = flatten_rows(
                payload
            )

            for row in leaf_rows:
                oci = str(
                    row.get(
                        "oci"
                    )
                    or ""
                ).strip()

                if not OCI_RE.fullmatch(
                    oci
                ):
                    raise RuntimeError(
                        "Malformed Attempt-05 OCI"
                    )

                if (
                    oci.split(
                        "-",
                        1,
                    )[0][-1]
                    != suffix
                ):
                    raise RuntimeError(
                        "Attempt-05 OCI outside leaf"
                    )

                rows.append(
                    row
                )

    if suffixes != set(
        "0123456789"
    ):
        raise RuntimeError(
            "Attempt-05 suffix universe incomplete"
        )

    if (
        len(rows)
        != EXPECTED_ATTEMPT05_ROWS
    ):
        raise RuntimeError(
            "Attempt-05 row count mismatch"
        )

    signatures = [
        canonical_row_signature(
            row
        )
        for row in rows
    ]

    if len(signatures) != len(
        set(signatures)
    ):
        raise RuntimeError(
            "Attempt-05 complete-row duplication"
        )

    digest = hashlib.sha256(
        "\n".join(
            sorted(
                signatures
            )
        ).encode(
            "utf-8"
        )
    ).hexdigest()

    if (
        digest
        != EXPECTED_ATTEMPT05_ROW_MULTISET_SHA256
    ):
        raise RuntimeError(
            "Attempt-05 complete-row identity mismatch"
        )

    ocis = {
        str(
            row.get("oci")
            or ""
        ).strip()
        for row in rows
    }

    if (
        len(ocis)
        != EXPECTED_ATTEMPT05_OCI_COUNT
    ):
        raise RuntimeError(
            "Attempt-05 OCI identity mismatch"
        )

    return (
        rows,
        ocis,
    )


def root_leaves() -> list[
    dict[str, Any]
]:
    result = [
        {
            "kind":
                "empty",
            "prefix":
                "",
            "regex":
                r"^$",
            "depth":
                0,
            "subdividable":
                False,
        },
        {
            "kind":
                "non_digit",
            "prefix":
                "",
            "regex":
                r"^[^0-9].*$",
            "depth":
                0,
            "subdividable":
                False,
        },
    ]

    for digit in (
        "0123456789"
    ):
        result.append({
            "kind":
                "prefix",
            "prefix":
                digit,
            "regex":
                rf"^{re.escape(digit)}.*$",
            "depth":
                0,
            "subdividable":
                True,
        })

    return result


def prefix_children(
    prefix: str,
    *,
    depth: int,
) -> list[
    dict[str, Any]
]:
    if not prefix:
        raise ValueError(
            "Cannot subdivide empty literal prefix"
        )

    children: list[
        dict[str, Any]
    ] = [
        {
            "kind":
                "exact",
            "prefix":
                prefix,
            "regex":
                rf"^{re.escape(prefix)}$",
            "depth":
                depth,
            "subdividable":
                False,
        },
    ]

    for digit in (
        "0123456789"
    ):
        child_prefix = (
            prefix
            + digit
        )

        children.append({
            "kind":
                "prefix",
            "prefix":
                child_prefix,
            "regex":
                rf"^{re.escape(child_prefix)}.*$",
            "depth":
                depth,
            "subdividable":
                True,
        })

    hyphen_prefix = (
        prefix
        + "-"
    )

    children.append({
        "kind":
            "prefix",
        "prefix":
            hyphen_prefix,
        "regex":
            rf"^{re.escape(hyphen_prefix)}.*$",
        "depth":
            depth,
        "subdividable":
            True,
    })

    children.append({
        "kind":
            "other",
        "prefix":
            prefix,
        "regex":
            (
                rf"^{re.escape(prefix)}"
                r"[^0-9-].*$"
            ),
        "depth":
            depth,
        "subdividable":
            False,
    })

    return children


def safe_prefix_name(
    value: str,
) -> str:
    if not value:
        return "EMPTY"

    return (
        value.replace(
            "-",
            "H",
        )
    )


def leaf_raw_path(
    raw_root: Path,
    leaf: dict[str, Any],
) -> Path:
    kind = str(
        leaf["kind"]
    )

    prefix = safe_prefix_name(
        str(
            leaf["prefix"]
        )
    )

    depth = int(
        leaf["depth"]
    )

    return (
        raw_root
        / f"depth_{depth:02d}"
        / f"{kind}_{prefix}.json"
    )


def validate_leaf_rows(
    payload: Any,
    *,
    leaf_regex: str,
) -> list[
    dict[str, Any]
]:
    rows = flatten_rows(
        payload
    )

    rx = re.compile(
        leaf_regex
    )

    for row in rows:
        if "creation" not in row:
            raise RuntimeError(
                "OpenCitations row lacks creation field"
            )

        creation = row[
            "creation"
        ]

        if not isinstance(
            creation,
            str,
        ):
            raise RuntimeError(
                "OpenCitations creation field is not a string"
            )

        if not rx.fullmatch(
            creation
        ):
            raise RuntimeError(
                "OpenCitations creation value does not "
                "belong to its partition leaf"
            )

    return rows


def validate_unique_complete_rows(
    records: list[
        tuple[
            dict[str, Any],
            Path,
        ]
    ],
) -> None:
    observed: dict[
        str,
        Path,
    ] = {}

    for row, raw_path in records:
        signature = (
            canonical_row_signature(
                row
            )
        )

        if signature in observed:
            raise RuntimeError(
                "Duplicate complete citation row across "
                "creation partitions"
            )

        observed[
            signature
        ] = raw_path


def retrieve_creation_partitioned(
    *,
    output_root: Path,
    headers: dict[str, str],
    fetcher: Callable[..., Any] = fetch_json,
    max_prefix_characters: int = (
        MAX_PREFIX_CHARACTERS
    ),
) -> tuple[
    list[
        tuple[
            dict[str, Any],
            Path,
        ]
    ],
    list[
        dict[str, Any]
    ],
]:
    raw_root = (
        output_root
        / "raw"
        / "creation_partitions"
    )

    records: list[
        tuple[
            dict[str, Any],
            Path,
        ]
    ] = []

    accepted_leaves: list[
        dict[str, Any]
    ] = []

    leaf_order = 0

    def retrieve_leaf(
        leaf: dict[str, Any],
    ) -> None:
        nonlocal leaf_order

        regex = str(
            leaf["regex"]
        )

        raw_path = (
            leaf_raw_path(
                raw_root,
                leaf,
            )
        )

        url = citations_url(
            regex
        )

        try:
            (
                payload,
                request_meta,
            ) = fetcher(
                url,
                headers=headers,
                raw_path=raw_path,
                delay=
                    REQUEST_DELAY_SECONDS,
            )

        except RuntimeError as exc:
            if (
                bool(
                    leaf[
                        "subdividable"
                    ]
                )
                and caused_by_incomplete_read(
                    exc
                )
            ):
                prefix = str(
                    leaf[
                        "prefix"
                    ]
                )

                if (
                    len(prefix)
                    >= max_prefix_characters
                ):
                    raise RuntimeError(
                        "Creation partition recursion "
                        "ceiling reached at "
                        f"{len(prefix)} prefix characters"
                    ) from exc

                for child in (
                    prefix_children(
                        prefix,
                        depth=(
                            int(
                                leaf[
                                    "depth"
                                ]
                            )
                            + 1
                        ),
                    )
                ):
                    retrieve_leaf(
                        child
                    )

                return

            raise

        rows = (
            validate_leaf_rows(
                payload,
                leaf_regex=regex,
            )
        )

        leaf_order += 1

        accepted_leaves.append({
            "leaf_order":
                leaf_order,
            "recursion_depth":
                int(
                    leaf[
                        "depth"
                    ]
                ),
            "partition_kind":
                str(
                    leaf[
                        "kind"
                    ]
                ),
            "literal_prefix":
                str(
                    leaf[
                        "prefix"
                    ]
                ),
            "leaf_regex":
                regex,
            "request_sha256":
                hashlib.sha256(
                    url.encode(
                        "utf-8"
                    )
                ).hexdigest(),
            "raw_file":
                str(
                    raw_path.relative_to(
                        output_root
                    )
                ),
            "row_count":
                len(rows),
        })

        for row in rows:
            records.append(
                (
                    row,
                    raw_path,
                )
            )

    for leaf in root_leaves():
        retrieve_leaf(
            leaf
        )

    validate_unique_complete_rows(
        records
    )

    return (
        records,
        accepted_leaves,
    )


def analyse_oci(
    rows: list[
        dict[str, Any]
    ],
    *,
    attempt05_ocis: set[str],
) -> dict[str, Any]:
    empty_rows: list[
        dict[str, Any]
    ] = []

    nonconforming_rows: list[
        dict[str, Any]
    ] = []

    valid_rows: list[
        dict[str, Any]
    ] = []

    counts: Counter[str] = (
        Counter()
    )

    for row in rows:
        value = row.get(
            "oci"
        )

        oci = str(
            value
            if value is not None
            else ""
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

        counts[
            oci
        ] += 1

    valid_set = set(
        counts
    )

    duplicate_ocis = sorted(
        oci
        for oci, n
        in counts.items()
        if n > 1
    )

    creation_only = sorted(
        valid_set
        - attempt05_ocis
    )

    attempt05_only = sorted(
        attempt05_ocis
        - valid_set
    )

    creation_only_set = set(
        creation_only
    )

    creation_only_rows = [
        row
        for row in valid_rows
        if str(
            row.get("oci")
            or ""
        ).strip()
        in creation_only_set
    ]

    return {
        "empty_oci_rows":
            len(
                empty_rows
            ),
        "nonconforming_oci_rows":
            len(
                nonconforming_rows
            ),
        "valid_numeric_oci_rows":
            len(
                valid_rows
            ),
        "unique_valid_numeric_ocis":
            len(
                valid_set
            ),
        "duplicate_valid_oci_count":
            len(
                duplicate_ocis
            ),
        "duplicate_valid_ocis":
            duplicate_ocis,
        "creation_only_oci_count":
            len(
                creation_only
            ),
        "attempt05_only_oci_count":
            len(
                attempt05_only
            ),
        "creation_only_ocis":
            creation_only,
        "attempt05_only_ocis":
            attempt05_only,
        "creation_only_rows":
            creation_only_rows,
        "exceptional_oci_rows":
            (
                empty_rows
                + nonconforming_rows
            ),
    }


def classify_result(
    *,
    pre_count: int,
    post_count: int,
    row_count: int,
) -> str:
    if (
        pre_count
        != post_count
    ):
        return (
            "COUNT_CHANGED_DURING_INTERVAL"
        )

    if (
        pre_count == 12846
        and row_count == 12846
    ):
        return (
            "STABLE_12846_COUNT_AND_12846_CREATION_ROWS"
        )

    if (
        pre_count == 12846
        and row_count == 12845
    ):
        return (
            "STABLE_12846_COUNT_AND_12845_CREATION_ROWS"
        )

    if (
        row_count
        == pre_count
    ):
        return (
            "STABLE_COUNT_RECONCILED_OTHER_VALUE"
        )

    return (
        "STABLE_COUNT_CREATION_ROW_MISMATCH_OTHER"
    )


def write_tsv(
    path: Path,
    fields: list[str],
    rows: list[
        dict[str, Any]
    ],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


def write_values(
    path: Path,
    values: list[str],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        fh.write(
            "oci\n"
        )

        for value in values:
            fh.write(
                f"{value}\n"
            )


def write_jsonl(
    path: Path,
    rows: list[
        dict[str, Any]
    ],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        for row in rows:
            fh.write(
                json.dumps(
                    row,
                    sort_keys=True,
                    ensure_ascii=False,
                )
                + "\n"
            )


def run_diagnostic(
    *,
    output_root: Path,
    attempt05_archive: Path,
    token: str,
    fetcher: Callable[..., Any] = fetch_json,
) -> dict[str, Any]:
    if output_root.exists():
        if any(
            output_root.iterdir()
        ):
            raise RuntimeError(
                "Diagnostic-02 output directory "
                "already exists and is non-empty"
            )
    else:
        output_root.mkdir(
            parents=True
        )

    (
        attempt05_rows,
        attempt05_ocis,
    ) = load_attempt05_rows(
        attempt05_archive
    )

    headers = {
        "Accept":
            "application/json",
        "User-Agent":
            "branchsnv-validation/"
            "experiment07-creation-diagnostic",
    }

    if token:
        headers[
            "authorization"
        ] = token

    (
        pre_payload,
        pre_meta,
    ) = fetcher(
        citation_count_url(),
        headers=headers,
        raw_path=(
            output_root
            / "count_pre.json"
        ),
        delay=
            REQUEST_DELAY_SECONDS,
    )

    pre_count = (
        parse_count_payload(
            pre_payload
        )
    )

    (
        records,
        leaves,
    ) = retrieve_creation_partitioned(
        output_root=
            output_root,
        headers=
            headers,
        fetcher=
            fetcher,
    )

    (
        post_payload,
        post_meta,
    ) = fetcher(
        citation_count_url(),
        headers=headers,
        raw_path=(
            output_root
            / "count_post.json"
        ),
        delay=
            REQUEST_DELAY_SECONDS,
    )

    post_count = (
        parse_count_payload(
            post_payload
        )
    )

    rows = [
        row
        for row, _
        in records
    ]

    analysis = analyse_oci(
        rows,
        attempt05_ocis=
            attempt05_ocis,
    )

    interpretation = (
        classify_result(
            pre_count=
                pre_count,
            post_count=
                post_count,
            row_count=
                len(rows),
        )
    )

    write_tsv(
        output_root
        / "creation_partition_leaves.tsv",
        LEAF_FIELDS,
        leaves,
    )

    write_values(
        output_root
        / "creation_only_ocis.tsv",
        analysis[
            "creation_only_ocis"
        ],
    )

    write_values(
        output_root
        / "attempt05_only_ocis.tsv",
        analysis[
            "attempt05_only_ocis"
        ],
    )

    write_values(
        output_root
        / "duplicate_valid_ocis.tsv",
        analysis[
            "duplicate_valid_ocis"
        ],
    )

    write_jsonl(
        output_root
        / "creation_only_rows.jsonl",
        analysis[
            "creation_only_rows"
        ],
    )

    write_jsonl(
        output_root
        / "exceptional_oci_rows.jsonl",
        analysis[
            "exceptional_oci_rows"
        ],
    )

    creation_counts = Counter(
        row["creation"]
        for row in rows
    )

    with (
        output_root
        / "creation_value_counts.tsv"
    ).open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        fh.write(
            "creation\trow_count\n"
        )

        for value, n in sorted(
            creation_counts.items()
        ):
            fh.write(
                f"{value}\t{n}\n"
            )

    max_depth = max(
        (
            int(
                leaf[
                    "recursion_depth"
                ]
            )
            for leaf in leaves
        ),
        default=0,
    )

    summary = {
        "schema_version": 1,
        "status":
            "COMPLETE_DIAGNOSTIC",
        "production_corpus":
            False,
        "scientific_screening":
            False,
        "attempt_05_reclassified":
            False,
        "partition_field":
            "creation",
        "partition_uses_oci":
            False,
        "anchor_id":
            ANCHOR_ID,
        "anchor_tool":
            ANCHOR_TOOL,
        "anchor_doi":
            ANCHOR_DOI,
        "pre_count":
            pre_count,
        "post_count":
            post_count,
        "bracketing_counts_equal":
            (
                pre_count
                == post_count
            ),
        "creation_partition_rows":
            len(rows),
        "unique_complete_rows":
            len({
                canonical_row_signature(
                    row
                )
                for row in rows
            }),
        "partition_leaf_count":
            len(leaves),
        "max_recursion_depth":
            max_depth,
        "empty_oci_rows":
            analysis[
                "empty_oci_rows"
            ],
        "nonconforming_oci_rows":
            analysis[
                "nonconforming_oci_rows"
            ],
        "valid_numeric_oci_rows":
            analysis[
                "valid_numeric_oci_rows"
            ],
        "unique_valid_numeric_ocis":
            analysis[
                "unique_valid_numeric_ocis"
            ],
        "duplicate_valid_oci_count":
            analysis[
                "duplicate_valid_oci_count"
            ],
        "creation_only_oci_count":
            analysis[
                "creation_only_oci_count"
            ],
        "attempt05_only_oci_count":
            analysis[
                "attempt05_only_oci_count"
            ],
        "attempt05_rows":
            len(
                attempt05_rows
            ),
        "attempt05_unique_ocis":
            len(
                attempt05_ocis
            ),
        "interpretation_class":
            interpretation,
        "request_metadata": {
            "count_pre":
                pre_meta,
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

    files = sorted(
        path
        for path in output_root.rglob("*")
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
        for path in files:
            fh.write(
                f"{sha256_file(path)}  "
                f"{path.relative_to(output_root)}\n"
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
        output_root=
            args.output,
        attempt05_archive=
            args.attempt05_archive,
        token=
            token,
    )

    print(
        "PASS | Diagnostic-02 completed"
    )

    for key in [
        "pre_count",
        "post_count",
        "creation_partition_rows",
        "unique_complete_rows",
        "partition_leaf_count",
        "max_recursion_depth",
        "empty_oci_rows",
        "nonconforming_oci_rows",
        "unique_valid_numeric_ocis",
        "duplicate_valid_oci_count",
        "creation_only_oci_count",
        "attempt05_only_oci_count",
        "interpretation_class",
    ]:
        print(
            f"{key} = "
            f"{summary[key]}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
