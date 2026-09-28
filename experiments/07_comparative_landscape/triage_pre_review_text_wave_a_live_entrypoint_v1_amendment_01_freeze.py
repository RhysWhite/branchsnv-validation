from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(
    "experiments/07_comparative_landscape"
)

BASE_DESIGN = (
    ROOT
    / "triage_pre_review_text_wave_a_live_entrypoint_v1_design.json"
)

AMENDMENT = (
    ROOT
    / "triage_pre_review_text_wave_a_live_entrypoint_v1_amendment_01_design.json"
)

DOCUMENT = (
    ROOT
    / "TRIAGE_PRE_REVIEW_TEXT_WAVE_A_LIVE_ENTRYPOINT_V1_AMENDMENT_01.md"
)

EXPECTED_PARENT = (
    "044aa94b22d9dfb4915bfdaeadc43b7397e94af4"
)

EXPECTED_BASE_DESIGN_SHA256 = (
    "84078785db79d2016739e8d4dd003917edf8ba79a5092b96a9f72d4fcd724e77"
)

FROZEN_MOCK_RUNNER = (
    ROOT
    / "triage_pre_review_text_wave_a_mock_runner_v1.py"
)

EXPECTED_MOCK_RUNNER_SHA256 = (
    "21c67dd6791aac29d995ab33828ec6ff444fd4e52d911a10fd20809d30ca5242"
)

FROZEN_ADAPTER_RUNNER_CHECKSUM = (
    ROOT
    / "triage_pre_review_text_wave_a_transport_adapter_runner_v1.sha256"
)


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

assert (
    sha256_file(
        BASE_DESIGN
    )
    == EXPECTED_BASE_DESIGN_SHA256
)

assert (
    sha256_file(
        FROZEN_MOCK_RUNNER
    )
    == EXPECTED_MOCK_RUNNER_SHA256
)

subprocess.run(
    [
        "sha256sum",
        "-c",
        str(
            FROZEN_ADAPTER_RUNNER_CHECKSUM
        ),
    ],
    check=True,
    stdout=subprocess.DEVNULL,
)


base = json.loads(
    BASE_DESIGN.read_text(
        encoding="utf-8"
    )
)

assert (
    base[
        "status"
    ]
    == "FROZEN_PRE_IMPLEMENTATION"
)


