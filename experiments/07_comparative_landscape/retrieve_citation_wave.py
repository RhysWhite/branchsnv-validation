#!/usr/bin/env python3
"""
Retrieve one frozen Experiment 07 citation-chaining wave.

Sources
-------
1. OpenAlex Works
2. OpenCitations Index v2

Important
---------
This program performs discovery only. It applies no scientific keyword,
citation-count, date, language, or publication-type filter.

It is designed to fail closed when a retrieval cannot be demonstrated to be
complete.

OpenAlex:
- anchors are resolved by DOI;
- backward edges come from the anchor Work's referenced_works array;
- forward neighbours are retrieved with the `cites:<anchor Work ID>` filter
  using cursor pagination.

OpenCitations:
- backward edges use /references/doi:<DOI>;
- forward edges use /citations/doi:<DOI>.

API credentials are read only from environment variables and are never
written to output files.
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
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


OPENALEX_ROOT = "https://api.openalex.org"
OPENCITATIONS_ROOT = "https://api.opencitations.net/index/v2"

OPENCITATIONS_PARTITION_DIGITS = "0123456789"
OPENCITATIONS_OCI_PATTERN = r"^[0-9]+-[0-9]+$"
OPENCITATIONS_PARTITION_MAX_SUFFIX_DIGITS = 64

OPENALEX_SELECT_SINGLE = ",".join([
    "id",
    "doi",
    "title",
    "display_name",
    "publication_year",
    "ids",
    "referenced_works",
    "referenced_works_count",
    "cited_by_count",
])

OPENALEX_SELECT_LIST = ",".join([
    "id",
    "doi",
    "title",
    "display_name",
    "publication_year",
    "ids",
])

EDGE_FIELDS = [
    "wave",
    "anchor_id",
    "anchor_tool",
    "source",
    "direction",
    "anchor_doi",
    "anchor_openalex_id",
    "citing_dois",
    "cited_dois",
    "citing_pmids",
    "cited_pmids",
    "citing_openalex_ids",
    "cited_openalex_ids",
    "citing_omids",
    "cited_omids",
    "oci",
    "raw_file",
]

NEIGHBOUR_FIELDS = [
    "wave",
    "anchor_id",
    "anchor_tool",
    "source",
    "direction",
    "doi",
    "pmid",
    "openalex_id",
    "omid",
    "title",
    "year",
    "source_record_id",
]

STATUS_FIELDS = [
    "wave",
    "anchor_id",
    "anchor_tool",
    "source",
    "direction",
    "status",
    "reported_count",
    "retrieved_count",
    "response_files",
    "terminal_detail",
]


OPENCITATIONS_PARTITION_FIELDS = [
    "wave",
    "anchor_id",
    "anchor_tool",
    "direction",
    "leaf_order",
    "recursion_depth",
    "suffix_digits",
    "partition_kind",
    "suffix",
    "leaf_regex",
    "request_sha256",
    "raw_file",
    "row_count",
]

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalise_doi(value: str | None) -> str:
    if not value:
        return ""

    value = str(value).strip()

    value = re.sub(
        r"^https?://(?:dx\.)?doi\.org/",
        "",
        value,
        flags=re.I,
    )

    value = re.sub(
        r"^doi:",
        "",
        value,
        flags=re.I,
    )

    return value.strip().lower()


def normalise_pmid(value: str | None) -> str:
    if not value:
        return ""

    value = str(value).strip()

    value = re.sub(
        r"^https?://pubmed\.ncbi\.nlm\.nih\.gov/",
        "",
        value,
        flags=re.I,
    )

    value = re.sub(
        r"^pmid:",
        "",
        value,
        flags=re.I,
    )

    match = re.search(r"(\d+)", value)
    return match.group(1) if match else value


def normalise_openalex_id(value: str | None) -> str:
    if not value:
        return ""

    value = str(value).strip()

    match = re.search(
        r"(?:https?://openalex\.org/)?(W\d+)$",
        value,
        flags=re.I,
    )

    if not match:
        return value

    return match.group(1).upper()


def normalise_omid(value: str | None) -> str:
    if not value:
        return ""

    value = str(value).strip().lower()

    if value.startswith("omid:"):
        value = value[5:]

    return value


def first_nonempty(values: list[str]) -> str:
    for value in values:
        if value:
            return value
    return ""


def unique_join(values: list[str]) -> str:
    return ";".join(sorted({
        v
        for v in values
        if v
    }))


def parse_pid_bundle(value: str | None) -> dict[str, list[str]]:
    """
    Extract DOI, PMID and OMID identifiers from an OpenCitations PID bundle.

    Handles strings such as:
      omid:br/061... doi:10.x/foo pmid:1234
    and source-prefixed variants such as:
      [oci] => omid:... doi:...
    """

    text = str(value or "")

    doi_matches = re.findall(
        r"(?i)\bdoi:([^\s;,\]]+)",
        text,
    )

    pmid_matches = re.findall(
        r"(?i)\bpmid:(\d+)",
        text,
    )

    omid_matches = re.findall(
        r"(?i)\bomid:([^\s;,\]]+)",
        text,
    )

    return {
        "doi": sorted({
            normalise_doi(v)
            for v in doi_matches
            if normalise_doi(v)
        }),
        "pmid": sorted({
            normalise_pmid(v)
            for v in pmid_matches
            if normalise_pmid(v)
        }),
        "omid": sorted({
            normalise_omid(v)
            for v in omid_matches
            if normalise_omid(v)
        }),
    }


def flatten_json_list(payload: Any) -> list[dict]:
    """
    OpenCitations normally returns a list of objects.

    Accept one accidental/documented extra list layer as well, but reject any
    other shape.
    """

    if not isinstance(payload, list):
        raise RuntimeError(
            "Expected JSON list payload"
        )

    if (
        len(payload) == 1
        and isinstance(payload[0], list)
    ):
        payload = payload[0]

    if not all(
        isinstance(item, dict)
        for item in payload
    ):
        raise RuntimeError(
            "Expected list of JSON objects"
        )

    return list(payload)


def parse_opencitations_count(
    payload: Any,
) -> int:
    """Parse one OpenCitations count-endpoint response."""

    rows = flatten_json_list(
        payload
    )

    if len(rows) != 1:
        raise RuntimeError(
            "OpenCitations count endpoint "
            f"returned {len(rows)} rows; expected 1"
        )

    if "count" not in rows[0]:
        raise RuntimeError(
            "OpenCitations count response "
            "does not contain 'count'"
        )

    try:
        count = int(
            rows[0]["count"]
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            "OpenCitations count is not an integer"
        ) from exc

    if count < 0:
        raise RuntimeError(
            "OpenCitations count is negative"
        )

    return count



def build_url(
    base: str,
    params: dict[str, str | int],
) -> str:
    return (
        base
        + "?"
        + urllib.parse.urlencode(params)
    )


def raw_rel(path: Path, root: Path) -> str:
    return str(
        path.relative_to(root)
    )


class NotIndexed(Exception):
    pass


def fetch_json(
    url: str,
    *,
    headers: dict[str, str],
    raw_path: Path,
    delay: float,
    retries: int = 5,
) -> Any:
    raw_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            url,
            headers=headers,
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=60,
            ) as response:
                data = response.read()

            raw_path.write_bytes(data)

            if delay:
                time.sleep(delay)

            return json.loads(
                data.decode("utf-8")
            )

        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise NotIndexed(
                    f"HTTP 404 for {url}"
                ) from exc

            last_error = exc

            if exc.code not in {
                408,
                429,
                500,
                502,
                503,
                504,
            }:
                raise

        except (
            urllib.error.URLError,
            TimeoutError,
            http.client.IncompleteRead,
            json.JSONDecodeError,
        ) as exc:
            last_error = exc

        if attempt < retries:
            time.sleep(min(
                2 ** (attempt - 1),
                30,
            ))

    raise RuntimeError(
        f"Request failed after {retries} attempts: {url}"
    ) from last_error


def read_anchors(
    path: Path,
    wave: int,
) -> list[dict[str, str]]:
    with path.open(
        newline="",
        encoding="utf-8",
    ) as fh:
        reader = csv.DictReader(
            fh,
            delimiter="\t",
        )
        rows = list(reader)

    required = {
        "wave",
        "anchor_id",
        "tool",
        "confirmed_role",
        "canonical_identifier_type",
        "canonical_identifier",
        "canonical_title",
        "canonical_year",
        "anchor_evidence",
        "anchor_origin",
        "retrieval_status",
    }

    if not required.issubset(
        set(reader.fieldnames or [])
    ):
        raise RuntimeError(
            "Unexpected anchor-table schema"
        )

    selected = [
        row
        for row in rows
        if int(row["wave"]) == wave
    ]

    if not selected:
        raise RuntimeError(
            f"No anchors found for wave {wave}"
        )

    ids = [
        row["anchor_id"]
        for row in selected
    ]

    if len(ids) != len(set(ids)):
        raise RuntimeError(
            "Duplicate anchor_id"
        )

    for row in selected:
        if (
            row["canonical_identifier_type"]
            != "doi"
        ):
            raise RuntimeError(
                f"{row['anchor_id']}: "
                "current implementation requires DOI anchors"
            )

        if row["retrieval_status"] != "pending":
            raise RuntimeError(
                f"{row['anchor_id']}: "
                "anchor is not pending"
            )

    return selected


def write_tsv(
    path: Path,
    fields: list[str],
    rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


def openalex_single_url(
    doi: str,
) -> str:
    external_id = urllib.parse.quote(
        f"doi:{normalise_doi(doi)}",
        safe=":",
    )

    return build_url(
        f"{OPENALEX_ROOT}/works/{external_id}",
        {
            "select": OPENALEX_SELECT_SINGLE,
        },
    )


def openalex_forward_url(
    work_id: str,
    cursor: str,
) -> str:
    work_id = normalise_openalex_id(
        work_id
    )

    return build_url(
        f"{OPENALEX_ROOT}/works",
        {
            "filter": f"cites:{work_id}",
            "per-page": 100,
            "cursor": cursor,
            "select": OPENALEX_SELECT_LIST,
        },
    )



def opencitations_url(
    direction: str,
    doi: str,
    *,
    oci_filter: str | None = None,
) -> str:
    if direction not in {
        "backward",
        "forward",
    }:
        raise ValueError(
            f"Invalid direction: {direction}"
        )

    operation = (
        "references"
        if direction == "backward"
        else "citations"
    )

    identifier = urllib.parse.quote(
        f"doi:{normalise_doi(doi)}",
        safe=":",
    )

    base = (
        f"{OPENCITATIONS_ROOT}/"
        f"{operation}/{identifier}"
    )

    if oci_filter is None:
        return base

    if not oci_filter:
        raise ValueError(
            "OpenCitations OCI filter cannot be empty"
        )

    return build_url(
        base,
        {
            "filter":
                f"oci:{oci_filter}",
        },
    )


def opencitations_count_url(
    direction: str,
    doi: str,
) -> str:
    if direction not in {
        "backward",
        "forward",
    }:
        raise ValueError(
            f"Invalid direction: {direction}"
        )

    operation = (
        "reference-count"
        if direction == "backward"
        else "citation-count"
    )

    identifier = urllib.parse.quote(
        f"doi:{normalise_doi(doi)}",
        safe=":",
    )

    return (
        f"{OPENCITATIONS_ROOT}/"
        f"{operation}/{identifier}"
    )



def openalex_ids(
    item: dict,
) -> tuple[str, str, str]:
    ids = item.get("ids") or {}

    if not isinstance(ids, dict):
        ids = {}

    doi = normalise_doi(
        item.get("doi")
        or ids.get("doi")
    )

    pmid = normalise_pmid(
        ids.get("pmid")
    )

    oid = normalise_openalex_id(
        item.get("id")
        or ids.get("openalex")
    )

    return doi, pmid, oid


def retrieve_openalex(
    anchor: dict[str, str],
    *,
    wave: int,
    api_key: str,
    output_root: Path,
    fetcher: Callable[..., Any] = fetch_json,
) -> tuple[
    list[dict],
    list[dict],
    list[dict],
]:
    raw_root = (
        output_root
        / "raw"
        / "openalex"
        / anchor["anchor_id"]
    )

    doi = normalise_doi(
        anchor["canonical_identifier"]
    )

    resolution_path = (
        raw_root
        / "resolve_anchor.json"
    )

    try:
        work = fetcher(
            openalex_single_url(
                doi,
            ),
            headers={
                "Authorization":
                    f"Bearer {api_key}",
                "User-Agent":
                    "branchsnv-validation/experiment07",
            },
            raw_path=resolution_path,
            delay=0.12,
        )
    except NotIndexed:
        statuses = []

        for direction in [
            "backward",
            "forward",
        ]:
            statuses.append({
                "wave": wave,
                "anchor_id":
                    anchor["anchor_id"],
                "anchor_tool":
                    anchor["tool"],
                "source": "openalex",
                "direction": direction,
                "status": "not_indexed",
                "reported_count": 0,
                "retrieved_count": 0,
                "response_files": 1,
                "terminal_detail":
                    "anchor DOI returned HTTP 404",
            })

        return [], [], statuses

    if not isinstance(work, dict):
        raise RuntimeError(
            f"{anchor['anchor_id']}: "
            "OpenAlex resolution did not return an object"
        )

    resolved_doi, _, work_id = (
        openalex_ids(work)
    )

    if not work_id:
        raise RuntimeError(
            f"{anchor['anchor_id']}: "
            "resolved OpenAlex Work lacks Work ID"
        )

    if (
        resolved_doi
        and resolved_doi != doi
    ):
        raise RuntimeError(
            f"{anchor['anchor_id']}: "
            f"OpenAlex DOI mismatch "
            f"{resolved_doi!r} != {doi!r}"
        )

    edges: list[dict] = []
    neighbours: list[dict] = []
    statuses: list[dict] = []

    # ------------------------------------------------------
    # Backward citations.
    # ------------------------------------------------------

    refs = work.get(
        "referenced_works"
    ) or []

    if not isinstance(refs, list):
        raise RuntimeError(
            f"{anchor['anchor_id']}: "
            "referenced_works is not a list"
        )

    refs = [
        normalise_openalex_id(v)
        for v in refs
        if normalise_openalex_id(v)
    ]

    if len(refs) != len(set(refs)):
        raise RuntimeError(
            f"{anchor['anchor_id']}: "
            "duplicate OpenAlex referenced_works IDs"
        )

    reported_refs = int(
        work.get(
            "referenced_works_count",
            len(refs),
        )
        or 0
    )

    if reported_refs != len(refs):
        raise RuntimeError(
            f"{anchor['anchor_id']}: "
            f"OpenAlex referenced_works_count="
            f"{reported_refs}, array={len(refs)}"
        )

    for cited_id in sorted(refs):
        edges.append({
            "wave": wave,
            "anchor_id":
                anchor["anchor_id"],
            "anchor_tool":
                anchor["tool"],
            "source": "openalex",
            "direction": "backward",
            "anchor_doi": doi,
            "anchor_openalex_id":
                work_id,
            "citing_dois": doi,
            "cited_dois": "",
            "citing_pmids": "",
            "cited_pmids": "",
            "citing_openalex_ids":
                work_id,
            "cited_openalex_ids":
                cited_id,
            "citing_omids": "",
            "cited_omids": "",
            "oci": "",
            "raw_file": raw_rel(
                resolution_path,
                output_root,
            ),
        })

        neighbours.append({
            "wave": wave,
            "anchor_id":
                anchor["anchor_id"],
            "anchor_tool":
                anchor["tool"],
            "source": "openalex",
            "direction": "backward",
            "doi": "",
            "pmid": "",
            "openalex_id": cited_id,
            "omid": "",
            "title": "",
            "year": "",
            "source_record_id":
                cited_id,
        })

    statuses.append({
        "wave": wave,
        "anchor_id":
            anchor["anchor_id"],
        "anchor_tool":
            anchor["tool"],
        "source": "openalex",
        "direction": "backward",
        "status": (
            "complete"
            if refs
            else "resolved_zero_edges"
        ),
        "reported_count":
            reported_refs,
        "retrieved_count":
            len(refs),
        "response_files": 1,
        "terminal_detail":
            "resolved via referenced_works",
    })

    # ------------------------------------------------------
    # Forward citations.
    # ------------------------------------------------------

    cursor = "*"
    page_number = 0
    reported_forward: int | None = None
    forward_seen: set[str] = set()

    while cursor:
        page_number += 1

        page_path = (
            raw_root
            / (
                "forward_"
                f"page_{page_number:04d}.json"
            )
        )

        payload = fetcher(
            openalex_forward_url(
                work_id,
                cursor,
            ),
            headers={
                "Authorization":
                    f"Bearer {api_key}",
                "User-Agent":
                    "branchsnv-validation/experiment07",
            },
            raw_path=page_path,
            delay=0.12,
        )

        if not isinstance(payload, dict):
            raise RuntimeError(
                f"{anchor['anchor_id']}: "
                "invalid OpenAlex forward payload"
            )

        meta = payload.get("meta") or {}
        results = payload.get(
            "results"
        ) or []

        if not isinstance(
            results,
            list,
        ):
            raise RuntimeError(
                f"{anchor['anchor_id']}: "
                "OpenAlex results is not a list"
            )

        if reported_forward is None:
            reported_forward = int(
                meta.get(
                    "count",
                    0,
                )
                or 0
            )

        for item in results:
            if not isinstance(
                item,
                dict,
            ):
                raise RuntimeError(
                    f"{anchor['anchor_id']}: "
                    "OpenAlex result is not an object"
                )

            (
                citing_doi,
                citing_pmid,
                citing_id,
            ) = openalex_ids(item)

            if not citing_id:
                raise RuntimeError(
                    f"{anchor['anchor_id']}: "
                    "forward OpenAlex Work lacks ID"
                )

            if citing_id in forward_seen:
                raise RuntimeError(
                    f"{anchor['anchor_id']}: "
                    f"duplicate forward Work "
                    f"{citing_id}"
                )

            forward_seen.add(
                citing_id
            )

            edges.append({
                "wave": wave,
                "anchor_id":
                    anchor["anchor_id"],
                "anchor_tool":
                    anchor["tool"],
                "source": "openalex",
                "direction": "forward",
                "anchor_doi": doi,
                "anchor_openalex_id":
                    work_id,
                "citing_dois":
                    citing_doi,
                "cited_dois": doi,
                "citing_pmids":
                    citing_pmid,
                "cited_pmids": "",
                "citing_openalex_ids":
                    citing_id,
                "cited_openalex_ids":
                    work_id,
                "citing_omids": "",
                "cited_omids": "",
                "oci": "",
                "raw_file": raw_rel(
                    page_path,
                    output_root,
                ),
            })

            neighbours.append({
                "wave": wave,
                "anchor_id":
                    anchor["anchor_id"],
                "anchor_tool":
                    anchor["tool"],
                "source": "openalex",
                "direction": "forward",
                "doi": citing_doi,
                "pmid": citing_pmid,
                "openalex_id":
                    citing_id,
                "omid": "",
                "title": str(
                    item.get("title")
                    or item.get(
                        "display_name"
                    )
                    or ""
                ).strip(),
                "year": str(
                    item.get(
                        "publication_year"
                    )
                    or ""
                ),
                "source_record_id":
                    citing_id,
            })

        next_cursor = meta.get(
            "next_cursor"
        )

        if results and next_cursor:
            cursor = str(
                next_cursor
            )
        else:
            cursor = ""

    reported_forward = (
        reported_forward
        if reported_forward is not None
        else 0
    )

    if (
        len(forward_seen)
        != reported_forward
    ):
        raise RuntimeError(
            f"{anchor['anchor_id']}: "
            f"OpenAlex forward reported "
            f"{reported_forward}, retrieved "
            f"{len(forward_seen)}"
        )

    statuses.append({
        "wave": wave,
        "anchor_id":
            anchor["anchor_id"],
        "anchor_tool":
            anchor["tool"],
        "source": "openalex",
        "direction": "forward",
        "status": (
            "complete"
            if forward_seen
            else "resolved_zero_edges"
        ),
        "reported_count":
            reported_forward,
        "retrieved_count":
            len(forward_seen),
        "response_files":
            page_number,
        "terminal_detail":
            "cursor pagination complete",
    })

    return (
        edges,
        neighbours,
        statuses,
    )


def opencitations_partition_regex(
    direction: str,
    suffix: str,
    *,
    exact: bool,
) -> str:
    if direction not in {
        "backward",
        "forward",
    }:
        raise ValueError(
            f"Invalid direction: {direction}"
        )

    if (
        not suffix
        or any(
            digit not in OPENCITATIONS_PARTITION_DIGITS
            for digit in suffix
        )
    ):
        raise ValueError(
            f"Invalid OCI decimal suffix: {suffix!r}"
        )

    if direction == "forward":
        if exact:
            return (
                rf"^{suffix}-[0-9]+$"
            )

        return (
            rf"^[0-9]*{suffix}-[0-9]+$"
        )

    if exact:
        return (
            rf"^[0-9]+-{suffix}$"
        )

    return (
        rf"^[0-9]+-[0-9]*{suffix}$"
    )


def opencitations_partition_raw_path(
    raw_root: Path,
    direction: str,
    suffix: str,
    *,
    exact: bool,
    recursion_depth: int,
) -> Path:
    kind = (
        "exact"
        if exact
        else "suffix"
    )

    return (
        raw_root
        / f"{direction}_partitions"
        / f"depth_{recursion_depth:02d}"
        / (
            f"digits_{len(suffix):02d}_"
            f"{kind}_{suffix}.json"
        )
    )


def caused_by_incomplete_read(
    exc: BaseException,
) -> bool:
    current: BaseException | None = exc
    visited: set[int] = set()

    while current is not None:
        identity = id(current)

        if identity in visited:
            break

        visited.add(identity)

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


def validate_opencitations_partition_payload(
    payload: Any,
    *,
    leaf_regex: str,
    context: str,
) -> list[dict]:
    rows = flatten_json_list(
        payload
    )

    full_re = re.compile(
        OPENCITATIONS_OCI_PATTERN
    )

    leaf_re = re.compile(
        leaf_regex
    )

    for row in rows:
        oci = str(
            row.get("oci")
            or ""
        ).strip()

        if not oci:
            raise RuntimeError(
                f"{context}: OpenCitations row "
                "contains no OCI"
            )

        if not full_re.fullmatch(oci):
            raise RuntimeError(
                f"{context}: malformed OCI {oci!r}"
            )

        if not leaf_re.fullmatch(oci):
            raise RuntimeError(
                f"{context}: OCI {oci!r} "
                "does not belong to its partition leaf"
            )

    return rows


def reconcile_opencitations_partition_rows(
    records: list[
        tuple[
            dict,
            Path,
        ]
    ],
    *,
    expected_count: int,
    context: str,
) -> list[
    tuple[
        dict,
        Path,
    ]
]:
    seen: dict[
        str,
        Path,
    ] = {}

    for row, raw_path in records:
        oci = str(
            row.get("oci")
            or ""
        ).strip()

        if not oci:
            raise RuntimeError(
                f"{context}: OpenCitations row "
                "contains no OCI during reconciliation"
            )

        if oci in seen:
            raise RuntimeError(
                f"{context}: duplicate OCI {oci!r} "
                "across partition leaves"
            )

        seen[oci] = raw_path

    if len(seen) != expected_count:
        raise RuntimeError(
            f"{context}: OpenCitations reported "
            f"{expected_count}, retrieved "
            f"{len(seen)} unique OCI rows"
        )

    return sorted(
        records,
        key=lambda pair: str(
            pair[0].get("oci")
            or ""
        ),
    )


def retrieve_opencitations_partitioned(
    *,
    anchor: dict[str, str],
    direction: str,
    doi: str,
    expected_count: int,
    wave: int,
    headers: dict[str, str],
    raw_root: Path,
    output_root: Path,
    fetcher: Callable[..., Any],
    max_suffix_digits: int = (
        OPENCITATIONS_PARTITION_MAX_SUFFIX_DIGITS
    ),
) -> tuple[
    list[
        tuple[
            dict,
            Path,
        ]
    ],
    list[dict],
]:
    if expected_count < 0:
        raise ValueError(
            "expected_count cannot be negative"
        )

    if max_suffix_digits < 1:
        raise ValueError(
            "max_suffix_digits must be positive"
        )

    if expected_count == 0:
        return [], []

    context = (
        f"{anchor['anchor_id']}: "
        f"OpenCitations {direction}"
    )

    records: list[
        tuple[
            dict,
            Path,
        ]
    ] = []

    leaves: list[dict] = []

    leaf_order = 0

    def retrieve_leaf(
        suffix: str,
        *,
        exact: bool,
        recursion_depth: int,
    ) -> None:
        nonlocal leaf_order

        leaf_regex = (
            opencitations_partition_regex(
                direction,
                suffix,
                exact=exact,
            )
        )

        raw_path = (
            opencitations_partition_raw_path(
                raw_root,
                direction,
                suffix,
                exact=exact,
                recursion_depth=recursion_depth,
            )
        )

        request_url = (
            opencitations_url(
                direction,
                doi,
                oci_filter=leaf_regex,
            )
        )

        try:
            payload = fetcher(
                request_url,
                headers=headers,
                raw_path=raw_path,
                delay=0.40,
            )

        except NotIndexed as exc:
            raise RuntimeError(
                f"{context}: independent count "
                "endpoint resolved the anchor but "
                "a filtered citation-data request "
                "returned HTTP 404"
            ) from exc

        except RuntimeError as exc:
            if (
                not exact
                and caused_by_incomplete_read(exc)
            ):
                if (
                    len(suffix)
                    >= max_suffix_digits
                ):
                    raise RuntimeError(
                        f"{context}: OCI partition "
                        "recursion ceiling reached at "
                        f"{len(suffix)} suffix digits "
                        f"for suffix {suffix!r}"
                    ) from exc

                retrieve_leaf(
                    suffix,
                    exact=True,
                    recursion_depth=(
                        recursion_depth + 1
                    ),
                )

                for digit in (
                    OPENCITATIONS_PARTITION_DIGITS
                ):
                    retrieve_leaf(
                        digit + suffix,
                        exact=False,
                        recursion_depth=(
                            recursion_depth + 1
                        ),
                    )

                return

            raise

        rows = (
            validate_opencitations_partition_payload(
                payload,
                leaf_regex=leaf_regex,
                context=context,
            )
        )

        leaf_order += 1

        leaves.append({
            "wave": wave,
            "anchor_id":
                anchor["anchor_id"],
            "anchor_tool":
                anchor["tool"],
            "direction":
                direction,
            "leaf_order":
                leaf_order,
            "recursion_depth":
                recursion_depth,
            "suffix_digits":
                len(suffix),
            "partition_kind":
                (
                    "exact"
                    if exact
                    else "suffix"
                ),
            "suffix":
                suffix,
            "leaf_regex":
                leaf_regex,
            "request_sha256":
                hashlib.sha256(
                    request_url.encode(
                        "utf-8"
                    )
                ).hexdigest(),
            "raw_file":
                raw_rel(
                    raw_path,
                    output_root,
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

    for digit in (
        OPENCITATIONS_PARTITION_DIGITS
    ):
        retrieve_leaf(
            digit,
            exact=False,
            recursion_depth=0,
        )

    reconciled = (
        reconcile_opencitations_partition_rows(
            records,
            expected_count=expected_count,
            context=context,
        )
    )

    return (
        reconciled,
        leaves,
    )


def retrieve_opencitations(
    anchor: dict[str, str],
    *,
    wave: int,
    token: str,
    output_root: Path,
    fetcher: Callable[..., Any] = fetch_json,
) -> tuple[
    list[dict],
    list[dict],
    list[dict],
    list[dict],
]:
    raw_root = (
        output_root
        / "raw"
        / "opencitations"
        / anchor["anchor_id"]
    )

    doi = normalise_doi(
        anchor["canonical_identifier"]
    )

    headers = {
        "Accept": "application/json",
        "User-Agent":
            "branchsnv-validation/experiment07",
    }

    if token:
        headers["authorization"] = token

    edges: list[dict] = []
    neighbours: list[dict] = []
    statuses: list[dict] = []
    partition_leaves: list[dict] = []

    for direction in [
        "backward",
        "forward",
    ]:
        count_path = (
            raw_root
            / f"{direction}_count.json"
        )

        try:
            count_payload = fetcher(
                opencitations_count_url(
                    direction,
                    doi,
                ),
                headers=headers,
                raw_path=count_path,
                delay=0.40,
            )

        except NotIndexed:
            statuses.append({
                "wave": wave,
                "anchor_id":
                    anchor["anchor_id"],
                "anchor_tool":
                    anchor["tool"],
                "source":
                    "opencitations",
                "direction": direction,
                "status": "not_indexed",
                "reported_count": 0,
                "retrieved_count": 0,
                "response_files": 1,
                "terminal_detail":
                    "count endpoint returned HTTP 404",
            })

            continue

        reported_count = (
            parse_opencitations_count(
                count_payload
            )
        )

        if reported_count == 0:
            statuses.append({
                "wave": wave,
                "anchor_id":
                    anchor["anchor_id"],
                "anchor_tool":
                    anchor["tool"],
                "source":
                    "opencitations",
                "direction": direction,
                "status":
                    "resolved_zero_edges",
                "reported_count": 0,
                "retrieved_count": 0,
                "response_files": 1,
                "terminal_detail":
                    "independent count endpoint "
                    "reported zero; no partition "
                    "data requests required",
            })

            continue

        (
            partition_rows,
            direction_leaves,
        ) = (
            retrieve_opencitations_partitioned(
                anchor=anchor,
                direction=direction,
                doi=doi,
                expected_count=reported_count,
                wave=wave,
                headers=headers,
                raw_root=raw_root,
                output_root=output_root,
                fetcher=fetcher,
            )
        )

        partition_leaves.extend(
            direction_leaves
        )

        seen_oci: set[str] = set()

        for (
            item,
            item_raw_path,
        ) in partition_rows:
            citing = parse_pid_bundle(
                item.get("citing")
            )

            cited = parse_pid_bundle(
                item.get("cited")
            )

            oci = str(
                item.get("oci")
                or ""
            ).strip()

            if oci in seen_oci:
                raise RuntimeError(
                    f"{anchor['anchor_id']}: "
                    f"duplicate OpenCitations "
                    f"{direction} OCI {oci!r}"
                )

            seen_oci.add(oci)

            edges.append({
                "wave": wave,
                "anchor_id":
                    anchor["anchor_id"],
                "anchor_tool":
                    anchor["tool"],
                "source":
                    "opencitations",
                "direction": direction,
                "anchor_doi": doi,
                "anchor_openalex_id": "",
                "citing_dois":
                    unique_join(
                        citing["doi"]
                    ),
                "cited_dois":
                    unique_join(
                        cited["doi"]
                    ),
                "citing_pmids":
                    unique_join(
                        citing["pmid"]
                    ),
                "cited_pmids":
                    unique_join(
                        cited["pmid"]
                    ),
                "citing_openalex_ids": "",
                "cited_openalex_ids": "",
                "citing_omids":
                    unique_join(
                        citing["omid"]
                    ),
                "cited_omids":
                    unique_join(
                        cited["omid"]
                    ),
                "oci": oci,
                "raw_file": raw_rel(
                    item_raw_path,
                    output_root,
                ),
            })

            neighbour = (
                cited
                if direction == "backward"
                else citing
            )

            source_record_id = (
                first_nonempty(
                    neighbour["doi"]
                )
                or first_nonempty(
                    neighbour["pmid"]
                )
                or first_nonempty(
                    neighbour["omid"]
                )
            )

            if not source_record_id:
                raise RuntimeError(
                    f"{anchor['anchor_id']}: "
                    "OpenCitations neighbour "
                    "contains no supported identifier"
                )

            neighbours.append({
                "wave": wave,
                "anchor_id":
                    anchor["anchor_id"],
                "anchor_tool":
                    anchor["tool"],
                "source":
                    "opencitations",
                "direction": direction,
                "doi": first_nonempty(
                    neighbour["doi"]
                ),
                "pmid": first_nonempty(
                    neighbour["pmid"]
                ),
                "openalex_id": "",
                "omid": first_nonempty(
                    neighbour["omid"]
                ),
                "title": "",
                "year": "",
                "source_record_id":
                    source_record_id,
            })

        statuses.append({
            "wave": wave,
            "anchor_id":
                anchor["anchor_id"],
            "anchor_tool":
                anchor["tool"],
            "source":
                "opencitations",
            "direction": direction,
            "status": "complete",
            "reported_count":
                reported_count,
            "retrieved_count":
                len(partition_rows),
            "response_files":
                1 + len(
                    direction_leaves
                ),
            "terminal_detail":
                "independent count endpoint "
                "reconciled with deterministic "
                "disjoint OCI partition union",
        })

    return (
        edges,
        neighbours,
        statuses,
        partition_leaves,
    )


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


def validate_status_matrix(
    anchors: list[dict[str, str]],
    statuses: list[dict],
) -> None:
    expected = {
        (
            anchor["anchor_id"],
            source,
            direction,
        )
        for anchor in anchors
        for source in [
            "openalex",
            "opencitations",
        ]
        for direction in [
            "backward",
            "forward",
        ]
    }

    observed = {
        (
            row["anchor_id"],
            row["source"],
            row["direction"],
        )
        for row in statuses
    }

    if observed != expected:
        missing = sorted(
            expected - observed
        )
        extra = sorted(
            observed - expected
        )

        raise RuntimeError(
            "Incomplete status matrix. "
            f"Missing={missing}; Extra={extra}"
        )

    terminal = {
        "complete",
        "resolved_zero_edges",
        "not_indexed",
    }

    for row in statuses:
        if row["status"] not in terminal:
            raise RuntimeError(
                "Non-terminal source status: "
                f"{row}"
            )

        if (
            int(row["retrieved_count"])
            != int(row["reported_count"])
        ):
            raise RuntimeError(
                "Reported/retrieved count mismatch: "
                f"{row}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--anchors",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--wave",
        required=True,
        type=int,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    api_key = os.environ.get(
        "OPENALEX_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise SystemExit(
            "ERROR | OPENALEX_API_KEY is required"
        )

    oc_token = os.environ.get(
        "OPENCITATIONS_ACCESS_TOKEN",
        "",
    ).strip()

    if args.output.exists():
        if any(
            args.output.iterdir()
        ):
            raise SystemExit(
                "ERROR | output directory "
                "already exists and is non-empty"
            )
    else:
        args.output.mkdir(
            parents=True,
        )

    anchors = read_anchors(
        args.anchors,
        args.wave,
    )

    all_edges: list[dict] = []
    all_neighbours: list[dict] = []
    all_statuses: list[dict] = []
    all_oc_partition_leaves: list[dict] = []

    for anchor in anchors:
        (
            edges,
            neighbours,
            statuses,
        ) = retrieve_openalex(
            anchor,
            wave=args.wave,
            api_key=api_key,
            output_root=args.output,
        )

        all_edges.extend(edges)
        all_neighbours.extend(
            neighbours
        )
        all_statuses.extend(
            statuses
        )

        (
            edges,
            neighbours,
            statuses,
            partition_leaves,
        ) = retrieve_opencitations(
            anchor,
            wave=args.wave,
            token=oc_token,
            output_root=args.output,
        )

        all_edges.extend(edges)
        all_neighbours.extend(
            neighbours
        )
        all_statuses.extend(
            statuses
        )
        all_oc_partition_leaves.extend(
            partition_leaves
        )

    validate_status_matrix(
        anchors,
        all_statuses,
    )

    all_edges.sort(
        key=lambda row: (
            int(row["wave"]),
            row["anchor_id"],
            row["source"],
            row["direction"],
            row["citing_openalex_ids"],
            row["citing_dois"],
            row["citing_pmids"],
            row["citing_omids"],
            row["cited_openalex_ids"],
            row["cited_dois"],
            row["cited_pmids"],
            row["cited_omids"],
            row["oci"],
        )
    )

    all_neighbours.sort(
        key=lambda row: (
            int(row["wave"]),
            row["anchor_id"],
            row["source"],
            row["direction"],
            row["openalex_id"],
            row["doi"],
            row["pmid"],
            row["omid"],
            row["source_record_id"],
        )
    )

    all_statuses.sort(
        key=lambda row: (
            int(row["wave"]),
            row["anchor_id"],
            row["source"],
            row["direction"],
        )
    )

    all_oc_partition_leaves.sort(
        key=lambda row: (
            int(row["wave"]),
            row["anchor_id"],
            row["direction"],
            int(row["leaf_order"]),
        )
    )

    write_tsv(
        args.output
        / "citation_edges.tsv",
        EDGE_FIELDS,
        all_edges,
    )

    write_tsv(
        args.output
        / "neighbour_records.tsv",
        NEIGHBOUR_FIELDS,
        all_neighbours,
    )

    write_tsv(
        args.output
        / "source_status.tsv",
        STATUS_FIELDS,
        all_statuses,
    )

    write_tsv(
        args.output
        / "opencitations_partition_leaves.tsv",
        OPENCITATIONS_PARTITION_FIELDS,
        all_oc_partition_leaves,
    )

    manifest = {
        "schema_version": 1,
        "status": "COMPLETE",
        "wave": args.wave,
        "retrieved_at_utc":
            utc_now(),
        "git_head": git_head(),
        "anchors_path":
            str(args.anchors),
        "anchors_sha256":
            sha256_file(
                args.anchors
            ),
        "retriever_sha256":
            sha256_file(
                Path(__file__)
            ),
        "anchor_count":
            len(anchors),
        "expected_source_direction_operations":
            len(anchors) * 4,
        "completed_source_direction_operations":
            len(all_statuses),
        "edge_rows":
            len(all_edges),
        "neighbour_rows":
            len(all_neighbours),
        "opencitations_partition_leaf_rows":
            len(all_oc_partition_leaves),
        "opencitations_partition_max_suffix_digits":
            OPENCITATIONS_PARTITION_MAX_SUFFIX_DIGITS,
        "credential_values_written":
            False,
        "openalex_api":
            OPENALEX_ROOT,
        "opencitations_api":
            OPENCITATIONS_ROOT,
        "opencitations_access_token_used":
            bool(oc_token),
    }

    (
        args.output
        / "retrieval_manifest.json"
    ).write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    checksum_names = [
        "citation_edges.tsv",
        "neighbour_records.tsv",
        "source_status.tsv",
        "opencitations_partition_leaves.tsv",
        "retrieval_manifest.json",
    ]

    with (
        args.output
        / "checksums.sha256"
    ).open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        for name in checksum_names:
            path = (
                args.output / name
            )
            fh.write(
                f"{sha256_file(path)}  "
                f"{name}\n"
            )

    print(
        f"PASS | anchors = {len(anchors)}"
    )
    print(
        "PASS | source-direction "
        f"operations = {len(all_statuses)}"
    )
    print(
        f"PASS | citation edges = "
        f"{len(all_edges)}"
    )
    print(
        f"PASS | neighbour records = "
        f"{len(all_neighbours)}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
