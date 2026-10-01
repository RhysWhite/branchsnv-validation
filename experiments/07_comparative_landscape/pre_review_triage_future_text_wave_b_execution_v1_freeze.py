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
    / "pre_review_triage_future_text_wave_b_execution_v1_freeze.py"
)

DESIGN = (
    ROOT
    / "pre_review_triage_future_text_wave_b_execution_v1_design.json"
)

DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_TEXT_WAVE_B_EXECUTION_V1.md"
)

CHECKSUMS = (
    ROOT
    / "pre_review_triage_future_text_wave_b_execution_v1.sha256"
)

EXPECTED_PARENT = (
    "8a476d1183b03a42ec6d06df6fb6ddb4e9fb8bbe"
)

WAVE_ID = (
    "TRIAGE_FUTURE_TEXT_LIVE_WAVE_B"
)

OUTPUT_ROOT = (
    "results/07_comparative_landscape/"
    "pre_review_triage_future_text_retrieval_v1/"
    "live_wave_b"
)

AUTHORIZATION_TYPE = (
    "TRIAGE_FUTURE_TEXT_LIVE_WAVE_B_AUTHORIZATION"
)

AUTHORIZATION_STATEMENT = (
    "AUTHORIZE_TRIAGE_FUTURE_TEXT_LIVE_WAVE_B"
)

MANIFEST = (
    FUT
    / "live_wave_b_request_manifest.tsv"
)

DERIVATION = (
    FUT
    / "live_wave_b_derivation.tsv"
)

MANIFEST_DESIGN = (
    ROOT
    / "pre_review_triage_future_text_wave_b_manifest_v1_design.json"
)

MANIFEST_FREEZE = (
    ROOT
    / "pre_review_triage_future_text_wave_b_manifest_v1_freeze.py"
)

MANIFEST_DOC = (
    ROOT
    / "PRE_REVIEW_TRIAGE_FUTURE_TEXT_WAVE_B_MANIFEST_V1.md"
)