amendment = {
    "schema_version":
        1,

    "amendment_id":
        (
            "TRIAGE_PRE_REVIEW_TEXT_WAVE_A_"
            "LIVE_ENTRYPOINT_V1_AMENDMENT_01"
        ),

    "status":
        "FROZEN_PRE_IMPLEMENTATION",

    "parent_commit":
        EXPECTED_PARENT,

    "base_design": {
        "path":
            str(
                BASE_DESIGN
            ),

        "sha256":
            EXPECTED_BASE_DESIGN_SHA256,
    },

    "reason":
        (
            "The base live-entrypoint design proposed refactoring the "
            "already committed mock runner into a thin wrapper over a "
            "shared core. The mock runner is itself pinned by the "
            "previously committed transport-adapter/runner checksum "
            "boundary. Modifying it would invalidate that earlier "
            "frozen implementation boundary. Amendment 01 preserves "
            "the proven mock implementation byte-for-byte and adds "
            "the live shared core without rewriting history."
        ),

    "replaces": {
        "implementation_architecture.mock_wrapper":
            True,

        "implementation_architecture.core_rule":
            True,

        "required_hostile_tests.shared_core_refactor_requirement":
            True,
    },

    "preserved_frozen_mock": {
        "path":
            str(
                FROZEN_MOCK_RUNNER
            ),

        "sha256":
            EXPECTED_MOCK_RUNNER_SHA256,

        "modification_permitted":
            False,

        "existing_hostile_suite_must_remain_passing":
            True,

        "existing_checksum_boundary_must_remain_passing":
            True,
    },

    "revised_implementation_architecture": {
        "new_live_core":
            "triage_pre_review_text_wave_a_runner_core_v1.py",

        "existing_mock_runner":
            "triage_pre_review_text_wave_a_mock_runner_v1.py",

        "live_entrypoint":
            "triage_pre_review_text_wave_a_live_entrypoint_v1.py",

        "existing_mock_runner_role":
            (
                "Frozen proven mock implementation retained "
                "byte-identically as an independent regression oracle."
            ),

        "new_live_core_role":
            (
                "Transport-injected implementation of the same frozen "
                "state/archive/evidence/checkpoint orchestration used "
                "for live execution. It has no default network "
                "executor and creates no authorization."
            ),

        "live_entrypoint_role":
            (
                "Sole wrapper permitted to bind the new live core to "
                "the frozen default_http_executor after all preclaim "
                "authorization checks succeed."
            ),

        "adapter_modification_permitted":
            False,

        "guard_modification_permitted":
            False,

        "exact_transport_modification_permitted":
            False,

        "mock_runner_modification_permitted":
            False,

        "new_independent_http_stack_permitted":
            False,
    },

    "behavioral_equivalence_contract": {
        "source_of_semantics":
            (
                "Frozen mock runner plus base adapter/guard/live "
                "retrieval contracts."
            ),

        "live_core_must_preserve": [
            "manifest sequence selection",
            "state refresh and validation",
            "durable adapter evidence before checkpoint",
            "verified raw archive recovery",
            "partial archive fail-closed behavior",
            "provider identity mismatch fail-closed behavior",
            "noncheckpointing transport fault behavior",
            "no automatic request replay after ambiguous evidence",
            "checkpoint receipt construction",
            "adapter and transport archive verification",
            "credential sanitization inherited from frozen transport",
        ],

        "deliberate_live_difference": {
            "mock":
                (
                    "Frozen mock runner rejects "
                    "default_http_executor."
                ),

            "live":
                (
                    "Only the live entrypoint may inject "
                    "default_http_executor into the new live core "
                    "after authorization preflight."
                ),
        },
    },

    "pacing_contract": {
        "live_core_accepts_prebuilt_paced_executor":
            True,

        "live_entrypoint_constructs_provider_pacer_once":
            True,

        "live_entrypoint_constructs_paced_executor_once":
            True,

        "same_paced_executor_reused_for_entire_process":
            True,

        "cold_start_seconds":
            0.5,

        "provider_maximum_initiation_rate_per_second":
            2.0,

        "redirects_and_retries_share_same_paced_executor":
            True,
    },

    "authorization_path_observation": {
        "canonical_path":
            (
                "results/07_comparative_landscape/"
                "triage_pre_review_text_retrieval_v1/"
                "live_wave_a/authorization.json"
            ),

        "observed_tracked_at_freeze":
            False,

        "observed_gitignored_at_freeze":
            False,

        "gitignore_change_required":
            False,

        "reason":
            (
                "The frozen guard's clean-tree check ignores untracked "
                "files. The live entrypoint separately requires the "
                "authorization itself to remain untracked. Being "
                "gitignored is not part of the authorization contract."
            ),

        "tracked_authorization_must_fail_closed":
            True,
    },

    "revised_required_hostile_tests": [
        (
            "Previously committed mock runner SHA remains exactly "
            "21c67dd6791aac29d995ab33828ec6ff444fd4e52d911a10fd20809d30ca5242."
        ),
        (
            "Previously committed adapter/mock checksum manifest "
            "continues to verify."
        ),
        (
            "Existing 26-test adapter/mock hostile suite remains "
            "passing without modification."
        ),
        (
            "Live core behavior is tested independently against the "
            "same success, recovery and fail-closed cases."
        ),
        (
            "Live core has no default executor and cannot initiate a "
            "request unless an executor is injected."
        ),
        (
            "Live entrypoint is the only new module that references "
            "default_http_executor for execution."
        ),
        (
            "One ProviderPacer and one paced executor are constructed "
            "per live process and reused across manifest requests."
        ),
        (
            "Missing authorization, noncanonical path, tracked "
            "authorization, wrong execution commit, dirty tracked "
            "tree, missing NCBI_EMAIL, NCBI_API_KEY presence, and "
            "wrong confirmation all fail before claim/network."
        ),
        (
            "Synthetic test authorization fixtures may exist only "
            "inside temporary test directories; no production "
            "authorization.json is created by implementation or tests."
        ),
        (
            "All live-entrypoint network tests replace the exact "
            "default_http_executor object with a synthetic executor "
            "before execution."
        ),
        (
            "Same execution ID resume does not duplicate a verified "
            "transport request."
        ),
        (
            "Different execution ID remains rejected by the frozen "
            "guard."
        ),
        (
            "Credential sentinels never appear in claim, state, "
            "checkpoint, adapter evidence or archived metadata."
        ),
        (
            "Wave B is never generated or invoked."
        ),
        (
            "Production boundary remains byte-identical."
        ),
    ],

    "human_gate_after_implementation": {
        "next_gate":
            (
                "COMMIT_FINAL_LIVE_CORE_AND_ENTRYPOINT_THEN_STOP_"
                "FOR_EXPLICIT_HUMAN_WAVE_A_NETWORK_AUTHORIZATION"
            ),

        "real_authorization_creation_permitted_before_that_gate":
            False,

        "real_network_execution_permitted_before_that_gate":
            False,
    },
}


