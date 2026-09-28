from __future__ import annotations

from collections import Counter
from pathlib import Path
import csv
import hashlib
import json

import triage_pre_review_text_normalizer_v1 as normalizer
import triage_pre_review_text_wave_a_guard_v1 as wave_a_guard


ROOT = Path(
    "experiments/07_comparative_landscape"
)

RESULT_ROOT = Path(
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1"
)

LIVE_A = RESULT_ROOT / "live_wave_a"

INPUT_MANIFEST = (
    RESULT_ROOT
    / "input_manifest.tsv"
)

WAVE_A_MANIFEST = (
    RESULT_ROOT
    / "live_wave_a_request_manifest.tsv"
)

WAVE_B_MANIFEST = (
    RESULT_ROOT
    / "live_wave_b_request_manifest.tsv"
)

WAVE_B_DERIVATION = (
    RESULT_ROOT
    / "live_wave_b_derivation.tsv"
)

DESIGN = (
    ROOT
    / "triage_pre_review_text_wave_b_manifest_v1_design.json"
)

DOC = (
    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_WAVE_B_MANIFEST_V1.md"
)

CHECKSUMS = (
    ROOT
    / "triage_pre_review_text_wave_b_manifest_v1.sha256"
)

FREEZE_SCRIPT = (
    ROOT
    / "triage_pre_review_text_wave_b_manifest_v1_freeze.py"
)

NORMALIZER_PATH = (
    ROOT
    / "triage_pre_review_text_normalizer_v1.py"
)

WAVE_A_GUARD_PATH = (
    ROOT
    / "triage_pre_review_text_wave_a_guard_v1.py"
)


EXPECTED_PARENT_COMMIT = (
    "ac9ff71d73956b2a6fc8ccd2252a68ae093ab45d"
)

EXPECTED_INPUT_MANIFEST_SHA256 = (
    "4e5ba0313e008a58e968a9368ea90b6f"
    "db70049b866003742ed1c967c31120ba"
)

EXPECTED_WAVE_A_MANIFEST_SHA256 = (
    "91a87f2d8a2bfc00ead9a5f1b6e6fcaf"
    "850666573583bb07317a1416d446211d"
)

EXPECTED_NORMALIZER_SHA256 = (
    "cbe66fc9ab406fa5ee3745e099c16250"
    "c404a949c0f301e40a7397c285dc459d"
)

WAVE_B_ID = (
    "TRIAGE_TEXT_LIVE_WAVE_B"
)


def sha256_bytes(
    data: bytes,
) -> str:
    return hashlib.sha256(
        data
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
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode(
        "utf-8"
    )


def write_json(
    path: Path,
    value,
) -> None:
    path.write_bytes(
        canonical_json_bytes(
            value
        )
    )


def write_tsv(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:

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
            extrasaction="raise",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    field:
                        str(
                            row.get(
                                field,
                                "",
                            )
                        )
                    for field in fields
                }
            )


# ============================================================
# Frozen source integrity.
# ============================================================

assert sha256_file(
    INPUT_MANIFEST
) == EXPECTED_INPUT_MANIFEST_SHA256

assert sha256_file(
    WAVE_A_MANIFEST
) == EXPECTED_WAVE_A_MANIFEST_SHA256

assert sha256_file(
    NORMALIZER_PATH
) == EXPECTED_NORMALIZER_SHA256


# ============================================================
# Wave A must be durably complete.
# ============================================================

claim_path = (
    LIVE_A
    / "authorization_claim.json"
)

state_path = (
    LIVE_A
    / "execution_state.json"
)

receipt_path = (
    LIVE_A
    / "completion_receipt.json"
)

for path in (
    claim_path,
    state_path,
    receipt_path,
):
    assert path.is_file(), path


claim = json.loads(
    claim_path.read_text(
        encoding="utf-8"
    )
)

state = json.loads(
    state_path.read_text(
        encoding="utf-8"
    )
)

receipt = json.loads(
    receipt_path.read_text(
        encoding="utf-8"
    )
)


assert claim["status"] == "COMPLETED"
assert state["status"] == "COMPLETED"
assert receipt["status"] == "COMPLETED"

assert claim[
    "completed_request_count"
] == 4490

assert state[
    "completed_request_count"
] == 4490

