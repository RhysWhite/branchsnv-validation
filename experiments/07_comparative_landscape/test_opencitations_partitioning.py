#!/usr/bin/env python3
"""
Offline invariants for deterministic OpenCitations OCI partitioning.

No network access is permitted.
"""

from __future__ import annotations

import http.client
import importlib.util
import json
import re
import tempfile
import urllib.parse

from pathlib import Path


ROOT = Path(
    "experiments/07_comparative_landscape"
)

SCRIPT = ROOT / "retrieve_citation_wave.py"

spec = importlib.util.spec_from_file_location(
    "citation_retriever_partition_test",
    SCRIPT,
)

if spec is None or spec.loader is None:
    raise RuntimeError(
        "Could not import citation retriever"
    )

mod = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(mod)


def expect_runtime(
    fn,
    contains: str,
):
    try:
        fn()
    except RuntimeError as exc:
        if contains not in str(exc):
            raise AssertionError(
                f"{contains!r} not found in {str(exc)!r}"
            )
    else:
        raise AssertionError(
            f"Expected RuntimeError containing {contains!r}"
        )


# ------------------------------------------------------------
# Root partitions: exhaustive and disjoint.
# ------------------------------------------------------------

forward_root = [
    re.compile(
        mod.opencitations_partition_regex(
            "forward",
            digit,
            exact=False,
        )
    )
    for digit in mod.OPENCITATIONS_PARTITION_DIGITS
]

backward_root = [
    re.compile(
        mod.opencitations_partition_regex(
            "backward",
            digit,
            exact=False,
        )
    )
    for digit in mod.OPENCITATIONS_PARTITION_DIGITS
]

for left in range(0, 10000):
    oci = f"{left}-123"

    hits = sum(
        bool(rx.fullmatch(oci))
        for rx in forward_root
    )

    if hits != 1:
        raise AssertionError(
            f"forward root membership {oci}: {hits}"
        )

for right in range(0, 10000):
    oci = f"123-{right}"

    hits = sum(
        bool(rx.fullmatch(oci))
        for rx in backward_root
    )

    if hits != 1:
        raise AssertionError(
            f"backward root membership {oci}: {hits}"
        )


# ------------------------------------------------------------
# Recursive exact + ten extended children partition parent.
# ------------------------------------------------------------

for direction in [
    "forward",
    "backward",
]:
    suffix = "7"

    parent = re.compile(
        mod.opencitations_partition_regex(
            direction,
            suffix,
            exact=False,
        )
    )

    exact = re.compile(
        mod.opencitations_partition_regex(
            direction,
            suffix,
            exact=True,
        )
    )

    children = [
        re.compile(
            mod.opencitations_partition_regex(
                direction,
                digit + suffix,
                exact=False,
            )
        )
        for digit in (
            mod.OPENCITATIONS_PARTITION_DIGITS
        )
    ]

    for value in range(0, 10000):
        component = str(value)

        oci = (
            f"{component}-123"
            if direction == "forward"
            else f"123-{component}"
        )

        if not parent.fullmatch(oci):
            continue

        hits = (
            int(bool(exact.fullmatch(oci)))
            + sum(
                bool(rx.fullmatch(oci))
                for rx in children
            )
        )

        if hits != 1:
            raise AssertionError(
                f"{direction} child membership "
                f"{oci}: {hits}"
            )


# ------------------------------------------------------------
# Direction-specific URL/filter construction.
# ------------------------------------------------------------

regex = (
    mod.opencitations_partition_regex(
        "forward",
        "7",
        exact=False,
    )
)

url = mod.opencitations_url(
    "forward",
    "10.1000/test",
    oci_filter=regex,
)

query = urllib.parse.parse_qs(
    urllib.parse.urlparse(
        url
    ).query
)

assert query == {
    "filter": [
        f"oci:{regex}",
    ]
}


# ------------------------------------------------------------
# Leaf validation.
# ------------------------------------------------------------

valid_row = {
    "oci": "17-1",
    "citing": "doi:10.1/a",
    "cited": "doi:10.1/b",
}

observed = (
    mod.validate_opencitations_partition_payload(
        [valid_row],
        leaf_regex=(
            mod.opencitations_partition_regex(
                "forward",
                "7",
                exact=False,
            )
        ),
        context="TEST",
    )
)

assert observed == [
    valid_row
]

expect_runtime(
    lambda:
        mod.validate_opencitations_partition_payload(
            [
                {
                    "citing": "doi:10.1/a",
                    "cited": "doi:10.1/b",
                }
            ],
            leaf_regex=(
                r"^[0-9]*7-[0-9]+$"
            ),
            context="TEST",
        ),
    "contains no OCI",
)

expect_runtime(
    lambda:
        mod.validate_opencitations_partition_payload(
            [
                {
                    "oci": "not-an-oci",
                }
            ],
            leaf_regex=(
                r"^[0-9]*7-[0-9]+$"
            ),
            context="TEST",
        ),
    "malformed OCI",
)

