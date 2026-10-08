#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import tempfile
import urllib.error

from datetime import datetime, timezone
from pathlib import Path

import retrieve_metadata_resolution_queue as transport


def row(
    *,
    lookup_id="lookup:test",
    provider="openalex",
    route="work_by_openalex_id",
    namespace="openalex",
    identifier="W1",
):
    return {
        "logical_lookup_id":
            lookup_id,

        "provider":
            provider,

        "route":
            route,

        "identifier_namespace":
            namespace,

        "identifier":
            identifier,
    }


def response(
    status,
    *,
    url="https://api.openalex.org/works/W1",
    headers=(),
    body=b"",
):
    return transport.HTTPResponse(
        status=status,
        url=url,
        headers=tuple(headers),
        body=body,
    )


# ------------------------------------------------------------
# Frozen queue dependency.
# ------------------------------------------------------------

transport.verify_frozen_queue()

rows = transport.read_queue()

assert len(rows) == 1731

print(
    "PASS | frozen 1,731-lookup queue dependency"
)


# ------------------------------------------------------------
# Exact request construction.
# ------------------------------------------------------------

r = transport.build_request(
    row()
)

assert r.method == "GET"

assert r.url == (
    "https://api.openalex.org/works/W1"
)

r = transport.build_request(
    row(
        provider="openalex",
        route="work_by_doi",
        namespace="doi",
        identifier="10.1/example",
    )
)

assert (
    "/works/doi:10.1%2Fexample"
    in r.url
)

r = transport.build_request(
    row(
        provider="openalex",
        route="work_by_pmid",
        namespace="pmid",
        identifier="123",
    )
)

assert r.url.endswith(
    "/works/pmid:123"
)

r = transport.build_request(
    row(
        provider="opencitations_meta",
        route="metadata_by_doi",
        namespace="doi",
        identifier="10.1/example",
    )
)

assert r.url == (
    "https://api.opencitations.net/"
    "meta/v1/metadata/doi:10.1%2Fexample"
)

r = transport.build_request(
    row(
        provider="opencitations_meta",
        route="metadata_by_omid",
        namespace="omid",
        identifier="br/123",
    )
)

assert r.url.endswith(
    "/metadata/omid:br%2F123"
)

r = transport.build_request(
    row(
        provider="pubmed",
        route="record_by_pmid",
        namespace="pmid",
        identifier="123",
    )
)

assert (
    "efetch.fcgi?"
    in r.url
)

assert "db=pubmed" in r.url
assert "id=123" in r.url
assert "retmode=xml" in r.url
assert (
    "tool=branchsnv_validation_experiment_07"
    in r.url
)

print(
    "PASS | all frozen routes construct exact requests"
)


# ------------------------------------------------------------
# Credentials exist only in headers and redact cleanly.
# ------------------------------------------------------------

secret_a = "OPENALEX-SUPER-SECRET"
secret_o = "OPENCITATIONS-SUPER-SECRET"

r = transport.build_request(
    row(),
    environ={
        "OPENALEX_API_KEY":
            secret_a,
    },
)

openalex_query = (
    transport.urllib.parse.parse_qs(
        transport.urllib.parse.urlsplit(
            r.url
        ).query
    )
)

assert openalex_query[
    "api_key"
] == [
    secret_a
]

assert not any(
    key.lower() == "authorization"
    for key, _
    in r.headers
)

sanitized_openalex = (
    transport.sanitized_url(
        r.url
    )
)

assert secret_a not in sanitized_openalex

sanitized_openalex_query = (
    transport.urllib.parse.parse_qs(
        transport.urllib.parse.urlsplit(
            sanitized_openalex
        ).query
    )
)

assert sanitized_openalex_query[
    "api_key"
] == [
    "<REDACTED>"
]

r2 = transport.build_request(
    row(
        provider="opencitations_meta",
        route="metadata_by_omid",
        namespace="omid",
        identifier="br/1",
    ),
    environ={
        "OPENCITATIONS_ACCESS_TOKEN":
            secret_o,
    },
)

