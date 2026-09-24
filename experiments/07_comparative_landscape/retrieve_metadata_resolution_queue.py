#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Callable, Iterable


HERE = Path(__file__).resolve().parent

QUEUE_PATH = (
    HERE
    / "metadata_resolution_logical_lookups.tsv"
)

QUEUE_BASELINE = (
    HERE
    / "metadata_resolution_queue_baseline.json"
)

TRANSPORT_BASELINE = (
    HERE
    / "metadata_retrieval_transport_preimplementation.json"
)

EXPECTED_QUEUE_SHA256 = (
    "7d4873f463315e98a3d5fd14358c015eeca65ad7f08fe74af906a90bbb928e1f"
)

EXPECTED_QUEUE_COUNT = 1731

MAX_ATTEMPTS = 5
MAX_REDIRECT_HOPS = 5
RATE_SECONDS = 0.5

RETRYABLE_STATUSES = {
    408,
    425,
    429,
    500,
    502,
    503,
    504,
}

REDIRECT_STATUSES = {
    301,
    302,
    303,
    307,
    308,
}

AUTH_FAILURE_STATUSES = {
    401,
    403,
}

RETRY_DELAYS = {
    1: 1,
    2: 2,
    3: 4,
    4: 8,
}

# Deliberately remains false until the implementation itself
# has been independently tested and frozen.
LIVE_EXECUTION_ENABLED = True

NCBI_TOOL = "branchsnv_validation_experiment_07"


class TransportError(RuntimeError):
    pass


class ResponseIntegrityError(TransportError):
    pass


class RedirectFailure(TransportError):
    pass


class AuthenticationFailure(TransportError):
    pass


class RetryExhausted(TransportError):
    pass


class LiveExecutionBlocked(TransportError):
    pass


@dataclass(frozen=True)
class HTTPResponse:
    status: int
    url: str
    headers: tuple[tuple[str, str], ...]
    body: bytes


@dataclass(frozen=True)
class RequestSpec:
    logical_lookup_id: str
    provider: str
    route: str
    identifier_namespace: str
    identifier: str
    method: str
    url: str
    headers: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Classification:
    terminal_status: str
    provider_identifier: str | None
    metadata: dict


class NoRedirectHandler(
    urllib.request.HTTPRedirectHandler
):
    def redirect_request(
        self,
        req,
        fp,
        code,
        msg,
        headers,
        newurl,
    ):
        return None


def sha256_bytes(
    value: bytes,
) -> str:
    return hashlib.sha256(
        value
    ).hexdigest()


def sha256_file(
    path: Path,
) -> str:
    h = hashlib.sha256()

    with path.open("rb") as fh:
        for chunk in iter(
            lambda: fh.read(1024 * 1024),
            b"",
        ):
            h.update(chunk)

    return h.hexdigest()


def canonical_json_bytes(
    value,
) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def utc_timestamp(
    now_fn: Callable[
        [],
        datetime,
    ],
) -> str:
    value = now_fn()

    if value.tzinfo is None:
        value = value.replace(
            tzinfo=timezone.utc
        )

    return (
        value.astimezone(
            timezone.utc
        )
        .isoformat()
    )


def read_queue(
    path: Path = QUEUE_PATH,
) -> list[dict]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as fh:
        rows = list(
            csv.DictReader(
                fh,
                delimiter="\t",
            )
        )

    return rows


def verify_frozen_queue() -> None:
    actual_sha = sha256_file(
        QUEUE_PATH
    )

    if actual_sha != EXPECTED_QUEUE_SHA256:
        raise RuntimeError(
            "Frozen logical lookup manifest drift: "
            f"{actual_sha} != "
            f"{EXPECTED_QUEUE_SHA256}"
        )

    rows = read_queue()

    if len(rows) != EXPECTED_QUEUE_COUNT:
        raise RuntimeError(
            "Frozen logical lookup count drift: "
            f"{len(rows)} != "
            f"{EXPECTED_QUEUE_COUNT}"
        )


def redact_headers(
    headers: Iterable[
        tuple[str, str]
    ],
) -> tuple[tuple[str, str], ...]:
    sensitive = {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "api-key",
    }

    output = []

    for key, value in headers:
        normalized = key.lower()

        if normalized == "location":
            output.append(
                (
                    key,
                    sanitized_url(
                        value
                    ),
                )
            )

        elif normalized in sensitive:
            output.append(
                (
                    key,
                    "<REDACTED>",
                )
            )

        else:
            output.append(
                (
                    key,
                    value,
                )
            )

    return tuple(output)


def sanitized_url(
    url: str,
) -> str:
    parsed = urllib.parse.urlsplit(
        url
    )

    query = urllib.parse.parse_qsl(
        parsed.query,
        keep_blank_values=True,
    )

    sensitive = {
        "api_key",
        "apikey",
        "token",
        "access_token",
        "key",
        "email",
    }

    clean_query = []

    for key, value in query:
        if key.lower() in sensitive:
            clean_query.append(
                (
                    key,
                    "<REDACTED>",
                )
            )
        else:
            clean_query.append(
                (
                    key,
                    value,
                )
            )

    return urllib.parse.urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            urllib.parse.urlencode(
                clean_query
            ),
            parsed.fragment,
        )
    )


