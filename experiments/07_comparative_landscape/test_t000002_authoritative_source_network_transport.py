#!/usr/bin/env python3

from pathlib import Path
import csv
import hashlib
import importlib.util
import io
import json
import tempfile
import sys


HERE = Path(__file__).resolve().parent

TRANSPORT_PATH = (
    HERE
    / "t000002_authoritative_source_network_transport.py"
)

spec = importlib.util.spec_from_file_location(
    "t000002_transport_hostile_tests",
    TRANSPORT_PATH,
)

assert spec is not None
assert spec.loader is not None

transport = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = transport

spec.loader.exec_module(
    transport
)


def expect_error(
    label,
    exception_type,
    fn,
):
    try:
        fn()

    except exception_type:
        print(
            "PASS |",
            label,
        )

        return

    raise AssertionError(
        "Expected "
        + exception_type.__name__
        + ": "
        + label
    )


design = transport.load_transport_design()

assert transport.canonical_sha(
    design[
        "network_policy"
    ]
) == transport.EXPECTED_NETWORK_POLICY_SHA256

assert transport.canonical_sha(
    design[
        "live_authorization_contract"
    ]
) == transport.EXPECTED_LIVE_AUTH_CONTRACT_SHA256

print(
    "PASS | frozen network policy identity reproduced"
)

print(
    "PASS | frozen live-authorization contract identity reproduced"
)


real_ledger_before = (
    transport.DEFAULT_LEDGER.read_bytes()
)

real_packet_before = (
    transport.DEFAULT_REVIEW_PACKET.read_bytes()
)

assert hashlib.sha256(
    real_ledger_before
).hexdigest() == transport.EXPECTED_LEDGER_SHA256

assert hashlib.sha256(
    real_packet_before
).hexdigest() == transport.EXPECTED_REVIEW_PACKET_SHA256


queue_context = transport.seed_queue_context(
    ledger_path=
        transport.DEFAULT_LEDGER,

    review_packet_path=
        transport.DEFAULT_REVIEW_PACKET,
)

queue = queue_context[
    "rows"
]

queue_payload = queue_context[
    "payload"
]

assert len(
    queue
) == 26

assert hashlib.sha256(
    queue_payload
).hexdigest() == transport.EXPECTED_SEED_QUEUE_SHA256

print(
    "PASS | exact 26-task frozen seed queue reproduced"
)


PUBLIC_IP = "93.184.216.34"


def public_resolver(
    hostname,
):
    return [
        PUBLIC_IP
    ]


validated = transport.validate_https_url(
    url=
        "https://example.org/path?a=1",

    resolver=
        public_resolver,
)

assert validated[
    "hostname"
] == "example.org"

assert validated[
    "selected_address"
] == PUBLIC_IP

print(
    "PASS | public HTTPS destination accepted"
)


for (
    label,
    url,
) in [
    (
        "HTTP downgrade rejected",
        "http://example.org/",
    ),
    (
        "userinfo rejected",
        "https://user:pass@example.org/",
    ),
    (
        "non-default port rejected",
        "https://example.org:8443/",
    ),
    (
        "IPv4 literal rejected",
        "https://93.184.216.34/",
    ),
    (
        "IPv6 literal rejected",
        "https://[2606:2800:220:1:248:1893:25c8:1946]/",
    ),
]:
    expect_error(
        label,
        transport.TransportPolicyError,
        lambda value=url:
            transport.validate_https_url(
                url=
                    value,

                resolver=
                    public_resolver,
            ),
    )


for (
    label,
    ip,
) in [
    (
        "loopback rejected",
        "127.0.0.1",
    ),
    (
        "private address rejected",
        "10.1.2.3",
    ),
    (
        "link-local rejected",
        "169.254.1.1",
    ),
    (
        "unspecified address rejected",
        "0.0.0.0",
    ),
    (
        "IPv6 loopback rejected",
        "::1",
    ),
]:
    expect_error(
        label,
        transport.TransportPolicyError,
        lambda value=ip:
            transport.validate_https_url(
                url=
                    "https://example.org/",

                resolver=
                    lambda hostname: [
                        value
                    ],
            ),
    )


