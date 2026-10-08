#!/usr/bin/env python3

from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import csv
import hashlib
import json
import subprocess


ROOT = Path(
    "experiments/07_comparative_landscape"
)

FUT = Path(
    "results/07_comparative_landscape/"
    "pre_review_triage_future_text_retrieval_v1"
)

FREEZER = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_freeze.py"
)

DESIGN = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1_design.json"
)

DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_TEXT_RECONCILIATION_V1.md"
)

SUMS = (
    ROOT
    / "pre_review_triage_future_text_reconciliation_v1.sha256"
)

DESIGN_PARENT_COMMIT = (
    "1c9abbe08310cb5c914d549e6bf4c41df14befe4"
)


# ------------------------------------------------------------
# Frozen source paths
# ------------------------------------------------------------

INPUT_MANIFEST = (
    FUT
    / "input_manifest.tsv"
)

WAVE_A_RESULT_MANIFEST = (
    FUT
    / "manifest.json"
)

WAVE_A_RESULT_CHECKSUMS = (
    FUT
    / "checksums.sha256"
)

WAVE_A_REQUEST_MANIFEST = (
    FUT
    / "live_wave_a_request_manifest_amendment_001.tsv"
)

WAVE_B_REQUEST_MANIFEST = (
    FUT
    / "live_wave_b_request_manifest.tsv"
)

WAVE_B_DERIVATION = (
    FUT
    / "live_wave_b_derivation.tsv"
)

WAVE_B_RETRIEVAL_MANIFEST = (
    FUT
    / "live_wave_b_retrieval_manifest.json"
)

WAVE_B_RETRIEVAL_CHECKSUMS = (
    FUT
    / "live_wave_b_retrieval_checksums.sha256"
)

WAVE_A_COMPLETION = (
    ROOT
    / "pre_review_triage_future_text_wave_a_retrieval_completion.json"
)

WAVE_B_COMPLETION = (
    ROOT
    / "pre_review_triage_future_text_wave_b_retrieval_completion.json"
)

NORMALIZER = (
    ROOT
    / "triage_pre_review_text_normalizer_v1.py"
)

TRANSPORT = (
    ROOT
    / "retrieve_metadata_resolution_queue.py"
)

FUTURE_WAVE_B_GUARD = (
    ROOT
    / "pre_review_triage_future_text_wave_b_guard_v1.py"
)

FUTURE_WAVE_B_ADAPTER = (
    ROOT
    / "pre_review_triage_future_text_wave_b_transport_evidence_adapter_v1.py"
)

HISTORICAL_RECONCILER = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1.py"
)

HISTORICAL_FAST_TEST = (
    ROOT
    / "test_triage_pre_review_text_reconciliation_v1.py"
)

HISTORICAL_HOSTILE_TEST = (
    ROOT
    / "test_triage_pre_review_text_reconciliation_hostile_v1.py"
)

HISTORICAL_DESIGN = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_design.json"
)

HISTORICAL_AMENDMENT_DESIGN = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_amendment_001_design.json"
)

HISTORICAL_IMPLEMENTATION_DESIGN = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_implementation_design.json"
)

HISTORICAL_IMPLEMENTATION_SUMS = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_implementation.sha256"
)

METADATA_ARCHIVE_CHECKSUMS = Path(
    "results/07_comparative_landscape/"
    "metadata_resolution_retrieval/"
    "checksums.sha256"
)


