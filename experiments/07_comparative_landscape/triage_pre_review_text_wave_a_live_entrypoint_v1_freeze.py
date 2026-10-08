from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(
    "experiments/07_comparative_landscape"
)

RESULT_ROOT = Path(
    "results/07_comparative_landscape/"
    "triage_pre_review_text_retrieval_v1/"
    "live_wave_a"
)

DESIGN = (
    ROOT
    / "triage_pre_review_text_wave_a_live_entrypoint_v1_design.json"
)

DOCUMENT = (
    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_WAVE_A_LIVE_ENTRYPOINT_V1.md"
)

EXPECTED_PARENT = (
    "e2754127593e25ad361025a301729c96391d44d8"
)

EXPECTED = {
    "live_retrieval_design": {
        "path":
            ROOT
            / "triage_pre_review_text_live_retrieval_v1_design.json",

        "sha256":
            "3dff9e1a41196343adc02951b7a88a2b1306e7df05838f3b2ab50ed53ce16172",
    },

    "authorization_guard": {
        "path":
            ROOT
            / "triage_pre_review_text_wave_a_guard_v1.py",

        "sha256":
            "40dadd678bfe282e196ef007dbb443e4672c578055f1608d737625bae9c5b7af",
    },

    "transport_adapter": {
        "path":
            ROOT
            / "triage_pre_review_text_wave_a_transport_evidence_adapter_v1.py",

        "sha256":
            "30a311626b3e99e6520601585b87df3b600991094d7724cd358b52159d902bac",
    },

    "mock_runner": {
        "path":
            ROOT
            / "triage_pre_review_text_wave_a_mock_runner_v1.py",

        "sha256":
            "21c67dd6791aac29d995ab33828ec6ff444fd4e52d911a10fd20809d30ca5242",
    },

    "adapter_runner_tests": {
        "path":
            ROOT
            / "test_triage_pre_review_text_wave_a_transport_adapter_runner_v1.py",

        "sha256":
            "1996a7c55759d2b26c556c1d45d58a82feb006c82c4d38f60a151558325caaa9",
    },

    "exact_transport": {
        "path":
            ROOT
            / "retrieve_metadata_resolution_queue.py",

        "sha256":
            "9c8c11edbbec86e5cbf857f25c1bf576a0638ba5cdcf69d1fa2a8b8bfc1a994f",
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
        "TRIAGE_PRE_REVIEW_TEXT_WAVE_A_LIVE_ENTRYPOINT_V1",

    "status":
        "FROZEN_PRE_IMPLEMENTATION",

    "parent_commit":
        EXPECTED_PARENT,

    "purpose":
        (
            "Provide the sole live Wave A execution entrypoint while "
            "retaining the frozen authorization guard, exact transport, "
            "transport-evidence adapter, manifest order, checkpoint "
            "semantics and fail-closed recovery behavior."
        ),

    "authority_boundary": {
        "creates_authorization":
            False,

        "creates_network_authority":
            False,

        "authorization_template_generation_permitted":
            False,

        "network_before_successful_human_authorization_validation":
            False,

        "scientific_decisions_permitted":
            False,

        "model_scoring_permitted":
            False,

        "blind_validation_content_use_permitted":
            False,

        "production_ledger_write_permitted":
            False,

        "wave_b_execution_permitted":
            False,
    },

    "authorization_lifecycle": {
        "canonical_authorization_path":
            str(
                RESULT_ROOT
                / "authorization.json"
            ),

        "authorization_must_be_human_created":
            True,

        "authorization_must_be_untracked_at_execution_time":
            True,

        "authorization_must_not_be_committed_before_execution":
            True,

        "reason":
            (
                "The frozen guard requires authorized_execution_commit "
                "to equal the current git HEAD. Committing an "
                "authorization that names the preceding implementation "
                "commit would change HEAD and invalidate the "
                "authorization."
            ),

        "authorized_execution_commit":
            (
                "Must equal the final committed live-entrypoint "
                "implementation HEAD at authorization creation and "
                "throughout execution/resume."
            ),

        "tracked_tree":
            "must remain clean",

        "intervening_tracked_commit_after_authorization":
            "forbidden",

        "authorization_bytes_bound_on_first_claim":
            True,

        "one_use":
            True,

        "same_execution_id_resume":
            True,

        "different_execution_id_resume":
            False,

        "post_execution_version_control":
            (
                "Any later archival or commit of execution artifacts "
                "is a separate post-run preservation step and does not "
                "form part of executable authorization."
            ),
    },

    "implementation_architecture": {
        "new_shared_core":
            (
                "triage_pre_review_text_wave_a_runner_core_v1.py"
            ),

        "mock_wrapper":
            (
                "triage_pre_review_text_wave_a_mock_runner_v1.py"
            ),

        "live_entrypoint":
            (
                "triage_pre_review_text_wave_a_live_entrypoint_v1.py"
            ),

        "adapter_modification_permitted":
            False,

        "transport_modification_permitted":
            False,

        "guard_modification_permitted":
            False,

        "core_rule":
            (
                "Shared core contains state, archive, evidence and "
                "checkpoint orchestration but has no default network "
                "executor and creates no authorization."
            ),

        "mock_rule":
            (
                "Mock wrapper accepts injected executors and must "
                "continue to reject the frozen default HTTP executor."
            ),

        "live_rule":
            (
                "Live entrypoint is the only wrapper permitted to bind "
                "the shared core to "
                "retrieve_metadata_resolution_queue."
                "default_http_executor."
            ),

        "new_independent_http_stack_permitted":
            False,
    },

    "preclaim_preflight_order": [
        (
            "require explicit CLI live-execution confirmation token"
        ),
        (
            "require explicitly supplied non-empty execution ID"
        ),
        (
            "require canonical authorization path"
        ),
        (
            "require authorization file to be untracked"
        ),
        (
            "validate frozen implementation dependencies"
        ),
        (
            "validate authorization non-mutatively with frozen guard"
        ),
        (
            "require NCBI_EMAIL because Wave A contains PubMed requests"
        ),
        (
            "reject NCBI_API_KEY"
        ),
        (
            "validate adapter base design plus amendment"
        ),
        (
            "only then call guard.open_execution and create/restore "
            "the one-use claim/state"
        ),
    ],

    "credential_contract": {
        "NCBI_EMAIL":
            "required at live start",

        "NCBI_API_KEY":
            "forbidden",

        "OPENALEX_API_KEY":
            "optional",

        "credentials_in_claim_state_checkpoint_or_adapter_evidence":
            False,

        "credentials_in_raw_archived_metadata":
            False,
    },

    "execution_contract": {
        "wave_id":
            "A",

        "manifest_order":
            "strictly ascending frozen request_sequence",

        "concurrency":
            1,

        "provider_maximum_initiation_rate_per_second":
            2.0,

        "provider_cold_start_seconds":
            0.5,

        "pacer_instances_per_process":
            1,

        "paced_executor_instances_per_process":
            1,

        "underlying_live_executor":
            (
                "retrieve_metadata_resolution_queue."
                "default_http_executor"
            ),

        "retry_sleeper":
            "time.sleep",

        "checkpoint_after_each_verified_terminal_lookup":
            True,

        "automatic_reissue_after_ambiguous_partial_archive":
            False,

        "automatic_reissue_after_noncheckpointing_fault":
            False,

        "continue_after_noncheckpointing_fault":
            False,

        "fallback_to_wave_b":
            False,

        "completion":
            (
                "Continue sequentially until guard state is COMPLETED "
                "or halt immediately on the first fault/exception."
            ),
    },

    "operator_interface": {
        "authorization_path_configurable":
            False,

        "execution_id_required":
            True,

        "explicit_confirmation_required":
            True,

        "explicit_confirmation_literal":
            "EXECUTE-AUTHORIZED-WAVE-A",

        "authorization_creation_command_provided":
            False,

        "automatic_execution_id_generation":
            False,

        "automatic_fault_cleanup":
            False,

        "automatic_claim_or_evidence_deletion":
            False,
    },

    "required_hostile_tests": [
        (
            "Missing authorization causes zero executor calls and "
            "creates no claim/state."
        ),
        (
            "Noncanonical authorization path is rejected before claim."
        ),
        (
            "Tracked authorization artifact is rejected before claim."
        ),
        (
            "Authorization bound to wrong git HEAD is rejected before "
            "any executor call."
        ),
        (
            "Dirty tracked tree is rejected before any executor call."
        ),
        (
            "Missing NCBI_EMAIL is rejected before claim."
        ),
        (
            "Presence of NCBI_API_KEY is rejected before claim."
        ),
        (
            "Missing or wrong explicit live confirmation is rejected "
            "before claim."
        ),
        (
            "Live entrypoint binds only the frozen default HTTP "
            "executor; tests monkeypatch that exact object with a "
            "synthetic executor so no real network occurs."
        ),
        (
            "One shared ProviderPacer and one paced executor are used "
            "throughout a process."
        ),
        (
            "Same execution ID resumes without duplicate transport."
        ),
        (
            "Different execution ID is rejected."
        ),
        (
            "Partial raw archive and noncheckpointing fault remain "
            "fail-closed with zero automatic reissue."
        ),
        (
            "Credential sentinel values are absent from every generated "
            "claim, state, checkpoint, adapter-evidence and archived "
            "request/response metadata file."
        ),
        (
            "Wave B files/routes are never generated or invoked."
        ),
        (
            "Existing adapter/mock hostile suite and guard hostile "
            "suite remain passing after shared-core refactor."
        ),
        (
            "No test performs a real network request."
        ),
        (
            "Production boundary remains byte-identical."
        ),
    ],

    "human_gate_after_implementation": {
        "next_gate":
            (
                "COMMIT_FINAL_LIVE_ENTRYPOINT_THEN_STOP_FOR_EXPLICIT_"
                "HUMAN_WAVE_A_NETWORK_AUTHORIZATION"
            ),

        "authorization_may_be_created_by_implementation_or_tests":
            False,

        "network_may_be_started_automatically_after_commit":
            False,
    },

    "frozen_inputs": {
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


doc = """# Wave A live entrypoint v1

## Status

`FROZEN_PRE_IMPLEMENTATION`

This freeze creates no authorization and performs no network traffic.

## Authorization lifecycle

The frozen guard requires `authorized_execution_commit` to equal the
current Git HEAD and requires the tracked tree to be clean.

Therefore the executable authorization is not committed before the
run. The sequence is:

1. commit the final live-entrypoint implementation;
2. stop;
3. obtain explicit human authorization;
4. create the canonical untracked `authorization.json` whose
   `authorized_execution_commit` is exactly that final HEAD;
5. execute or resume under the same HEAD and same execution ID.

Any tracked commit between steps 4 and 5 invalidates the authorization.

The first claim durably binds the exact authorization bytes and
execution ID. The authorization remains one-use.

## Architecture

The existing adapter, authorization guard and exact transport remain
unchanged.

The current mocked runner is refactored so transport-independent
execution logic lives in a shared core. The mock wrapper continues to
reject the real HTTP executor.

A separate live entrypoint is the only component permitted to bind the
shared core to the already-frozen `default_http_executor`. No second
HTTP stack may be introduced.

## Pre-claim safety

All non-mutating checks occur before `guard.open_execution`:

- explicit live confirmation;
- explicit execution ID;
- canonical untracked authorization path;
- frozen implementation verification;
- authorization validation;
- NCBI contact-policy validation;
- adapter-contract validation.

Only after all of those pass may the one-use claim/state be created or
resumed.

## Execution

Wave A remains serial and manifest-ordered. One provider pacer and one
paced executor are retained for the process. Every request initiation,
including retries and redirects, remains subject to the provider pacing
contract.

Verified terminal evidence is durable before checkpoint advancement.

Ambiguous partial archives, identity failures, authentication failures,
redirect failures, integrity failures and retry exhaustion halt the run.
They are not automatically replayed.

There is no Wave B fallback.

## Human gate

After the live entrypoint is implemented, hostile-tested and committed,
execution stops again.

Creation of the real authorization file and initiation of network
traffic require a separate explicit human authorization.
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
    "PASS | live-entrypoint design frozen pre-implementation"
)

print(
    "NO AUTHORITY | no authorization created; no network"
)
