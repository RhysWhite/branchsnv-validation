#!/usr/bin/env python3

from pathlib import Path
import csv
import hashlib
import importlib.util
import shutil
import sys
import tempfile


HERE = Path(__file__).resolve().parent

MODULE_PATH = (
    HERE
    / "baseline_scientific_screening_event_appender.py"
)

spec = importlib.util.spec_from_file_location(
    "baseline_scientific_screening_event_appender_tests",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

mod = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = mod

spec.loader.exec_module(
    mod
)

base = mod.load_base_engine()


def expect_error(
    label,
    fn,
):
    try:
        fn()

    except (
        mod.EventAppenderError,
        base.ExecutionValidationError,
    ):
        print(
            "PASS |",
            label,
        )

        return

    raise AssertionError(
        "Expected fail-closed error: "
        + label
    )


def fake_baseline_row(
    entity_id,
    *,
    state="ready",
):
    row = {
        field: ""
        for field
        in base.QUEUE_FIELDS
    }

    row.update({
        "screening_entity_id":
            entity_id,

        "screening_entity_class":
            "publication",

        "publication_reconciliation_key":
            entity_id,

        "database_dedup_keys":
            "doi:10.1000/"
            + entity_id.replace(
                ":",
                "_",
            ),

        "title_or_software_name":
            "Synthetic test record",

        "title_variants":
            '["Synthetic test record"]',

        "doi":
            "10.1000/"
            + entity_id.replace(
                ":",
                "_",
            ),

        "metadata_screenability":
            (
                "screenable"
                if state == "ready"
                else "blocked_title_unresolved"
            ),

        "screening_state":
            state,
    })

    return row


synthetic_rows = [
    fake_baseline_row(
        "entity:001"
    ),
    fake_baseline_row(
        "entity:002"
    ),
    fake_baseline_row(
        "entity:003"
    ),
    fake_baseline_row(
        "entity:999",
        state="blocked_metadata",
    ),
]

synthetic_by_id = {
    row[
        "screening_entity_id"
    ]:
        row
    for row in synthetic_rows
}

synthetic_baseline = base.Baseline(
    fields=
        list(
            base.QUEUE_FIELDS
        ),

    rows=
        synthetic_rows,

    by_id=
        synthetic_by_id,

    row_sha256={
        entity_id:
            base.canonical_row_sha256(
                row
            )
        for entity_id, row
        in synthetic_by_id.items()
    },

    ready_ids=(
        "entity:001",
        "entity:002",
        "entity:003",
    ),

    blocked_ids=(
        "entity:999",
    ),
)

synthetic_membership = {
    "B000001": (
        "entity:001",
        "entity:002",
    ),

    "B000002": (
        "entity:003",
    ),
}

synthetic_membership_by_entity = {
    "entity:001": {
        "batch_id":
            "B000001",

        "batch_index":
            1,

        "position_in_batch":
            1,

        "global_active_index":
            1,

        "baseline_row_sha256":
            synthetic_baseline.row_sha256[
                "entity:001"
            ],
    },

    "entity:002": {
        "batch_id":
            "B000001",

        "batch_index":
            1,

        "position_in_batch":
            2,

        "global_active_index":
            2,

        "baseline_row_sha256":
            synthetic_baseline.row_sha256[
                "entity:002"
            ],
    },

    "entity:003": {
        "batch_id":
            "B000002",

        "batch_index":
            2,

        "position_in_batch":
            1,

        "global_active_index":
            3,

        "baseline_row_sha256":
            synthetic_baseline.row_sha256[
                "entity:003"
            ],
    },
}

synthetic_context = {
    "design":
        {},

    "base":
        base,

    "baseline":
        synthetic_baseline,

    "batch_membership":
        synthetic_membership,

    "membership_by_entity":
        synthetic_membership_by_entity,
}


def proposal_row(
    entity_id,
    batch_id,
    *,
    event_type,
    record_decision="",
    exclusion_reason_code="",
    candidate_method_flag="",
    evidence_basis="Synthetic unit-test evidence basis",
    evidence_source_locator="",
    evidence_escalation_status="",
    supersedes_event_id="",
    operator_id="synthetic-human",
    operator_type="human",
    notes="synthetic test only",
):
    return {
        "screening_entity_id":
            entity_id,

        "batch_id":
            batch_id,

        "event_type":
            event_type,

        "record_decision":
            record_decision,

        "exclusion_reason_code":
            exclusion_reason_code,

        "candidate_method_flag":
            candidate_method_flag,

        "evidence_basis":
            evidence_basis,

        "evidence_source_locator":
            evidence_source_locator,

        "evidence_escalation_status":
            evidence_escalation_status,

        "supersedes_event_id":
            supersedes_event_id,

        "operator_id":
            operator_id,

        "operator_type":
            operator_type,

        "notes":
            notes,
    }


genesis_bytes = base.tsv_bytes(
    fields=
        list(
            base.EVENT_FIELDS
        ),
    rows=[],
)

genesis_fields, genesis_rows = (
    mod.parse_tsv_bytes(
        genesis_bytes
    )
)

genesis_sha = hashlib.sha256(
    genesis_bytes
).hexdigest()


source_proposal = [
    proposal_row(
        "entity:001",
        "B000001",
        event_type=
            "source_escalation",

        evidence_basis=
            "Synthetic unit test requires authoritative source lookup",

        evidence_source_locator=
            "",

        evidence_escalation_status=
            "awaiting_source_escalation",
    ),
]


prepared_source = (
    mod.prepare_transaction_core(
        existing_fields=
            genesis_fields,

        existing_rows=
            genesis_rows,

        existing_bytes=
            genesis_bytes,

        expected_pre_ledger_sha256=
            genesis_sha,

        proposal_rows=
            source_proposal,

        proposal_sha256=
            hashlib.sha256(
                b"synthetic-source-proposal"
            ).hexdigest(),

        context=
            synthetic_context,

        transaction_timestamp_utc=
            "2026-09-25T00:00:00Z",
    )
)

assert prepared_source[
    "new_rows"
][
    0
][
    "event_id"
] == "E000000001"

assert prepared_source[
    "new_rows"
][
    0
][
    "event_type"
] == "source_escalation"

assert prepared_source[
    "new_rows"
][
    0
][
    "reviewer_id"
] == ""

assert prepared_source[
    "receipt"
][
    "strict_prefix_extension"
] is True

assert prepared_source[
    "candidate_bytes"
].startswith(
    genesis_bytes
)

print(
    "PASS | initial source escalation prepared"
)

print(
    "PASS | first deterministic event ID = E000000001"
)

print(
    "PASS | review/adjudication fields automatically blank"
)

print(
    "PASS | candidate ledger is exact prefix extension"
)


source_fields, source_rows = (
    mod.parse_tsv_bytes(
        prepared_source[
            "candidate_bytes"
        ]
    )
)


resolution_proposal = [
    proposal_row(
        "entity:001",
        "B000001",
        event_type=
            "superseding_record_decision",

        record_decision=
            "retain_for_method_assessment",

        candidate_method_flag=
            "true",

        evidence_basis=
            "Synthetic authoritative source establishes reusable method",

        evidence_source_locator=
            "doi:10.1000/synthetic",

        evidence_escalation_status=
            "resolved",

        supersedes_event_id=
            "E000000001",
    ),
]


prepared_resolution = (
    mod.prepare_transaction_core(
        existing_fields=
            source_fields,

        existing_rows=
            source_rows,

        existing_bytes=
            prepared_source[
                "candidate_bytes"
            ],

        expected_pre_ledger_sha256=
            hashlib.sha256(
                prepared_source[
                    "candidate_bytes"
                ]
            ).hexdigest(),

        proposal_rows=
            resolution_proposal,

        proposal_sha256=
            hashlib.sha256(
                b"synthetic-resolution-proposal"
            ).hexdigest(),

        context=
            synthetic_context,

        transaction_timestamp_utc=
            "2026-09-25T00:01:00Z",
    )
)

assert prepared_resolution[
    "new_rows"
][
    0
][
    "event_id"
] == "E000000002"

assert prepared_resolution[
    "new_rows"
][
    0
][
    "supersedes_event_id"
] == "E000000001"

assert prepared_resolution[
    "receipt"
][
    "derived_state_counts_after_append"
][
    "complete"
] == 1

print(
    "PASS | source escalation resolves through superseding terminal event"
)

print(
    "PASS | second deterministic event ID = E000000002"
)


resolved_fields, resolved_rows = (
    mod.parse_tsv_bytes(
        prepared_resolution[
            "candidate_bytes"
        ]
    )
)


correction_proposal = [
    proposal_row(
        "entity:001",
        "B000001",
        event_type=
            "superseding_record_decision",

        record_decision=
            "exclude",

        exclusion_reason_code=
            "application_only_no_reusable_method",

        candidate_method_flag=
            "false",

        evidence_basis=
            "Synthetic correction evidence",

        evidence_source_locator=
            "doi:10.1000/synthetic-correction",

        evidence_escalation_status=
            "resolved",

        supersedes_event_id=
            "E000000002",
    ),
]


prepared_correction = (
    mod.prepare_transaction_core(
        existing_fields=
            resolved_fields,

        existing_rows=
            resolved_rows,

        existing_bytes=
            prepared_resolution[
                "candidate_bytes"
            ],

        expected_pre_ledger_sha256=
            hashlib.sha256(
                prepared_resolution[
                    "candidate_bytes"
                ]
            ).hexdigest(),

        proposal_rows=
            correction_proposal,

        proposal_sha256=
            hashlib.sha256(
                b"synthetic-correction-proposal"
            ).hexdigest(),

        context=
            synthetic_context,

        transaction_timestamp_utc=
            "2026-09-25T00:02:00Z",
    )
)

assert prepared_correction[
    "new_rows"
][
    0
][
    "event_id"
] == "E000000003"

assert prepared_correction[
    "new_rows"
][
    0
][
    "supersedes_event_id"
] == "E000000002"

assert prepared_correction[
    "new_rows"
][
    0
][
    "evidence_escalation_status"
] == "resolved"

print(
    "PASS | terminal correction preserves escalation-history status"
)


initial_terminal = [
    proposal_row(
        "entity:002",
        "B000001",
        event_type=
            "record_decision",

        record_decision=
            "retain_for_method_assessment",

        candidate_method_flag=
            "true",

        evidence_basis=
            "Synthetic terminal evidence",

        evidence_source_locator=
            "doi:10.1000/synthetic-terminal",
    ),
]

prepared_terminal = (
    mod.prepare_transaction_core(
        existing_fields=
            genesis_fields,

        existing_rows=
            genesis_rows,

        existing_bytes=
            genesis_bytes,

        expected_pre_ledger_sha256=
            genesis_sha,

        proposal_rows=
            initial_terminal,

        proposal_sha256=
            hashlib.sha256(
                b"synthetic-terminal-proposal"
            ).hexdigest(),

        context=
            synthetic_context,

        transaction_timestamp_utc=
            "2026-09-25T00:03:00Z",
    )
)

assert prepared_terminal[
    "new_rows"
][
    0
][
    "record_decision"
] == "retain_for_method_assessment"

print(
    "PASS | initial terminal decision contract accepted"
)


bad_duplicate = [
    initial_terminal[0],
    dict(
        initial_terminal[0]
    ),
]

expect_error(
    "multiple proposal rows for one entity prohibited",
    lambda:
        mod.prepare_transaction_core(
            existing_fields=
                genesis_fields,

            existing_rows=
                genesis_rows,

            existing_bytes=
                genesis_bytes,

            expected_pre_ledger_sha256=
                genesis_sha,

            proposal_rows=
                bad_duplicate,

            proposal_sha256=
                hashlib.sha256(
                    b"duplicate"
                ).hexdigest(),

            context=
                synthetic_context,

            transaction_timestamp_utc=
                "2026-09-25T00:04:00Z",
        ),
)


cross_batch = [
    initial_terminal[0],
    proposal_row(
        "entity:003",
        "B000002",
        event_type=
            "record_decision",

        record_decision=
            "retain_for_method_assessment",

        candidate_method_flag=
            "true",

        evidence_source_locator=
            "doi:10.1000/other",
    ),
]

expect_error(
    "cross-batch transaction prohibited",
    lambda:
        mod.prepare_transaction_core(
            existing_fields=
                genesis_fields,

            existing_rows=
                genesis_rows,

            existing_bytes=
                genesis_bytes,

            expected_pre_ledger_sha256=
                genesis_sha,

            proposal_rows=
                cross_batch,

            proposal_sha256=
                hashlib.sha256(
                    b"cross-batch"
                ).hexdigest(),

            context=
                synthetic_context,

            transaction_timestamp_utc=
                "2026-09-25T00:05:00Z",
        ),
)


bad_terminal_locator = [
    proposal_row(
        "entity:002",
        "B000001",
        event_type=
            "record_decision",

        record_decision=
            "retain_for_method_assessment",

        candidate_method_flag=
            "true",

        evidence_source_locator=
            "",
    ),
]

expect_error(
    "terminal event requires evidence source locator",
    lambda:
        mod.prepare_transaction_core(
            existing_fields=
                genesis_fields,

            existing_rows=
                genesis_rows,

            existing_bytes=
                genesis_bytes,

            expected_pre_ledger_sha256=
                genesis_sha,

            proposal_rows=
                bad_terminal_locator,

            proposal_sha256=
                hashlib.sha256(
                    b"no-locator"
                ).hexdigest(),

            context=
                synthetic_context,

            transaction_timestamp_utc=
                "2026-09-25T00:06:00Z",
        ),
)


bad_flag = [
    proposal_row(
        "entity:002",
        "B000001",
        event_type=
            "record_decision",

        record_decision=
            "retain_for_method_assessment",

        candidate_method_flag=
            "false",

        evidence_source_locator=
            "doi:10.1000/bad-flag",
    ),
]

expect_error(
    "retain decision with false candidate flag prohibited",
    lambda:
        mod.prepare_transaction_core(
            existing_fields=
                genesis_fields,

            existing_rows=
                genesis_rows,

            existing_bytes=
                genesis_bytes,

            expected_pre_ledger_sha256=
                genesis_sha,

            proposal_rows=
                bad_flag,

            proposal_sha256=
                hashlib.sha256(
                    b"bad-flag"
                ).hexdigest(),

            context=
                synthetic_context,

            transaction_timestamp_utc=
                "2026-09-25T00:07:00Z",
        ),
)


bad_supersede = [
    proposal_row(
        "entity:001",
        "B000001",
        event_type=
            "superseding_record_decision",

        record_decision=
            "retain_for_method_assessment",

        candidate_method_flag=
            "true",

        evidence_source_locator=
            "doi:10.1000/bad-super",

        evidence_escalation_status=
            "resolved",

        supersedes_event_id=
            "E000000999",
    ),
]

expect_error(
    "supersession must reference current event",
    lambda:
        mod.prepare_transaction_core(
            existing_fields=
                source_fields,

            existing_rows=
                source_rows,

            existing_bytes=
                prepared_source[
                    "candidate_bytes"
                ],

            expected_pre_ledger_sha256=
                hashlib.sha256(
                    prepared_source[
                        "candidate_bytes"
                    ]
                ).hexdigest(),

            proposal_rows=
                bad_supersede,

            proposal_sha256=
                hashlib.sha256(
                    b"bad-super"
                ).hexdigest(),

            context=
                synthetic_context,

            transaction_timestamp_utc=
                "2026-09-25T00:08:00Z",
        ),
)


branching_escalation = [
    proposal_row(
        "entity:001",
        "B000001",
        event_type=
            "source_escalation",

        evidence_escalation_status=
            "awaiting_source_escalation",
    ),
]

expect_error(
    "second unsuperseded source escalation prohibited",
    lambda:
        mod.prepare_transaction_core(
            existing_fields=
                source_fields,

            existing_rows=
                source_rows,

            existing_bytes=
                prepared_source[
                    "candidate_bytes"
                ],

            expected_pre_ledger_sha256=
                hashlib.sha256(
                    prepared_source[
                        "candidate_bytes"
                    ]
                ).hexdigest(),

            proposal_rows=
                branching_escalation,

            proposal_sha256=
                hashlib.sha256(
                    b"branching"
                ).hexdigest(),

            context=
                synthetic_context,

            transaction_timestamp_utc=
                "2026-09-25T00:09:00Z",
        ),
)


newline_note = [
    proposal_row(
        "entity:002",
        "B000001",
        event_type=
            "record_decision",

        record_decision=
            "retain_for_method_assessment",

        candidate_method_flag=
            "true",

        evidence_source_locator=
            "doi:10.1000/newline",

        notes=
            "bad\nnote",
    ),
]

expect_error(
    "embedded newline in event field prohibited",
    lambda:
        mod.prepare_transaction_core(
            existing_fields=
                genesis_fields,

            existing_rows=
                genesis_rows,

            existing_bytes=
                genesis_bytes,

            expected_pre_ledger_sha256=
                genesis_sha,

            proposal_rows=
                newline_note,

            proposal_sha256=
                hashlib.sha256(
                    b"newline"
                ).hexdigest(),

            context=
                synthetic_context,

            transaction_timestamp_utc=
                "2026-09-25T00:10:00Z",
        ),
)


expect_error(
    "stale expected ledger SHA prohibited",
    lambda:
        mod.prepare_transaction_core(
            existing_fields=
                genesis_fields,

            existing_rows=
                genesis_rows,

            existing_bytes=
                genesis_bytes,

            expected_pre_ledger_sha256=
                "0" * 64,

            proposal_rows=
                initial_terminal,

            proposal_sha256=
                hashlib.sha256(
                    b"stale"
                ).hexdigest(),

            context=
                synthetic_context,

            transaction_timestamp_utc=
                "2026-09-25T00:11:00Z",
        ),
)


expect_error(
    "subsecond transaction timestamp prohibited",
    lambda:
        mod.prepare_transaction_core(
            existing_fields=
                genesis_fields,

            existing_rows=
                genesis_rows,

            existing_bytes=
                genesis_bytes,

            expected_pre_ledger_sha256=
                genesis_sha,

            proposal_rows=
                initial_terminal,

            proposal_sha256=
                hashlib.sha256(
                    b"timestamp"
                ).hexdigest(),

            context=
                synthetic_context,

            transaction_timestamp_utc=
                "2026-09-25T00:11:00.123Z",
        ),
)


# ---------------------------------------------------------
# Real frozen package integration tests, but all mutations
# occur only on temporary copies of the genesis ledger.
# ---------------------------------------------------------

real_context = mod.load_context(
    queue_path=
        mod.DEFAULT_QUEUE,

    execution_root=
        mod.EXECUTION_ROOT,

    design_path=
        mod.DEFAULT_DESIGN,
)

real_validation = mod.validate_current_ledger(
    ledger_path=
        mod.DEFAULT_LEDGER,

    context=
        real_context,
)

assert real_validation[
    "event_count"
] == 0

assert real_validation[
    "ledger_sha256"
] == mod.EXPECTED_GENESIS_LEDGER_SHA256

print(
    "PASS | real production genesis validates read-only"
)


first_batch = real_context[
    "batch_membership"
][
    "B000001"
]

first_entity = first_batch[
    0
]


with tempfile.TemporaryDirectory(
    prefix="branchsnv-exp07-event-appender-tests-"
) as tmp:
    root = Path(tmp)

    temp_ledger = (
        root
        / "event_ledger.tsv"
    )

    shutil.copyfile(
        mod.DEFAULT_LEDGER,
        temp_ledger,
    )

    proposal_path = (
        root
        / "proposal.tsv"
    )

    proposal = proposal_row(
        first_entity,
        "B000001",
        event_type=
            "source_escalation",

        evidence_basis=
            (
                "SYNTHETIC_TEST_ONLY: "
                "exercise source-escalation append machinery"
            ),

        evidence_source_locator=
            "",

        evidence_escalation_status=
            "awaiting_source_escalation",

        operator_id=
            "synthetic-test-operator",

        operator_type=
            "human",

        notes=
            "synthetic temporary-ledger test only",
    )

    with proposal_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=
                mod.PROPOSAL_FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerow(
            proposal
        )

    old_bytes = temp_ledger.read_bytes()

    result = mod.append_transaction_atomic(
        ledger_path=
            temp_ledger,

        proposal_path=
            proposal_path,

        expected_pre_ledger_sha256=
            hashlib.sha256(
                old_bytes
            ).hexdigest(),

        context=
            real_context,

        transaction_timestamp_utc=
            "2026-09-25T01:00:00Z",

        allow_production=False,
    )

    assert result[
        "published"
    ] is True

    assert result[
        "first_assigned_event_id"
    ] == "E000000001"

    new_bytes = temp_ledger.read_bytes()

    assert new_bytes.startswith(
        old_bytes
    )

    assert len(
        new_bytes
    ) > len(
        old_bytes
    )

    validated = mod.validate_current_ledger(
        ledger_path=
            temp_ledger,

        context=
            real_context,
    )

    assert validated[
        "event_count"
    ] == 1

    assert validated[
        "derived_state_counts"
    ][
        "awaiting_source_escalation"
    ] == 1

    print(
        "PASS | atomic append succeeds on temporary genesis copy"
    )

    print(
        "PASS | temporary ledger is strict prefix extension"
    )

    print(
        "PASS | post-publication temporary ledger validates"
    )


    expect_error(
        "stale-SHA replay after successful append prohibited",
        lambda:
            mod.append_transaction_atomic(
                ledger_path=
                    temp_ledger,

                proposal_path=
                    proposal_path,

                expected_pre_ledger_sha256=
                    hashlib.sha256(
                        old_bytes
                    ).hexdigest(),

                context=
                    real_context,

                transaction_timestamp_utc=
                    "2026-09-25T01:01:00Z",

                allow_production=False,
            ),
    )


expect_error(
    "direct production mutation prohibited without later authorisation",
    lambda:
        mod.append_transaction_atomic(
            ledger_path=
                mod.DEFAULT_LEDGER,

            proposal_path=
                Path(
                    "/nonexistent/proposal.tsv"
                ),

            expected_pre_ledger_sha256=
                mod.EXPECTED_GENESIS_LEDGER_SHA256,

            context=
                real_context,

            transaction_timestamp_utc=
                "2026-09-25T01:02:00Z",

            allow_production=False,
        ),
)


assert hashlib.sha256(
    mod.DEFAULT_LEDGER.read_bytes()
).hexdigest() == mod.EXPECTED_GENESIS_LEDGER_SHA256

print(
    "PASS | real production ledger remained untouched throughout tests"
)

print(
    "PASS | hostile event-appender tests complete"
)