assert secret_o not in r2.url
assert secret_o not in json.dumps(
    transport.redact_headers(
        r2.headers
    )
)

print(
    "PASS | provider credentials follow amended source contract and redact"
)


# ------------------------------------------------------------
# PubMed tool/email source contract and URL redaction.
# ------------------------------------------------------------

contact = "developer@example.org"

pubmed_contact_request = (
    transport.build_request(
        row(
            provider="pubmed",
            route="record_by_pmid",
            namespace="pmid",
            identifier="123",
        ),
        environ={
            "NCBI_EMAIL":
                contact,
        },
    )
)

pubmed_contact_query = (
    transport.urllib.parse.parse_qs(
        transport.urllib.parse.urlsplit(
            pubmed_contact_request.url
        ).query
    )
)

assert pubmed_contact_query[
    "tool"
] == [
    "branchsnv_validation_experiment_07"
]

assert pubmed_contact_query[
    "email"
] == [
    contact
]

sanitized_pubmed = (
    transport.sanitized_url(
        pubmed_contact_request.url
    )
)

assert contact not in sanitized_pubmed

sanitized_pubmed_query = (
    transport.urllib.parse.parse_qs(
        transport.urllib.parse.urlsplit(
            sanitized_pubmed
        ).query
    )
)

assert sanitized_pubmed_query[
    "email"
] == [
    "<REDACTED>"
]

try:
    transport.build_request(
        row(
            provider="pubmed",
            route="record_by_pmid",
            namespace="pmid",
            identifier="123",
        ),
        environ={
            "NCBI_EMAIL":
                "not-an-email",
        },
    )

except ValueError:
    pass

else:
    raise AssertionError(
        "Malformed NCBI_EMAIL accepted"
    )

print(
    "PASS | PubMed tool/email parameters validate and redact"
)


# ------------------------------------------------------------
# OpenAlex success.
# ------------------------------------------------------------

req = transport.build_request(
    row()
)

classification = (
    transport.classify_response(
        req,
        response(
            200,
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {
                    "openalex":
                        "https://openalex.org/W1",
                },
            }).encode(),
        ),
    )
)

assert (
    classification.terminal_status
    == "success"
)

assert (
    classification.provider_identifier
    == "https://openalex.org/W1"
)

print(
    "PASS | OpenAlex successful response validation"
)


# ------------------------------------------------------------
# OpenAlex malformed result fails closed.
# ------------------------------------------------------------

try:
    transport.classify_response(
        req,
        response(
            200,
            body=b'{"id":"x"}',
        ),
    )

except transport.ResponseIntegrityError:
    pass

else:
    raise AssertionError(
        "Malformed OpenAlex payload accepted"
    )

print(
    "PASS | malformed OpenAlex payload fails closed"
)


# ------------------------------------------------------------
# OpenCitations exact empty result is terminal not_found.
# ------------------------------------------------------------

req_oc = transport.build_request(
    row(
        provider="opencitations_meta",
        route="metadata_by_omid",
        namespace="omid",
        identifier="br/1",
    )
)

classification = (
    transport.classify_response(
        req_oc,
        response(
            200,
            url=req_oc.url,
            body=b"[]",
        ),
    )
)

assert (
    classification.terminal_status
    == "not_found"
)

print(
    "PASS | OpenCitations empty exact result is terminal negative evidence"
)


# ------------------------------------------------------------
# Amendment 36:
# identity-concordant OpenCitations multiplicity is accepted,
# but only under the exact frozen rule.
# ------------------------------------------------------------

oc_common = {
    "id":
        "omid:br/1 doi:10.1234/example",

    "title":
        "Example title",

    "author":
        "Example Author",

    "type":
        "journal article",

    "pub_date":
        "2020-01-01",
}

eligible_venue = [
    {
        **oc_common,
        "venue":
            "Venue A",
    },
    {
        **oc_common,
        "venue":
            "Venue B",
    },
]