AMENDMENT.write_text(
    json.dumps(
        amendment,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)


doc = """# Wave A live entrypoint v1 — amendment 01

## Status

`FROZEN_PRE_IMPLEMENTATION`

This amendment creates no authorization and performs no network
traffic.

## Why this amendment is required

The base live-entrypoint design proposed moving the existing mock
runner into a shared core.

That mock runner had already been committed and checksum-pinned by the
previous transport-adapter/runner implementation boundary. Altering it
would therefore invalidate an earlier frozen boundary.

The previous implementation remains authoritative and byte-identical.

## Revised architecture

The existing mock runner remains unchanged and continues to serve as a
regression oracle.

A new `triage_pre_review_text_wave_a_runner_core_v1.py` implements the
same state, archive, adapter-evidence and checkpoint orchestration for
the live path, but has no default network executor.

A new live entrypoint is the only new component permitted to inject the
already-frozen `default_http_executor`, and only after all frozen
preclaim checks succeed.

This deliberately accepts a small amount of duplicated orchestration
code in preference to mutating a previously frozen implementation.

## Pacing

The live entrypoint constructs one `ProviderPacer` and one paced
executor for the process. That executor is reused across all manifest
requests, retries and redirects.

## Authorization path

The canonical authorization path is currently untracked and not
gitignored.

No `.gitignore` change is required. The frozen guard deliberately
ignores untracked files when checking tracked-tree cleanliness, while
the live entrypoint separately rejects an authorization if it has
become tracked.

## Human gate

After the live core and live entrypoint have been implemented,
hostile-tested and committed, execution stops again.

No production authorization file and no real network request are
permitted before a separate explicit human authorization.
"""

DOCUMENT.write_text(
    doc,
    encoding="utf-8",
)


print(
    "base design SHA256 =",
    sha256_file(
        BASE_DESIGN
    )
)

print(
    "mock runner SHA256 =",
    sha256_file(
        FROZEN_MOCK_RUNNER
    )
)

print(
    "amendment SHA256 =",
    sha256_file(
        AMENDMENT
    )
)

print(
    "document SHA256 =",
    sha256_file(
        DOCUMENT
    )
)

print(
    "PASS | live-entrypoint amendment 01 frozen"
)

print(
    "NO AUTHORITY | no authorization; no network"
)
