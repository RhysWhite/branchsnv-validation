#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import sys


HERE = Path(__file__).resolve().parent

MODULE_PATH = (
    HERE
    / "baseline_scientific_screening_execution.py"
)

spec = importlib.util.spec_from_file_location(
    "baseline_scientific_screening_execution",
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


def expect_error(
    label,
    fn,
):
    try:
        fn()

    except mod.ExecutionValidationError:
        print(
            "PASS |",
            label,
        )

        return

    raise AssertionError(
        "Expected ExecutionValidationError: "
        + label
    )


def fake_queue_row(
    entity_id,
    *,
    state="ready",
):
    return {
        "screening_entity_id":
            entity_id,

        "screening_entity_class":
            "publication",

        "publication_reconciliation_key":
            entity_id,

        "database_dedup_keys":
            "",

        "biotools_id":
            "",

        "citation_provenance_ids":
            "",

        "discovery_stages":
            "",

        "citation_wave_provenance":
            "",

        "title_or_software_name":
            "Example",

        "title_variants":
            '["Example"]',

        "year":
            "2020",

        "doi":
            "",

        "pmid":
            "",

        "openalex_id":
            "",

        "omid":
            "",

        "identity_attention_status":
            "",

        "metadata_screenability":
            (
                "screenable"
                if state == "ready"
                else "blocked_title_unresolved"
            ),

        "screening_state":
            state,

        "record_decision":
            "",

        "exclusion_reason_code":
            "",

        "candidate_method_flag":
            "",

        "evidence_escalation_status":
            "",

        "operator":
            "",

        "decision_batch":
            "",

        "notes":
            "",
    }


def fake_baseline():
    rows = [
        fake_queue_row(
            "entity:001"
        ),
        fake_queue_row(
            "entity:002"
        ),
        fake_queue_row(
            "entity:003"
        ),
        fake_queue_row(
            "entity:004",
            state="blocked_metadata",
        ),
    ]

    by_id = {
        row[
            "screening_entity_id"
        ]:
            row
        for row in rows
    }

    hashes = {
        entity_id:
            mod.canonical_row_sha256(
                row
            )
        for entity_id, row
        in by_id.items()
    }

    return mod.Baseline(
        fields=
            list(
                mod.QUEUE_FIELDS
            ),

        rows=rows,

        by_id=by_id,

        row_sha256=hashes,

        ready_ids=(
            "entity:001",
            "entity:002",
            "entity:003",
        ),

        blocked_ids=(
            "entity:004",
        ),
    )


baseline = fake_baseline()


# ------------------------------------------------------------
# Frozen decision semantics.
# ------------------------------------------------------------

mod.validate_terminal_fields(
    record_decision=
        "retain_for_method_assessment",

    exclusion_reason_code=
        "",

    candidate_method_flag=
        "true",
)

print(
    "PASS | retain invariant accepted"
)


mod.validate_terminal_fields(
    record_decision=
        "exclude",

    exclusion_reason_code=
        "application_only_no_reusable_method",

    candidate_method_flag=
        "false",
)

print(
    "PASS | exclusion invariant accepted"
)


expect_error(
    "retain cannot carry exclusion reason",
    lambda:
        mod.validate_terminal_fields(
            record_decision=
                "retain_for_method_assessment",

            exclusion_reason_code=
                "unrelated_variant_or_data_type",

            candidate_method_flag=
                "true",
        ),
)


expect_error(
    "exclude requires candidate_method_flag=false",
    lambda:
        mod.validate_terminal_fields(
            record_decision=
                "exclude",

            exclusion_reason_code=
                "unrelated_variant_or_data_type",

            candidate_method_flag=
                "true",
        ),
)


expect_error(
    "unknown exclusion reason fails closed",
    lambda:
        mod.validate_terminal_fields(
            record_decision=
                "exclude",

            exclusion_reason_code=
                "invented_reason",

            candidate_method_flag=
                "false",
        ),
)


# ------------------------------------------------------------
# Carry-forward mapping fails closed.
# ------------------------------------------------------------

pending = mod.load_carry_forward_map(
    path=None,
    baseline=baseline,
)

assert pending[
    "status"
] == "PENDING_FROZEN_MAPPING"

assert pending[
    "anchor_count"
] == 0

print(
    "PASS | absent carry-forward mapping remains pending"
)


expect_error(
    "real batch generation prohibited before carry-forward mapping",
    lambda:
        mod.build_batch_manifests(
            baseline=baseline,
            carry_forward=pending,
            max_batch_size=2,
        ),
)


# Synthetic complete mapping uses exactly eight distinct
# ready entities, so use a larger synthetic baseline.
rows = [
    fake_queue_row(
        f"entity:{index:03d}"
    )
    for index in range(
        1,
        13,
    )
]

by_id = {
    row[
        "screening_entity_id"
    ]:
        row
    for row in rows
}

synthetic = mod.Baseline(
    fields=
        list(
            mod.QUEUE_FIELDS
        ),

    rows=rows,

    by_id=by_id,

    row_sha256={
        key:
            mod.canonical_row_sha256(
                row
            )
        for key, row
        in by_id.items()
    },

    ready_ids=tuple(
        sorted(
            by_id
        )
    ),

    blocked_ids=tuple(),
)

carry_rows = []

for index in range(
    1,
    9,
):
    carry_rows.append({
        "anchor_id":
            f"anchor:{index}",

        "prior_adjudication_source_id":
            f"source:{index}",

        "prior_adjudication_source_sha256":
            "a" * 64,

        "screening_entity_id":
            f"entity:{index:03d}",

        "mapping_basis":
            "frozen_exact_identity",

        "record_decision":
            "retain_for_method_assessment",

        "exclusion_reason_code":
            "",

        "candidate_method_flag":
            "true",

        "notes":
            "",
    })


complete = (
    mod.validate_carry_forward_rows(
        fields=
            list(
                mod.CARRY_FORWARD_FIELDS
            ),

        rows=carry_rows,
        baseline=synthetic,
    )
)

assert complete[
    "status"
] == "COMPLETE_UNIQUE_MAPPING"

assert complete[
    "anchor_count"
] == 8

print(
    "PASS | exact eight-anchor mapping accepted"
)


manifests, membership = (
    mod.build_batch_manifests(
        baseline=synthetic,
        carry_forward=complete,
        max_batch_size=2,
    )
)

assert [
    row[
        "batch_id"
    ]
    for row in manifests
] == [
    "B000001",
    "B000002",
]

assert membership[
    "B000001"
] == (
    "entity:009",
    "entity:010",
)

assert membership[
    "B000002"
] == (
    "entity:011",
    "entity:012",
)

print(
    "PASS | deterministic batching excludes prior carry-forwards"
)


bad_fuzzy = [
    dict(
        row
    )
    for row in carry_rows
]

bad_fuzzy[
    0
][
    "mapping_basis"
] = "fuzzy_title_match"

expect_error(
    "fuzzy carry-forward mapping prohibited",
    lambda:
        mod.validate_carry_forward_rows(
            fields=
                list(
                    mod.CARRY_FORWARD_FIELDS
                ),

            rows=bad_fuzzy,
            baseline=synthetic,
        ),
)


# ------------------------------------------------------------
# Event validation.
# ------------------------------------------------------------

event_baseline = synthetic

event_carry = complete

event_manifests, event_membership = (
    mod.build_batch_manifests(
        baseline=event_baseline,
        carry_forward=event_carry,
        max_batch_size=2,
    )
)

row = {
    "event_id":
        "EV000001",

    "event_type":
        "record_decision",

    "screening_entity_id":
        "entity:009",

    "baseline_queue_sha256":
        mod.EXPECTED_QUEUE_SHA256,

    "baseline_row_sha256":
        event_baseline.row_sha256[
            "entity:009"
        ],

    "batch_id":
        "B000001",

    "record_decision":
        "retain_for_method_assessment",

    "exclusion_reason_code":
        "",

    "candidate_method_flag":
        "true",

    "evidence_basis":
        "frozen_baseline_metadata",

    "evidence_source_locator":
        "",

    "evidence_escalation_status":
        "",

    "operator_id":
        "operator:test",

    "operator_type":
        "human",

    "decision_timestamp_utc":
        "2026-09-25T00:00:00Z",

    "supersedes_event_id":
        "",

    "reviewer_id":
        "",

    "review_status":
        "",

    "adjudication_status":
        "",

    "notes":
        "",
}


mod.validate_event_row(
    row=row,
    baseline=event_baseline,
    batch_membership=
        event_membership,
    existing_event_ids=set(),
    prior_events_by_id={},
)

print(
    "PASS | valid terminal event accepted"
)


blocked_event = dict(
    row
)

blocked_event[
    "event_id"
] = "EVBLOCKED"

blocked_event[
    "screening_entity_id"
] = "entity:004"

blocked_baseline = baseline

blocked_event[
    "baseline_row_sha256"
] = blocked_baseline.row_sha256[
    "entity:004"
]

expect_error(
    "blocked_metadata cannot receive scientific event",
    lambda:
        mod.validate_event_row(
            row=blocked_event,
            baseline=blocked_baseline,
            batch_membership={
                "B000001":
                    (
                        "entity:004",
                    )
            },
            existing_event_ids=set(),
            prior_events_by_id={},
        ),
)


escalation = dict(
    row
)

escalation[
    "event_id"
] = "EV000002"

escalation[
    "event_type"
] = "source_escalation"

escalation[
    "screening_entity_id"
] = "entity:010"

escalation[
    "baseline_row_sha256"
] = event_baseline.row_sha256[
    "entity:010"
]

escalation[
    "record_decision"
] = ""

escalation[
    "candidate_method_flag"
] = ""

escalation[
    "exclusion_reason_code"
] = ""

escalation[
    "evidence_escalation_status"
] = "awaiting_source_escalation"

mod.validate_event_row(
    row=escalation,
    baseline=event_baseline,
    batch_membership=
        event_membership,
    existing_event_ids={
        "EV000001",
    },
    prior_events_by_id={
        "EV000001":
            row,
    },
)

print(
    "PASS | source escalation event accepted without terminal decision"
)


bad_escalation = dict(
    escalation
)

bad_escalation[
    "record_decision"
] = "exclude"

bad_escalation[
    "candidate_method_flag"
] = "false"

bad_escalation[
    "exclusion_reason_code"
] = "unrelated_variant_or_data_type"

expect_error(
    "source escalation cannot smuggle terminal decision",
    lambda:
        mod.validate_event_row(
            row=bad_escalation,
            baseline=event_baseline,
            batch_membership=
                event_membership,
            existing_event_ids=set(),
            prior_events_by_id={},
        ),
)


# ------------------------------------------------------------
# Derived ledger state.
# ------------------------------------------------------------

summary = (
    mod.validate_event_ledger(
        fields=
            list(
                mod.EVENT_FIELDS
            ),

        rows=[
            row,
            escalation,
        ],

        baseline=event_baseline,
        batch_membership=
            event_membership,
    )
)

assert summary[
    "event_count"
] == 2

assert summary[
    "state_counts"
][
    "complete"
] == 1

assert summary[
    "state_counts"
][
    "awaiting_source_escalation"
] == 1

print(
    "PASS | deterministic current-state projection valid"
)


conflict = dict(
    row
)

conflict[
    "event_id"
] = "EV000003"

conflict[
    "record_decision"
] = "exclude"

conflict[
    "candidate_method_flag"
] = "false"

conflict[
    "exclusion_reason_code"
] = "unrelated_variant_or_data_type"

expect_error(
    "conflicting unsuperseded terminal events fail closed",
    lambda:
        mod.validate_event_ledger(
            fields=
                list(
                    mod.EVENT_FIELDS
                ),

            rows=[
                row,
                conflict,
            ],

            baseline=event_baseline,
            batch_membership=
                event_membership,
        ),
)


print(
    "PASS | hostile execution tests complete"
)