assert receipt[
    "completed_request_count"
] == 4490

assert state[
    "next_request_sequence"
] == 4491


# ============================================================
# Index terminal evidence exactly once.
# ============================================================

terminal_by_lookup = {}

for path in (
    LIVE_A
    / "raw"
).rglob(
    "terminal.json"
):

    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    lookup_id = value[
        "logical_lookup_id"
    ]

    assert (
        lookup_id
        not in terminal_by_lookup
    )

    terminal_by_lookup[
        lookup_id
    ] = (
        path,
        value,
    )


assert len(
    terminal_by_lookup
) == 4490


# ============================================================
# Derive PubMed fallback set using frozen normalizer.
# ============================================================

fallback = []

evidence_paths = sorted(
    (
        LIVE_A
        / "transport_evidence"
    ).glob(
        "*.json"
    )
)

assert len(
    evidence_paths
) == 4490


for evidence_path in evidence_paths:

    evidence = json.loads(
        evidence_path.read_text(
            encoding="utf-8"
        )
    )

    if (
        evidence[
            "provider"
        ]
        != "pubmed"
    ):
        continue


    sequence = int(
        evidence[
            "request_sequence"
        ]
    )

    pmid = str(
        evidence[
            "identifier"
        ]
    )

    adapter_status = evidence[
        "adapter_status"
    ]


    if (
        adapter_status
        == "verified_not_found"
    ):

        assert (
            evidence[
                "provider_identity_status"
            ]
            == "not_applicable_not_found"
        )

        assert (
            evidence[
                "transport_terminal_status"
            ]
            == "not_found"
        )

        fallback.append({
            "wave_a_request_sequence":
                sequence,

            "pmid":
                pmid,

            "fallback_reason":
                "verified_not_found",

            "wave_a_request_identity_sha256":
                evidence[
                    "request_identity_sha256"
                ],

            "wave_a_adapter_evidence_sha256":
                sha256_file(
                    evidence_path
                ),

            "wave_a_terminal_body_sha256":
                "",
        })

        continue


    assert (
        adapter_status
        == "verified_success"
    )

    assert (
        evidence[
            "transport_terminal_status"
        ]
        == "success"
    )

    lookup_id = evidence[
        "logical_lookup_id"
    ]

    assert (
        lookup_id
        in terminal_by_lookup
    )

    terminal_path, terminal = (
        terminal_by_lookup[
            lookup_id
        ]
    )

    assert (
        terminal[
            "terminal_status"
        ]
        == "success"
    )

    expected_body_sha = terminal[
        "terminal_body_sha256"
    ]

    bodies = []

    for body_path in (
        terminal_path.parent
    ).rglob(
        "*.bin"
    ):

        body = body_path.read_bytes()

        if (
            sha256_bytes(
                body
            )
            == expected_body_sha
        ):
            bodies.append(
                body
            )


    assert len(
        bodies
    ) == 1, (
        terminal_path,
        len(
            bodies
        ),
    )


    result = (
        normalizer.normalize_pubmed(
            bodies[0],
            pmid,
        )
    )


    assert (
        result[
            "provider_identity_status"
        ]
        == "matched"
    )

    assert (
        result[
            "parser_status"
        ]
        == "ok"
    )


    abstract_status = result[
        "abstract_status"
    ]


    if (
        abstract_status
        == "usable_abstract_pubmed"
    ):
        continue


    assert (
        abstract_status
        == "abstract_absent"
    ), (
        sequence,
        pmid,
        abstract_status,
    )


    fallback.append({
        "wave_a_request_sequence":
            sequence,

        "pmid":
            pmid,

        "fallback_reason":
            "abstract_absent",

        "wave_a_request_identity_sha256":
            evidence[
                "request_identity_sha256"
            ],

        "wave_a_adapter_evidence_sha256":
            sha256_file(
                evidence_path
            ),

        "wave_a_terminal_body_sha256":
            expected_body_sha,
    })


fallback = sorted(
    fallback,
    key=lambda row:
        row[
            "wave_a_request_sequence"
        ],
)


assert len(
    fallback
) == 25


assert Counter(
    row[
        "fallback_reason"
    ]
    for row in fallback
) == {
    "abstract_absent":
        24,

    "verified_not_found":
        1,
}


