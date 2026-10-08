from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(
    "experiments/07_comparative_landscape"
)

RESULT_ROOT = Path(
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1"
)

IMPLEMENTATION_PARENT_COMMIT = (
    "c42e80f3a25fe8abe37f65f46582ce0f49b168a1"
)

EXECUTION_DESIGN_SHA256 = (
    "4a607178762e9e884f430b8fe1c47d078"
    "408b5a51e4e47701f2f4302ab5ca2ca"
)

REQUEST_MANIFEST_SHA256 = (
    "f099f86cce2321ab07d639aeef5570145"
    "85faf49e2306a09f3fe40119535f0a6"
)

DERIVATION_SHA256 = (
    "a58356439478ca27a48c3967dbbab6a16"
    "b275987dc4af7b19f67dd430eeab32b"
)

NORMALIZER_SHA256 = (
    "cbe66fc9ab406fa5ee3745e099c16250"
    "c404a949c0f301e40a7397c285dc459d"
)

IMPLEMENTATION_FILES = {
    (
        ROOT
        / "triage_pre_review_text_wave_b_guard_v1.py"
    ):
        (
            "dfbd56b90ae47068f880328e21f3c3cc"
            "52aa86ef7c80db9c5f069342bc025cb3"
        ),

    (
        ROOT
        / "triage_pre_review_text_wave_b_transport_evidence_adapter_v1.py"
    ):
        (
            "d6d04019521f1bec3d1d9b27014fb571"
            "8a774488d93b8a48852a483b51664a79"
        ),

    (
        ROOT
        / "triage_pre_review_text_wave_b_runner_core_v1.py"
    ):
        (
            "3bdbf2d827eadc2c5d7d25593cba9231"
            "da65336722f70e01e59aeba3248f1b3f"
        ),

    (
        ROOT
        / "triage_pre_review_text_wave_b_live_entrypoint_v1.py"
    ):
        (
            "beb0bf427a0c4f935d9c58655aa80c0c"
            "bb859705b373fd901827c451b580c2e7"
        ),
}

TEST_FILES = {
    (
        ROOT
        / "test_triage_pre_review_text_wave_b_execution_v1.py"
    ):
        (
            "48619aa35b016efe9d15926608a7c49e4"
            "82b158b69cf07083faea8d7e13f8332"
        ),

    (
        ROOT
        / "test_triage_pre_review_text_wave_b_live_hostile_v1.py"
    ):
        (
            "0cb3ba9bdcb5f7efd10d16cdc69bc6cf"
            "59e53445191ce09e3d19940c5b408663"
        ),
}

WAVE_A_AND_TRANSPORT_FILES = {
    (
        ROOT
        / "triage_pre_review_text_wave_a_guard_v1.py"
    ):
        (
            "40dadd678bfe282e196ef007dbb443e467"
            "2c578055f1608d737625bae9c5b7af"
        ),

    (
        ROOT
        / "triage_pre_review_text_wave_a_transport_evidence_adapter_v1.py"
    ):
        (
            "30a311626b3e99e6520601585b87df3b6"
            "00991094d7724cd358b52159d902bac"
        ),

    (
        ROOT
        / "triage_pre_review_text_wave_a_runner_core_v1.py"
    ):
        (
            "d1b4a3cff4a99e91d5ea35446e204426"
            "bd4794e3c81b769d386c22d5c5e529ad"
        ),

    (
        ROOT
        / "triage_pre_review_text_wave_a_live_entrypoint_v1.py"
    ):
        (
            "f27d23cc311d7959ced8db865026dcaa8"
            "162af6d4b6ac1b2a579b1b715e7239a"
        ),

    (
        ROOT
        / "retrieve_metadata_resolution_queue.py"
    ):
        (
            "9c8c11edbbec86e5cbf857f25c1bf576"
            "a0638ba5cdcf69d1fa2a8b8bfc1a994f"
        ),

    (
        ROOT
        / "t000002_authoritative_source_network_transport.py"
    ):
        (
            "cc68579ff66af7633b7dd79520f748cfb"
            "e09cf8f95eaaf5cc927b833c4a7d962"
        ),
}

EXECUTION_DESIGN = (
    ROOT
    / "triage_pre_review_text_wave_b_execution_v1_design.json"
)