classification = (
    transport.classify_response(
        req_oc,
        response(
            200,
            url=req_oc.url,
            body=json.dumps(
                eligible_venue
            ).encode(),
        ),
    )
)

assert (
    classification.terminal_status
    == "success"
)

assert (
    classification.provider_identifier
    == "omid:br/1 doi:10.1234/example"
)

print(
    "PASS | Amendment 36 accepts "
    "identity-concordant venue multiplicity"
)


eligible_date = [
    {
        **oc_common,
        "venue":
            "Venue A",
        "pub_date":
            "2020",
    },
    {
        **oc_common,
        "venue":
            "Venue A",
        "pub_date":
            "2020-01",
    },
]

classification = (
    transport.classify_response(
        req_oc,
        response(
            200,
            url=req_oc.url,
            body=json.dumps(
                eligible_date
            ).encode(),
        ),
    )
)

assert (
    classification.provider_identifier
    == "omid:br/1 doi:10.1234/example"
)

print(
    "PASS | Amendment 36 accepts "
    "identity-concordant pub_date multiplicity"
)


def expect_oc_integrity_failure(
    payload,
    label,
):
    try:
        transport.classify_response(
            req_oc,
            response(
                200,
                url=req_oc.url,
                body=json.dumps(
                    payload
                ).encode(),
            ),
        )

    except transport.ResponseIntegrityError:
        print(
            "PASS |",
            label,
        )

    else:
        raise AssertionError(
            "Invalid OpenCitations "
            "multiplicity accepted: "
            + label
        )


expect_oc_integrity_failure(
    [
        {},
        {},
    ],
    "OpenCitations empty-object multiplicity fails closed",
)

expect_oc_integrity_failure(
    [
        {
            **oc_common,
            "id":
                "omid:br/1 doi:10.1234/example",
            "venue":
                "Venue A",
        },
        {
            **oc_common,
            "id":
                "omid:br/2 doi:10.1234/example",
            "venue":
                "Venue B",
        },
    ],
    "OpenCitations differing identifier bundles fail closed",
)

expect_oc_integrity_failure(
    [
        {
            **oc_common,
            "id":
                "doi:10.1234/example",
            "venue":
                "Venue A",
        },
        {
            **oc_common,
            "id":
                "doi:10.1234/example",
            "venue":
                "Venue B",
        },
    ],
    "OpenCitations rows lacking requested exact token fail closed",
)

expect_oc_integrity_failure(
    [
        {
            **oc_common,
            "venue":
                "Venue A",
        },
        {
            **oc_common,
            "title":
                "Different title",
            "venue":
                "Venue B",
        },
    ],
    "OpenCitations title disagreement fails closed",
)

expect_oc_integrity_failure(
    [
        {
            **oc_common,
            "venue":
                "Venue A",
        },
        {
            **oc_common,
            "author":
                "Different Author",
            "venue":
                "Venue B",
        },
    ],
    "OpenCitations author disagreement fails closed",
)

expect_oc_integrity_failure(
    [
        {
            **oc_common,
            "venue":
                "Venue A",
        },
        {
            **oc_common,
            "type":
                "book",
            "venue":
                "Venue B",
        },
    ],
    "OpenCitations type disagreement fails closed",
)

# ------------------------------------------------------------
# PubMed successful exact PMID.
# ------------------------------------------------------------

req_pm = transport.build_request(
    row(
        provider="pubmed",
        route="record_by_pmid",
        namespace="pmid",
        identifier="123",
    )
)

pubmed_xml = b"""<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID Version="1">123</PMID>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""

classification = (
    transport.classify_response(
        req_pm,
        transport.HTTPResponse(
            status=200,
            url=req_pm.url,
            headers=(),
            body=pubmed_xml,
        ),
    )
)

assert (
    classification.terminal_status
    == "success"
)

assert (
    classification.provider_identifier
    == "123"
)

print(
    "PASS | PubMed exact PMID response validation"
)


# ------------------------------------------------------------
# Related-article PMID must not be mistaken for primary PMID.
# ------------------------------------------------------------

pubmed_with_correction_xml = b"""<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID Version="1">123</PMID>
      <CommentsCorrectionsList>
        <CommentsCorrections RefType="ErratumFor">
          <PMID Version="1">999</PMID>
        </CommentsCorrections>
      </CommentsCorrectionsList>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""

