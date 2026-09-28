from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(
    "experiments/07_comparative_landscape"
)

OUT = Path(
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1"
)

DESIGN = (
    ROOT
    / "triage_pre_review_text_wave_a_transport_evidence_adapter_v1_design.json"
)

DOCUMENT = (
    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_WAVE_A_TRANSPORT_EVIDENCE_ADAPTER_V1.md"
)

EXPECTED_PARENT = (
    "1150286b4c0ff43ef5533657d8c16456c68417db"
)

EXPECTED = {
    "live_design": {
        "path":
            ROOT
            / "triage_pre_review_text_live_retrieval_v1_design.json",

        "sha256":
            "3dff9e1a41196343adc02951b7a88a2b1306e7df05838f3b2ab50ed53ce16172",
    },

    "wave_a_manifest": {
        "path":
            OUT
            / "live_wave_a_request_manifest.tsv",

        "sha256":
            "91a87f2d8a2bfc00ead9a5f1b6e6fcaf850666573583bb07317a1416d446211d",
    },

    "normalizer": {
        "path":
            ROOT
            / "triage_pre_review_text_normalizer_v1.py",

        "sha256":
            "cbe66fc9ab406fa5ee3745e099c16250c404a949c0f301e40a7397c285dc459d",
    },

    "guard": {
        "path":
            ROOT
            / "triage_pre_review_text_wave_a_guard_v1.py",

        "sha256":
            "40dadd678bfe282e196ef007dbb443e4672c578055f1608d737625bae9c5b7af",
    },

    "transport": {
        "path":
            ROOT
            / "retrieve_metadata_resolution_queue.py",

        "sha256":
            "9c8c11edbbec86e5cbf857f25c1bf576a0638ba5cdcf69d1fa2a8b8bfc1a994f",
    },

    "authoritative_transport_policy_source": {
        "path":
            ROOT
            / "t000002_authoritative_source_network_transport.py",

        "sha256":
            "cc68579ff66af7633b7dd79520f748cfbe09cf8f95eaaf5cc927b833c4a7d962",
    },
}


