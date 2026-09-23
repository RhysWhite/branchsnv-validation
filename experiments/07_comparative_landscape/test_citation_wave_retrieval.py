#!/usr/bin/env python3
"""
Offline tests for Experiment 07 citation-wave retrieval.

No network access is permitted by these tests.
"""

from __future__ import annotations

import importlib.util
import http.client
import json
import re
import tempfile
import urllib.parse

from pathlib import Path
from unittest.mock import patch


ROOT = Path(
    "experiments/07_comparative_landscape"
)

SCRIPT = ROOT / "retrieve_citation_wave.py"


spec = importlib.util.spec_from_file_location(
    "citation_retriever",
    SCRIPT,
)

if spec is None or spec.loader is None:
    raise RuntimeError(
        "Could not import retriever"
    )

mod = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(mod)


def assert_equal(
    observed,
    expected,
    label,
):
    if observed != expected:
        raise AssertionError(
            f"{label}: "
            f"{observed!r} != {expected!r}"
        )


# ------------------------------------------------------------
# Identifier normalisation.
# ------------------------------------------------------------

assert_equal(
    mod.normalise_doi(
        "https://doi.org/10.1093/VE/VEX042"
    ),
    "10.1093/ve/vex042",
    "DOI normalisation",
)

assert_equal(
    mod.normalise_pmid(
        "pmid:123456"
    ),
    "123456",
    "PMID normalisation",
)

assert_equal(
    mod.normalise_openalex_id(
        "https://openalex.org/w123456"
    ),
    "W123456",
    "OpenAlex normalisation",
)

# ------------------------------------------------------------
# OpenCitations PID parsing.
# ------------------------------------------------------------

bundle = mod.parse_pid_bundle(
    "[oci] => "
    "omid:br/06101801781 "
    "doi:10.7717/peerj-cs.421 "
    "pmid:33817056"
)

assert_equal(
    bundle,
    {
        "doi": [
            "10.7717/peerj-cs.421"
        ],
        "pmid": [
            "33817056"
        ],
        "omid": [
            "br/06101801781"
        ],
    },
    "PID bundle",
)

multi = mod.parse_pid_bundle(
    "omid:br/1 "
    "doi:10.1000/a "
    "doi:10.1000/b"
)

assert_equal(
    multi["doi"],
    [
        "10.1000/a",
        "10.1000/b",
    ],
    "multiple DOI parsing",
)

# ------------------------------------------------------------
# OpenCitations list-shape tolerance.
# ------------------------------------------------------------

flat = [
    {
        "oci": "1-2",
        "citing": "doi:10.1/a",
        "cited": "doi:10.1/b",
    }
]

assert_equal(
    mod.flatten_json_list(flat),
    flat,
    "flat JSON list",
)

assert_equal(
    mod.flatten_json_list([flat]),
    flat,
    "one nested JSON list",
)

for bad in [
    {},
    ["not an object"],
    [[["too deep"]]],
]:
    try:
        mod.flatten_json_list(
            bad
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            f"invalid payload accepted: {bad!r}"
        )

# ------------------------------------------------------------
# OpenCitations count parsing.
# ------------------------------------------------------------

assert_equal(
    mod.parse_opencitations_count(
        [{"count": "35"}]
    ),
    35,
    "OpenCitations count parsing",
)

for bad in [
    [],
    [{"not_count": "1"}],
    [{"count": "-1"}],
    [{"count": "abc"}],
    [{"count": "1"}, {"count": "2"}],
]:
    try:
        mod.parse_opencitations_count(
            bad
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "invalid OpenCitations count "
            f"accepted: {bad!r}"
        )


# ------------------------------------------------------------
# Request construction.
# ------------------------------------------------------------

single_url = mod.openalex_single_url(
    "10.1093/ve/vex042",
)

assert (
    "doi:10.1093%2Fve%2Fvex042"
    in single_url
)

assert "SECRET" not in single_url
assert "api_key" not in single_url

forward_url = mod.openalex_forward_url(
    "https://openalex.org/W123",
    "*",
)

assert "SECRET" not in forward_url
assert "api_key" not in forward_url

assert "cites%3AW123" in forward_url
assert "cursor=%2A" in forward_url

back_url = mod.opencitations_url(
    "backward",
    "10.1093/ve/vex042",
)

forward_oc_url = mod.opencitations_url(
    "forward",
    "10.1093/ve/vex042",
)