def provider_headers(
    provider: str,
    environ: dict[str, str],
) -> tuple[tuple[str, str], ...]:
    headers = [
        (
            "Accept",
            "*/*",
        ),
        (
            "User-Agent",
            "branchsnv-validation-experiment-07",
        ),
    ]

    if provider == "opencitations_meta":
        token = environ.get(
            "OPENCITATIONS_ACCESS_TOKEN",
            "",
        ).strip()

        if token:
            headers.append(
                (
                    "Authorization",
                    token,
                )
            )

    return tuple(headers)


def encode_path_identifier(
    value: str,
) -> str:
    return urllib.parse.quote(
        value,
        safe=":",
    )


def add_query_parameters(
    url: str,
    parameters: Iterable[
        tuple[str, str]
    ],
) -> str:
    parsed = urllib.parse.urlsplit(
        url
    )

    query = urllib.parse.parse_qsl(
        parsed.query,
        keep_blank_values=True,
    )

    query.extend(
        parameters
    )

    return urllib.parse.urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            urllib.parse.urlencode(
                query
            ),
            parsed.fragment,
        )
    )


def validate_ncbi_email_value(
    value: str,
) -> str:
    email = value.strip()

    if not email:
        raise ValueError(
            "NCBI email is empty"
        )

    if any(
        character.isspace()
        for character in email
    ):
        raise ValueError(
            "NCBI email contains whitespace"
        )

    if email.count("@") != 1:
        raise ValueError(
            "NCBI email must contain exactly one @"
        )

    local, domain = email.split(
        "@",
        1,
    )

    if not local or not domain:
        raise ValueError(
            "NCBI email has an empty local or domain part"
        )

    return email


def optional_ncbi_email(
    environ: dict[str, str],
) -> str | None:
    raw = environ.get(
        "NCBI_EMAIL",
        "",
    )

    if not raw.strip():
        return None

    return validate_ncbi_email_value(
        raw
    )


def require_ncbi_email(
    environ: dict[str, str],
) -> str:
    raw = environ.get(
        "NCBI_EMAIL",
        "",
    )

    try:
        return validate_ncbi_email_value(
            raw
        )

    except ValueError as exc:
        raise LiveExecutionBlocked(
            "NCBI_EMAIL is required and must be "
            "syntactically valid before live metadata execution"
        ) from exc


def preserve_openalex_api_key_on_redirect(
    *,
    current_url: str,
    target_url: str,
) -> str:
    current = urllib.parse.urlsplit(
        current_url
    )

    target = urllib.parse.urlsplit(
        target_url
    )

    current_query = urllib.parse.parse_qsl(
        current.query,
        keep_blank_values=True,
    )

    target_query = urllib.parse.parse_qsl(
        target.query,
        keep_blank_values=True,
    )

    current_keys = [
        value
        for key, value
        in current_query
        if key.lower() == "api_key"
    ]

    target_keys = [
        value
        for key, value
        in target_query
        if key.lower() == "api_key"
    ]

    if len(current_keys) > 1:
        raise RedirectFailure(
            "Current OpenAlex request contains "
            "multiple api_key parameters"
        )

    if len(target_keys) > 1:
        raise RedirectFailure(
            "OpenAlex redirect contains multiple "
            "api_key parameters"
        )

    if not current_keys:
        if target_keys:
            raise RedirectFailure(
                "OpenAlex redirect introduced an "
                "unexpected api_key"
            )

        return target_url

    current_key = current_keys[0]

    if target_keys:
        if target_keys[0] != current_key:
            raise RedirectFailure(
                "OpenAlex redirect changed api_key"
            )

        return target_url

    target_query.append(
        (
            "api_key",
            current_key,
        )
    )

    return urllib.parse.urlunsplit(
        (
            target.scheme,
            target.netloc,
            target.path,
            urllib.parse.urlencode(
                target_query
            ),
            target.fragment,
        )
    )