def sha256_file(
    path: Path,
) -> str:

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def git_head() -> str:

    return subprocess.check_output(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()


assert git_head() == EXPECTED_PARENT


for name, record in EXPECTED.items():

    actual = sha256_file(
        record[
            "path"
        ]
    )

    assert (
        actual
        == record[
            "sha256"
        ]
    ), (
        name,
        actual,
        record[
            "sha256"
        ],
    )


design = {
    "schema_version":
        1,

    "design_id":
        "TRIAGE_PRE_REVIEW_TEXT_WAVE_A_TRANSPORT_EVIDENCE_ADAPTER_V1",

    "status":
        "FROZEN_PRE_IMPLEMENTATION",

    "parent_commit":
        EXPECTED_PARENT,

    "purpose":
        (
            "Provide a pure evidence-validation layer between the "
            "frozen exact-identifier transport and the Wave A "
            "authorization guard without modifying either frozen "
            "transport implementation."
        ),

    "authority_boundary": {
        "creates_live_authorization":
            False,

        "creates_network_authority":
            False,

        "performs_network_requests":
            False,

        "performs_scientific_decisions":
            False,

        "performs_model_scoring":
            False,

        "permits_blind_validation_access":
            False,

        "permits_production_ledger_mutation":
            False,
    },

    "transport_roles": {
        "wave_a_execution_transport": {
            "path":
                str(
                    EXPECTED[
                        "transport"
                    ][
                        "path"
                    ]
                ),

            "sha256":
                EXPECTED[
                    "transport"
                ][
                    "sha256"
                ],

            "functions_reused": [
                "build_request",
                "transport_lookup",
                "verify_terminal_archive",
                "ProviderPacer",
            ],

            "modification_permitted":
                False,
        },

        "authoritative_transport_policy_source": {
            "path":
                str(
                    EXPECTED[
                        "authoritative_transport_policy_source"
                    ][
                        "path"
                    ]
                ),

            "sha256":
                EXPECTED[
                    "authoritative_transport_policy_source"
                ][
                    "sha256"
                ],

            "invoked_as_wave_a_request_executor":
                False,

            "role":
                (
                    "Frozen provenance/safety-policy dependency; "
                    "its independent live seed-run authorization "
                    "machinery is not reused as Wave A authority."
                ),

            "modification_permitted":
                False,
        },
    },

    "manifest_to_transport_mapping": {
        "logical_lookup_id":
            (
                "triage_text_wave_a:"
                "{request_sequence:04d}:"
                "{request_identity_sha256_prefix16}"
            ),

        "provider":
            "manifest.provider",

        "route":
            "manifest.transport_route",

        "identifier_namespace":
            "manifest.identifier_namespace",

        "identifier":
            "manifest.identifier",

        "allowed_routes": [
            {
                "provider":
                    "pubmed",

                "manifest_route":
                    "exact_pmid_efetch",

                "transport_route":
                    "record_by_pmid",

                "identifier_namespace":
                    "pmid",
            },

            {
                "provider":
                    "openalex",

                "manifest_route":
                    "exact_work_id",

                "transport_route":
                    "work_by_openalex_id",

                "identifier_namespace":
                    "openalex",
            },

            {
                "provider":
                    "openalex",

                "manifest_route":
                    "exact_doi",

                "transport_route":
                    "work_by_doi",

                "identifier_namespace":
                    "doi",
            },
        ],
    },

    "request_pacing": {
        "maximum_initiation_rate_per_provider_per_second":
            2.0,

        "minimum_interval_seconds":
            0.5,

        "implementation":
            "retrieve_metadata_resolution_queue.ProviderPacer",

        "required_location":
            "executor_wrapper",

        "rule":
            (
                "The injected executor must call "
                "ProviderPacer.wait(request.provider) immediately "
                "before every underlying HTTP executor invocation."
            ),

        "reason":
            (
                "Pacing at logical-lookup level alone does not "
                "cover redirect hops initiated internally by "
                "request_with_redirects."
            ),

        "unpaced_underlying_executor_permitted":
            False,
    },

    "archive_contract": {
        "raw_transport_archive_preserved":
            True,

        "raw_archive_mutation_by_adapter_permitted":
            False,

        "success_or_not_found_requires":
            [
                "transport terminal.json exists",
                "verify_terminal_archive passes",
                "terminal request identity matches frozen manifest-derived transport request",
                "final archived response body SHA matches transport terminal",
            ],

        "normalized_text_may_be_generated_only_after":
            [
                "verified transport archive",
                "provider identity validation",
            ],
    },

    "provider_identity_validation": {
        "pubmed_success": {
            "required":
                True,

            "rule":
                (
                    "Returned primary PMID must equal the exact "
                    "requested PMID. The frozen transport and "
                    "normalizer both enforce this condition."
                ),
        },

        "openalex_work_id_success": {
            "required":
                True,

            "requested_normalization":
                (
                    "Normalize requested value to canonical "
                    "OpenAlex Work token W<digits>."
                ),

            "required_response_evidence": [
                "top-level id is a canonical OpenAlex Work identifier",
                "top-level id Work token equals requested Work token",
                "ids is an object",
                "if ids.openalex is present, its Work token also equals requested Work token",
            ],

            "mismatch_status":
                "provider_identity_mismatch",
        },

        "openalex_doi_success": {
            "required":
                True,

            "requested_normalization":
                (
                    "Trim whitespace, remove DOI URL or doi: "
                    "prefix, and compare case-insensitively."
                ),

            "required_response_evidence": [
                "ids is an object",
                "ids.doi is present and non-empty",
                "normalized ids.doi equals normalized requested DOI",
                "top-level OpenAlex id is present and canonical",
            ],

            "mismatch_status":
                "provider_identity_mismatch",
        },

        "not_found": {
            "identity_status":
                "not_applicable_not_found",

            "rule":
                (
                    "The exact request identity must still match "
                    "the verified archived terminal record."
                ),
        },
    },

    "transport_outcome_policy": {
        "checkpoint_eligible": [
            "verified_success",
            "verified_not_found",
        ],

        "non_checkpointing_execution_faults": [
            "authentication_failure",
            "redirect_failure",
            "response_integrity_failure",
            "retry_exhausted",
            "provider_identity_mismatch",
            "missing_terminal_archive",
            "archive_verification_failure",
            "unknown_transport_status",
        ],

        "fault_action":
            "halt_execution_without_advancing_guard_checkpoint",

        "automatic_retry_after_fault_permitted":
            False,

        "automatic_resume_after_fault_permitted":
            False,

        "fault_recovery":
            (
                "Requires a separately frozen recovery design "
                "before any further live request for the same "
                "manifest position."
            ),

        "rationale":
            (
                "Several frozen transport failure paths return "
                "a status without writing terminal.json. They "
                "must not be silently promoted to verified "
                "terminal evidence or allowed to advance Wave A."
            ),
    },

    "uniform_evidence_record": {
        "output_subdirectory":
            "transport_evidence",

        "filename":
            "{request_sequence:04d}.json",

        "required_fields": [
            "schema_version",
            "wave_id",
            "request_sequence",
            "request_identity_sha256",
            "logical_lookup_id",
            "provider",
            "transport_route",
            "identifier_namespace",
            "identifier",
            "transport_terminal_status",
            "adapter_status",
            "checkpoint_eligible",
            "provider_record_id",
            "provider_identity_status",
            "transport_terminal_json_sha256",
            "terminal_body_sha256",
        ],

        "guard_terminal_receipt": {
            "archived_terminal_sha256":
                "SHA256 of verified raw transport terminal.json",

            "additional_required_field":
                "adapter_evidence_sha256",
        },

        "credential_fields_permitted":
            False,

        "scientific_fields_permitted":
            False,

        "model_fields_permitted":
            False,
    },

    "mock_runner_gate": {
        "next_gate":
            (
                "IMPLEMENT_AND_HOSTILE_TEST_PURE_ADAPTER_AND_"
                "MOCKED_SINGLE_REQUEST_RUNNER_WITH_ZERO_REAL_NETWORK"
            ),

        "requirements": [
            "OpenAlex DOI mismatch is rejected",
            "OpenAlex Work-ID mismatch is rejected",
            "PubMed PMID mismatch remains rejected",
            "success archive tampering is rejected",
            "not-found archive tampering is rejected",
            "transport failure without terminal.json halts and never checkpoints",
            "identity mismatch never checkpoints",
            "pacer wraps every executor invocation including redirect hops",
            "manifest order cannot be skipped or reordered",
            "same manifest request cannot be checkpointed twice",
            "guard checkpoint occurs only after verified adapter evidence is durable",
            "all tests use injected synthetic executor",
            "no test calls default_http_executor",
            "no live authorization is created",
            "production boundary remains unchanged",
        ],
    },

    "frozen_sources": {
        name: {
            "path":
                str(
                    record[
                        "path"
                    ]
                ),

            "sha256":
                record[
                    "sha256"
                ],
        }
        for name, record
        in EXPECTED.items()
    },
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


doc = """# Wave A transport-evidence adapter v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This design creates no live authorization and performs no network
activity.

## Why the adapter exists

The frozen exact-identifier transport is retained byte-for-byte.

Two gaps are handled above that transport:

1. OpenAlex successful responses must be explicitly validated against
   the exact requested Work ID or DOI before they are considered
   checkpoint-eligible.
2. Several transport failure outcomes return a status without writing
   the `terminal.json` required for verified terminal evidence.

The adapter does not rewrite those transport semantics. It validates
them and fails closed where the frozen evidence requirement cannot be
met.

## Checkpoint eligibility

Only two adapter outcomes may advance the Wave A guard:

- `verified_success`;
- `verified_not_found`.

Authentication failure, redirect failure, response-integrity failure,
retry exhaustion, identity mismatch, missing terminal archive, archive
verification failure, and unknown statuses halt execution without
advancing the guard checkpoint.

No automatic retry or automatic live resume after such a fault is
authorized by this design.

## OpenAlex identity

For exact Work-ID retrieval, the canonical Work token returned by
OpenAlex must match the requested Work token.

For exact DOI retrieval, `ids.doi` must be present and normalize to the
same DOI as the exact requested DOI.

A successful HTTP response that fails either comparison is
`provider_identity_mismatch`, not successful evidence.

## Pacing

The existing `ProviderPacer` remains authoritative for the two
requests-per-second provider bound.

The future runner must wrap the injected HTTP executor so that
`ProviderPacer.wait(request.provider)` executes immediately before
every underlying request initiation. This includes redirects as well as
initial requests.

## Evidence order

For checkpoint-eligible outcomes:

1. frozen manifest row;
2. exact transport request;
3. raw transport archive;
4. transport archive verification;
5. provider identity validation;
6. durable adapter evidence record;
7. Wave A guard checkpoint.

The guard may never be advanced before step 6 is durable.

## Next gate

Implement the pure adapter plus a mocked single-request runner.
Every test must use an injected synthetic executor. No real network
request, live authorization, scientific decision, model operation,
future scoring or production mutation is permitted.
"""

DOCUMENT.write_text(
    doc,
    encoding="utf-8",
)


print(
    "design =",
    DESIGN
)

print(
    "document =",
    DOCUMENT
)

print(
    "design SHA256 =",
    sha256_file(
        DESIGN
    )
)

print(
    "document SHA256 =",
    sha256_file(
        DOCUMENT
    )
)

print(
    "PASS | Wave A transport-evidence adapter "
    "design frozen pre-implementation"
)

print(
    "NO AUTHORITY | no network; no authorization; "
    "no production mutation"
)