back_count_url = mod.opencitations_count_url(
    "backward",
    "10.1093/ve/vex042",
)

forward_count_url = mod.opencitations_count_url(
    "forward",
    "10.1093/ve/vex042",
)

assert (
    "/reference-count/"
    "doi:10.1093%2Fve%2Fvex042"
    in back_count_url
)

assert (
    "/citation-count/"
    "doi:10.1093%2Fve%2Fvex042"
    in forward_count_url
)

assert (
    "/references/"
    "doi:10.1093%2Fve%2Fvex042"
    in back_url
)

assert (
    "/citations/"
    "doi:10.1093%2Fve%2Fvex042"
    in forward_oc_url
)

# ------------------------------------------------------------
# Direct transport retry: IncompleteRead then success.
# ------------------------------------------------------------

class IncompleteThenCompleteResponse:
    def __init__(
        self,
        *,
        fail,
        payload,
    ):
        self.fail = fail
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        return False

    def read(self):
        if self.fail:
            raise http.client.IncompleteRead(
                b'{"partial":',
                100,
            )

        return self.payload


with tempfile.TemporaryDirectory() as td:
    raw_path = (
        Path(td)
        / "response.json"
    )

    payload = json.dumps(
        {
            "status": "complete",
            "records": [1, 2, 3],
        }
    ).encode("utf-8")

    responses = [
        IncompleteThenCompleteResponse(
            fail=True,
            payload=b"",
        ),
        IncompleteThenCompleteResponse(
            fail=False,
            payload=payload,
        ),
    ]

    calls = []

    def fake_urlopen(
        request,
        timeout,
    ):
        calls.append(request.full_url)

        if not responses:
            raise AssertionError(
                "unexpected additional urlopen call"
            )

        return responses.pop(0)

    with patch(
        "urllib.request.urlopen",
        side_effect=fake_urlopen,
    ):
        observed = mod.fetch_json(
            "https://example.invalid/test",
            headers={
                "Authorization":
                    "Bearer TEST",
            },
            raw_path=raw_path,
            delay=0,
            retries=2,
        )

    assert_equal(
        observed,
        {
            "status": "complete",
            "records": [1, 2, 3],
        },
        "IncompleteRead retry result",
    )

    assert_equal(
        len(calls),
        2,
        "IncompleteRead retry request count",
    )

    assert_equal(
        raw_path.read_bytes(),
        payload,
        "IncompleteRead retry raw output",
    )


# ------------------------------------------------------------
# Persistent IncompleteRead must fail closed.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as td:
    raw_path = (
        Path(td)
        / "response.json"
    )

    calls = []

    def always_incomplete(
        request,
        timeout,
    ):
        calls.append(request.full_url)

        return IncompleteThenCompleteResponse(
            fail=True,
            payload=b"",
        )

    with patch(
        "urllib.request.urlopen",
        side_effect=always_incomplete,
    ):
        try:
            mod.fetch_json(
                "https://example.invalid/test",
                headers={},
                raw_path=raw_path,
                delay=0,
                retries=2,
            )
        except RuntimeError as exc:
            assert (
                "Request failed after 2 attempts"
                in str(exc)
            )
        else:
            raise AssertionError(
                "persistent IncompleteRead did not fail"
            )

    assert_equal(
        len(calls),
        2,
        "persistent IncompleteRead attempts",
    )

    if raw_path.exists():
        raise AssertionError(
            "incomplete HTTP body was written to raw output"
        )


# ------------------------------------------------------------
# Synthetic anchor.
# ------------------------------------------------------------

anchor = {
    "wave": "0",
    "anchor_id": "W0TEST",
    "tool": "TEST",
    "confirmed_role": "direct",
    "canonical_identifier_type":
        "doi",
    "canonical_identifier":
        "10.1000/test",
    "canonical_title":
        "Synthetic test work",
    "canonical_year": "2020",
    "anchor_evidence": "TEST",
    "anchor_origin": "test",
    "retrieval_status": "pending",
}


