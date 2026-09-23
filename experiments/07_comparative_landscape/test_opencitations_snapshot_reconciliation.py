#!/usr/bin/env python3
"""
Offline tests for dual-axis OpenCitations snapshot reconciliation.

No network access is permitted.
"""

from __future__ import annotations

import http.client
import importlib.util
import json
import os
import re
import sys
import tempfile
import urllib.parse

from pathlib import Path


ROOT = Path(
    "experiments/07_comparative_landscape"
)

SCRIPT = (
    ROOT
    / "retrieve_citation_wave.py"
)

spec = importlib.util.spec_from_file_location(
    "citation_retriever_snapshot_test",
    SCRIPT,
)

if spec is None or spec.loader is None:
    raise RuntimeError(
        "Cannot import production citation retriever"
    )

mod = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    mod
)


# ------------------------------------------------------------------
# Absolute network prohibition.
# ------------------------------------------------------------------

def forbidden_network(*args, **kwargs):
    raise AssertionError(
        "NETWORK ACCESS PROHIBITED IN OFFLINE TEST"
    )


mod.urllib.request.urlopen = (
    forbidden_network
)


def expect_runtime(
    fn,
    contains: str,
):
    try:
        fn()
    except RuntimeError as exc:
        if contains not in str(exc):
            raise AssertionError(
                f"{contains!r} absent from {str(exc)!r}"
            )
        return exc
    else:
        raise AssertionError(
            f"Expected RuntimeError containing {contains!r}"
        )


ANCHOR = {
    "wave":
        "0",
    "anchor_id":
        "W0TEST",
    "tool":
        "TEST",
    "confirmed_role":
        "direct",
    "canonical_identifier_type":
        "doi",
    "canonical_identifier":
        "10.1000/test",
    "canonical_title":
        "Synthetic test anchor",
    "canonical_year":
        "2020",
    "anchor_evidence":
        "TEST",
    "anchor_origin":
        "test",
    "retrieval_status":
        "pending",
}


BACKWARD_ROWS = [
    {
        "oci":
            "1-2",
        "citing":
            "omid:br/1 doi:10.1000/test",
        "cited":
            "omid:br/2 doi:10.2000/ref-a pmid:200",
        "creation":
            "2020",
        "timespan":
            "P0Y",
        "journal_sc":
            "no",
        "author_sc":
            "no",
    },
    {
        "oci":
            "1-4",
        "citing":
            "omid:br/1 doi:10.1000/test",
        "cited":
            "omid:br/4 doi:10.4000/ref-b pmid:400",
        "creation":
            "2021-03",
        "timespan":
            "P1Y3M",
        "journal_sc":
            "no",
        "author_sc":
            "no",
    },
]


FORWARD_ROWS = [
    {
        "oci":
            "3-1",
        "citing":
            "omid:br/3 doi:10.3000/citer-a pmid:300",
        "cited":
            "omid:br/1 doi:10.1000/test",
        "creation":
            "2020-05-01",
        "timespan":
            "P0Y5M",
        "journal_sc":
            "no",
        "author_sc":
            "no",
    },
    {
        "oci":
            "5-1",
        "citing":
            "omid:br/5 doi:10.5000/citer-b pmid:500",
        "cited":
            "omid:br/1 doi:10.1000/test",
        "creation":
            "",
        "timespan":
            "P2Y",
        "journal_sc":
            "no",
        "author_sc":
            "no",
    },
]


def direction_for_url(
    url: str,
) -> str:
    if (
        "/reference-count/" in url
        or "/references/" in url
    ):
        return "backward"

    if (
        "/citation-count/" in url
        or "/citations/" in url
    ):
        return "forward"

    raise AssertionError(
        f"Unknown OpenCitations URL: {url}"
    )


def rows_for_direction(
    direction: str,
):
    source = (
        BACKWARD_ROWS
        if direction == "backward"
        else FORWARD_ROWS
    )

    return [
        dict(row)
        for row in source
    ]


def parse_partition_filter(
    url: str,
):
    query = urllib.parse.parse_qs(
        urllib.parse.urlparse(
            url
        ).query
    )

    values = query.get(
        "filter",
        [],
    )

    if len(values) != 1:
        raise AssertionError(
            f"Expected exactly one filter: {url}"
        )

    value = values[0]

    if ":" not in value:
        raise AssertionError(
            f"Malformed filter: {value}"
        )

    field, regex = value.split(
        ":",
        1,
    )

    if field not in {
        "oci",
        "creation",
    }:
        raise AssertionError(
            f"Unexpected partition field: {field}"
        )

    return (
        field,
        regex,
    )


def filter_rows(
    rows,
    field,
    regex,
):
    selected = [
        dict(row)
        for row in rows
        if re.fullmatch(
            regex,
            row[field],
        )
    ]

    # Deliberately reverse the independent witness.
    # Cross-axis equality must be set-based, not order-based.
    if field == "creation":
        selected.reverse()

    return selected


