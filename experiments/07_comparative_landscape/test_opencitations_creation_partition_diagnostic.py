#!/usr/bin/env python3

from __future__ import annotations

import http.client
import importlib.util
import json
import re
import tempfile
import urllib.parse

from collections import Counter
from pathlib import Path
from unittest.mock import patch


ROOT = Path(
    "experiments/07_comparative_landscape"
)

SCRIPT = (
    ROOT
    / "run_opencitations_creation_partition_diagnostic.py"
)

ARCHIVE = (
    ROOT
    / "audit/citation_wave_0_attempt_05_count_mismatch/"
      "partial_wave_0_raw.tar.gz"
)

spec = importlib.util.spec_from_file_location(
    "creation_diag",
    SCRIPT,
)

if spec is None or spec.loader is None:
    raise RuntimeError(
        "Cannot import Diagnostic-02 implementation"
    )

mod = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    mod
)


def expect_runtime(
    fn,
    contains: str,
) -> None:
    try:
        fn()
    except RuntimeError as exc:
        if contains not in str(
            exc
        ):
            raise AssertionError(
                f"{contains!r} absent from {str(exc)!r}"
            )
    else:
        raise AssertionError(
            f"Expected RuntimeError containing {contains!r}"
        )


# ------------------------------------------------------------
# Frozen Attempt-05 comparator identity.
# ------------------------------------------------------------

attempt_rows, attempt_ocis = (
    mod.load_attempt05_rows(
        ARCHIVE
    )
)

assert len(
    attempt_rows
) == 12845

assert len(
    attempt_ocis
) == 12845

signatures = [
    mod.canonical_row_signature(
        row
    )
    for row in attempt_rows
]

assert len(
    signatures
) == len(
    set(signatures)
)

digest = mod.hashlib.sha256(
    "\n".join(
        sorted(signatures)
    ).encode("utf-8")
).hexdigest()

assert (
    digest
    ==
    mod.EXPECTED_ATTEMPT05_ROW_MULTISET_SHA256
)


# ------------------------------------------------------------
# Root partition is exhaustive/disjoint for every REAL
# archived creation value.
# ------------------------------------------------------------

roots = (
    mod.root_leaves()
)

for row in attempt_rows:
    creation = row[
        "creation"
    ]

    hits = [
        leaf
        for leaf in roots
        if re.fullmatch(
            leaf["regex"],
            creation,
        )
    ]

    if len(hits) != 1:
        raise AssertionError(
            f"root membership for {creation!r}: {len(hits)}"
        )


# ------------------------------------------------------------
# Recursive children partition representative parent languages.
# ------------------------------------------------------------

tests = {
    "2": [
        "2",
        "20",
        "29",
        "2-",
        "2x",
        "2021",
        "2021-03",
    ],
    "2021": [
        "2021",
        "20210",
        "20219",
        "2021-",
        "2021x",
        "2021-03",
        "2021-03-10",
    ],
    "2021-03": [
        "2021-03",
        "2021-030",
        "2021-039",
        "2021-03-",
        "2021-03x",
        "2021-03-10",
    ],
}

for prefix, values in tests.items():
    parent = re.compile(
        rf"^{re.escape(prefix)}.*$"
    )

    children = (
        mod.prefix_children(
            prefix,
            depth=1,
        )
    )

    assert len(
        children
    ) == 13

    for value in values:
        assert parent.fullmatch(
            value
        )

        hits = sum(
            bool(
                re.fullmatch(
                    child[
                        "regex"
                    ],
                    value,
                )
            )
            for child in children
        )

        if hits != 1:
            raise AssertionError(
                (
                    prefix,
                    value,
                    hits,
                )
            )


# ------------------------------------------------------------
# Leaf validation.
# ------------------------------------------------------------

valid = {
    "creation":
        "2021",
    "oci":
        "1-2",
}

