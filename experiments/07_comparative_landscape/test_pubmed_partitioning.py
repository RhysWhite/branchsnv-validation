#!/usr/bin/env python3
"""Offline regression tests for Experiment 07 PubMed EDAT partitioning."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import urllib.parse
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parent
    / "retrieve_high_recall_corpus.py"
)

spec = importlib.util.spec_from_file_location(
    "high_recall_retriever",
    SCRIPT,
)

if spec is None or spec.loader is None:
    raise RuntimeError("Could not load high-recall retriever")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


QUERY = {
    "query_id": "TEST",
    "query_family": "offline_test",
    "pubmed_query": "(example[Title/Abstract])",
}


def parse_url(url: str):
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.parse_qs(parsed.query)


def fake_summary_payload(ids):
    result = {"uids": list(ids)}

    for pmid in ids:
        result[str(pmid)] = {
            "uid": str(pmid),
            "title": f"Test publication {pmid}",
            "pubdate": "2020",
            "articleids": [
                {
                    "idtype": "pubmed",
                    "value": str(pmid),
                }
            ],
        }

    return {"result": result}


class Scenario:
    def __init__(
        self,
        *,
        envelope_mismatch=False,
        child_mismatch=False,
        duplicate=False,
    ):
        self.envelope_mismatch = envelope_mismatch
        self.child_mismatch = child_mismatch
        self.duplicate = duplicate
        self.calls = []

    def fetch_json(
        self,
        url,
        *,
        headers,
        delay,
        raw_path,
    ):
        del headers, delay

        params = parse_url(url)
        self.calls.append((url, Path(raw_path)))

        raw_path = Path(raw_path)
        raw_path.parent.mkdir(parents=True, exist_ok=True)

        # --------------------------------------------------
        # ESummary
        # --------------------------------------------------
        if "esummary.fcgi" in url:
            ids = params["id"][0].split(",")
            payload = fake_summary_payload(ids)

        # --------------------------------------------------
        # ESearch
        # --------------------------------------------------
        elif "esearch.fcgi" in url:
            has_dates = "datetype" in params
            count_only = params.get("rettype") == ["count"]

            # Original unbounded scientific query.
            if not has_dates:
                count = 10001
                ids = [str(i) for i in range(1, 10001)]

            # EDAT envelope / recursively partitioned calls.
            else:
                mindate = params["mindate"][0]
                maxdate = params["maxdate"][0]

                # Full transport envelope.
                if (
                    mindate == "1000/01/01"
                    and maxdate == "3000/12/31"
                ):
                    count = (
                        9999
                        if self.envelope_mismatch
                        else 10001
                    )
                    ids = []

                # The deterministic first bisection produces one
                # interval ending before 2001 and one beginning
                # around 2000/2001. We only need two disjoint
                # terminal sets for this offline test.
                elif maxdate < "2001/01/01":
                    count = 5000
                    ids = [str(i) for i in range(1, 5001)]

                else:
                    count = 5001
                    ids = [str(i) for i in range(5001, 10002)]

                    if self.child_mismatch and count_only:
                        count = 5000

                    if self.duplicate and not count_only:
                        # Maintain 5,001 returned IDs but duplicate
                        # PMID 5000 across the two terminal leaves.
                        ids[0] = "5000"

                if count_only:
                    ids = []

            payload = {
                "esearchresult": {
                    "count": str(count),
                    "idlist": ids,
                }
            }

        else:
            raise RuntimeError(f"Unexpected URL: {url}")

        raw_path.write_text(
            json.dumps(payload, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        return payload


def run_scenario(scenario: Scenario):
    original = module.fetch_json
    module.fetch_json = scenario.fetch_json

    try:
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw"

            return module.retrieve_pubmed(
                QUERY,
                raw_root=raw,
                email="offline@example.invalid",
                user_agent="offline-test",
            )
    finally:
        module.fetch_json = original


def expect_failure(
    name: str,
    scenario: Scenario,
    expected_fragment: str,
):
    try:
        run_scenario(scenario)
    except RuntimeError as exc:
        message = str(exc)

        if expected_fragment not in message:
            raise AssertionError(
                f"{name}: wrong failure\n"
                f"expected fragment: {expected_fragment!r}\n"
                f"observed: {message!r}"
            ) from exc

        print(f"PASS | {name}")
        return

    raise AssertionError(
        f"{name}: expected RuntimeError but retrieval succeeded"
    )


def main():
    # ------------------------------------------------------
    # Successful >10,000-record partition.
    # ------------------------------------------------------
    rows, summary = run_scenario(Scenario())

    assert summary["reported_count"] == 10001
    assert summary["retrieved_count"] == 10001
    assert summary["complete"] is True

    pmids = [row["pmid"] for row in rows]

    assert len(pmids) == 10001
    assert len(set(pmids)) == 10001
    assert set(pmids) == {
        str(i)
        for i in range(1, 10002)
    }

    print("PASS | >10,000-record EDAT partition retrieves complete PMID set")

    # ------------------------------------------------------
    # Lossy transport envelope must fail closed.
    # ------------------------------------------------------
    expect_failure(
        "EDAT envelope mismatch fails closed",
        Scenario(envelope_mismatch=True),
        "Partition envelope is not lossless",
    )

    # ------------------------------------------------------
    # Parent/child counts must reconcile.
    # ------------------------------------------------------
    expect_failure(
        "child-count mismatch fails closed",
        Scenario(child_mismatch=True),
        "EDAT child counts do not reconcile",
    )

    # ------------------------------------------------------
    # Non-overlapping leaves may not produce duplicate PMIDs.
    # ------------------------------------------------------
    expect_failure(
        "duplicate PMID across leaves fails closed",
        Scenario(duplicate=True),
        "duplicate PMID occurrence",
    )

    print()
    print("PASS | all offline PubMed partition regression tests")


if __name__ == "__main__":
    main()