class StableDualAxisFetcher:
    def __init__(
        self,
    ):
        self.count_calls = {
            "backward": 0,
            "forward": 0,
        }

        self.data_calls = {
            "backward": 0,
            "forward": 0,
        }

    def count_value(
        self,
        direction,
    ):
        return 2

    def transform_rows(
        self,
        *,
        direction,
        field,
        rows,
    ):
        return rows

    def __call__(
        self,
        url,
        *,
        headers,
        raw_path,
        delay,
        retries=5,
    ):
        direction = (
            direction_for_url(
                url
            )
        )

        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if (
            "/reference-count/" in url
            or "/citation-count/" in url
        ):
            self.count_calls[
                direction
            ] += 1

            payload = [
                {
                    "count":
                        str(
                            self.count_value(
                                direction
                            )
                        )
                }
            ]

        else:
            self.data_calls[
                direction
            ] += 1

            field, regex = (
                parse_partition_filter(
                    url
                )
            )

            rows = (
                rows_for_direction(
                    direction
                )
            )

            rows = (
                self.transform_rows(
                    direction=
                        direction,
                    field=
                        field,
                    rows=
                        rows,
                )
            )

            payload = filter_rows(
                rows,
                field,
                regex,
            )

        raw_path.write_text(
            json.dumps(
                payload
            ),
            encoding="utf-8",
        )

        return payload


# ==================================================================
# 1. Stable positive snapshot:
#    count -> OCI -> creation -> count, exact agreement.
# ==================================================================

with tempfile.TemporaryDirectory() as td:
    out = Path(td)

    fetcher = (
        StableDualAxisFetcher()
    )

    (
        edges,
        neighbours,
        statuses,
        oci_leaves,
        creation_leaves,
        attempts,
    ) = (
        mod.retrieve_opencitations_dual_axis(
            ANCHOR,
            wave=0,
            token="",
            output_root=out,
            fetcher=fetcher,
        )
    )

    assert len(
        edges
    ) == 4

    assert len(
        neighbours
    ) == 4

    assert [
        (
            row["direction"],
            row["reported_count"],
            row["retrieved_count"],
            row["status"],
        )
        for row in statuses
    ] == [
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
    ]

    assert fetcher.count_calls == {
        "backward": 2,
        "forward": 2,
    }

    assert len(
        oci_leaves
    ) == 20

    assert len(
        creation_leaves
    ) == 24

    assert len(
        attempts
    ) == 2

    for record in attempts:
        assert record[
            "snapshot_attempt"
        ] == 1

        assert record[
            "status"
        ] == "accepted"

        assert record[
            "retryable"
        ] is False

        assert record[
            "pre_count"
        ] == 2

        assert record[
            "post_count"
        ] == 2

        assert record[
            "oci_row_count"
        ] == 2

        assert record[
            "creation_row_count"
        ] == 2

        assert record[
            "complete_row_sets_equal"
        ] is True

        assert record[
            "oci_sets_equal"
        ] is True

        assert (
            record[
                "oci_complete_row_sha256"
            ]
            ==
            record[
                "creation_complete_row_sha256"
            ]
        )

        assert (
            record[
                "oci_set_sha256"
            ]
            ==
            record[
                "creation_oci_set_sha256"
            ]
        )

        assert record[
            "oci_leaf_count"
        ] == 10

        assert record[
            "creation_leaf_count"
        ] == 12

        assert record[
            "response_files"
        ] == 24

    # Production edges must retain OCI-axis provenance.
    for edge in edges:
        assert (
            "/oci_axis/"
            in edge[
                "raw_file"
            ]
        )

        assert (
            "/creation_axis/"
            not in edge[
                "raw_file"
            ]
        )

    # Empty creation is not lost.
    assert any(
        row["row_count"] == 1
        and row["partition_kind"] == "empty"
        and row["direction"] == "forward"
        for row in creation_leaves
    )


# ==================================================================
# 2. Complete-row equality is stricter than OCI-set equality.
#
# Same OCIs, same counts, but one source field differs between axes.
# Must retry whole snapshots and fail after exactly three.
# ==================================================================

class CrossAxisMetadataMismatch(
    StableDualAxisFetcher
):
    def transform_rows(
        self,
        *,
        direction,
        field,
        rows,
    ):
        if field == "creation":
            rows = [
                dict(row)
                for row in rows
            ]

            rows[0][
                "author_sc"
            ] = "yes"

        return rows


with tempfile.TemporaryDirectory() as td:
    out = Path(td)

    exc = expect_runtime(
        lambda:
            mod.retrieve_opencitations_dual_axis(
                ANCHOR,
                wave=0,
                token="",
                output_root=out,
                fetcher=
                    CrossAxisMetadataMismatch(),
            ),
        "did not produce an acceptable snapshot within 3 attempts",
    )

    assert (
        "cross-axis complete-row sets differ"
        in str(exc)
    )

    for attempt in (
        1,
        2,
        3,
    ):
        p = (
            out
            / "raw/opencitations/W0TEST/"
              "backward_snapshot_attempt_"
              f"{attempt:02d}/snapshot_attempt.json"
        )

        assert p.is_file()

        record = json.loads(
            p.read_text(
                encoding="utf-8"
            )
        )

        assert record[
            "status"
        ] == "retryable_failure"

        assert record[
            "retryable"
        ] is True

        assert record[
            "complete_row_sets_equal"
        ] is False

        # This is the critical distinction.
        assert record[
            "oci_sets_equal"
        ] is True

    assert not (
        out
        / "raw/opencitations/W0TEST/"
          "backward_snapshot_attempt_04"
    ).exists()


# ==================================================================
# 3. Stable count/data mismatch is retryable.
#
# Attempt 1:
#     pre=1, both complete axes actually contain 2, post=1.
# Attempt 2:
#     pre=2, both axes contain 2, post=2.
#
# Accepted production records must come only from attempt 2.
# ==================================================================