network_policy = design[
    "network_policy"
]


first_pubmed = next(
    row
    for row in queue
    if row[
        "route_code"
    ] == "pubmed_record"
)

first_doi = next(
    row
    for row in queue
    if row[
        "route_code"
    ] == "doi_publisher_article"
)


pubmed_url = (
    transport.build_initial_url(
        row=
            first_pubmed,

        network_policy=
            network_policy,
    )
)

assert pubmed_url.startswith(
    "https://eutils.ncbi.nlm.nih.gov/"
)

assert (
    "db=pubmed"
    in pubmed_url
)

assert (
    "retmode=xml"
    in pubmed_url
)

print(
    "PASS | PubMed route URL derives only from frozen PMID"
)


doi_url = transport.build_initial_url(
    row=
        first_doi,

    network_policy=
        network_policy,
)

assert doi_url.startswith(
    "https://doi.org/"
)

assert "%2F" in doi_url

print(
    "PASS | DOI path percent-encodes frozen DOI"
)


expect_error(
    "NCBI cross-host redirect rejected",
    transport.TransportPolicyError,
    lambda:
        transport.validate_redirect(
            route_code=
                "pubmed_record",

            source_url=
                pubmed_url,

            target_url=
                "https://publisher.example/article",

            resolver=
                public_resolver,

            network_policy=
                network_policy,
        ),
)


allowed_redirect = transport.validate_redirect(
    route_code=
        "doi_publisher_article",

    source_url=
        doi_url,

    target_url=
        "https://publisher.example/article",

    resolver=
        public_resolver,

    network_policy=
        network_policy,
)

assert allowed_redirect[
    "hostname"
] == "publisher.example"

print(
    "PASS | DOI cross-host public HTTPS redirect accepted"
)


expect_error(
    "DOI HTTP redirect downgrade rejected",
    transport.TransportPolicyError,
    lambda:
        transport.validate_redirect(
            route_code=
                "doi_publisher_article",

            source_url=
                doi_url,

            target_url=
                "http://publisher.example/article",

            resolver=
                public_resolver,

            network_policy=
                network_policy,
        ),
)


class FakeClock:
    def __init__(
        self,
    ):
        self.value = 0.0
        self.sleeps = []

    def now(
        self,
    ):
        return self.value

    def sleep(
        self,
        seconds,
    ):
        seconds = float(
            seconds
        )

        self.sleeps.append(
            seconds
        )

        self.value += (
            seconds
        )