class FakeOpenAlex:
    def __init__(self):
        self.calls = 0

    def __call__(
        self,
        url,
        *,
        headers,
        raw_path,
        delay,
        retries=5,
    ):
        self.calls += 1

        assert "SECRET" not in url
        assert "api_key" not in url
        assert headers.get(
            "Authorization"
        ) == "Bearer SECRET"

        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if "/works/doi:" in url:
            payload = {
                "id":
                    "https://openalex.org/W100",
                "doi":
                    "https://doi.org/10.1000/test",
                "title":
                    "Synthetic test work",
                "publication_year": 2020,
                "ids": {
                    "openalex":
                        "https://openalex.org/W100",
                    "doi":
                        "https://doi.org/10.1000/test",
                },
                "referenced_works": [
                    "https://openalex.org/W10",
                    "https://openalex.org/W20",
                ],
                "referenced_works_count": 2,
                "cited_by_count": 2,
            }

        elif "cursor=%2A" in url:
            payload = {
                "meta": {
                    "count": 2,
                    "next_cursor": "NEXT",
                },
                "results": [
                    {
                        "id":
                            "https://openalex.org/W200",
                        "doi":
                            "https://doi.org/10.2000/a",
                        "title": "Citing A",
                        "publication_year":
                            2021,
                        "ids": {
                            "openalex":
                                "https://openalex.org/W200",
                            "doi":
                                "https://doi.org/10.2000/a",
                            "pmid":
                                "https://pubmed.ncbi.nlm.nih.gov/200/",
                        },
                    }
                ],
            }

        elif "cursor=NEXT" in url:
            payload = {
                "meta": {
                    "count": 2,
                    "next_cursor": None,
                },
                "results": [
                    {
                        "id":
                            "https://openalex.org/W300",
                        "doi":
                            "https://doi.org/10.3000/b",
                        "title": "Citing B",
                        "publication_year":
                            2022,
                        "ids": {
                            "openalex":
                                "https://openalex.org/W300",
                            "doi":
                                "https://doi.org/10.3000/b",
                        },
                    }
                ],
            }

        else:
            raise AssertionError(
                f"Unexpected fake URL: {url}"
            )

        raw_path.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

        return payload


class FakeOpenCitations:
    @staticmethod
    def filtered_rows(
        url,
        rows,
    ):
        query = urllib.parse.parse_qs(
            urllib.parse.urlparse(
                url
            ).query
        )

        filters = query.get(
            "filter",
            [],
        )

        if len(filters) != 1:
            raise AssertionError(
                f"expected one OCI filter: {url}"
            )

        value = filters[0]

        if not value.startswith(
            "oci:"
        ):
            raise AssertionError(
                f"unexpected filter field: {value}"
            )

        pattern = value[
            len("oci:"):
        ]

        return [
            row
            for row in rows
            if re.fullmatch(
                pattern,
                row["oci"],
            )
        ]

    def __call__(
        self,
        url,
        *,
        headers,
        raw_path,
        delay,
        retries=5,
    ):
        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if "/reference-count/" in url:
            payload = [
                {
                    "count": "1",
                }
            ]

        elif "/citation-count/" in url:
            payload = [
                {
                    "count": "1",
                }
            ]

        elif "/references/" in url:
            rows = [
                {
                    "oci": "1-2",
                    "citing":
                        "omid:br/1 "
                        "doi:10.1000/test",
                    "cited":
                        "omid:br/2 "
                        "doi:10.4000/ref "
                        "pmid:400",
                }
            ]

            payload = self.filtered_rows(
                url,
                rows,
            )

        elif "/citations/" in url:
            rows = [
                {
                    "oci": "3-1",
                    "citing":
                        "omid:br/3 "
                        "doi:10.5000/citer "
                        "pmid:500",
                    "cited":
                        "omid:br/1 "
                        "doi:10.1000/test",
                }
            ]

            payload = self.filtered_rows(
                url,
                rows,
            )

        else:
            raise AssertionError(
                f"Unexpected fake URL: {url}"
            )

        raw_path.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

        return payload


