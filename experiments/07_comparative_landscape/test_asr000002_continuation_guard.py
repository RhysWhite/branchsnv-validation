#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import json
import tempfile
import sys


HERE = Path(__file__).resolve().parent

GUARD_PATH = (
    HERE
    / "asr000002_continuation_guard.py"
)

name = "asr000002_guard_tests"

spec = importlib.util.spec_from_file_location(
    name,
    GUARD_PATH,
)

assert spec is not None
assert spec.loader is not None

guard = importlib.util.module_from_spec(
    spec
)

sys.modules[name] = guard
spec.loader.exec_module(
    guard
)

transport = guard.load_transport()

assert guard.load_transport() is transport

assert (
    guard.load_transport().NetworkTransientError
    is transport.NetworkTransientError
)

print(
    "PASS | guard reuses one frozen transport module instance"
)

print(
    "PASS | transient exception class identity stable across guard and adapter"
)


def public_resolver(
    hostname,
):
    return [
        "93.184.216.34",
        "93.184.216.35",
    ]


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def now(self):
        return self.value

    def sleep(
        self,
        seconds,
    ):
        self.value += float(
            seconds
        )


class FailoverAdapter:
    def __init__(self):
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
        self.calls.append(
            (
                url,
                resolved_ip,
            )
        )

        if (
            resolved_ip
            == "93.184.216.34"
        ):
            raise transport.NetworkTransientError(
                "synthetic first-address route failure"
            )

        if "elink.fcgi" in url:
            payload = (
                b"<eLinkResult/>"
            )

        else:
            payload = (
                b"<PubmedArticleSet/>"
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
                payload,
        }


guard.validate_asr000001()

queue = guard.continuation_queue_context(
    ledger_path=
        guard.DEFAULT_LEDGER,

    review_packet_path=
        guard.DEFAULT_REVIEW_PACKET,
)

assert len(
    queue[
        "rows"
    ]
) == 16

assert guard.sha256_bytes(
    queue[
        "payload"
    ]
) == guard.EXPECTED_CONTINUATION_QUEUE_SHA256

assert [
    row[
        "queue_id"
    ]
    for row in queue[
        "rows"
    ]
] == guard.EXPECTED_QUEUE_IDS

assert all(
    row[
        "route_code"
    ]
    in {
        "pubmed_record",
        "pubmed_pmc_link_discovery",
    }
    for row in queue[
        "rows"
    ]
)

print(
    "PASS | exact 16-task ASR000002 continuation queue reproduced"
)

print(
    "PASS | no DOI task present in continuation"
)


policy = transport.load_transport_design()[
    "network_policy"
]

clock = FakeClock()

adapter = FailoverAdapter()

pacer = transport.RequestPacer(
    minimum_interval_seconds=1.0,
    clock=clock.now,
    sleeper=clock.sleep,
)

single = transport.execute_seed_task(
    row=
        queue[
            "rows"
        ][
            0
        ],

    network_policy=
        policy,

    adapter=
        adapter,

    resolver=
        public_resolver,

    pacer=
        pacer,

    timestamp=
        lambda:
            "2026-09-25T11:30:00Z",

    sleeper=
        clock.sleep,
)

assert single[
    "final_status"
] == "retrieved"

assert len(
    single[
        "attempts"
    ]
) == 2

assert single[
    "attempts"
][
    0
][
    "resolved_addresses_attempted"
] == [
    "93.184.216.34"
]

assert single[
    "attempts"
][
    1
][
    "resolved_addresses_attempted"
] == [
    "93.184.216.35"
]

print(
    "PASS | retry fails over from first validated public address to second"
)

print(
    "PASS | attempted resolved address retained in evidence"
)


with tempfile.TemporaryDirectory() as temporary:
    root = Path(
        temporary
    )

    auth_path = (
        root
        / "authorization.json"
    )

    fake_guard_sha = (
        "4"
        * 64
    )

    authorization = guard.synthetic_authorization(
        parent_commit=
            "0"
            * 40,

        guard_freeze_sha256=
            fake_guard_sha,
    )

    auth_path.write_bytes(
        guard.pretty_json_bytes(
            authorization
        )
    )

    validated = guard.validate_authorization(
        authorization_path=
            auth_path,

        require_tracked=
            False,

        guard_freeze_sha256_override=
            fake_guard_sha,
    )

    assert validated[
        "authorization_commit"
    ] == "UNTRACKED_TEST_AUTHORIZATION"

    test_root = (
        root
        / "production"
    )

    fake_clock = FakeClock()

    fake_adapter = FailoverAdapter()

    result = guard.execute_continuation(
        authorization_path=
            auth_path,

        ledger_path=
            guard.DEFAULT_LEDGER,

        review_packet_path=
            guard.DEFAULT_REVIEW_PACKET,

        production_root=
            test_root,

        adapter=
            fake_adapter,

        resolver=
            public_resolver,

        timestamp=
            lambda:
                "2026-09-25T11:31:00Z",

        monotonic_clock=
            fake_clock.now,

        sleeper=
            fake_clock.sleep,

        require_tracked_authorization=
            False,

        guard_freeze_sha256_override=
            fake_guard_sha,

        allow_noncanonical_root=
            True,
    )

    assert result[
        "status"
    ] == "ASR000002_EXECUTION_COMPLETE"

    assert result[
        "tasks_considered"
    ] == 16

    assert result[
        "transport_attempt_count"
    ] == 32

    assert result[
        "final_transport_status_counts"
    ] == {
        "retrieved":
            16,
    }

    assert result[
        "scientific_decisions_made"
    ] is False

    final = (
        test_root
        / "ASR000002"
    )

    assert final.is_dir()

    summary = json.loads(
        (
            final
            / "retrieval_summary.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert summary[
        "tasks_considered"
    ] == 16

    assert summary[
        "transport_attempt_count"
    ] == 32

    assert summary[
        "final_transport_status_counts"
    ] == {
        "retrieved":
            16,
    }

    assert summary[
        "scientific_decisions_made"
    ] is False

    assert summary[
        "event_ledger_mutated"
    ] is False

    assert summary[
        "review_packet_mutated"
    ] is False

    print(
        "PASS | complete fake ASR000002 continuation succeeds"
    )

    print(
        "PASS | 16 tasks complete after deterministic address failover"
    )

    print(
        "PASS | no scientific decision created"
    )


assert not guard.ASR000002_ROOT.exists()
assert not guard.LIVE_AUTHORIZATION.exists()

print(
    "PASS | canonical ASR000002 production run remains absent"
)

print(
    "PASS | canonical ASR000002 authorization remains absent"
)

print(
    "PASS | no real DNS/network request occurred"
)

print(
    "PASS | hostile ASR000002 continuation tests complete"
)
