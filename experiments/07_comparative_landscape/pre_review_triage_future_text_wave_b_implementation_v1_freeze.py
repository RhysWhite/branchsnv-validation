#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import argparse
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

FREEZE = (
    ROOT
    / "pre_review_triage_future_text_wave_b_implementation_v1_freeze.py"
)

DESIGN = (
    ROOT
    / "pre_review_triage_future_text_wave_b_implementation_v1_design.json"
)

DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_TEXT_WAVE_B_IMPLEMENTATION_V1.md"
)

CHECKSUMS = (
    ROOT
    / "pre_review_triage_future_text_wave_b_implementation_v1.sha256"
)

IMPLEMENTATION_COMMIT = (
    "c410749fec34c726a5a6ce8a76d0ad84df18f2db"
)

WAVE_ID = (
    "TRIAGE_FUTURE_TEXT_LIVE_WAVE_B"
)

EXECUTION_DESIGN = (
    ROOT
    / "pre_review_triage_future_text_wave_b_execution_v1_design.json"
)

MANIFEST_DESIGN = (
    ROOT
    / "pre_review_triage_future_text_wave_b_manifest_v1_design.json"
)

REQUEST_MANIFEST = (
    FUT
    / "live_wave_b_request_manifest.tsv"
)

DERIVATION = (
    FUT
    / "live_wave_b_derivation.tsv"
)

GUARD = (
    ROOT
    / "pre_review_triage_future_text_wave_b_guard_v1.py"
)

ADAPTER = (
    ROOT
    / "pre_review_triage_future_text_wave_b_transport_evidence_adapter_v1.py"
)

RUNNER = (
    ROOT
    / "pre_review_triage_future_text_wave_b_runner_core_v1.py"
)

LIVE = (
    ROOT
    / "pre_review_triage_future_text_wave_b_live_entrypoint_v1.py"
)

FOCUSED_TEST = (
    ROOT
    / "test_pre_review_triage_future_text_wave_b_execution_v1.py"
)

HOSTILE_TEST = (
    ROOT
    / "test_pre_review_triage_future_text_wave_b_live_hostile_v1.py"
)

TRANSPORT = (
    ROOT
    / "retrieve_metadata_resolution_queue.py"
)

TRANSPORT_POLICY = (
    ROOT
    / "t000002_authoritative_source_network_transport.py"
)

NORMALIZER = (
    ROOT
    / "triage_pre_review_text_normalizer_v1.py"
)


EXPECTED = {
    EXECUTION_DESIGN:
        "bb6fe772ccb8d12515d5469a2b790240ffa9da632e87f45187d1e3db73393230",

    MANIFEST_DESIGN:
        "aab3d23f6d7c4b4c155d924730e062d1a9fc14ff57e35a12a9a3df7c03077afd",

    REQUEST_MANIFEST:
        "e6b79c2fff3f31a8155dd7c37188d0ea2c4bd786c7e7de9950570288a2c62d11",

    DERIVATION:
        "7fc3bd6fee6c5a3539587223ef6459df1ecce41ad670de3929836eef7a6c4474",

    GUARD:
        "60dad0cf516e829e4a33c52d693436662dd40dbae02dc7b67ae830dabc9f8610",

    ADAPTER:
        "fff2203b57de35b11fbce2678466196dfcc192599978eedf3e12cf18996271d6",

    RUNNER:
        "bf94d9d84d74783fbe05b4414738b332d0ed9bfe8fad8798c09b3775c03df101",

    LIVE:
        "47c64d12ea4a79724ed3eede9355f3c14cb9e2602c458968622f5861d21ffc48",

    FOCUSED_TEST:
        "dd8638517d8b7656609814b19c7a2ecd2a3e555d85f62f334262c37385077d26",

    HOSTILE_TEST:
        "666146dc99d2aaf379df8fcb655c65918080d70b372ac5f0b6777bce783919e2",

    TRANSPORT:
        "9c8c11edbbec86e5cbf857f25c1bf576a0638ba5cdcf69d1fa2a8b8bfc1a994f",

    TRANSPORT_POLICY:
        "cc68579ff66af7633b7dd79520f748cfbe09cf8f95eaaf5cc927b833c4a7d962",

    NORMALIZER:
        "cbe66fc9ab406fa5ee3745e099c16250c404a949c0f301e40a7397c285dc459d",
}


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


def verify_sources() -> None:

    for path, expected in (
        EXPECTED.items()
    ):

        if not path.is_file():

            raise FreezeError(
                "missing frozen source: "
                + str(
                    path
                )
            )

        actual = sha256_file(
            path
        )

        if actual != expected:

            raise FreezeError(
                "frozen source hash mismatch: "
                + str(
                    path
                )
                + "\nexpected="
                + expected
                + "\nactual="
                + actual
            )


