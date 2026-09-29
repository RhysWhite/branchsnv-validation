from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import json
import subprocess
import sys


ROOT = Path(
    "experiments/07_comparative_landscape"
)

RROOT = Path(
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1"
)

EXPECTED_PARENT = (
    "c767211bec514e3b5396e202aa2a40ccfb1dc138"
)

FREEZE = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_freeze.py"
)

DESIGN = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1_design.json"
)

DOCUMENT = (
    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_RECONCILIATION_V1.md"
)

CHECKSUM = (
    ROOT
    / "triage_pre_review_text_reconciliation_v1.sha256"
)


DESIGN_PATHS = {
    str(FREEZE),
    str(DESIGN),
    str(DOCUMENT),
    str(CHECKSUM),
}


PLANNED_OUTPUTS = {
    "resolution":
        RROOT
        / "reconciled_resolution.tsv",

    "normalized_text":
        RROOT
        / "reconciled_normalized_text.tsv",

    "summary":
        RROOT
        / "reconciliation_summary.json",

    "checksums":
        RROOT
        / "reconciliation_outputs.sha256",
}


NORMALIZED_TEXT_COLUMNS = [
    "retrieval_record_index",
    "screening_entity_id",
    "provider_used",
    "provider_lookup_type",
    "provider_record_id",
    "source_body_sha256",
    "provider_identity_status",
    "parser_status",
    "abstract_status",
    "title_text",
    "abstract_text",
    "abstract_section_metadata_json",
]


RESOLUTION_COLUMNS = [
    "retrieval_record_index",
    "screening_entity_id",
    "resolution_lane",
    "provider_used",
    "provider_lookup_type",
    "provider_record_id",
    "source_body_sha256",
    "provider_identity_status",
    "parser_status",
    "abstract_status",
    "wave_a_request_sequence",
    "wave_a_request_identity_sha256",
    "wave_b_request_sequence",
    "wave_b_request_identity_sha256",
    "fallback_reason",
    "normalized_text_present",
]


SOURCE_PATHS = [
    ROOT
    / "triage_pre_review_text_normalizer_v1.py",

    ROOT
    / "triage_pre_review_text_retrieval_v1_design.json",

    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_RETRIEVAL_V1.md",

    ROOT
    / "triage_pre_review_text_wave_a_guard_v1.py",

    ROOT
    / "triage_pre_review_text_wave_a_transport_evidence_adapter_v1.py",

    ROOT
    / "triage_pre_review_text_wave_b_guard_v1.py",

    ROOT
    / "triage_pre_review_text_wave_b_transport_evidence_adapter_v1.py",

    ROOT
    / "retrieve_metadata_resolution_queue.py",

    RROOT
    / "input_manifest.tsv",

    RROOT
    / "offline_cache_resolution.tsv",

    RROOT
    / "offline_cached_normalized_text.tsv",

    RROOT
    / "offline_network_requirements.tsv",

    RROOT
    / "live_wave_a_request_manifest.tsv",

    RROOT
    / "live_wave_a"
    / "completion_receipt.json",

    RROOT
    / "live_wave_b_request_manifest.tsv",

    RROOT
    / "live_wave_b_derivation.tsv",

    RROOT
    / "live_wave_b"
    / "completion_receipt.json",
]


KNOWN_HASHES = {
    str(
        ROOT
        / "triage_pre_review_text_normalizer_v1.py"
    ):
        (
            "cbe66fc9ab406fa5ee3745e099c16250"
            "c404a949c0f301e40a7397c285dc459d"
        ),

    str(
        RROOT
        / "input_manifest.tsv"
    ):
        (
            "4e5ba0313e008a58e968a9368ea90b6f"
            "db70049b866003742ed1c967c31120ba"
        ),

    str(
        RROOT
        / "live_wave_a_request_manifest.tsv"
    ):
        (
            "91a87f2d8a2bfc00ead9a5f1b6e6fca"
            "f850666573583bb07317a1416d446211d"
        ),

    str(
        RROOT
        / "live_wave_b_request_manifest.tsv"
    ):
        (
            "f099f86cce2321ab07d639aeef557014"
            "585faf49e2306a09f3fe40119535f0a6"
        ),
}


EXPECTED_ROW_COUNTS = {
    "input_manifest":
        4499,

    "offline_cache_resolution":
        4499,

    "offline_cached_normalized_text":
        3,

    "offline_network_requirements":
        4490,

    "wave_a_request_manifest":
        4490,

    "wave_b_request_manifest":
        25,

    "wave_b_derivation":
        25,
}