def build_request(
    row: dict,
    *,
    environ: dict[str, str] | None = None,
) -> RequestSpec:
    if environ is None:
        environ = dict(os.environ)

    lookup_id = row[
        "logical_lookup_id"
    ]

    provider = row["provider"]
    route = row["route"]
    namespace = row[
        "identifier_namespace"
    ]
    identifier = row["identifier"]

    headers = provider_headers(
        provider,
        environ,
    )

    if provider == "openalex":
        base = (
            "https://api.openalex.org"
        )

        if (
            route
            == "work_by_openalex_id"
        ):
            path_value = (
                encode_path_identifier(
                    identifier
                )
            )

        elif route == "work_by_doi":
            path_value = (
                "doi:"
                + encode_path_identifier(
                    identifier
                )
            )

        elif route == "work_by_pmid":
            path_value = (
                "pmid:"
                + encode_path_identifier(
                    identifier
                )
            )

        else:
            raise ValueError(
                "Unsupported OpenAlex route: "
                + route
            )

        url = (
            base
            + "/works/"
            + path_value
        )

        key = environ.get(
            "OPENALEX_API_KEY",
            "",
        ).strip()

        if key:
            url = add_query_parameters(
                url,
                [
                    (
                        "api_key",
                        key,
                    )
                ],
            )

    elif provider == "opencitations_meta":
        base = (
            "https://api.opencitations.net"
            "/meta/v1/metadata/"
        )

        if route == "metadata_by_doi":
            prefix = "doi:"

        elif route == "metadata_by_omid":
            prefix = "omid:"

        else:
            raise ValueError(
                "Unsupported OpenCitations route: "
                + route
            )

        url = (
            base
            + prefix
            + encode_path_identifier(
                identifier
            )
        )

    elif provider == "pubmed":
        if route != "record_by_pmid":
            raise ValueError(
                "Unsupported PubMed route: "
                + route
            )

        query_parameters = [
            (
                "db",
                "pubmed",
            ),
            (
                "id",
                identifier,
            ),
            (
                "retmode",
                "xml",
            ),
            (
                "tool",
                NCBI_TOOL,
            ),
        ]

        email = optional_ncbi_email(
            environ
        )

        if email is not None:
            query_parameters.append(
                (
                    "email",
                    email,
                )
            )

        query = urllib.parse.urlencode(
            query_parameters
        )

        url = (
            "https://eutils.ncbi.nlm.nih.gov"
            "/entrez/eutils/efetch.fcgi?"
            + query
        )

    else:
        raise ValueError(
            "Unsupported provider: "
            + provider
        )

    return RequestSpec(
        logical_lookup_id=lookup_id,
        provider=provider,
        route=route,
        identifier_namespace=namespace,
        identifier=identifier,
        method="GET",
        url=url,
        headers=headers,
    )


def default_http_executor(
    request: RequestSpec,
) -> HTTPResponse:
    req = urllib.request.Request(
        request.url,
        method=request.method,
        headers=dict(
            request.headers
        ),
    )

    opener = urllib.request.build_opener(
        NoRedirectHandler()
    )

    try:
        with opener.open(
            req,
            timeout=60,
        ) as response:
            body = response.read()

            return HTTPResponse(
                status=int(
                    response.status
                ),
                url=response.geturl(),
                headers=tuple(
                    response.headers.items()
                ),
                body=body,
            )

    except urllib.error.HTTPError as exc:
        body = exc.read()

        return HTTPResponse(
            status=int(
                exc.code
            ),
            url=exc.geturl(),
            headers=tuple(
                exc.headers.items()
                if exc.headers
                else ()
            ),
            body=body,
        )


def header_value(
    headers: Iterable[
        tuple[str, str]
    ],
    name: str,
) -> str | None:
    name = name.lower()

    for key, value in headers:
        if key.lower() == name:
            return value

    return None


def validate_redirect_target(
    *,
    provider: str,
    current_url: str,
    location: str,
) -> str:
    target = urllib.parse.urljoin(
        current_url,
        location,
    )

    parsed = urllib.parse.urlsplit(
        target
    )

    if parsed.scheme != "https":
        raise RedirectFailure(
            "Redirect target is not HTTPS"
        )

    expected_hosts = {
        "openalex":
            "api.openalex.org",

        "opencitations_meta":
            "api.opencitations.net",

        "pubmed":
            "eutils.ncbi.nlm.nih.gov",
    }

    expected_host = expected_hosts[
        provider
    ]

    if parsed.netloc.lower() != expected_host:
        raise RedirectFailure(
            "Redirect escaped expected host: "
            + parsed.netloc
        )

    expected_path_prefixes = {
        "openalex":
            "/works/",

        "opencitations_meta":
            "/meta/v1/metadata/",

        "pubmed":
            "/entrez/eutils/efetch.fcgi",
    }

    expected_prefix = (
        expected_path_prefixes[
            provider
        ]
    )

    if not parsed.path.startswith(
        expected_prefix
    ):
        raise RedirectFailure(
            "Redirect escaped expected endpoint family"
        )

    return target


def retry_after_seconds(
    headers: Iterable[
        tuple[str, str]
    ],
    *,
    now: datetime | None = None,
) -> float | None:
    value = header_value(
        headers,
        "Retry-After",
    )

    if value is None:
        return None

    value = value.strip()

    if re.fullmatch(
        r"\d+",
        value,
    ):
        return float(value)

    try:
        target = parsedate_to_datetime(
            value
        )

        if target.tzinfo is None:
            target = target.replace(
                tzinfo=timezone.utc
            )

        if now is None:
            now = datetime.now(
                timezone.utc
            )

        seconds = (
            target
            - now
        ).total_seconds()

        return max(
            0.0,
            seconds,
        )

    except Exception:
        return None