expect_runtime(
    lambda:
        mod.validate_opencitations_partition_payload(
            [
                {
                    "oci": "18-1",
                }
            ],
            leaf_regex=(
                r"^[0-9]*7-[0-9]+$"
            ),
            context="TEST",
        ),
    "does not belong to its partition leaf",
)


# ------------------------------------------------------------
# Reconciliation: duplicate, exact count, order independence.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as td:
    root = Path(td)

    rows_a = [
        (
            {
                "oci": "17-1",
            },
            root / "a.json",
        ),
        (
            {
                "oci": "7-1",
            },
            root / "b.json",
        ),
    ]

    rows_b = list(
        reversed(
            rows_a
        )
    )

    a = (
        mod.reconcile_opencitations_partition_rows(
            rows_a,
            expected_count=2,
            context="TEST",
        )
    )

    b = (
        mod.reconcile_opencitations_partition_rows(
            rows_b,
            expected_count=2,
            context="TEST",
        )
    )

    assert [
        row["oci"]
        for row, _ in a
    ] == [
        "17-1",
        "7-1",
    ]

    assert [
        row["oci"]
        for row, _ in b
    ] == [
        "17-1",
        "7-1",
    ]

    expect_runtime(
        lambda:
            mod.reconcile_opencitations_partition_rows(
                [
                    (
                        {
                            "oci": "7-1",
                        },
                        root / "a.json",
                    ),
                    (
                        {
                            "oci": "7-1",
                        },
                        root / "b.json",
                    ),
                ],
                expected_count=2,
                context="TEST",
            ),
        "duplicate OCI",
    )

    expect_runtime(
        lambda:
            mod.reconcile_opencitations_partition_rows(
                [
                    (
                        {
                            "oci": "7-1",
                        },
                        root / "a.json",
                    ),
                ],
                expected_count=2,
                context="TEST",
            ),
        "reported 2, retrieved 1 unique OCI rows",
    )


# ------------------------------------------------------------
# Retry exhaustion caused by IncompleteRead triggers exactly
# the frozen deterministic subdivision rule.
# ------------------------------------------------------------