EXPECTED_RECONCILIATION = {
    "total_records":
        4499,

    "usable_abstract_total":
        4190,

    "abstract_absent_total":
        309,

    "abstract_status_counts": {
        "usable_abstract_pubmed":
            3931,

        "usable_abstract_openalex":
            259,

        "abstract_absent":
            309,
    },

    "terminal_source_counts": {
        "offline_cache_openalex":
            9,

        "wave_a_pubmed":
            3931,

        "wave_a_openalex":
            534,

        "wave_b_openalex_after_pubmed_abstract_absent":
            24,

        "wave_b_openalex_after_pubmed_verified_not_found":
            1,
    },

    "terminal_source_status_counts": {
        "offline_cache_openalex": {
            "usable_abstract_openalex":
                3,
            "abstract_absent":
                6,
        },

        "wave_a_pubmed": {
            "usable_abstract_pubmed":
                3931,
        },

        "wave_a_openalex": {
            "usable_abstract_openalex":
                248,
            "abstract_absent":
                286,
        },

        "wave_b_openalex_after_pubmed_abstract_absent": {
            "usable_abstract_openalex":
                7,
            "abstract_absent":
                17,
        },

        "wave_b_openalex_after_pubmed_verified_not_found": {
            "usable_abstract_openalex":
                1,
        },
    },

    "wave_b_fallback_reason_counts": {
        "pubmed_abstract_absent":
            24,

        "pubmed_verified_not_found":
            1,
    },

    "parser_or_position_gap_count":
        0,
}


def sha256_file(
    path: Path,
) -> str:

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def read_tsv(
    path: Path,
) -> tuple[list[str], list[dict[str, str]]]:

    with path.open(
        "r",
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

        return (
            list(
                reader.fieldnames
                or []
            ),
            rows,
        )


def git(
    *args: str,
) -> str:

    return subprocess.check_output(
        [
            "git",
            *args,
        ],
        text=True,
    ).strip()


def repository_position() -> str:

    head = git(
        "rev-parse",
        "HEAD",
    )

    if head == EXPECTED_PARENT:

        return (
            "PRE_COMMIT_PARENT"
        )

    parent = git(
        "rev-parse",
        "HEAD^",
    )

    if parent != EXPECTED_PARENT:

        raise RuntimeError(
            "Repository is neither the frozen parent "
            "nor its direct design-freeze child"
        )

    changed = {
        line
        for line in git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).splitlines()
        if line.strip()
    }

    if changed != DESIGN_PATHS:

        raise RuntimeError(
            "Post-commit design-freeze path set differs: "
            + repr(
                {
                    "missing":
                        sorted(
                            DESIGN_PATHS
                            - changed
                        ),
                    "unexpected":
                        sorted(
                            changed
                            - DESIGN_PATHS
                        ),
                }
            )
        )

    return (
        "COMMITTED_FREEZE"
    )


