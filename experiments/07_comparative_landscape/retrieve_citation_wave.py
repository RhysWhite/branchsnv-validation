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
OPENCITATIONS_CREATION_PARTITION_MAX_PREFIX_CHARACTERS = 32
OPENCITATIONS_MAX_SNAPSHOT_ATTEMPTS = 3

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
    "snapshot_attempt",
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

OPENCITATIONS_CREATION_PARTITION_FIELDS = [
    "wave",
    "anchor_id",
    "anchor_tool",
    "direction",
    "snapshot_attempt",
    "leaf_order",
    "recursion_depth",
    "partition_kind",
    "literal_prefix",
    "leaf_regex",
    "request_sha256",
    "raw_file",
    "row_count",
]

OPENCITATIONS_SNAPSHOT_FIELDS = [
    "wave",
    "anchor_id",
    "anchor_tool",
    "direction",
    "snapshot_attempt",
    "status",
    "retryable",
    "pre_count",
    "post_count",
    "oci_row_count",
    "creation_row_count",
    "oci_complete_row_sha256",
    "creation_complete_row_sha256",
    "oci_set_sha256",
    "creation_oci_set_sha256",
    "complete_row_sets_equal",
    "oci_sets_equal",
    "production_axis",
    "provider_reconciliation_candidate",
    "provider_reconciliation",
    "provider_reconciled_row_count",
    "provider_reconciled_complete_row_sha256",
    "provider_reconciled_oci_set_sha256",
    "provider_alias_pair_count",
    "provider_missing_row_count",
    "provider_discrepant_oci_count",
    "provider_direct_lookup_count",
    "oci_leaf_count",
    "creation_leaf_count",
    "oci_max_recursion_depth",
    "creation_max_recursion_depth",
    "response_files",
    "terminal_detail",
]


