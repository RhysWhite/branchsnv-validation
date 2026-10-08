#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import sys


HERE = Path(__file__).resolve().parent

MODULE_PATH = (
    HERE
    / "baseline_scientific_screening_execution_amendment_01.py"
)

spec = importlib.util.spec_from_file_location(
    "baseline_scientific_screening_execution_amendment_01",
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

base = mod.load_frozen_base_module()


def expect_error(
    label,
    fn,
):
    try:
        fn()

    except mod.AmendmentValidationError:
        print(
            "PASS |",
            label,
        )

        return

    raise AssertionError(
        "Expected AmendmentValidationError: "
        + label
    )


def fake_row(
    entity_id,
    doi,
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
            (
                "doi:"
                + doi
            ),

        "title_or_software_name":
            "Example publication",

        "title_variants":
            '["Example publication"]',

        "doi":
            doi,

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


dois = [
    "10.1000/a1",
    "10.1000/a2",
    "10.1000/a3",
    "10.1000/a4",
    "10.1000/a5",
    "10.1000/a7",
    "10.1000/a8",
]

rows = [
    fake_row(
        f"entity:{index:03d}",
        doi,
    )
    for index, doi
    in zip(
        [
            1,
            2,
            3,
            4,
            5,
            7,
            8,
        ],
        dois,
    )
]

# Three ordinary ready records remain active.
rows.extend([
    fake_row(
        "entity:101",
        "10.2000/x1",
    ),
    fake_row(
        "entity:102",
        "10.2000/x2",
    ),
    fake_row(
        "entity:103",
        "10.2000/x3",
    ),
])

# One metadata blocker.
rows.append(
    fake_row(
        "entity:999",
        "10.2000/blocked",
        state="blocked_metadata",
    )
)

rows = sorted(
    rows,
    key=lambda row:
        row[
            "screening_entity_id"
        ],
)

by_id = {
    row[
        "screening_entity_id"
    ]:
        row
    for row in rows
}

baseline = base.Baseline(
    fields=
        list(
            base.QUEUE_FIELDS
        ),

    rows=rows,

    by_id=by_id,

    row_sha256={
        entity_id:
            base.canonical_row_sha256(
                row
            )
        for entity_id, row
        in by_id.items()
    },

    ready_ids=tuple(
        row[
            "screening_entity_id"
        ]
        for row in rows
        if row[
            "screening_state"
        ] == "ready"
    ),

    blocked_ids=tuple(
        row[
            "screening_entity_id"
        ]
        for row in rows
        if row[
            "screening_state"
        ] == "blocked_metadata"
    ),
)


resolution_rows = []

anchor_data = [
    ("W0A01", "Tool1", "10.1000/a1", "entity:001"),
    ("W0A02", "Tool2", "10.1000/a2", "entity:002"),
    ("W0A03", "Tool3", "10.1000/a3", "entity:003"),
    ("W0A04", "Tool4", "10.1000/a4", "entity:004"),
    ("W0A05", "Tool5", "10.1000/a5", "entity:005"),
    (
        "W0A06",
        "kSNP3.0",
        mod.OUT_OF_BASELINE_DOI,
        "",
    ),
    ("W0A07", "Tool7", "10.1000/a7", "entity:007"),
    ("W0A08", "Tool8", "10.1000/a8", "entity:008"),
]

for anchor_id, tool, doi, entity_id in anchor_data:
    in_baseline = bool(
        entity_id
    )

    resolution_rows.append({
        "anchor_id":
            anchor_id,

        "tool":
            tool,

        "canonical_identifier_type":
            "doi",

        "canonical_identifier":
            doi,

        "prior_anchor_decision":
            "include_as_anchor",

        "prior_landscape_decision":
            "include",

        "prior_confirmed_role":
            (
                "direct"
                if anchor_id
                in {
                    "W0A01",
                    "W0A02",
                    "W0A03",
                    "W0A04",
                }
                else "near_direct"
            ),

        "baseline_presence_status":
            (
                "in_baseline"
                if in_baseline
                else "out_of_baseline"
            ),

        "screening_entity_id":
            entity_id,

        "mapping_basis":
            (
                "exact_canonical_doi_to_database_dedup_key"
                if in_baseline
                else "canonical_doi_absent_from_baseline"
            ),

        "record_decision_projection":
            "retain_for_method_assessment",

        "candidate_method_flag_projection":
            "true",

        "additional_same_doi_entity_count":
            "0",

        "scientific_reassessment_performed":
            "false",
    })


resolution = mod.validate_resolution_rows(
    fields=
        list(
            mod.RESOLUTION_FIELDS
        ),

    rows=resolution_rows,
    baseline=baseline,
)

assert resolution[
    "status"
] == "COMPLETE_RESOLVED_8_EQ_7_PLUS_1"

assert resolution[
    "historical_anchor_count"
] == 8

assert resolution[
    "in_baseline_count"
] == 7

assert resolution[
    "out_of_baseline_count"
] == 1

assert len(
    resolution[
        "mapped_screening_entity_ids"
    ]
) == 7

print(
    "PASS | synthetic 8=7+1 resolution accepted"
)


compat = (
    mod.build_compatibility_carry_forward(
        resolution
    )
)

assert compat[
    "status"
] == "COMPLETE_UNIQUE_MAPPING"

assert compat[
    "anchor_count"
] == 7

assert len(
    compat[
        "mapped_screening_entity_ids"
    ]
) == 7

print(
    "PASS | seven-row compatibility carry-forward created"
)


manifests, membership = (
    base.build_batch_manifests(
        baseline=baseline,
        carry_forward=compat,
        max_batch_size=2,
    )
)

active = [
    entity_id
    for batch_id in sorted(
        membership
    )
    for entity_id
    in membership[
        batch_id
    ]
]

assert active == [
    "entity:101",
    "entity:102",
    "entity:103",
]

assert [
    row[
        "batch_id"
    ]
    for row in manifests
] == [
    "B000001",
    "B000002",
]

assert manifests[
    0
][
    "entity_count"
] == "2"

assert manifests[
    1
][
    "entity_count"
] == "1"

print(
    "PASS | batching excludes exactly seven carry-forward targets"
)

print(
    "PASS | out-of-baseline anchor subtracts no baseline entity"
)

print(
    "PASS | metadata blocker excluded from active population"
)


bad_extra_mapping = [
    dict(row)
    for row in resolution_rows
]

for row in bad_extra_mapping:
    if row[
        "anchor_id"
    ] == "W0A06":
        row[
            "baseline_presence_status"
        ] = "in_baseline"

        row[
            "screening_entity_id"
        ] = "entity:101"

        row[
            "mapping_basis"
        ] = (
            "exact_canonical_doi_to_database_dedup_key"
        )

expect_error(
    "W0A06 cannot be fabricated as in-baseline",
    lambda:
        mod.validate_resolution_rows(
            fields=
                list(
                    mod.RESOLUTION_FIELDS
                ),

            rows=bad_extra_mapping,
            baseline=baseline,
        ),
)


bad_substitute = [
    dict(row)
    for row in resolution_rows
]

for row in bad_substitute:
    if row[
        "anchor_id"
    ] == "W0A06":
        row[
            "canonical_identifier"
        ] = "10.2000/x1"

expect_error(
    "W0A06 canonical DOI cannot be substituted",
    lambda:
        mod.validate_resolution_rows(
            fields=
                list(
                    mod.RESOLUTION_FIELDS
                ),

            rows=bad_substitute,
            baseline=baseline,
        ),
)


bad_duplicate = [
    dict(row)
    for row in resolution_rows
]

bad_duplicate[
    1
][
    "screening_entity_id"
] = (
    bad_duplicate[
        0
    ][
        "screening_entity_id"
    ]
)

expect_error(
    "duplicate carry-forward target prohibited",
    lambda:
        mod.validate_resolution_rows(
            fields=
                list(
                    mod.RESOLUTION_FIELDS
                ),

            rows=bad_duplicate,
            baseline=baseline,
        ),
)


bad_mapping_basis = [
    dict(row)
    for row in resolution_rows
]

bad_mapping_basis[
    0
][
    "mapping_basis"
] = "fuzzy_title_match"

expect_error(
    "non-exact in-baseline mapping basis prohibited",
    lambda:
        mod.validate_resolution_rows(
            fields=
                list(
                    mod.RESOLUTION_FIELDS
                ),

            rows=bad_mapping_basis,
            baseline=baseline,
        ),
)


bad_reassessment = [
    dict(row)
    for row in resolution_rows
]

bad_reassessment[
    0
][
    "scientific_reassessment_performed"
] = "true"

expect_error(
    "scientific reassessment prohibited",
    lambda:
        mod.validate_resolution_rows(
            fields=
                list(
                    mod.RESOLUTION_FIELDS
                ),

            rows=bad_reassessment,
            baseline=baseline,
        ),
)


# If the out-of-baseline DOI appears anywhere in baseline,
# validation must fail closed.
rogue = fake_row(
    "entity:500",
    mod.OUT_OF_BASELINE_DOI,
)

rogue_rows = sorted(
    rows + [rogue],
    key=lambda row:
        row[
            "screening_entity_id"
        ],
)

rogue_by_id = {
    row[
        "screening_entity_id"
    ]:
        row
    for row in rogue_rows
}

rogue_baseline = base.Baseline(
    fields=
        list(
            base.QUEUE_FIELDS
        ),

    rows=rogue_rows,

    by_id=rogue_by_id,

    row_sha256={
        entity_id:
            base.canonical_row_sha256(
                row
            )
        for entity_id, row
        in rogue_by_id.items()
    },

    ready_ids=tuple(
        row[
            "screening_entity_id"
        ]
        for row in rogue_rows
        if row[
            "screening_state"
        ] == "ready"
    ),

    blocked_ids=tuple(
        row[
            "screening_entity_id"
        ]
        for row in rogue_rows
        if row[
            "screening_state"
        ] == "blocked_metadata"
    ),
)

expect_error(
    "out-of-baseline W0A06 DOI appearing in baseline fails closed",
    lambda:
        mod.validate_resolution_rows(
            fields=
                list(
                    mod.RESOLUTION_FIELDS
                ),

            rows=resolution_rows,
            baseline=rogue_baseline,
        ),
)


print(
    "PASS | hostile amendment tests complete"
)