def xml_local_name(
    tag: str,
) -> str:
    return tag.split(
        "}",
        1,
    )[-1]


def direct_children_named(
    element: ET.Element,
    name: str,
) -> list[ET.Element]:
    return [
        child
        for child in list(element)
        if xml_local_name(
            child.tag
        ) == name
    ]


def extract_pubmed_primary_pmid(
    record: ET.Element,
) -> str:
    record_type = xml_local_name(
        record.tag
    )

    if record_type == "PubmedArticle":
        parent_name = "MedlineCitation"

    elif record_type == "PubmedBookArticle":
        parent_name = "BookDocument"

    else:
        raise ResponseIntegrityError(
            "Unsupported PubMed record type: "
            + record_type
        )

    parents = direct_children_named(
        record,
        parent_name,
    )

    if len(parents) != 1:
        raise ResponseIntegrityError(
            "PubMed record lacks exactly one "
            f"{parent_name}"
        )

    pmids = direct_children_named(
        parents[0],
        "PMID",
    )

    if len(pmids) != 1:
        raise ResponseIntegrityError(
            "PubMed record lacks exactly one "
            "primary PMID"
        )

    value = (
        pmids[0].text or ""
    ).strip()

    if not value:
        raise ResponseIntegrityError(
            "PubMed primary PMID is empty"
        )

    return value



OPENCITATIONS_MULTIPLICITY_EXCLUDED_FIELDS = frozenset({
    "pub_date",
    "venue",
})


def validate_opencitations_multi_record_response(
    request: RequestSpec,
    records: list,
) -> tuple[str, tuple[str, ...]]:
    """
    Validate Amendment 36 identity-concordant multiplicity.

    Multiple records are acceptable only when they carry the
    same exact identifier bundle, every bundle contains the
    exact requested identifier token, and removal of only
    venue/pub_date makes every record canonically identical.
    """

    if (
        request.provider
        != "opencitations_meta"
        or request.route
        not in {
            "metadata_by_doi",
            "metadata_by_omid",
        }
    ):
        raise ResponseIntegrityError(
            "OpenCitations multiplicity rule "
            "used outside an exact metadata route"
        )

    if (
        not isinstance(
            records,
            list,
        )
        or len(records) <= 1
    ):
        raise ResponseIntegrityError(
            "OpenCitations multiplicity rule "
            "requires more than one record"
        )

    expected_token = (
        f"{request.identifier_namespace}:"
        f"{request.identifier}"
    )

    provider_ids = []
    reduced_records = []

    for record in records:
        if not isinstance(
            record,
            dict,
        ):
            raise ResponseIntegrityError(
                "OpenCitations multi-record "
                "response contains a non-object"
            )

        provider_id = record.get(
            "id"
        )

        if (
            not isinstance(
                provider_id,
                str,
            )
            or not provider_id.strip()
        ):
            raise ResponseIntegrityError(
                "OpenCitations multi-record "
                "response lacks a non-empty id"
            )

        provider_id = (
            provider_id.strip()
        )

        if (
            expected_token
            not in provider_id.split()
        ):
            raise ResponseIntegrityError(
                "OpenCitations multi-record "
                "response lacks the exact "
                "requested identifier token"
            )

        provider_ids.append(
            provider_id
        )

        reduced_records.append({
            key: value
            for key, value
            in record.items()
            if key
            not in (
                OPENCITATIONS_MULTIPLICITY_EXCLUDED_FIELDS
            )
        })

    if len(
        set(provider_ids)
    ) != 1:
        raise ResponseIntegrityError(
            "OpenCitations multi-record "
            "response has differing id bundles"
        )

    canonical_reduced = {
        canonical_json_bytes(
            record
        )
        for record in reduced_records
    }

    if len(
        canonical_reduced
    ) != 1:
        raise ResponseIntegrityError(
            "OpenCitations multi-record "
            "response differs outside "
            "venue/pub_date"
        )

    all_keys = sorted(
        set().union(
            *[
                set(record)
                for record in records
            ]
        )
    )

    varying_fields = []

    for key in all_keys:
        values = {
            canonical_json_bytes(
                record.get(
                    key,
                    None,
                )
            )
            for record in records
        }

        if len(values) > 1:
            varying_fields.append(
                key
            )

    if not set(
        varying_fields
    ).issubset(
        OPENCITATIONS_MULTIPLICITY_EXCLUDED_FIELDS
    ):
        raise ResponseIntegrityError(
            "OpenCitations multi-record "
            "response has an unpermitted "
            "varying field"
        )

    return (
        provider_ids[0],
        tuple(
            varying_fields
        ),
    )