with tempfile.TemporaryDirectory() as td:
    out = Path(td)

    oa = FakeOpenAlex()

    (
        oa_edges,
        oa_neighbours,
        oa_status,
    ) = mod.retrieve_openalex(
        anchor,
        wave=0,
        api_key="SECRET",
        output_root=out,
        fetcher=oa,
    )

    assert_equal(
        len(oa_edges),
        4,
        "OpenAlex edge count",
    )

    assert_equal(
        len(oa_neighbours),
        4,
        "OpenAlex neighbour count",
    )

    assert_equal(
        [
            (
                r["direction"],
                r["reported_count"],
                r["retrieved_count"],
                r["status"],
            )
            for r in oa_status
        ],
        [
            (
                "backward",
                2,
                2,
                "complete",
            ),
            (
                "forward",
                2,
                2,
                "complete",
            ),
        ],
        "OpenAlex statuses",
    )

    (
        oc_edges,
        oc_neighbours,
        oc_status,
        oc_partitions,
    ) = mod.retrieve_opencitations(
        anchor,
        wave=0,
        token="",
        output_root=out,
        fetcher=FakeOpenCitations(),
    )

    assert_equal(
        len(oc_edges),
        2,
        "OpenCitations edge count",
    )

    assert_equal(
        len(oc_neighbours),
        2,
        "OpenCitations neighbour count",
    )

    assert_equal(
        len(oc_partitions),
        20,
        "OpenCitations root partition leaf count",
    )

    assert_equal(
        sorted(
            {
                row["direction"]
                for row in oc_partitions
            }
        ),
        [
            "backward",
            "forward",
        ],
        "OpenCitations partition directions",
    )

    assert_equal(
        {
            edge["oci"]:
                edge["raw_file"]
            for edge in oc_edges
        },
        {
            "1-2":
                "raw/opencitations/W0TEST/"
                "backward_partitions/"
                "depth_00/"
                "digits_01_suffix_2.json",
            "3-1":
                "raw/opencitations/W0TEST/"
                "forward_partitions/"
                "depth_00/"
                "digits_01_suffix_3.json",
        },
        "OpenCitations leaf raw provenance",
    )

    assert_equal(
        [
            (
                r["direction"],
                r["reported_count"],
                r["retrieved_count"],
                r["status"],
            )
            for r in oc_status
        ],
        [
            (
                "backward",
                1,
                1,
                "complete",
            ),
            (
                "forward",
                1,
                1,
                "complete",
            ),
        ],
        "OpenCitations statuses",
    )

    mod.validate_status_matrix(
        [anchor],
        oa_status + oc_status,
    )


# ------------------------------------------------------------
# Fail-closed tests.
# ------------------------------------------------------------

class BadOpenAlexCount:
    def __call__(
        self,
        url,
        *,
        headers,
        raw_path,
        delay,
        retries=5,
    ):
        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if "/works/doi:" in url:
            payload = {
                "id":
                    "https://openalex.org/W100",
                "doi":
                    "https://doi.org/10.1000/test",
                "ids": {
                    "openalex":
                        "https://openalex.org/W100",
                },
                "referenced_works": [],
                "referenced_works_count": 1,
                "cited_by_count": 0,
            }
        else:
            raise AssertionError(
                "Should fail before forward retrieval"
            )

        raw_path.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

        return payload


with tempfile.TemporaryDirectory() as td:
    try:
        mod.retrieve_openalex(
            anchor,
            wave=0,
            api_key="SECRET",
            output_root=Path(td),
            fetcher=BadOpenAlexCount(),
        )
    except RuntimeError as exc:
        assert (
            "referenced_works_count"
            in str(exc)
        )
    else:
        raise AssertionError(
            "OpenAlex count mismatch did not fail"
        )


class BadOpenCitationsCount:
    def __call__(
        self,
        url,
        *,
        headers,
        raw_path,
        delay,
        retries=5,
    ):
        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if "/reference-count/" in url:
            payload = [
                {
                    "count": "2",
                }
            ]

        elif "/references/" in url:
            query = urllib.parse.parse_qs(
                urllib.parse.urlparse(
                    url
                ).query
            )

            filters = query.get(
                "filter",
                [],
            )

            if len(filters) != 1:
                raise AssertionError(
                    "partition filter missing"
                )

            value = filters[0]

            if not value.startswith(
                "oci:"
            ):
                raise AssertionError(
                    "unexpected partition field"
                )

            pattern = value[
                len("oci:"):
            ]

            row = {
                "oci": "1-2",
                "citing":
                    "doi:10.1000/test",
                "cited":
                    "doi:10.4000/ref",
            }

            payload = (
                [row]
                if re.fullmatch(
                    pattern,
                    row["oci"],
                )
                else []
            )

        else:
            raise AssertionError(
                "Should fail during backward "
                "OpenCitations reconciliation"
            )

        raw_path.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

        return payload


with tempfile.TemporaryDirectory() as td:
    try:
        mod.retrieve_opencitations(
            anchor,
            wave=0,
            token="",
            output_root=Path(td),
            fetcher=BadOpenCitationsCount(),
        )
    except RuntimeError as exc:
        assert (
            "reported 2, retrieved 1 unique OCI rows"
            in str(exc)
        )
    else:
        raise AssertionError(
            "OpenCitations count mismatch "
            "did not fail"
        )