class SubdivisionFetcher:
    def __init__(self):
        self.calls = []

        self.rows = [
            {
                "oci": "7-1",
                "citing":
                    "doi:10.7000/a",
                "cited":
                    "doi:10.1000/test",
            },
            {
                "oci": "17-1",
                "citing":
                    "doi:10.17000/b",
                "cited":
                    "doi:10.1000/test",
            },
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
        query = urllib.parse.parse_qs(
            urllib.parse.urlparse(
                url
            ).query
        )

        value = query[
            "filter"
        ][0]

        assert value.startswith(
            "oci:"
        )

        regex = value[
            len("oci:"):
        ]

        self.calls.append(
            regex
        )

        failed_parent = (
            mod.opencitations_partition_regex(
                "forward",
                "7",
                exact=False,
            )
        )

        if regex == failed_parent:
            try:
                raise (
                    http.client.IncompleteRead(
                        b'{"partial":',
                        1000,
                    )
                )
            except http.client.IncompleteRead as exc:
                raise RuntimeError(
                    "Request failed after 5 attempts: TEST"
                ) from exc

        payload = [
            row
            for row in self.rows
            if re.fullmatch(
                regex,
                row["oci"],
            )
        ]

        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        raw_path.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

        return payload


anchor = {
    "anchor_id": "W0TEST",
    "tool": "TEST",
}

with tempfile.TemporaryDirectory() as td:
    out = Path(td)
    raw_root = (
        out
        / "raw"
        / "opencitations"
        / "W0TEST"
    )

    fetcher = SubdivisionFetcher()

    (
        rows,
        leaves,
    ) = (
        mod.retrieve_opencitations_partitioned(
            anchor=anchor,
            direction="forward",
            doi="10.1000/test",
            expected_count=2,
            wave=0,
            headers={},
            raw_root=raw_root,
            output_root=out,
            fetcher=fetcher,
        )
    )

    assert [
        row["oci"]
        for row, _ in rows
    ] == [
        "17-1",
        "7-1",
    ]

    # Root leaves 0..6 = 7.
    # Root 7 fails and is replaced by exact + ten children = 11.
    # Root leaves 8..9 = 2.
    assert len(leaves) == 20

    assert [
        int(row["leaf_order"])
        for row in leaves
    ] == list(
        range(
            1,
            21,
        )
    )

    exact_7 = [
        row
        for row in leaves
        if (
            row["suffix"] == "7"
            and row["partition_kind"] == "exact"
        )
    ]

    assert len(exact_7) == 1
    assert exact_7[0]["row_count"] == 1

    suffix_17 = [
        row
        for row in leaves
        if (
            row["suffix"] == "17"
            and row["partition_kind"] == "suffix"
        )
    ]

    assert len(suffix_17) == 1
    assert suffix_17[0]["row_count"] == 1

    failed_parent_path = (
        mod.opencitations_partition_raw_path(
            raw_root,
            "forward",
            "7",
            exact=False,
            recursion_depth=0,
        )
    )

    assert not failed_parent_path.exists()


# ------------------------------------------------------------
# Recursion ceiling is fail-closed.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as td:
    out = Path(td)
    raw_root = (
        out
        / "raw"
        / "opencitations"
        / "W0TEST"
    )

    fetcher = SubdivisionFetcher()

    expect_runtime(
        lambda:
            mod.retrieve_opencitations_partitioned(
                anchor=anchor,
                direction="forward",
                doi="10.1000/test",
                expected_count=2,
                wave=0,
                headers={},
                raw_root=raw_root,
                output_root=out,
                fetcher=fetcher,
                max_suffix_digits=1,
            ),
        "OCI partition recursion ceiling reached",
    )


# ------------------------------------------------------------
# Non-IncompleteRead failures do not silently subdivide.
# ------------------------------------------------------------

class OtherFailureFetcher:
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

        try:
            raise TimeoutError(
                "synthetic timeout"
            )
        except TimeoutError as exc:
            raise RuntimeError(
                "Request failed after 5 attempts: TEST"
            ) from exc


with tempfile.TemporaryDirectory() as td:
    out = Path(td)
    raw_root = (
        out
        / "raw"
        / "opencitations"
        / "W0TEST"
    )

    fetcher = OtherFailureFetcher()

    expect_runtime(
        lambda:
            mod.retrieve_opencitations_partitioned(
                anchor=anchor,
                direction="forward",
                doi="10.1000/test",
                expected_count=1,
                wave=0,
                headers={},
                raw_root=raw_root,
                output_root=out,
                fetcher=fetcher,
            ),
        "Request failed after 5 attempts",
    )

    assert fetcher.calls == 1


# ------------------------------------------------------------
# Zero independent count performs no data-partition requests.
# ------------------------------------------------------------

class ZeroCountFetcher:
    def __init__(self):
        self.count_calls = 0
        self.data_calls = 0

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

        if (
            "/reference-count/" in url
            or "/citation-count/" in url
        ):
            self.count_calls += 1

            payload = [
                {
                    "count": "0",
                }
            ]

            raw_path.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            return payload

        self.data_calls += 1

        raise AssertionError(
            "zero-count operation attempted "
            "a citation-data request"
        )


full_anchor = {
    "wave": "0",
    "anchor_id": "W0ZERO",
    "tool": "ZERO",
    "confirmed_role": "direct",
    "canonical_identifier_type": "doi",
    "canonical_identifier": "10.1000/zero",
    "canonical_title": "Zero test",
    "canonical_year": "2020",
    "anchor_evidence": "TEST",
    "anchor_origin": "test",
    "retrieval_status": "pending",
}

with tempfile.TemporaryDirectory() as td:
    fetcher = ZeroCountFetcher()

    (
        edges,
        neighbours,
        statuses,
        leaves,
    ) = mod.retrieve_opencitations(
        full_anchor,
        wave=0,
        token="",
        output_root=Path(td),
        fetcher=fetcher,
    )

    assert edges == []
    assert neighbours == []
    assert leaves == []

    assert fetcher.count_calls == 2
    assert fetcher.data_calls == 0

    assert [
        (
            row["direction"],
            row["status"],
            row["reported_count"],
            row["retrieved_count"],
            row["response_files"],
        )
        for row in statuses
    ] == [
        (
            "backward",
            "resolved_zero_edges",
            0,
            0,
            1,
        ),
        (
            "forward",
            "resolved_zero_edges",
            0,
            0,
            1,
        ),
    ]


print("PASS | ten root OCI buckets are exhaustive and disjoint")
print("PASS | recursive exact+ten children partition parent buckets")
print("PASS | forward/backward variable OCI components are distinct")
print("PASS | filtered OpenCitations URL construction")
print("PASS | valid OCI leaf membership")
print("PASS | missing OCI fails closed")
print("PASS | malformed OCI fails closed")
print("PASS | out-of-leaf OCI fails closed")
print("PASS | duplicate OCI fails closed")
print("PASS | independent-count mismatch fails closed")
print("PASS | reconstructed OCI union is order-independent")
print("PASS | IncompleteRead exhaustion triggers deterministic subdivision")
print("PASS | failed incomplete parent body is not accepted as a leaf")
print("PASS | leaf execution order is deterministic")
print("PASS | recursion ceiling fails closed")
print("PASS | unrelated exhausted transport failure does not subdivide")
print("PASS | zero-count shortcut performs no data requests")
print("PASS | partition invariant tests made zero network requests")
