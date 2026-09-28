from pathlib import Path
import hashlib
import json

ROOT = Path(
    "experiments/07_comparative_landscape"
)

RESULT_ROOT = Path(
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1"
)

DESIGN = (
    ROOT
    / "triage_pre_review_text_wave_b_execution_v1_design.json"
)

DOC = (
    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_WAVE_B_EXECUTION_V1.md"
)

FREEZE = (
    ROOT
    / "triage_pre_review_text_wave_b_execution_v1_freeze.py"
)

SUMS = (
    ROOT
    / "triage_pre_review_text_wave_b_execution_v1.sha256"
)

MANIFEST = (
    RESULT_ROOT
    / "live_wave_b_request_manifest.tsv"
)

DERIVATION = (
    RESULT_ROOT
    / "live_wave_b_derivation.tsv"
)

NORMALIZER = (
    ROOT
    / "triage_pre_review_text_normalizer_v1.py"
)

TRANSPORT = (
    ROOT
    / "retrieve_metadata_resolution_queue.py"
)

TRANSPORT_POLICY = (
    ROOT
    / "t000002_authoritative_source_network_transport.py"
)

WAVE_A_GUARD = (
    ROOT
    / "triage_pre_review_text_wave_a_guard_v1.py"
)

WAVE_A_ADAPTER = (
    ROOT
    / "triage_pre_review_text_wave_a_transport_evidence_adapter_v1.py"
)

WAVE_A_RUNNER = (
    ROOT
    / "triage_pre_review_text_wave_a_runner_core_v1.py"
)

WAVE_A_ENTRYPOINT = (
    ROOT
    / "triage_pre_review_text_wave_a_live_entrypoint_v1.py"
)


EXPECTED = {
    str(MANIFEST):
        (
            "f099f86cce2321ab07d639aeef557014585faf49e"
            "2306a09f3fe40119535f0a6"
        ),

    str(DERIVATION):
        (
            "a58356439478ca27a48c3967dbbab6a16b275987"
            "dc4af7b19f67dd430eeab32b"
        ),

    str(NORMALIZER):
        (
            "cbe66fc9ab406fa5ee3745e099c16250c404a949"
            "c0f301e40a7397c285dc459d"
        ),

    str(TRANSPORT):
        (
            "9c8c11edbbec86e5cbf857f25c1bf576a0638ba5"
            "cdcf69d1fa2a8b8bfc1a994f"
        ),

    str(TRANSPORT_POLICY):
        (
            "cc68579ff66af7633b7dd79520f748cfbe09cf8f"
            "95eaaf5cc927b833c4a7d962"
        ),

    str(WAVE_A_GUARD):
        (
            "40dadd678bfe282e196ef007dbb443e4672c578055"
            "f1608d737625bae9c5b7af"
        ),

    str(WAVE_A_ADAPTER):
        (
            "30a311626b3e99e6520601585b87df3b600991094"
            "d7724cd358b52159d902bac"
        ),

    str(WAVE_A_RUNNER):
        (
            "d1b4a3cff4a99e91d5ea35446e204426bd4794e3"
            "c81b769d386c22d5c5e529ad"
        ),

    str(WAVE_A_ENTRYPOINT):
        (
            "f27d23cc311d7959ced8db865026dcaa8162af6d4"
            "b6ac1b2a579b1b715e7239a"
        ),
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


for raw_path, expected_sha in EXPECTED.items():

    path = Path(raw_path)

    assert path.is_file(), path

    actual = sha256_file(path)

    assert actual == expected_sha, (
        path,
        actual,
        expected_sha,
    )


design = {
    "schema_version": 1,

    "design_id":
        "TRIAGE_PRE_REVIEW_TEXT_WAVE_B_EXECUTION_V1",

    "status":
        "FROZEN_PRE_IMPLEMENTATION",

    "wave_id":
        "TRIAGE_TEXT_LIVE_WAVE_B",

    "design_parent_commit":
        (
            "885bc43b845790ec85a29a9063b844217b36b67d"
        ),

    "request_contract": {
        "manifest_path":
            str(MANIFEST),

        "manifest_sha256":
            EXPECTED[str(MANIFEST)],

        "maximum_request_count":
            25,

        "provider":
            "openalex",

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
        ],

        "pubmed_permitted":
            False,

        "search_or_list_endpoints_permitted":
            False,

        "crossref_permitted":
            False,

        "ad_hoc_probe_permitted":
            False,
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
                "triage_text_wave_b:"
                "{request_sequence:04d}:"
                "{request_identity_sha256_prefix16}"
            ),

        "output_root":
            (
                "results/07_comparative_landscape/"
                "triage_pre_review_text_retrieval_v1/"
                "live_wave_b"
            ),
    },

    "openalex_identity_contract": {
        "exact_work_id":
            (
                "returned OpenAlex Work identity must match the "
                "requested Work ID, subject only to the already-"
                "validated canonical Work redirect contract"
            ),

        "exact_doi":
            (
                "returned DOI identity must match the requested "
                "normalized DOI"
            ),

        "position_gap":
            (
                "normalization position-gap remains explicit and "
                "must not be treated as an ordinary usable abstract"
            ),
    },

    "archive_contract": {
        "request_written_before_network":
            True,

        "terminal_body_sha256_required":
            True,

        "raw_archive_bundle_sha256_required_for_checkpoint":
            True,

        "terminal_checkpoint_after_verified_terminal_only":
            True,

        "credentials_must_be_redacted_from_persisted_urls":
            True,

        "credential_values_must_not_be_archived":
            True,
    },

    "authorization_contract": {
        "explicit_human_authorization_required":
            True,

        "authorization_type":
            "TRIAGE_TEXT_LIVE_WAVE_B_AUTHORIZATION",

        "authorization_statement":
            "AUTHORIZE_TRIAGE_TEXT_LIVE_WAVE_B",

        "canonical_path":
            (
                "results/07_comparative_landscape/"
                "triage_pre_review_text_retrieval_v1/"
                "live_wave_b/authorization.json"
            ),

        "must_be_untracked_at_execution_time":
            True,

        "one_use":
            True,

        "execution_id_bound_at_first_start":
            True,

        "second_execution_id_with_same_authorization_permitted":
            False,

        "completed_authorization_replay_permitted":
            False,

        "authorization_created_by_this_freeze":
            False,
    },

    "implementation_strategy": {
        "modify_wave_a_implementation":
            False,

        "wave_a_files_must_remain_byte_identical":
            True,

        "create_wave_b_specific_guard":
            True,

        "create_wave_b_specific_transport_evidence_adapter":
            True,

        "create_wave_b_specific_runner_core":
            True,

        "create_wave_b_specific_live_entrypoint":
            True,

        "reuse_low_level_transport_unchanged":
            True,

        "reuse_transport_policy_module_as_execution_authority":
            False,
    },

    "frozen_dependencies": {
        path:
            digest
        for path, digest in EXPECTED.items()
    },

    "safety_boundary": {
        "network_authorized":
            False,

        "authorization_created":
            False,

        "network_execution_permitted":
            False,

        "production_mutation_permitted":
            False,

        "blind_validation_content_used":
            False,

        "scientific_decision_fields_permitted_in_transport_evidence":
            False,
    },

    "next_gate":
        (
            "IMPLEMENT_AND_HOSTILE_TEST_WAVE_B_GUARD_ADAPTER_"
            "RUNNER_AND_LIVE_ENTRYPOINT_THEN_FREEZE_FINAL_"
            "EXECUTABLE_COMMIT_BEFORE_HUMAN_AUTHORIZATION"
        ),
}