classification = (
    transport.classify_response(
        req_pm,
        transport.HTTPResponse(
            status=200,
            url=req_pm.url,
            headers=(),
            body=pubmed_with_correction_xml,
        ),
    )
)

assert (
    classification.terminal_status
    == "success"
)

assert (
    classification.provider_identifier
    == "123"
)

print(
    "PASS | related CommentsCorrections PMID does not contaminate primary PMID"
)


# ------------------------------------------------------------
# PubmedBookArticle uses BookDocument/PMID as primary PMID.
# ------------------------------------------------------------

book_xml = b"""<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedBookArticle>
    <BookDocument>
      <PMID Version="1">123</PMID>
      <ArticleIdList>
        <ArticleId IdType="bookaccession">NBK1</ArticleId>
      </ArticleIdList>
      <Book>
        <Publisher>
          <PublisherName>Example</PublisherName>
        </Publisher>
        <BookTitle>Example Book</BookTitle>
      </Book>
    </BookDocument>
  </PubmedBookArticle>
</PubmedArticleSet>
"""

classification = (
    transport.classify_response(
        req_pm,
        transport.HTTPResponse(
            status=200,
            url=req_pm.url,
            headers=(),
            body=book_xml,
        ),
    )
)

assert (
    classification.terminal_status
    == "success"
)

assert (
    classification.provider_identifier
    == "123"
)

print(
    "PASS | PubmedBookArticle primary PMID validated via BookDocument/PMID"
)


# ------------------------------------------------------------
# PubMed empty exact retrieval is not_found.
# ------------------------------------------------------------

classification = (
    transport.classify_response(
        req_pm,
        transport.HTTPResponse(
            status=200,
            url=req_pm.url,
            headers=(),
            body=b"<PubmedArticleSet/>",
        ),
    )
)

assert (
    classification.terminal_status
    == "not_found"
)

print(
    "PASS | PubMed empty exact retrieval is terminal negative evidence"
)


# ------------------------------------------------------------
# PubMed mismatched PMID fails closed.
# ------------------------------------------------------------

bad_xml = b"""<PubmedArticleSet>
<PubmedArticle>
<MedlineCitation>
<PMID>999</PMID>
</MedlineCitation>
</PubmedArticle>
</PubmedArticleSet>"""

try:
    transport.classify_response(
        req_pm,
        transport.HTTPResponse(
            status=200,
            url=req_pm.url,
            headers=(),
            body=bad_xml,
        ),
    )

except transport.ResponseIntegrityError:
    pass

else:
    raise AssertionError(
        "Mismatched PubMed PMID accepted"
    )

print(
    "PASS | incompatible PubMed PMID fails closed"
)


# ------------------------------------------------------------
# Redirect acceptance and archival.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    calls = []

    def executor(req):
        calls.append(req.url)

        if len(calls) == 1:
            return transport.HTTPResponse(
                status=301,
                url=req.url,
                headers=(
                    (
                        "Location",
                        "https://api.openalex.org/works/W2",
                    ),
                ),
                body=b"redirect-body",
            )

        return transport.HTTPResponse(
            status=200,
            url=req.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W2",
                "ids": {
                    "openalex":
                        "https://openalex.org/W2",
                },
            }).encode(),
        )

    result = transport.transport_lookup(
        row(),
        archive_root=root,
        executor=executor,
        sleeper=lambda _: None,
        environ={},
    )

    assert result[
        "terminal_status"
    ] == "success"

    assert result[
        "provider_identifier"
    ] == "https://openalex.org/W2"

    assert result[
        "attempts"
    ][0][
        "redirect_hops"
    ] == 1

    assert len(calls) == 2

print(
    "PASS | same-provider redirect retained and followed explicitly"
)