def validate_source_state() -> dict[str, str]:

    if git(
        "status",
        "--porcelain",
        "--untracked-files=no",
    ):
        raise RuntimeError(
            "Tracked working tree is not clean"
        )

    for path in SOURCE_PATHS:

        if not path.is_file():

            raise RuntimeError(
                "Missing frozen source: "
                + str(
                    path
                )
            )

    source_hashes = {
        str(path):
            sha256_file(
                path
            )
        for path in SOURCE_PATHS
    }

    for path, expected in (
        KNOWN_HASHES.items()
    ):

        observed = source_hashes[
            path
        ]

        if observed != expected:

            raise RuntimeError(
                "Known frozen source hash changed: "
                + path
            )

    for path in (
        PLANNED_OUTPUTS.values()
    ):

        if path.exists():

            raise RuntimeError(
                "Final reconciliation output already exists: "
                + str(
                    path
                )
            )

    tables = {
        "input_manifest":
            RROOT
            / "input_manifest.tsv",

        "offline_cache_resolution":
            RROOT
            / "offline_cache_resolution.tsv",

        "offline_cached_normalized_text":
            RROOT
            / "offline_cached_normalized_text.tsv",

        "offline_network_requirements":
            RROOT
            / "offline_network_requirements.tsv",

        "wave_a_request_manifest":
            RROOT
            / "live_wave_a_request_manifest.tsv",

        "wave_b_request_manifest":
            RROOT
            / "live_wave_b_request_manifest.tsv",

        "wave_b_derivation":
            RROOT
            / "live_wave_b_derivation.tsv",
    }

    for name, path in (
        tables.items()
    ):

        _header, rows = read_tsv(
            path
        )

        expected = (
            EXPECTED_ROW_COUNTS[
                name
            ]
        )

        if len(
            rows
        ) != expected:

            raise RuntimeError(
                f"{name} row count changed: "
                f"{len(rows)} != {expected}"
            )

    cached_header, _ = read_tsv(
        RROOT
        / "offline_cached_normalized_text.tsv"
    )

    if (
        cached_header
        != NORMALIZED_TEXT_COLUMNS
    ):

        raise RuntimeError(
            "Existing normalized-text schema changed"
        )

    for wave, expected_count in (
        (
            "live_wave_a",
            4490,
        ),
        (
            "live_wave_b",
            25,
        ),
    ):

        receipt = json.loads(
            (
                RROOT
                / wave
                / "completion_receipt.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        if (
            receipt.get(
                "status"
            )
            != "COMPLETED"
        ):

            raise RuntimeError(
                wave
                + " completion receipt is not COMPLETED"
            )

        if (
            receipt.get(
                "completed_request_count"
            )
            != expected_count
        ):

            raise RuntimeError(
                wave
                + " completed request count changed"
            )

    return source_hashes


def expected_design(
    source_hashes: dict[str, str],
) -> dict:

    return {
        "schema_version":
            1,

        "design_name":
            "triage_pre_review_text_reconciliation_v1",

        "status":
            "FROZEN_PRE_IMPLEMENTATION",

        "design_parent_commit":
            EXPECTED_PARENT,

        "purpose":
            (
                "Offline deterministic reconciliation of the "
                "frozen 4,499-record pre-review text retrieval "
                "cascade after completed Wave A and Wave B."
            ),

        "source_hashes":
            source_hashes,

        "expected_reconciliation":
            EXPECTED_RECONCILIATION,

        "output_contract": {
            "resolution": {
                "path":
                    str(
                        PLANNED_OUTPUTS[
                            "resolution"
                        ]
                    ),

                "row_count":
                    4499,

                "columns":
                    RESOLUTION_COLUMNS,

                "one_row_per_input_manifest_record":
                    True,

                "ordering":
                    "ascending_retrieval_record_index",
            },

            "normalized_text": {
                "path":
                    str(
                        PLANNED_OUTPUTS[
                            "normalized_text"
                        ]
                    ),

                "row_count":
                    4190,

                "columns":
                    NORMALIZED_TEXT_COLUMNS,

                "included_abstract_statuses": [
                    "usable_abstract_pubmed",
                    "usable_abstract_openalex",
                ],

                "excluded_from_this_text_table": [
                    "abstract_absent",
                ],

                "ordering":
                    "ascending_retrieval_record_index",

                "title_only_rows_promoted_to_model_text":
                    False,

                "minimum_abstract_length_threshold":
                    None,
            },

            "summary": {
                "path":
                    str(
                        PLANNED_OUTPUTS[
                            "summary"
                        ]
                    ),

                "must_include":
                    [
                        "source_hashes",
                        "output_hashes",
                        "row_counts",
                        "abstract_status_counts",
                        "terminal_source_counts",
                        "fallback_reason_counts",
                        "safety_boundaries",
                    ],

                "title_or_abstract_text_permitted":
                    False,
            },

            "checksums": {
                "path":
                    str(
                        PLANNED_OUTPUTS[
                            "checksums"
                        ]
                    ),

                "must_cover": [
                    str(
                        PLANNED_OUTPUTS[
                            "resolution"
                        ]
                    ),
                    str(
                        PLANNED_OUTPUTS[
                            "normalized_text"
                        ]
                    ),
                    str(
                        PLANNED_OUTPUTS[
                            "summary"
                        ]
                    ),
                ],
            },
        },

        "resolution_semantics": {
            "resolution_lane_values": [
                "offline_cache",
                "wave_a_primary",
                "wave_b_fallback",
            ],

            "wave_b_fallback_reason_values": [
                "pubmed_abstract_absent",
                "pubmed_verified_not_found",
            ],

            "normalized_text_present_values": [
                "0",
                "1",
            ],

            "abstract_absence_is_scientific_exclusion_evidence":
                False,

            "provider_not_found_is_scientific_exclusion_evidence":
                False,

            "retrieval_failure_is_scientific_exclusion_evidence":
                False,
        },

        "leakage_boundary": {
            "scientific_decisions_permitted":
                False,

            "scientific_labels_permitted":
                False,

            "review_evidence_permitted":
                False,

            "operator_fields_permitted":
                False,

            "notes_fields_permitted":
                False,

            "model_scores_permitted":
                False,

            "thresholds_permitted":
                False,

            "batch_identifier_as_feature_permitted":
                False,

            "blind_validation_content_used":
                False,

            "future_universe_scored":
                False,
        },

        "execution_boundary": {
            "network_permitted":
                False,

            "production_ledger_write_permitted":
                False,

            "raw_archive_modification_permitted":
                False,

            "wave_a_archive_modification_permitted":
                False,

            "wave_b_archive_modification_permitted":
                False,

            "reconciliation_outputs_are_derived_only":
                True,
        },

        "implementation_gate": {
            "next_gate":
                (
                    "IMPLEMENT_AND_HOSTILE_TEST_OFFLINE_"
                    "TRIAGE_PRE_REVIEW_TEXT_RECONCILIATION_V1"
                ),

            "requirements": [
                (
                    "reconstruct all 4,499 terminal cascade "
                    "outcomes from frozen sources"
                ),
                (
                    "verify Wave A and Wave B durable evidence "
                    "through native frozen adapters before use"
                ),
                (
                    "apply only the checksum-pinned frozen "
                    "PubMed/OpenAlex normalizer"
                ),
                (
                    "reproduce exactly 4,190 usable abstracts "
                    "and 309 abstract-absent records"
                ),
                (
                    "reproduce all frozen provider/lane/fallback "
                    "counts exactly"
                ),
                (
                    "write normalized text only for usable "
                    "abstract statuses"
                ),
                (
                    "preserve every abstract-absent record in "
                    "the 4,499-row resolution table"
                ),
                (
                    "fail closed on body/evidence/identity/"
                    "checksum mismatch"
                ),
                (
                    "prove deterministic byte-identical output "
                    "across independent temporary rebuilds"
                ),
                (
                    "prove implementation performs no network "
                    "request"
                ),
                (
                    "prove implementation does not read blind "
                    "validation content"
                ),
                (
                    "prove output contains no scientific labels, "
                    "review evidence, scores, thresholds, notes "
                    "or operator fields"
                ),
                (
                    "prove Wave A/Wave B raw archives remain "
                    "byte-identical"
                ),
                (
                    "prove production ledger boundary remains "
                    "unchanged"
                ),
                (
                    "freeze implementation before controlled "
                    "generation of final derived artifacts"
                ),
            ],
        },
    }


def write_candidate() -> None:

    position = repository_position()

    if (
        position
        != "PRE_COMMIT_PARENT"
    ):
        raise RuntimeError(
            "Candidate may only be written at frozen parent"
        )

    for path in (
        DESIGN,
        DOCUMENT,
        CHECKSUM,
    ):

        if path.exists():

            raise RuntimeError(
                "Refusing to overwrite existing design artifact: "
                + str(
                    path
                )
            )

    source_hashes = (
        validate_source_state()
    )

    design = expected_design(
        source_hashes
    )

    DESIGN.write_text(
        json.dumps(
            design,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    doc = f"""# Triage pre-review text reconciliation v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This freeze defines the offline deterministic reconciliation layer
after completed Wave A and Wave B retrieval.

It creates no network authority, performs no scientific screening,
fits no model, selects no threshold, accesses no blind-validation
content, and permits no production-ledger mutation.

## Frozen population

- Retrieval-lane records: 4,499
- Wave A records: 4,490
- No-network cached records: 9
- Wave B PubMed-to-OpenAlex fallbacks: 25
- Final usable abstracts: 4,190
- Final verified abstract-absent records: 309

Final abstract statuses:

- `usable_abstract_pubmed`: 3,931
- `usable_abstract_openalex`: 259
- `abstract_absent`: 309

## Frozen source provenance

Terminal source counts:

- offline cached OpenAlex: 9
- Wave A PubMed: 3,931
- Wave A OpenAlex: 534
- Wave B OpenAlex after PubMed abstract absence: 24
- Wave B OpenAlex after verified PubMed not-found: 1

Wave B fallback reasons:

- `pubmed_abstract_absent`: 24
- `pubmed_verified_not_found`: 1

There are no accepted parser faults, OpenAlex position-gap states,
provider-identity mismatches, or unresolved transport states in the
frozen reconciled population.

## Planned derived outputs

### Resolution table

`{PLANNED_OUTPUTS["resolution"]}`

Exactly 4,499 rows, one for every retrieval input record, ordered by
`retrieval_record_index`.

It preserves retrieval provenance and terminal abstract state. An
`abstract_absent` row remains present and must not be converted into a
scientific exclusion.

### Normalized-text table

`{PLANNED_OUTPUTS["normalized_text"]}`

Exactly 4,190 rows.

The schema is deliberately identical to the existing frozen
`offline_cached_normalized_text.tsv` schema.

Only `usable_abstract_pubmed` and `usable_abstract_openalex` rows are
written to this table. Title-only/abstract-absent records are not
silently promoted to primary model text in v1.

No minimum abstract-length threshold is introduced.

### Summary and checksums

`{PLANNED_OUTPUTS["summary"]}`

`{PLANNED_OUTPUTS["checksums"]}`

The summary contains counts, hashes and provenance only; it contains
no title or abstract text.

## Scientific boundary

Retrieval failure, provider absence, verified provider not-found and
abstract absence are not scientific evidence for exclusion.

This reconciliation layer may not contain scientific decisions,
scientific labels, review evidence, operator fields, notes, model
scores or thresholds.

The blind validation content is not used.

## Archive boundary

Wave A and Wave B raw archives are immutable inputs.

The implementation must fail closed on any body, checksum, request
identity, evidence or provider-identity mismatch.

No network request is permitted during reconciliation.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_OFFLINE_TRIAGE_PRE_REVIEW_TEXT_RECONCILIATION_V1`

Final derived outputs must not be generated until the offline
reconciler and its deterministic/hostile tests are implemented,
audited and frozen.
"""

    DOCUMENT.write_text(
        doc,
        encoding="utf-8",
    )

    checksum_lines = []

    for path in (
        FREEZE,
        DESIGN,
        DOCUMENT,
    ):

        checksum_lines.append(
            f"{sha256_file(path)}  {path}"
        )

    CHECKSUM.write_text(
        "\n".join(
            checksum_lines
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "PASS | reconciliation design-freeze candidate written"
    )


def validate_candidate() -> None:

    position = repository_position()

    source_hashes = (
        validate_source_state()
    )

    if not DESIGN.is_file():
        raise RuntimeError(
            "Design JSON missing"
        )

    if not DOCUMENT.is_file():
        raise RuntimeError(
            "Human-readable design missing"
        )

    if not CHECKSUM.is_file():
        raise RuntimeError(
            "Design checksum manifest missing"
        )

    observed = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    expected = expected_design(
        source_hashes
    )

    if observed != expected:

        raise RuntimeError(
            "Design JSON differs from frozen expected object"
        )

    lines = [
        line
        for line in CHECKSUM.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    if len(
        lines
    ) != 3:

        raise RuntimeError(
            "Checksum manifest must contain exactly 3 entries"
        )

    expected_targets = {
        str(FREEZE),
        str(DESIGN),
        str(DOCUMENT),
    }

    observed_targets = set()

    for line in lines:

        digest, path_text = (
            line.split(
                None,
                1,
            )
        )

        path_text = (
            path_text.strip()
        )

        path = Path(
            path_text
        )

        observed_targets.add(
            path_text
        )

        if (
            sha256_file(
                path
            )
            != digest
        ):

            raise RuntimeError(
                "Design checksum mismatch: "
                + path_text
            )

    if (
        observed_targets
        != expected_targets
    ):

        raise RuntimeError(
            "Design checksum target set differs"
        )

    print(
        "PASS | repository position =",
        position,
    )

    print(
        "PASS | reconciliation design freeze validates"
    )


def main() -> None:

    if (
        len(
            sys.argv
        )
        != 2
    ):

        raise SystemExit(
            "usage: "
            + str(FREEZE)
            + " --write|--validate"
        )

    if sys.argv[1] == "--write":

        write_candidate()

    elif sys.argv[1] == "--validate":

        validate_candidate()

    else:

        raise SystemExit(
            "unknown argument"
        )


if __name__ == "__main__":
    main()