EXPECTED_HASHES = {
    INPUT_MANIFEST:
        "345c90522a44f9f548fb164618943cac24fb87f7820d52a9048bcfe7a4eec6cf",

    WAVE_A_RESULT_MANIFEST:
        "021942963bce5afd5ada74ad3f2a097ce0c9f0a7f971eec198a665bb0b8ca106",

    WAVE_A_RESULT_CHECKSUMS:
        "6d79c99c164c6d5b1db0cfb6168a8fb4211fa02cbf1866737b953767d7756c3c",

    WAVE_A_REQUEST_MANIFEST:
        "9c5a1b7cda465f0f4a88fc06c612c979af3093f0cecabbe4d8b42576cac30e73",

    WAVE_B_REQUEST_MANIFEST:
        "e6b79c2fff3f31a8155dd7c37188d0ea2c4bd786c7e7de9950570288a2c62d11",

    WAVE_B_DERIVATION:
        "7fc3bd6fee6c5a3539587223ef6459df1ecce41ad670de3929836eef7a6c4474",

    WAVE_B_RETRIEVAL_MANIFEST:
        "f5e68fd14b5c17ed353ab39270bc3f320e11ed3865dd86d840e81d0c44f18043",

    WAVE_B_RETRIEVAL_CHECKSUMS:
        "34ec1ac483d423ce528477300cd492c5a22f7da6196a712de50e2aec5c386b82",

    WAVE_A_COMPLETION:
        "034140d5e6aecc10eb3b1f04f1e6dbc93c857b5cefc9796814345e424cac95ab",

    WAVE_B_COMPLETION:
        "245fd3064374c3211bd921f30eae9cd2df0d60f96abcdb92120a74249e02049b",

    NORMALIZER:
        "cbe66fc9ab406fa5ee3745e099c16250c404a949c0f301e40a7397c285dc459d",

    TRANSPORT:
        "9c8c11edbbec86e5cbf857f25c1bf576a0638ba5cdcf69d1fa2a8b8bfc1a994f",

    FUTURE_WAVE_B_GUARD:
        "60dad0cf516e829e4a33c52d693436662dd40dbae02dc7b67ae830dabc9f8610",

    FUTURE_WAVE_B_ADAPTER:
        "fff2203b57de35b11fbce2678466196dfcc192599978eedf3e12cf18996271d6",

    HISTORICAL_RECONCILER:
        "2383ef19b895056d3b66c78019d1cbd62e830bffa034dffb70424c921244ddad",

    HISTORICAL_FAST_TEST:
        "fb43dde98b8da8e9964ff672fca598141d70d366357f57755774175e97a95014",

    HISTORICAL_HOSTILE_TEST:
        "b7be01254ee62bf13e35c8805af690b2301567522558efae16a6885cf0d40bd1",

    HISTORICAL_DESIGN:
        "a4bad21a4cdafc0e8ad958726e1c694b0a6cab6e568febb71773eedda93eba89",

    HISTORICAL_AMENDMENT_DESIGN:
        "7c670aba3e85b62e16cf391bf41ba8501fbae7548308fec58b39906b95330360",

    HISTORICAL_IMPLEMENTATION_DESIGN:
        "c35f7de39af4fe0cabb6fd345c08f0c0ae9eca11141fea0d9e859db9b72c7f94",

    HISTORICAL_IMPLEMENTATION_SUMS:
        "f382c47cb2aacc6f7d043e093cb9757f511359821d582f336fec6ba0b53dc5e1",

    METADATA_ARCHIVE_CHECKSUMS:
        "f51080de3383cae1981e19c57687e4c8ea0e7f9832316a3936728a23995e8b86",
}


CANONICAL_OUTPUTS = (
    FUT
    / "reconciled_resolution.tsv",

    FUT
    / "reconciled_normalized_text.tsv",

    FUT
    / "reconciliation_summary.json",

    FUT
    / "reconciliation_outputs.sha256",
)


class FreezeError(RuntimeError):
    pass


def sha256_bytes(
    value: bytes,
) -> str:

    return hashlib.sha256(
        value
    ).hexdigest()


def sha256_file(
    path: Path,
) -> str:

    return sha256_bytes(
        path.read_bytes()
    )


def canonical_json_bytes(
    value,
) -> bytes:

    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    ).encode(
        "utf-8"
    )


def read_json(
    path: Path,
) -> dict:

    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        value,
        dict,
    ):
        raise FreezeError(
            f"JSON object required: {path}"
        )

    return value


def read_tsv(
    path: Path,
) -> tuple[list[str], list[dict[str, str]]]:

    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:

        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        rows = list(
            reader
        )

        fields = list(
            reader.fieldnames
            or []
        )

    return fields, rows


def verify_hashes() -> None:

    for path, expected in (
        EXPECTED_HASHES.items()
    ):

        if not path.is_file():

            raise FreezeError(
                "missing frozen dependency: "
                + str(
                    path
                )
            )

        actual = sha256_file(
            path
        )

        if actual != expected:

            raise FreezeError(
                "frozen dependency hash mismatch: "
                + str(
                    path
                )
                + "\nexpected="
                + expected
                + "\nactual="
                + actual
            )