# ------------------------------------------------------------
# Redirect outside provider fails closed.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    def bad_redirect(req):
        return transport.HTTPResponse(
            status=301,
            url=req.url,
            headers=(
                (
                    "Location",
                    "https://example.com/evil",
                ),
            ),
            body=b"",
        )

    result = transport.transport_lookup(
        row(),
        archive_root=root,
        executor=bad_redirect,
        sleeper=lambda _: None,
        environ={},
    )

    assert result[
        "terminal_status"
    ] == "redirect_failure"

print(
    "PASS | cross-host redirect fails closed"
)


# ------------------------------------------------------------
# 404 exact OpenAlex result is terminal and not retried.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    count = [0]

    def missing(req):
        count[0] += 1

        return transport.HTTPResponse(
            status=404,
            url=req.url,
            headers=(),
            body=b'{"error":"not found"}',
        )

    result = transport.transport_lookup(
        row(),
        archive_root=root,
        executor=missing,
        sleeper=lambda _: None,
        environ={},
    )

    assert result[
        "terminal_status"
    ] == "not_found"

    assert result[
        "attempt_count"
    ] == 1

    assert count[0] == 1

print(
    "PASS | exact 404 is terminal negative evidence"
)


# ------------------------------------------------------------
# Retryable status retries with deterministic delay.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    calls = [0]
    sleeps = []

    def flaky(req):
        calls[0] += 1

        if calls[0] == 1:
            return transport.HTTPResponse(
                status=503,
                url=req.url,
                headers=(),
                body=b"temporary",
            )

        return transport.HTTPResponse(
            status=200,
            url=req.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    result = transport.transport_lookup(
        row(),
        archive_root=root,
        executor=flaky,
        sleeper=sleeps.append,
        environ={},
    )

    assert result[
        "terminal_status"
    ] == "success"

    assert result[
        "attempt_count"
    ] == 2

    assert sleeps == [1.0]

print(
    "PASS | retryable HTTP failure retries deterministically"
)


# ------------------------------------------------------------
# Retry-After overrides shorter local backoff.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    calls = [0]
    sleeps = []

    def limited(req):
        calls[0] += 1

        if calls[0] == 1:
            return transport.HTTPResponse(
                status=429,
                url=req.url,
                headers=(
                    (
                        "Retry-After",
                        "7",
                    ),
                ),
                body=b"",
            )

        return transport.HTTPResponse(
            status=404,
            url=req.url,
            headers=(),
            body=b"",
        )

    result = transport.transport_lookup(
        row(),
        archive_root=root,
        executor=limited,
        sleeper=sleeps.append,
        environ={},
    )

    assert result[
        "terminal_status"
    ] == "not_found"

    assert sleeps == [7.0]

print(
    "PASS | Retry-After overrides shorter retry delay"
)


# ------------------------------------------------------------
# Persistent transient failure exhausts exactly five attempts.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    calls = [0]
    sleeps = []

    def unavailable(req):
        calls[0] += 1

        return transport.HTTPResponse(
            status=503,
            url=req.url,
            headers=(),
            body=b"x",
        )

    result = transport.transport_lookup(
        row(),
        archive_root=root,
        executor=unavailable,
        sleeper=sleeps.append,
        environ={},
    )

    assert result[
        "terminal_status"
    ] == "retry_exhausted"

    assert calls[0] == 5

    assert sleeps == [
        1.0,
        2.0,
        4.0,
        8.0,
    ]

print(
    "PASS | retry exhaustion occurs after exactly five attempts"
)


# ------------------------------------------------------------
# Authentication failure is not retried.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    count = [0]

    def denied(req):
        count[0] += 1

        return transport.HTTPResponse(
            status=401,
            url=req.url,
            headers=(),
            body=b"",
        )

    result = transport.transport_lookup(
        row(),
        archive_root=root,
        executor=denied,
        sleeper=lambda _: None,
        environ={},
    )

    assert result[
        "terminal_status"
    ] == "authentication_failure"

    assert count[0] == 1

print(
    "PASS | authentication failure fails closed without retry"
)


# ------------------------------------------------------------
# Raw response bytes preserved exactly and checksummed.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    raw = (
        b'\x00\x01RAW\r\n'
        b'{"id":"https://openalex.org/W1",'
        b'"ids":{}}'
    )

    # First two bytes make this invalid JSON, so test the raw
    # archival primitive directly.
    req = transport.build_request(
        row()
    )

    directory = (
        root / "attempt"
    )

    evidence = transport.archive_hop(
        directory,
        hop_number=0,
        request=req,
        response=transport.HTTPResponse(
            status=200,
            url=req.url,
            headers=(),
            body=raw,
        ),
    )

    archived = (
        directory
        / evidence["body_file"]
    ).read_bytes()

    assert archived == raw

    assert evidence[
        "body_sha256"
    ] == transport.sha256_bytes(
        raw
    )