bad_status = [
    {
        "anchor_id": "W0TEST",
        "source": "openalex",
        "direction": "backward",
        "status": "complete",
        "reported_count": 1,
        "retrieved_count": 1,
    }
]

try:
    mod.validate_status_matrix(
        [anchor],
        bad_status,
    )
except RuntimeError as exc:
    assert "Incomplete status matrix" in str(exc)
else:
    raise AssertionError(
        "Incomplete source matrix did not fail"
    )


print("PASS | identifier normalisation")
print("PASS | OpenCitations PID parsing")
print("PASS | OpenCitations payload-shape validation")
print("PASS | API request construction")
print("PASS | IncompleteRead is retried from a fresh request")
print("PASS | successful retry writes only the complete response")
print("PASS | persistent IncompleteRead fails closed")
print("PASS | incomplete response body is never written")
print("PASS | OpenAlex credential absent from request URLs")
print("PASS | OpenAlex credential supplied by Authorization header")


# ==================================================================
# OpenAlex forward cursor snapshot retry.
#
# Attempt 1:
#   page 1 -> A, B
#   page 2 -> B, C
#
# Work B therefore appears twice across cursor pages. The duplicate
# record is byte-identical, but the whole traversal is invalid and
# must be discarded from production.
#
# Attempt 2:
#   page 1 -> A, B
#   page 2 -> C
#
# This complete 3/3 unique-Work traversal is accepted.
#
# Failed-attempt raw responses must remain preserved, while production
# edge provenance must reference only accepted attempt 2.
# ==================================================================

class OpenAlexDuplicateThenStableFetcher:
    def __init__(
        self,
    ):
        self.forward_starts = 0

    @staticmethod
    def work(
        work_id,
        doi,
    ):
        return {
            "id":
                f"https://openalex.org/{work_id}",
            "doi":
                f"https://doi.org/{doi}",
            "title":
                f"Synthetic {work_id}",
            "publication_year":
                2024,
        }

    def __call__(
        self,
        url,
        *,
        headers,
        raw_path,
        delay,
        retries=5,
    ):
        import urllib.parse

        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if raw_path.name == "resolve_anchor.json":
            payload = {
                "id":
                    "https://openalex.org/W9000000001",
                "doi":
                    "https://doi.org/10.1234/openalex-retry",
                "referenced_works":
                    [],
                "referenced_works_count":
                    0,
            }

        else:
            query = urllib.parse.parse_qs(
                urllib.parse.urlparse(
                    url
                ).query
            )

            cursor = query.get(
                "cursor",
                [""],
            )[0]

            if cursor == "*":
                self.forward_starts += 1

            attempt = self.forward_starts

            if attempt == 1:
                if cursor == "*":
                    results = [
                        self.work(
                            "W1000000001",
                            "10.2000/a",
                        ),
                        self.work(
                            "W1000000002",
                            "10.2000/b",
                        ),
                    ]

                    next_cursor = (
                        "attempt-1-page-2"
                    )

                elif cursor == "attempt-1-page-2":
                    results = [
                        # Deliberately repeated across cursor pages.
                        self.work(
                            "W1000000002",
                            "10.2000/b",
                        ),
                        self.work(
                            "W1000000003",
                            "10.2000/c",
                        ),
                    ]

                    next_cursor = None

                else:
                    raise AssertionError(
                        "Unexpected attempt-1 cursor: "
                        f"{cursor!r}"
                    )

            elif attempt == 2:
                if cursor == "*":
                    results = [
                        self.work(
                            "W1000000001",
                            "10.2000/a",
                        ),
                        self.work(
                            "W1000000002",
                            "10.2000/b",
                        ),
                    ]

                    next_cursor = (
                        "attempt-2-page-2"
                    )

                elif cursor == "attempt-2-page-2":
                    results = [
                        self.work(
                            "W1000000003",
                            "10.2000/c",
                        ),
                    ]

                    next_cursor = None

                else:
                    raise AssertionError(
                        "Unexpected attempt-2 cursor: "
                        f"{cursor!r}"
                    )

            else:
                raise AssertionError(
                    "Unexpected additional OpenAlex "
                    f"snapshot attempt: {attempt}"
                )

            payload = {
                "meta": {
                    "count":
                        3,
                    "next_cursor":
                        next_cursor,
                },
                "results":
                    results,
            }

        raw_path.write_text(
            json.dumps(
                payload
            ),
            encoding="utf-8",
        )

        return payload