class CountDataMismatchThenStable(
    StableDualAxisFetcher
):
    def __init__(
        self,
    ):
        super().__init__()

        self.count_sequences = {
            "backward": [
                1,
                1,
                2,
                2,
            ],
            "forward": [
                2,
                2,
            ],
        }

    def count_value(
        self,
        direction,
    ):
        index = (
            self.count_calls[
                direction
            ]
        )

        # count_calls is incremented before count_value()
        return self.count_sequences[
            direction
        ][
            index - 1
        ]


with tempfile.TemporaryDirectory() as td:
    out = Path(td)

    (
        edges,
        neighbours,
        statuses,
        oci_leaves,
        creation_leaves,
        attempts,
    ) = (
        mod.retrieve_opencitations_dual_axis(
            ANCHOR,
            wave=0,
            token="",
            output_root=out,
            fetcher=
                CountDataMismatchThenStable(),
        )
    )

    backward_attempts = [
        row
        for row in attempts
        if row[
            "direction"
        ] == "backward"
    ]

    assert [
        (
            row["snapshot_attempt"],
            row["status"],
        )
        for row in backward_attempts
    ] == [
        (
            1,
            "retryable_failure",
        ),
        (
            2,
            "accepted",
        ),
    ]

    assert (
        "OCI-axis row count 2!=1"
        in backward_attempts[
            0
        ][
            "terminal_detail"
        ]
    )

    assert (
        "creation-axis row count 2!=1"
        in backward_attempts[
            0
        ][
            "terminal_detail"
        ]
    )

    accepted_backward_edges = [
        row
        for row in edges
        if row[
            "direction"
        ] == "backward"
    ]

    assert accepted_backward_edges

    assert all(
        "backward_snapshot_attempt_02/"
        in row["raw_file"]
        for row in accepted_backward_edges
    )

    assert all(
        "backward_snapshot_attempt_01/"
        not in row["raw_file"]
        for row in accepted_backward_edges
    )

    # Returned leaf ledgers represent the accepted production
    # attempt only; failed attempts remain preserved in raw/
    # and the snapshot-attempt ledger.
    assert all(
        not (
            row["direction"] == "backward"
            and int(
                row[
                    "snapshot_attempt"
                ]
            ) == 1
        )
        for row in oci_leaves
    )

    assert all(
        not (
            row["direction"] == "backward"
            and int(
                row[
                    "snapshot_attempt"
                ]
            ) == 1
        )
        for row in creation_leaves
    )


# ==================================================================
# 4. Pre/post count drift forces a fresh whole snapshot.
# ==================================================================

class CountDriftThenStable(
    StableDualAxisFetcher
):
    def __init__(
        self,
    ):
        super().__init__()

        self.count_sequences = {
            "backward": [
                2,
                3,
                2,
                2,
            ],
            "forward": [
                2,
                2,
            ],
        }

    def count_value(
        self,
        direction,
    ):
        index = (
            self.count_calls[
                direction
            ]
        )

        return self.count_sequences[
            direction
        ][
            index - 1
        ]


with tempfile.TemporaryDirectory() as td:
    out = Path(td)

    (
        edges,
        neighbours,
        statuses,
        oci_leaves,
        creation_leaves,
        attempts,
    ) = (
        mod.retrieve_opencitations_dual_axis(
            ANCHOR,
            wave=0,
            token="",
            output_root=out,
            fetcher=
                CountDriftThenStable(),
        )
    )

    backward = [
        row
        for row in attempts
        if row["direction"] == "backward"
    ]

    assert len(
        backward
    ) == 2

    assert backward[
        0
    ][
        "pre_count"
    ] == 2

    assert backward[
        0
    ][
        "post_count"
    ] == 3

    assert backward[
        0
    ][
        "status"
    ] == "retryable_failure"

    assert (
        "pre/post count disagreement 2!=3"
        in backward[
            0
        ][
            "terminal_detail"
        ]
    )

    assert backward[
        1
    ][
        "status"
    ] == "accepted"

    assert all(
        "backward_snapshot_attempt_02/"
        in row["raw_file"]
        for row in edges
        if row["direction"] == "backward"
    )


# ==================================================================
# 5. Retryable transport failure forces whole-snapshot retry.
# ==================================================================

class TransportFailureThenStable(
    StableDualAxisFetcher
):
    def __init__(
        self,
    ):
        super().__init__()
        self.failed_once = False

    def __call__(
        self,
        url,
        *,
        headers,
        raw_path,
        delay,
        retries=5,
    ):
        if (
            not self.failed_once
            and "/references/" in url
            and "filter=" in url
        ):
            field, _ = (
                parse_partition_filter(
                    url
                )
            )

            if field == "oci":
                self.failed_once = True

                try:
                    raise TimeoutError(
                        "synthetic transport timeout"
                    )
                except TimeoutError as exc:
                    raise RuntimeError(
                        "Request failed after 5 attempts: synthetic"
                    ) from exc

        return super().__call__(
            url,
            headers=headers,
            raw_path=raw_path,
            delay=delay,
            retries=retries,
        )


