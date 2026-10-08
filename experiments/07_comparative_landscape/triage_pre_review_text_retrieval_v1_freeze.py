from __future__ import annotations

from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(
    "experiments/07_comparative_landscape"
)

RESULT_ROOT = Path(
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1"
)

MANIFEST = (
    RESULT_ROOT
    / "input_manifest.tsv"
)

DESIGN = (
    ROOT
    / "triage_pre_review_text_retrieval_v1_design.json"
)

DOCUMENT = (
    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_RETRIEVAL_V1.md"
)


EXPECTED_PRODUCTION = {
    "ledger_sha256":
        "f7175d03bb559a8996e7a2fb1aba3959abab87429b86adbd19df74f0f0cbf45e",
    "event_count":
        2011,
}


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


def canonical_row_sha256(
    row: dict[str, str],
) -> str:

    value = json.dumps(
        row,
        sort_keys=True,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    ).encode(
        "utf-8"
    )

    return sha256_bytes(
        value
    )


def git_head() -> str:

    return subprocess.check_output(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()


# ============================================================
# Load frozen screening infrastructure.
# ============================================================

layer = (
    ROOT
    / "c000001_campaign_execution_v4.py"
)

spec = importlib.util.spec_from_file_location(
    "campaign",
    layer,
)

assert spec and spec.loader

m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

guard = m.load_guard()

boundary = m.validate_production_boundary()

assert boundary == EXPECTED_PRODUCTION


queue_fields, queue = guard.read_tsv(
    m.QUEUE
)

_, membership = guard.read_tsv(
    m.EXECUTION_ROOT
    / "batch_membership.tsv"
)

_, ledger = guard.read_tsv(
    m.LEDGER
)


queue_by_id = {
    row[
        "screening_entity_id"
    ]: row
    for row in queue
}

membership_by_id = {
    row[
        "screening_entity_id"
    ]: row
    for row in membership
}

membership_ids = set(
    membership_by_id
)


# ============================================================
# Reconstruct exact development labels.
#
# Labels are used ONLY to determine membership of the already
# frozen development corpus. They are never written to the
# retrieval manifest.
# ============================================================

POSITIVE = (
    "retain_for_method_assessment"
)

terminal_types = {
    "record_decision",
    "superseding_record_decision",
}

terminal_decisions = {
    "exclude",
    POSITIVE,
}


latest = {}

for row in ledger:

    latest[
        row[
            "screening_entity_id"
        ]
    ] = row


labels = {}
batch_by_id = {}


for entity_id, row in latest.items():

    if (
        entity_id in membership_ids
        and row[
            "event_type"
        ] in terminal_types
        and row[
            "record_decision"
        ] in terminal_decisions
    ):

        labels[
            entity_id
        ] = row[
            "record_decision"
        ]

        batch_by_id[
            entity_id
        ] = row[
            "batch_id"
        ]


assert len(labels) == 2000


for batch in m.BATCHES:

    batch_id = batch[
        "batch_id"
    ]

    transaction_id = batch[
        "transaction_id"
    ]

    identity = m.build_target_identity(
        guard=guard,
        batch_id=batch_id,
    )

    _, proposals = guard.read_tsv(
        m.proposal_path(
            batch_id,
            transaction_id,
        )
    )

    assert len(
        identity[
            "entities"
        ]
    ) == 500

    assert len(
        proposals
    ) == 500

    for entity, proposal in zip(
        identity[
            "entities"
        ],
        proposals,
        strict=True,
    ):

        entity_id = entity[
            "screening_entity_id"
        ]

        assert entity_id not in labels

        decision = proposal[
            "record_decision"
        ]

        assert decision in terminal_decisions

        labels[
            entity_id
        ] = decision

        batch_by_id[
            entity_id
        ] = batch_id


assert len(labels) == 4500

assert Counter(
    labels.values()
) == {
    "exclude":
        4297,
    POSITIVE:
        203,
}


# ============================================================
# Freeze retrieval population.
#
# Publication records with any identity-attention state are
# protected from this text-retrieval lane.
# ============================================================

protected_ids = {
    entity_id
    for entity_id in labels
    if (
        queue_by_id[
            entity_id
        ][
            "screening_entity_class"
        ] != "publication"
        or queue_by_id[
            entity_id
        ][
            "identity_attention_status"
        ].strip()
    )
}


assert len(
    protected_ids
) == 1


eligible_ids = [
    entity_id
    for entity_id in labels
    if entity_id not in protected_ids
]


assert len(
    eligible_ids
) == 4499


for entity_id in eligible_ids:

    assert (
        queue_by_id[
            entity_id
        ][
            "screening_entity_class"
        ]
        == "publication"
    )

    assert not (
        queue_by_id[
            entity_id
        ][
            "identity_attention_status"
        ].strip()
    )


# Deterministic ordering uses membership only.
eligible_ids.sort(
    key=lambda entity_id:
        int(
            membership_by_id[
                entity_id
            ][
                "global_active_index"
            ]
        )
)


# ============================================================
# Construct label-blind exact-ID retrieval manifest.
# ============================================================

RESULT_ROOT.mkdir(
    parents=True,
    exist_ok=True,
)


manifest_fields = [
    "retrieval_record_index",
    "screening_entity_id",
    "queue_row_sha256",
    "pmid",
    "openalex_id",
    "doi",
    "omid",
    "pubmed_route",
    "openalex_route",
    "openalex_lookup_value",
    "retrieval_cascade",
]


rows = []

for index, entity_id in enumerate(
    eligible_ids,
    start=1,
):

    row = queue_by_id[
        entity_id
    ]

    pmid = row[
        "pmid"
    ].strip()

    openalex_id = row[
        "openalex_id"
    ].strip()

    doi = row[
        "doi"
    ].strip()

    omid = row[
        "omid"
    ].strip()


    assert (
        pmid
        or openalex_id
        or doi
    )


    pubmed_route = (
        "exact_pmid_efetch"
        if pmid
        else ""
    )


    if openalex_id:

        openalex_route = (
            "exact_work_id"
        )

        openalex_lookup_value = (
            openalex_id
        )

    elif doi:

        openalex_route = (
            "exact_doi"
        )

        openalex_lookup_value = (
            doi
        )

    elif pmid:

        openalex_route = (
            "exact_pmid"
        )

        openalex_lookup_value = (
            pmid
        )

    else:

        raise AssertionError(
            "eligible record has no "
            "OpenAlex fallback identifier"
        )


    if pubmed_route:

        cascade = (
            pubmed_route
            + ">"
            + "openalex_"
            + openalex_route
        )

    else:

        cascade = (
            "openalex_"
            + openalex_route
        )


    rows.append({
        "retrieval_record_index":
            str(index),

        "screening_entity_id":
            entity_id,

        "queue_row_sha256":
            canonical_row_sha256(
                row
            ),

        "pmid":
            pmid,

        "openalex_id":
            openalex_id,

        "doi":
            doi,

        "omid":
            omid,

        "pubmed_route":
            pubmed_route,

        "openalex_route":
            openalex_route,

        "openalex_lookup_value":
            openalex_lookup_value,

        "retrieval_cascade":
            cascade,
    })


with MANIFEST.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:

    writer = csv.DictWriter(
        handle,
        fieldnames=manifest_fields,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writeheader()
    writer.writerows(
        rows
    )


manifest_sha256 = sha256_file(
    MANIFEST
)


# ============================================================
# Freeze all source identities needed to reproduce the design.
# ============================================================

freeze_documents = sorted(
    [
        *ROOT.glob(
            "b000001*_approved_scientific_decision_freeze.json"
        ),

        ROOT
        / "b000002_t000011_positions_1_500_approved_scientific_decision_freeze.json",

        ROOT
        / "b000003_t000012_positions_1_500_approved_scientific_decision_freeze.json",

        ROOT
        / "b000004_t000013_positions_1_500_approved_scientific_decision_freeze.json",

        ROOT
        / "c000001_approved_scientific_decision_freeze.json",
    ],
    key=lambda value:
        str(value),
)


freeze_documents = [
    path
    for path in freeze_documents
    if path.exists()
]


assert len(
    freeze_documents
) == 12


scientific_contracts = [
    ROOT
    / "scientific_screening_design.json",

    ROOT
    / "SCIENTIFIC_SCREENING_DESIGN.md",

    ROOT
    / "SCIENTIFIC_DECISION_LEDGER.md",

    ROOT
    / "PROTOCOL.md",
]


transport_sources = [
    ROOT
    / "retrieve_metadata_resolution_queue.py",

    ROOT
    / "t000002_authoritative_source_network_transport.py",
]


for path in (
    freeze_documents
    + scientific_contracts
    + transport_sources
):

    assert path.exists(), path


def path_hash_record(
    path: Path,
) -> dict[str, str]:

    return {
        "path":
            str(path),

        "sha256":
            sha256_file(
                path
            ),
    }


source_hashes = {
    "baseline_queue":
        path_hash_record(
            m.QUEUE
        ),

    "active_membership":
        path_hash_record(
            m.EXECUTION_ROOT
            / "batch_membership.tsv"
        ),

    "production_ledger":
        path_hash_record(
            m.LEDGER
        ),

    "scientific_contracts": [
        path_hash_record(
            path
        )
        for path
        in scientific_contracts
    ],

    "scientific_decision_freezes": [
        path_hash_record(
            path
        )
        for path
        in freeze_documents
    ],

    "existing_transport_sources": [
        path_hash_record(
            path
        )
        for path
        in transport_sources
    ],
}


# ============================================================
# Population statistics.
# ============================================================

pmid_count = sum(
    bool(
        row[
            "pmid"
        ]
    )
    for row in rows
)

openalex_count = sum(
    bool(
        row[
            "openalex_id"
        ]
    )
    for row in rows
)

doi_count = sum(
    bool(
        row[
            "doi"
        ]
    )
    for row in rows
)

route_counts = Counter(
    row[
        "retrieval_cascade"
    ]
    for row in rows
)


# ============================================================
# Frozen design.
# ============================================================

design = {
    "schema_version":
        1,

    "design_id":
        "TRIAGE_PRE_REVIEW_TEXT_RETRIEVAL_V1",

    "status":
        "FROZEN_PRE_IMPLEMENTATION",

    "parent_commit":
        git_head(),

    "purpose":
        (
            "Freeze the development-only, "
            "label-blind pre-review publication-text "
            "retrieval design required to evaluate "
            "title-plus-abstract triage without "
            "modifying the production scientific "
            "screening workflow."
        ),

    "production_boundary":
        boundary,

    "development_population": {
        "expanded_terminal_or_frozen_labels":
            4500,

        "final_label_counts":
            dict(
                Counter(
                    labels.values()
                )
            ),

        "publication_text_retrieval_eligible":
            4499,

        "protected_from_publication_text_lane":
            1,

        "protected_rule":
            (
                "screening_entity_class != publication "
                "OR identity_attention_status non-empty"
            ),

        "scientifically_poolable_for_development":
            True,

        "poolability_basis":
            (
                "Audit 15 established common frozen "
                "record-level decision semantics across "
                "the historical and C000001 development "
                "labels."
            ),

        "batch_retained_as_validation_group":
            True,

        "batch_prohibited_as_predictive_feature":
            True,
    },

    "retrieval_manifest": {
        "path":
            str(
                MANIFEST
            ),

        "sha256":
            manifest_sha256,

        "rows":
            len(
                rows
            ),

        "contains_scientific_labels":
            False,

        "contains_batch_id":
            False,

        "contains_model_scores":
            False,

        "contains_review_evidence":
            False,

        "ordering":
            (
                "ascending frozen global_active_index; "
                "global_active_index itself is not emitted"
            ),

        "identifier_coverage": {
            "pmid":
                pmid_count,

            "openalex_id":
                openalex_count,

            "doi":
                doi_count,

            "primary_identifier_available":
                len(
                    rows
                ),
        },

        "cascade_counts":
            dict(
                sorted(
                    route_counts.items()
                )
            ),
    },

    "scope_boundary": {
        "development_publications_only":
            True,

        "blind_validation_sample_in_scope":
            False,

        "future_universe_in_scope":
            False,

        "software_registry_in_scope":
            False,

        "identity_attention_records_in_scope":
            False,

        "production_screening_in_scope":
            False,
    },

    "retrieval_cascade": {
        "label_blind":
            True,

        "same_rules_for_every_manifest_row":
            True,

        "pubmed": {
            "condition":
                "PMID present",

            "transport":
                "exact PMID EFetch",

            "priority":
                1,

            "usable_abstract_stops_cascade":
                True,

            "absence_or_not_found_allows_openalex_fallback":
                True,

            "transient_failure_is_recorded":
                True,

            "transient_failure_does_not_imply_scientific_exclusion":
                True,
        },

        "openalex": {
            "priority":
                2,

            "lookup_preference": [
                "exact_work_id",
                "exact_doi",
                "exact_pmid",
            ],

            "used_when":
                (
                    "PubMed is not applicable, "
                    "does not yield a usable abstract, "
                    "or fails to resolve the requested "
                    "record."
                ),

            "transient_failure_is_recorded":
                True,

            "transient_failure_does_not_imply_scientific_exclusion":
                True,
        },

        "crossref_primary_route":
            False,
    },

    "transport_contract": {
        "reuse_existing_exact_identifier_transport":
            True,

        "new_independent_http_stack_prohibited":
            True,

        "raw_provider_response_must_be_archived":
            True,

        "raw_response_sha256_required":
            True,

        "provider_identity_validation_required":
            True,

        "existing_retry_rate_limit_and_redirect_semantics_preserved":
            True,

        "credentials_must_not_be_persisted":
            True,

        "transport_source_hashes":
            source_hashes[
                "existing_transport_sources"
            ],
    },

    "normalization_contract": {
        "normalizer_is_pure_derivative_of_verified_raw_bytes":
            True,

        "production_reconciliation_parser_must_not_be_modified":
            True,

        "pubmed": {
            "accepted_record_types": [
                "PubmedArticle",
                "PubmedBookArticle",
            ],

            "requested_pmid_must_match_returned_record":
                True,

            "title_sources": [
                "ArticleTitle",
                "BookTitle",
            ],

            "abstract_source":
                "AbstractText elements in document order",

            "whitespace_normalization":
                "collapse Unicode whitespace to single spaces",

            "section_labels_preserved_as_metadata":
                True,

            "section_labels_injected_into_model_text":
                False,

            "empty_abstract_elements_count_as_usable":
                False,
        },

        "openalex": {
            "title_sources": [
                "display_name",
                "title",
            ],

            "abstract_source":
                "abstract_inverted_index",

            "reconstruction":
                (
                    "sort observed integer positions "
                    "ascending and emit corresponding tokens"
                ),

            "non_string_token":
                "parser_failure",

            "non_list_position_vector":
                "parser_failure",

            "non_integer_position":
                "parser_failure",

            "duplicate_position":
                "parser_failure",

            "noncontiguous_positions":
                (
                    "record explicit position_gap status; "
                    "do not silently classify as ordinary "
                    "primary-model abstract"
                ),

            "null_or_absent_abstract":
                "abstract_absent",
        },

        "minimum_abstract_length_threshold":
            None,

        "reason_no_threshold_is_frozen":
            (
                "No evidence-based minimum length "
                "criterion has yet been approved; "
                "absence/quality must not be converted "
                "into an implicit exclusion rule."
            ),
    },

    "planned_derived_statuses": [
        "usable_abstract_pubmed",
        "usable_abstract_openalex",
        "abstract_absent_all_attempted_sources",
        "openalex_position_gap",
        "provider_not_found",
        "provider_identity_mismatch",
        "retrieval_failure",
        "parser_failure",
    ],

    "planned_normalized_output_fields": [
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
    ],

    "retrieval_output_prohibitions": [
        "record_decision",
        "exclusion_reason_code",
        "candidate_method_flag",
        "evidence_basis",
        "evidence_source_locator",
        "evidence_escalation_status",
        "operator_id",
        "operator_type",
        "reviewer_id",
        "review_status",
        "adjudication_status",
        "notes",
        "model_score",
        "model_threshold",
    ],

    "downstream_feature_prohibitions_without_separate_amendment": [
        "batch_id",
        "global_active_index",
        "discovery_stage",
        "doi_prefix",
        "journal",
        "publisher",
        "provider_used",
        "retrieval_status",
        "retrieval_failure_state",
        "review_evidence",
        "scientific_decision_fields",
    ],

    "model_development_boundary": {
        "retrieval_freeze_does_not_freeze_a_classifier":
            True,

        "retrieval_freeze_does_not_freeze_a_threshold":
            True,

        "acceptable_recall_threshold_defined":
            False,

        "whole_batch_nested_validation_required":
            True,

        "blind_holdout_must_remain_unopened_for_model_development":
            True,

        "future_records_must_not_be_scored_during_development":
            True,

        "missing_abstract_must_not_be_treated_as_negative_evidence":
            True,
    },

    "authority_separation": {
        "design_creates_network_authority":
            False,

        "design_creates_production_authority":
            False,

        "design_creates_scientific_decisions":
            False,

        "design_creates_model_authority":
            False,

        "live_network_retrieval_requires_separate_explicit_authorization":
            True,

        "production_scientific_screening_protocol_unchanged":
            True,

        "automated_exclusion_protocol_amendment_approved":
            False,
    },

    "implementation_gate": {
        "next_gate":
            (
                "IMPLEMENT_AND_TEST_PURE_ABSTRACT_NORMALIZER_"
                "AND_DEVELOPMENT_ONLY_RETRIEVAL_RUNNER_"
                "BEFORE_ANY_LIVE_NETWORK_RETRIEVAL"
            ),

        "requirements": [
            (
                "parser tests using archived verified "
                "PubMed and OpenAlex payloads"
            ),
            (
                "tests for PubMed multi-section abstracts"
            ),
            (
                "tests for OpenAlex null abstracts"
            ),
            (
                "tests for OpenAlex malformed and "
                "duplicate positions"
            ),
            (
                "tests for OpenAlex noncontiguous "
                "position handling"
            ),
            (
                "deterministic output and checksum tests"
            ),
            (
                "assert no retrieval artifact contains "
                "scientific labels or review evidence"
            ),
            (
                "assert blind validation sample is not "
                "read by implementation"
            ),
            (
                "assert production ledger boundary "
                "remains unchanged"
            ),
        ],
    },

    "frozen_source_hashes":
        source_hashes,
}


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


# ============================================================
# Human-readable freeze.
# ============================================================

doc = f"""# Triage pre-review text retrieval v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This document freezes a development-only pre-review text retrieval
design. It does not authorize network access, production screening,
automated exclusion, model fitting, threshold selection, future
scoring, or blind-validation access.

## Development population

- Expanded frozen development corpus: 4,500 records.
- Publication-text retrieval lane: 4,499 records.
- Protected from this lane: 1 record with a non-empty identity-attention
  state.
- Final development labels remain outside the retrieval manifest:
  4,297 `exclude` and 203 `retain_for_method_assessment`.
- Historical and C000001 labels are treated as scientifically compatible
  for development under the common frozen screening contract.
- Batch remains a validation grouping and is prohibited as a predictive
  feature.

## Frozen retrieval manifest

Path:

`{MANIFEST}`

SHA-256:

`{manifest_sha256}`

Rows: {len(rows)}

The manifest contains identifiers and deterministic transport routing
only. It contains no scientific decision, exclusion reason, review
evidence, model score, or batch identifier.

## Retrieval cascade

For records with a PMID, PubMed exact-PMID EFetch is attempted first.
A usable PubMed abstract terminates the cascade for that record.

When PubMed is not applicable or does not yield a usable abstract,
OpenAlex is the fallback. OpenAlex lookup identity is selected in this
order:

1. exact OpenAlex Work ID;
2. exact DOI;
3. exact PMID.

Crossref is not a primary route in v1.

Retrieval failure, provider absence, or abstract absence is never itself
scientific evidence for exclusion.

## Transport

The implementation must reuse the existing exact-identifier transport
semantics and raw-response archival machinery. A separate independent
HTTP stack is prohibited.

Every successful raw response must remain byte-verifiable through its
SHA-256 and provider identity checks. Existing retry, rate-limit,
redirect, credential-sanitisation, and archive-integrity semantics are
preserved.

## Text normalization

### PubMed

The parser reads a single `PubmedArticle` or `PubmedBookArticle`,
validates the requested identity, extracts title text, and concatenates
non-empty `AbstractText` elements in document order.

`Label` and `NlmCategory` values are retained as metadata but are not
inserted into model text.

### OpenAlex

The parser reconstructs `abstract_inverted_index` by integer position.

Malformed tokens, position vectors, non-integer positions, or duplicate
positions fail closed at the parser layer.

Non-contiguous position sets receive an explicit position-gap status;
they are not silently treated as ordinary primary-model abstracts.

No minimum abstract-length threshold is frozen in v1.

## Leakage boundary

The normalized retrieval artifact must not contain scientific decisions,
review evidence, operator fields, notes, model scores, or thresholds.

Provider identity, retrieval status, failure state, batch, discovery
provenance, DOI prefix, journal, and publisher are not model features
under this design.

## Model and validation boundary

This freeze does not select a classifier or threshold.

Whole-batch nested development validation remains required.

The frozen blind validation sample remains outside this work and must
not be opened for model development. Future-universe records must not be
scored during development.

Missing abstract text must not be interpreted as negative scientific
evidence.

## Authority boundary

This design creates no network authority and no production authority.

Live retrieval requires a separate explicit authorization after the
parser and development-only retrieval runner have been implemented and
tested against archived payloads.

The production scientific-screening protocol remains unchanged.
"""


DOCUMENT.write_text(
    doc,
    encoding="utf-8",
)


print(
    "design =",
    DESIGN,
)

print(
    "manifest =",
    MANIFEST,
)

print(
    "document =",
    DOCUMENT,
)

print(
    "parent commit =",
    design[
        "parent_commit"
    ],
)

print(
    "development records =",
    4500,
)

print(
    "retrieval eligible =",
    len(rows),
)

print(
    "protected =",
    len(protected_ids),
)

print(
    "label counts =",
    dict(
        Counter(
            labels.values()
        )
    ),
)

print(
    "PMID =",
    pmid_count,
)

print(
    "OpenAlex ID =",
    openalex_count,
)

print(
    "DOI =",
    doi_count,
)

print(
    "cascade counts =",
    dict(
        sorted(
            route_counts.items()
        )
    ),
)

print(
    "manifest SHA256 =",
    manifest_sha256,
)

print(
    "design SHA256 =",
    sha256_file(
        DESIGN
    ),
)

print(
    "document SHA256 =",
    sha256_file(
        DOCUMENT
    ),
)

print()
print(
    "PASS | triage pre-review text retrieval v1 "
    "design frozen pre-implementation"
)

print(
    "NO ACTION | no network request; no model fit; "
    "no threshold; no future scoring; no blind-holdout "
    "access; no production mutation"
)