with tempfile.TemporaryDirectory() as td:
    out = Path(td)

    retry_anchor = {
        "anchor_id":
            "W0OPENALEXRETRY",
        "tool":
            "synthetic",
        "canonical_identifier":
            "10.1234/openalex-retry",
    }

    fetcher = (
        OpenAlexDuplicateThenStableFetcher()
    )

    (
        retry_edges,
        retry_neighbours,
        retry_statuses,
    ) = mod.retrieve_openalex(
        retry_anchor,
        wave=0,
        api_key="synthetic-key",
        output_root=out,
        fetcher=fetcher,
    )

    assert fetcher.forward_starts == 2

    forward_edges = [
        row
        for row in retry_edges
        if row["direction"] == "forward"
    ]

    forward_neighbours = [
        row
        for row in retry_neighbours
        if row["direction"] == "forward"
    ]

    assert len(
        forward_edges
    ) == 3

    assert len(
        forward_neighbours
    ) == 3

    assert {
        row[
            "citing_openalex_ids"
        ]
        for row in forward_edges
    } == {
        "W1000000001",
        "W1000000002",
        "W1000000003",
    }

    # Failed attempt 1 must not contaminate accepted production.
    assert all(
        "forward_snapshot_attempt_02/"
        in row[
            "raw_file"
        ]
        for row in forward_edges
    )

    assert all(
        "forward_snapshot_attempt_01/"
        not in row[
            "raw_file"
        ]
        for row in forward_edges
    )

    forward_status = [
        row
        for row in retry_statuses
        if row[
            "direction"
        ] == "forward"
    ]

    assert len(
        forward_status
    ) == 1

    assert forward_status[
        0
    ][
        "status"
    ] == "complete"

    assert forward_status[
        0
    ][
        "reported_count"
    ] == 3

    assert forward_status[
        0
    ][
        "retrieved_count"
    ] == 3

    # Two responses in failed attempt 1 + two responses in accepted
    # attempt 2.
    assert forward_status[
        0
    ][
        "response_files"
    ] == 4

    assert (
        "accepted forward snapshot attempt 2"
        in forward_status[
            0
        ][
            "terminal_detail"
        ]
    )

    attempt_1 = (
        out
        / "raw/openalex/W0OPENALEXRETRY/"
          "forward_snapshot_attempt_01/"
          "snapshot_attempt.json"
    )

    attempt_2 = (
        out
        / "raw/openalex/W0OPENALEXRETRY/"
          "forward_snapshot_attempt_02/"
          "snapshot_attempt.json"
    )

    assert attempt_1.is_file()
    assert attempt_2.is_file()

    a1 = json.loads(
        attempt_1.read_text(
            encoding="utf-8"
        )
    )

    a2 = json.loads(
        attempt_2.read_text(
            encoding="utf-8"
        )
    )

    assert a1[
        "status"
    ] == "retryable_failure"

    assert a1[
        "retryable"
    ] is True

    assert a1[
        "reported_count"
    ] == 3

    assert (
        "duplicate forward Work W1000000002"
        in a1[
            "terminal_detail"
        ]
    )

    assert a2[
        "status"
    ] == "accepted"

    assert a2[
        "retryable"
    ] is False

    assert a2[
        "reported_count"
    ] == 3

    assert a2[
        "retrieved_count"
    ] == 3

    # Both failed-attempt pages remain as forensic evidence.
    assert (
        out
        / "raw/openalex/W0OPENALEXRETRY/"
          "forward_snapshot_attempt_01/"
          "forward_page_0001.json"
    ).is_file()

    assert (
        out
        / "raw/openalex/W0OPENALEXRETRY/"
          "forward_snapshot_attempt_01/"
          "forward_page_0002.json"
    ).is_file()


print("PASS | synthetic OpenAlex backward retrieval")
print("PASS | synthetic OpenAlex cursor pagination")
print("PASS | synthetic OpenCitations backward retrieval")
print("PASS | synthetic OpenCitations forward retrieval")
print("PASS | synthetic OpenCitations root OCI partitioning")
print("PASS | OpenCitations edge raw-file leaf provenance")
print("PASS | complete source-direction matrix validation")
print("PASS | OpenAlex count mismatch fails closed")
print("PASS | OpenCitations independent count mismatch fails closed")
print("PASS | incomplete source matrix fails closed")
print("PASS | offline tests made zero network requests")