def classify_response(
    request: RequestSpec,
    response: HTTPResponse,
) -> Classification:
    if response.status == 404:
        if request.provider in {
            "openalex",
            "opencitations_meta",
        }:
            return Classification(
                terminal_status=
                    "not_found",
                provider_identifier=None,
                metadata={},
            )

    if response.status != 200:
        raise ResponseIntegrityError(
            "Cannot classify non-200/non-negative "
            f"status {response.status}"
        )

    if request.provider == "openalex":
        try:
            value = json.loads(
                response.body.decode(
                    "utf-8"
                )
            )
        except Exception as exc:
            raise ResponseIntegrityError(
                "OpenAlex response is not valid JSON"
            ) from exc

        if not isinstance(
            value,
            dict,
        ):
            raise ResponseIntegrityError(
                "OpenAlex response is not one object"
            )

        provider_id = value.get(
            "id"
        )

        ids = value.get(
            "ids"
        )

        if (
            not isinstance(
                provider_id,
                str,
            )
            or not provider_id.strip()
        ):
            raise ResponseIntegrityError(
                "OpenAlex response lacks non-empty id"
            )

        if not isinstance(
            ids,
            dict,
        ):
            raise ResponseIntegrityError(
                "OpenAlex response lacks ids object"
            )

        return Classification(
            terminal_status="success",
            provider_identifier=
                provider_id.strip(),
            metadata={
                "provider_id":
                    provider_id.strip(),
            },
        )

    if request.provider == "opencitations_meta":
        try:
            value = json.loads(
                response.body.decode(
                    "utf-8"
                )
            )
        except Exception as exc:
            raise ResponseIntegrityError(
                "OpenCitations response is not valid JSON"
            ) from exc

        if not isinstance(
            value,
            list,
        ):
            raise ResponseIntegrityError(
                "OpenCitations response is not a list"
            )

        if len(value) == 0:
            return Classification(
                terminal_status=
                    "not_found",
                provider_identifier=None,
                metadata={},
            )

        if len(value) > 1:
            (
                provider_id,
                _varying_fields,
            ) = (
                validate_opencitations_multi_record_response(
                    request,
                    value,
                )
            )

            return Classification(
                terminal_status="success",
                provider_identifier=
                    provider_id,
                metadata={
                    "provider_id":
                        provider_id,
                },
            )

        if not isinstance(
            value[0],
            dict,
        ):
            raise ResponseIntegrityError(
                "OpenCitations record is not an object"
            )

        provider_id = value[0].get(
            "id"
        )

        if provider_id is not None:
            provider_id = str(
                provider_id
            ).strip() or None

        return Classification(
            terminal_status="success",
            provider_identifier=
                provider_id,
            metadata={
                "provider_id":
                    provider_id,
            },
        )

    if request.provider == "pubmed":
        try:
            root = ET.fromstring(
                response.body
            )
        except Exception as exc:
            raise ResponseIntegrityError(
                "PubMed response is not valid XML"
            ) from exc

        records = []

        for element in root.iter():
            tag = (
                element.tag.split(
                    "}",
                    1,
                )[-1]
            )

            if tag in {
                "PubmedArticle",
                "PubmedBookArticle",
            }:
                records.append(
                    element
                )

        if len(records) == 0:
            return Classification(
                terminal_status=
                    "not_found",
                provider_identifier=None,
                metadata={},
            )

        if len(records) != 1:
            raise ResponseIntegrityError(
                "PubMed exact lookup returned "
                f"{len(records)} records"
            )

        returned = extract_pubmed_primary_pmid(
            records[0]
        )

        if returned != request.identifier:
            raise ResponseIntegrityError(
                "PubMed returned incompatible PMID: "
                f"{returned} != "
                f"{request.identifier}"
            )

        return Classification(
            terminal_status="success",
            provider_identifier=returned,
            metadata={
                "provider_id":
                    returned,
            },
        )

    raise ResponseIntegrityError(
        "Unsupported provider during classification"
    )


def attempt_directory(
    root: Path,
    lookup_id: str,
    attempt_number: int,
) -> Path:
    safe_lookup = lookup_id.replace(
        ":",
        "_",
    )

    return (
        root
        / "raw"
        / safe_lookup
        / f"attempt_{attempt_number:02d}"
    )


def archive_hop(
    directory: Path,
    *,
    hop_number: int,
    request: RequestSpec,
    response: HTTPResponse,
) -> dict:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    body_name = (
        f"hop_{hop_number:02d}_body.bin"
    )

    header_name = (
        f"hop_{hop_number:02d}_response.json"
    )

    body_path = (
        directory / body_name
    )

    body_path.write_bytes(
        response.body
    )

    evidence = {
        "hop_number":
            hop_number,

        "request_url":
            sanitized_url(
                request.url
            ),

        "request_headers":
            list(
                redact_headers(
                    request.headers
                )
            ),

        "response_status":
            response.status,

        "response_url":
            sanitized_url(
                response.url
            ),

        "response_headers":
            list(
                redact_headers(
                    response.headers
                )
            ),

        "body_file":
            body_name,

        "body_sha256":
            sha256_bytes(
                response.body
            ),

        "body_length":
            len(
                response.body
            ),
    }

    (
        directory
        / header_name
    ).write_bytes(
        canonical_json_bytes(
            evidence
        )
    )

    return evidence


