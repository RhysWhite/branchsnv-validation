#!/usr/bin/env python3

"""
Experiment 07 T000002 authoritative-source network transport.

This module implements the transport capability frozen by the authoritative-
source network-transport design.

Important boundary:

* Network primitives exist in this module.
* Importing or inspecting this module performs no network activity.
* Read-only status performs no network activity.
* Live production execution requires a separately tracked one-use
  authorization.
* Scientific decisions, event-ledger mutation and review-packet mutation are
  prohibited.
* Hostile tests use injected fake adapters/resolvers only.

The HTTP implementation pins each connection to an IP address that has already
passed the frozen public-address policy while preserving TLS SNI/certificate
validation against the original hostname. This avoids validating one DNS
answer and then silently reconnecting through a second resolution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable
import argparse
import csv
import datetime as dt
import hashlib
import http.client
import importlib.util
import io
import ipaddress
import json
import os
import socket
import ssl
import subprocess
import sys
import time
import urllib.parse
import uuid
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

RESULTS_ROOT = (
    REPO_ROOT
    / "results"
    / "07_comparative_landscape"
)

EXECUTION_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_execution"
)

REVIEW_ROOT = (
    RESULTS_ROOT
    / "baseline_scientific_screening_review_work"
    / "B000001"
)

DEFAULT_LEDGER = (
    EXECUTION_ROOT
    / "event_ledger.tsv"
)

DEFAULT_REVIEW_PACKET = (
    REVIEW_ROOT
    / "review_packet.tsv"
)

PRODUCTION_ROOT = (
    RESULTS_ROOT
    / "t000002_authoritative_source_retrieval"
)

PRENETWORK_RUNNER = (
    HERE
    / "t000002_authoritative_source_retrieval.py"
)

PRENETWORK_IMPL_SUMS = (
    HERE
    / "t000002_authoritative_source_retrieval_implementation.sha256"
)

RETRIEVAL_DESIGN_SUMS = (
    HERE
    / "t000002_authoritative_source_retrieval_and_escalation_resolution_design.sha256"
)

T000002_COMPLETION_SUMS = (
    HERE
    / "t000002_production_completion_and_reconciliation.sha256"
)

TRANSPORT_DESIGN = (
    HERE
    / "t000002_authoritative_source_network_transport_and_live_retrieval_authorization_design.json"
)

TRANSPORT_DESIGN_SUMS = (
    HERE
    / "t000002_authoritative_source_network_transport_and_live_retrieval_authorization_design.sha256"
)

TRANSPORT_IMPLEMENTATION_SUMS = (
    HERE
    / "t000002_authoritative_source_network_transport_implementation.sha256"
)

LIVE_AUTHORIZATION = (
    HERE
    / "t000002_authoritative_source_live_retrieval_authorization.json"
)


EXPECTED_TRANSPORT_DESIGN_COMMIT = (
    "3312c68ed2b2a5e23769345cb457dddbfd32bcfe"
)

EXPECTED_PRENETWORK_RUNNER_SHA256 = (
    "f2ac303829b0d582737cde00a95384ed"
    "c6cc64936dec601847258bc503f724eb"
)

EXPECTED_NETWORK_POLICY_SHA256 = (
    "201ea525346222c72483e775aa2c5109"
    "aa355af22a27ccc2df4e956c50c63e6a"
)

EXPECTED_LIVE_AUTH_CONTRACT_SHA256 = (
    "8117f35c0c348afe49478a666aba0523"
    "1eff1bc131eba19b6baafb3bd7d82360"
)

EXPECTED_SEED_QUEUE_SHA256 = (
    "04b758cb6feb7460811116efef9b38a5"
    "09b5996f63ca30cf225d9cf75448c691"
)

EXPECTED_TARGET_IDENTITY_SHA256 = (
    "5970e1ec739b5b01c546e526c402d2f3"
    "a6e06e8f43aef0bfcd375e692bc2ab5e"
)

EXPECTED_LEDGER_SHA256 = (
    "fb90d762d4fe9e81410816fe9403c735"
    "de138fe1614c11cb83993b40f2c63dff"
)

EXPECTED_REVIEW_PACKET_SHA256 = (
    "09e08a25873e9a628a2c7900b82f384f"
    "7b5838bb166b89d412759fe92a9101d6"
)

EXPECTED_REVIEW_PACKET_BYTES = 314642

RUN_ID = "ASR000001"

REDIRECT_STATUSES = {
    301,
    302,
    303,
    307,
    308,
}

TRANSIENT_HTTP_STATUSES = {
    429,
    502,
    503,
    504,
}


class TransportError(
    RuntimeError
):
    pass


class TransportPolicyError(
    TransportError
):
    pass


class AuthorizationError(
    TransportError
):
    pass


class LiveAuthorizationRequiredError(
    AuthorizationError
):
    pass


class NetworkTransientError(
    TransportError
):
    pass


class NetworkTLSValidationError(
    TransportError
):
    pass


class PayloadTooLargeError(
    TransportError
):
    pass


class RecoveryRequiredError(
    TransportError
):
    pass


class ExistingRunError(
    RecoveryRequiredError
):
    pass


def sha256_bytes(
    payload: bytes,
) -> str:
    return hashlib.sha256(
        payload
    ).hexdigest()


def sha256_file(
    path: Path,
) -> str:
    return sha256_bytes(
        path.read_bytes()
    )


def canonical_json_bytes(
    value: Any,
) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )


def canonical_sha(
    value: Any,
) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            value
        )
    )


def pretty_json_bytes(
    value: Any,
) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode(
        "utf-8"
    )


def utc_now() -> str:
    return (
        dt.datetime.now(
            dt.timezone.utc
        )
        .replace(
            microsecond=0
        )
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


def write_bytes_atomic(
    path: Path,
    payload: bytes,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_name(
        "."
        + path.name
        + ".tmp."
        + uuid.uuid4().hex
    )

    temporary.write_bytes(
        payload
    )

    os.replace(
        temporary,
        path,
    )


def tsv_bytes(
    *,
    fields: list[str],
    rows: list[dict[str, str]],
) -> bytes:
    buffer = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        buffer,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )

    writer.writeheader()
    writer.writerows(
        rows
    )

    return buffer.getvalue().encode(
        "utf-8"
    )


def load_module(
    path: Path,
    name: str,
):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise TransportError(
            f"Unable to import {path}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    sys.modules[
        name
    ] = module

    spec.loader.exec_module(
        module
    )

    return module


def load_prenetwork_runner():
    if (
        sha256_file(
            PRENETWORK_RUNNER
        )
        != EXPECTED_PRENETWORK_RUNNER_SHA256
    ):
        raise TransportError(
            "Frozen pre-network retrieval runner SHA changed"
        )

    return load_module(
        PRENETWORK_RUNNER,
        "t000002_authoritative_source_retrieval_frozen",
    )


def load_transport_design() -> dict:
    value = json.loads(
        TRANSPORT_DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        value[
            "status"
        ]
        != "FROZEN_PRE_NETWORK_TRANSPORT_IMPLEMENTATION"
    ):
        raise TransportError(
            "Transport design status changed"
        )

    if (
        value[
            "parent_retrieval_implementation_commit"
        ]
        != (
            "a756caf01d49b6ffdd8ff7e4081d3f8fc12bdc9a"
        )
    ):
        raise TransportError(
            "Transport design parent changed"
        )

    if (
        canonical_sha(
            value[
                "network_policy"
            ]
        )
        != EXPECTED_NETWORK_POLICY_SHA256
    ):
        raise TransportError(
            "Network policy no longer reproduces frozen identity"
        )

    if (
        value[
            "network_policy_sha256"
        ]
        != EXPECTED_NETWORK_POLICY_SHA256
    ):
        raise TransportError(
            "Frozen network-policy SHA changed"
        )

    if (
        canonical_sha(
            value[
                "live_authorization_contract"
            ]
        )
        != EXPECTED_LIVE_AUTH_CONTRACT_SHA256
    ):
        raise TransportError(
            "Live-authorization contract no longer reproduces frozen identity"
        )

    if (
        value[
            "live_authorization_contract_sha256"
        ]
        != EXPECTED_LIVE_AUTH_CONTRACT_SHA256
    ):
        raise TransportError(
            "Frozen live-authorization-contract SHA changed"
        )

    frozen = value[
        "frozen_input"
    ]

    if (
        frozen[
            "seed_queue_sha256"
        ]
        != EXPECTED_SEED_QUEUE_SHA256
    ):
        raise TransportError(
            "Frozen seed queue identity changed"
        )

    if (
        frozen[
            "target_identity_sha256"
        ]
        != EXPECTED_TARGET_IDENTITY_SHA256
    ):
        raise TransportError(
            "Frozen target identity changed"
        )

    if (
        frozen[
            "ledger_sha256"
        ]
        != EXPECTED_LEDGER_SHA256
    ):
        raise TransportError(
            "Frozen pre-retrieval ledger identity changed"
        )

    if (
        frozen[
            "review_packet_sha256"
        ]
        != EXPECTED_REVIEW_PACKET_SHA256
    ):
        raise TransportError(
            "Frozen pre-retrieval packet identity changed"
        )

    authority = value[
        "authority_boundary"
    ]

    if authority[
        "network_execution_authorized_by_this_design"
    ]:
        raise TransportError(
            "Design unexpectedly grants live network authority"
        )

    if authority[
        "scientific_resolution_authorized_by_this_design"
    ]:
        raise TransportError(
            "Design unexpectedly grants scientific authority"
        )

    return value


def validate_scientific_state(
    *,
    ledger_path: Path,
    review_packet_path: Path,
) -> None:
    if (
        sha256_file(
            ledger_path
        )
        != EXPECTED_LEDGER_SHA256
    ):
        raise TransportError(
            "Production ledger differs from frozen pre-retrieval state"
        )

    if (
        sha256_file(
            review_packet_path
        )
        != EXPECTED_REVIEW_PACKET_SHA256
    ):
        raise TransportError(
            "Review packet differs from frozen pre-retrieval state"
        )

    if (
        review_packet_path.stat().st_size
        != EXPECTED_REVIEW_PACKET_BYTES
    ):
        raise TransportError(
            "Review packet byte count changed"
        )


def seed_queue_context(
    *,
    ledger_path: Path,
    review_packet_path: Path,
) -> dict:
    validate_scientific_state(
        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,
    )

    runner = load_prenetwork_runner()

    design = runner.load_design()

    runner.validate_current_state(
        design=
            design,

        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,
    )

    rows = runner.build_seed_queue(
        design=
            design,
    )

    payload = runner.tsv_bytes(
        fields=
            runner.QUEUE_FIELDS,

        rows=
            rows,
    )

    if (
        sha256_bytes(
            payload
        )
        != EXPECTED_SEED_QUEUE_SHA256
    ):
        raise TransportError(
            "Seed queue bytes differ from frozen identity"
        )

    if len(
        rows
    ) != 26:
        raise TransportError(
            "Expected exactly 26 frozen seed tasks"
        )

    return {
        "runner":
            runner,

        "retrieval_design":
            design,

        "rows":
            rows,

        "payload":
            payload,
    }


def default_resolver(
    hostname: str,
) -> list[str]:
    try:
        answers = socket.getaddrinfo(
            hostname,
            443,
            type=socket.SOCK_STREAM,
        )

    except socket.gaierror as exc:
        raise NetworkTransientError(
            f"DNS resolution failed for {hostname}: {exc}"
        ) from exc

    addresses = sorted({
        item[
            4
        ][
            0
        ]
        for item in answers
    })

    if not addresses:
        raise NetworkTransientError(
            f"DNS resolution returned no addresses for {hostname}"
        )

    return addresses


def public_ip_addresses(
    *,
    hostname: str,
    resolver: Callable[[str], list[str]],
) -> list[str]:
    try:
        ipaddress.ip_address(
            hostname
        )

    except ValueError:
        pass

    else:
        raise TransportPolicyError(
            "IP-literal destination hosts are prohibited"
        )

    addresses = resolver(
        hostname
    )

    if not addresses:
        raise TransportPolicyError(
            "Destination hostname has no resolved addresses"
        )

    validated = []

    for text in addresses:
        try:
            address = ipaddress.ip_address(
                text
            )

        except ValueError as exc:
            raise TransportPolicyError(
                f"Resolver returned invalid IP address: {text}"
            ) from exc

        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
            or not address.is_global
        ):
            raise TransportPolicyError(
                f"Destination resolved to prohibited address: {address}"
            )

        validated.append(
            str(
                address
            )
        )

    return sorted(
        set(
            validated
        )
    )


def validate_https_url(
    *,
    url: str,
    resolver: Callable[[str], list[str]],
) -> dict:
    try:
        parsed = urllib.parse.urlsplit(
            url
        )

    except ValueError as exc:
        raise TransportPolicyError(
            "Invalid URL"
        ) from exc

    if (
        parsed.scheme.lower()
        != "https"
    ):
        raise TransportPolicyError(
            "Only HTTPS destinations are permitted"
        )

    if (
        parsed.username is not None
        or parsed.password is not None
    ):
        raise TransportPolicyError(
            "URL userinfo is prohibited"
        )

    hostname = (
        parsed.hostname
        or ""
    ).lower()

    if not hostname:
        raise TransportPolicyError(
            "Destination hostname is required"
        )

    try:
        port = parsed.port

    except ValueError as exc:
        raise TransportPolicyError(
            "Invalid destination port"
        ) from exc

    if (
        port is not None
        and port != 443
    ):
        raise TransportPolicyError(
            "Non-default HTTPS ports are prohibited"
        )

    addresses = public_ip_addresses(
        hostname=
            hostname,

        resolver=
            resolver,
    )

    return {
        "url":
            url,

        "hostname":
            hostname,

        "resolved_addresses":
            addresses,

        "selected_address":
            addresses[
                0
            ],

        "path_and_query":
            urllib.parse.urlunsplit(
                (
                    "",
                    "",
                    parsed.path
                    or "/",
                    parsed.query,
                    "",
                )
            ),
    }


def build_initial_url(
    *,
    row: dict[str, str],
    network_policy: dict,
) -> str:
    route_code = row[
        "route_code"
    ]

    route = network_policy[
        "route_contracts"
    ][
        route_code
    ]

    value = row[
        "identifier_value"
    ]

    if (
        route_code
        == "pubmed_record"
    ):
        query = urllib.parse.urlencode([
            (
                "db",
                "pubmed",
            ),
            (
                "id",
                value,
            ),
            (
                "retmode",
                "xml",
            ),
        ])

        return (
            "https://eutils.ncbi.nlm.nih.gov"
            "/entrez/eutils/efetch.fcgi?"
            + query
        )

    if (
        route_code
        == "pubmed_pmc_link_discovery"
    ):
        query = urllib.parse.urlencode([
            (
                "db",
                "pmc",
            ),
            (
                "dbfrom",
                "pubmed",
            ),
            (
                "id",
                value,
            ),
            (
                "retmode",
                "xml",
            ),
        ])

        return (
            "https://eutils.ncbi.nlm.nih.gov"
            "/entrez/eutils/elink.fcgi?"
            + query
        )

    if (
        route_code
        == "doi_publisher_article"
    ):
        encoded = urllib.parse.quote(
            value,
            safe="",
        )

        return (
            "https://doi.org/"
            + encoded
        )

    raise TransportPolicyError(
        f"Unsupported frozen route: {route_code}"
    )


def validate_initial_url(
    *,
    row: dict[str, str],
    url: str,
    resolver: Callable[[str], list[str]],
    network_policy: dict,
) -> dict:
    validated = validate_https_url(
        url=
            url,

        resolver=
            resolver,
    )

    route = network_policy[
        "route_contracts"
    ][
        row[
            "route_code"
        ]
    ]

    if (
        validated[
            "hostname"
        ]
        != route[
            "initial_host"
        ]
    ):
        raise TransportPolicyError(
            "Initial route host differs from frozen contract"
        )

    return validated


def validate_redirect(
    *,
    route_code: str,
    source_url: str,
    target_url: str,
    resolver: Callable[[str], list[str]],
    network_policy: dict,
) -> dict:
    source = urllib.parse.urlsplit(
        source_url
    )

    target = validate_https_url(
        url=
            target_url,

        resolver=
            resolver,
    )

    if (
        route_code
        in {
            "pubmed_record",
            "pubmed_pmc_link_discovery",
        }
        and target[
            "hostname"
        ]
        != (
            source.hostname
            or ""
        ).lower()
    ):
        raise TransportPolicyError(
            "NCBI retrieval routes may not redirect cross-host"
        )

    return target


class PinnedHTTPSConnection(
    http.client.HTTPSConnection
):
    def __init__(
        self,
        *,
        hostname: str,
        resolved_ip: str,
        timeout: float,
        context: ssl.SSLContext,
    ):
        super().__init__(
            host=hostname,
            port=443,
            timeout=timeout,
            context=context,
        )

        self._resolved_ip = (
            resolved_ip
        )

    def connect(
        self,
    ) -> None:
        sock = socket.create_connection(
            (
                self._resolved_ip,
                443,
            ),
            timeout=
                self.timeout,
        )

        self.sock = self._context.wrap_socket(
            sock,
            server_hostname=
                self.host,
        )


class PinnedHTTPSAdapter:
    """
    One-request adapter.

    Redirects are deliberately not followed here. Redirect policy is enforced
    by the orchestration layer before a subsequent request is made.
    """

    def __init__(
        self,
        *,
        context: ssl.SSLContext | None = None,
    ):
        self.context = (
            context
            or ssl.create_default_context()
        )

    def request_once(
        self,
        *,
        url: str,
        resolved_ip: str,
        headers: dict[str, str],
        timeout_seconds: float,
        max_payload_bytes: int,
    ) -> dict:
        parsed = urllib.parse.urlsplit(
            url
        )

        hostname = (
            parsed.hostname
            or ""
        )

        path = urllib.parse.urlunsplit(
            (
                "",
                "",
                parsed.path
                or "/",
                parsed.query,
                "",
            )
        )

        connection = PinnedHTTPSConnection(
            hostname=
                hostname,

            resolved_ip=
                resolved_ip,

            timeout=
                timeout_seconds,

            context=
                self.context,
        )

        try:
            connection.request(
                "GET",
                path,
                headers=
                    headers,
            )

            response = connection.getresponse()

            response_headers = [
                [
                    key,
                    value,
                ]
                for (
                    key,
                    value,
                ) in response.getheaders()
            ]

            location = (
                response.getheader(
                    "Location"
                )
                or ""
            )

            # Redirect bodies are not needed to execute the frozen redirect
            # contract.
            if (
                response.status
                in REDIRECT_STATUSES
            ):
                payload = b""

            else:
                payload = response.read(
                    max_payload_bytes
                    + 1
                )

                if (
                    len(
                        payload
                    )
                    > max_payload_bytes
                ):
                    raise PayloadTooLargeError(
                        "Response exceeded frozen payload limit"
                    )

            return {
                "status":
                    int(
                        response.status
                    ),

                "reason":
                    str(
                        response.reason
                        or ""
                    ),

                "headers":
                    response_headers,

                "location":
                    location,

                "payload":
                    payload,
            }

        except ssl.SSLCertVerificationError as exc:
            raise NetworkTLSValidationError(
                f"TLS certificate validation failed: {exc}"
            ) from exc

        except ssl.SSLError as exc:
            raise NetworkTransientError(
                f"TLS transport error: {exc}"
            ) from exc

        except (
            socket.timeout,
            TimeoutError,
            ConnectionError,
            OSError,
            http.client.HTTPException,
        ) as exc:
            raise NetworkTransientError(
                f"Transient HTTPS transport error: {exc}"
            ) from exc

        finally:
            connection.close()


class RequestPacer:
    def __init__(
        self,
        *,
        minimum_interval_seconds: float,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        self.minimum_interval_seconds = (
            float(
                minimum_interval_seconds
            )
        )

        self.clock = clock
        self.sleeper = sleeper
        self.last_request_started = None

    def wait(
        self,
    ) -> None:
        now = self.clock()

        if (
            self.last_request_started
            is not None
        ):
            elapsed = (
                now
                - self.last_request_started
            )

            remaining = (
                self.minimum_interval_seconds
                - elapsed
            )

            if (
                remaining
                > 0
            ):
                self.sleeper(
                    remaining
                )

                now = self.clock()

        self.last_request_started = (
            now
        )


def headers_dict(
    pairs: Iterable[Iterable[str]],
) -> dict[str, str]:
    value = {}

    for pair in pairs:
        key, item = pair

        value[
            str(
                key
            ).lower()
        ] = str(
            item
        )

    return value


def normalized_content_type(
    headers: Iterable[Iterable[str]],
) -> str:
    value = headers_dict(
        headers
    ).get(
        "content-type",
        "",
    )

    return (
        value.split(
            ";",
            1,
        )[
            0
        ]
        .strip()
        .lower()
    )


def retry_after_seconds(
    *,
    headers: Iterable[Iterable[str]],
    maximum: int,
) -> float | None:
    raw = headers_dict(
        headers
    ).get(
        "retry-after",
        "",
    ).strip()

    if not raw:
        return None

    try:
        value = int(
            raw
        )

    except ValueError:
        return None

    if value < 0:
        return None

    return float(
        min(
            value,
            maximum,
        )
    )


def discover_pmcids(
    payload: bytes,
) -> list[str]:
    try:
        root = ET.fromstring(
            payload
        )

    except ET.ParseError:
        return []

    observed = []

    for node in root.findall(
        ".//LinkSetDb/Link/Id"
    ):
        text = (
            node.text
            or ""
        ).strip()

        if (
            text
            and text.isdigit()
        ):
            observed.append(
                "PMC"
                + text
            )

    return sorted(
        set(
            observed
        )
    )


def execute_seed_task(
    *,
    row: dict[str, str],
    network_policy: dict,
    adapter,
    resolver: Callable[[str], list[str]],
    pacer: RequestPacer,
    timestamp: Callable[[], str],
    sleeper: Callable[[float], None],
) -> dict:
    retry = network_policy[
        "retry_policy"
    ]

    request = network_policy[
        "request_policy"
    ]

    route = network_policy[
        "route_contracts"
    ][
        row[
            "route_code"
        ]
    ]

    max_attempts = int(
        retry[
            "maximum_attempts_per_seed_task"
        ]
    )

    max_redirects = int(
        network_policy[
            "redirect_policy"
        ][
            "maximum_redirects"
        ]
    )

    initial_url = build_initial_url(
        row=
            row,

        network_policy=
            network_policy,
    )

    attempts = []

    final_status = None
    final_payload = b""
    final_content_type = ""
    final_url = initial_url
    final_http_status = ""
    final_redirect_chain = []
    discovered_routes = []

    for attempt_number in range(
        1,
        max_attempts + 1,
    ):
        attempt_started = timestamp()

        current_url = initial_url
        redirect_chain = []

        attempt_status = None
        response = None
        payload = b""
        content_type = ""

        try:
            validated = validate_initial_url(
                row=
                    row,

                url=
                    current_url,

                resolver=
                    resolver,

                network_policy=
                    network_policy,
            )

            while True:
                pacer.wait()

                response = adapter.request_once(
                    url=
                        current_url,

                    resolved_ip=
                        validated[
                            "selected_address"
                        ],

                    headers=
                        request[
                            "default_headers"
                        ],

                    timeout_seconds=
                        float(
                            request[
                                "read_timeout_seconds"
                            ]
                        ),

                    max_payload_bytes=
                        int(
                            route[
                                "max_payload_bytes"
                            ]
                        ),
                )

                status = int(
                    response[
                        "status"
                    ]
                )

                if (
                    status
                    in REDIRECT_STATUSES
                ):
                    location = (
                        response.get(
                            "location",
                            ""
                        )
                        or ""
                    ).strip()

                    if not location:
                        attempt_status = (
                            "http_error"
                        )

                        final_http_status = str(
                            status
                        )

                        break

                    if (
                        len(
                            redirect_chain
                        )
                        >= max_redirects
                    ):
                        raise TransportPolicyError(
                            "Maximum redirect count exceeded"
                        )

                    target_url = urllib.parse.urljoin(
                        current_url,
                        location,
                    )

                    next_validated = validate_redirect(
                        route_code=
                            row[
                                "route_code"
                            ],

                        source_url=
                            current_url,

                        target_url=
                            target_url,

                        resolver=
                            resolver,

                        network_policy=
                            network_policy,
                    )

                    redirect_chain.append({
                        "status":
                            status,

                        "from":
                            current_url,

                        "to":
                            target_url,
                    })

                    current_url = (
                        target_url
                    )

                    validated = (
                        next_validated
                    )

                    continue

                payload = (
                    response.get(
                        "payload",
                        b"",
                    )
                    or b""
                )

                content_type = (
                    normalized_content_type(
                        response.get(
                            "headers",
                            [],
                        )
                    )
                )

                final_http_status = str(
                    status
                )

                if (
                    status
                    in TRANSIENT_HTTP_STATUSES
                ):
                    attempt_status = (
                        "transient_http_error"
                    )

                elif (
                    200
                    <= status
                    <= 299
                ):
                    accepted = {
                        item.lower()
                        for item in route[
                            "accepted_response_content_types"
                        ]
                    }

                    if (
                        content_type
                        and content_type
                        not in accepted
                    ):
                        attempt_status = (
                            "retrieved_unexpected_content_type"
                        )

                    else:
                        attempt_status = (
                            "retrieved"
                        )

                else:
                    attempt_status = (
                        "http_error"
                    )

                break

        except PayloadTooLargeError as exc:
            attempt_status = (
                "payload_too_large"
            )

            response = None
            payload = b""

            error_text = str(
                exc
            )

        except NetworkTLSValidationError as exc:
            attempt_status = (
                "tls_validation_failure"
            )

            response = None
            payload = b""

            error_text = str(
                exc
            )

        except TransportPolicyError as exc:
            attempt_status = (
                "policy_failure"
            )

            response = None
            payload = b""

            error_text = str(
                exc
            )

        except NetworkTransientError as exc:
            attempt_status = (
                "transient_transport_error"
            )

            response = None
            payload = b""

            error_text = str(
                exc
            )

        else:
            error_text = ""

        attempt_record = {
            "attempt_number":
                attempt_number,

            "retrieved_at_utc":
                attempt_started,

            "retrieval_status":
                attempt_status,

            "http_status":
                final_http_status,

            "content_type":
                content_type,

            "final_url":
                current_url,

            "redirect_chain":
                redirect_chain,

            "response_headers":
                (
                    response.get(
                        "headers",
                        [],
                    )
                    if response
                    else []
                ),

            "payload":
                payload,

            "payload_sha256":
                (
                    sha256_bytes(
                        payload
                    )
                    if payload
                    else ""
                ),

            "payload_bytes":
                len(
                    payload
                ),

            "error":
                error_text,
        }

        attempts.append(
            attempt_record
        )

        final_status = (
            attempt_status
        )

        final_payload = (
            payload
        )

        final_content_type = (
            content_type
        )

        final_url = (
            current_url
        )

        final_redirect_chain = (
            redirect_chain
        )

        retryable = (
            attempt_status
            in {
                "transient_http_error",
                "transient_transport_error",
            }
        )

        if (
            not retryable
            or attempt_number
            >= max_attempts
        ):
            break

        configured = retry[
            "backoff_seconds"
        ]

        backoff_index = (
            attempt_number
            - 1
        )

        if (
            backoff_index
            < len(
                configured
            )
        ):
            wait_seconds = float(
                configured[
                    backoff_index
                ]
            )

        else:
            wait_seconds = float(
                configured[
                    -1
                ]
            )

        if (
            response is not None
            and int(
                response[
                    "status"
                ]
            ) == 429
            and retry[
                "retry_after_header_may_extend_backoff"
            ]
        ):
            retry_after = retry_after_seconds(
                headers=
                    response.get(
                        "headers",
                        [],
                    ),

                maximum=
                    int(
                        retry[
                            "maximum_retry_after_seconds"
                        ]
                    ),
            )

            if (
                retry_after
                is not None
            ):
                wait_seconds = max(
                    wait_seconds,
                    retry_after,
                )

        sleeper(
            wait_seconds
        )

    if (
        row[
            "route_code"
        ]
        == "pubmed_pmc_link_discovery"
        and final_status
        in {
            "retrieved",
            "retrieved_unexpected_content_type",
        }
        and final_payload
    ):
        for pmcid in discover_pmcids(
            final_payload
        ):
            discovered_routes.append({
                "parent_queue_id":
                    row[
                        "queue_id"
                    ],

                "route_type":
                    "pmcid_full_text_candidate",

                "identifier":
                    pmcid,

                "executed":
                    False,
            })

    return {
        "queue_id":
            row[
                "queue_id"
            ],

        "position_in_batch":
            int(
                row[
                    "position_in_batch"
                ]
            ),

        "current_event_id":
            row[
                "current_event_id"
            ],

        "screening_entity_id":
            row[
                "screening_entity_id"
            ],

        "route_code":
            row[
                "route_code"
            ],

        "final_status":
            final_status,

        "final_http_status":
            final_http_status,

        "final_content_type":
            final_content_type,

        "final_url":
            final_url,

        "final_payload":
            final_payload,

        "final_redirect_chain":
            final_redirect_chain,

        "attempts":
            attempts,

        "discovered_routes":
            discovered_routes,
    }


def manifest_rows_for_result(
    *,
    queue_row: dict[str, str],
    result: dict,
    raw_relative_prefix: str = "raw",
) -> tuple[
    list[dict[str, str]],
    list[tuple[str, bytes]],
]:
    manifest = []
    raw_files = []

    for attempt in result[
        "attempts"
    ]:
        attempt_number = int(
            attempt[
                "attempt_number"
            ]
        )

        source_id = (
            queue_row[
                "queue_id"
            ]
            + f"-A{attempt_number:02d}"
        )

        payload = attempt[
            "payload"
        ]

        payload_relative = ""

        if payload:
            payload_relative = (
                raw_relative_prefix
                + "/"
                + source_id
                + ".payload"
            )

            raw_files.append(
                (
                    payload_relative,
                    payload,
                )
            )

        response_metadata = {
            "source_id":
                source_id,

            "queue_id":
                queue_row[
                    "queue_id"
                ],

            "attempt_number":
                attempt_number,

            "retrieved_at_utc":
                attempt[
                    "retrieved_at_utc"
                ],

            "retrieval_status":
                attempt[
                    "retrieval_status"
                ],

            "http_status":
                attempt[
                    "http_status"
                ],

            "content_type":
                attempt[
                    "content_type"
                ],

            "final_url":
                attempt[
                    "final_url"
                ],

            "redirect_chain":
                attempt[
                    "redirect_chain"
                ],

            "response_headers":
                attempt[
                    "response_headers"
                ],

            "payload_sha256":
                attempt[
                    "payload_sha256"
                ],

            "payload_bytes":
                attempt[
                    "payload_bytes"
                ],

            "error":
                attempt[
                    "error"
                ],

            "scientific_assessment":
                False,
        }

        metadata_relative = (
            raw_relative_prefix
            + "/"
            + source_id
            + ".response.json"
        )

        raw_files.append(
            (
                metadata_relative,
                pretty_json_bytes(
                    response_metadata
                ),
            )
        )

        notes = [
            (
                "attempt="
                + str(
                    attempt_number
                )
            ),
            (
                "redirect_count="
                + str(
                    len(
                        attempt[
                            "redirect_chain"
                        ]
                    )
                )
            ),
        ]

        if attempt[
            "error"
        ]:
            notes.append(
                "error="
                + attempt[
                    "error"
                ]
            )

        manifest.append({
            "position_in_batch":
                queue_row[
                    "position_in_batch"
                ],

            "current_event_id":
                queue_row[
                    "current_event_id"
                ],

            "screening_entity_id":
                queue_row[
                    "screening_entity_id"
                ],

            "source_id":
                source_id,

            "source_class":
                queue_row[
                    "expected_source_class"
                ],

            "authority_class":
                queue_row[
                    "authority_expectation"
                ],

            "locator":
                queue_row[
                    "locator"
                ],

            "retrieval_route":
                queue_row[
                    "route_code"
                ],

            "retrieved_at_utc":
                attempt[
                    "retrieved_at_utc"
                ],

            "retrieval_status":
                attempt[
                    "retrieval_status"
                ],

            "http_status":
                attempt[
                    "http_status"
                ],

            "content_type":
                attempt[
                    "content_type"
                ],

            "payload_sha256":
                attempt[
                    "payload_sha256"
                ],

            "payload_bytes":
                (
                    str(
                        attempt[
                            "payload_bytes"
                        ]
                    )
                    if payload
                    else ""
                ),

            "storage_mode":
                (
                    "archive_payload"
                    if payload
                    else "metadata_and_hash"
                ),

            "local_path":
                payload_relative,

            "license_or_access_note":
                "untracked_transport_evidence",

            "notes":
                "; ".join(
                    notes
                ),
        })

    return (
        manifest,
        raw_files,
    )


def checksum_manifest_bytes(
    *,
    root: Path,
    relative_paths: list[str],
) -> bytes:
    lines = []

    for relative in sorted(
        relative_paths
    ):
        path = (
            root
            / relative
        )

        digest = sha256_file(
            path
        )

        lines.append(
            digest
            + "  "
            + relative
            + "\n"
        )

    return "".join(
        lines
    ).encode(
        "utf-8"
    )


def existing_run_state(
    *,
    production_root: Path,
) -> dict:
    final = (
        production_root
        / RUN_ID
    )

    staging = sorted(
        production_root.glob(
            "."
            + RUN_ID
            + ".tmp.*"
        )
    ) if production_root.exists() else []

    if final.exists():
        return {
            "status":
                "FINAL_RUN_EXISTS",

            "final_path":
                str(
                    final
                ),

            "staging_paths":
                [
                    str(
                        path
                    )
                    for path in staging
                ],
        }

    if staging:
        return {
            "status":
                "STAGING_RUN_EXISTS",

            "final_path":
                "",

            "staging_paths":
                [
                    str(
                        path
                    )
                    for path in staging
                ],
        }

    return {
        "status":
            "NO_RUN",

        "final_path":
            "",

        "staging_paths":
            [],
    }


def assert_run_absent(
    *,
    production_root: Path,
) -> None:
    state = existing_run_state(
        production_root=
            production_root,
    )

    if (
        state[
            "status"
        ]
        != "NO_RUN"
    ):
        raise ExistingRunError(
            "ASR000001 cannot start from state: "
            + state[
                "status"
            ]
        )


def git_output(
    *args: str,
) -> str:
    return subprocess.check_output(
        [
            "git",
            *args,
        ],
        cwd=
            REPO_ROOT,
        text=True,
    ).strip()


def validate_authorization(
    *,
    authorization_path: Path,
    design: dict,
    require_tracked: bool,
    implementation_freeze_sha256_override: str | None = None,
) -> dict:
    authorization = json.loads(
        authorization_path.read_text(
            encoding="utf-8"
        )
    )

    contract = design[
        "live_authorization_contract"
    ]

    exact_fields = set(
        contract[
            "exact_fields"
        ]
    )

    if (
        set(
            authorization
        )
        != exact_fields
    ):
        raise AuthorizationError(
            "Live authorization schema mismatch"
        )

    if (
        authorization[
            "status"
        ]
        != contract[
            "status"
        ]
    ):
        raise AuthorizationError(
            "Live authorization status mismatch"
        )

    if (
        authorization[
            "schema_version"
        ]
        != 1
    ):
        raise AuthorizationError(
            "Live authorization schema version mismatch"
        )

    expected_impl_freeze_sha = (
        implementation_freeze_sha256_override
    )

    if require_tracked:
        if not TRANSPORT_IMPLEMENTATION_SUMS.is_file():
            raise AuthorizationError(
                "Frozen transport implementation checksum file is absent"
            )

        expected_impl_freeze_sha = (
            sha256_file(
                TRANSPORT_IMPLEMENTATION_SUMS
            )
        )

    if not expected_impl_freeze_sha:
        raise AuthorizationError(
            "Transport implementation freeze identity is required"
        )

    exact_values = {
        "network_transport_design_freeze_sha256":
            sha256_file(
                TRANSPORT_DESIGN_SUMS
            ),

        "network_transport_implementation_freeze_sha256":
            expected_impl_freeze_sha,

        "retrieval_implementation_freeze_sha256":
            sha256_file(
                PRENETWORK_IMPL_SUMS
            ),

        "retrieval_design_freeze_sha256":
            sha256_file(
                RETRIEVAL_DESIGN_SUMS
            ),

        "t000002_completion_freeze_sha256":
            sha256_file(
                T000002_COMPLETION_SUMS
            ),

        "retrieval_run_id":
            RUN_ID,

        "target_identity_sha256":
            EXPECTED_TARGET_IDENTITY_SHA256,

        "seed_queue_sha256":
            EXPECTED_SEED_QUEUE_SHA256,

        "seed_queue_task_count":
            26,

        "authorized_queue_ids": [
            f"RQ{value:06d}"
            for value in range(
                1,
                27,
            )
        ],

        "authorized_route_codes": [
            "pubmed_record",
            "pubmed_pmc_link_discovery",
            "doi_publisher_article",
        ],

        "network_policy_sha256":
            EXPECTED_NETWORK_POLICY_SHA256,

        "expected_pre_ledger_sha256":
            EXPECTED_LEDGER_SHA256,

        "expected_pre_review_packet_sha256":
            EXPECTED_REVIEW_PACKET_SHA256,

        "production_root":
            (
                "results/07_comparative_landscape/"
                "t000002_authoritative_source_retrieval"
            ),

        "operator_id":
            "Rhys",

        "operator_type":
            "human_with_assistance",

        "all_seed_tasks_must_be_considered":
            True,

        "successful_response_required_for_every_task":
            False,

        "dynamic_child_route_execution_authorized":
            False,

        "scientific_decisions_authorized":
            False,

        "event_ledger_mutation_authorized":
            False,

        "review_packet_mutation_authorized":
            False,

        "one_use":
            True,
    }

    for (
        key,
        expected,
    ) in exact_values.items():
        if (
            authorization[
                key
            ]
            != expected
        ):
            raise AuthorizationError(
                f"Live authorization field mismatch: {key}"
            )

    parent_commit = (
        authorization[
            "parent_commit"
        ]
    )

    if (
        not isinstance(
            parent_commit,
            str,
        )
        or len(
            parent_commit
        )
        != 40
        or any(
            character
            not in "0123456789abcdef"
            for character in parent_commit
        )
    ):
        raise AuthorizationError(
            "Invalid authorization parent commit"
        )

    authorization_commit = (
        "UNTRACKED_TEST_AUTHORIZATION"
    )

    if require_tracked:
        canonical = (
            LIVE_AUTHORIZATION.resolve()
        )

        if (
            authorization_path.resolve()
            != canonical
        ):
            raise AuthorizationError(
                "Real live authorization must use canonical path"
            )

        relative = (
            LIVE_AUTHORIZATION.relative_to(
                REPO_ROOT
            )
            .as_posix()
        )

        head = git_output(
            "rev-parse",
            "HEAD",
        )

        head_parent = git_output(
            "rev-parse",
            "HEAD^",
        )

        if (
            parent_commit
            != head_parent
        ):
            raise AuthorizationError(
                "Authorization parent is not current HEAD parent"
            )

        try:
            tracked = git_output(
                "ls-files",
                "--error-unmatch",
                relative,
            )

        except subprocess.CalledProcessError as exc:
            raise AuthorizationError(
                "Live authorization is not tracked"
            ) from exc

        if (
            tracked
            != relative
        ):
            raise AuthorizationError(
                "Unexpected tracked authorization path"
            )

        introducing_commit = git_output(
            "log",
            "-1",
            "--format=%H",
            "--",
            relative,
        )

        if (
            introducing_commit
            != head
        ):
            raise AuthorizationError(
                "Live authorization was not introduced by current HEAD"
            )

        changed = set(
            git_output(
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                "HEAD",
            ).splitlines()
        )

        if (
            changed
            != {
                relative
            }
        ):
            raise AuthorizationError(
                "Live authorization commit must contain exactly one file"
            )

        committed_bytes = subprocess.check_output(
            [
                "git",
                "show",
                "HEAD:"
                + relative,
            ],
            cwd=
                REPO_ROOT,
        )

        if (
            committed_bytes
            != authorization_path.read_bytes()
        ):
            raise AuthorizationError(
                "Working authorization differs from committed authorization"
            )

        transport_relative = (
            Path(__file__)
            .resolve()
            .relative_to(
                REPO_ROOT
            )
            .as_posix()
        )

        parent_transport = subprocess.check_output(
            [
                "git",
                "show",
                "HEAD^:"
                + transport_relative,
            ],
            cwd=
                REPO_ROOT,
        )

        if (
            sha256_bytes(
                parent_transport
            )
            != sha256_file(
                Path(__file__).resolve()
            )
        ):
            raise AuthorizationError(
                "Authorization parent does not contain this frozen transport implementation"
            )

        authorization_commit = (
            head
        )

    return {
        "authorization":
            authorization,

        "authorization_commit":
            authorization_commit,

        "authorization_sha256":
            sha256_file(
                authorization_path
            ),
    }


def synthetic_authorization(
    *,
    design: dict,
    parent_commit: str = "0" * 40,
    implementation_freeze_sha256: str = "1" * 64,
) -> dict:
    contract = design[
        "live_authorization_contract"
    ]

    return {
        "status":
            contract[
                "status"
            ],

        "schema_version":
            1,

        "parent_commit":
            parent_commit,

        "network_transport_design_freeze_sha256":
            sha256_file(
                TRANSPORT_DESIGN_SUMS
            ),

        "network_transport_implementation_freeze_sha256":
            implementation_freeze_sha256,

        "retrieval_implementation_freeze_sha256":
            sha256_file(
                PRENETWORK_IMPL_SUMS
            ),

        "retrieval_design_freeze_sha256":
            sha256_file(
                RETRIEVAL_DESIGN_SUMS
            ),

        "t000002_completion_freeze_sha256":
            sha256_file(
                T000002_COMPLETION_SUMS
            ),

        "retrieval_run_id":
            RUN_ID,

        "target_identity_sha256":
            EXPECTED_TARGET_IDENTITY_SHA256,

        "seed_queue_sha256":
            EXPECTED_SEED_QUEUE_SHA256,

        "seed_queue_task_count":
            26,

        "authorized_queue_ids": [
            f"RQ{value:06d}"
            for value in range(
                1,
                27,
            )
        ],

        "authorized_route_codes": [
            "pubmed_record",
            "pubmed_pmc_link_discovery",
            "doi_publisher_article",
        ],

        "network_policy_sha256":
            EXPECTED_NETWORK_POLICY_SHA256,

        "expected_pre_ledger_sha256":
            EXPECTED_LEDGER_SHA256,

        "expected_pre_review_packet_sha256":
            EXPECTED_REVIEW_PACKET_SHA256,

        "production_root":
            (
                "results/07_comparative_landscape/"
                "t000002_authoritative_source_retrieval"
            ),

        "operator_id":
            "Rhys",

        "operator_type":
            "human_with_assistance",

        "all_seed_tasks_must_be_considered":
            True,

        "successful_response_required_for_every_task":
            False,

        "dynamic_child_route_execution_authorized":
            False,

        "scientific_decisions_authorized":
            False,

        "event_ledger_mutation_authorized":
            False,

        "review_packet_mutation_authorized":
            False,

        "one_use":
            True,
    }


def create_header_only_evidence_assessment(
    *,
    runner,
) -> bytes:
    return tsv_bytes(
        fields=
            runner.EVIDENCE_ASSESSMENT_FIELDS,

        rows=[],
    )


def execute_seed_run(
    *,
    authorization_path: Path,
    ledger_path: Path,
    review_packet_path: Path,
    production_root: Path,
    adapter,
    resolver: Callable[[str], list[str]],
    timestamp: Callable[[], str],
    monotonic_clock: Callable[[], float],
    sleeper: Callable[[float], None],
    require_tracked_authorization: bool,
    implementation_freeze_sha256_override: str | None = None,
    allow_noncanonical_root: bool = False,
) -> dict:
    transport_design = load_transport_design()

    auth_validation = validate_authorization(
        authorization_path=
            authorization_path,

        design=
            transport_design,

        require_tracked=
            require_tracked_authorization,

        implementation_freeze_sha256_override=
            implementation_freeze_sha256_override,
    )

    if (
        not allow_noncanonical_root
        and production_root.resolve()
        != PRODUCTION_ROOT.resolve()
    ):
        raise TransportPolicyError(
            "Real retrieval execution requires canonical production root"
        )

    if (
        allow_noncanonical_root
        and production_root.resolve()
        == PRODUCTION_ROOT.resolve()
    ):
        raise TransportPolicyError(
            "Test execution cannot target canonical production root"
        )

    validate_scientific_state(
        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,
    )

    queue_context = seed_queue_context(
        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,
    )

    runner = queue_context[
        "runner"
    ]

    rows = queue_context[
        "rows"
    ]

    queue_payload = queue_context[
        "payload"
    ]

    if len(
        rows
    ) != auth_validation[
        "authorization"
    ][
        "seed_queue_task_count"
    ]:
        raise AuthorizationError(
            "Authorized seed task count differs from frozen queue"
        )

    assert_run_absent(
        production_root=
            production_root,
    )

    # Authorization consumption begins here. From this point onward, staging
    # evidence is preserved if execution is interrupted.
    production_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    staging = (
        production_root
        / (
            "."
            + RUN_ID
            + ".tmp."
            + uuid.uuid4().hex
        )
    )

    staging.mkdir()

    raw_dir = (
        staging
        / "raw"
    )

    raw_dir.mkdir()

    try:
        write_bytes_atomic(
            staging
            / "authorization.json",

            authorization_path.read_bytes(),
        )

        write_bytes_atomic(
            staging
            / "seed_queue.tsv",

            queue_payload,
        )

        pacer = RequestPacer(
            minimum_interval_seconds=
                float(
                    transport_design[
                        "network_policy"
                    ][
                        "request_policy"
                    ][
                        "global_minimum_interval_seconds"
                    ]
                ),

            clock=
                monotonic_clock,

            sleeper=
                sleeper,
        )

        manifest_rows = []
        results = []
        discovered_routes = []

        for row in rows:
            result = execute_seed_task(
                row=
                    row,

                network_policy=
                    transport_design[
                        "network_policy"
                    ],

                adapter=
                    adapter,

                resolver=
                    resolver,

                pacer=
                    pacer,

                timestamp=
                    timestamp,

                sleeper=
                    sleeper,
            )

            results.append(
                result
            )

            manifest_part, raw_files = (
                manifest_rows_for_result(
                    queue_row=
                        row,

                    result=
                        result,
                )
            )

            manifest_rows.extend(
                manifest_part
            )

            discovered_routes.extend(
                result[
                    "discovered_routes"
                ]
            )

            for (
                relative,
                payload,
            ) in raw_files:
                write_bytes_atomic(
                    staging
                    / relative,

                    payload,
                )

        if len(
            results
        ) != 26:
            raise RecoveryRequiredError(
                "Live retrieval did not consider all 26 frozen seed tasks"
            )

        final_status_counts = {}

        for result in results:
            key = (
                result[
                    "final_status"
                ]
                or "unknown"
            )

            final_status_counts[
                key
            ] = (
                final_status_counts.get(
                    key,
                    0,
                )
                + 1
            )

        summary = {
            "status":
                "ASR000001_COMPLETE",

            "retrieval_run_id":
                RUN_ID,

            "authorization_commit":
                auth_validation[
                    "authorization_commit"
                ],

            "authorization_sha256":
                auth_validation[
                    "authorization_sha256"
                ],

            "target_identity_sha256":
                EXPECTED_TARGET_IDENTITY_SHA256,

            "seed_queue_sha256":
                EXPECTED_SEED_QUEUE_SHA256,

            "seed_task_count":
                26,

            "tasks_considered":
                len(
                    results
                ),

            "transport_attempt_count":
                sum(
                    len(
                        result[
                            "attempts"
                        ]
                    )
                    for result in results
                ),

            "final_transport_status_counts":
                dict(
                    sorted(
                        final_status_counts.items()
                    )
                ),

            "discovered_child_routes":
                discovered_routes,

            "dynamic_child_routes_executed":
                False,

            "scientific_decisions_made":
                False,

            "event_ledger_mutated":
                False,

            "review_packet_mutated":
                False,

            "pre_ledger_sha256":
                EXPECTED_LEDGER_SHA256,

            "pre_review_packet_sha256":
                EXPECTED_REVIEW_PACKET_SHA256,
        }

        manifest_payload = tsv_bytes(
            fields=
                runner.RETRIEVAL_MANIFEST_FIELDS,

            rows=
                manifest_rows,
        )

        write_bytes_atomic(
            staging
            / "retrieval_manifest.tsv",

            manifest_payload,
        )

        write_bytes_atomic(
            staging
            / "retrieval_summary.json",

            pretty_json_bytes(
                summary
            ),
        )

        write_bytes_atomic(
            staging
            / "evidence_assessment.tsv",

            create_header_only_evidence_assessment(
                runner=
                    runner,
            ),
        )

        checksum_paths = [
            str(
                path.relative_to(
                    staging
                )
            )
            for path in staging.rglob(
                "*"
            )
            if (
                path.is_file()
                and path.name
                != "checksums.sha256"
            )
        ]

        write_bytes_atomic(
            staging
            / "checksums.sha256",

            checksum_manifest_bytes(
                root=
                    staging,

                relative_paths=
                    checksum_paths,
            ),
        )

        # Scientific state must still be byte-identical before publication of
        # the retrieval evidence directory.
        validate_scientific_state(
            ledger_path=
                ledger_path,

            review_packet_path=
                review_packet_path,
        )

        final = (
            production_root
            / RUN_ID
        )

        os.replace(
            staging,
            final,
        )

        return {
            "status":
                "ASR000001_EXECUTION_COMPLETE",

            "retrieval_run_id":
                RUN_ID,

            "authorization_commit":
                auth_validation[
                    "authorization_commit"
                ],

            "authorization_sha256":
                auth_validation[
                    "authorization_sha256"
                ],

            "seed_queue_sha256":
                EXPECTED_SEED_QUEUE_SHA256,

            "tasks_considered":
                26,

            "transport_attempt_count":
                summary[
                    "transport_attempt_count"
                ],

            "final_transport_status_counts":
                summary[
                    "final_transport_status_counts"
                ],

            "discovered_child_route_count":
                len(
                    discovered_routes
                ),

            "scientific_decisions_made":
                False,

            "event_ledger_mutated":
                False,

            "review_packet_mutated":
                False,

            "final_run_directory":
                str(
                    final
                ),

            "mutation_performed":
                True,
        }

    except Exception as exc:
        # Once staging exists, the authorization has entered the one-use live
        # lifecycle. Preserve all evidence and require explicit recovery.
        raise RecoveryRequiredError(
            "ASR000001 interrupted after authorization consumption; "
            f"staging evidence preserved at {staging}"
        ) from exc


def describe_status(
    *,
    ledger_path: Path,
    review_packet_path: Path,
) -> dict:
    design = load_transport_design()

    queue = seed_queue_context(
        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,
    )

    run_state = existing_run_state(
        production_root=
            PRODUCTION_ROOT,
    )

    return {
        "status":
            (
                "T000002_AUTHORITATIVE_SOURCE_NETWORK_TRANSPORT_"
                "IMPLEMENTED_PRE_LIVE_AUTHORIZATION"
            ),

        "transport_design_commit":
            EXPECTED_TRANSPORT_DESIGN_COMMIT,

        "network_policy_sha256":
            EXPECTED_NETWORK_POLICY_SHA256,

        "live_authorization_contract_sha256":
            EXPECTED_LIVE_AUTH_CONTRACT_SHA256,

        "target_identity_sha256":
            EXPECTED_TARGET_IDENTITY_SHA256,

        "seed_queue_sha256":
            sha256_bytes(
                queue[
                    "payload"
                ]
            ),

        "seed_queue_task_count":
            len(
                queue[
                    "rows"
                ]
            ),

        "network_transport_implemented":
            True,

        "dns_pinning_implemented":
            True,

        "tls_hostname_validation_required":
            True,

        "ssrf_policy_implemented":
            True,

        "redirect_policy_implemented":
            True,

        "payload_limits_implemented":
            True,

        "retry_policy_implemented":
            True,

        "production_retrieval_state":
            run_state[
                "status"
            ],

        "live_authorization_present":
            LIVE_AUTHORIZATION.exists(),

        "live_network_execution_authorized":
            False,

        "scientific_decisions_allowed":
            False,

        "event_ledger_mutation_allowed":
            False,

        "review_packet_mutation_allowed":
            False,

        "ledger_sha256":
            sha256_file(
                ledger_path
            ),

        "review_packet_sha256":
            sha256_file(
                review_packet_path
            ),

        "mutation_performed":
            False,
    }


def execute_live(
    *,
    authorization_path: Path,
    ledger_path: Path,
    review_packet_path: Path,
) -> dict:
    # Validate a tracked one-use authorization BEFORE creating a production
    # directory or making any DNS/network call.
    design = load_transport_design()

    validate_authorization(
        authorization_path=
            authorization_path,

        design=
            design,

        require_tracked=
            True,
    )

    assert_run_absent(
        production_root=
            PRODUCTION_ROOT,
    )

    return execute_seed_run(
        authorization_path=
            authorization_path,

        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,

        production_root=
            PRODUCTION_ROOT,

        adapter=
            PinnedHTTPSAdapter(),

        resolver=
            default_resolver,

        timestamp=
            utc_now,

        monotonic_clock=
            time.monotonic,

        sleeper=
            time.sleep,

        require_tracked_authorization=
            True,

        allow_noncanonical_root=
            False,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
    )

    parser.add_argument(
        "--review-packet",
        type=Path,
        default=DEFAULT_REVIEW_PACKET,
    )

    parser.add_argument(
        "--authorization-json",
        type=Path,
    )

    parser.add_argument(
        "--execute-live",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    ledger = (
        args.ledger.resolve()
    )

    review = (
        args.review_packet.resolve()
    )

    if args.execute_live:
        if (
            args.authorization_json
            is None
        ):
            raise LiveAuthorizationRequiredError(
                "Live network execution requires the separately tracked "
                "one-use authorization"
            )

        result = execute_live(
            authorization_path=
                args.authorization_json.resolve(),

            ledger_path=
                ledger,

            review_packet_path=
                review,
        )

        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    print(
        json.dumps(
            describe_status(
                ledger_path=
                    ledger,

                review_packet_path=
                    review,
            ),
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