def validate_structure() -> dict:

    input_fields, input_rows = (
        read_tsv(
            INPUT_MANIFEST
        )
    )

    if len(
        input_rows
    ) != 12162:

        raise FreezeError(
            "future input manifest cardinality changed"
        )

    required_input_fields = {
        "retrieval_record_index",
        "screening_entity_id",
    }

    if not required_input_fields.issubset(
        input_fields
    ):

        raise FreezeError(
            "future input manifest schema incompatible"
        )

    input_keys = {
        (
            row[
                "retrieval_record_index"
            ],
            row[
                "screening_entity_id"
            ],
        )
        for row in input_rows
    }

    if len(
        input_keys
    ) != 12162:

        raise FreezeError(
            "future input manifest identity is not unique"
        )


    wave_a_fields, wave_a_rows = (
        read_tsv(
            WAVE_A_REQUEST_MANIFEST
        )
    )

    if len(
        wave_a_rows
    ) != 12147:

        raise FreezeError(
            "Future Wave-A request cardinality changed"
        )

    for field in (
        "request_sequence",
        "retrieval_record_index",
        "screening_entity_id",
        "provider",
        "request_identity_sha256",
    ):

        if field not in wave_a_fields:

            raise FreezeError(
                "Future Wave-A schema missing "
                + field
            )

    wave_a_by_sequence = {
        row[
            "request_sequence"
        ]:
            row
        for row in wave_a_rows
    }

    if len(
        wave_a_by_sequence
    ) != 12147:

        raise FreezeError(
            "Future Wave-A request sequence duplicated"
        )


    derivation_fields, derivation_rows = (
        read_tsv(
            WAVE_B_DERIVATION
        )
    )

    required_derivation_fields = {
        "wave_b_request_sequence",
        "wave_a_request_sequence",
        "retrieval_record_index",
        "screening_entity_id",
        "fallback_reason",
    }

    if not required_derivation_fields.issubset(
        derivation_fields
    ):

        raise FreezeError(
            "Future Wave-B derivation schema incompatible"
        )

    if len(
        derivation_rows
    ) != 40:

        raise FreezeError(
            "Future Wave-B derivation cardinality changed"
        )

    expected_sequences = [
        str(
            value
        )
        for value in range(
            1,
            41,
        )
    ]

    observed_sequences = [
        row[
            "wave_b_request_sequence"
        ]
        for row in derivation_rows
    ]

    if observed_sequences != expected_sequences:

        raise FreezeError(
            "Future Wave-B derivation ordering changed"
        )

    fallback_counts = dict(
        sorted(
            Counter(
                row[
                    "fallback_reason"
                ]
                for row in derivation_rows
            ).items()
        )
    )

    if fallback_counts != {
        "abstract_absent":
            38,

        "verified_not_found":
            2,
    }:

        raise FreezeError(
            "Future Wave-B fallback reasons changed"
        )


    # Every fallback must bind an existing future input row
    # and its frozen Wave-A request.
    primary_provider_counts = Counter()

    for row in derivation_rows:

        key = (
            row[
                "retrieval_record_index"
            ],
            row[
                "screening_entity_id"
            ],
        )

        if key not in input_keys:

            raise FreezeError(
                "Future Wave-B fallback is outside input manifest"
            )

        wave_a_sequence = (
            row[
                "wave_a_request_sequence"
            ]
        )

        if (
            wave_a_sequence
            not in wave_a_by_sequence
        ):

            raise FreezeError(
                "Future Wave-B derivation references "
                "unknown Wave-A sequence"
            )

        wave_a = (
            wave_a_by_sequence[
                wave_a_sequence
            ]
        )

        if (
            wave_a[
                "retrieval_record_index"
            ]
            != row[
                "retrieval_record_index"
            ]
            or wave_a[
                "screening_entity_id"
            ]
            != row[
                "screening_entity_id"
            ]
        ):

            raise FreezeError(
                "Future Wave-B derivation / Wave-A identity mismatch"
            )

        primary_provider_counts[
            wave_a[
                "provider"
            ]
        ] += 1


    wave_b_fields, wave_b_rows = (
        read_tsv(
            WAVE_B_REQUEST_MANIFEST
        )
    )

    if len(
        wave_b_rows
    ) != 40:

        raise FreezeError(
            "Future Wave-B request cardinality changed"
        )

    for field in (
        "request_sequence",
        "retrieval_record_index",
        "screening_entity_id",
        "provider",
        "frozen_route",
        "request_identity_sha256",
    ):

        if field not in wave_b_fields:

            raise FreezeError(
                "Future Wave-B request schema missing "
                + field
            )

    if [
        row[
            "request_sequence"
        ]
        for row in wave_b_rows
    ] != expected_sequences:

        raise FreezeError(
            "Future Wave-B request ordering changed"
        )

    route_counts = dict(
        sorted(
            Counter(
                row[
                    "frozen_route"
                ]
                for row in wave_b_rows
            ).items()
        )
    )

    if route_counts != {
        "exact_doi":
            8,

        "exact_pmid":
            1,

        "exact_work_id":
            31,
    }:

        raise FreezeError(
            "Future Wave-B route population changed"
        )

    if (
        set(
            row[
                "provider"
            ]
            for row in wave_b_rows
        )
        != {
            "openalex",
        }
    ):

        raise FreezeError(
            "Future Wave-B provider population changed"
        )


    for derivation, request in zip(
        derivation_rows,
        wave_b_rows,
        strict=True,
    ):

        if (
            derivation[
                "wave_b_request_sequence"
            ]
            != request[
                "request_sequence"
            ]
        ):

            raise FreezeError(
                "Future Wave-B sequence mapping changed"
            )

        if (
            derivation[
                "retrieval_record_index"
            ]
            != request[
                "retrieval_record_index"
            ]
            or derivation[
                "screening_entity_id"
            ]
            != request[
                "screening_entity_id"
            ]
        ):

            raise FreezeError(
                "Future Wave-B request / derivation identity mismatch"
            )


    retrieval = read_json(
        WAVE_B_RETRIEVAL_MANIFEST
    )

    if (
        retrieval[
            "status"
        ]
        != "FROZEN_COMPLETED_RETRIEVAL"
    ):

        raise FreezeError(
            "Future Wave-B retrieval is not frozen completed"
        )

    execution = (
        retrieval[
            "execution"
        ]
    )

    if (
        execution[
            "completed_request_count"
        ]
        != 40
        or execution[
            "next_request_sequence"
        ]
        != 41
        or execution[
            "execution_status"
        ]
        != "COMPLETED"
    ):

        raise FreezeError(
            "Future Wave-B completion state changed"
        )

    outcomes = (
        retrieval[
            "live_outcomes"
        ]
    )

    if (
        outcomes[
            "transport_terminal_status_counts"
        ]
        != {
            "success":
                40,
        }
    ):

        raise FreezeError(
            "Future Wave-B transport outcomes changed"
        )

    if (
        outcomes[
            "canonical_adapter_status_counts"
        ]
        != {
            "verified_success":
                40,
        }
    ):

        raise FreezeError(
            "Future Wave-B adapter outcomes changed"
        )

    if (
        outcomes[
            "provider_identity_status_counts"
        ]
        != {
            "matched":
                40,
        }
    ):

        raise FreezeError(
            "Future Wave-B provider identities changed"
        )

    if (
        outcomes[
            "checkpoint_ineligible_sequences"
        ]
        != []
        or outcomes[
            "unresolved_fault_sequences"
        ]
        != []
    ):

        raise FreezeError(
            "Future Wave-B retrieval contains unresolved evidence"
        )


    return {
        "future_input_rows":
            12162,

        "future_wave_a_request_rows":
            12147,

        "future_terminal_offline_rows":
            15,

        "future_wave_b_fallback_rows":
            40,

        "future_wave_b_fallback_reason_counts":
            fallback_counts,

        "future_wave_b_route_counts":
            route_counts,

        "future_wave_b_primary_provider_counts":
            dict(
                sorted(
                    primary_provider_counts.items()
                )
            ),

        "future_wave_b_transport_status_counts": {
            "success":
                40,
        },

        "future_wave_b_adapter_status_counts": {
            "verified_success":
                40,
        },

        "future_wave_b_identity_status_counts": {
            "matched":
                40,
        },
    }