def request_with_redirects(
    request: RequestSpec,
    *,
    executor: Callable[
        [RequestSpec],
        HTTPResponse,
    ],
    archive_directory: Path,
) -> tuple[
    HTTPResponse,
    list[dict],
]:
    current = request
    evidence = []

    seen_urls = set()

    for hop in range(
        MAX_REDIRECT_HOPS + 1
    ):
        if current.url in seen_urls:
            raise RedirectFailure(
                "Redirect loop detected"
            )

        seen_urls.add(
            current.url
        )

        response = executor(
            current
        )

        evidence.append(
            archive_hop(
                archive_directory,
                hop_number=hop,
                request=current,
                response=response,
            )
        )

        if (
            response.status
            not in REDIRECT_STATUSES
        ):
            return (
                response,
                evidence,
            )

        location = header_value(
            response.headers,
            "Location",
        )

        if not location:
            raise RedirectFailure(
                "Redirect lacks Location header"
            )

        if hop >= MAX_REDIRECT_HOPS:
            raise RedirectFailure(
                "Redirect ceiling exceeded"
            )

        target = validate_redirect_target(
            provider=current.provider,
            current_url=current.url,
            location=location,
        )

        if current.provider == "openalex":
            target = (
                preserve_openalex_api_key_on_redirect(
                    current_url=current.url,
                    target_url=target,
                )
            )

        current = RequestSpec(
            logical_lookup_id=
                current.logical_lookup_id,

            provider=
                current.provider,

            route=
                current.route,

            identifier_namespace=
                current.identifier_namespace,

            identifier=
                current.identifier,

            method="GET",

            url=target,

            headers=current.headers,
        )

    raise RedirectFailure(
        "Redirect processing fell through"
    )