assert (
    mod.validate_leaf_rows(
        [valid],
        leaf_regex=
            r"^2021$",
    )
    == [valid]
)

expect_runtime(
    lambda:
        mod.validate_leaf_rows(
            [
                {
                    "oci":
                        "1-2",
                }
            ],
            leaf_regex=
                r"^2021$",
        ),
    "lacks creation field",
)

expect_runtime(
    lambda:
        mod.validate_leaf_rows(
            [
                {
                    "creation":
                        None,
                    "oci":
                        "1-2",
                }
            ],
            leaf_regex=
                r"^$",
        ),
    "not a string",
)

expect_runtime(
    lambda:
        mod.validate_leaf_rows(
            [
                {
                    "creation":
                        "2020",
                    "oci":
                        "1-2",
                }
            ],
            leaf_regex=
                r"^2021$",
        ),
    "does not belong",
)


# ------------------------------------------------------------
# Complete-row duplicate prohibition.
# ------------------------------------------------------------

row = {
    "creation":
        "2021",
    "oci":
        "1-2",
}

expect_runtime(
    lambda:
        mod.validate_unique_complete_rows(
            [
                (
                    row,
                    Path("a.json"),
                ),
                (
                    dict(row),
                    Path("b.json"),
                ),
            ]
        ),
    "Duplicate complete citation row",
)


# ------------------------------------------------------------
# OCI analysis is independent of partition membership.
# ------------------------------------------------------------

analysis = mod.analyse_oci(
    [
        {
            "creation": "",
            "oci": "1-2",
        },
        {
            "creation": "2021",
            "oci": "3-4",
        },
        {
            "creation": "2021-03",
            "oci": "3-4",
        },
        {
            "creation": "2021-03-01",
            "oci": "",
        },
        {
            "creation": "2022",
            "oci": "bad",
        },
    ],
    attempt05_ocis={
        "1-2",
        "5-6",
    },
)

assert (
    analysis[
        "empty_oci_rows"
    ]
    == 1
)

assert (
    analysis[
        "nonconforming_oci_rows"
    ]
    == 1
)

assert (
    analysis[
        "valid_numeric_oci_rows"
    ]
    == 3
)

assert (
    analysis[
        "unique_valid_numeric_ocis"
    ]
    == 2
)

assert (
    analysis[
        "duplicate_valid_oci_count"
    ]
    == 1
)

assert (
    analysis[
        "creation_only_ocis"
    ]
    == [
        "3-4",
    ]
)

assert (
    analysis[
        "attempt05_only_ocis"
    ]
    == [
        "5-6",
    ]
)


# ------------------------------------------------------------
# Interpretation matrix.
# ------------------------------------------------------------

assert (
    mod.classify_result(
        pre_count=12846,
        post_count=12847,
        row_count=12846,
    )
    ==
    "COUNT_CHANGED_DURING_INTERVAL"
)

assert (
    mod.classify_result(
        pre_count=12846,
        post_count=12846,
        row_count=12846,
    )
    ==
    "STABLE_12846_COUNT_AND_12846_CREATION_ROWS"
)

assert (
    mod.classify_result(
        pre_count=12846,
        post_count=12846,
        row_count=12845,
    )
    ==
    "STABLE_12846_COUNT_AND_12845_CREATION_ROWS"
)


# ------------------------------------------------------------
# Fake source built from REAL Attempt-05 rows + one extra.
#
# It deliberately raises IncompleteRead for filtered sets
# larger than 1000 rows. This forces recursive creation
# partitioning on the actual observed creation distribution.
# ------------------------------------------------------------

extra_oci = (
    "999999999999999999-"
    "999999999999999999"
)

assert (
    extra_oci
    not in attempt_ocis
)

extra = {
    "author_sc":
        "no",
    "cited":
        "doi:10.1093/molbev/msm088",
    "citing":
        "doi:10.9999/extra",
    "creation":
        "2026-09-23",
    "journal_sc":
        "no",
    "oci":
        extra_oci,
    "timespan":
        "P0Y",
}

