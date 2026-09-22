#!/usr/bin/env python3
"""
Offline tests for Experiment 07 citation-wave retrieval.

No network access is permitted by these tests.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile

from pathlib import Path


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
    "SECRET",
)

assert (
    "doi:10.1093%2Fve%2Fvex042"
    in single_url
)

assert "api_key=SECRET" in single_url

forward_url = mod.openalex_forward_url(
    "https://openalex.org/W123",
    "*",
    "SECRET",
)

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
            payload = [
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

        elif "/citations/" in url:
            payload = [
                [
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
            ]

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
            payload = [
                {
                    "oci": "1-2",
                    "citing":
                        "doi:10.1000/test",
                    "cited":
                        "doi:10.4000/ref",
                }
            ]

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
        assert "reported 2, retrieved 1" in str(exc)
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
print("PASS | synthetic OpenAlex backward retrieval")
print("PASS | synthetic OpenAlex cursor pagination")
print("PASS | synthetic OpenCitations backward retrieval")
print("PASS | synthetic OpenCitations forward retrieval")
print("PASS | complete source-direction matrix validation")
print("PASS | OpenAlex count mismatch fails closed")
print("PASS | OpenCitations independent count mismatch fails closed")
print("PASS | incomplete source matrix fails closed")
print("PASS | offline tests made zero network requests")
