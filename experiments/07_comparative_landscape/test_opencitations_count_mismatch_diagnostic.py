#!/usr/bin/env python3
"""
Offline tests for the frozen OpenCitations count-mismatch diagnostic.

No network access is permitted.
"""

from __future__ import annotations

import csv
import http.client
import importlib.util
import io
import json
import tempfile

from pathlib import Path
from unittest.mock import patch


ROOT = Path(
    "experiments/07_comparative_landscape"
)

SCRIPT = (
    ROOT
    / "run_opencitations_count_mismatch_diagnostic.py"
)

ARCHIVE = (
    ROOT
    / "audit/citation_wave_0_attempt_05_count_mismatch/"
      "partial_wave_0_raw.tar.gz"
)

spec = importlib.util.spec_from_file_location(
    "oc_count_mismatch_diagnostic",
    SCRIPT,
)

if spec is None or spec.loader is None:
    raise RuntimeError(
        "Could not import diagnostic retriever"
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
                f"{contains!r} not found in "
                f"{str(exc)!r}"
            )
    else:
        raise AssertionError(
            "Expected RuntimeError containing "
            f"{contains!r}"
        )


# ------------------------------------------------------------
# Frozen URLs.
# ------------------------------------------------------------

assert (
    mod.citation_count_url()
    ==
    "https://api.opencitations.net/index/v2/"
    "citation-count/"
    "doi:10.1093%2Fmolbev%2Fmsm088"
)

assert (
    mod.citations_url()
    ==
    "https://api.opencitations.net/index/v2/"
    "citations/"
    "doi:10.1093%2Fmolbev%2Fmsm088"
)


# ------------------------------------------------------------
# Attempt-05 committed archive reconstruction.
# ------------------------------------------------------------

attempt05_ocis = (
    mod.load_attempt05_oci_union(
        ARCHIVE
    )
)

assert len(
    attempt05_ocis
) == 12845


# ------------------------------------------------------------
# Count parser.
# ------------------------------------------------------------

assert (
    mod.parse_count_body(
        b'[{"count":"12846"}]'
    )
    == 12846
)

for bad in [
    b"",
    b"not-json",
    b"[]",
    b'[{"other":"1"}]',
    b'[{"count":"-1"}]',
    b'[{"count":"abc"}]',
]:
    expect_runtime(
        lambda bad=bad:
            mod.parse_count_body(
                bad
            ),
        (
            "citation-count"
            if bad in {
                b"",
                b"not-json",
            }
            else ""
        ),
    )


# ------------------------------------------------------------
# CSV structural parser.
# ------------------------------------------------------------

body = (
    "oci,citing,cited,creation\n"
    "1-2,doi:10.1/a,doi:10.1/b,2020-01-01\n"
).encode(
    "utf-8"
)

fields, rows = (
    mod.parse_csv_body(
        body
    )
)

assert fields == [
    "oci",
    "citing",
    "cited",
    "creation",
]

assert rows == [
    {
        "oci": "1-2",
        "citing": "doi:10.1/a",
        "cited": "doi:10.1/b",
        "creation": "2020-01-01",
    }
]

expect_runtime(
    lambda:
        mod.parse_csv_body(
            b"oci,citing\n1-2,a\n"
        ),
    "missing required fields",
)


# ------------------------------------------------------------
# OCI analysis retains exceptional rows.
# ------------------------------------------------------------

analysis = (
    mod.analyse_csv_rows(
        [
            {
                "oci": "1-2",
            },
            {
                "oci": "3-4",
            },
            {
                "oci": "3-4",
            },
            {
                "oci": "",
            },
            {
                "oci": "bad",
            },
        ],
        attempt05_ocis={
            "1-2",
            "5-6",
        },
    )
)