source_rows = [
    dict(row)
    for row in attempt_rows
] + [
    extra
]


class FakeFetcher:
    def __init__(
        self,
    ):
        self.calls = []

    def __call__(
        self,
        url,
        *,
        headers,
        raw_path,
        delay,
        **kwargs,
    ):
        self.calls.append(
            url
        )

        raw_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if "/citation-count/" in url:
            payload = [
                {
                    "count":
                        "12846",
                }
            ]

            raw_path.write_text(
                json.dumps(
                    payload
                ),
                encoding="utf-8",
            )

            return (
                payload,
                {
                    "url":
                        url,
                    "attempt":
                        1,
                    "bytes":
                        raw_path.stat().st_size,
                },
            )

        if "/citations/" not in url:
            raise AssertionError(
                f"unexpected URL: {url}"
            )

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
                f"missing filter: {url}"
            )

        value = values[0]

        if not value.startswith(
            "creation:"
        ):
            raise AssertionError(
                f"non-creation filter: {value}"
            )

        regex = value[
            len("creation:"):
        ]

        selected = [
            row
            for row in source_rows
            if re.fullmatch(
                regex,
                row["creation"],
            )
        ]

        if len(selected) > 1000:
            try:
                raise (
                    http.client.IncompleteRead(
                        b'{"partial":',
                        1000,
                    )
                )
            except http.client.IncompleteRead as exc:
                raise RuntimeError(
                    "Diagnostic request failed after "
                    "5 attempts: synthetic"
                ) from exc

        raw_path.write_text(
            json.dumps(
                selected,
            ),
            encoding="utf-8",
        )

        return (
            selected,
            {
                "url":
                    url,
                "attempt":
                    1,
                "bytes":
                    raw_path.stat().st_size,
            },
        )


with tempfile.TemporaryDirectory() as td:
    out = (
        Path(td)
        / "diag"
    )

    fetcher = (
        FakeFetcher()
    )

    with patch(
        "urllib.request.urlopen",
        side_effect=AssertionError(
            "network prohibited"
        ),
    ):
        summary = (
            mod.run_diagnostic(
                output_root=
                    out,
                attempt05_archive=
                    ARCHIVE,
                token=
                    "",
                fetcher=
                    fetcher,
            )
        )

    assert (
        summary[
            "pre_count"
        ]
        == 12846
    )

    assert (
        summary[
            "post_count"
        ]
        == 12846
    )

    assert (
        summary[
            "creation_partition_rows"
        ]
        == 12846
    )

    assert (
        summary[
            "unique_complete_rows"
        ]
        == 12846
    )

    assert (
        summary[
            "unique_valid_numeric_ocis"
        ]
        == 12846
    )

    assert (
        summary[
            "creation_only_oci_count"
        ]
        == 1
    )

    assert (
        summary[
            "attempt05_only_oci_count"
        ]
        == 0
    )

    assert (
        summary[
            "interpretation_class"
        ]
        ==
        "STABLE_12846_COUNT_AND_12846_CREATION_ROWS"
    )

    assert (
        summary[
            "max_recursion_depth"
        ]
        > 0
    )

    # The 119 genuinely empty archived creation values must
    # survive the independent partition.
    empty_leaf = [
        leaf
        for leaf in (
            json.loads(
                json.dumps([])
            )
            or []
        )
    ]

    leaf_tsv = (
        out
        / "creation_partition_leaves.tsv"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "\tempty\t\t^$\t"
        in leaf_tsv
    )

    empty_raw = (
        out
        / "raw/creation_partitions/"
          "depth_00/empty_EMPTY.json"
    )

    empty_payload = json.loads(
        empty_raw.read_text(
            encoding="utf-8"
        )
    )

    assert len(
        empty_payload
    ) == 119

    # Failed oversized parent leaves must never be persisted.
    failed_root_2 = (
        out
        / "raw/creation_partitions/"
          "depth_00/prefix_2.json"
    )

    assert not (
        failed_root_2.exists()
    )

    values = (
        out
        / "creation_only_ocis.tsv"
    ).read_text(
        encoding="utf-8"
    ).splitlines()

    assert values == [
        "oci",
        extra_oci,
    ]

    assert (
        json.loads(
            (
                out
                / "diagnostic_summary.json"
            ).read_text(
                encoding="utf-8"
            )
        )[
            "production_corpus"
        ]
        is False
    )