MANIFEST_CHECKSUMS = (
    ROOT
    / "pre_review_triage_future_text_wave_b_manifest_v1.sha256"
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

FUTURE_WAVE_A_GUARD = (
    ROOT
    / "pre_review_triage_future_text_wave_a_guard_v1.py"
)

DEV_GUARD = (
    ROOT
    / "triage_pre_review_text_wave_b_guard_v1.py"
)

DEV_ADAPTER = (
    ROOT
    / "triage_pre_review_text_wave_b_transport_evidence_adapter_v1.py"
)

DEV_RUNNER = (
    ROOT
    / "triage_pre_review_text_wave_b_runner_core_v1.py"
)

DEV_LIVE = (
    ROOT
    / "triage_pre_review_text_wave_b_live_entrypoint_v1.py"
)

DEV_TEST = (
    ROOT
    / "test_triage_pre_review_text_wave_b_execution_v1.py"
)

DEV_HOSTILE = (
    ROOT
    / "test_triage_pre_review_text_wave_b_live_hostile_v1.py"
)


EXPECTED_HASHES = {
    MANIFEST:
        "e6b79c2fff3f31a8155dd7c37188d0ea2c4bd786c7e7de9950570288a2c62d11",

    DERIVATION:
        "7fc3bd6fee6c5a3539587223ef6459df1ecce41ad670de3929836eef7a6c4474",

    MANIFEST_DESIGN:
        "aab3d23f6d7c4b4c155d924730e062d1a9fc14ff57e35a12a9a3df7c03077afd",

    MANIFEST_FREEZE:
        "50267b7027e875ff04c7fdafe78815495661295c2a3e75edbdf0ce3fe6321007",

    MANIFEST_DOC:
        "e69d281c47cb39f2568ebf8217b1b7da0985dc4ba383e2e8e4d76be92c174f3e",

    TRANSPORT:
        "9c8c11edbbec86e5cbf857f25c1bf576a0638ba5cdcf69d1fa2a8b8bfc1a994f",

    TRANSPORT_POLICY:
        "cc68579ff66af7633b7dd79520f748cfbe09cf8f95eaaf5cc927b833c4a7d962",

    NORMALIZER:
        "cbe66fc9ab406fa5ee3745e099c16250c404a949c0f301e40a7397c285dc459d",

    FUTURE_WAVE_A_GUARD:
        "79300875f7620afde503f70b27a78449d11fcda35c23b11dc44d2fe538bcb28c",

    DEV_GUARD:
        "dfbd56b90ae47068f880328e21f3c3cc52aa86ef7c80db9c5f069342bc025cb3",

    DEV_ADAPTER:
        "d6d04019521f1bec3d1d9b27014fb5718a774488d93b8a48852a483b51664a79",

    DEV_RUNNER:
        "3bdbf2d827eadc2c5d7d25593cba9231da65336722f70e01e59aeba3248f1b3f",

    DEV_LIVE:
        "beb0bf427a0c4f935d9c58655aa80c0cbb859705b373fd901827c451b580c2e7",

    DEV_TEST:
        "48619aa35b016efe9d15926608a7c49e482b158b69cf07083faea8d7e13f8332",

    DEV_HOSTILE:
        "0cb3ba9bdcb5f7efd10d16cdc69bc6cf59e53445191ce09e3d19940c5b408663",
}


class FreezeError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(
        value
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(
        path.read_bytes()
    )


def canonical_json_bytes(value) -> bytes:
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


def check_sources() -> None:

    for path, expected in (
        EXPECTED_HASHES.items()
    ):
        if not path.is_file():
            raise FreezeError(
                f"missing dependency: {path}"
            )

        actual = sha256_file(
            path
        )

        if actual != expected:
            raise FreezeError(
                "dependency hash mismatch: "
                f"{path}\n"
                f"expected={expected}\n"
                f"actual={actual}"
            )

    if not MANIFEST_CHECKSUMS.is_file():
        raise FreezeError(
            "Wave-B manifest checksum freeze missing"
        )


def build():

    check_sources()

    design = {
        "design_id":
            "PRE_REVIEW_TRIAGE_FUTURE_TEXT_WAVE_B_EXECUTION_V1",

        "schema_version":
            1,

        "status":
            "FROZEN_PRE_IMPLEMENTATION",

        "wave_id":
            WAVE_ID,

        "design_parent_commit":
            EXPECTED_PARENT,

        "request_contract": {
            "provider":
                "openalex",

            "maximum_request_count":
                40,

            "manifest_path":
                str(
                    MANIFEST
                ),

            "manifest_sha256":
                EXPECTED_HASHES[
                    MANIFEST
                ],

            "derivation_path":
                str(
                    DERIVATION
                ),

            "derivation_sha256":
                EXPECTED_HASHES[
                    DERIVATION
                ],

            "allowed_exact_routes": [
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

            "route_population": {
                "exact_work_id":
                    31,

                "exact_doi":
                    8,

                "exact_pmid":
                    1,
            },

            "search_or_list_endpoints_permitted":
                False,

            "crossref_permitted":
                False,

            "pubmed_provider_permitted":
                False,

            "ad_hoc_probe_permitted":
                False,
        },

        "openalex_identity_contract": {
            "exact_work_id":
                (
                    "Returned OpenAlex Work identity must "
                    "match the requested Work ID, subject "
                    "only to the already validated canonical "
                    "OpenAlex Work redirect contract."
                ),

            "exact_doi":
                (
                    "Returned OpenAlex payload must carry "
                    "the requested DOI identity after pinned "
                    "DOI normalization."
                ),

            "exact_pmid":
                (
                    "Returned OpenAlex payload must carry "
                    "the exact requested PMID identity in its "
                    "provider identifier bundle. Absence, "
                    "multiplicity incompatible with the exact "
                    "request, or disagreement is a provider "
                    "identity mismatch."
                ),

            "position_gap":
                (
                    "OpenAlex normalization position-gap "
                    "remains explicit and cannot be treated "
                    "as an ordinary usable abstract."
                ),
        },

        "execution_contract": {
            "ordering":
                "strict ascending request_sequence",

            "concurrency":
                1,

            "maximum_requests_per_second_per_provider":
                2,

            "cold_start_seconds_before_first_openalex_request":
                0.5,

            "halt_on_first_unresolved_fault":
                True,

            "automatic_reissue_after_ambiguous_network_intent":
                False,

            "same_execution_id_resume_only":
                True,

            "logical_lookup_id_format":
                (
                    "triage_future_text_wave_b:"
                    "{request_sequence:04d}:"
                    "{request_identity_sha256_prefix16}"
                ),

            "output_root":
                OUTPUT_ROOT,

            "request_written_before_network":
                True,

            "terminal_checkpoint_after_verified_terminal_only":
                True,

            "raw_archive_bundle_sha256_required_for_checkpoint":
                True,

            "terminal_body_sha256_required":
                True,

            "runtime_invariants_rechecked_between_requests":
                True,

            "cross_process_execution_lock_required":
                True,
        },

        "authorization_contract": {
            "authorization_type":
                AUTHORIZATION_TYPE,

            "authorization_statement":
                AUTHORIZATION_STATEMENT,

            "canonical_path":
                OUTPUT_ROOT
                + "/authorization.json",

            "explicit_human_authorization_required":
                True,

            "authorization_created_by_this_freeze":
                False,

            "must_be_untracked_at_execution_time":
                True,

            "authorization_must_bind_exact_executable_commit":
                True,

            "one_use":
                True,

            "execution_id_bound_at_first_start":
                True,

            "same_execution_id_resume_permitted":
                True,

            "second_execution_id_with_same_authorization_permitted":
                False,

            "completed_authorization_replay_permitted":
                False,

            "wave_a_authorization_permitted":
                False,
        },

        "implementation_strategy": {
            "create_future_wave_b_specific_guard":
                True,

            "create_future_wave_b_specific_transport_evidence_adapter":
                True,

            "create_future_wave_b_specific_runner_core":
                True,

            "create_future_wave_b_specific_live_entrypoint":
                True,

            "create_future_wave_b_specific_tests":
                True,

            "development_wave_b_files_must_remain_byte_identical":
                True,

            "future_wave_a_files_must_remain_byte_identical":
                True,

            "reuse_low_level_transport_unchanged":
                True,

            "reuse_normalizer_unchanged":
                True,

            "reuse_transport_policy_module_as_execution_authority":
                False,
        },

        "required_hostile_tests": {
            "exact_work_id_success_identity":
                True,

            "exact_doi_success_identity":
                True,

            "exact_pmid_success_identity":
                True,

            "exact_pmid_missing_requested_identity_fails_closed":
                True,

            "exact_pmid_wrong_requested_identity_fails_closed":
                True,

            "exact_pmid_not_found_checkpointable":
                True,

            "non_openalex_provider_rejected":
                True,

            "unlisted_route_rejected":
                True,

            "partial_archive_never_reissued":
                True,

            "durable_evidence_resume_never_reissues":
                True,

            "different_execution_id_rejected":
                True,

            "wrong_head_rejected_before_claim":
                True,

            "dirty_tree_rejected_before_claim":
                True,

            "authorization_byte_drift_rejected":
                True,

            "concurrent_execution_rejected":
                True,

            "runtime_invariants_rechecked_between_requests":
                True,

            "real_network_executor_blocked_in_tests":
                True,
        },

        "frozen_dependencies": {
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
        },

        "preservation_contract": {
            "low_level_transport_byte_identical":
                True,

            "development_wave_b_sources_byte_identical":
                True,

            "future_wave_a_sources_byte_identical":
                True,

            "future_wave_a_archives_byte_identical":
                True,

            "blind_validation_content_used":
                False,

            "scientific_decision_fields_permitted_in_transport_evidence":
                False,
        },

        "safety_boundary": {
            "authorization_created":
                False,

            "network_authorized":
                False,

            "network_execution_permitted":
                False,

            "production_mutation_permitted":
                False,

            "reconciliation_performed":
                False,

            "future_scoring_performed":
                False,

            "model_fit_permitted":
                False,

            "threshold_selection_permitted":
                False,

            "blind_validation_scientific_content_used":
                False,
        },

        "next_gate":
            (
                "IMPLEMENT_AND_HOSTILE_TEST_FUTURE_WAVE_B_"
                "GUARD_ADAPTER_RUNNER_AND_LIVE_ENTRYPOINT_"
                "THEN_FREEZE_EXECUTABLE_COMMIT_BEFORE_"
                "SEPARATE_HUMAN_AUTHORIZATION"
            ),
    }

    design_body = canonical_json_bytes(
        design
    )

    design_sha = sha256_bytes(
        design_body
    )

    doc = f"""# Pre-review triage future text Wave B execution v1

Status: `FROZEN_PRE_IMPLEMENTATION`

## Purpose

This design defines the executable safety contract for the 40-request
Future Wave B OpenAlex fallback population.

It does not authorize network execution.

## Frozen population

Future Wave B contains exactly 40 OpenAlex exact lookups:

- 31 `exact_work_id -> work_by_openalex_id`;
- 8 `exact_doi -> work_by_doi`;
- 1 `exact_pmid -> work_by_pmid`.

The exact-PMID request is frozen Wave B request sequence 32.

## Transport boundary

The existing low-level exact transport already supports
`work_by_pmid`; it must remain byte-identical.

The historical development Wave B execution layer supports only
Work-ID and DOI routes and therefore must not be used unchanged for
this future population.

Future-specific guard and adapter implementations are required.

## Exact-PMID identity

A successful `work_by_pmid` response is checkpoint-eligible only when
the archived OpenAlex payload carries the exact requested PMID identity
under the future adapter's pinned normalization rules.

A missing or incompatible PMID identity is a fail-closed provider
identity mismatch.

The exact-PMID success, mismatch and not-found paths must be explicitly
hostile-tested before authorization is possible.

## Authorization boundary

No authorization is created by this freeze.

Future Wave B requires a separate explicit human authorization bound to
the final executable implementation commit.

The Future Wave A authorization cannot authorize this execution.

## Execution semantics

Requests execute sequentially in frozen manifest order with concurrency
1 and a maximum provider rate of 2 requests per second.

Partial archives, identity failures, non-checkpointing transport faults,
or unverifiable evidence halt execution. Automatic replay across an
ambiguous network-send boundary is forbidden.

Same-execution-ID durable-evidence recovery is permitted; a second
execution ID under the same one-use authorization is forbidden.

## Next gate

`IMPLEMENT_AND_HOSTILE_TEST_FUTURE_WAVE_B_GUARD_ADAPTER_RUNNER_AND_LIVE_ENTRYPOINT_THEN_FREEZE_EXECUTABLE_COMMIT_BEFORE_SEPARATE_HUMAN_AUTHORIZATION`
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
        str(
            FREEZE
        ):
            freeze_sha,

        str(
            DESIGN
        ):
            design_sha,

        str(
            DOC
        ):
            doc_sha,
    }

    for path, digest in (
        EXPECTED_HASHES.items()
    ):
        checksum_records[
            str(path)
        ] = digest

    checksum_records[
        str(
            MANIFEST_CHECKSUMS
        )
    ] = sha256_file(
        MANIFEST_CHECKSUMS
    )

    checksums_body = "".join(
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
            checksums_body,
    }, {
        "design_sha256":
            design_sha,

        "document_sha256":
            doc_sha,

        "freeze_generator_sha256":
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

        if head != EXPECTED_PARENT:
            raise FreezeError(
                "wrong design parent commit: "
                + head
            )

    outputs, hashes = build()

    if args.verify_only:

        for path, expected in (
            outputs.items()
        ):
            if not path.is_file():
                raise FreezeError(
                    f"missing frozen output: {path}"
                )

            if path.read_bytes() != expected:
                raise FreezeError(
                    "frozen execution-design output "
                    f"does not reproduce: {path}"
                )

        print(
            "PASS | future Wave-B execution design "
            "reproduces byte-identically"
        )

    else:

        for path in outputs:
            if path.exists():
                raise FreezeError(
                    f"refusing overwrite: {path}"
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
            "PASS | future Wave-B execution "
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
        "maximum_request_count = 40"
    )

    print(
        "allowed_routes = "
        "exact_work_id,exact_doi,exact_pmid"
    )

    print(
        "exact_pmid_request_count = 1"
    )

    print(
        "NETWORK_AUTHORIZED=NO"
    )

    print(
        "EXECUTION_PERMITTED=NO"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
