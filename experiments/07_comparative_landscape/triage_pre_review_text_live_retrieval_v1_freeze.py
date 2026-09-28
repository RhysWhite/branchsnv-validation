from __future__ import annotations

from collections import Counter
import csv
import hashlib
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

NETWORK_REQUIREMENTS = (
    RESULT_ROOT
    / "offline_network_requirements.tsv"
)

INPUT_MANIFEST = (
    RESULT_ROOT
    / "input_manifest.tsv"
)

WAVE_A_MANIFEST = (
    RESULT_ROOT
    / "live_wave_a_request_manifest.tsv"
)

DESIGN = (
    ROOT
    / "triage_pre_review_text_live_retrieval_v1_design.json"
)

DOCUMENT = (
    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_LIVE_RETRIEVAL_V1.md"
)


EXPECTED_PARENT = (
    "0a49d448f98d20d40f8ef344d623e986f1d08a5d"
)

EXPECTED_NETWORK_REQUIREMENTS_SHA256 = (
    "87b9786c1928773d51708b2bc93cea137d1eb7b36"
    "af43d0d26ab5a29487d0dc9"
)

EXPECTED_INPUT_MANIFEST_SHA256 = (
    "4e5ba0313e008a58e968a9368ea90b6fdb70049b"
    "866003742ed1c967c31120ba"
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


def canonical_hash(
    value,
) -> str:

    raw = json.dumps(
        value,
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
        raw
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

        assert reader.fieldnames is not None

        rows = list(
            reader
        )

    return list(
        reader.fieldnames
    ), rows


def write_tsv(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


assert git_head() == EXPECTED_PARENT

assert (
    sha256_file(
        NETWORK_REQUIREMENTS
    )
    == EXPECTED_NETWORK_REQUIREMENTS_SHA256
)

assert (
    sha256_file(
        INPUT_MANIFEST
    )
    == EXPECTED_INPUT_MANIFEST_SHA256
)


# ============================================================
# Load frozen transport source identities.
# ============================================================

retrieval_design_path = (
    ROOT
    / "triage_pre_review_text_retrieval_v1_design.json"
)

retrieval_design = json.loads(
    retrieval_design_path.read_text(
        encoding="utf-8"
    )
)

transport_sources = (
    retrieval_design[
        "frozen_source_hashes"
    ][
        "existing_transport_sources"
    ]
)

assert len(
    transport_sources
) == 2


# ============================================================
# Convert the offline requirement inventory into an exact,
# immutable Wave A transport manifest.
# ============================================================

network_fields, network_rows = read_tsv(
    NETWORK_REQUIREMENTS
)

assert network_fields == [
    "retrieval_record_index",
    "screening_entity_id",
    "provider",
    "route",
    "identifier",
    "reason",
]

assert len(
    network_rows
) == 4490


expected_counts = {
    (
        "pubmed",
        "exact_pmid_efetch",
    ):
        3956,

    (
        "openalex",
        "exact_work_id",
    ):
        526,

    (
        "openalex",
        "exact_doi",
    ):
        8,
}


actual_counts = Counter(
    (
        row[
            "provider"
        ],
        row[
            "route"
        ],
    )
    for row in network_rows
)

assert actual_counts == expected_counts


ROUTE_MAP = {
    (
        "pubmed",
        "exact_pmid_efetch",
    ): {
        "transport_route":
            "record_by_pmid",
        "identifier_namespace":
            "pmid",
    },

    (
        "openalex",
        "exact_work_id",
    ): {
        "transport_route":
            "work_by_openalex_id",
        "identifier_namespace":
            "openalex",
    },

    (
        "openalex",
        "exact_doi",
    ): {
        "transport_route":
            "work_by_doi",
        "identifier_namespace":
            "doi",
    },
}


network_rows = sorted(
    network_rows,
    key=lambda row:
        int(
            row[
                "retrieval_record_index"
            ]
        ),
)


# Physical exact requests must be unique before we authorize
# an exact request count.
physical_keys = [
    (
        row[
            "provider"
        ],
        row[
            "route"
        ],
        row[
            "identifier"
        ],
    )
    for row in network_rows
]

assert len(
    set(
        physical_keys
    )
) == 4490, (
    "duplicate physical exact lookup discovered; "
    "do not freeze 4,490-request authorization"
)


wave_rows = []

for sequence, row in enumerate(
    network_rows,
    start=1,
):

    key = (
        row[
            "provider"
        ],
        row[
            "route"
        ],
    )

    assert key in ROUTE_MAP

    mapping = ROUTE_MAP[
        key
    ]

    identity = {
        "wave_id":
            "TRIAGE_TEXT_LIVE_WAVE_A",

        "request_sequence":
            sequence,

        "retrieval_record_index":
            int(
                row[
                    "retrieval_record_index"
                ]
            ),

        "screening_entity_id":
            row[
                "screening_entity_id"
            ],

        "provider":
            row[
                "provider"
            ],

        "frozen_route":
            row[
                "route"
            ],

        "transport_route":
            mapping[
                "transport_route"
            ],

        "identifier_namespace":
            mapping[
                "identifier_namespace"
            ],

        "identifier":
            row[
                "identifier"
            ],
    }

    wave_rows.append({
        "wave_id":
            identity[
                "wave_id"
            ],

        "request_sequence":
            str(
                identity[
                    "request_sequence"
                ]
            ),

        "retrieval_record_index":
            str(
                identity[
                    "retrieval_record_index"
                ]
            ),

        "screening_entity_id":
            identity[
                "screening_entity_id"
            ],

        "provider":
            identity[
                "provider"
            ],

        "frozen_route":
            identity[
                "frozen_route"
            ],

        "transport_route":
            identity[
                "transport_route"
            ],

        "identifier_namespace":
            identity[
                "identifier_namespace"
            ],

        "identifier":
            identity[
                "identifier"
            ],

        "request_identity_sha256":
            canonical_hash(
                identity
            ),
    })


wave_fields = [
    "wave_id",
    "request_sequence",
    "retrieval_record_index",
    "screening_entity_id",
    "provider",
    "frozen_route",
    "transport_route",
    "identifier_namespace",
    "identifier",
    "request_identity_sha256",
]


assert len(
    wave_rows
) == 4490

assert len({
    row[
        "request_identity_sha256"
    ]
    for row in wave_rows
}) == 4490


write_tsv(
    WAVE_A_MANIFEST,
    wave_fields,
    wave_rows,
)

wave_a_sha256 = sha256_file(
    WAVE_A_MANIFEST
)


# ============================================================
# Bind implementation sources that a later authorization must
# match exactly.
# ============================================================

source_paths = {
    "retrieval_design":
        retrieval_design_path,

    "input_manifest":
        INPUT_MANIFEST,

    "offline_network_requirements":
        NETWORK_REQUIREMENTS,

    "normalizer":
        ROOT
        / "triage_pre_review_text_normalizer_v1.py",

    "offline_runner":
        ROOT
        / "triage_pre_review_text_offline_runner_v1.py",
}


source_hashes = {
    key: {
        "path":
            str(
                path
            ),
        "sha256":
            sha256_file(
                path
            ),
    }
    for key, path
    in source_paths.items()
}


# ============================================================
# Frozen pre-authorization design.
# ============================================================

design = {
    "schema_version":
        1,

    "design_id":
        "TRIAGE_PRE_REVIEW_TEXT_LIVE_RETRIEVAL_V1",

    "status":
        "FROZEN_PRE_AUTHORIZATION",

    "parent_commit":
        EXPECTED_PARENT,

    "purpose":
        (
            "Freeze the live-network authority boundary "
            "for development-only pre-review text retrieval "
            "without creating live network authority."
        ),

    "production_boundary":
        EXPECTED_PRODUCTION,

    "wave_a": {
        "wave_id":
            "TRIAGE_TEXT_LIVE_WAVE_A",

        "purpose":
            "execute only frozen first-hop exact lookups",

        "request_manifest": {
            "path":
                str(
                    WAVE_A_MANIFEST
                ),
            "sha256":
                wave_a_sha256,
            "rows":
                4490,
        },

        "request_counts": {
            "pubmed_exact_pmid_efetch":
                3956,

            "openalex_exact_work_id":
                526,

            "openalex_exact_doi":
                8,

            "total":
                4490,
        },

        "transport_mapping": {
            "pubmed:exact_pmid_efetch": {
                "transport_route":
                    "record_by_pmid",
                "identifier_namespace":
                    "pmid",
            },

            "openalex:exact_work_id": {
                "transport_route":
                    "work_by_openalex_id",
                "identifier_namespace":
                    "openalex",
            },

            "openalex:exact_doi": {
                "transport_route":
                    "work_by_doi",
                "identifier_namespace":
                    "doi",
            },
        },

        "execution_order":
            "ascending request_sequence",

        "concurrency":
            1,

        "maximum_request_initiation_rate_per_second": {
            "pubmed":
                2.0,
            "openalex":
                2.0,
        },

        "search_or_list_endpoints_permitted":
            False,

        "crossref_permitted":
            False,

        "ad_hoc_connectivity_probe_permitted":
            False,
    },

    "transport_contract": {
        "reuse_existing_exact_identifier_transport":
            True,

        "transport_sources":
            transport_sources,

        "raw_response_archive_required":
            True,

        "response_body_sha256_required":
            True,

        "terminal_record_required":
            True,

        "provider_identity_validation_required":
            True,

        "retry_semantics_inherited":
            True,

        "redirect_semantics_inherited":
            True,

        "credential_sanitization_inherited":
            True,

        "new_independent_http_stack_permitted":
            False,

        "pubmed": {
            "ncbi_email_required_for_live_execution":
                True,

            "ncbi_email_must_not_be_archived":
                True,

            "ncbi_api_key_permitted":
                False,

            "tool_parameter_inherited_from_transport":
                True,
        },

        "openalex": {
            "api_key_optional":
                True,

            "api_key_must_not_be_archived":
                True,
        },
    },

    "authorization_contract": {
        "authorization_created_by_this_freeze":
            False,

        "network_authority_created_by_this_freeze":
            False,

        "execution_authority_created_by_this_freeze":
            False,

        "explicit_human_authorization_required":
            True,

        "future_authorization_must_bind": [
            "wave_id",
            "wave_a_request_manifest_sha256",
            "design_sha256",
            "parent_commit",
            "normalizer_sha256",
            "transport_source_hashes",
            "maximum_request_count",
            "execution_output_root",
        ],

        "maximum_request_count":
            4490,

        "one_use":
            True,

        "execution_id_bound_on_first_start":
            True,

        "resume_same_execution_id_permitted":
            True,

        "second_execution_id_with_same_authorization_permitted":
            False,

        "request_outside_frozen_manifest_permitted":
            False,

        "completed_authorization_replay_permitted":
            False,

        "checkpoint_after_each_terminal_lookup":
            True,

        "completion_receipt_required":
            True,
    },

    "wave_b": {
        "wave_id":
            "TRIAGE_TEXT_LIVE_WAVE_B",

        "authorized_by_wave_a_authorization":
            False,

        "manifest_exists":
            False,

        "separate_human_authorization_required":
            True,

        "purpose":
            (
                "OpenAlex fallback only after verified "
                "Wave A PubMed outcomes establish that "
                "the frozen PubMed first route did not "
                "yield usable abstract text."
            ),

        "eligible_parent_records":
            "Wave A PubMed requests only",

        "eligible_pubmed_outcomes": [
            "verified successful exact PubMed payload normalized as abstract_absent",
            "verified terminal provider not-found state under pinned transport semantics",
        ],

        "ineligible_pubmed_outcomes": [
            "usable_abstract_pubmed",
            "provider_identity_mismatch",
            "parser_failure",
            "retrieval_failure",
            "retry_exhausted",
            "unverified_or_missing_archive",
        ],

        "fallback_route_selection":
            [
                "exact OpenAlex Work ID when frozen input manifest provides one",
                "otherwise exact DOI",
                "otherwise exact PMID",
            ],

        "transport_route_mapping": {
            "exact_work_id":
                "work_by_openalex_id",

            "exact_doi":
                "work_by_doi",

            "exact_pmid":
                "work_by_pmid",
        },

        "wave_b_manifest_must_be_derived_deterministically_from":
            [
                "frozen input manifest",
                "Wave A terminal evidence",
                "pinned normalizer",
            ],
    },

    "execution_output_contract": {
        "root":
            (
                "results/07_comparative_landscape/"
                "triage_pre_review_text_retrieval_v1/"
                "live_wave_a"
            ),

        "raw_provider_bytes_preserved":
            True,

        "request_and_response_metadata_preserved":
            True,

        "credentials_or_unredacted_contact_values_preserved":
            False,

        "normalized_text_generated_only_from_verified_archived_bytes":
            True,

        "scientific_labels_permitted":
            False,

        "review_evidence_permitted":
            False,

        "model_scores_permitted":
            False,

        "production_ledger_write_permitted":
            False,
    },

    "scientific_boundary": {
        "model_fitting_authorized":
            False,

        "threshold_selection_authorized":
            False,

        "automated_exclusion_authorized":
            False,

        "future_universe_scoring_authorized":
            False,

        "blind_validation_sample_in_scope":
            False,

        "production_screening_protocol_changed":
            False,
    },

    "implementation_gate": {
        "next_gate":
            (
                "IMPLEMENT_AND_HOSTILE_TEST_LIVE_WAVE_A_"
                "AUTHORIZATION_GUARD_AND_EXECUTION_RUNNER_"
                "WITHOUT_NETWORK"
            ),

        "requirements": [
            "authorization absent -> fail closed before network",
            "manifest hash mismatch -> fail closed",
            "design hash mismatch -> fail closed",
            "parent/source hash mismatch -> fail closed",
            "request outside manifest -> fail closed",
            "request count cannot exceed 4490",
            "second execution ID using consumed authorization -> fail closed",
            "same execution ID may resume only from verified checkpoint",
            "completed authorization replay -> fail closed",
            "provider credentials must never enter archived evidence",
            "all hostile tests perform zero real network requests",
            "production boundary remains unchanged",
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


doc = f"""# Triage pre-review text live retrieval v1

## Status

`FROZEN_PRE_AUTHORIZATION`

This freeze creates no live-network authority.

It defines the authority boundary that must be satisfied before any
development-text retrieval request is sent.

## Wave A

Wave A contains exactly 4,490 first-hop exact requests:

- 3,956 PubMed exact PMID EFetch requests;
- 526 OpenAlex exact Work-ID requests;
- 8 OpenAlex exact DOI requests.

Frozen request manifest:

`{WAVE_A_MANIFEST}`

SHA-256:

`{wave_a_sha256}`

Only exact singleton retrieval is permitted. Search/list endpoints,
Crossref fallback, and ad hoc connectivity probes are outside Wave A.

## Transport

The existing exact-identifier transport is reused unchanged.

Frozen transport mappings are:

- PubMed `exact_pmid_efetch` -> `record_by_pmid`;
- OpenAlex `exact_work_id` -> `work_by_openalex_id`;
- OpenAlex `exact_doi` -> `work_by_doi`.

Maximum initiation rate remains two requests per second for each
provider. Execution is serial in frozen request order.

PubMed live execution requires the configured NCBI contact email.
The contact value and provider credentials must never enter archived
evidence.

## Authorization

This freeze is not an authorization.

A later authorization must bind the exact design, Wave A request
manifest, source hashes, output root, parent commit, and maximum request
count.

Authorization is one-use. The first execution binds an execution ID.
A failed/interrupted run may resume only under that same execution ID
from a verified checkpoint. A second execution ID or replay after
completion fails closed.

## Wave B

Wave A does not authorize OpenAlex fallback requests for PubMed records.

After Wave A is complete, a second deterministic manifest may be
derived only for PubMed records whose verified result establishes no
usable PubMed abstract under the frozen rules.

Transient transport failure, parser failure, identity mismatch, or
unverified evidence cannot trigger fallback.

Wave B requires a separate human authorization.

## Scientific boundary

Neither Wave A nor this design creates a scientific decision, model
score, threshold, automated exclusion rule, production-screening
authority, future-universe scoring authority, or blind-validation
authority.

## Next gate

Implement and hostile-test the Wave A authorization guard and live
execution runner with mocked transport only. No real network request is
permitted at that gate.
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
    "document =",
    DOCUMENT,
)

print(
    "Wave A manifest =",
    WAVE_A_MANIFEST,
)

print(
    "Wave A rows =",
    len(
        wave_rows
    ),
)

print(
    "Wave A counts =",
    dict(
        sorted(
            actual_counts.items()
        )
    ),
)

print(
    "Wave A manifest SHA256 =",
    wave_a_sha256,
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
    "PASS | live retrieval v1 frozen "
    "pre-authorization"
)

print(
    "NO AUTHORITY | no live authorization created; "
    "no network request; no model fit; no future scoring; "
    "blind validation not scientifically used; "
    "no production mutation"
)