assert (
    analysis[
        "csv_data_rows"
    ]
    == 5
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
        "csv_only_ocis"
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

base = {
    "csv_data_rows": 12846,
    "empty_oci_rows": 0,
    "nonconforming_oci_rows": 0,
    "unique_valid_numeric_ocis": 12846,
    "duplicate_valid_oci_count": 0,
}

assert (
    mod.classify_result(
        pre_count=12846,
        post_count=12847,
        analysis=base,
    )
    ==
    "COUNT_CHANGED_DURING_INTERVAL"
)

assert (
    mod.classify_result(
        pre_count=12846,
        post_count=12846,
        analysis=base,
    )
    ==
    "STABLE_COUNT_CSV_12846_UNIQUE_VALID"
)

case = dict(
    base
)

case[
    "csv_data_rows"
] = 12845

case[
    "unique_valid_numeric_ocis"
] = 12845

assert (
    mod.classify_result(
        pre_count=12846,
        post_count=12846,
        analysis=case,
    )
    ==
    "STABLE_COUNT_CSV_12845_ROWS"
)

case = dict(
    base
)

case[
    "nonconforming_oci_rows"
] = 1

case[
    "unique_valid_numeric_ocis"
] = 12845

assert (
    mod.classify_result(
        pre_count=12846,
        post_count=12846,
        analysis=case,
    )
    ==
    "STABLE_COUNT_NONCONFORMING_OCI"
)


# ------------------------------------------------------------
# Transport: incomplete first body is never written.
# ------------------------------------------------------------

class Headers:
    def __init__(
        self,
        content_type: str,
    ):
        self.content_type = (
            content_type
        )

    def get(
        self,
        key,
        default=None,
    ):
        if key.lower() == (
            "content-type"
        ):
            return self.content_type

        return default


class FakeResponse:
    def __init__(
        self,
        *,
        body: bytes,
        fail_incomplete: bool = False,
        content_type: str = "application/json",
    ):
        self.body = body
        self.fail_incomplete = (
            fail_incomplete
        )
        self.status = 200
        self.headers = Headers(
            content_type
        )

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        return False

    def read(
        self,
    ):
        if self.fail_incomplete:
            raise (
                http.client.IncompleteRead(
                    b"partial",
                    100,
                )
            )

        return self.body


with tempfile.TemporaryDirectory() as td:
    raw = (
        Path(td)
        / "response.json"
    )

    sequence = [
        FakeResponse(
            body=b"",
            fail_incomplete=True,
        ),
        FakeResponse(
            body=b'[{"count":"1"}]',
        ),
    ]

    def opener(
        request,
        timeout,
    ):
        return sequence.pop(0)

    body, meta = (
        mod.fetch_bytes(
            "https://example.invalid",
            headers={},
            raw_path=raw,
            opener=opener,
            retries=2,
            delay=0,
        )
    )

    assert body == (
        b'[{"count":"1"}]'
    )

    assert raw.read_bytes() == body
    assert meta["attempt"] == 2


with tempfile.TemporaryDirectory() as td:
    raw = (
        Path(td)
        / "response.json"
    )

    def opener(
        request,
        timeout,
    ):
        return FakeResponse(
            body=b"",
            fail_incomplete=True,
        )

    expect_runtime(
        lambda:
            mod.fetch_bytes(
                "https://example.invalid",
                headers={},
                raw_path=raw,
                opener=opener,
                retries=2,
                delay=0,
            ),
        "failed after 2 attempts",
    )

    assert not raw.exists()


# ------------------------------------------------------------
# Full offline diagnostic using the REAL frozen Attempt-05
# 12,845-OCI archive plus exactly one synthetic extra OCI.
# ------------------------------------------------------------

extra_oci = (
    "999999999999999999-"
    "999999999999999999"
)

assert (
    extra_oci
    not in attempt05_ocis
)

csv_buffer = io.StringIO(
    newline=""
)

writer = csv.DictWriter(
    csv_buffer,
    fieldnames=[
        "oci",
        "citing",
        "cited",
        "creation",
    ],
    lineterminator="\n",
)

writer.writeheader()

for oci in sorted(
    attempt05_ocis
):
    writer.writerow({
        "oci":
            oci,
        "citing":
            "doi:10.2000/citer",
        "cited":
            "doi:10.1093/molbev/msm088",
        "creation":
            "2020-01-01",
    })

writer.writerow({
    "oci":
        extra_oci,
    "citing":
        "doi:10.9999/extra",
    "cited":
        "doi:10.1093/molbev/msm088",
    "creation":
        "2026-09-23",
})

synthetic_csv = (
    csv_buffer.getvalue().encode(
        "utf-8"
    )
)


class DiagnosticOpener:
    def __init__(
        self,
    ):
        self.calls = []

    def __call__(
        self,
        request,
        timeout,
    ):
        accept = request.headers.get(
            "Accept",
            "",
        )

        self.calls.append(
            (
                request.full_url,
                accept,
            )
        )

        if accept == "text/csv":
            return FakeResponse(
                body=
                    synthetic_csv,
                content_type=
                    "text/csv",
            )

        if accept == (
            "application/json"
        ):
            return FakeResponse(
                body=
                    b'[{"count":"12846"}]',
                content_type=
                    "application/json",
            )

        raise AssertionError(
            f"Unexpected Accept: {accept}"
        )


with tempfile.TemporaryDirectory() as td:
    out = Path(td) / "diagnostic"

    opener = (
        DiagnosticOpener()
    )

    # Prove no accidental network access.
    with patch(
        "urllib.request.urlopen",
        side_effect=AssertionError(
            "network access prohibited"
        ),
    ):
        summary = (
            mod.run_diagnostic(
                output_root=out,
                attempt05_archive=
                    ARCHIVE,
                token="",
                opener=opener,
                sleep_fn=lambda _: None,
            )
        )

    assert len(
        opener.calls
    ) == 3

    assert [
        accept
        for _, accept
        in opener.calls
    ] == [
        "application/json",
        "text/csv",
        "application/json",
    ]

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
            "csv_data_rows"
        ]
        == 12846
    )

    assert (
        summary[
            "csv_unique_valid_numeric_ocis"
        ]
        == 12846
    )

    assert (
        summary[
            "csv_only_oci_count"
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
        "STABLE_COUNT_CSV_12846_UNIQUE_VALID"
    )

    assert (
        out
        / "citations_unfiltered.csv"
    ).read_bytes() == (
        synthetic_csv
    )

    with (
        out
        / "csv_only_ocis.tsv"
    ).open(
        encoding="utf-8",
    ) as fh:
        lines = [
            line.rstrip("\n")
            for line in fh
        ]

    assert lines == [
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

    checksums = (
        out
        / "checksums.sha256"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "citations_unfiltered.csv"
        in checksums
    )

print("PASS | frozen diagnostic URLs")
print("PASS | Attempt-05 archive reconstructs exactly 12845 unique OCIs")
print("PASS | count-response validation")
print("PASS | CSV structural validation")
print("PASS | exceptional OCI rows retained")
print("PASS | duplicate OCI analysis")
print("PASS | OCI set-difference analysis")
print("PASS | diagnostic interpretation matrix")
print("PASS | IncompleteRead retry discards incomplete body")
print("PASS | persistent incomplete transport fails closed")
print("PASS | full count -> CSV -> count sequence")
print("PASS | real Attempt-05 union + one synthetic OCI isolated exactly")
print("PASS | diagnostic output explicitly marked non-production")
print("PASS | offline diagnostic tests made zero network requests")