print(
    "PASS | raw provider bytes preserved exactly"
)


# ------------------------------------------------------------
# Credential never enters archived request metadata.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    secret = (
        "THIS-MUST-NEVER-BE-ARCHIVED"
    )

    def ok(req):
        return transport.HTTPResponse(
            status=200,
            url=req.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    result = transport.transport_lookup(
        row(),
        archive_root=root,
        executor=ok,
        sleeper=lambda _: None,
        environ={
            "OPENALEX_API_KEY":
                secret,
        },
    )

    assert result[
        "terminal_status"
    ] == "success"

    for path in root.rglob("*"):
        if path.is_file():
            assert secret.encode() not in (
                path.read_bytes()
            )

print(
    "PASS | credential absent from complete synthetic archive"
)


# ------------------------------------------------------------
# Resume/archive verification accepts intact terminal evidence.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    def ok(req):
        return transport.HTTPResponse(
            status=200,
            url=req.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    transport.transport_lookup(
        row(),
        archive_root=root,
        executor=ok,
        sleeper=lambda _: None,
        environ={},
    )

    lookup_root = (
        root
        / "raw"
        / "lookup_test"
    )

    terminal = (
        transport.verify_terminal_archive(
            lookup_root
        )
    )

    assert terminal[
        "terminal_status"
    ] == "success"

print(
    "PASS | intact terminal archive validates for resume"
)


# ------------------------------------------------------------
# Tampered body fails resume validation.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    def ok(req):
        return transport.HTTPResponse(
            status=200,
            url=req.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    transport.transport_lookup(
        row(),
        archive_root=root,
        executor=ok,
        sleeper=lambda _: None,
        environ={},
    )

    lookup_root = (
        root
        / "raw"
        / "lookup_test"
    )

    body = next(
        lookup_root.rglob(
            "hop_*_body.bin"
        )
    )

    body.write_bytes(
        b"TAMPERED"
    )

    try:
        transport.verify_terminal_archive(
            lookup_root
        )

    except RuntimeError:
        pass

    else:
        raise AssertionError(
            "Tampered archive accepted"
        )

print(
    "PASS | tampered raw evidence fails resume validation"
)


# ------------------------------------------------------------
# Completion gate.
# ------------------------------------------------------------

small_queue = [
    {
        "logical_lookup_id":
            "lookup:a",
    },
    {
        "logical_lookup_id":
            "lookup:b",
    },
]

complete = (
    transport.validate_completion(
        small_queue,
        [
            {
                "logical_lookup_id":
                    "lookup:a",
                "terminal_status":
                    "success",
            },
            {
                "logical_lookup_id":
                    "lookup:b",
                "terminal_status":
                    "not_found",
            },
        ],
    )
)

assert complete[
    "status"
] == "COMPLETE"

incomplete = (
    transport.validate_completion(
        small_queue,
        [
            {
                "logical_lookup_id":
                    "lookup:a",
                "terminal_status":
                    "success",
            },
            {
                "logical_lookup_id":
                    "lookup:b",
                "terminal_status":
                    "retry_exhausted",
            },
        ],
    )
)

assert incomplete[
    "status"
] == "INCOMPLETE"

print(
    "PASS | completion requires success/not_found for every lookup"
)


# ------------------------------------------------------------
# Provider pacing is independent.
# ------------------------------------------------------------

clock = [0.0]
sleeps = []


def monotonic():
    return clock[0]


def sleeper(seconds):
    sleeps.append(seconds)
    clock[0] += seconds


pacer = transport.ProviderPacer(
    interval_seconds=0.5,
    monotonic=monotonic,
    sleeper=sleeper,
)

pacer.wait("openalex")

pacer.wait("openalex")

pacer.wait("pubmed")

assert sleeps == [0.5]

print(
    "PASS | per-provider pacing is independent"
)


# ------------------------------------------------------------
# Live-capable transport still requires independent runtime
# authorization. These checks invoke no network operation.
# ------------------------------------------------------------

assert (
    transport.LIVE_EXECUTION_ENABLED
    is True
)

try:
    transport.assert_live_execution_allowed(
        environ={
            "NCBI_EMAIL":
                "developer@example.org",
        }
    )

except transport.LiveExecutionBlocked as exc:
    assert (
        "BRANCHSNV_ALLOW_METADATA_NETWORK"
        in str(exc)
    )

else:
    raise AssertionError(
        "Live execution accepted missing "
        "network authorization"
    )

transport.assert_live_execution_allowed(
    environ={
        "BRANCHSNV_ALLOW_METADATA_NETWORK":
            "YES",

        "NCBI_EMAIL":
            "developer@example.org",
    }
)

print(
    "PASS | live-capable transport retains "
    "independent runtime authorization gates"
)


# ------------------------------------------------------------
# Production-directory presence is no longer a test invariant after the first live retrieval.
# ------------------------------------------------------------

production = (
    Path(__file__).resolve().parent.parent.parent
    / "results"
    / "07_comparative_landscape"
    / "metadata_resolution_retrieval"
)

pass  # production-directory presence is no longer a transport-test invariant

print(
    "PASS | transport synthetic tests are independent of production-directory presence"
)


print()
print(
    "PASS | all metadata-resolution transport synthetic tests"
)


# ------------------------------------------------------------
# IncompleteRead is retryable.
# ------------------------------------------------------------

import http.client


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    calls = [0]
    sleeps = []

    def incomplete_then_ok(req):
        calls[0] += 1

        if calls[0] == 1:
            raise http.client.IncompleteRead(
                b"partial",
                100,
            )

        return transport.HTTPResponse(
            status=200,
            url=req.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    result = transport.transport_lookup(
        row(),
        archive_root=root,
        executor=incomplete_then_ok,
        sleeper=sleeps.append,
        environ={},
    )

    assert result[
        "terminal_status"
    ] == "success"

    assert result[
        "attempt_count"
    ] == 2

    assert sleeps == [1.0]

print(
    "PASS | IncompleteRead is retried from a new attempt"
)


# ------------------------------------------------------------
# Resume starts after an immutable prior attempt.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    prior = {
        "attempt_number":
            1,

        "outcome":
            "retryable_http_status",

        "http_status":
            503,
    }

    attempt_1 = (
        transport.attempt_directory(
            root,
            "lookup:test",
            1,
        )
    )

    attempt_1.mkdir(
        parents=True,
        exist_ok=True,
    )

    preserved = (
        b'{"attempt_number":1,'
        b'"http_status":503,'
        b'"outcome":"retryable_http_status"}\\n'
    )

    (
        attempt_1
        / "attempt.json"
    ).write_bytes(
        preserved
    )

    def ok(req):
        return transport.HTTPResponse(
            status=200,
            url=req.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W1",
                "ids": {},
            }).encode(),
        )

    result = transport.transport_lookup(
        row(),
        archive_root=root,
        executor=ok,
        sleeper=lambda _: None,
        environ={},
        start_attempt_number=2,
        prior_attempts=[prior],
    )

    assert result[
        "terminal_status"
    ] == "success"

    assert result[
        "attempt_count"
    ] == 2

    assert [
        x["attempt_number"]
        for x in result["attempts"]
    ] == [
        1,
        2,
    ]

    assert (
        attempt_1
        / "attempt.json"
    ).read_bytes() == preserved

print(
    "PASS | resume continues after prior immutable attempt"
)


# ------------------------------------------------------------
# Amendment 34: authenticated OpenAlex redirects retain the
# api_key without persisting it.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    redirect_secret = (
        "OPENALEX-REDIRECT-SECRET"
    )

    initial = transport.build_request(
        row(),
        environ={
            "OPENALEX_API_KEY":
                redirect_secret,
        },
    )

    seen = []

    def redirect_then_ok(req):
        seen.append(
            req
        )

        if len(seen) == 1:
            return transport.HTTPResponse(
                status=301,
                url=req.url,
                headers=(
                    (
                        "Location",
                        "https://api.openalex.org/works/W2",
                    ),
                ),
                body=b"",
            )

        return transport.HTTPResponse(
            status=200,
            url=req.url,
            headers=(),
            body=json.dumps({
                "id":
                    "https://openalex.org/W2",
                "ids": {},
            }).encode(),
        )

    final_response, evidence = (
        transport.request_with_redirects(
            initial,
            executor=redirect_then_ok,
            archive_directory=root,
        )
    )

    assert final_response.status == 200
    assert len(seen) == 2
    assert len(evidence) == 2

    second_query = (
        transport.urllib.parse.parse_qs(
            transport.urllib.parse.urlsplit(
                seen[1].url
            ).query
        )
    )

    assert second_query[
        "api_key"
    ] == [
        redirect_secret
    ]

    for path in root.rglob("*"):
        if path.is_file():
            assert (
                redirect_secret.encode()
                not in path.read_bytes()
            )