# ============================================================
# Bind candidates to frozen original retrieval manifest.
# ============================================================

with INPUT_MANIFEST.open(
    encoding="utf-8",
    newline="",
) as handle:

    input_rows = list(
        csv.DictReader(
            handle,
            delimiter="\t",
        )
    )


assert len(
    input_rows
) == 4499


input_by_pmid = {}

for row in input_rows:

    pmid = (
        row.get(
            "pmid",
            ""
        )
        or ""
    ).strip()

    if not pmid:
        continue

    input_by_pmid.setdefault(
        pmid,
        []
    ).append(
        row
    )


manifest_rows = []
derivation_rows = []


for wave_b_sequence, item in enumerate(
    fallback,
    start=1,
):

    pmid = item[
        "pmid"
    ]

    matches = input_by_pmid.get(
        pmid,
        [],
    )

    assert len(
        matches
    ) == 1, (
        pmid,
        len(
            matches
        ),
    )


    source = matches[0]


    frozen_route = (
        source[
            "openalex_route"
        ]
        or ""
    ).strip()

    identifier = (
        source[
            "openalex_lookup_value"
        ]
        or ""
    ).strip()


    assert frozen_route in {
        "exact_work_id",
        "exact_doi",
    }

    assert identifier


    if (
        frozen_route
        == "exact_work_id"
    ):

        transport_route = (
            "work_by_openalex_id"
        )

        identifier_namespace = (
            "openalex"
        )

        assert (
            identifier
            == (
                source[
                    "openalex_id"
                ]
                or ""
            ).strip()
        )


    else:

        transport_route = (
            "work_by_doi"
        )

        identifier_namespace = (
            "doi"
        )

        assert (
            identifier
            == (
                source[
                    "doi"
                ]
                or ""
            ).strip()
        )


    request_row = {
        "wave_id":
            WAVE_B_ID,

        "request_sequence":
            str(
                wave_b_sequence
            ),

        "retrieval_record_index":
            source[
                "retrieval_record_index"
            ],

        "screening_entity_id":
            source[
                "screening_entity_id"
            ],

        "provider":
            "openalex",

        "frozen_route":
            frozen_route,

        "transport_route":
            transport_route,

        "identifier_namespace":
            identifier_namespace,

        "identifier":
            identifier,
    }


    request_row[
        "request_identity_sha256"
    ] = (
        wave_a_guard.expected_request_identity(
            request_row
        )
    )


    manifest_rows.append(
        request_row
    )


    derivation_rows.append({
        "wave_b_request_sequence":
            str(
                wave_b_sequence
            ),

        "wave_a_request_sequence":
            str(
                item[
                    "wave_a_request_sequence"
                ]
            ),

        "retrieval_record_index":
            source[
                "retrieval_record_index"
            ],

        "screening_entity_id":
            source[
                "screening_entity_id"
            ],

        "pmid":
            pmid,

        "fallback_reason":
            item[
                "fallback_reason"
            ],

        "wave_a_request_identity_sha256":
            item[
                "wave_a_request_identity_sha256"
            ],

        "wave_a_adapter_evidence_sha256":
            item[
                "wave_a_adapter_evidence_sha256"
            ],

        "wave_a_terminal_body_sha256":
            item[
                "wave_a_terminal_body_sha256"
            ],

        "openalex_route":
            frozen_route,

        "openalex_lookup_value":
            identifier,
    })


# ============================================================
# Manifest invariants.
# ============================================================

assert len(
    manifest_rows
) == 25

assert [
    int(
        row[
            "request_sequence"
        ]
    )
    for row in manifest_rows
] == list(
    range(
        1,
        26,
    )
)


assert Counter(
    row[
        "frozen_route"
    ]
    for row in manifest_rows
) == {
    "exact_work_id":
        21,

    "exact_doi":
        4,
}


assert len({
    (
        row[
            "provider"
        ],
        row[
            "frozen_route"
        ],
        row[
            "identifier"
        ],
    )
    for row in manifest_rows
}) == 25


assert len({
    row[
        "request_identity_sha256"
    ]
    for row in manifest_rows
}) == 25


for row in manifest_rows:

    assert (
        wave_a_guard.expected_request_identity(
            row
        )
        == row[
            "request_identity_sha256"
        ]
    )


# ============================================================
# Write deterministic Wave B artifacts.
# ============================================================