REQUEST_MANIFEST = (
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

DESIGN = (
    ROOT
    / "triage_pre_review_text_wave_b_implementation_v1_design.json"
)

DOC = (
    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_WAVE_B_IMPLEMENTATION_V1.md"
)

CHECKSUM = (
    ROOT
    / "triage_pre_review_text_wave_b_implementation_v1.sha256"
)

FREEZE = (
    ROOT
    / "triage_pre_review_text_wave_b_implementation_v1_freeze.py"
)

LIVE_ROOT = (
    RESULT_ROOT
    / "live_wave_b"
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


def git_head() -> str:

    return subprocess.check_output(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()


def tracked_tree_clean() -> bool:

    result = subprocess.check_output(
        [
            "git",
            "status",
            "--porcelain",
            "--untracked-files=no",
        ],
        text=True,
    )

    return not result.strip()


def verify_hash(
    path: Path,
    expected: str,
) -> None:

    if not path.is_file():
        raise RuntimeError(
            "Required file missing: "
            + str(
                path
            )
        )

    observed = sha256_file(
        path
    )

    if observed != expected:
        raise RuntimeError(
            "SHA256 mismatch: "
            + str(
                path
            )
            + "\nexpected="
            + expected
            + "\nobserved="
            + observed
        )



def verify_preconditions() -> None:

    current_head = git_head()

    expected_freeze_commit_paths = {
        str(
            ROOT
            / "triage_pre_review_text_wave_b_guard_v1.py"
        ),
        str(
            ROOT
            / "triage_pre_review_text_wave_b_transport_evidence_adapter_v1.py"
        ),
        str(
            ROOT
            / "triage_pre_review_text_wave_b_runner_core_v1.py"
        ),
        str(
            ROOT
            / "triage_pre_review_text_wave_b_live_entrypoint_v1.py"
        ),
        str(
            ROOT
            / "test_triage_pre_review_text_wave_b_execution_v1.py"
        ),
        str(
            ROOT
            / "test_triage_pre_review_text_wave_b_live_hostile_v1.py"
        ),
        str(
            FREEZE
        ),
        str(
            DESIGN
        ),
        str(
            DOC
        ),
        str(
            CHECKSUM
        ),
    }

    if (
        current_head
        == IMPLEMENTATION_PARENT_COMMIT
    ):

        repository_position = (
            "PRE_COMMIT_PARENT"
        )

    else:

        parent = subprocess.check_output(
            [
                "git",
                "rev-parse",
                "HEAD^",
            ],
            text=True,
        ).strip()

        if (
            parent
            != IMPLEMENTATION_PARENT_COMMIT
        ):
            raise RuntimeError(
                "Current HEAD is neither the implementation "
                "parent nor its direct freeze commit"
            )

        changed = {
            item
            for item in subprocess.check_output(
                [
                    "git",
                    "diff-tree",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "HEAD",
                ],
                text=True,
            ).splitlines()
            if item.strip()
        }

        if (
            changed
            != expected_freeze_commit_paths
        ):
            raise RuntimeError(
                "Freeze commit path set mismatch\n"
                "expected="
                + repr(
                    sorted(
                        expected_freeze_commit_paths
                    )
                )
                + "\nobserved="
                + repr(
                    sorted(
                        changed
                    )
                )
            )

        repository_position = (
            "COMMITTED_FREEZE"
        )

    if not tracked_tree_clean():
        raise RuntimeError(
            "Tracked tree is not clean"
        )

    verify_hash(
        EXECUTION_DESIGN,
        EXECUTION_DESIGN_SHA256,
    )

    verify_hash(
        REQUEST_MANIFEST,
        REQUEST_MANIFEST_SHA256,
    )

    verify_hash(
        DERIVATION,
        DERIVATION_SHA256,
    )

    verify_hash(
        NORMALIZER,
        NORMALIZER_SHA256,
    )

    for path, expected in (
        IMPLEMENTATION_FILES.items()
    ):
        verify_hash(
            path,
            expected,
        )

    for path, expected in (
        TEST_FILES.items()
    ):
        verify_hash(
            path,
            expected,
        )

    for path, expected in (
        WAVE_A_AND_TRANSPORT_FILES.items()
    ):
        verify_hash(
            path,
            expected,
        )

    forbidden_runtime_artifacts = [
        LIVE_ROOT
        / "authorization.json",

        LIVE_ROOT
        / "authorization_claim.json",

        LIVE_ROOT
        / "execution_state.json",

        LIVE_ROOT
        / "completion_receipt.json",
    ]

    for path in forbidden_runtime_artifacts:

        if path.exists():
            raise RuntimeError(
                "Wave B authority/runtime artifact exists: "
                + str(path)
            )

    print(
        "PASS | repository position =",
        repository_position,
    )



def run_tests() -> None:

    env = {
        **dict(
            __import__(
                "os"
            ).environ
        ),
        "PYTHONDONTWRITEBYTECODE":
            "1",
        "PYTHONPATH":
            str(
                ROOT
            ),
    }

    suites = [
        (
            "Wave B focused",
            "test_triage_pre_review_text_wave_b_execution_v1",
            17,
        ),
        (
            "Wave B live hostile",
            "test_triage_pre_review_text_wave_b_live_hostile_v1",
            20,
        ),
        (
            "Wave A guard regression",
            "test_triage_pre_review_text_wave_a_guard_v1",
            13,
        ),
        (
            "Wave A adapter/runner regression",
            "test_triage_pre_review_text_wave_a_transport_adapter_runner_v1",
            26,
        ),
        (
            "Wave A live regression",
            "test_triage_pre_review_text_wave_a_live_entrypoint_v1",
            24,
        ),
    ]

    for label, module, expected_count in suites:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "-v",
                module,
            ],
            env=env,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                label
                + " suite failed"
            )

        print(
            "PASS |",
            label,
            "| expected tests =",
            expected_count,
        )


def design_object() -> dict:

    return {
        "schema_version":
            1,

        "freeze_id":
            "TRIAGE_PRE_REVIEW_TEXT_WAVE_B_IMPLEMENTATION_V1",

        "status":
            "FROZEN_PRE_AUTHORIZATION",

        "wave_id":
            "TRIAGE_TEXT_LIVE_WAVE_B",

        "implementation_parent_commit":
            IMPLEMENTATION_PARENT_COMMIT,

        "freeze_commit_binding":
            (
                "The immutable implementation freeze is the git "
                "commit containing this exact artifact together "
                "with the exact source and test hashes recorded here."
            ),

        "frozen_upstream": {
            "execution_design_sha256":
                EXECUTION_DESIGN_SHA256,

            "request_manifest_sha256":
                REQUEST_MANIFEST_SHA256,

            "derivation_sha256":
                DERIVATION_SHA256,

            "normalizer_sha256":
                NORMALIZER_SHA256,
        },

        "implementation_source_sha256": {
            str(
                path
            ):
                expected
            for path, expected
            in IMPLEMENTATION_FILES.items()
        },

        "test_source_sha256": {
            str(
                path
            ):
                expected
            for path, expected
            in TEST_FILES.items()
        },

        "test_contract": {
            "wave_b_focused_tests":
                17,

            "wave_b_live_hostile_tests":
                20,

            "wave_b_total_tests":
                37,

            "wave_a_guard_regression_tests":
                13,

            "wave_a_adapter_runner_regression_tests":
                26,

            "wave_a_live_regression_tests":
                24,

            "wave_a_total_regression_tests":
                63,

            "required_result":
                "all tests pass",
        },

        "execution_contract": {
            "provider":
                "openalex",

            "maximum_request_count":
                25,

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
            ],

            "pubmed_permitted":
                False,

            "search_or_list_endpoints_permitted":
                False,

            "crossref_permitted":
                False,

            "ad_hoc_probe_permitted":
                False,

            "same_execution_id_resume_only":
                True,

            "automatic_reissue_after_ambiguous_network_intent":
                False,

            "runtime_invariants_rechecked_between_requests":
                True,

            "cross_process_execution_lock_required":
                True,

            "credential_values_must_not_be_archived":
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
        },

        "preservation_contract": {
            "wave_a_sources_byte_identical":
                True,

            "low_level_transport_byte_identical":
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
                "Commit exactly the frozen implementation, tests, "
                "and freeze artifacts; record the resulting exact HEAD; "
                "only then may a separate explicit human Wave B "
                "authorization be considered."
            ),
    }