class OpenCitationsSnapshotRetryable(RuntimeError):
    """Transient snapshot-consistency failure eligible for a fresh attempt."""

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
    creation_filter: str | None = None,
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

    selected = [
        (
            "oci",
            oci_filter,
        ),
        (
            "creation",
            creation_filter,
        ),
    ]

    selected = [
        (
            field,
            value,
        )
        for field, value in selected
        if value is not None
    ]

    if not selected:
        return base

    if len(selected) != 1:
        raise ValueError(
            "Exactly one OpenCitations partition "
            "filter may be supplied"
        )

    field, value = selected[0]

    if not value:
        raise ValueError(
            f"OpenCitations {field} filter cannot be empty"
        )

    return build_url(
        base,
        {
            "filter":
                f"{field}:{value}",
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
    #
    # OpenAlex cursor pagination is a live traversal rather
    # than a documented immutable snapshot. A provider-side
    # index change during traversal can therefore manifest as
    # duplicate Works, changing counts, cursor cycles, or a
    # final unique-Work/count mismatch.
    #
    # Each attempt is staged independently. Failed attempts
    # remain on disk as forensic evidence but contribute no
    # production edges or neighbours. A retry always restarts
    # from cursor="*".
    # ------------------------------------------------------

    max_forward_snapshot_attempts = 3
    forward_response_files = 0
    forward_accepted = False
    final_retry_reason = ""

    for snapshot_attempt in range(
        1,
        max_forward_snapshot_attempts + 1,
    ):
        attempt_root = (
            raw_root
            / (
                "forward_snapshot_attempt_"
                f"{snapshot_attempt:02d}"
            )
        )

        attempt_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        cursor = "*"
        seen_cursors = {
            cursor,
        }

        page_number = 0
        reported_forward: int | None = None
        forward_seen: set[str] = set()

        attempt_edges: list[dict] = []
        attempt_neighbours: list[dict] = []

        retry_reason = ""

        while cursor:
            page_number += 1

            page_path = (
                attempt_root
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

            forward_response_files += 1

            if not isinstance(
                payload,
                dict,
            ):
                raise RuntimeError(
                    f"{anchor['anchor_id']}: "
                    "invalid OpenAlex forward payload"
                )

            meta = payload.get(
                "meta"
            ) or {}

            if not isinstance(
                meta,
                dict,
            ):
                raise RuntimeError(
                    f"{anchor['anchor_id']}: "
                    "OpenAlex forward meta is not an object"
                )

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

            page_reported = int(
                meta.get(
                    "count",
                    0,
                )
                or 0
            )

            if reported_forward is None:
                reported_forward = (
                    page_reported
                )

            elif (
                page_reported
                != reported_forward
            ):
                retry_reason = (
                    "OpenAlex forward meta.count "
                    "changed during cursor traversal "
                    f"{reported_forward}!="
                    f"{page_reported}"
                )
                break

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
                ) = openalex_ids(
                    item
                )

                if not citing_id:
                    raise RuntimeError(
                        f"{anchor['anchor_id']}: "
                        "forward OpenAlex Work lacks ID"
                    )

                if (
                    citing_id
                    in forward_seen
                ):
                    retry_reason = (
                        "duplicate forward Work "
                        f"{citing_id}"
                    )
                    break

                forward_seen.add(
                    citing_id
                )

                attempt_edges.append({
                    "wave":
                        wave,
                    "anchor_id":
                        anchor["anchor_id"],
                    "anchor_tool":
                        anchor["tool"],
                    "source":
                        "openalex",
                    "direction":
                        "forward",
                    "anchor_doi":
                        doi,
                    "anchor_openalex_id":
                        work_id,
                    "citing_dois":
                        citing_doi,
                    "cited_dois":
                        doi,
                    "citing_pmids":
                        citing_pmid,
                    "cited_pmids":
                        "",
                    "citing_openalex_ids":
                        citing_id,
                    "cited_openalex_ids":
                        work_id,
                    "citing_omids":
                        "",
                    "cited_omids":
                        "",
                    "oci":
                        "",
                    "raw_file":
                        raw_rel(
                            page_path,
                            output_root,
                        ),
                })

                attempt_neighbours.append({
                    "wave":
                        wave,
                    "anchor_id":
                        anchor["anchor_id"],
                    "anchor_tool":
                        anchor["tool"],
                    "source":
                        "openalex",
                    "direction":
                        "forward",
                    "doi":
                        citing_doi,
                    "pmid":
                        citing_pmid,
                    "openalex_id":
                        citing_id,
                    "omid":
                        "",
                    "title":
                        str(
                            item.get(
                                "title"
                            )
                            or item.get(
                                "display_name"
                            )
                            or ""
                        ).strip(),
                    "year":
                        str(
                            item.get(
                                "publication_year"
                            )
                            or ""
                        ),
                    "source_record_id":
                        citing_id,
                })

            if retry_reason:
                break

            next_cursor = meta.get(
                "next_cursor"
            )

            if (
                results
                and next_cursor
            ):
                next_cursor = str(
                    next_cursor
                )

                if (
                    next_cursor
                    in seen_cursors
                ):
                    retry_reason = (
                        "OpenAlex forward cursor cycle "
                        f"{next_cursor!r}"
                    )
                    break

                seen_cursors.add(
                    next_cursor
                )

                cursor = next_cursor

            else:
                cursor = ""

        reported_forward = (
            reported_forward
            if reported_forward is not None
            else 0
        )

        if (
            not retry_reason
            and len(
                forward_seen
            )
            != reported_forward
        ):
            retry_reason = (
                "OpenAlex forward reported "
                f"{reported_forward}, retrieved "
                f"{len(forward_seen)}"
            )

        attempt_record = {
            "wave":
                wave,
            "anchor_id":
                anchor["anchor_id"],
            "anchor_tool":
                anchor["tool"],
            "source":
                "openalex",
            "direction":
                "forward",
            "snapshot_attempt":
                snapshot_attempt,
            "status":
                (
                    "retryable_failure"
                    if retry_reason
                    else "accepted"
                ),
            "retryable":
                bool(
                    retry_reason
                ),
            "reported_count":
                reported_forward,
            "retrieved_count":
                len(
                    forward_seen
                ),
            "response_files":
                page_number,
            "terminal_detail":
                (
                    retry_reason
                    if retry_reason
                    else (
                        "complete unique-Work cursor "
                        "snapshot"
                    )
                ),
        }

        (
            attempt_root
            / "snapshot_attempt.json"
        ).write_text(
            json.dumps(
                attempt_record,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        if retry_reason:
            final_retry_reason = (
                retry_reason
            )

            if (
                snapshot_attempt
                == max_forward_snapshot_attempts
            ):
                break

            continue

        # Only a completely validated traversal is promoted
        # into production.
        edges.extend(
            attempt_edges
        )

        neighbours.extend(
            attempt_neighbours
        )

        statuses.append({
            "wave":
                wave,
            "anchor_id":
                anchor["anchor_id"],
            "anchor_tool":
                anchor["tool"],
            "source":
                "openalex",
            "direction":
                "forward",
            "status":
                (
                    "complete"
                    if forward_seen
                    else "resolved_zero_edges"
                ),
            "reported_count":
                reported_forward,
            "retrieved_count":
                len(
                    forward_seen
                ),
            "response_files":
                forward_response_files,
            "terminal_detail":
                (
                    "cursor pagination complete; "
                    "accepted forward snapshot "
                    f"attempt {snapshot_attempt}"
                ),
        })

        forward_accepted = True
        break

    if not forward_accepted:
        raise RuntimeError(
            f"{anchor['anchor_id']}: "
            "OpenAlex forward did not produce "
            "an acceptable snapshot within "
            f"{max_forward_snapshot_attempts} attempts: "
            f"{final_retry_reason}"
        )

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
    expected_count: int | None,
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

    if (
        expected_count is not None
        and len(seen) != expected_count
    ):
        raise OpenCitationsSnapshotRetryable(
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
    snapshot_attempt: int = 0,
    enforce_expected_count: bool = True,
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
            "snapshot_attempt":
                snapshot_attempt,
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
            expected_count=(
                expected_count
                if enforce_expected_count
                else None
            ),
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


def canonical_opencitations_row(
    row: dict,
) -> str:
    return json.dumps(
        row,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def hash_sorted_strings(
    values,
) -> str:
    return hashlib.sha256(
        "\n".join(
            sorted(values)
        ).encode(
            "utf-8"
        )
    ).hexdigest()


def opencitations_complete_row_identity(
    records: list[
        tuple[
            dict,
            Path,
        ]
    ],
    *,
    context: str,
) -> tuple[
    set[str],
    str,
]:
    signatures = [
        canonical_opencitations_row(
            row
        )
        for row, _ in records
    ]

    unique = set(
        signatures
    )

    if len(unique) != len(signatures):
        raise RuntimeError(
            f"{context}: duplicate complete "
            "OpenCitations row"
        )

    return (
        unique,
        hash_sorted_strings(
            unique
        ),
    )


def opencitations_oci_identity(
    records: list[
        tuple[
            dict,
            Path,
        ]
    ],
    *,
    context: str,
) -> tuple[
    set[str],
    str,
]:
    full_re = re.compile(
        OPENCITATIONS_OCI_PATTERN
    )

    ocis = []

    for row, _ in records:
        oci = str(
            row.get("oci")
            or ""
        ).strip()

        if not oci:
            raise RuntimeError(
                f"{context}: row contains no OCI"
            )

        if not full_re.fullmatch(
            oci
        ):
            raise RuntimeError(
                f"{context}: malformed OCI {oci!r}"
            )

        ocis.append(
            oci
        )

    if len(ocis) != len(set(ocis)):
        raise RuntimeError(
            f"{context}: duplicate OCI"
        )

    values = set(
        ocis
    )

    return (
        values,
        hash_sorted_strings(
            values
        ),
    )



def opencitations_identifier_values(
    value: str,
    scheme: str,
) -> set[str]:
    scheme = scheme.lower()

    values = set()

    for token in str(
        value
        or ""
    ).split():
        if ":" not in token:
            continue

        observed_scheme, identifier = (
            token.split(
                ":",
                1,
            )
        )

        if (
            observed_scheme.lower()
            != scheme
        ):
            continue

        identifier = identifier.strip()

        if not identifier:
            continue

        if scheme == "doi":
            identifier = (
                normalise_doi(
                    identifier
                ).lower()
            )
        else:
            identifier = (
                identifier.lower()
            )

        values.add(
            identifier
        )

    return values


def opencitations_single_citing_openalex(
    row: dict,
) -> str | None:
    values = (
        opencitations_identifier_values(
            str(
                row.get(
                    "citing"
                )
                or ""
            ),
            "openalex",
        )
    )

    if len(values) != 1:
        return None

    return next(
        iter(values)
    )


def opencitations_direct_citation_url(
    oci: str,
) -> str:
    return (
        f"{OPENCITATIONS_ROOT}/citation/"
        + urllib.parse.quote(
            oci,
            safe="-",
        )
    )


def build_opencitations_provider_candidate(
    *,
    anchor: dict[str, str],
    direction: str,
    expected_count: int,
    oci_rows: list[
        tuple[
            dict,
            Path,
        ]
    ],
    creation_rows: list[
        tuple[
            dict,
            Path,
        ]
    ],
    attempt_root: Path,
) -> dict | None:
    """
    Build a narrowly scoped candidate for a known class of
    OpenCitations forward filtered-endpoint inconsistency.

    The OCI axis remains canonical. Creation-axis rows are used only
    to identify:
      1. alternate OCI representations of a work already present on
         the OCI axis, paired by exactly one OpenAlex citing-work ID;
      2. genuinely missing works absent from the complete OCI axis.

    Only genuinely missing creation-axis rows enter production.
    """

    if direction != "forward":
        return None

    if (
        len(creation_rows)
        != expected_count
    ):
        return None

    oci_by_signature = {
        canonical_opencitations_row(
            row
        ):
            (
                row,
                raw_path,
            )
        for row, raw_path in oci_rows
    }

    creation_by_signature = {
        canonical_opencitations_row(
            row
        ):
            (
                row,
                raw_path,
            )
        for row, raw_path in creation_rows
    }

    only_oci_signatures = (
        set(
            oci_by_signature
        )
        - set(
            creation_by_signature
        )
    )

    only_creation_signatures = (
        set(
            creation_by_signature
        )
        - set(
            oci_by_signature
        )
    )

    if (
        not only_oci_signatures
        or not only_creation_signatures
    ):
        return None

    only_oci = [
        oci_by_signature[
            signature
        ]
        for signature in sorted(
            only_oci_signatures
        )
    ]

    only_creation = [
        creation_by_signature[
            signature
        ]
        for signature in sorted(
            only_creation_signatures
        )
    ]

    oci_by_openalex = {}

    for row, raw_path in only_oci:
        openalex_id = (
            opencitations_single_citing_openalex(
                row
            )
        )

        if openalex_id is None:
            return None

        if (
            openalex_id
            in oci_by_openalex
        ):
            return None

        oci_by_openalex[
            openalex_id
        ] = (
            row,
            raw_path,
        )

    creation_by_openalex = {}

    for row, raw_path in only_creation:
        openalex_id = (
            opencitations_single_citing_openalex(
                row
            )
        )

        if openalex_id is None:
            return None

        if (
            openalex_id
            in creation_by_openalex
        ):
            return None

        creation_by_openalex[
            openalex_id
        ] = (
            row,
            raw_path,
        )

    alias_ids = (
        set(
            oci_by_openalex
        )
        & set(
            creation_by_openalex
        )
    )

    unmatched_oci_ids = (
        set(
            oci_by_openalex
        )
        - set(
            creation_by_openalex
        )
    )

    missing_ids = (
        set(
            creation_by_openalex
        )
        - set(
            oci_by_openalex
        )
    )

    # This exception is intentionally limited to the observed class
    # of inconsistency: at least one alternate representation and at
    # least one genuinely missing creation-axis work.
    if (
        not alias_ids
        or not missing_ids
        or unmatched_oci_ids
    ):
        return None

    all_oci_openalex = {}

    for row, _ in oci_rows:
        for openalex_id in (
            opencitations_identifier_values(
                str(
                    row.get(
                        "citing"
                    )
                    or ""
                ),
                "openalex",
            )
        ):
            all_oci_openalex[
                openalex_id
            ] = (
                all_oci_openalex.get(
                    openalex_id,
                    0,
                )
                + 1
            )

    all_creation_openalex = {}

    for row, _ in creation_rows:
        for openalex_id in (
            opencitations_identifier_values(
                str(
                    row.get(
                        "citing"
                    )
                    or ""
                ),
                "openalex",
            )
        ):
            all_creation_openalex[
                openalex_id
            ] = (
                all_creation_openalex.get(
                    openalex_id,
                    0,
                )
                + 1
            )

    for openalex_id in alias_ids:
        if (
            all_oci_openalex.get(
                openalex_id,
                0,
            )
            != 1
            or all_creation_openalex.get(
                openalex_id,
                0,
            )
            != 1
        ):
            return None

    missing_records = []

    for openalex_id in sorted(
        missing_ids
    ):
        if (
            all_oci_openalex.get(
                openalex_id,
                0,
            )
            != 0
        ):
            return None

        if (
            all_creation_openalex.get(
                openalex_id,
                0,
            )
            != 1
        ):
            return None

        missing_records.append(
            creation_by_openalex[
                openalex_id
            ]
        )

    production_rows = (
        list(
            oci_rows
        )
        + missing_records
    )

    if (
        len(production_rows)
        != expected_count
    ):
        return None

    try:
        (
            production_complete_rows,
            production_complete_hash,
        ) = (
            opencitations_complete_row_identity(
                production_rows,
                context=(
                    f"{anchor['anchor_id']}: "
                    f"OpenCitations {direction} "
                    "provider-reconciled production"
                ),
            )
        )

        (
            production_ocis,
            production_oci_hash,
        ) = (
            opencitations_oci_identity(
                production_rows,
                context=(
                    f"{anchor['anchor_id']}: "
                    f"OpenCitations {direction} "
                    "provider-reconciled production"
                ),
            )
        )

    except RuntimeError:
        return None

    if (
        len(
            production_complete_rows
        )
        != expected_count
        or len(
            production_ocis
        )
        != expected_count
    ):
        return None

    discrepant_records = {}

    for row, raw_path in (
        only_oci
        + only_creation
    ):
        oci = str(
            row.get(
                "oci"
            )
            or ""
        ).strip()

        if not oci:
            return None

        signature = (
            canonical_opencitations_row(
                row
            )
        )

        if (
            oci in discrepant_records
            and discrepant_records[
                oci
            ][
                "signature"
            ]
            != signature
        ):
            return None

        discrepant_records[
            oci
        ] = {
            "row":
                row,
            "signature":
                signature,
            "raw_path":
                raw_path,
        }

    alias_pairs = []

    for openalex_id in sorted(
        alias_ids
    ):
        oci_row, oci_raw = (
            oci_by_openalex[
                openalex_id
            ]
        )

        creation_row, creation_raw = (
            creation_by_openalex[
                openalex_id
            ]
        )

        alias_pairs.append({
            "openalex_id":
                openalex_id,
            "oci_axis_oci":
                str(
                    oci_row.get(
                        "oci"
                    )
                    or ""
                ),
            "creation_axis_oci":
                str(
                    creation_row.get(
                        "oci"
                    )
                    or ""
                ),
            "oci_axis_raw_file":
                str(
                    oci_raw.relative_to(
                        attempt_root
                    )
                ),
            "creation_axis_raw_file":
                str(
                    creation_raw.relative_to(
                        attempt_root
                    )
                ),
        })

    missing_evidence = []

    for openalex_id in sorted(
        missing_ids
    ):
        row, raw_path = (
            creation_by_openalex[
                openalex_id
            ]
        )

        missing_evidence.append({
            "openalex_id":
                openalex_id,
            "oci":
                str(
                    row.get(
                        "oci"
                    )
                    or ""
                ),
            "raw_file":
                str(
                    raw_path.relative_to(
                        attempt_root
                    )
                ),
            "complete_row":
                row,
        })

    evidence = {
        "status":
            "provider_reconciliation_candidate",
        "anchor_id":
            anchor[
                "anchor_id"
            ],
        "direction":
            direction,
        "reported_count":
            expected_count,
        "oci_row_count":
            len(
                oci_rows
            ),
        "creation_row_count":
            len(
                creation_rows
            ),
        "alias_pair_count":
            len(
                alias_pairs
            ),
        "missing_row_count":
            len(
                missing_records
            ),
        "discrepant_oci_count":
            len(
                discrepant_records
            ),
        "reconciled_row_count":
            len(
                production_rows
            ),
        "reconciled_complete_row_sha256":
            production_complete_hash,
        "reconciled_oci_set_sha256":
            production_oci_hash,
        "alias_pairs":
            alias_pairs,
        "missing_rows":
            missing_evidence,
        "discrepant_ocis":
            sorted(
                discrepant_records
            ),
    }

    return {
        "production_rows":
            production_rows,
        "row_count":
            len(
                production_rows
            ),
        "complete_row_sha256":
            production_complete_hash,
        "oci_set_sha256":
            production_oci_hash,
        "alias_pair_count":
            len(
                alias_pairs
            ),
        "missing_row_count":
            len(
                missing_records
            ),
        "discrepant_oci_count":
            len(
                discrepant_records
            ),
        "discrepant_records":
            discrepant_records,
        "evidence":
            evidence,
    }


def verify_opencitations_provider_discrepancies(
    *,
    anchor: dict[str, str],
    doi: str,
    candidate: dict,
    attempt_root: Path,
    raw_root: Path,
    headers: dict[str, str],
    fetcher: Callable[..., Any],
    verification_cache: dict,
    seen_discrepant_ocis: set[str],
) -> bool:
    """
    Directly verify each unique discrepant OCI exactly once.

    A direct /citation/{oci} result must reproduce the complete
    discrepant row byte-for-byte after canonical JSON serialisation
    and must cite the anchor DOI.
    """

    anchor_doi = (
        normalise_doi(
            doi
        ).lower()
    )

    discrepant_records = (
        candidate[
            "discrepant_records"
        ]
    )

    seen_discrepant_ocis.update(
        discrepant_records
    )

    for oci in sorted(
        discrepant_records
    ):
        expected = (
            discrepant_records[
                oci
            ]
        )

        expected_signature = (
            expected[
                "signature"
            ]
        )

        if (
            oci
            in verification_cache
        ):
            if (
                verification_cache[
                    oci
                ][
                    "complete_row"
                ]
                != expected_signature
            ):
                return False

            continue

        raw_path = (
            attempt_root
            / "provider_reconciliation_direct_oci"
            / f"{oci}.json"
        )

        payload = fetcher(
            opencitations_direct_citation_url(
                oci
            ),
            headers=headers,
            raw_path=raw_path,
            delay=0.40,
        )

        rows = flatten_json_list(
            payload
        )

        if len(rows) != 1:
            return False

        direct_row = rows[
            0
        ]

        direct_signature = (
            canonical_opencitations_row(
                direct_row
            )
        )

        if (
            direct_signature
            != expected_signature
        ):
            return False

        cited_dois = (
            opencitations_identifier_values(
                str(
                    direct_row.get(
                        "cited"
                    )
                    or ""
                ),
                "doi",
            )
        )

        if (
            anchor_doi
            not in cited_dois
        ):
            return False

        verification_cache[
            oci
        ] = {
            "complete_row":
                direct_signature,
            "raw_file":
                str(
                    raw_path.relative_to(
                        raw_root
                    )
                ),
        }

    return (
        set(
            verification_cache
        )
        >= seen_discrepant_ocis
    )


def opencitations_creation_root_leaves() -> list[dict]:
    leaves = [
        {
            "partition_kind":
                "empty",
            "literal_prefix":
                "",
            "leaf_regex":
                r"^$",
            "recursion_depth":
                0,
            "subdividable":
                False,
        },
        {
            "partition_kind":
                "non_digit",
            "literal_prefix":
                "",
            "leaf_regex":
                r"^[^0-9].*$",
            "recursion_depth":
                0,
            "subdividable":
                False,
        },
    ]

    for digit in (
        OPENCITATIONS_PARTITION_DIGITS
    ):
        leaves.append({
            "partition_kind":
                "prefix",
            "literal_prefix":
                digit,
            "leaf_regex":
                rf"^{re.escape(digit)}.*$",
            "recursion_depth":
                0,
            "subdividable":
                True,
        })

    return leaves


def opencitations_creation_prefix_children(
    prefix: str,
    *,
    recursion_depth: int,
) -> list[dict]:
    if not prefix:
        raise ValueError(
            "Cannot subdivide empty creation prefix"
        )

    children = [
        {
            "partition_kind":
                "exact",
            "literal_prefix":
                prefix,
            "leaf_regex":
                rf"^{re.escape(prefix)}$",
            "recursion_depth":
                recursion_depth,
            "subdividable":
                False,
        },
    ]

    for digit in (
        OPENCITATIONS_PARTITION_DIGITS
    ):
        child_prefix = (
            prefix
            + digit
        )

        children.append({
            "partition_kind":
                "prefix",
            "literal_prefix":
                child_prefix,
            "leaf_regex":
                rf"^{re.escape(child_prefix)}.*$",
            "recursion_depth":
                recursion_depth,
            "subdividable":
                True,
        })

    hyphen_prefix = (
        prefix
        + "-"
    )

    children.append({
        "partition_kind":
            "prefix",
        "literal_prefix":
            hyphen_prefix,
        "leaf_regex":
            rf"^{re.escape(hyphen_prefix)}.*$",
        "recursion_depth":
            recursion_depth,
        "subdividable":
            True,
    })

    children.append({
        "partition_kind":
            "other",
        "literal_prefix":
            prefix,
        "leaf_regex":
            (
                rf"^{re.escape(prefix)}"
                r"[^0-9-].*$"
            ),
        "recursion_depth":
            recursion_depth,
        "subdividable":
            False,
    })

    return children


def opencitations_creation_safe_prefix(
    value: str,
) -> str:
    if not value:
        return "EMPTY"

    return value.replace(
        "-",
        "H",
    )


def opencitations_creation_raw_path(
    raw_root: Path,
    leaf: dict,
) -> Path:
    return (
        raw_root
        / "creation_partitions"
        / (
            "depth_"
            f"{int(leaf['recursion_depth']):02d}"
        )
        / (
            f"{leaf['partition_kind']}_"
            f"{opencitations_creation_safe_prefix(str(leaf['literal_prefix']))}"
            ".json"
        )
    )


def validate_opencitations_creation_payload(
    payload: Any,
    *,
    leaf_regex: str,
    context: str,
) -> list[dict]:
    rows = flatten_json_list(
        payload
    )

    rx = re.compile(
        leaf_regex
    )

    for row in rows:
        if "creation" not in row:
            raise RuntimeError(
                f"{context}: OpenCitations row "
                "lacks creation field"
            )

        creation = row[
            "creation"
        ]

        if not isinstance(
            creation,
            str,
        ):
            raise RuntimeError(
                f"{context}: OpenCitations creation "
                "field is not a string"
            )

        if not rx.fullmatch(
            creation
        ):
            raise RuntimeError(
                f"{context}: creation value "
                f"{creation!r} does not belong "
                "to its partition leaf"
            )

    return rows


def reconcile_opencitations_creation_rows(
    records: list[
        tuple[
            dict,
            Path,
        ]
    ],
    *,
    expected_count: int | None,
    context: str,
) -> list[
    tuple[
        dict,
        Path,
    ]
]:
    opencitations_complete_row_identity(
        records,
        context=context,
    )

    (
        ocis,
        _,
    ) = opencitations_oci_identity(
        records,
        context=context,
    )

    if (
        expected_count is not None
        and len(records) != expected_count
    ):
        raise OpenCitationsSnapshotRetryable(
            f"{context}: OpenCitations reported "
            f"{expected_count}, creation partition "
            f"retrieved {len(records)} complete rows"
        )

    if len(ocis) != len(records):
        raise RuntimeError(
            f"{context}: creation partition OCI "
            "cardinality differs from row cardinality"
        )

    return sorted(
        records,
        key=lambda pair: str(
            pair[0].get("oci")
            or ""
        ),
    )


def retrieve_opencitations_creation_partitioned(
    *,
    anchor: dict[str, str],
    direction: str,
    doi: str,
    expected_count: int,
    wave: int,
    snapshot_attempt: int,
    headers: dict[str, str],
    raw_root: Path,
    output_root: Path,
    fetcher: Callable[..., Any],
    enforce_expected_count: bool = True,
    max_prefix_characters: int = (
        OPENCITATIONS_CREATION_PARTITION_MAX_PREFIX_CHARACTERS
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

    if max_prefix_characters < 1:
        raise ValueError(
            "max_prefix_characters must be positive"
        )

    if expected_count == 0:
        return [], []

    context = (
        f"{anchor['anchor_id']}: "
        f"OpenCitations {direction} creation axis"
    )

    records = []
    leaves = []
    leaf_order = 0

    def retrieve_leaf(
        leaf: dict,
    ) -> None:
        nonlocal leaf_order

        leaf_regex = str(
            leaf["leaf_regex"]
        )

        raw_path = (
            opencitations_creation_raw_path(
                raw_root,
                leaf,
            )
        )

        request_url = (
            opencitations_url(
                direction,
                doi,
                creation_filter=
                    leaf_regex,
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
                        "literal_prefix"
                    ]
                )

                if (
                    len(prefix)
                    >= max_prefix_characters
                ):
                    raise RuntimeError(
                        f"{context}: creation partition "
                        "recursion ceiling reached at "
                        f"{len(prefix)} prefix characters"
                    ) from exc

                for child in (
                    opencitations_creation_prefix_children(
                        prefix,
                        recursion_depth=(
                            int(
                                leaf[
                                    "recursion_depth"
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
            validate_opencitations_creation_payload(
                payload,
                leaf_regex=
                    leaf_regex,
                context=
                    context,
            )
        )

        leaf_order += 1

        leaves.append({
            "wave":
                wave,
            "anchor_id":
                anchor["anchor_id"],
            "anchor_tool":
                anchor["tool"],
            "direction":
                direction,
            "snapshot_attempt":
                snapshot_attempt,
            "leaf_order":
                leaf_order,
            "recursion_depth":
                int(
                    leaf[
                        "recursion_depth"
                    ]
                ),
            "partition_kind":
                str(
                    leaf[
                        "partition_kind"
                    ]
                ),
            "literal_prefix":
                str(
                    leaf[
                        "literal_prefix"
                    ]
                ),
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

    for leaf in (
        opencitations_creation_root_leaves()
    ):
        retrieve_leaf(
            leaf
        )

    reconciled = (
        reconcile_opencitations_creation_rows(
            records,
            expected_count=(
                expected_count
                if enforce_expected_count
                else None
            ),
            context=context,
        )
    )

    return (
        reconciled,
        leaves,
    )


def caused_by_retryable_transport_error(
    exc: BaseException,
) -> bool:
    current = exc
    seen = set()

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
            urllib.error.HTTPError,
        ):
            return (
                current.code == 429
                or 500 <= current.code <= 599
            )

        if isinstance(
            current,
            (
                http.client.IncompleteRead,
                TimeoutError,
            ),
        ):
            return True

        if isinstance(
            current,
            urllib.error.URLError,
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


def opencitations_attempt_response_files(
    attempt_root: Path,
) -> int:
    return sum(
        1
        for path in attempt_root.rglob(
            "*.json"
        )
        if path.name not in {
            "snapshot_attempt.json",
            "provider_reconciliation_candidate.json",
            "provider_reconciliation.json",
        }
    )


def write_opencitations_snapshot_attempt(
    attempt_root: Path,
    record: dict,
) -> None:
    attempt_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        attempt_root
        / "snapshot_attempt.json"
    ).write_text(
        json.dumps(
            record,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )


def opencitations_rows_to_outputs(
    *,
    partition_rows: list[
        tuple[
            dict,
            Path,
        ]
    ],
    anchor: dict[str, str],
    direction: str,
    doi: str,
    wave: int,
    output_root: Path,
) -> tuple[
    list[dict],
    list[dict],
]:
    edges = []
    neighbours = []
    seen_oci = set()

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

        seen_oci.add(
            oci
        )

        edges.append({
            "wave":
                wave,
            "anchor_id":
                anchor["anchor_id"],
            "anchor_tool":
                anchor["tool"],
            "source":
                "opencitations",
            "direction":
                direction,
            "anchor_doi":
                doi,
            "anchor_openalex_id":
                "",
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
            "citing_openalex_ids":
                "",
            "cited_openalex_ids":
                "",
            "citing_omids":
                unique_join(
                    citing["omid"]
                ),
            "cited_omids":
                unique_join(
                    cited["omid"]
                ),
            "oci":
                oci,
            "raw_file":
                raw_rel(
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
            "wave":
                wave,
            "anchor_id":
                anchor["anchor_id"],
            "anchor_tool":
                anchor["tool"],
            "source":
                "opencitations",
            "direction":
                direction,
            "doi":
                first_nonempty(
                    neighbour["doi"]
                ),
            "pmid":
                first_nonempty(
                    neighbour["pmid"]
                ),
            "openalex_id":
                "",
            "omid":
                first_nonempty(
                    neighbour["omid"]
                ),
            "title":
                "",
            "year":
                "",
            "source_record_id":
                source_record_id,
        })

    return (
        edges,
        neighbours,
    )


def retrieve_opencitations_dual_axis(
    anchor: dict[str, str],
    *,
    wave: int,
    token: str,
    output_root: Path,
    fetcher: Callable[..., Any] = fetch_json,
    maximum_snapshot_attempts: int = (
        OPENCITATIONS_MAX_SNAPSHOT_ATTEMPTS
    ),
) -> tuple[
    list[dict],
    list[dict],
    list[dict],
    list[dict],
    list[dict],
    list[dict],
]:
    if maximum_snapshot_attempts < 1:
        raise ValueError(
            "maximum_snapshot_attempts must be positive"
        )

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
        "Accept":
            "application/json",
        "User-Agent":
            "branchsnv-validation/experiment07",
    }

    if token:
        headers[
            "authorization"
        ] = token

    edges = []
    neighbours = []
    statuses = []
    oci_partition_leaves = []
    creation_partition_leaves = []
    snapshot_attempts = []

    for direction in [
        "backward",
        "forward",
    ]:
        direction_attempt_records = []
        direction_complete = False

        provider_direct_verification = {}
        provider_seen_discrepant_ocis = set()

        for snapshot_attempt in range(
            1,
            maximum_snapshot_attempts + 1,
        ):
            attempt_root = (
                raw_root
                / (
                    f"{direction}_snapshot_attempt_"
                    f"{snapshot_attempt:02d}"
                )
            )

            record = {
                "wave":
                    wave,
                "anchor_id":
                    anchor["anchor_id"],
                "anchor_tool":
                    anchor["tool"],
                "direction":
                    direction,
                "snapshot_attempt":
                    snapshot_attempt,
                "status":
                    "",
                "retryable":
                    "",
                "pre_count":
                    "",
                "post_count":
                    "",
                "oci_row_count":
                    "",
                "creation_row_count":
                    "",
                "oci_complete_row_sha256":
                    "",
                "creation_complete_row_sha256":
                    "",
                "oci_set_sha256":
                    "",
                "creation_oci_set_sha256":
                    "",
                "complete_row_sets_equal":
                    "",
                "oci_sets_equal":
                    "",
                "production_axis":
                    "",
                "provider_reconciliation_candidate":
                    False,
                "provider_reconciliation":
                    False,
                "provider_reconciled_row_count":
                    "",
                "provider_reconciled_complete_row_sha256":
                    "",
                "provider_reconciled_oci_set_sha256":
                    "",
                "provider_alias_pair_count":
                    "",
                "provider_missing_row_count":
                    "",
                "provider_discrepant_oci_count":
                    "",
                "provider_direct_lookup_count":
                    0,
                "oci_leaf_count":
                    0,
                "creation_leaf_count":
                    0,
                "oci_max_recursion_depth":
                    0,
                "creation_max_recursion_depth":
                    0,
                "response_files":
                    0,
                "terminal_detail":
                    "",
            }

            try:
                pre_path = (
                    attempt_root
                    / "count_pre.json"
                )

                try:
                    pre_payload = fetcher(
                        opencitations_count_url(
                            direction,
                            doi,
                        ),
                        headers=headers,
                        raw_path=pre_path,
                        delay=0.40,
                    )

                except NotIndexed:
                    record[
                        "status"
                    ] = "not_indexed"

                    record[
                        "retryable"
                    ] = False

                    record[
                        "response_files"
                    ] = 1

                    record[
                        "terminal_detail"
                    ] = (
                        "pre-count endpoint returned HTTP 404"
                    )

                    write_opencitations_snapshot_attempt(
                        attempt_root,
                        record,
                    )

                    direction_attempt_records.append(
                        dict(
                            record
                        )
                    )

                    snapshot_attempts.append(
                        dict(
                            record
                        )
                    )

                    statuses.append({
                        "wave":
                            wave,
                        "anchor_id":
                            anchor[
                                "anchor_id"
                            ],
                        "anchor_tool":
                            anchor[
                                "tool"
                            ],
                        "source":
                            "opencitations",
                        "direction":
                            direction,
                        "status":
                            "not_indexed",
                        "reported_count":
                            0,
                        "retrieved_count":
                            0,
                        "response_files":
                            1,
                        "terminal_detail":
                            (
                                "count endpoint "
                                "returned HTTP 404"
                            ),
                    })

                    direction_complete = True
                    break

                pre_count = (
                    parse_opencitations_count(
                        pre_payload
                    )
                )

                record[
                    "pre_count"
                ] = pre_count

                if pre_count == 0:
                    post_path = (
                        attempt_root
                        / "count_post.json"
                    )

                    post_payload = fetcher(
                        opencitations_count_url(
                            direction,
                            doi,
                        ),
                        headers=headers,
                        raw_path=
                            post_path,
                        delay=0.40,
                    )

                    post_count = (
                        parse_opencitations_count(
                            post_payload
                        )
                    )

                    record[
                        "post_count"
                    ] = post_count

                    empty_hash = (
                        hash_sorted_strings(
                            set()
                        )
                    )

                    record[
                        "oci_row_count"
                    ] = 0
                    record[
                        "creation_row_count"
                    ] = 0
                    record[
                        "oci_complete_row_sha256"
                    ] = empty_hash
                    record[
                        "creation_complete_row_sha256"
                    ] = empty_hash
                    record[
                        "oci_set_sha256"
                    ] = empty_hash
                    record[
                        "creation_oci_set_sha256"
                    ] = empty_hash
                    record[
                        "complete_row_sets_equal"
                    ] = True
                    record[
                        "oci_sets_equal"
                    ] = True
                    record[
                        "production_axis"
                    ] = "none"

                    if post_count != 0:
                        raise OpenCitationsSnapshotRetryable(
                            f"{anchor['anchor_id']}: "
                            f"OpenCitations {direction} "
                            "zero pre-count changed to "
                            f"post-count {post_count}"
                        )

                    record[
                        "status"
                    ] = "accepted_zero"

                    record[
                        "retryable"
                    ] = False

                    record[
                        "response_files"
                    ] = (
                        opencitations_attempt_response_files(
                            attempt_root
                        )
                    )

                    record[
                        "terminal_detail"
                    ] = (
                        "stable zero pre/post count; "
                        "no partition data requests"
                    )

                    write_opencitations_snapshot_attempt(
                        attempt_root,
                        record,
                    )

                    direction_attempt_records.append(
                        dict(record)
                    )
                    snapshot_attempts.append(
                        dict(record)
                    )

                    statuses.append({
                        "wave":
                            wave,
                        "anchor_id":
                            anchor[
                                "anchor_id"
                            ],
                        "anchor_tool":
                            anchor[
                                "tool"
                            ],
                        "source":
                            "opencitations",
                        "direction":
                            direction,
                        "status":
                            "resolved_zero_edges",
                        "reported_count":
                            0,
                        "retrieved_count":
                            0,
                        "response_files":
                            sum(
                                int(
                                    item[
                                        "response_files"
                                    ]
                                )
                                for item in (
                                    direction_attempt_records
                                )
                            ),
                        "terminal_detail":
                            (
                                "dual-axis snapshot "
                                "reconciliation accepted "
                                f"attempt {snapshot_attempt}; "
                                "stable zero count"
                            ),
                    })

                    direction_complete = True
                    break

                (
                    oci_rows,
                    oci_leaves,
                ) = (
                    retrieve_opencitations_partitioned(
                        anchor=anchor,
                        direction=
                            direction,
                        doi=doi,
                        expected_count=
                            pre_count,
                        wave=wave,
                        headers=headers,
                        raw_root=(
                            attempt_root
                            / "oci_axis"
                        ),
                        output_root=
                            output_root,
                        fetcher=
                            fetcher,
                        snapshot_attempt=
                            snapshot_attempt,
                        enforce_expected_count=
                            False,
                    )
                )

                (
                    creation_rows,
                    creation_leaves,
                ) = (
                    retrieve_opencitations_creation_partitioned(
                        anchor=anchor,
                        direction=
                            direction,
                        doi=doi,
                        expected_count=
                            pre_count,
                        wave=wave,
                        snapshot_attempt=
                            snapshot_attempt,
                        headers=headers,
                        raw_root=(
                            attempt_root
                            / "creation_axis"
                        ),
                        output_root=
                            output_root,
                        fetcher=
                            fetcher,
                        enforce_expected_count=
                            False,
                    )
                )

                (
                    oci_row_set,
                    oci_row_hash,
                ) = (
                    opencitations_complete_row_identity(
                        oci_rows,
                        context=(
                            f"{anchor['anchor_id']}: "
                            f"OpenCitations {direction} "
                            "OCI axis"
                        ),
                    )
                )

                (
                    creation_row_set,
                    creation_row_hash,
                ) = (
                    opencitations_complete_row_identity(
                        creation_rows,
                        context=(
                            f"{anchor['anchor_id']}: "
                            f"OpenCitations {direction} "
                            "creation axis"
                        ),
                    )
                )

                (
                    oci_set,
                    oci_set_hash,
                ) = opencitations_oci_identity(
                    oci_rows,
                    context=(
                        f"{anchor['anchor_id']}: "
                        f"OpenCitations {direction} "
                        "OCI axis"
                    ),
                )

                (
                    creation_oci_set,
                    creation_oci_set_hash,
                ) = opencitations_oci_identity(
                    creation_rows,
                    context=(
                        f"{anchor['anchor_id']}: "
                        f"OpenCitations {direction} "
                        "creation axis"
                    ),
                )

                record[
                    "oci_row_count"
                ] = len(
                    oci_rows
                )
                record[
                    "creation_row_count"
                ] = len(
                    creation_rows
                )
                record[
                    "oci_complete_row_sha256"
                ] = oci_row_hash
                record[
                    "creation_complete_row_sha256"
                ] = creation_row_hash
                record[
                    "oci_set_sha256"
                ] = oci_set_hash
                record[
                    "creation_oci_set_sha256"
                ] = creation_oci_set_hash
                record[
                    "complete_row_sets_equal"
                ] = (
                    oci_row_set
                    == creation_row_set
                )
                record[
                    "oci_sets_equal"
                ] = (
                    oci_set
                    == creation_oci_set
                )
                record[
                    "oci_leaf_count"
                ] = len(
                    oci_leaves
                )
                record[
                    "creation_leaf_count"
                ] = len(
                    creation_leaves
                )
                record[
                    "oci_max_recursion_depth"
                ] = max(
                    (
                        int(
                            item[
                                "recursion_depth"
                            ]
                        )
                        for item in oci_leaves
                    ),
                    default=0,
                )
                record[
                    "creation_max_recursion_depth"
                ] = max(
                    (
                        int(
                            item[
                                "recursion_depth"
                            ]
                        )
                        for item in creation_leaves
                    ),
                    default=0,
                )

                post_path = (
                    attempt_root
                    / "count_post.json"
                )

                post_payload = fetcher(
                    opencitations_count_url(
                        direction,
                        doi,
                    ),
                    headers=headers,
                    raw_path=post_path,
                    delay=0.40,
                )

                post_count = (
                    parse_opencitations_count(
                        post_payload
                    )
                )

                record[
                    "post_count"
                ] = post_count

                failures = []

                if pre_count != post_count:
                    failures.append(
                        "pre/post count disagreement "
                        f"{pre_count}!={post_count}"
                    )

                if len(
                    oci_rows
                ) != pre_count:
                    failures.append(
                        "OCI-axis row count "
                        f"{len(oci_rows)}!={pre_count}"
                    )

                if len(
                    creation_rows
                ) != pre_count:
                    failures.append(
                        "creation-axis row count "
                        f"{len(creation_rows)}!={pre_count}"
                    )

                if (
                    oci_row_set
                    != creation_row_set
                ):
                    failures.append(
                        "cross-axis complete-row "
                        "sets differ"
                    )

                if (
                    oci_set
                    != creation_oci_set
                ):
                    failures.append(
                        "cross-axis OCI sets differ"
                    )

                production_rows = (
                    oci_rows
                )

                accepted_status = (
                    "accepted"
                )

                source_status = (
                    "complete"
                )

                accepted_detail = (
                    "stable counts and exact "
                    "dual-axis row/OCI agreement"
                )

                provider_accepted = False

                if failures:
                    candidate = None

                    if (
                        direction == "forward"
                        and pre_count
                        == post_count
                    ):
                        candidate = (
                            build_opencitations_provider_candidate(
                                anchor=
                                    anchor,
                                direction=
                                    direction,
                                expected_count=
                                    pre_count,
                                oci_rows=
                                    oci_rows,
                                creation_rows=
                                    creation_rows,
                                attempt_root=
                                    attempt_root,
                            )
                        )

                    if candidate is not None:
                        record[
                            "provider_reconciliation_candidate"
                        ] = True

                        record[
                            "provider_reconciled_row_count"
                        ] = candidate[
                            "row_count"
                        ]

                        record[
                            "provider_reconciled_complete_row_sha256"
                        ] = candidate[
                            "complete_row_sha256"
                        ]

                        record[
                            "provider_reconciled_oci_set_sha256"
                        ] = candidate[
                            "oci_set_sha256"
                        ]

                        record[
                            "provider_alias_pair_count"
                        ] = candidate[
                            "alias_pair_count"
                        ]

                        record[
                            "provider_missing_row_count"
                        ] = candidate[
                            "missing_row_count"
                        ]

                        record[
                            "provider_discrepant_oci_count"
                        ] = candidate[
                            "discrepant_oci_count"
                        ]

                        (
                            attempt_root
                            / "provider_reconciliation_candidate.json"
                        ).write_text(
                            json.dumps(
                                candidate[
                                    "evidence"
                                ],
                                indent=2,
                                sort_keys=True,
                            )
                            + "\n",
                            encoding="utf-8",
                        )

                        directly_verified = (
                            verify_opencitations_provider_discrepancies(
                                anchor=
                                    anchor,
                                doi=
                                    doi,
                                candidate=
                                    candidate,
                                attempt_root=
                                    attempt_root,
                                raw_root=
                                    raw_root,
                                headers=
                                    headers,
                                fetcher=
                                    fetcher,
                                verification_cache=
                                    provider_direct_verification,
                                seen_discrepant_ocis=
                                    provider_seen_discrepant_ocis,
                            )
                        )

                        record[
                            "provider_direct_lookup_count"
                        ] = len(
                            provider_direct_verification
                        )

                        stable_three = False

                        if (
                            directly_verified
                            and len(
                                direction_attempt_records
                            )
                            >= 2
                        ):
                            previous = (
                                direction_attempt_records[
                                    -2:
                                ]
                            )

                            stable_three = all(
                                item.get(
                                    "provider_reconciliation_candidate"
                                )
                                is True
                                and item.get(
                                    "pre_count"
                                )
                                == pre_count
                                and item.get(
                                    "post_count"
                                )
                                == post_count
                                and item.get(
                                    "provider_reconciled_row_count"
                                )
                                == candidate[
                                    "row_count"
                                ]
                                and item.get(
                                    "provider_reconciled_complete_row_sha256"
                                )
                                == candidate[
                                    "complete_row_sha256"
                                ]
                                and item.get(
                                    "provider_reconciled_oci_set_sha256"
                                )
                                == candidate[
                                    "oci_set_sha256"
                                ]
                                for item in previous
                            )

                        all_seen_verified = (
                            set(
                                provider_direct_verification
                            )
                            ==
                            provider_seen_discrepant_ocis
                        )

                        if (
                            stable_three
                            and all_seen_verified
                        ):
                            provider_accepted = True

                            production_rows = (
                                candidate[
                                    "production_rows"
                                ]
                            )

                            accepted_status = (
                                "accepted_provider_reconciled"
                            )

                            source_status = (
                                "complete_provider_reconciled"
                            )

                            accepted_detail = (
                                "three forward snapshots produced "
                                "byte-identical OCI-plus-verified-"
                                "missing-work reconciliation; all "
                                "unique discrepant OCIs directly "
                                "verified"
                            )

                            record[
                                "provider_reconciliation"
                            ] = True

                            record[
                                "production_axis"
                            ] = (
                                "oci_plus_verified_creation_missing"
                            )

                            reconciliation_evidence = {
                                "status":
                                    accepted_status,
                                "anchor_id":
                                    anchor[
                                        "anchor_id"
                                    ],
                                "direction":
                                    direction,
                                "reported_count":
                                    pre_count,
                                "production_axis":
                                    record[
                                        "production_axis"
                                    ],
                                "reconciled_row_count":
                                    candidate[
                                        "row_count"
                                    ],
                                "reconciled_complete_row_sha256":
                                    candidate[
                                        "complete_row_sha256"
                                    ],
                                "reconciled_oci_set_sha256":
                                    candidate[
                                        "oci_set_sha256"
                                    ],
                                "stable_snapshot_attempts":
                                    [
                                        int(
                                            previous[
                                                0
                                            ][
                                                "snapshot_attempt"
                                            ]
                                        ),
                                        int(
                                            previous[
                                                1
                                            ][
                                                "snapshot_attempt"
                                            ]
                                        ),
                                        snapshot_attempt,
                                    ],
                                "unique_discrepant_ocis":
                                    sorted(
                                        provider_seen_discrepant_ocis
                                    ),
                                "direct_verification":
                                    {
                                        oci:
                                            provider_direct_verification[
                                                oci
                                            ]
                                        for oci in sorted(
                                            provider_direct_verification
                                        )
                                    },
                                "accepted_candidate":
                                    candidate[
                                        "evidence"
                                    ],
                            }

                            (
                                attempt_root
                                / "provider_reconciliation.json"
                            ).write_text(
                                json.dumps(
                                    reconciliation_evidence,
                                    indent=2,
                                    sort_keys=True,
                                )
                                + "\n",
                                encoding="utf-8",
                            )

                    if not provider_accepted:
                        raise OpenCitationsSnapshotRetryable(
                            f"{anchor['anchor_id']}: "
                            f"OpenCitations {direction} "
                            "snapshot reconciliation failed: "
                            + "; ".join(
                                failures
                            )
                        )

                else:
                    record[
                        "production_axis"
                    ] = "oci"

                record[
                    "status"
                ] = accepted_status

                record[
                    "retryable"
                ] = False

                record[
                    "response_files"
                ] = (
                    opencitations_attempt_response_files(
                        attempt_root
                    )
                )

                record[
                    "terminal_detail"
                ] = accepted_detail

                write_opencitations_snapshot_attempt(
                    attempt_root,
                    record,
                )

                direction_attempt_records.append(
                    dict(record)
                )
                snapshot_attempts.append(
                    dict(record)
                )

                oci_partition_leaves.extend(
                    oci_leaves
                )

                creation_partition_leaves.extend(
                    creation_leaves
                )

                (
                    direction_edges,
                    direction_neighbours,
                ) = (
                    opencitations_rows_to_outputs(
                        partition_rows=
                            production_rows,
                        anchor=
                            anchor,
                        direction=
                            direction,
                        doi=
                            doi,
                        wave=
                            wave,
                        output_root=
                            output_root,
                    )
                )

                edges.extend(
                    direction_edges
                )
                neighbours.extend(
                    direction_neighbours
                )

                statuses.append({
                    "wave":
                        wave,
                    "anchor_id":
                        anchor[
                            "anchor_id"
                        ],
                    "anchor_tool":
                        anchor[
                            "tool"
                        ],
                    "source":
                        "opencitations",
                    "direction":
                        direction,
                    "status":
                        source_status,
                    "reported_count":
                        pre_count,
                    "retrieved_count":
                        len(
                            production_rows
                        ),
                    "response_files":
                        sum(
                            int(
                                item[
                                    "response_files"
                                ]
                            )
                            for item in (
                                direction_attempt_records
                            )
                        ),
                    "terminal_detail":
                        (
                            accepted_detail
                            + "; accepted attempt "
                            + str(
                                snapshot_attempt
                            )
                        ),
                })

                direction_complete = True
                break

            except Exception as exc:
                message = str(
                    exc
                )

                recursion_ceiling = (
                    "partition recursion ceiling"
                    in message
                )

                retryable = (
                    isinstance(
                        exc,
                        OpenCitationsSnapshotRetryable,
                    )
                    or (
                        not recursion_ceiling
                        and caused_by_retryable_transport_error(
                            exc
                        )
                    )
                )

                record[
                    "status"
                ] = (
                    "retryable_failure"
                    if retryable
                    else "nonretryable_failure"
                )

                record[
                    "retryable"
                ] = retryable

                record[
                    "response_files"
                ] = (
                    opencitations_attempt_response_files(
                        attempt_root
                    )
                )

                record[
                    "terminal_detail"
                ] = message

                write_opencitations_snapshot_attempt(
                    attempt_root,
                    record,
                )

                direction_attempt_records.append(
                    dict(record)
                )
                snapshot_attempts.append(
                    dict(record)
                )

                if (
                    retryable
                    and snapshot_attempt
                    < maximum_snapshot_attempts
                ):
                    continue

                if retryable:
                    raise RuntimeError(
                        f"{anchor['anchor_id']}: "
                        f"OpenCitations {direction} "
                        "did not produce an acceptable "
                        "snapshot within "
                        f"{maximum_snapshot_attempts} "
                        "attempts. Last failure: "
                        f"{message}"
                    ) from exc

                raise

        if not direction_complete:
            raise RuntimeError(
                f"{anchor['anchor_id']}: "
                f"OpenCitations {direction} "
                "did not reach a terminal state"
            )

    return (
        edges,
        neighbours,
        statuses,
        oci_partition_leaves,
        creation_partition_leaves,
        snapshot_attempts,
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
        "complete_provider_reconciled",
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
    all_oc_creation_partition_leaves: list[dict] = []
    all_oc_snapshot_attempts: list[dict] = []

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
            creation_partition_leaves,
            snapshot_attempts,
        ) = retrieve_opencitations_dual_axis(
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
        all_oc_creation_partition_leaves.extend(
            creation_partition_leaves
        )
        all_oc_snapshot_attempts.extend(
            snapshot_attempts
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
            int(row["snapshot_attempt"]),
            int(row["leaf_order"]),
        )
    )

    all_oc_creation_partition_leaves.sort(
        key=lambda row: (
            int(row["wave"]),
            row["anchor_id"],
            row["direction"],
            int(row["snapshot_attempt"]),
            int(row["leaf_order"]),
        )
    )

    all_oc_snapshot_attempts.sort(
        key=lambda row: (
            int(row["wave"]),
            row["anchor_id"],
            row["direction"],
            int(row["snapshot_attempt"]),
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

    write_tsv(
        args.output
        / "opencitations_creation_partition_leaves.tsv",
        OPENCITATIONS_CREATION_PARTITION_FIELDS,
        all_oc_creation_partition_leaves,
    )

    write_tsv(
        args.output
        / "opencitations_snapshot_attempts.tsv",
        OPENCITATIONS_SNAPSHOT_FIELDS,
        all_oc_snapshot_attempts,
    )

    manifest = {
        "schema_version": 3,
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
        "opencitations_oci_partition_leaf_rows":
            len(all_oc_partition_leaves),
        "opencitations_creation_partition_leaf_rows":
            len(all_oc_creation_partition_leaves),
        "opencitations_snapshot_attempt_rows":
            len(all_oc_snapshot_attempts),
        "opencitations_partition_max_suffix_digits":
            OPENCITATIONS_PARTITION_MAX_SUFFIX_DIGITS,
        "opencitations_creation_partition_max_prefix_characters":
            OPENCITATIONS_CREATION_PARTITION_MAX_PREFIX_CHARACTERS,
        "opencitations_max_snapshot_attempts":
            OPENCITATIONS_MAX_SNAPSHOT_ATTEMPTS,
        "opencitations_snapshot_reconciliation":
            "dual_axis_exact_or_verified_forward_oci_plus_creation_missing",
        "opencitations_canonical_production_axis":
            "oci_or_oci_plus_verified_creation_missing",
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
        "opencitations_creation_partition_leaves.tsv",
        "opencitations_snapshot_attempts.tsv",
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
