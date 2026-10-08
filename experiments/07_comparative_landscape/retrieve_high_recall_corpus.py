#!/usr/bin/env python3
"""Retrieve the prespecified Experiment 07 high-recall expansion corpus.

Sources:
  - PubMed E-utilities
  - OpenAlex Works API
  - bio.tools registry API

The script:
  * reads the frozen high_recall_queries.tsv;
  * retrieves every result for every query;
  * preserves raw metadata responses;
  * records source/query provenance for every hit;
  * produces a conservative deduplicated record table;
  * records retrieval metadata and exact software/query hashes; and
  * writes SHA-256 checksums for the complete retrieval corpus.

No API credentials are written to output files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
OPENALEX_API_ROOT = "https://api.openalex.org/"
BIOTOOLS_TOOLS = "https://bio.tools/api/tool/"

OPENALEX_SELECT = ",".join([
    "id",
    "doi",
    "title",
    "display_name",
    "publication_year",
    "publication_date",
    "type",
    "ids",
    "referenced_works",
    "cited_by_count",
    "primary_location",
])

CANDIDATE_FIELDS = [
    "source",
    "query_id",
    "query_family",
    "source_record_id",
    "entity_type",
    "title_or_name",
    "year",
    "doi",
    "pmid",
    "openalex_id",
    "biotools_id",
    "source_url",
]

COUNT_FIELDS = [
    "source",
    "query_id",
    "query_family",
    "reported_count",
    "retrieved_count",
    "response_files",
    "complete",
]

DEDUP_FIELDS = [
    "dedup_key",
    "entity_type",
    "title_or_name",
    "year",
    "doi",
    "pmid",
    "sources",
    "query_ids",
    "source_record_ids",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        text=True,
    ).strip()


def build_url(base: str, params: dict[str, str | int]) -> str:
    return base + "?" + urllib.parse.urlencode(params)


def request_bytes(
    url: str,
    *,
    headers: dict[str, str],
    delay: float,
    retries: int = 6,
) -> bytes:
    """GET with bounded exponential retry for transient HTTP/network errors."""

    last_error: Exception | None = None

    for attempt in range(retries):
        if delay:
            time.sleep(delay)

        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return response.read()

        except urllib.error.HTTPError as exc:
            last_error = exc

            if exc.code not in {429, 500, 502, 503, 504}:
                raise

        except urllib.error.URLError as exc:
            last_error = exc

        if attempt + 1 < retries:
            time.sleep(min(2 ** attempt, 30))

    raise RuntimeError(
        f"Request failed after {retries} attempts: {url}"
    ) from last_error


def fetch_json(
    url: str,
    *,
    headers: dict[str, str],
    delay: float,
    raw_path: Path,
) -> dict:
    raw = request_bytes(url, headers=headers, delay=delay)

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(raw)

    try:
        value = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(
            f"Invalid JSON returned for {url}; raw response: {raw_path}"
        ) from exc

    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object from {url}")

    return value


def normalise_doi(value: str | None) -> str:
    if not value:
        return ""
    value = str(value).strip()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.I)
    return value.lower()


def normalise_pmid(value: str | None) -> str:
    if not value:
        return ""
    value = str(value).strip()
    match = re.search(r"(\d+)(?:/)?$", value)
    return match.group(1) if match else value


def normalise_title(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^\w\s]", "", value)
    return value.strip()


def first_four_digit_year(value: str | None) -> str:
    if not value:
        return ""
    m = re.search(r"\b(18|19|20|21)\d{2}\b", str(value))
    return m.group(0) if m else ""


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def read_queries(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        rows = list(reader)

    expected = [
        "query_id",
        "concept",
        "query_family",
        "pubmed_query",
        "openalex_parameter",
        "openalex_query",
        "biotools_query",
    ]

    if reader.fieldnames != expected:
        raise RuntimeError(
            f"Unexpected search-query schema: {reader.fieldnames}"
        )

    ids = [r["query_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate query IDs")

    return rows


def pubmed_article_ids(item: dict) -> tuple[str, str]:
    doi = ""
    pmid = ""

    for entry in item.get("articleids", []) or []:
        if not isinstance(entry, dict):
            continue

        kind = str(entry.get("idtype", "")).lower()
        value = str(entry.get("value", "")).strip()

        if kind == "doi" and not doi:
            doi = normalise_doi(value)
        elif kind in {"pubmed", "pmid"} and not pmid:
            pmid = normalise_pmid(value)

    return doi, pmid


def biotools_publication_ids(tool: dict) -> tuple[str, str]:
    doi = ""
    pmid = ""

    for pub in tool.get("publication", []) or []:
        if not isinstance(pub, dict):
            continue

        if not doi and pub.get("doi"):
            doi = normalise_doi(pub.get("doi"))

        if not pmid and pub.get("pmid"):
            pmid = normalise_pmid(pub.get("pmid"))

    return doi, pmid


def retrieve_pubmed(
    query: dict[str, str],
    *,
    raw_root: Path,
    email: str,
    user_agent: str,
) -> tuple[list[dict], dict]:
    """Retrieve one PubMed query, partitioning by EDAT above 10,000 hits.

    EDAT is used only as a deterministic transport partition. The scientific
    query expression is never modified.
    """

    qid = query["query_id"]
    scientific_term = query["pubmed_query"]
    max_esearch_ids = 10000

    # Broad transport envelope only. Equality with the original unbounded
    # count is required before partitioned retrieval can proceed.
    envelope_start = date(1000, 1, 1)
    envelope_end = date(3000, 12, 31)

    response_files = 0

    def fetch_esearch(
        *,
        raw_name: str,
        mindate: date | None = None,
        maxdate: date | None = None,
        count_only: bool = False,
    ) -> tuple[int, list[str]]:
        nonlocal response_files

        if (mindate is None) != (maxdate is None):
            raise RuntimeError(
                f"{qid}: PubMed EDAT bounds must be supplied together"
            )

        params: dict[str, str | int] = {
            "db": "pubmed",
            "term": scientific_term,
            "retmode": "json",
            "retmax": 0 if count_only else max_esearch_ids,
            "tool": "branchsnv_validation",
            "email": email,
        }

        if count_only:
            params["rettype"] = "count"

        if mindate is not None and maxdate is not None:
            params["datetype"] = "edat"
            params["mindate"] = mindate.strftime("%Y/%m/%d")
            params["maxdate"] = maxdate.strftime("%Y/%m/%d")

        url = build_url(PUBMED_ESEARCH, params)

        payload = fetch_json(
            url,
            headers={"User-Agent": user_agent},
            delay=0.36,
            raw_path=raw_root / "pubmed" / raw_name,
        )

        response_files += 1

        result = payload.get("esearchresult", {})
        reported_count = int(result.get("count", 0))
        ids = [str(x) for x in result.get("idlist", [])]

        if count_only:
            if ids:
                raise RuntimeError(
                    f"{qid}: count-only PubMed ESearch unexpectedly "
                    f"returned {len(ids)} IDs"
                )
            return reported_count, []

        if reported_count <= max_esearch_ids:
            if len(ids) != reported_count:
                raise RuntimeError(
                    f"{qid}: PubMed reported {reported_count} records "
                    f"but returned {len(ids)} IDs"
                )
        else:
            # ESearch can expose only the first 10,000 PubMed UIDs.
            if len(ids) > max_esearch_ids:
                raise RuntimeError(
                    f"{qid}: PubMed returned more than "
                    f"{max_esearch_ids} IDs in one ESearch response"
                )

        return reported_count, ids

    # --------------------------------------------------------
    # Original unmodified search.
    # --------------------------------------------------------

    reported, initial_ids = fetch_esearch(
        raw_name=f"{qid}_esearch.json",
    )

    partition_metadata: dict | None = None

    if reported <= max_esearch_ids:
        ids = initial_ids

    else:
        # ----------------------------------------------------
        # Verify that the broad EDAT envelope is lossless.
        # ----------------------------------------------------

        envelope_count, _ = fetch_esearch(
            raw_name=f"{qid}_edat_envelope_count.json",
            mindate=envelope_start,
            maxdate=envelope_end,
            count_only=True,
        )

        if envelope_count != reported:
            raise RuntimeError(
                f"{qid}: unbounded PubMed count is {reported:,}, "
                f"but EDAT envelope "
                f"{envelope_start.isoformat()}.."
                f"{envelope_end.isoformat()} contains "
                f"{envelope_count:,}. "
                "Partition envelope is not lossless."
            )

        nodes: list[dict] = []
        leaves: list[dict] = []

        def interval_label(start_date: date, end_date: date) -> str:
            return (
                f"{start_date.strftime('%Y%m%d')}_"
                f"{end_date.strftime('%Y%m%d')}"
            )

        def retrieve_interval(
            start_date: date,
            end_date: date,
            interval_count: int,
            *,
            depth: int,
        ) -> list[str]:
            """Recursively retrieve one inclusive EDAT interval."""

            if start_date > end_date:
                raise RuntimeError(
                    f"{qid}: invalid EDAT interval "
                    f"{start_date}..{end_date}"
                )

            node = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "count": interval_count,
                "depth": depth,
                "terminal": interval_count <= max_esearch_ids,
            }
            nodes.append(node)

            if interval_count <= max_esearch_ids:
                label = interval_label(start_date, end_date)

                leaf_reported, leaf_ids = fetch_esearch(
                    raw_name=f"{qid}_edat_{label}_esearch.json",
                    mindate=start_date,
                    maxdate=end_date,
                    count_only=False,
                )

                if leaf_reported != interval_count:
                    raise RuntimeError(
                        f"{qid}: EDAT leaf {start_date}..{end_date} "
                        f"was counted as {interval_count:,} records "
                        f"but retrieval reported {leaf_reported:,}"
                    )

                if len(leaf_ids) != interval_count:
                    raise RuntimeError(
                        f"{qid}: EDAT leaf {start_date}..{end_date} "
                        f"expected {interval_count:,} IDs but returned "
                        f"{len(leaf_ids):,}"
                    )

                leaves.append({
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "count": interval_count,
                })

                return leaf_ids

            if start_date == end_date:
                raise RuntimeError(
                    f"{qid}: single-day EDAT interval "
                    f"{start_date.isoformat()} contains "
                    f"{interval_count:,} records, exceeding the "
                    f"{max_esearch_ids:,}-record ESearch limit"
                )

            midpoint = start_date + (
                (end_date - start_date) // 2
            )

            left_start = start_date
            left_end = midpoint
            right_start = midpoint + timedelta(days=1)
            right_end = end_date

            left_label = interval_label(left_start, left_end)
            right_label = interval_label(right_start, right_end)

            left_count, _ = fetch_esearch(
                raw_name=f"{qid}_edat_{left_label}_count.json",
                mindate=left_start,
                maxdate=left_end,
                count_only=True,
            )

            right_count, _ = fetch_esearch(
                raw_name=f"{qid}_edat_{right_label}_count.json",
                mindate=right_start,
                maxdate=right_end,
                count_only=True,
            )

            if left_count + right_count != interval_count:
                raise RuntimeError(
                    f"{qid}: EDAT child counts do not reconcile for "
                    f"{start_date}..{end_date}: "
                    f"{left_count:,} + {right_count:,} != "
                    f"{interval_count:,}"
                )

            left_ids = retrieve_interval(
                left_start,
                left_end,
                left_count,
                depth=depth + 1,
            )

            right_ids = retrieve_interval(
                right_start,
                right_end,
                right_count,
                depth=depth + 1,
            )

            return left_ids + right_ids

        ids = retrieve_interval(
            envelope_start,
            envelope_end,
            envelope_count,
            depth=0,
        )

        leaf_count_sum = sum(
            int(leaf["count"])
            for leaf in leaves
        )

        if leaf_count_sum != reported:
            raise RuntimeError(
                f"{qid}: terminal EDAT counts sum to "
                f"{leaf_count_sum:,}, expected {reported:,}"
            )

        if len(ids) != reported:
            raise RuntimeError(
                f"{qid}: partition retrieval returned "
                f"{len(ids):,} PMIDs, expected {reported:,}"
            )

        unique_ids = set(ids)

        if len(unique_ids) != reported:
            duplicate_count = len(ids) - len(unique_ids)
            raise RuntimeError(
                f"{qid}: partition retrieval contains "
                f"{duplicate_count:,} duplicate PMID occurrence(s); "
                "non-overlapping EDAT intervals must be disjoint"
            )

        partition_metadata = {
            "schema_version": 1,
            "query_id": qid,
            "partition_field": "edat",
            "scientific_query_modified": False,
            "unbounded_reported_count": reported,
            "envelope": {
                "start": envelope_start.isoformat(),
                "end": envelope_end.isoformat(),
                "reported_count": envelope_count,
            },
            "max_ids_per_esearch": max_esearch_ids,
            "node_count": len(nodes),
            "leaf_count": len(leaves),
            "terminal_count_sum": leaf_count_sum,
            "retrieved_pmid_count": len(ids),
            "unique_pmid_count": len(unique_ids),
            "nodes": nodes,
            "leaves": leaves,
        }

        partition_path = (
            raw_root
            / "pubmed"
            / f"{qid}_edat_partition_metadata.json"
        )

        partition_path.parent.mkdir(parents=True, exist_ok=True)

        with partition_path.open("w", encoding="utf-8") as fh:
            json.dump(
                partition_metadata,
                fh,
                indent=2,
                sort_keys=True,
            )
            fh.write("\n")

    # Sorting makes downstream output independent of partition traversal.
    ids = sorted(ids, key=int)

    if len(ids) != reported:
        raise RuntimeError(
            f"{qid}: final PubMed PMID count is {len(ids):,}; "
            f"expected {reported:,}"
        )

    if len(set(ids)) != reported:
        raise RuntimeError(
            f"{qid}: final PubMed PMID set is not unique"
        )

    # --------------------------------------------------------
    # Retrieve summaries exactly as before.
    # --------------------------------------------------------

    candidates: list[dict] = []

    for batch_number, start in enumerate(
        range(0, len(ids), 200),
        start=1,
    ):
        batch = ids[start:start + 200]

        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "json",
            "tool": "branchsnv_validation",
            "email": email,
        }

        summary_url = build_url(PUBMED_ESUMMARY, params)

        summary = fetch_json(
            summary_url,
            headers={"User-Agent": user_agent},
            delay=0.36,
            raw_path=(
                raw_root
                / "pubmed"
                / f"{qid}_esummary_{batch_number:04d}.json"
            ),
        )

        response_files += 1
        result_obj = summary.get("result", {})

        for pmid in batch:
            item = result_obj.get(pmid)

            if not isinstance(item, dict):
                raise RuntimeError(
                    f"{qid}: missing PubMed summary for PMID {pmid}"
                )

            doi, item_pmid = pubmed_article_ids(item)
            item_pmid = item_pmid or pmid

            candidates.append({
                "source": "pubmed",
                "query_id": qid,
                "query_family": query["query_family"],
                "source_record_id": pmid,
                "entity_type": "publication",
                "title_or_name": str(item.get("title", "")).strip(),
                "year": first_four_digit_year(item.get("pubdate")),
                "doi": doi,
                "pmid": item_pmid,
                "openalex_id": "",
                "biotools_id": "",
                "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })

    if len(candidates) != reported:
        raise RuntimeError(
            f"{qid}: PubMed candidate count is "
            f"{len(candidates):,}; expected {reported:,}"
        )

    return candidates, {
        "source": "pubmed",
        "query_id": qid,
        "query_family": query["query_family"],
        "reported_count": reported,
        "retrieved_count": len(candidates),
        "response_files": response_files,
        "complete": reported == len(candidates),
    }



def retrieve_openalex(
    query: dict[str, str],
    *,
    raw_root: Path,
    api_key: str,
    user_agent: str,
) -> tuple[list[dict], dict]:

    qid = query["query_id"]
    parameter = query["openalex_parameter"]

    if parameter != "oql":
        raise RuntimeError(
            f"{qid}: expected OpenAlex OQL parameter; observed {parameter}"
        )

    cursor = "*"
    page_number = 0
    reported: int | None = None
    candidates: list[dict] = []

    while cursor:
        page_number += 1

        params = {
            "oql": query["openalex_query"],
            "per-page": 100,
            "cursor": cursor,
            "select": OPENALEX_SELECT,
        }

        url = build_url(OPENALEX_API_ROOT, params)

        payload = fetch_json(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": user_agent,
            },
            delay=0.12,
            raw_path=(
                raw_root
                / "openalex"
                / f"{qid}_page_{page_number:04d}.json"
            ),
        )

        meta = payload.get("meta", {})

        if reported is None:
            reported = int(meta.get("count", 0))

        results = payload.get("results", [])

        if not isinstance(results, list):
            raise RuntimeError(f"{qid}: invalid OpenAlex results payload")

        for work in results:
            if not isinstance(work, dict):
                continue

            oid = str(work.get("id", "")).strip()
            ids = work.get("ids") or {}

            pmid = ""
            if isinstance(ids, dict):
                pmid = normalise_pmid(ids.get("pmid"))

            doi = normalise_doi(work.get("doi"))

            candidates.append({
                "source": "openalex",
                "query_id": qid,
                "query_family": query["query_family"],
                "source_record_id": oid.rsplit("/", 1)[-1],
                "entity_type": "publication",
                "title_or_name": str(
                    work.get("title")
                    or work.get("display_name")
                    or ""
                ).strip(),
                "year": str(work.get("publication_year") or ""),
                "doi": doi,
                "pmid": pmid,
                "openalex_id": oid,
                "biotools_id": "",
                "source_url": oid,
            })

        next_cursor = meta.get("next_cursor")

        if not results:
            cursor = None
        elif next_cursor:
            cursor = str(next_cursor)
        else:
            cursor = None

    reported = reported or 0

    if len(candidates) != reported:
        raise RuntimeError(
            f"{qid}: OpenAlex reported {reported} records but "
            f"{len(candidates)} were retrieved."
        )

    return candidates, {
        "source": "openalex",
        "query_id": qid,
        "query_family": query["query_family"],
        "reported_count": reported,
        "retrieved_count": len(candidates),
        "response_files": page_number,
        "complete": reported == len(candidates),
    }


def retrieve_biotools(
    query: dict[str, str],
    *,
    raw_root: Path,
    user_agent: str,
) -> tuple[list[dict], dict]:

    qid = query["query_id"]
    per_page = 50

    page = 1
    reported: int | None = None
    candidates: list[dict] = []

    while True:
        params = {
            "q": query["biotools_query"],
            "page": page,
            "per_page": per_page,
            "format": "json",
            "sort": "name",
            "ord": "asc",
        }

        url = build_url(BIOTOOLS_TOOLS, params)

        payload = fetch_json(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": user_agent,
            },
            delay=0.15,
            raw_path=(
                raw_root
                / "biotools"
                / f"{qid}_page_{page:04d}.json"
            ),
        )

        if reported is None:
            reported = int(payload.get("count", 0))

        tools = payload.get("list", [])

        if not isinstance(tools, list):
            raise RuntimeError(f"{qid}: invalid bio.tools list payload")

        for tool in tools:
            if not isinstance(tool, dict):
                continue

            bid = str(tool.get("biotoolsID", "")).strip()
            doi, pmid = biotools_publication_ids(tool)

            candidates.append({
                "source": "biotools",
                "query_id": qid,
                "query_family": query["query_family"],
                "source_record_id": bid,
                "entity_type": "software_registry",
                "title_or_name": str(tool.get("name", "")).strip(),
                "year": "",
                "doi": doi,
                "pmid": pmid,
                "openalex_id": "",
                "biotools_id": bid,
                "source_url": (
                    f"https://bio.tools/{bid}" if bid else ""
                ),
            })

        if not payload.get("next"):
            break

        page += 1

    reported = reported or 0

    if len(candidates) != reported:
        raise RuntimeError(
            f"{qid}: bio.tools reported {reported} records but "
            f"{len(candidates)} were retrieved."
        )

    return candidates, {
        "source": "biotools",
        "query_id": qid,
        "query_family": query["query_family"],
        "reported_count": reported,
        "retrieved_count": len(candidates),
        "response_files": page,
        "complete": reported == len(candidates),
    }


def dedup_key(row: dict) -> str:
    if row["entity_type"] == "software_registry":
        bid = row["biotools_id"].casefold().strip()
        if bid:
            return f"biotools:{bid}"

    doi = normalise_doi(row.get("doi"))
    if doi:
        return f"doi:{doi}"

    pmid = normalise_pmid(row.get("pmid"))
    if pmid:
        return f"pmid:{pmid}"

    title = normalise_title(row.get("title_or_name", ""))
    year = str(row.get("year", "")).strip()

    if title:
        return f"title:{title}|year:{year}"

    return (
        f"source:{row['source']}|"
        f"id:{row['source_record_id']}"
    )


def make_deduplicated(rows: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)

    for row in rows:
        groups[dedup_key(row)].append(row)

    output: list[dict] = []

    for key in sorted(groups):
        group = groups[key]

        exemplar = sorted(
            group,
            key=lambda r: (
                0 if r["source"] == "pubmed" else
                1 if r["source"] == "openalex" else
                2,
                r["title_or_name"],
            ),
        )[0]

        doi = next((r["doi"] for r in group if r["doi"]), "")
        pmid = next((r["pmid"] for r in group if r["pmid"]), "")
        year = next((r["year"] for r in group if r["year"]), "")

        output.append({
            "dedup_key": key,
            "entity_type": exemplar["entity_type"],
            "title_or_name": exemplar["title_or_name"],
            "year": year,
            "doi": doi,
            "pmid": pmid,
            "sources": ";".join(sorted({r["source"] for r in group})),
            "query_ids": ";".join(sorted({r["query_id"] for r in group})),
            "source_record_ids": ";".join(sorted({
                f"{r['source']}:{r['source_record_id']}"
                for r in group
            })),
        })

    return output


def write_corpus_checksums(out: Path) -> None:
    checksum_file = out / "corpus_checksums.sha256"

    paths = sorted(
        p for p in out.rglob("*")
        if p.is_file() and p != checksum_file
    )

    with checksum_file.open("w", encoding="utf-8", newline="") as fh:
        for path in paths:
            rel = path.relative_to(out)
            fh.write(f"{sha256_file(path)}  {rel.as_posix()}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--queries",
        default=(
            "experiments/07_comparative_landscape/"
            "high_recall_queries.tsv"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=(
            "results/07_comparative_landscape/"
            "high_recall_search"
        ),
    )
    args = parser.parse_args()

    repo = Path.cwd().resolve()
    query_path = (repo / args.queries).resolve()
    out = (repo / args.output_dir).resolve()

    if out.exists():
        raise SystemExit(
            f"ERROR: output directory already exists: {out}"
        )

    api_key = os.environ.get("OPENALEX_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "ERROR: OPENALEX_API_KEY is not set. "
            "Formal retrieval will not run partially."
        )

    email = os.environ.get("NCBI_EMAIL", "").strip()
    if not email:
        raise SystemExit(
            "ERROR: NCBI_EMAIL is not set. "
            "Set it before formal retrieval."
        )

    script_path = Path(__file__).resolve()
    queries = read_queries(query_path)

    if len(queries) != 5:
        raise SystemExit(
            f"ERROR: expected 5 frozen high-recall queries; found {len(queries)}"
        )

    out.mkdir(parents=True)
    raw_root = out / "raw"
    started = utc_now()

    user_agent = (
        f"BRANCHSNV-validation/Experiment07 "
        f"(contact: {email})"
    )

    candidates: list[dict] = []
    counts: list[dict] = []

    try:
        for query in queries:
            qid = query["query_id"]
            print(f"[{qid}] PubMed", flush=True)
            rows, summary = retrieve_pubmed(
                query,
                raw_root=raw_root,
                email=email,
                user_agent=user_agent,
            )
            candidates.extend(rows)
            counts.append(summary)

            print(f"[{qid}] OpenAlex", flush=True)
            rows, summary = retrieve_openalex(
                query,
                raw_root=raw_root,
                api_key=api_key,
                user_agent=user_agent,
            )
            candidates.extend(rows)
            counts.append(summary)

            print(f"[{qid}] bio.tools", flush=True)
            rows, summary = retrieve_biotools(
                query,
                raw_root=raw_root,
                user_agent=user_agent,
            )
            candidates.extend(rows)
            counts.append(summary)

        if not all(bool(row["complete"]) for row in counts):
            raise RuntimeError("One or more retrievals were incomplete")

        candidates.sort(
            key=lambda r: (
                r["source"],
                r["query_id"],
                r["source_record_id"],
            )
        )

        counts.sort(
            key=lambda r: (
                r["source"],
                r["query_id"],
            )
        )

        deduplicated = make_deduplicated(candidates)

        write_tsv(
            out / "search_counts.tsv",
            COUNT_FIELDS,
            counts,
        )

        write_tsv(
            out / "candidate_records.tsv",
            CANDIDATE_FIELDS,
            candidates,
        )

        write_tsv(
            out / "deduplicated_records.tsv",
            DEDUP_FIELDS,
            deduplicated,
        )

        manifest = {
            "schema_version": 1,
            "experiment": "07_comparative_landscape_high_recall_search",
            "status": "COMPLETE",
            "started_utc": started,
            "completed_utc": utc_now(),
            "repository_commit": git_head(repo),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "retrieval_script": str(script_path.relative_to(repo)),
            "retrieval_script_sha256": sha256_file(script_path),
            "search_queries": str(query_path.relative_to(repo)),
            "search_queries_sha256": sha256_file(query_path),
            "query_count": len(queries),
            "sources": [
                "PubMed",
                "OpenAlex",
                "bio.tools",
            ],
            "openalex_authentication": "Bearer API key used; key not recorded",
            "ncbi_contact_email_supplied": True,
            "raw_metadata_only": True,
            "candidate_record_rows": len(candidates),
            "deduplicated_record_rows": len(deduplicated),
            "source_query_retrievals": len(counts),
            "all_retrievals_complete": True,
        }

        with (out / "retrieval_manifest.json").open(
            "w",
            encoding="utf-8",
        ) as fh:
            json.dump(
                manifest,
                fh,
                indent=2,
                sort_keys=True,
            )
            fh.write("\n")

        write_corpus_checksums(out)

    except Exception:
        failure = {
            "schema_version": 1,
            "experiment": "07_comparative_landscape_high_recall_search",
            "status": "FAILED",
            "started_utc": started,
            "failed_utc": utc_now(),
            "repository_commit": git_head(repo),
            "python_version": platform.python_version(),
            "retrieval_script_sha256": sha256_file(script_path),
            "search_queries_sha256": sha256_file(query_path),
        }

        with (out / "FAILED.json").open(
            "w",
            encoding="utf-8",
        ) as fh:
            json.dump(failure, fh, indent=2, sort_keys=True)
            fh.write("\n")

        write_corpus_checksums(out)
        raise

    print()
    print("PASS | high-recall search retrieval complete")
    print(f"candidate rows     = {len(candidates):,}")
    print(f"deduplicated rows  = {len(deduplicated):,}")
    print(f"source/query pulls = {len(counts):,}")
    print(f"output             = {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