manifest_fields = [
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

derivation_fields = [
    "wave_b_request_sequence",
    "wave_a_request_sequence",
    "retrieval_record_index",
    "screening_entity_id",
    "pmid",
    "fallback_reason",
    "wave_a_request_identity_sha256",
    "wave_a_adapter_evidence_sha256",
    "wave_a_terminal_body_sha256",
    "openalex_route",
    "openalex_lookup_value",
]


write_tsv(
    WAVE_B_MANIFEST,
    manifest_fields,
    manifest_rows,
)

write_tsv(
    WAVE_B_DERIVATION,
    derivation_fields,
    derivation_rows,
)


manifest_sha = sha256_file(
    WAVE_B_MANIFEST
)

derivation_sha = sha256_file(
    WAVE_B_DERIVATION
)


# ============================================================
# Freeze design.
# ============================================================

design = {
    "schema_version":
        1,

    "design_id":
        "TRIAGE_PRE_REVIEW_TEXT_WAVE_B_MANIFEST_V1",

    "status":
        "FROZEN_PRE_IMPLEMENTATION",

    "wave_id":
        WAVE_B_ID,

    "design_parent_commit":
        EXPECTED_PARENT_COMMIT,

    "purpose":
        (
            "Freeze the deterministic OpenAlex fallback "
            "request population derived from completed "
            "Wave A PubMed outcomes."
        ),

    "eligibility_contract": {
        "eligible": [
            (
                "Wave A PubMed terminal outcome is "
                "verified_not_found"
            ),
            (
                "Wave A PubMed terminal outcome is "
                "verified_success and the frozen normalizer "
                "returns provider_identity_status=matched, "
                "parser_status=ok, and "
                "abstract_status=abstract_absent"
            ),
        ],

        "not_eligible": [
            "usable_abstract_pubmed",
            "provider identity mismatch",
            "parser failure",
            "retrieval failure or unresolved transport fault",
            "unverifiable evidence",
        ],

        "scientific_exclusion_inference":
            False,
    },

    "candidate_population": {
        "rows":
            25,

        "fallback_reason_counts": {
            "abstract_absent":
                24,

            "verified_not_found":
                1,
        },

        "openalex_route_counts": {
            "exact_work_id":
                21,

            "exact_doi":
                4,

            "exact_pmid":
                0,
        },
    },

    "routing_contract": {
        "provider":
            "openalex",

        "precedence": [
            "exact_work_id",
            "exact_doi",
            "exact_pmid",
        ],

        "actual_routes_in_manifest": [
            "exact_work_id",
            "exact_doi",
        ],
    },

    "request_identity_contract": {
        "implementation":
            (
                "triage_pre_review_text_wave_a_guard_v1."
                "expected_request_identity"
            ),

        "fields": [
            "wave_id",
            "request_sequence",
            "retrieval_record_index",
            "screening_entity_id",
            "provider",
            "frozen_route",
            "transport_route",
            "identifier_namespace",
            "identifier",
        ],
    },

    "source_bindings": {
        "input_manifest": {
            "path":
                str(
                    INPUT_MANIFEST
                ),

            "sha256":
                EXPECTED_INPUT_MANIFEST_SHA256,
        },

        "wave_a_request_manifest": {
            "path":
                str(
                    WAVE_A_MANIFEST
                ),

            "sha256":
                EXPECTED_WAVE_A_MANIFEST_SHA256,
        },

        "normalizer": {
            "path":
                str(
                    NORMALIZER_PATH
                ),

            "sha256":
                EXPECTED_NORMALIZER_SHA256,
        },

        "wave_a_guard": {
            "path":
                str(
                    WAVE_A_GUARD_PATH
                ),

            "sha256":
                sha256_file(
                    WAVE_A_GUARD_PATH
                ),
        },

        "wave_a_authorization_claim_sha256":
            sha256_file(
                claim_path
            ),

        "wave_a_execution_state_sha256":
            sha256_file(
                state_path
            ),

        "wave_a_completion_receipt_sha256":
            sha256_file(
                receipt_path
            ),
    },

    "outputs": {
        "request_manifest": {
            "path":
                str(
                    WAVE_B_MANIFEST
                ),

            "sha256":
                manifest_sha,

            "rows":
                25,
        },

        "derivation_evidence": {
            "path":
                str(
                    WAVE_B_DERIVATION
                ),

            "sha256":
                derivation_sha,

            "rows":
                25,
        },
    },

    "authority_boundary": {
        "network_authorized":
            False,

        "authorization_created":
            False,

        "wave_b_execution_permitted":
            False,

        "production_scientific_screening_changed":
            False,

        "blind_validation_content_used":
            False,
    },

    "next_gate":
        (
            "IMPLEMENT_AND_TEST_WAVE_B_EXECUTION_GUARD_"
            "AND_TRANSPORT_ADAPTER_BEFORE_SEPARATE_"
            "EXPLICIT_HUMAN_AUTHORIZATION"
        ),
}


write_json(
    DESIGN,
    design,
)


design_sha = sha256_file(
    DESIGN
)


# ============================================================
# Human-readable freeze.
# ============================================================

doc = f"""# Triage pre-review text Wave B manifest v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This freeze defines the deterministic Wave B OpenAlex fallback
request population. It does not authorize network access.

## Derivation

Wave A completed 3,956 PubMed logical requests.

Frozen offline normalization identified:

- 3,931 usable PubMed abstracts;
- 24 verified PubMed records with `abstract_absent`;
- 1 verified PubMed `not_found`;
- 0 blocked, malformed, or identity-mismatched PubMed outcomes.

Exactly 25 records therefore satisfy the frozen fallback contract.

## Wave B routes

- 21 exact OpenAlex Work ID requests;
- 4 exact DOI requests;
- 0 exact PMID-only requests.

The frozen precedence remains:

1. exact OpenAlex Work ID;
2. exact DOI;
3. exact PMID.

## Request manifest

Path:

`{WAVE_B_MANIFEST}`

SHA-256:

`{manifest_sha}`

Rows: 25

The request manifest contains transport identity only. It contains no
scientific decision, exclusion reason, review evidence, model score,
batch identifier, or operator note.

## Derivation evidence

Path:

`{WAVE_B_DERIVATION}`

SHA-256:

`{derivation_sha}`

The derivation table records only the Wave A retrieval/normalization
state necessary to establish deterministic fallback eligibility.

## Authority boundary

This freeze:

- does not authorize Wave B network access;
- does not create an authorization artifact;
- does not execute OpenAlex requests;
- does not mutate the production scientific ledger;
- does not use blind-validation content.

A separately implemented and tested Wave B execution boundary must be
frozen before any separate explicit human authorization.

## Design

Design SHA-256:

`{design_sha}`
"""

DOC.write_text(
    doc,
    encoding="utf-8",
)


# ============================================================
# Checksums.
# ============================================================

checksum_targets = [
    FREEZE_SCRIPT,
    DESIGN,
    DOC,
    WAVE_B_MANIFEST,
    WAVE_B_DERIVATION,
]

CHECKSUMS.write_text(
    "".join(
        (
            f"{sha256_file(path)}  "
            f"{path}\n"
        )
        for path in checksum_targets
    ),
    encoding="utf-8",
)


# ============================================================
# Explicitly assert no Wave B live authority exists.
# ============================================================

live_b_execution_root = (
    RESULT_ROOT
    / "live_wave_b"
)

for name in (
    "authorization.json",
    "authorization_claim.json",
    "execution_state.json",
    "completion_receipt.json",
):

    assert not (
        live_b_execution_root
        / name
    ).exists()


print(
    "wave_b_manifest_sha256 =",
    manifest_sha,
)

print(
    "wave_b_derivation_sha256 =",
    derivation_sha,
)

print(
    "wave_b_design_sha256 =",
    design_sha,
)

print(
    "wave_b_rows =",
    len(
        manifest_rows
    ),
)

print(
    "route_counts =",
    dict(
        sorted(
            Counter(
                row[
                    "frozen_route"
                ]
                for row in manifest_rows
            ).items()
        )
    ),
)

print(
    "fallback_reason_counts =",
    dict(
        sorted(
            Counter(
                row[
                    "fallback_reason"
                ]
                for row in derivation_rows
            ).items()
        )
    ),
)

print(
    "PASS | Wave B manifest v1 frozen offline"
)

print(
    "NO AUTHORITY | no Wave B network authorization created"
)