DESIGN.write_text(
    json.dumps(
        design,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)


design_sha = sha256_file(
    DESIGN
)


DOC.write_text(
    f"""# Triage pre-review text Wave B execution v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This design defines the execution boundary for the already frozen
25-request Wave B OpenAlex fallback manifest.

It does not authorize network access.

## Request population

Wave B contains exactly 25 requests:

- 21 exact OpenAlex Work ID requests;
- 4 exact DOI requests.

PubMed, OpenAlex search/list endpoints, Crossref, and ad hoc probes
are outside this execution contract.

## Architecture

The frozen Wave A implementation remains byte-identical.

Wave B receives dedicated:

- authorization guard;
- transport-evidence adapter;
- runner core;
- live entrypoint.

The already frozen low-level HTTP transport is reused unchanged.

The historical T000002 transport module remains a frozen
provenance/safety dependency and is not Wave B execution authority.

## Execution

Requests execute serially in ascending request sequence.

Concurrency is one.

OpenAlex is limited to no more than two requests per second, including
redirects, with a 0.5-second cold-start delay before the first request.

Only verified terminal evidence may advance the request checkpoint.

An unresolved or ambiguous fault halts execution fail-closed.

## Authorization

Wave B requires a separate explicit human authorization after the
implementation and hostile tests have themselves been frozen.

Canonical future authorization path:

`results/07_comparative_landscape/triage_pre_review_text_retrieval_v1/live_wave_b/authorization.json`

The authorization must remain untracked at execution time and is
one-use.

This design creates no authorization.

## Authority boundary

- No Wave B network authorization exists.
- No Wave B network request is permitted by this freeze.
- No production mutation is permitted.
- Blind-validation content is not used.
- Transport evidence contains no scientific decision fields.

## Design SHA-256

`{design_sha}`
""",
    encoding="utf-8",
)


targets = [
    FREEZE,
    DESIGN,
    DOC,
]

SUMS.write_text(
    "".join(
        f"{sha256_file(path)}  {path}\n"
        for path in targets
    ),
    encoding="utf-8",
)


print(
    "wave_b_execution_design_sha256 =",
    design_sha,
)

print(
    "PASS | Wave B execution contract frozen pre-implementation"
)

print(
    "NO AUTHORITY | no network authorization created"
)