with tempfile.TemporaryDirectory() as td:
    out = Path(td)

    (
        edges,
        neighbours,
        statuses,
        oci_leaves,
        creation_leaves,
        attempts,
    ) = (
        mod.retrieve_opencitations_dual_axis(
            ANCHOR,
            wave=0,
            token="",
            output_root=out,
            fetcher=
                TransportFailureThenStable(),
        )
    )

    backward = [
        row
        for row in attempts
        if row["direction"] == "backward"
    ]

    assert [
        row["status"]
        for row in backward
    ] == [
        "retryable_failure",
        "accepted",
    ]

    assert backward[
        0
    ][
        "retryable"
    ] is True

    assert all(
        "backward_snapshot_attempt_02/"
        in row["raw_file"]
        for row in edges
        if row["direction"] == "backward"
    )


# ==================================================================
# 6. Stable zero requires TWO bracketing count requests and performs
#    no partition-data requests.
# ==================================================================

class StableZeroFetcher:
    def __init__(
        self,
    ):
        self.count_calls = {
            "backward": 0,
            "forward": 0,
        }
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
        direction = (
            direction_for_url(
                url
            )
        )

        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if (
            "/reference-count/" in url
            or "/citation-count/" in url
        ):
            self.count_calls[
                direction
            ] += 1

            payload = [
                {
                    "count": "0"
                }
            ]

            raw_path.write_text(
                json.dumps(
                    payload
                ),
                encoding="utf-8",
            )

            return payload

        self.data_calls += 1

        raise AssertionError(
            "zero snapshot attempted a data request"
        )


with tempfile.TemporaryDirectory() as td:
    out = Path(td)

    fetcher = (
        StableZeroFetcher()
    )

    (
        edges,
        neighbours,
        statuses,
        oci_leaves,
        creation_leaves,
        attempts,
    ) = (
        mod.retrieve_opencitations_dual_axis(
            ANCHOR,
            wave=0,
            token="",
            output_root=out,
            fetcher=fetcher,
        )
    )

    assert edges == []
    assert neighbours == []
    assert oci_leaves == []
    assert creation_leaves == []

    assert fetcher.count_calls == {
        "backward": 2,
        "forward": 2,
    }

    assert fetcher.data_calls == 0

    assert [
        row["status"]
        for row in attempts
    ] == [
        "accepted_zero",
        "accepted_zero",
    ]

    assert all(
        row["response_files"] == 2
        for row in attempts
    )

    assert all(
        row["status"]
        == "resolved_zero_edges"
        for row in statuses
    )

    assert all(
        row["response_files"] == 2
        for row in statuses
    )


# ==================================================================
# 7. Missing creation is an integrity failure, NOT a snapshot retry.
# ==================================================================

class MissingCreationFetcher(
    StableDualAxisFetcher
):
    def transform_rows(
        self,
        *,
        direction,
        field,
        rows,
    ):
        if field == "creation":
            changed = []

            for row in rows:
                row = dict(
                    row
                )
                row.pop(
                    "creation",
                    None,
                )
                changed.append(
                    row
                )

            # The fake filtering layer needs a lexical value to
            # select the affected records. Supply a sentinel solely
            # for selection, then remove it in __call__ below.
            return changed

        return rows

    def __call__(
        self,
        url,
        *,
        headers,
        raw_path,
        delay,
        retries=5,
    ):
        direction = (
            direction_for_url(
                url
            )
        )

        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if (
            "/reference-count/" in url
            or "/citation-count/" in url
        ):
            self.count_calls[
                direction
            ] += 1

            payload = [
                {
                    "count": "2"
                }
            ]

            raw_path.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            return payload

        self.data_calls[
            direction
        ] += 1

        field, regex = (
            parse_partition_filter(
                url
            )
        )

        source = (
            rows_for_direction(
                direction
            )
        )

        if field == "oci":
            payload = filter_rows(
                source,
                field,
                regex,
            )

        else:
            selected = [
                dict(row)
                for row in source
                if re.fullmatch(
                    regex,
                    row["creation"],
                )
            ]

            for row in selected:
                row.pop(
                    "creation",
                    None,
                )

            payload = selected

        raw_path.write_text(
            json.dumps(
                payload
            ),
            encoding="utf-8",
        )

        return payload


with tempfile.TemporaryDirectory() as td:
    out = Path(td)

    exc = expect_runtime(
        lambda:
            mod.retrieve_opencitations_dual_axis(
                ANCHOR,
                wave=0,
                token="",
                output_root=out,
                fetcher=
                    MissingCreationFetcher(),
            ),
        "lacks creation field",
    )

    p1 = (
        out
        / "raw/opencitations/W0TEST/"
          "backward_snapshot_attempt_01/"
          "snapshot_attempt.json"
    )

    assert p1.is_file()

    record = json.loads(
        p1.read_text(
            encoding="utf-8"
        )
    )

    assert record[
        "status"
    ] == "nonretryable_failure"

    assert record[
        "retryable"
    ] is False

    assert not (
        out
        / "raw/opencitations/W0TEST/"
          "backward_snapshot_attempt_02"
    ).exists()


# ==================================================================
# 8. Production creation partition preserves deterministic
#    IncompleteRead subdivision and does not retain failed parent.
# ==================================================================