def document_text(
    design_sha256: str,
) -> str:

    return f"""# Wave B implementation freeze v1

Status: **FROZEN_PRE_AUTHORIZATION**

This freeze records the exact offline-tested implementation for
`TRIAGE_TEXT_LIVE_WAVE_B`.

It creates **no authorization** and grants **no network execution authority**.

## Frozen upstream

- Execution design SHA256: `{EXECUTION_DESIGN_SHA256}`
- Request manifest SHA256: `{REQUEST_MANIFEST_SHA256}`
- Derivation SHA256: `{DERIVATION_SHA256}`
- Normalizer SHA256: `{NORMALIZER_SHA256}`
- Implementation design SHA256: `{design_sha256}`

## Frozen execution scope

Wave B contains exactly 25 OpenAlex requests in frozen manifest order:

- 21 exact OpenAlex Work-ID requests
- 4 exact DOI requests

No PubMed request, search/list endpoint, Crossref lookup, or ad hoc probe is
permitted.

Execution remains serial with concurrency 1, a maximum of two OpenAlex
requests per second, and a 0.5-second cold start before the first OpenAlex
request.

## Recovery and evidence boundary

The implementation retains the fail-closed recovery contract:

- request intent is durably evidenced before network execution;
- verified terminal evidence is required before checkpointing;
- ambiguous or partial network intent is not automatically reissued;
- only the same execution ID may resume;
- runtime authorization and repository invariants are rechecked;
- a cross-process lock prevents concurrent use of the same authorization;
- credential values must not appear in durable evidence.

## Test freeze

The frozen Wave B implementation passed:

- 17 focused/static tests;
- 20 live-hostile tests;
- 37 Wave B tests total.

The unchanged Wave A stack also passed its 63 regression tests:

- 13 guard tests;
- 26 adapter/runner tests;
- 24 live-entrypoint hostile tests.

## Preservation boundary

Wave A implementation files and the low-level transport remain byte-identical
to their previously frozen hashes. Production mutation is not permitted.
Blind validation content has not been scientifically inspected or used.

## Authorization boundary

This freeze does not create an authorization file, claim, state, completion
receipt, or network authority.

A later Wave B authorization, if explicitly approved by a human, must bind the
exact git HEAD containing this freeze and must remain untracked at execution.

The next gate is therefore:

**commit the exact frozen implementation/test/freeze set, record the resulting
HEAD, and stop before authorization.**
"""