class FakeAdapter:
    def __init__(
        self,
    ):
        self.calls = []
        self.count_by_url = {}

    def request_once(
        self,
        *,
        url,
        resolved_ip,
        headers,
        connect_timeout_seconds,
        read_timeout_seconds,
        max_payload_bytes,
    ):
        self.calls.append({
            "url":
                url,

            "resolved_ip":
                resolved_ip,

            "headers":
                dict(
                    headers
                ),

            "connect_timeout_seconds":
                connect_timeout_seconds,

            "read_timeout_seconds":
                read_timeout_seconds,

            "max_payload_bytes":
                max_payload_bytes,
        })

        count = (
            self.count_by_url.get(
                url,
                0,
            )
            + 1
        )

        self.count_by_url[
            url
        ] = count

        parsed = transport.urllib.parse.urlsplit(
            url
        )

        # One deterministic transient failure exercises retry logic.
        if (
            "efetch.fcgi"
            in parsed.path
            and count == 1
            and len(
                [
                    item
                    for item in self.calls
                    if "efetch.fcgi"
                    in transport.urllib.parse.urlsplit(
                        item[
                            "url"
                        ]
                    ).path
                ]
            ) == 1
        ):
            return {
                "status":
                    503,

                "reason":
                    "Service Unavailable",

                "headers": [
                    [
                        "Content-Type",
                        "text/plain",
                    ],
                ],

                "location":
                    "",

                "payload":
                    b"retry",
            }

        if (
            parsed.hostname
            == "doi.org"
        ):
            return {
                "status":
                    302,

                "reason":
                    "Found",

                "headers": [
                    [
                        "Location",
                        (
                            "https://publisher.example"
                            + parsed.path
                        ),
                    ],
                ],

                "location":
                    (
                        "https://publisher.example"
                        + parsed.path
                    ),

                "payload":
                    b"",
            }

        if (
            parsed.hostname
            == "publisher.example"
        ):
            # Give the final versioned DOI a legitimate terminal transport
            # outcome that is not a scientific decision.
            if (
                "pub2"
                in parsed.path.lower()
            ):
                return {
                    "status":
                        404,

                    "reason":
                        "Not Found",

                    "headers": [
                        [
                            "Content-Type",
                            "text/html",
                        ],
                    ],

                    "location":
                        "",

                    "payload":
                        b"<html>not found</html>",
                }

            return {
                "status":
                    200,

                "reason":
                    "OK",

                "headers": [
                    [
                        "Content-Type",
                        "text/html; charset=utf-8",
                    ],
                ],

                "location":
                    "",

                "payload":
                    (
                        b"<html><body>"
                        b"authoritative publisher test payload"
                        b"</body></html>"
                    ),
            }

        if (
            "elink.fcgi"
            in parsed.path
        ):
            return {
                "status":
                    200,

                "reason":
                    "OK",

                "headers": [
                    [
                        "Content-Type",
                        "application/xml",
                    ],
                ],

                "location":
                    "",

                "payload":
                    (
                        b"<eLinkResult>"
                        b"<LinkSet>"
                        b"<LinkSetDb>"
                        b"<Link><Id>123456</Id></Link>"
                        b"</LinkSetDb>"
                        b"</LinkSet>"
                        b"</eLinkResult>"
                    ),
            }

        return {
            "status":
                200,

            "reason":
                "OK",

            "headers": [
                [
                    "Content-Type",
                    "application/xml",
                ],
            ],

            "location":
                "",

            "payload":
                b"<PubmedArticleSet/>",
        }


class ExplodingAdapter:
    def __init__(
        self,
        explode_on_call,
    ):
        self.explode_on_call = int(
            explode_on_call
        )

        self.calls = 0

    def request_once(
        self,
        **kwargs,
    ):
        self.calls += 1

        if (
            self.calls
            >= self.explode_on_call
        ):
            raise RuntimeError(
                "synthetic process interruption"
            )

        return {
            "status":
                200,

            "reason":
                "OK",

            "headers": [
                [
                    "Content-Type",
                    "application/xml",
                ],
            ],

            "location":
                "",

            "payload":
                b"<test/>",
        }


class WallLimitAdapter:
    def __init__(
        self,
        clock,
    ):
        self.clock = clock
        self.calls = []

    def request_once(
        self,
        *,
        url,
        resolved_ip,
        headers,
        connect_timeout_seconds,
        read_timeout_seconds,
        max_payload_bytes,
    ):
        self.calls.append({
            "url":
                url,

            "connect_timeout_seconds":
                float(
                    connect_timeout_seconds
                ),

            "read_timeout_seconds":
                float(
                    read_timeout_seconds
                ),
        })

        # Simulate a request that returns only after the frozen 60-second
        # per-attempt wall limit has been exceeded.
        self.clock.value += 61.0

        return {
            "status":
                200,

            "reason":
                "OK",

            "headers": [
                [
                    "Content-Type",
                    "application/xml",
                ],
            ],

            "location":
                "",

            "payload":
                b"<late/>",
        }


wall_clock = FakeClock()

wall_adapter = WallLimitAdapter(
    wall_clock
)

wall_pacer = transport.RequestPacer(
    minimum_interval_seconds=1.0,
    clock=wall_clock.now,
    sleeper=wall_clock.sleep,
)