class CreationSubdivisionFetcher:
    def __init__(
        self,
    ):
        self.rows = [
            dict(
                FORWARD_ROWS[0]
            ),
            {
                **dict(
                    FORWARD_ROWS[1]
                ),
                "creation":
                    "2021",
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
        field, regex = (
            parse_partition_filter(
                url
            )
        )

        assert field == "creation"

        if regex == r"^2.*$":
            try:
                raise (
                    http.client.IncompleteRead(
                        b'{"partial":',
                        1000,
                    )
                )
            except http.client.IncompleteRead as exc:
                raise RuntimeError(
                    "Request failed after 5 attempts: synthetic"
                ) from exc

        payload = [
            dict(row)
            for row in self.rows
            if re.fullmatch(
                regex,
                row["creation"],
            )
        ]

        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        raw_path.write_text(
            json.dumps(
                payload
            ),
            encoding="utf-8",
        )

        return payload


with tempfile.TemporaryDirectory() as td:
    out = Path(td)

    raw_root = (
        out
        / "raw/opencitations/W0TEST/"
          "forward_snapshot_attempt_01/"
          "creation_axis"
    )

    (
        rows,
        leaves,
    ) = (
        mod.retrieve_opencitations_creation_partitioned(
            anchor=
                ANCHOR,
            direction=
                "forward",
            doi=
                "10.1000/test",
            expected_count=
                2,
            wave=
                0,
            snapshot_attempt=
                1,
            headers={},
            raw_root=
                raw_root,
            output_root=
                out,
            fetcher=
                CreationSubdivisionFetcher(),
        )
    )

    assert len(
        rows
    ) == 2

    assert max(
        int(
            row[
                "recursion_depth"
            ]
        )
        for row in leaves
    ) == 1

    assert any(
        row[
            "partition_kind"
        ] == "exact"
        and row[
            "literal_prefix"
        ] == "2"
        for row in leaves
    )

    failed_parent = (
        raw_root
        / "creation_partitions/"
          "depth_00/prefix_2.json"
    )

    assert not (
        failed_parent.exists()
    )


# ==================================================================
# 9. Main output wiring:
#    new ledgers + manifest schema 2 + checksums.
#
# Retrieval functions are replaced with in-memory fakes. No network.
# ==================================================================

with tempfile.TemporaryDirectory() as td:
    root = Path(td)

    anchors_path = (
        root
        / "anchors.tsv"
    )

    anchors_path.write_text(
        "synthetic-anchor-input\n",
        encoding="utf-8",
    )

    output = (
        root
        / "wave"
    )

    sample_oci_leaf = {
        "wave": 0,
        "anchor_id": "W0TEST",
        "anchor_tool": "TEST",
        "direction": "backward",
        "snapshot_attempt": 1,
        "leaf_order": 1,
        "recursion_depth": 0,
        "suffix_digits": 1,
        "partition_kind": "suffix",
        "suffix": "2",
        "leaf_regex": r"^[0-9]+-[0-9]*2$",
        "request_sha256": "a" * 64,
        "raw_file": (
            "raw/opencitations/W0TEST/"
            "backward_snapshot_attempt_01/"
            "oci_axis/backward_partitions/"
            "depth_00/digits_01_suffix_2.json"
        ),
        "row_count": 0,
    }

    sample_creation_leaf = {
        "wave": 0,
        "anchor_id": "W0TEST",
        "anchor_tool": "TEST",
        "direction": "backward",
        "snapshot_attempt": 1,
        "leaf_order": 1,
        "recursion_depth": 0,
        "partition_kind": "empty",
        "literal_prefix": "",
        "leaf_regex": r"^$",
        "request_sha256": "b" * 64,
        "raw_file": (
            "raw/opencitations/W0TEST/"
            "backward_snapshot_attempt_01/"
            "creation_axis/creation_partitions/"
            "depth_00/empty_EMPTY.json"
        ),
        "row_count": 0,
    }

    empty_hash = (
        mod.hash_sorted_strings(
            set()
        )
    )

    def fake_read_anchors(
        path,
        wave,
    ):
        return [
            dict(
                ANCHOR
            )
        ]

    def fake_openalex(
        anchor,
        *,
        wave,
        api_key,
        output_root,
        fetcher=mod.fetch_json,
    ):
        return (
            [],
            [],
            [
                {
                    "wave": wave,
                    "anchor_id":
                        anchor[
                            "anchor_id"
                        ],
                    "anchor_tool":
                        anchor[
                            "tool"
                        ],
                    "source":
                        "openalex",
                    "direction":
                        "backward",
                    "status":
                        "resolved_zero_edges",
                    "reported_count":
                        0,
                    "retrieved_count":
                        0,
                    "response_files":
                        1,
                    "terminal_detail":
                        "synthetic",
                },
                {
                    "wave": wave,
                    "anchor_id":
                        anchor[
                            "anchor_id"
                        ],
                    "anchor_tool":
                        anchor[
                            "tool"
                        ],
                    "source":
                        "openalex",
                    "direction":
                        "forward",
                    "status":
                        "resolved_zero_edges",
                    "reported_count":
                        0,
                    "retrieved_count":
                        0,
                    "response_files":
                        1,
                    "terminal_detail":
                        "synthetic",
                },
            ],
        )

    def fake_dual(
        anchor,
        *,
        wave,
        token,
        output_root,
        fetcher=mod.fetch_json,
        maximum_snapshot_attempts=(
            mod.OPENCITATIONS_MAX_SNAPSHOT_ATTEMPTS
        ),
    ):
        statuses = []

        attempts = []

        for direction in [
            "backward",
            "forward",
        ]:
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
                    2,
                "terminal_detail":
                    "synthetic dual-axis zero",
            })

            attempts.append({
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
                "direction":
                    direction,
                "snapshot_attempt":
                    1,
                "status":
                    "accepted_zero",
                "retryable":
                    False,
                "pre_count":
                    0,
                "post_count":
                    0,
                "oci_row_count":
                    0,
                "creation_row_count":
                    0,
                "oci_complete_row_sha256":
                    empty_hash,
                "creation_complete_row_sha256":
                    empty_hash,
                "oci_set_sha256":
                    empty_hash,
                "creation_oci_set_sha256":
                    empty_hash,
                "complete_row_sets_equal":
                    True,
                "oci_sets_equal":
                    True,
                "oci_leaf_count":
                    0,
                "creation_leaf_count":
                    0,
                "oci_max_recursion_depth":
                    0,
                "creation_max_recursion_depth":
                    0,
                "response_files":
                    2,
                "terminal_detail":
                    "synthetic",
            })

        oci_leaf = dict(
            sample_oci_leaf
        )

        creation_leaf = dict(
            sample_creation_leaf
        )

        return (
            [],
            [],
            statuses,
            [
                oci_leaf
            ],
            [
                creation_leaf
            ],
            attempts,
        )

    original_read = (
        mod.read_anchors
    )
    original_oa = (
        mod.retrieve_openalex
    )
    original_dual = (
        mod.retrieve_opencitations_dual_axis
    )
    original_argv = list(
        sys.argv
    )
    original_api_key = (
        os.environ.get(
            "OPENALEX_API_KEY"
        )
    )
    original_oc_token = (
        os.environ.get(
            "OPENCITATIONS_ACCESS_TOKEN"
        )
    )

    try:
        mod.read_anchors = (
            fake_read_anchors
        )
        mod.retrieve_openalex = (
            fake_openalex
        )
        mod.retrieve_opencitations_dual_axis = (
            fake_dual
        )

        os.environ[
            "OPENALEX_API_KEY"
        ] = "SYNTHETIC_NOT_WRITTEN"

        os.environ.pop(
            "OPENCITATIONS_ACCESS_TOKEN",
            None,
        )

        sys.argv = [
            str(SCRIPT),
            "--anchors",
            str(
                anchors_path
            ),
            "--wave",
            "0",
            "--output",
            str(
                output
            ),
        ]

        rc = mod.main()

    finally:
        mod.read_anchors = (
            original_read
        )
        mod.retrieve_openalex = (
            original_oa
        )
        mod.retrieve_opencitations_dual_axis = (
            original_dual
        )
        sys.argv = (
            original_argv
        )

        if original_api_key is None:
            os.environ.pop(
                "OPENALEX_API_KEY",
                None,
            )
        else:
            os.environ[
                "OPENALEX_API_KEY"
            ] = original_api_key

        if original_oc_token is None:
            os.environ.pop(
                "OPENCITATIONS_ACCESS_TOKEN",
                None,
            )
        else:
            os.environ[
                "OPENCITATIONS_ACCESS_TOKEN"
            ] = original_oc_token

    assert rc == 0

    required_outputs = {
        "citation_edges.tsv",
        "neighbour_records.tsv",
        "source_status.tsv",
        "opencitations_partition_leaves.tsv",
        "opencitations_creation_partition_leaves.tsv",
        "opencitations_snapshot_attempts.tsv",
        "retrieval_manifest.json",
        "checksums.sha256",
    }

    observed_outputs = {
        path.name
        for path in output.iterdir()
        if path.is_file()
    }

    assert required_outputs <= observed_outputs

    manifest = json.loads(
        (
            output
            / "retrieval_manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert manifest[
        "schema_version"
    ] == 3

    assert manifest[
        "opencitations_snapshot_reconciliation"
    ] == (
        "dual_axis_exact_or_verified_forward_oci_plus_creation_missing"
    )

    assert manifest[
        "opencitations_canonical_production_axis"
    ] == (
        "oci_or_oci_plus_verified_creation_missing"
    )

    assert manifest[
        "opencitations_snapshot_attempt_rows"
    ] == 2

    assert manifest[
        "opencitations_oci_partition_leaf_rows"
    ] == 1

    assert manifest[
        "opencitations_creation_partition_leaf_rows"
    ] == 1

    checksums = (
        output
        / "checksums.sha256"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "opencitations_creation_partition_leaves.tsv"
        in checksums
    )

    assert (
        "opencitations_snapshot_attempts.tsv"
        in checksums
    )

    combined_bytes = b"".join(
        path.read_bytes()
        for path in output.iterdir()
        if path.is_file()
    )

    assert (
        b"SYNTHETIC_NOT_WRITTEN"
        not in combined_bytes
    )




# ==================================================================
# Verified forward-provider reconciliation.
#
# Synthetic analogue of the live W0A07 behaviour:
#
# reported count = 4
#
# Stable OCI axis:
#   shared A
#   work B, representation B1
#   work C, representation C1
#
# Creation attempt 1:
#   shared A
#   B1
#   C2 (alias of C1)
#   genuinely missing work D
#
# Creation attempts 2 and 3:
#   shared A
#   C1
#   B2 (alias of B1)
#   genuinely missing work D
#
# Thus the raw creation-axis complete-row set changes, but:
#
#   canonical production =
#       stable OCI axis
#       + genuinely missing work D
#
# is exactly identical across all three attempts.
#
# Every cross-axis discrepant row has exactly one OpenAlex citing-work
# identity. Alias rows pair by that identity. The unmatched creation
# row is absent from the complete OCI axis and accounts exactly for
# the one-row count deficit.
#
# All unique discrepant OCIs across all three attempts must then be
# verified directly through /citation/{oci}.
# ==================================================================

PROVIDER_SHARED = {
    "oci":
        "101-201",
    "citing":
        "omid:br/101 doi:10.2000/shared "
        "openalex:W100000001",
    "cited":
        "omid:br/201 doi:10.1000/test "
        "openalex:W900000001",
    "creation":
        "2010",
    "timespan":
        "P0Y",
    "journal_sc":
        "no",
    "author_sc":
        "no",
}

PROVIDER_B_OCI = {
    "oci":
        "301-201",
    "citing":
        "omid:br/301 doi:10.2000/b "
        "openalex:W100000002",
    "cited":
        "omid:br/201 doi:10.1000/test "
        "openalex:W900000001",
    "creation":
        "2018",
    "timespan":
        "P8Y",
    "journal_sc":
        "no",
    "author_sc":
        "no",
}

PROVIDER_B_ALIAS = {
    "oci":
        "302-201",
    "citing":
        "omid:br/302 openalex:W100000002 pmid:3002",
    "cited":
        "omid:br/201 doi:10.1000/test "
        "openalex:W900000001",
    "creation":
        "2018-05-31",
    "timespan":
        "P8Y4M",
    "journal_sc":
        "no",
    "author_sc":
        "no",
}

PROVIDER_C_OCI = {
    "oci":
        "401-201",
    "citing":
        "omid:br/401 openalex:W100000003 pmid:4001",
    "cited":
        "omid:br/201 doi:10.1000/test "
        "openalex:W900000001",
    "creation":
        "2017",
    "timespan":
        "P7Y",
    "journal_sc":
        "no",
    "author_sc":
        "no",
}

PROVIDER_C_ALIAS = {
    "oci":
        "402-201",
    "citing":
        "omid:br/402 doi:10.2000/c "
        "openalex:W100000003",
    "cited":
        "omid:br/201 doi:10.1000/test "
        "openalex:W900000001",
    "creation":
        "2017-06-01",
    "timespan":
        "P7Y5M",
    "journal_sc":
        "no",
    "author_sc":
        "no",
}

PROVIDER_MISSING = {
    "oci":
        "501-201",
    "citing":
        "omid:br/501 doi:10.2000/missing "
        "openalex:W100000004",
    "cited":
        "omid:br/201 doi:10.1000/test "
        "openalex:W900000001",
    "creation":
        "2008",
    "timespan":
        "P0Y",
    "journal_sc":
        "no",
    "author_sc":
        "no",
}


class VolatileProviderAliasFetcher(
    StableDualAxisFetcher
):
    def __init__(
        self,
    ):
        super().__init__()

        self.direct_calls = []

        self.direct_rows = {
            row["oci"]:
                row
            for row in [
                PROVIDER_B_OCI,
                PROVIDER_B_ALIAS,
                PROVIDER_C_OCI,
                PROVIDER_C_ALIAS,
                PROVIDER_MISSING,
            ]
        }

    def count_value(
        self,
        direction,
    ):
        if direction == "forward":
            return 4

        return 2

    def transform_rows(
        self,
        *,
        direction,
        field,
        rows,
    ):
        if direction != "forward":
            return rows

        if field == "oci":
            return [
                dict(PROVIDER_SHARED),
                dict(PROVIDER_B_OCI),
                dict(PROVIDER_C_OCI),
            ]

        if field != "creation":
            raise AssertionError(
                f"Unexpected field: {field}"
            )

        # During partition retrieval the forward pre-count has
        # already occurred, while the post-count has not.
        #
        # count_calls = 1,3,5 for attempts 1,2,3.
        attempt = (
            self.count_calls[
                "forward"
            ]
            + 1
        ) // 2

        if attempt == 1:
            return [
                dict(PROVIDER_SHARED),
                dict(PROVIDER_B_OCI),
                dict(PROVIDER_C_ALIAS),
                dict(PROVIDER_MISSING),
            ]

        return [
            dict(PROVIDER_SHARED),
            dict(PROVIDER_C_OCI),
            dict(PROVIDER_B_ALIAS),
            dict(PROVIDER_MISSING),
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
        parsed = urllib.parse.urlparse(
            url
        )

        if (
            "/citation/" in parsed.path
            and "/citations/" not in parsed.path
        ):
            oci = urllib.parse.unquote(
                parsed.path.rsplit(
                    "/",
                    1,
                )[-1]
            )

            if oci not in self.direct_rows:
                raise AssertionError(
                    f"Unexpected direct OCI lookup: {oci}"
                )

            self.direct_calls.append(
                oci
            )

            payload = [
                dict(
                    self.direct_rows[
                        oci
                    ]
                )
            ]

            raw_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            raw_path.write_text(
                json.dumps(
                    payload
                ),
                encoding="utf-8",
            )

            return payload

        return super().__call__(
            url,
            headers=headers,
            raw_path=raw_path,
            delay=delay,
            retries=retries,
        )


with tempfile.TemporaryDirectory() as td:
    out = Path(td)

    fetcher = (
        VolatileProviderAliasFetcher()
    )

    (
        edges,
        neighbours,
        statuses,
        oci_leaves,
        creation_leaves,
        attempts,
    ) = (
        mod.retrieve_opencitations_dual_axis(
            ANCHOR,
            wave=0,
            token="",
            output_root=out,
            fetcher=fetcher,
        )
    )

    forward = [
        row
        for row in attempts
        if row[
            "direction"
        ] == "forward"
    ]

    assert [
        row["status"]
        for row in forward
    ] == [
        "retryable_failure",
        "retryable_failure",
        "accepted_provider_reconciled",
    ]

    # Raw creation snapshots are deliberately NOT stable.
    assert (
        forward[0][
            "creation_complete_row_sha256"
        ]
        !=
        forward[1][
            "creation_complete_row_sha256"
        ]
    )

    assert (
        forward[1][
            "creation_complete_row_sha256"
        ]
        ==
        forward[2][
            "creation_complete_row_sha256"
        ]
    )

    # The reconciled production set must nevertheless be identical
    # across all three independent attempts.
    assert len({
        row[
            "provider_reconciled_complete_row_sha256"
        ]
        for row in forward
    }) == 1

    assert len({
        row[
            "provider_reconciled_oci_set_sha256"
        ]
        for row in forward
    }) == 1

    for row in forward:
        assert row[
            "provider_reconciliation_candidate"
        ] is True

        assert row[
            "provider_reconciled_row_count"
        ] == 4

        assert row[
            "provider_alias_pair_count"
        ] == 1

        assert row[
            "provider_missing_row_count"
        ] == 1

        assert row[
            "provider_discrepant_oci_count"
        ] == 3

    accepted = forward[-1]

    assert accepted[
        "provider_reconciliation"
    ] is True

    assert accepted[
        "production_axis"
    ] == "oci_plus_verified_creation_missing"

    # Five unique discrepant OCIs appeared across the three attempts:
    # B1, B2, C1, C2, and missing D.
    assert accepted[
        "provider_direct_lookup_count"
    ] == 5

    assert sorted(
        fetcher.direct_calls
    ) == sorted([
        "301-201",
        "302-201",
        "401-201",
        "402-201",
        "501-201",
    ])

    forward_edges = [
        row
        for row in edges
        if row[
            "direction"
        ] == "forward"
    ]

    assert len(
        forward_edges
    ) == 4

    assert sum(
        "/oci_axis/"
        in row[
            "raw_file"
        ]
        for row in forward_edges
    ) == 3

    assert sum(
        "/creation_axis/"
        in row[
            "raw_file"
        ]
        for row in forward_edges
    ) == 1

    forward_status = [
        row
        for row in statuses
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
    ] == "complete_provider_reconciled"

    assert forward_status[
        0
    ][
        "reported_count"
    ] == 4

    assert forward_status[
        0
    ][
        "retrieved_count"
    ] == 4

    evidence = (
        out
        / "raw/opencitations/W0TEST/"
          "forward_snapshot_attempt_03/"
          "provider_reconciliation.json"
    )

    assert evidence.is_file()



# The exceptional completion state must also satisfy the final
# source-direction matrix validator used by main().
provider_terminal_matrix = []

for source in (
    "openalex",
    "opencitations",
):
    for direction in (
        "backward",
        "forward",
    ):
        status = "complete"

        if (
            source == "opencitations"
            and direction == "forward"
        ):
            status = (
                "complete_provider_reconciled"
            )

        provider_terminal_matrix.append({
            "anchor_id":
                ANCHOR[
                    "anchor_id"
                ],
            "source":
                source,
            "direction":
                direction,
            "status":
                status,
            "reported_count":
                1,
            "retrieved_count":
                1,
        })

mod.validate_status_matrix(
    [ANCHOR],
    provider_terminal_matrix,
)

print(
    "PASS | status matrix accepts provider-reconciled terminal status"
)

print("PASS | volatile raw aliases reconcile to stable production")
print("PASS | stable positive dual-axis snapshot accepted")
print("PASS | pre/post counts bracket both partition axes")
print("PASS | both axes independently match the stable count")
print("PASS | complete-row equality is order-independent")
print("PASS | production edges use OCI-axis raw provenance only")
print("PASS | empty creation values survive independent witness partition")
print("PASS | same OCI set but different complete rows is rejected")
print("PASS | cross-axis mismatch retries exactly three whole snapshots")
print("PASS | stable count/data mismatch triggers fresh whole snapshot")
print("PASS | failed snapshot rows are not reused in accepted production output")
print("PASS | pre/post source drift triggers fresh whole snapshot")
print("PASS | exhausted retryable transport failure triggers fresh whole snapshot")
print("PASS | stable zero is bracketed by two independent count requests")
print("PASS | stable zero performs no partition-data requests")
print("PASS | missing creation is a non-retryable integrity failure")
print("PASS | non-retryable integrity failure does not start attempt 2")
print("PASS | creation IncompleteRead subdivision remains deterministic")
print("PASS | failed creation parent response is not retained")
print("PASS | main writes independent creation-partition ledger")
print("PASS | main writes snapshot-attempt reconciliation ledger")
print("PASS | manifest schema 3 records exact-or-verified reconciliation")
print("PASS | checksum manifest includes both new production ledgers")
print("PASS | credential value absent from generated outputs")
print("PASS | dedicated snapshot-reconciliation tests made zero network requests")