def transport_lookup(
    row: dict,
    *,
    archive_root: Path,
    executor: Callable[
        [RequestSpec],
        HTTPResponse,
    ],
    sleeper: Callable[[float], None],
    environ: dict[str, str] | None = None,
    now_fn: Callable[
        [],
        datetime,
    ] | None = None,
    start_attempt_number: int = 1,
    prior_attempts: list[dict] | None = None,
) -> dict:
    request = build_request(
        row,
        environ=environ,
    )

    if now_fn is None:
        now_fn = lambda: datetime.now(
            timezone.utc
        )

    if prior_attempts is None:
        prior_attempts = []

    if not (
        1
        <= start_attempt_number
        <= MAX_ATTEMPTS
    ):
        raise ValueError(
            "Invalid start_attempt_number: "
            f"{start_attempt_number}"
        )

    expected_prior_numbers = list(
        range(
            1,
            start_attempt_number,
        )
    )

    observed_prior_numbers = [
        int(
            record[
                "attempt_number"
            ]
        )
        for record
        in prior_attempts
    ]

    if (
        observed_prior_numbers
        != expected_prior_numbers
    ):
        raise ValueError(
            "Prior attempts are not a complete "
            "sequential prefix"
        )

    attempts = [
        dict(record)
        for record
        in prior_attempts
    ]

    for attempt_number in range(
        start_attempt_number,
        MAX_ATTEMPTS + 1,
    ):
        directory = attempt_directory(
            archive_root,
            request.logical_lookup_id,
            attempt_number,
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        request_record = {
            "timestamp_utc":
                utc_timestamp(
                    now_fn
                ),

            "logical_lookup_id":
                request.logical_lookup_id,

            "provider":
                request.provider,

            "route":
                request.route,

            "identifier_namespace":
                request.identifier_namespace,

            "identifier":
                request.identifier,

            "attempt_number":
                attempt_number,

            "method":
                request.method,

            "url":
                sanitized_url(
                    request.url
                ),

            "headers":
                list(
                    redact_headers(
                        request.headers
                    )
                ),
        }

        (
            directory
            / "request.json"
        ).write_bytes(
            canonical_json_bytes(
                request_record
            )
        )

        try:
            response, redirects = (
                request_with_redirects(
                    request,
                    executor=executor,
                    archive_directory=
                        directory,
                )
            )

        except (
            urllib.error.URLError,
            http.client.IncompleteRead,
            TimeoutError,
            socket.timeout,
            ConnectionError,
        ) as exc:
            record = {
                "attempt_number":
                    attempt_number,

                "outcome":
                    "retryable_transport_failure",

                "error_type":
                    type(exc).__name__,
            }

            attempts.append(
                record
            )

            (
                directory
                / "attempt.json"
            ).write_bytes(
                canonical_json_bytes(
                    record
                )
            )

            if attempt_number >= MAX_ATTEMPTS:
                return {
                    "logical_lookup_id":
                        request.logical_lookup_id,

                    "terminal_status":
                        "retry_exhausted",

                    "attempt_count":
                        attempt_number,

                    "attempts":
                        attempts,
                }

            sleeper(
                RETRY_DELAYS[
                    attempt_number
                ]
            )

            continue

        except RedirectFailure as exc:
            record = {
                "attempt_number":
                    attempt_number,

                "outcome":
                    "redirect_failure",

                "error_type":
                    type(exc).__name__,

                "error":
                    str(exc),
            }

            attempts.append(
                record
            )

            (
                directory
                / "attempt.json"
            ).write_bytes(
                canonical_json_bytes(
                    record
                )
            )

            return {
                "logical_lookup_id":
                    request.logical_lookup_id,

                "terminal_status":
                    "redirect_failure",

                "attempt_count":
                    attempt_number,

                "attempts":
                    attempts,
            }

        status = response.status

        if status in AUTH_FAILURE_STATUSES:
            record = {
                "attempt_number":
                    attempt_number,

                "outcome":
                    "authentication_failure",

                "http_status":
                    status,
            }

            attempts.append(
                record
            )

            (
                directory
                / "attempt.json"
            ).write_bytes(
                canonical_json_bytes(
                    record
                )
            )

            return {
                "logical_lookup_id":
                    request.logical_lookup_id,

                "terminal_status":
                    "authentication_failure",

                "attempt_count":
                    attempt_number,

                "attempts":
                    attempts,
            }

        if status == 400:
            record = {
                "attempt_number":
                    attempt_number,

                "outcome":
                    "response_integrity_failure",

                "http_status":
                    status,
            }

            attempts.append(
                record
            )

            (
                directory
                / "attempt.json"
            ).write_bytes(
                canonical_json_bytes(
                    record
                )
            )

            return {
                "logical_lookup_id":
                    request.logical_lookup_id,

                "terminal_status":
                    "response_integrity_failure",

                "attempt_count":
                    attempt_number,

                "attempts":
                    attempts,
            }

        if status in RETRYABLE_STATUSES:
            record = {
                "attempt_number":
                    attempt_number,

                "outcome":
                    "retryable_http_status",

                "http_status":
                    status,
            }

            attempts.append(
                record
            )

            (
                directory
                / "attempt.json"
            ).write_bytes(
                canonical_json_bytes(
                    record
                )
            )

            if attempt_number >= MAX_ATTEMPTS:
                return {
                    "logical_lookup_id":
                        request.logical_lookup_id,

                    "terminal_status":
                        "retry_exhausted",

                    "attempt_count":
                        attempt_number,

                    "attempts":
                        attempts,
                }

            delay = retry_after_seconds(
                response.headers,
                now=now_fn(),
            )

            if delay is None:
                delay = RETRY_DELAYS[
                    attempt_number
                ]

            sleeper(
                max(
                    float(
                        RETRY_DELAYS[
                            attempt_number
                        ]
                    ),
                    float(delay),
                )
            )

            continue

        if (
            status >= 400
            and status != 404
        ):
            record = {
                "attempt_number":
                    attempt_number,

                "outcome":
                    "response_integrity_failure",

                "http_status":
                    status,
            }

            attempts.append(
                record
            )

            (
                directory
                / "attempt.json"
            ).write_bytes(
                canonical_json_bytes(
                    record
                )
            )

            return {
                "logical_lookup_id":
                    request.logical_lookup_id,

                "terminal_status":
                    "response_integrity_failure",

                "attempt_count":
                    attempt_number,

                "attempts":
                    attempts,
            }

        try:
            classification = (
                classify_response(
                    request,
                    response,
                )
            )

        except ResponseIntegrityError as exc:
            record = {
                "attempt_number":
                    attempt_number,

                "outcome":
                    "response_integrity_failure",

                "http_status":
                    status,

                "error":
                    str(exc),
            }

            attempts.append(
                record
            )

            (
                directory
                / "attempt.json"
            ).write_bytes(
                canonical_json_bytes(
                    record
                )
            )

            return {
                "logical_lookup_id":
                    request.logical_lookup_id,

                "terminal_status":
                    "response_integrity_failure",

                "attempt_count":
                    attempt_number,

                "attempts":
                    attempts,
            }

        record = {
            "attempt_number":
                attempt_number,

            "outcome":
                classification.terminal_status,

            "http_status":
                status,

            "provider_identifier":
                classification.provider_identifier,

            "redirect_hops":
                len(redirects) - 1,

            "final_body_sha256":
                sha256_bytes(
                    response.body
                ),
        }

        attempts.append(
            record
        )

        (
            directory
            / "attempt.json"
        ).write_bytes(
            canonical_json_bytes(
                record
            )
        )

        terminal = {
            "logical_lookup_id":
                request.logical_lookup_id,

            "provider":
                request.provider,

            "route":
                request.route,

            "identifier_namespace":
                request.identifier_namespace,

            "identifier":
                request.identifier,

            "terminal_status":
                classification.terminal_status,

            "provider_identifier":
                classification.provider_identifier,

            "attempt_count":
                attempt_number,

            "attempts":
                attempts,

            "terminal_body_sha256":
                sha256_bytes(
                    response.body
                ),
        }

        lookup_root = (
            archive_root
            / "raw"
            / request.logical_lookup_id.replace(
                ":",
                "_",
            )
        )

        (
            lookup_root
            / "terminal.json"
        ).write_bytes(
            canonical_json_bytes(
                terminal
            )
        )

        return terminal

    raise RuntimeError(
        "Attempt loop fell through"
    )


class ProviderPacer:
    def __init__(
        self,
        interval_seconds: float = RATE_SECONDS,
        *,
        monotonic: Callable[
            [],
            float,
        ] = time.monotonic,
        sleeper: Callable[
            [float],
            None,
        ] = time.sleep,
    ):
        self.interval_seconds = (
            interval_seconds
        )

        self.monotonic = monotonic
        self.sleeper = sleeper
        self.last: dict[
            str,
            float,
        ] = {}

    def wait(
        self,
        provider: str,
    ) -> None:
        now = self.monotonic()

        if provider in self.last:
            earliest = (
                self.last[provider]
                + self.interval_seconds
            )

            if now < earliest:
                self.sleeper(
                    earliest - now
                )

                now = self.monotonic()

        self.last[
            provider
        ] = now


def verify_terminal_archive(
    lookup_root: Path,
) -> dict:
    terminal_path = (
        lookup_root
        / "terminal.json"
    )

    if not terminal_path.exists():
        raise RuntimeError(
            "Terminal archive missing"
        )

    terminal = json.loads(
        terminal_path.read_text(
            encoding="utf-8"
        )
    )

    attempt_number = int(
        terminal[
            "attempt_count"
        ]
    )

    attempt_root = (
        lookup_root
        / f"attempt_{attempt_number:02d}"
    )

    hop_files = sorted(
        attempt_root.glob(
            "hop_*_response.json"
        )
    )

    if not hop_files:
        raise RuntimeError(
            "Terminal attempt lacks archived response"
        )

    final_metadata = json.loads(
        hop_files[-1].read_text(
            encoding="utf-8"
        )
    )

    body_path = (
        attempt_root
        / final_metadata[
            "body_file"
        ]
    )

    body = body_path.read_bytes()

    actual = sha256_bytes(
        body
    )

    expected = final_metadata[
        "body_sha256"
    ]

    if actual != expected:
        raise RuntimeError(
            "Archived body checksum mismatch"
        )

    if (
        actual
        != terminal[
            "terminal_body_sha256"
        ]
    ):
        raise RuntimeError(
            "Terminal checksum differs from archived final body"
        )

    return terminal


def validate_completion(
    queue_rows: list[dict],
    terminal_rows: list[dict],
) -> dict:
    expected = {
        row[
            "logical_lookup_id"
        ]
        for row in queue_rows
    }

    observed = [
        row[
            "logical_lookup_id"
        ]
        for row in terminal_rows
    ]

    if len(observed) != len(
        set(observed)
    ):
        raise RuntimeError(
            "Duplicate logical lookup terminal status"
        )

    observed_set = set(
        observed
    )

    if observed_set != expected:
        raise RuntimeError(
            "Terminal lookup set differs from queue"
        )

    accepted = {
        "success",
        "not_found",
    }

    failures = [
        row
        for row in terminal_rows
        if row[
            "terminal_status"
        ]
        not in accepted
    ]

    if failures:
        return {
            "status":
                "INCOMPLETE",

            "logical_lookup_count":
                len(expected),

            "terminal_count":
                len(terminal_rows),

            "failure_count":
                len(failures),
        }

    return {
        "status":
            "COMPLETE",

        "logical_lookup_count":
            len(expected),

        "terminal_count":
            len(terminal_rows),

        "failure_count":
            0,
    }


def assert_live_execution_allowed(
    *,
    environ: dict[str, str],
) -> None:
    if not LIVE_EXECUTION_ENABLED:
        raise LiveExecutionBlocked(
            "Live metadata execution is hard-disabled "
            "until the transport implementation is frozen"
        )

    if environ.get(
        "BRANCHSNV_ALLOW_METADATA_NETWORK"
    ) != "YES":
        raise LiveExecutionBlocked(
            "BRANCHSNV_ALLOW_METADATA_NETWORK=YES "
            "is required"
        )

    require_ncbi_email(
        environ
    )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--queue",
        type=Path,
        default=QUEUE_PATH,
    )

    parser.add_argument(
        "--execute-live",
        action="store_true",
    )

    args = parser.parse_args()

    verify_frozen_queue()

    rows = read_queue(
        args.queue
    )

    if not args.execute_live:
        print(
            json.dumps(
                {
                    "status":
                        "DRY_RUN_ONLY",

                    "logical_lookup_count":
                        len(rows),

                    "live_execution_enabled":
                        LIVE_EXECUTION_ENABLED,

                    "message":
                        "Transport implementation loaded; "
                        "no network request executed.",
                },
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    assert_live_execution_allowed(
        environ=dict(
            os.environ
        )
    )

    raise LiveExecutionBlocked(
        "Production live runner intentionally "
        "not enabled in this implementation stage"
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