# ------------------------------------------------------------
# Non-IncompleteRead failures must not trigger subdivision.
# ------------------------------------------------------------

class OtherFailure:
    def __init__(self):
        self.calls = 0

    def __call__(
        self,
        url,
        *,
        headers,
        raw_path,
        delay,
        **kwargs,
    ):
        self.calls += 1

        try:
            raise TimeoutError(
                "synthetic timeout"
            )
        except TimeoutError as exc:
            raise RuntimeError(
                "Diagnostic request failed after 5 attempts"
            ) from exc


with tempfile.TemporaryDirectory() as td:
    output = Path(td)

    expect_runtime(
        lambda:
            mod.retrieve_creation_partitioned(
                output_root=
                    output,
                headers={},
                fetcher=
                    OtherFailure(),
            ),
        "Diagnostic request failed",
    )


# ------------------------------------------------------------
# Recursion ceiling fails closed.
# ------------------------------------------------------------

class AlwaysIncomplete:
    def __call__(
        self,
        url,
        *,
        headers,
        raw_path,
        delay,
        **kwargs,
    ):
        # Empty and non-digit roots must succeed so execution
        # reaches the first subdividable digit-prefix bucket.
        query = urllib.parse.parse_qs(
            urllib.parse.urlparse(
                url
            ).query
        )

        regex = query[
            "filter"
        ][0][
            len("creation:"):
        ]

        if regex in {
            r"^$",
            r"^[^0-9].*$",
        }:
            raw_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            raw_path.write_text(
                "[]",
                encoding="utf-8",
            )

            return (
                [],
                {
                    "url":
                        url,
                    "attempt":
                        1,
                    "bytes":
                        2,
                },
            )

        try:
            raise http.client.IncompleteRead(
                b"partial",
                100,
            )
        except http.client.IncompleteRead as exc:
            raise RuntimeError(
                "Diagnostic request failed after 5 attempts"
            ) from exc


with tempfile.TemporaryDirectory() as td:
    expect_runtime(
        lambda:
            mod.retrieve_creation_partitioned(
                output_root=
                    Path(td),
                headers={},
                fetcher=
                    AlwaysIncomplete(),
                max_prefix_characters=
                    1,
            ),
        "recursion ceiling",
    )


print("PASS | Attempt-05 complete-row identity")
print("PASS | all 12845 real creation values occupy exactly one root bucket")
print("PASS | exact+digit+hyphen+other recursive partition is disjoint")
print("PASS | reduced-precision creation strings preserved")
print("PASS | missing creation fails closed")
print("PASS | non-string creation fails closed")
print("PASS | out-of-leaf creation fails closed")
print("PASS | duplicate complete rows fail closed")
print("PASS | OCI analysis independent of creation partition")
print("PASS | interpretation matrix")
print("PASS | real Attempt-05 rows + one synthetic row reconstruct 12846")
print("PASS | recursive subdivision exercised on real creation distribution")
print("PASS | all 119 empty creation values preserved")
print("PASS | failed oversized parent response not persisted")
print("PASS | one synthetic extra OCI isolated exactly")
print("PASS | unrelated persistent failure does not subdivide")
print("PASS | recursion ceiling fails closed")
print("PASS | Diagnostic-02 explicitly remains non-production")
print("PASS | offline Diagnostic-02 tests made zero network requests")