def build():

    verify_sources()

    design = {
        "freeze_id":
            "PRE_REVIEW_TRIAGE_FUTURE_TEXT_WAVE_B_IMPLEMENTATION_V1",

        "schema_version":
            1,

        "status":
            "FROZEN_PRE_AUTHORIZATION",

        "wave_id":
            WAVE_ID,

        "implementation_commit":
            IMPLEMENTATION_COMMIT,

        "freeze_parent_commit":
            IMPLEMENTATION_COMMIT,

        "implementation_source_sha256": {
            str(GUARD):
                EXPECTED[GUARD],

            str(ADAPTER):
                EXPECTED[ADAPTER],

            str(RUNNER):
                EXPECTED[RUNNER],

            str(LIVE):
                EXPECTED[LIVE],
        },

        "test_source_sha256": {
            str(FOCUSED_TEST):
                EXPECTED[FOCUSED_TEST],

            str(HOSTILE_TEST):
                EXPECTED[HOSTILE_TEST],
        },

        "frozen_upstream": {
            "execution_design_sha256":
                EXPECTED[
                    EXECUTION_DESIGN
                ],

            "manifest_design_sha256":
                EXPECTED[
                    MANIFEST_DESIGN
                ],

            "request_manifest_sha256":
                EXPECTED[
                    REQUEST_MANIFEST
                ],

            "derivation_sha256":
                EXPECTED[
                    DERIVATION
                ],

            "normalizer_sha256":
                EXPECTED[
                    NORMALIZER
                ],

            "exact_transport_sha256":
                EXPECTED[
                    TRANSPORT
                ],

            "transport_policy_sha256":
                EXPECTED[
                    TRANSPORT_POLICY
                ],
        },

        "execution_contract": {
            "provider":
                "openalex",

            "maximum_request_count":
                40,

            "ordering":
                "strict ascending request_sequence",

            "concurrency":
                1,

            "maximum_requests_per_second":
                2,

            "cold_start_seconds":
                0.5,

            "allowed_routes": [
                {
                    "frozen_route":
                        "exact_work_id",

                    "transport_route":
                        "work_by_openalex_id",

                    "identifier_namespace":
                        "openalex",
                },
                {
                    "frozen_route":
                        "exact_doi",

                    "transport_route":
                        "work_by_doi",

                    "identifier_namespace":
                        "doi",
                },
                {
                    "frozen_route":
                        "exact_pmid",

                    "transport_route":
                        "work_by_pmid",

                    "identifier_namespace":
                        "pmid",
                },
            ],

            "search_or_list_endpoints_permitted":
                False,

            "crossref_permitted":
                False,

            "pubmed_provider_permitted":
                False,

            "ad_hoc_probe_permitted":
                False,

            "automatic_reissue_after_ambiguous_network_intent":
                False,

            "same_execution_id_resume_only":
                True,

            "runtime_invariants_rechecked_between_requests":
                True,

            "cross_process_execution_lock_required":
                True,

            "credential_values_must_not_be_archived":
                True,
        },

        "test_contract": {
            "focused_future_tests":
                13,

            "future_live_hostile_tests":
                30,

            "future_total_tests":
                43,

            "required_result":
                "all tests pass",

            "exact_pmid_success_identity_tested":
                True,

            "exact_pmid_missing_identity_fails_closed_tested":
                True,

            "exact_pmid_wrong_identity_fails_closed_tested":
                True,

            "exact_pmid_not_found_checkpoint_eligible_tested":
                True,

            "partial_archive_replay_prohibited_tested":
                True,

            "same_execution_id_no_reissue_tested":
                True,

            "different_execution_id_rejected_tested":
                True,

            "runtime_invariant_recheck_tested":
                True,

            "cross_process_lock_tested":
                True,

            "real_default_network_executor_blocked_in_tests":
                True,
        },

        "authorization_gate": {
            "authorization_created_by_this_freeze":
                False,

            "network_authorized_by_this_freeze":
                False,

            "explicit_human_authorization_required":
                True,

            "authorization_must_bind_exact_current_git_head":
                True,

            "authorization_must_remain_untracked_at_execution":
                True,

            "one_use":
                True,

            "same_execution_id_resume_permitted":
                True,

            "second_execution_id_with_same_authorization_permitted":
                False,

            "completed_authorization_replay_permitted":
                False,

            "wave_a_authorization_reusable":
                False,
        },

        "freeze_commit_binding":
            (
                "The executable authorization boundary is the "
                "git commit containing this exact freeze artifact "
                "together with the exact implementation and test "
                "hashes recorded here. Any later authorization "
                "must bind that exact clean current HEAD."
            ),

        "preservation_contract": {
            "low_level_transport_byte_identical":
                True,

            "transport_policy_byte_identical":
                True,

            "normalizer_byte_identical":
                True,

            "development_wave_b_sources_byte_identical":
                True,

            "future_wave_a_sources_and_archives_byte_identical":
                True,

            "production_mutation_permitted":
                False,

            "blind_validation_content_used":
                False,

            "scientific_decision_fields_permitted_in_transport_evidence":
                False,
        },

        "next_gate":
            (
                "OBTAIN_SEPARATE_EXPLICIT_ONE_USE_HUMAN_"
                "FUTURE_WAVE_B_NETWORK_AUTHORIZATION_BOUND_"
                "TO_THE_RESULTING_IMPLEMENTATION_FREEZE_HEAD"
            ),
    }

    design_body = canonical_json_bytes(
        design
    )

    design_sha = sha256_bytes(
        design_body
    )

    doc = f"""# Pre-review triage future text Wave B implementation v1

Status: `FROZEN_PRE_AUTHORIZATION`

## Executable implementation

The Future Wave B executable layer is frozen from implementation commit:

`{IMPLEMENTATION_COMMIT}`

The frozen implementation contains:

- Future Wave B authorization guard;
- Future Wave B transport-evidence adapter;
- Future Wave B runner core;
- Future Wave B live entrypoint;
- focused execution tests;
- live hostile tests.

## Frozen request population

Exactly 40 OpenAlex requests are permitted:

- 31 `exact_work_id -> work_by_openalex_id`;
- 8 `exact_doi -> work_by_doi`;
- 1 `exact_pmid -> work_by_pmid`.

No search/list endpoint, Crossref route, PubMed provider route, or ad-hoc probe
is permitted.

## Test boundary

The committed clean implementation passes 43 Future Wave B tests:

- 13 focused implementation tests;
- 30 live hostile tests.

The suite covers exact-PMID success identity, missing/wrong PMID fail-closed
behaviour, exact-PMID verified-not-found checkpointing, partial-archive replay
prevention, durable same-execution-ID recovery without reissue, different-ID
rejection, runtime invariant rechecks, and cross-process execution locking.

The real default network executor is blocked during hostile testing.

## Authorization boundary

This implementation freeze does not create authorization.

It does not authorize network access.

The earlier Future Wave A authorization cannot be reused.

A new explicit one-use human Future Wave B authorization is required and must
bind the exact clean git HEAD containing this freeze artifact.

The authorization must remain untracked.

## Preservation boundary

The low-level transport, transport-policy implementation, normalizer,
historical development Wave B implementation, Future Wave A implementation and
Future Wave A archives remain unchanged.

No reconciliation, future scoring, model fitting, threshold selection,
scientific screening, or blind-validation scientific inspection is performed
by this freeze.

## Next gate

`OBTAIN_SEPARATE_EXPLICIT_ONE_USE_HUMAN_FUTURE_WAVE_B_NETWORK_AUTHORIZATION_BOUND_TO_THE_RESULTING_IMPLEMENTATION_FREEZE_HEAD`
"""

    doc_body = doc.encode(
        "utf-8"
    )

    doc_sha = sha256_bytes(
        doc_body
    )

    freeze_sha = sha256_file(
        FREEZE
    )

    checksum_records = {
        str(FREEZE):
            freeze_sha,

        str(DESIGN):
            design_sha,

        str(DOC):
            doc_sha,
    }

    for path, digest in (
        EXPECTED.items()
    ):
        checksum_records[
            str(path)
        ] = digest

    checksum_body = "".join(
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

    return {
        DESIGN:
            design_body,

        DOC:
            doc_body,

        CHECKSUMS:
            checksum_body,
    }, {
        "implementation_freeze_design_sha256":
            design_sha,

        "implementation_freeze_document_sha256":
            doc_sha,

        "implementation_freeze_generator_sha256":
            freeze_sha,
    }


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--verify-only",
        action="store_true",
    )

    args = parser.parse_args()

    if not args.verify_only:

        head = subprocess.check_output(
            [
                "git",
                "rev-parse",
                "HEAD",
            ],
            text=True,
        ).strip()

        if head != IMPLEMENTATION_COMMIT:

            raise FreezeError(
                "wrong implementation parent HEAD: "
                + head
            )

    outputs, hashes = build()

    if args.verify_only:

        for path, expected in (
            outputs.items()
        ):

            if not path.is_file():

                raise FreezeError(
                    "missing implementation-freeze output: "
                    + str(
                        path
                    )
                )

            if (
                path.read_bytes()
                != expected
            ):

                raise FreezeError(
                    "implementation-freeze output "
                    "does not reproduce byte-identically: "
                    + str(
                        path
                    )
                )

        print(
            "PASS | implementation freeze "
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
            "PASS | Future Wave-B implementation "
            "freeze created"
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
        "implementation_commit =",
        IMPLEMENTATION_COMMIT,
    )

    print(
        "future_tests = 43"
    )

    print(
        "maximum_request_count = 40"
    )

    print(
        "NETWORK_AUTHORIZED=NO"
    )

    print(
        "AUTHORIZATION_CREATED=NO"
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