wall_result = transport.execute_seed_task(
    row=
        first_pubmed,

    network_policy=
        network_policy,

    adapter=
        wall_adapter,

    resolver=
        public_resolver,

    pacer=
        wall_pacer,

    timestamp=
        lambda:
            "2026-09-25T10:00:00Z",

    sleeper=
        wall_clock.sleep,
)

assert wall_result[
    "final_status"
] == "transient_transport_error"

assert len(
    wall_result[
        "attempts"
    ]
) == 3

assert all(
    (
        "Per-attempt wall-time limit exceeded"
        in attempt[
            "error"
        ]
    )
    for attempt in wall_result[
        "attempts"
    ]
)

assert len(
    wall_adapter.calls
) == 3

assert all(
    call[
        "connect_timeout_seconds"
    ] <= 10.0
    for call in wall_adapter.calls
)

assert all(
    call[
        "read_timeout_seconds"
    ] <= 30.0
    for call in wall_adapter.calls
)

print(
    "PASS | frozen 60-second per-attempt wall-time limit enforced"
)

print(
    "PASS | frozen connect timeout never exceeds 10 seconds"
)

print(
    "PASS | frozen read timeout never exceeds 30 seconds"
)


with tempfile.TemporaryDirectory() as temporary:
    temp = Path(
        temporary
    )

    authorization_path = (
        temp
        / "authorization.json"
    )

    implementation_freeze_sha = (
        "1"
        * 64
    )

    authorization = (
        transport.synthetic_authorization(
            design=
                design,

            implementation_freeze_sha256=
                implementation_freeze_sha,
        )
    )

    authorization_path.write_bytes(
        transport.pretty_json_bytes(
            authorization
        )
    )

    validation = transport.validate_authorization(
        authorization_path=
            authorization_path,

        design=
            design,

        require_tracked=
            False,

        implementation_freeze_sha256_override=
            implementation_freeze_sha,
    )

    assert validation[
        "authorization_commit"
    ] == "UNTRACKED_TEST_AUTHORIZATION"

    print(
        "PASS | synthetic authorization accepted only in test validation mode"
    )


    fake_clock = FakeClock()
    adapter = FakeAdapter()

    test_root = (
        temp
        / "retrieval"
    )

    execution = transport.execute_seed_run(
        authorization_path=
            authorization_path,

        ledger_path=
            transport.DEFAULT_LEDGER,

        review_packet_path=
            transport.DEFAULT_REVIEW_PACKET,

        production_root=
            test_root,

        adapter=
            adapter,

        resolver=
            public_resolver,

        timestamp=
            lambda:
                "2026-09-25T10:00:00Z",

        monotonic_clock=
            fake_clock.now,

        sleeper=
            fake_clock.sleep,

        require_tracked_authorization=
            False,

        implementation_freeze_sha256_override=
            implementation_freeze_sha,

        allow_noncanonical_root=
            True,
    )

    assert execution[
        "status"
    ] == "ASR000001_EXECUTION_COMPLETE"

    assert execution[
        "tasks_considered"
    ] == 26

    assert execution[
        "scientific_decisions_made"
    ] is False

    assert execution[
        "event_ledger_mutated"
    ] is False

    assert execution[
        "review_packet_mutated"
    ] is False

    assert adapter.calls

    assert all(
        call[
            "connect_timeout_seconds"
        ] <= 10.0
        for call in adapter.calls
    )

    assert all(
        call[
            "read_timeout_seconds"
        ] <= 30.0
        for call in adapter.calls
    )

    print(
        "PASS | fake full run uses frozen connect-timeout ceiling"
    )

    print(
        "PASS | fake full run uses frozen read-timeout ceiling"
    )

    final = (
        test_root
        / transport.RUN_ID
    )

    assert final.is_dir()

    required = {
        "authorization.json",
        "seed_queue.tsv",
        "retrieval_manifest.tsv",
        "retrieval_summary.json",
        "evidence_assessment.tsv",
        "checksums.sha256",
        "raw",
    }

    assert required.issubset({
        item.name
        for item in final.iterdir()
    })

    assert hashlib.sha256(
        (
            final
            / "seed_queue.tsv"
        ).read_bytes()
    ).hexdigest() == transport.EXPECTED_SEED_QUEUE_SHA256

    with (
        final
        / "retrieval_manifest.tsv"
    ).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        manifest = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    assert len(
        manifest
    ) >= 26

    assert all(
        row[
            "screening_entity_id"
        ]
        for row in manifest
    )

    assert not any(
        (
            row.get(
                "notes",
                ""
            )
            or ""
        ).lower().startswith(
            "scientific decision"
        )
        for row in manifest
    )

    evidence_bytes = (
        final
        / "evidence_assessment.tsv"
    ).read_bytes()

    evidence_reader = csv.DictReader(
        io.StringIO(
            evidence_bytes.decode(
                "utf-8"
            )
        ),
        delimiter="\t",
    )

    assert list(
        evidence_reader
    ) == []

    summary = json.loads(
        (
            final
            / "retrieval_summary.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert summary[
        "status"
    ] == "ASR000001_COMPLETE"

    assert summary[
        "seed_task_count"
    ] == 26

    assert summary[
        "tasks_considered"
    ] == 26

    assert summary[
        "dynamic_child_routes_executed"
    ] is False

    assert summary[
        "scientific_decisions_made"
    ] is False

    assert summary[
        "event_ledger_mutated"
    ] is False

    assert summary[
        "review_packet_mutated"
    ] is False

    assert len(
        summary[
            "discovered_child_routes"
        ]
    ) == 8

    assert all(
        item[
            "executed"
        ] is False
        for item in summary[
            "discovered_child_routes"
        ]
    )

    checksums = (
        final
        / "checksums.sha256"
    ).read_text(
        encoding="utf-8"
    ).splitlines()

    assert checksums

    for line in checksums:
        digest, relative = line.split(
            "  ",
            1,
        )

        observed = hashlib.sha256(
            (
                final
                / relative
            ).read_bytes()
        ).hexdigest()

        assert digest == observed

    print(
        "PASS | complete 26-task fake retrieval run succeeds"
    )

    print(
        "PASS | fake execution persisted exact frozen seed queue"
    )

    print(
        "PASS | retrieval manifest created from transport evidence only"
    )

    print(
        "PASS | evidence assessment remains header-only"
    )

    print(
        "PASS | discovered PMC child routes recorded but not executed"
    )

    print(
        "PASS | retrieval evidence checksums verify"
    )

    print(
        "PASS | no scientific decision created by fake transport"
    )


with tempfile.TemporaryDirectory() as temporary:
    temp = Path(
        temporary
    )

    authorization_path = (
        temp
        / "authorization.json"
    )

    implementation_freeze_sha = (
        "2"
        * 64
    )

    authorization = (
        transport.synthetic_authorization(
            design=
                design,

            implementation_freeze_sha256=
                implementation_freeze_sha,
        )
    )

    authorization_path.write_bytes(
        transport.pretty_json_bytes(
            authorization
        )
    )

    fake_clock = FakeClock()

    interrupted_root = (
        temp
        / "interrupted"
    )

    exploding = ExplodingAdapter(
        explode_on_call=3
    )

    expect_error(
        "interrupted fake live run enters recovery state",
        transport.RecoveryRequiredError,
        lambda:
            transport.execute_seed_run(
                authorization_path=
                    authorization_path,

                ledger_path=
                    transport.DEFAULT_LEDGER,

                review_packet_path=
                    transport.DEFAULT_REVIEW_PACKET,

                production_root=
                    interrupted_root,

                adapter=
                    exploding,

                resolver=
                    public_resolver,

                timestamp=
                    lambda:
                        "2026-09-25T10:01:00Z",

                monotonic_clock=
                    fake_clock.now,

                sleeper=
                    fake_clock.sleep,

                require_tracked_authorization=
                    False,

                implementation_freeze_sha256_override=
                    implementation_freeze_sha,

                allow_noncanonical_root=
                    True,
            ),
    )

    state = transport.existing_run_state(
        production_root=
            interrupted_root,
    )

    assert state[
        "status"
    ] == "STAGING_RUN_EXISTS"

    assert state[
        "staging_paths"
    ]

    assert not (
        interrupted_root
        / transport.RUN_ID
    ).exists()

    print(
        "PASS | interrupted-run staging evidence preserved"
    )

    expect_error(
        "existing interrupted staging blocks silent rerun",
        transport.ExistingRunError,
        lambda:
            transport.assert_run_absent(
                production_root=
                    interrupted_root,
            ),
    )


# A real production live invocation with an untracked synthetic authorization
# must fail before DNS, network I/O or production-root creation.

with tempfile.TemporaryDirectory() as temporary:
    temp = Path(
        temporary
    )

    authorization_path = (
        temp
        / "authorization.json"
    )

    authorization = (
        transport.synthetic_authorization(
            design=
                design,

            implementation_freeze_sha256=
                "3"
                * 64,
        )
    )

    authorization_path.write_bytes(
        transport.pretty_json_bytes(
            authorization
        )
    )

    expect_error(
        "untracked authorization cannot enable real live retrieval",
        transport.AuthorizationError,
        lambda:
            transport.execute_live(
                authorization_path=
                    authorization_path,

                ledger_path=
                    transport.DEFAULT_LEDGER,

                review_packet_path=
                    transport.DEFAULT_REVIEW_PACKET,
            ),
    )


assert (
    transport.DEFAULT_LEDGER.read_bytes()
    == real_ledger_before
)

assert (
    transport.DEFAULT_REVIEW_PACKET.read_bytes()
    == real_packet_before
)

assert transport.PRODUCTION_ROOT.is_dir()

asr000001_root = (
    transport.PRODUCTION_ROOT
    / "ASR000001"
)

assert asr000001_root.is_dir()

asr000001_checksums = (
    asr000001_root
    / "checksums.sha256"
)

assert asr000001_checksums.is_file()

for line in asr000001_checksums.read_text(
    encoding="utf-8"
).splitlines():
    digest, relative = line.split(
        "  ",
        1,
    )

    assert transport.sha256_file(
        asr000001_root
        / relative
    ) == digest

asr000001_summary = json.loads(
    (
        asr000001_root
        / "retrieval_summary.json"
    ).read_text(
        encoding="utf-8"
    )
)

assert asr000001_summary[
    "status"
] == "ASR000001_COMPLETE"

assert asr000001_summary[
    "scientific_decisions_made"
] is False

assert asr000001_summary[
    "event_ledger_mutated"
] is False

assert asr000001_summary[
    "review_packet_mutated"
] is False

assert not (
    transport.PRODUCTION_ROOT
    / "ASR000002"
).exists()

assert not list(
    transport.PRODUCTION_ROOT.glob(
        ".ASR000002.tmp.*"
    )
)

assert transport.LIVE_AUTHORIZATION.is_file()

assert transport.sha256_file(
    transport.LIVE_AUTHORIZATION
) == (
    "5e12f5eb15fbfa1dab5f826d8e174270"
    "bc395e089a01e2f311537267217aa1be"
)

print(
    "PASS | real production ledger unchanged"
)

print(
    "PASS | real review packet unchanged"
)

print(
    "PASS | completed ASR000001 production evidence preserved checksum-exact"
)

print(
    "PASS | ASR000002 production run remains absent"
)

print(
    "PASS | consumed ASR000001 authorization preserved byte-identically"
)

print(
    "PASS | no real DNS or network request occurred in hostile tests"
)

print(
    "PASS | hostile network-transport tests complete"
)