def build():

    verify_hashes()

    structure = (
        validate_structure()
    )

    for path in CANONICAL_OUTPUTS:

        if path.exists():

            raise FreezeError(
                "canonical reconciliation output already exists: "
                + str(
                    path
                )
            )


    source_bindings = {
        str(path):
            digest
        for path, digest
        in sorted(
            EXPECTED_HASHES.items(),
            key=lambda item:
                str(
                    item[0]
                ),
        )
    }


    design = {
        "design_id":
            "PRE_REVIEW_TRIAGE_FUTURE_TEXT_RECONCILIATION_V1",

        "schema_version":
            1,

        "status":
            "FROZEN_PRE_IMPLEMENTATION",

        "design_parent_commit":
            DESIGN_PARENT_COMMIT,

        "purpose":
            (
                "Offline deterministic reconciliation of the "
                "frozen 12,162-record future pre-review text "
                "retrieval cascade after completed Future Wave A "
                "and Future Wave B retrieval."
            ),

        "architecture": {
            "implementation_strategy":
                "future_specific_module",

            "implementation_module":
                (
                    "experiments/07_comparative_landscape/"
                    "pre_review_triage_future_text_reconciliation_v1.py"
                ),

            "focused_test_module":
                (
                    "experiments/07_comparative_landscape/"
                    "test_pre_review_triage_future_text_reconciliation_v1.py"
                ),

            "hostile_test_module":
                (
                    "experiments/07_comparative_landscape/"
                    "test_pre_review_triage_future_text_reconciliation_hostile_v1.py"
                ),

            "historical_reconciler_role":
                "semantic_reference_only",

            "historical_reconciler_modification_permitted":
                False,

            "historical_tests_modification_permitted":
                False,

            "future_wave_a_archive_modification_permitted":
                False,

            "future_wave_b_archive_modification_permitted":
                False,
        },

        "known_structural_population":
            structure,

        "source_bindings":
            source_bindings,

        "reconciliation_semantics": {
            "one_resolution_row_per_input_record":
                True,

            "resolution_row_count":
                12162,

            "resolution_ordering":
                "ascending_retrieval_record_index",

            "resolution_lanes": [
                "offline_cache",
                "wave_a_primary",
                "wave_b_fallback",
            ],

            "frozen_normalizer_only":
                True,

            "wave_b_fallback_is_one_to_one":
                True,

            "wave_b_fallback_source_reason_values": [
                "abstract_absent",
                "verified_not_found",
            ],

            "historical_fallback_labels_may_only_be_used_after_primary_provider_validation":
                True,

            "abstract_absence_is_scientific_exclusion_evidence":
                False,

            "provider_not_found_is_scientific_exclusion_evidence":
                False,

            "retrieval_failure_is_scientific_exclusion_evidence":
                False,

            "title_only_rows_promoted_to_model_text":
                False,

            "usable_abstract_rows_enter_normalized_text":
                True,

            "abstract_absent_rows_enter_normalized_text":
                False,

            "wave_b_success_must_be_reconstructed_from_frozen_raw_archive":
                True,

            "wave_b_durable_adapter_evidence_must_match_reconstruction":
                True,
        },

        "preimplementation_unknowns": {
            "final_abstract_status_counts":
                None,

            "final_usable_abstract_total":
                None,

            "final_abstract_absent_total":
                None,

            "final_normalized_text_row_count":
                None,

            "final_terminal_source_counts":
                None,

            "final_terminal_source_status_counts":
                None,

            "final_output_sha256":
                None,

            "parser_or_position_gap_count":
                None,

            "reason":
                (
                    "Transport success does not establish whether "
                    "an OpenAlex record contains a usable abstract. "
                    "These values must be measured only by the "
                    "frozen normalizer during deterministic temporary "
                    "reconciliation builds."
                ),
        },

        "output_contract": {
            "canonical_output_root":
                str(
                    FUT
                ),

            "outputs": [
                "reconciled_resolution.tsv",
                "reconciled_normalized_text.tsv",
                "reconciliation_summary.json",
                "reconciliation_outputs.sha256",
            ],

            "historical_column_schemas_preserved":
                True,

            "canonical_production_write_permitted_by_this_design":
                False,

            "temporary_output_generation_permitted_during_implementation_validation":
                True,

            "temporary_builds_must_not_modify_frozen_retrieval_archives":
                True,

            "temporary_build_count_required_before_implementation_freeze":
                2,

            "independent_temporary_builds_must_be_byte_identical":
                True,

            "canonical_write_requires_future_implementation_freeze":
                True,

            "canonical_write_requires_exact_expected_output_hashes":
                True,
        },

        "implementation_validation_requirements": [
            "verify every source binding before reconciliation",
            "fail closed if future input cardinality is not 12162",
            "fail closed if Future Wave A request cardinality is not 12147",
            "fail closed if Future Wave B derivation cardinality is not 40",
            "fail closed unless Future Wave B fallback reasons are exactly 38 abstract_absent and 2 verified_not_found",
            "fail closed unless Future Wave B route counts are exactly 31 exact_work_id, 8 exact_doi and 1 exact_pmid",
            "fail closed unless all 40 Future Wave B retrieval records remain success, verified_success and matched",
            "verify every Future Wave B request is joined one-to-one to its derivation row",
            "verify every Future Wave B fallback maps to the same retrieval_record_index and screening_entity_id as its frozen Wave A request",
            "reverify Future Wave B raw transport archives before normalization",
            "reconstruct Future Wave B durable adapter evidence and require byte-identical equality",
            "use only triage_pre_review_text_normalizer_v1",
            "preserve historical reconciliation output schemas",
            "do not place abstract_absent rows in reconciled_normalized_text.tsv",
            "do not promote title-only rows to model text",
            "do not treat absence, not-found or retrieval failure as scientific exclusion evidence",
            "fail closed on duplicate or missing input identities",
            "fail closed on parser or position gaps before any canonical write",
            "perform two independent temporary builds",
            "require those temporary builds to be byte-identical",
            "derive final abstract-status counts and final output SHA256 values from the temporary builds rather than predeclaring them",
            "run focused and hostile future-specific reconciliation tests",
            "preserve all historical development reconciliation files byte-identically",
            "preserve Future Wave A and Future Wave B retrieval archives byte-identically",
        ],

        "safety_boundaries": {
            "network_execution_permitted":
                False,

            "production_write_permitted":
                False,

            "raw_archive_mutation_permitted":
                False,

            "future_wave_a_mutation_permitted":
                False,

            "future_wave_b_mutation_permitted":
                False,

            "scientific_decision_permitted":
                False,

            "scientific_label_addition_permitted":
                False,

            "abstract_absence_as_exclusion_evidence_permitted":
                False,

            "blind_validation_content_use_permitted":
                False,

            "future_scoring_permitted":
                False,

            "model_fit_permitted":
                False,

            "threshold_selection_permitted":
                False,
        },

        "next_gate":
            (
                "IMPLEMENT_AND_HOSTILE_TEST_FUTURE_TEXT_"
                "RECONCILIATION_V1_WITH_TWO_INDEPENDENT_"
                "TEMPORARY_BUILDS"
            ),
    }


    design_body = (
        canonical_json_bytes(
            design
        )
    )

    design_sha = (
        sha256_bytes(
            design_body
        )
    )


    doc = f"""# Pre-review triage future text reconciliation v1

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design governs offline deterministic reconciliation of the frozen
12,162-record future pre-review text retrieval population after completion of
Future Wave A and Future Wave B.

## Architecture

A future-specific reconciliation module must be implemented.

The historical development reconciliation implementation is a semantic reference
only and must remain byte-identical. It is not directly executable for this
population because it is frozen around the historical 4,499-record population
and 25-request development Wave B.

## Frozen structural population

- total future input records: 12,162
- Future Wave A live requests: 12,147
- terminal offline rows: 15
- Future Wave B fallback rows: 40
- Future Wave B fallback reasons:
  - `abstract_absent`: 38
  - `verified_not_found`: 2
- Future Wave B routes:
  - `exact_work_id`: 31
  - `exact_doi`: 8
  - `exact_pmid`: 1
- Future Wave B retrieval:
  - transport `success`: 40
  - adapter `verified_success`: 40
  - provider identity `matched`: 40

## Deliberately unresolved before implementation

This design does not predeclare the final number of usable abstracts,
abstract-absent records, normalized-text rows, terminal-source status counts, or
canonical output hashes.

All 40 Future Wave B requests succeeded at the transport and identity layers,
but that does not establish whether each returned OpenAlex record contains a
usable abstract.

Those values may be determined only by applying the frozen normalizer during
future-specific deterministic reconciliation validation.

## Reconciliation semantics

The future implementation must retain the historical reconciliation semantics:

- exactly one resolution row per input record;
- resolution ordered by ascending retrieval-record index;
- only usable abstracts enter the normalized-text output;
- abstract absence, provider not-found and retrieval failure are provenance
  states, not scientific exclusion evidence;
- title-only records are not promoted to model text;
- frozen retrieval evidence must be independently verified before use.

Every Future Wave B raw archive must be reverified and every durable adapter
evidence object must reconstruct exactly before its body is normalized.

## Validation before canonical output

Implementation validation must use two independent temporary builds.

The two builds must be byte-identical.

Only after those builds establish the actual future reconciliation counts and
output hashes may an implementation freeze authorize a later controlled
canonical output write.

This design itself does not authorize canonical output generation.

## Safety boundary

No network access is permitted.

No Future Wave A or Future Wave B retrieval artifact may be modified.

No scientific screening decision, future score, model fit, threshold selection,
or blind-validation content use is permitted.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_FUTURE_TEXT_RECONCILIATION_V1_WITH_TWO_INDEPENDENT_TEMPORARY_BUILDS`
"""

    doc_body = (
        doc.encode(
            "utf-8"
        )
    )

    doc_sha = (
        sha256_bytes(
            doc_body
        )
    )

    freezer_sha = (
        sha256_file(
            FREEZER
        )
    )


    checksum_records = {
        str(
            FREEZER
        ):
            freezer_sha,

        str(
            DESIGN
        ):
            design_sha,

        str(
            DOC
        ):
            doc_sha,
    }

    checksum_records.update(
        source_bindings
    )

    sums_body = "".join(
        digest
        + "  "
        + path
        + "\n"
        for path, digest
        in sorted(
            checksum_records.items()
        )
    ).encode(
        "utf-8"
    )


    return (
        {
            DESIGN:
                design_body,

            DOC:
                doc_body,

            SUMS:
                sums_body,
        },
        {
            "design_sha256":
                design_sha,

            "document_sha256":
                doc_sha,

            "freezer_sha256":
                freezer_sha,
        },
        structure,
    )


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--verify-only",
        action="store_true",
    )

    args = parser.parse_args()


    head = subprocess.check_output(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()

    if (
        head
        != DESIGN_PARENT_COMMIT
    ):

        raise FreezeError(
            "wrong design parent HEAD: "
            + head
        )


    outputs, hashes, structure = (
        build()
    )


    if args.verify_only:

        for path, expected in (
            outputs.items()
        ):

            if not path.is_file():

                raise FreezeError(
                    "missing design-freeze output: "
                    + str(
                        path
                    )
                )

            if (
                path.read_bytes()
                != expected
            ):

                raise FreezeError(
                    "design-freeze output does not reproduce "
                    "byte-identically: "
                    + str(
                        path
                    )
                )

        print(
            "PASS | future reconciliation design "
            "reproduces byte-identically"
        )

    else:

        for path in outputs:

            if path.exists():

                raise FreezeError(
                    "refusing overwrite: "
                    + str(
                        path
                    )
                )

        for path, body in (
            outputs.items()
        ):

            with path.open(
                "xb"
            ) as handle:

                handle.write(
                    body
                )

        print(
            "PASS | future reconciliation "
            "design freeze created"
        )


    for name in sorted(
        hashes
    ):

        print(
            name,
            "=",
            hashes[
                name
            ],
        )


    print(
        "future_input_rows =",
        structure[
            "future_input_rows"
        ],
    )

    print(
        "future_wave_a_request_rows =",
        structure[
            "future_wave_a_request_rows"
        ],
    )

    print(
        "future_terminal_offline_rows =",
        structure[
            "future_terminal_offline_rows"
        ],
    )

    print(
        "future_wave_b_fallback_rows =",
        structure[
            "future_wave_b_fallback_rows"
        ],
    )

    print(
        "future_wave_b_fallback_reason_counts =",
        json.dumps(
            structure[
                "future_wave_b_fallback_reason_counts"
            ],
            sort_keys=True,
        ),
    )

    print(
        "future_wave_b_route_counts =",
        json.dumps(
            structure[
                "future_wave_b_route_counts"
            ],
            sort_keys=True,
        ),
    )

    print(
        "future_wave_b_primary_provider_counts =",
        json.dumps(
            structure[
                "future_wave_b_primary_provider_counts"
            ],
            sort_keys=True,
        ),
    )

    print(
        "CANONICAL_RECONCILIATION_WRITE_AUTHORIZED=NO"
    )

    print(
        "NETWORK_AUTHORIZED=NO"
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