def write_outputs() -> None:

    design = design_object()

    design_bytes = (
        json.dumps(
            design,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    ).encode(
        "utf-8"
    )

    DESIGN.write_bytes(
        design_bytes
    )

    design_sha = sha256_bytes(
        design_bytes
    )

    DOC.write_text(
        document_text(
            design_sha
        ),
        encoding="utf-8",
    )

    checksum_lines = []

    for path in (
        FREEZE,
        DESIGN,
        DOC,
    ):

        checksum_lines.append(
            sha256_file(
                path
            )
            + "  "
            + str(
                path
            )
        )

    CHECKSUM.write_text(
        "\n".join(
            checksum_lines
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "implementation_design_sha256 =",
        design_sha,
    )

    print(
        "PASS | Wave B implementation freeze artifacts written"
    )


def validate_outputs() -> None:

    verify_preconditions()

    if not DESIGN.is_file():
        raise RuntimeError(
            "Implementation design missing"
        )

    if not DOC.is_file():
        raise RuntimeError(
            "Implementation freeze document missing"
        )

    if not CHECKSUM.is_file():
        raise RuntimeError(
            "Implementation checksum file missing"
        )

    design = json.loads(
        DESIGN.read_text(
            encoding="utf-8"
        )
    )

    if (
        design.get(
            "status"
        )
        != "FROZEN_PRE_AUTHORIZATION"
    ):
        raise RuntimeError(
            "Implementation freeze status changed"
        )

    if (
        design.get(
            "wave_id"
        )
        != "TRIAGE_TEXT_LIVE_WAVE_B"
    ):
        raise RuntimeError(
            "Wave identity changed"
        )

    if (
        design[
            "authorization_gate"
        ][
            "authorization_created_by_this_freeze"
        ]
        is not False
    ):
        raise RuntimeError(
            "Freeze unexpectedly creates authorization"
        )

    if (
        design[
            "authorization_gate"
        ][
            "network_authorized_by_this_freeze"
        ]
        is not False
    ):
        raise RuntimeError(
            "Freeze unexpectedly grants network authority"
        )

    expected_checksum_lines = []

    for path in (
        FREEZE,
        DESIGN,
        DOC,
    ):

        expected_checksum_lines.append(
            sha256_file(
                path
            )
            + "  "
            + str(
                path
            )
        )

    observed = CHECKSUM.read_text(
        encoding="utf-8"
    )

    expected = (
        "\n".join(
            expected_checksum_lines
        )
        + "\n"
    )

    if observed != expected:
        raise RuntimeError(
            "Implementation checksum manifest mismatch"
        )

    print(
        "PASS | Wave B implementation freeze validates"
    )


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--write",
        action="store_true",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
    )

    parser.add_argument(
        "--run-tests",
        action="store_true",
    )

    args = parser.parse_args()

    if (
        args.write
        == args.validate
    ):
        raise SystemExit(
            "Choose exactly one of --write or --validate"
        )

    verify_preconditions()

    if args.run_tests:
        run_tests()

    if args.write:
        write_outputs()
        validate_outputs()

    else:
        validate_outputs()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
