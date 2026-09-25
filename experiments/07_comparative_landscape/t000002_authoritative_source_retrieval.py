#!/usr/bin/env python3

"""
Experiment 07 T000002 authoritative-source retrieval queue and pre-network
runner.

This implementation deliberately contains no network transport capability.

It:
- validates the frozen T000002 authoritative-source design;
- validates the exact current post-T000002 production state;
- reconstructs exactly the ten unresolved escalation targets;
- creates a deterministic seed retrieval queue;
- provides read-only status and queue serialization;
- hard-refuses live network execution.

The seed queue contains only source routes derivable from already-frozen
identifiers. Source links discovered from retrieved publications, including
supplements, repositories and documentation, require a later separately
controlled queue expansion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import csv
import hashlib
import io
import json
import sys


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

RESULTS_ROOT = (
    REPO_ROOT
    / "results"
    / "07_comparative_landscape"
)

SCREENING_ROOT = (
    RESULTS_ROOT
    / "scientific_screening"
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

PRODUCTION_ROOT = (
    RESULTS_ROOT
    / "t000002_authoritative_source_retrieval"
)

DEFAULT_QUEUE = (
    SCREENING_ROOT
    / "baseline_screening_queue.tsv"
)

DEFAULT_LEDGER = (
    EXECUTION_ROOT
    / "event_ledger.tsv"
)

DEFAULT_REVIEW_PACKET = (
    REVIEW_ROOT
    / "review_packet.tsv"
)

DESIGN = (
    HERE
    / "t000002_authoritative_source_retrieval_and_escalation_resolution_design.json"
)

DESIGN_SUMS = (
    HERE
    / "t000002_authoritative_source_retrieval_and_escalation_resolution_design.sha256"
)


EXPECTED_DESIGN_PARENT_COMMIT = (
    "8cfefe12c6c300c2f9b2ad70683274f5d2976a72"
)

EXPECTED_DESIGN_COMMIT = (
    "bae2a0a6854df50a05163f7ffc8121379579fe3e"
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

EXPECTED_TARGET_IDENTITY_SHA256 = (
    "5970e1ec739b5b01c546e526c402d2f3"
    "a6e06e8f43aef0bfcd375e692bc2ab5e"
)

EXPECTED_POSITIONS = list(
    range(
        2,
        12,
    )
)

EXPECTED_EVENT_IDS = [
    f"E{value:09d}"
    for value in range(
        2,
        12,
    )
]

EXPECTED_TARGET_COUNT = 10

QUEUE_FIELDS = [
    "queue_id",
    "position_in_batch",
    "current_event_id",
    "screening_entity_id",
    "baseline_row_sha256",
    "route_rank",
    "task_kind",
    "route_code",
    "expected_source_class",
    "authority_expectation",
    "identifier_type",
    "identifier_value",
    "locator",
    "network_required",
    "scientific_decision_allowed",
    "queue_status",
    "notes",
]

RETRIEVAL_MANIFEST_FIELDS = [
    "position_in_batch",
    "current_event_id",
    "screening_entity_id",
    "source_id",
    "source_class",
    "authority_class",
    "locator",
    "retrieval_route",
    "retrieved_at_utc",
    "retrieval_status",
    "http_status",
    "content_type",
    "payload_sha256",
    "payload_bytes",
    "storage_mode",
    "local_path",
    "license_or_access_note",
    "notes",
]

EVIDENCE_ASSESSMENT_FIELDS = [
    "position_in_batch",
    "current_event_id",
    "screening_entity_id",
    "source_id",
    "evidence_question",
    "evidence_present",
    "evidence_locator",
    "evidence_excerpt_or_summary",
    "human_reviewer",
    "assessment_status",
    "notes",
]

KNOWN_ROUTE_CODES = {
    "pubmed_record",
    "pubmed_pmc_link_discovery",
    "doi_publisher_article",
}

ROUTE_SPECS = {
    "pubmed_record": {
        "route_rank":
            1,

        "task_kind":
            "authoritative_source",

        "expected_source_class":
            "primary_publication_abstract",

        "authority_expectation":
            "terminal_capable_if_substantive",

        "identifier_type":
            "pmid",
    },

    "pubmed_pmc_link_discovery": {
        "route_rank":
            2,

        "task_kind":
            "source_discovery",

        "expected_source_class":
            "primary_publication_full_text",

        "authority_expectation":
            "terminal_capable_if_discovered_and_substantive",

        "identifier_type":
            "pmid",
    },

    "doi_publisher_article": {
        "route_rank":
            3,

        "task_kind":
            "authoritative_source",

        "expected_source_class":
            "primary_publication_full_text",

        "authority_expectation":
            "terminal_capable_if_substantive",

        "identifier_type":
            "doi",
    },
}


class RetrievalImplementationError(
    RuntimeError
):
    pass


class NetworkExecutionNotAuthorizedError(
    RetrievalImplementationError
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


def read_tsv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        return (
            list(
                reader.fieldnames
                or []
            ),
            list(reader),
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


def load_design() -> dict:
    value = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        value[
            "status"
        ]
        != "FROZEN_PRE_IMPLEMENTATION"
    ):
        raise RetrievalImplementationError(
            "Authoritative-source design status changed"
        )

    if (
        value[
            "design_id"
        ]
        != (
            "T000002_AUTHORITATIVE_SOURCE_RETRIEVAL_"
            "AND_ESCALATION_RESOLUTION"
        )
    ):
        raise RetrievalImplementationError(
            "Authoritative-source design identity changed"
        )

    if (
        value[
            "parent_t000002_completion_commit"
        ]
        != EXPECTED_DESIGN_PARENT_COMMIT
    ):
        raise RetrievalImplementationError(
            "Authoritative-source design parent changed"
        )

    target = value[
        "target_scope"
    ]

    if (
        target[
            "positions"
        ]
        != EXPECTED_POSITIONS
    ):
        raise RetrievalImplementationError(
            "Target positions changed"
        )

    if (
        target[
            "current_event_ids"
        ]
        != EXPECTED_EVENT_IDS
    ):
        raise RetrievalImplementationError(
            "Current event IDs changed"
        )

    if (
        target[
            "entity_count"
        ]
        != EXPECTED_TARGET_COUNT
    ):
        raise RetrievalImplementationError(
            "Target count changed"
        )

    if (
        target[
            "canonical_target_identity_sha256"
        ]
        != EXPECTED_TARGET_IDENTITY_SHA256
    ):
        raise RetrievalImplementationError(
            "Target identity SHA changed"
        )

    if (
        canonical_sha(
            target[
                "targets"
            ]
        )
        != EXPECTED_TARGET_IDENTITY_SHA256
    ):
        raise RetrievalImplementationError(
            "Target identity rows no longer reproduce frozen SHA"
        )

    if (
        value[
            "live_network_retrieval_permitted_by_this_design"
        ]
        is not False
    ):
        raise RetrievalImplementationError(
            "Design unexpectedly grants network authority"
        )

    if (
        value[
            "scientific_decisions_permitted_by_this_design"
        ]
        is not False
    ):
        raise RetrievalImplementationError(
            "Design unexpectedly grants scientific-decision authority"
        )

    if (
        value[
            "production_mutation_permitted_by_this_design"
        ]
        is not False
    ):
        raise RetrievalImplementationError(
            "Design unexpectedly grants production mutation authority"
        )

    return value


def validate_current_state(
    *,
    design: dict,
    ledger_path: Path,
    review_packet_path: Path,
) -> dict:
    if (
        sha256_file(
            ledger_path
        )
        != EXPECTED_LEDGER_SHA256
    ):
        raise RetrievalImplementationError(
            "Production ledger differs from frozen T000002 state"
        )

    if (
        sha256_file(
            review_packet_path
        )
        != EXPECTED_REVIEW_PACKET_SHA256
    ):
        raise RetrievalImplementationError(
            "Review packet differs from frozen T000002 state"
        )

    if (
        review_packet_path.stat().st_size
        != EXPECTED_REVIEW_PACKET_BYTES
    ):
        raise RetrievalImplementationError(
            "Review packet byte count changed"
        )

    _, ledger = read_tsv(
        ledger_path
    )

    _, packet = read_tsv(
        review_packet_path
    )

    if len(
        ledger
    ) != 11:
        raise RetrievalImplementationError(
            "Expected exactly eleven production events"
        )

    if len(
        packet
    ) != 500:
        raise RetrievalImplementationError(
            "Expected 500-row B000001 review packet"
        )

    targets = design[
        "target_scope"
    ][
        "targets"
    ]

    if len(
        targets
    ) != EXPECTED_TARGET_COUNT:
        raise RetrievalImplementationError(
            "Frozen target row count changed"
        )

    for target in targets:
        position = target[
            "position_in_batch"
        ]

        event_id = target[
            "current_event_id"
        ]

        if position not in EXPECTED_POSITIONS:
            raise RetrievalImplementationError(
                "Unexpected target position"
            )

        event = ledger[
            position - 1
        ]

        review = packet[
            position - 1
        ]

        if (
            event[
                "event_id"
            ]
            != event_id
        ):
            raise RetrievalImplementationError(
                f"Current event mismatch at position {position}"
            )

        if (
            event[
                "event_type"
            ]
            != "source_escalation"
        ):
            raise RetrievalImplementationError(
                f"Position {position} is no longer source escalation"
            )

        if (
            event[
                "evidence_escalation_status"
            ]
            != "awaiting_source_escalation"
        ):
            raise RetrievalImplementationError(
                f"Position {position} escalation status changed"
            )

        if event[
            "record_decision"
        ]:
            raise RetrievalImplementationError(
                f"Position {position} unexpectedly has terminal decision"
            )

        if event[
            "candidate_method_flag"
        ]:
            raise RetrievalImplementationError(
                f"Position {position} unexpectedly has candidate-method decision"
            )

        if (
            event[
                "screening_entity_id"
            ]
            != target[
                "screening_entity_id"
            ]
        ):
            raise RetrievalImplementationError(
                f"Ledger target identity mismatch at position {position}"
            )

        if (
            review[
                "screening_entity_id"
            ]
            != target[
                "screening_entity_id"
            ]
        ):
            raise RetrievalImplementationError(
                f"Review target identity mismatch at position {position}"
            )

        if (
            review[
                "baseline_row_sha256"
            ]
            != target[
                "baseline_row_sha256"
            ]
        ):
            raise RetrievalImplementationError(
                f"Baseline-row identity mismatch at position {position}"
            )

    return {
        "ledger_rows":
            ledger,

        "review_rows":
            packet,

        "targets":
            targets,
    }


def make_queue_row(
    *,
    queue_id: str,
    target: dict,
    route_code: str,
    identifier_value: str,
    locator: str,
) -> dict[str, str]:
    spec = ROUTE_SPECS[
        route_code
    ]

    return {
        "queue_id":
            queue_id,

        "position_in_batch":
            str(
                target[
                    "position_in_batch"
                ]
            ),

        "current_event_id":
            target[
                "current_event_id"
            ],

        "screening_entity_id":
            target[
                "screening_entity_id"
            ],

        "baseline_row_sha256":
            target[
                "baseline_row_sha256"
            ],

        "route_rank":
            str(
                spec[
                    "route_rank"
                ]
            ),

        "task_kind":
            spec[
                "task_kind"
            ],

        "route_code":
            route_code,

        "expected_source_class":
            spec[
                "expected_source_class"
            ],

        "authority_expectation":
            spec[
                "authority_expectation"
            ],

        "identifier_type":
            spec[
                "identifier_type"
            ],

        "identifier_value":
            identifier_value,

        "locator":
            locator,

        "network_required":
            "true",

        "scientific_decision_allowed":
            "false",

        "queue_status":
            "planned_pre_network_authorization",

        "notes":
            (
                "Seed route derived only from frozen target identifiers; "
                "no scientific disposition encoded."
            ),
    }


def build_seed_queue(
    *,
    design: dict,
) -> list[dict[str, str]]:
    rows = []

    counter = 0

    for target in design[
        "target_scope"
    ][
        "targets"
    ]:
        pmid = (
            target.get(
                "pmid",
                ""
            )
            or ""
        ).strip()

        doi = (
            target.get(
                "doi",
                ""
            )
            or ""
        ).strip()

        if pmid:
            counter += 1

            rows.append(
                make_queue_row(
                    queue_id=
                        f"RQ{counter:06d}",

                    target=
                        target,

                    route_code=
                        "pubmed_record",

                    identifier_value=
                        pmid,

                    locator=
                        f"PMID:{pmid}",
                )
            )

            counter += 1

            rows.append(
                make_queue_row(
                    queue_id=
                        f"RQ{counter:06d}",

                    target=
                        target,

                    route_code=
                        "pubmed_pmc_link_discovery",

                    identifier_value=
                        pmid,

                    locator=
                        f"PMID:{pmid}",
                )
            )

        if doi:
            counter += 1

            rows.append(
                make_queue_row(
                    queue_id=
                        f"RQ{counter:06d}",

                    target=
                        target,

                    route_code=
                        "doi_publisher_article",

                    identifier_value=
                        doi,

                    locator=
                        f"DOI:{doi}",
                )
            )

        if (
            not pmid
            and not doi
        ):
            raise RetrievalImplementationError(
                "Frozen target has neither PMID nor DOI seed route"
            )

    validate_seed_queue(
        rows=
            rows,

        design=
            design,
    )

    return rows


def validate_seed_queue(
    *,
    rows: list[dict[str, str]],
    design: dict,
) -> None:
    if not rows:
        raise RetrievalImplementationError(
            "Seed retrieval queue is empty"
        )

    expected_ids = [
        f"RQ{value:06d}"
        for value in range(
            1,
            len(rows) + 1,
        )
    ]

    observed_ids = [
        row[
            "queue_id"
        ]
        for row in rows
    ]

    if (
        observed_ids
        != expected_ids
    ):
        raise RetrievalImplementationError(
            "Retrieval queue IDs are not canonical sequential order"
        )

    if len(
        set(
            observed_ids
        )
    ) != len(
        observed_ids
    ):
        raise RetrievalImplementationError(
            "Duplicate retrieval queue ID"
        )

    targets = {
        target[
            "position_in_batch"
        ]:
            target
        for target in design[
            "target_scope"
        ][
            "targets"
        ]
    }

    observed_positions = set()

    previous_key = None

    for row in rows:
        if set(
            row
        ) != set(
            QUEUE_FIELDS
        ):
            raise RetrievalImplementationError(
                "Retrieval queue schema mismatch"
            )

        position = int(
            row[
                "position_in_batch"
            ]
        )

        route_rank = int(
            row[
                "route_rank"
            ]
        )

        if (
            position
            not in EXPECTED_POSITIONS
        ):
            raise RetrievalImplementationError(
                "Retrieval queue contains out-of-scope position"
            )

        observed_positions.add(
            position
        )

        target = targets[
            position
        ]

        if (
            row[
                "current_event_id"
            ]
            != target[
                "current_event_id"
            ]
        ):
            raise RetrievalImplementationError(
                "Retrieval queue current-event mismatch"
            )

        if (
            row[
                "screening_entity_id"
            ]
            != target[
                "screening_entity_id"
            ]
        ):
            raise RetrievalImplementationError(
                "Retrieval queue entity mismatch"
            )

        if (
            row[
                "baseline_row_sha256"
            ]
            != target[
                "baseline_row_sha256"
            ]
        ):
            raise RetrievalImplementationError(
                "Retrieval queue baseline-row mismatch"
            )

        route_code = row[
            "route_code"
        ]

        if (
            route_code
            not in KNOWN_ROUTE_CODES
        ):
            raise RetrievalImplementationError(
                "Unknown retrieval route"
            )

        spec = ROUTE_SPECS[
            route_code
        ]

        if (
            route_rank
            != spec[
                "route_rank"
            ]
        ):
            raise RetrievalImplementationError(
                "Retrieval route rank mismatch"
            )

        if (
            row[
                "task_kind"
            ]
            != spec[
                "task_kind"
            ]
        ):
            raise RetrievalImplementationError(
                "Retrieval task kind mismatch"
            )

        if (
            row[
                "expected_source_class"
            ]
            != spec[
                "expected_source_class"
            ]
        ):
            raise RetrievalImplementationError(
                "Expected source class mismatch"
            )

        if (
            row[
                "authority_expectation"
            ]
            != spec[
                "authority_expectation"
            ]
        ):
            raise RetrievalImplementationError(
                "Authority expectation mismatch"
            )

        if (
            row[
                "identifier_type"
            ]
            != spec[
                "identifier_type"
            ]
        ):
            raise RetrievalImplementationError(
                "Identifier type mismatch"
            )

        expected_identifier = (
            target.get(
                spec[
                    "identifier_type"
                ],
                "",
            )
            or ""
        ).strip()

        if (
            row[
                "identifier_value"
            ]
            != expected_identifier
        ):
            raise RetrievalImplementationError(
                "Identifier value mismatch"
            )

        expected_prefix = (
            "PMID:"
            if spec[
                "identifier_type"
            ] == "pmid"
            else "DOI:"
        )

        if (
            row[
                "locator"
            ]
            != (
                expected_prefix
                + expected_identifier
            )
        ):
            raise RetrievalImplementationError(
                "Seed locator mismatch"
            )

        if (
            row[
                "network_required"
            ]
            != "true"
        ):
            raise RetrievalImplementationError(
                "Seed retrieval route must require network"
            )

        if (
            row[
                "scientific_decision_allowed"
            ]
            != "false"
        ):
            raise RetrievalImplementationError(
                "Retrieval queue cannot authorize scientific decisions"
            )

        if (
            row[
                "queue_status"
            ]
            != "planned_pre_network_authorization"
        ):
            raise RetrievalImplementationError(
                "Retrieval queue status mismatch"
            )

        ordering_key = (
            position,
            route_rank,
        )

        if (
            previous_key is not None
            and ordering_key < previous_key
        ):
            raise RetrievalImplementationError(
                "Retrieval queue is not in canonical target/route order"
            )

        previous_key = ordering_key

    if (
        observed_positions
        != set(
            EXPECTED_POSITIONS
        )
    ):
        raise RetrievalImplementationError(
            "Retrieval queue does not cover all ten targets"
        )

    counts = {
        code:
            sum(
                row[
                    "route_code"
                ] == code
                for row in rows
            )
        for code in sorted(
            KNOWN_ROUTE_CODES
        )
    }

    if counts != {
        "doi_publisher_article":
            10,

        "pubmed_pmc_link_discovery":
            8,

        "pubmed_record":
            8,
    }:
        raise RetrievalImplementationError(
            f"Unexpected seed-route distribution: {counts}"
        )

    if len(
        rows
    ) != 26:
        raise RetrievalImplementationError(
            "Seed retrieval queue must contain exactly 26 tasks"
        )


def queue_bytes(
    *,
    design: dict,
) -> bytes:
    rows = build_seed_queue(
        design=
            design,
    )

    return tsv_bytes(
        fields=
            QUEUE_FIELDS,

        rows=
            rows,
    )


def describe_status(
    *,
    design: dict,
    ledger_path: Path,
    review_packet_path: Path,
) -> dict:
    state = validate_current_state(
        design=
            design,

        ledger_path=
            ledger_path,

        review_packet_path=
            review_packet_path,
    )

    rows = build_seed_queue(
        design=
            design,
    )

    payload = tsv_bytes(
        fields=
            QUEUE_FIELDS,

        rows=
            rows,
    )

    route_counts = {
        code:
            sum(
                row[
                    "route_code"
                ] == code
                for row in rows
            )
        for code in sorted(
            KNOWN_ROUTE_CODES
        )
    }

    return {
        "status":
            (
                "T000002_AUTHORITATIVE_SOURCE_RETRIEVAL_"
                "IMPLEMENTATION_READY_PRE_NETWORK_AUTHORIZATION"
            ),

        "design_commit":
            EXPECTED_DESIGN_COMMIT,

        "target_count":
            len(
                state[
                    "targets"
                ]
            ),

        "target_positions":
            EXPECTED_POSITIONS,

        "current_event_ids":
            EXPECTED_EVENT_IDS,

        "target_identity_sha256":
            EXPECTED_TARGET_IDENTITY_SHA256,

        "seed_queue_task_count":
            len(
                rows
            ),

        "seed_queue_sha256":
            sha256_bytes(
                payload
            ),

        "route_counts":
            route_counts,

        "retrieval_manifest_schema":
            RETRIEVAL_MANIFEST_FIELDS,

        "evidence_assessment_schema":
            EVIDENCE_ASSESSMENT_FIELDS,

        "network_transport_implemented":
            False,

        "network_execution_authorized":
            False,

        "scientific_decisions_allowed":
            False,

        "production_mutation_allowed":
            False,

        "production_root_exists":
            PRODUCTION_ROOT.exists(),

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


def execute_network() -> None:
    raise NetworkExecutionNotAuthorizedError(
        "Live authoritative-source network retrieval is not "
        "implemented or authorized by this frozen implementation gate"
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
        "--print-queue",
        action="store_true",
    )

    parser.add_argument(
        "--execute-network",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if (
        args.print_queue
        and args.execute_network
    ):
        raise RetrievalImplementationError(
            "Choose only one action"
        )

    design = load_design()

    validate_current_state(
        design=
            design,

        ledger_path=
            args.ledger.resolve(),

        review_packet_path=
            args.review_packet.resolve(),
    )

    if args.execute_network:
        execute_network()

    if args.print_queue:
        sys.stdout.buffer.write(
            queue_bytes(
                design=
                    design,
            )
        )

        return 0

    print(
        json.dumps(
            describe_status(
                design=
                    design,

                ledger_path=
                    args.ledger.resolve(),

                review_packet_path=
                    args.review_packet.resolve(),
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
