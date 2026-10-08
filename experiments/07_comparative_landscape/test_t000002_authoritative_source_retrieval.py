#!/usr/bin/env python3

from pathlib import Path
import copy
import hashlib
import importlib.util
import io
import csv
import sys


HERE = Path(__file__).resolve().parent

MODULE_PATH = (
    HERE
    / "t000002_authoritative_source_retrieval.py"
)

spec = importlib.util.spec_from_file_location(
    "t000002_authoritative_source_retrieval_tests",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

runner = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = runner

spec.loader.exec_module(
    runner
)


def expect_error(
    label,
    fn,
):
    try:
        fn()

    except runner.RetrievalImplementationError:
        print(
            "PASS |",
            label,
        )

        return

    raise AssertionError(
        "Expected fail-closed error: "
        + label
    )


design = runner.load_design()

state = runner.validate_current_state(
    design=
        design,

    ledger_path=
        runner.DEFAULT_LEDGER,

    review_packet_path=
        runner.DEFAULT_REVIEW_PACKET,
)

assert len(
    state[
        "targets"
    ]
) == 10

assert runner.canonical_sha(
    design[
        "target_scope"
    ][
        "targets"
    ]
) == runner.EXPECTED_TARGET_IDENTITY_SHA256

print(
    "PASS | exact ten-record authoritative-source target validated"
)

print(
    "PASS | target identity SHA reproduced"
)


real_ledger_before = (
    runner.DEFAULT_LEDGER.read_bytes()
)

real_packet_before = (
    runner.DEFAULT_REVIEW_PACKET.read_bytes()
)

assert hashlib.sha256(
    real_ledger_before
).hexdigest() == runner.EXPECTED_LEDGER_SHA256

assert hashlib.sha256(
    real_packet_before
).hexdigest() == runner.EXPECTED_REVIEW_PACKET_SHA256


queue1 = runner.build_seed_queue(
    design=
        design,
)

queue2 = runner.build_seed_queue(
    design=
        design,
)

assert queue1 == queue2

assert len(
    queue1
) == 26

assert [
    row[
        "queue_id"
    ]
    for row in queue1
] == [
    f"RQ{value:06d}"
    for value in range(
        1,
        27,
    )
]

assert {
    int(
        row[
            "position_in_batch"
        ]
    )
    for row in queue1
} == set(
    range(
        2,
        12,
    )
)

route_counts = {
    code:
        sum(
            row[
                "route_code"
            ] == code
            for row in queue1
        )
    for code in sorted(
        runner.KNOWN_ROUTE_CODES
    )
}

assert route_counts == {
    "doi_publisher_article":
        10,

    "pubmed_pmc_link_discovery":
        8,

    "pubmed_record":
        8,
}

assert all(
    row[
        "network_required"
    ] == "true"
    for row in queue1
)

assert all(
    row[
        "scientific_decision_allowed"
    ] == "false"
    for row in queue1
)

print(
    "PASS | deterministic seed retrieval queue built"
)

print(
    "PASS | exact seed task count = 26"
)

print(
    "PASS | PubMed record routes = 8"
)

print(
    "PASS | PubMed-to-PMC discovery routes = 8"
)

print(
    "PASS | DOI publisher routes = 10"
)

print(
    "PASS | every seed route requires future network authority"
)

print(
    "PASS | no seed route permits scientific decisions"
)


payload1 = runner.queue_bytes(
    design=
        design,
)

payload2 = runner.queue_bytes(
    design=
        design,
)

assert payload1 == payload2

queue_sha = hashlib.sha256(
    payload1
).hexdigest()

print(
    "PASS | seed queue is byte-deterministic"
)

print(
    "INFO | deterministic seed queue SHA256 =",
    queue_sha,
)


# Confirm TSV round-trip.
reader = csv.DictReader(
    io.StringIO(
        payload1.decode(
            "utf-8"
        )
    ),
    delimiter="\t",
)

roundtrip_rows = list(
    reader
)

assert list(
    reader.fieldnames
    or []
) == runner.QUEUE_FIELDS

assert roundtrip_rows == queue1

print(
    "PASS | seed queue TSV round-trip exact"
)


# Positions 10 and 11 intentionally have DOI route only.
for position in (
    10,
    11,
):
    rows = [
        row
        for row in queue1
        if int(
            row[
                "position_in_batch"
            ]
        ) == position
    ]

    assert len(
        rows
    ) == 1

    assert rows[
        0
    ][
        "route_code"
    ] == "doi_publisher_article"

print(
    "PASS | positions 10/11 receive no inferred duplicate or synthetic PubMed route"
)


# Missing task.
bad = copy.deepcopy(
    queue1[
        :-1
    ]
)

expect_error(
    "missing retrieval task rejected",
    lambda:
        runner.validate_seed_queue(
            rows=
                bad,

            design=
                design,
        ),
)


# Out-of-scope position.
bad = copy.deepcopy(
    queue1
)

bad[
    0
][
    "position_in_batch"
] = "12"

expect_error(
    "out-of-scope retrieval position rejected",
    lambda:
        runner.validate_seed_queue(
            rows=
                bad,

            design=
                design,
        ),
)


# Scientific-decision authority.
bad = copy.deepcopy(
    queue1
)

bad[
    0
][
    "scientific_decision_allowed"
] = "true"

expect_error(
    "retrieval queue cannot authorize scientific decision",
    lambda:
        runner.validate_seed_queue(
            rows=
                bad,

            design=
                design,
        ),
)


# Unknown route.
bad = copy.deepcopy(
    queue1
)

bad[
    0
][
    "route_code"
] = "invented_route"

expect_error(
    "unknown retrieval route rejected",
    lambda:
        runner.validate_seed_queue(
            rows=
                bad,

            design=
                design,
        ),
)


# Event-ID tampering.
bad = copy.deepcopy(
    queue1
)

bad[
    0
][
    "current_event_id"
] = "E999999999"

expect_error(
    "current escalation event tamper rejected",
    lambda:
        runner.validate_seed_queue(
            rows=
                bad,

            design=
                design,
        ),
)


# Target-identity tampering.
bad = copy.deepcopy(
    queue1
)

bad[
    0
][
    "screening_entity_id"
] = "tampered"

expect_error(
    "target entity tamper rejected",
    lambda:
        runner.validate_seed_queue(
            rows=
                bad,

            design=
                design,
        ),
)


# Baseline-row identity tampering.
bad = copy.deepcopy(
    queue1
)

bad[
    0
][
    "baseline_row_sha256"
] = "0" * 64

expect_error(
    "baseline-row identity tamper rejected",
    lambda:
        runner.validate_seed_queue(
            rows=
                bad,

            design=
                design,
        ),
)


# Live transport deliberately unavailable.
expect_error(
    "live network execution hard-refused",
    runner.execute_network,
)


status = runner.describe_status(
    design=
        design,

    ledger_path=
        runner.DEFAULT_LEDGER,

    review_packet_path=
        runner.DEFAULT_REVIEW_PACKET,
)

assert status[
    "status"
] == (
    "T000002_AUTHORITATIVE_SOURCE_RETRIEVAL_"
    "IMPLEMENTATION_READY_PRE_NETWORK_AUTHORIZATION"
)

assert status[
    "target_count"
] == 10

assert status[
    "seed_queue_task_count"
] == 26

assert status[
    "seed_queue_sha256"
] == queue_sha

assert status[
    "network_transport_implemented"
] is False

assert status[
    "network_execution_authorized"
] is False

assert status[
    "scientific_decisions_allowed"
] is False

assert status[
    "production_mutation_allowed"
] is False

assert status[
    "production_root_exists"
] is False

assert status[
    "mutation_performed"
] is False

print(
    "PASS | read-only implementation status exact"
)

print(
    "PASS | network transport remains unimplemented"
)

print(
    "PASS | production mutation remains prohibited"
)


assert (
    runner.DEFAULT_LEDGER.read_bytes()
    == real_ledger_before
)

assert (
    runner.DEFAULT_REVIEW_PACKET.read_bytes()
    == real_packet_before
)

assert not runner.PRODUCTION_ROOT.exists()

print(
    "PASS | real production ledger unchanged"
)

print(
    "PASS | real review packet unchanged"
)

print(
    "PASS | production retrieval root remains absent"
)

print(
    "PASS | hostile authoritative-source retrieval tests complete"
)