print(
    "PASS | OpenAlex redirect preserves api_key without persistence"
)


# ------------------------------------------------------------
# A redirect may not substitute or introduce another OpenAlex
# credential, and Location evidence must remain redacted.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    redirect_secret = (
        "OPENALEX-ORIGINAL-SECRET"
    )

    attacker_secret = (
        "OPENALEX-UNEXPECTED-SECRET"
    )

    initial = transport.build_request(
        row(),
        environ={
            "OPENALEX_API_KEY":
                redirect_secret,
        },
    )

    def conflicting_redirect(req):
        return transport.HTTPResponse(
            status=301,
            url=req.url,
            headers=(
                (
                    "Location",
                    "https://api.openalex.org/works/W2"
                    "?api_key="
                    + attacker_secret,
                ),
            ),
            body=b"",
        )

    try:
        transport.request_with_redirects(
            initial,
            executor=conflicting_redirect,
            archive_directory=root,
        )

    except transport.RedirectFailure:
        pass

    else:
        raise AssertionError(
            "OpenAlex redirect changed api_key"
        )

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        payload = path.read_bytes()

        assert (
            redirect_secret.encode()
            not in payload
        )

        assert (
            attacker_secret.encode()
            not in payload
        )

print(
    "PASS | OpenAlex redirect credential substitution fails closed and redacts"
)


# ------------------------------------------------------------
# PubMed contact address must not enter archived evidence.
# ------------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    contact = "developer@example.org"

    xml = b"""<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID Version="1">123</PMID>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""

    def pubmed_ok(req):
        return transport.HTTPResponse(
            status=200,
            url=req.url,
            headers=(),
            body=xml,
        )

    result = transport.transport_lookup(
        row(
            provider="pubmed",
            route="record_by_pmid",
            namespace="pmid",
            identifier="123",
        ),
        archive_root=root,
        executor=pubmed_ok,
        sleeper=lambda _: None,
        environ={
            "NCBI_EMAIL":
                contact,
        },
    )

    assert result[
        "terminal_status"
    ] == "success"

    for path in root.rglob("*"):
        if path.is_file():
            assert (
                contact.encode()
                not in path.read_bytes()
            )

print(
    "PASS | NCBI_EMAIL absent from complete synthetic archive"
)
