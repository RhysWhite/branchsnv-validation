from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import unittest


import pre_review_triage_future_text_wave_a_guard_v1 as guard
import pre_review_triage_future_text_wave_a_runner_core_v1 as core

import test_pre_review_triage_future_text_wave_a_guard_v1 as guard_tests

import test_triage_pre_review_text_wave_a_transport_adapter_runner_v1 as development_tests

import triage_pre_review_text_wave_a_mock_runner_v1 as frozen_mock


ROOT = Path(
    "experiments/07_comparative_landscape"
)

DEV_CORE = (
    ROOT
    / "triage_pre_review_text_wave_a_runner_core_v1.py"
)

FUTURE_CORE = (
    ROOT
    / "pre_review_triage_future_text_wave_a_runner_core_v1.py"
)


EXPECTED_FUTURE_CORE_SHA256 = (
    "c4775bfcef700ee7df35c32dafbeb97f5"
    "46ff6c14b935f675ae2f745ba8144cd"
)

EXPECTED_GUARD_SHA256 = (
    "79300875f7620afde503f70b27a78449"
    "d11fcda35c23b11dc44d2fe538bcb28c"
)

EXPECTED_MANIFEST_SHA256 = (
    "9c5a1b7cda465f0f4a88fc06c612c979"
    "af3093f0cecabbe4d8b42576cac30e73"
)

EXPECTED_REQUEST_COUNT = 12147


SELECTED_BEHAVIOR_TESTS = [
    "test_mock_runner_checkpoints_first_manifest_request",
    "test_transport_failure_never_checkpoints",
    "test_partial_raw_archive_halts_without_executor",
    "test_durable_evidence_precedes_guard_checkpoint",
    "test_raw_archive_tamper_blocks_evidence_recovery",
    "test_no_default_http_executor_path",
    "test_pubmed_live_preflight_requires_email",
    "test_pubmed_mismatch_remains_rejected",
    "test_not_found_archive_tamper_rejected",
    "test_redirect_metadata_tamper_after_durable_evidence_rejected",
    "test_identity_mismatch_runner_never_checkpoints",
    "test_crash_after_durable_evidence_recovers_without_transport",
    "test_second_run_advances_without_duplicate",
]


def sha256_file(
    path: Path,
) -> str:

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


class FutureCoreRunnerShim:
    """Test-only pacing adapter around the transport-injected core.

    The frozen mock runner owns the already-tested ProviderPacer wrapper.
    The future core itself remains unchanged and receives only the
    resulting injected executor.
    """

    # Existing development behavioral tests temporarily patch
    # runner.guard.checkpoint_terminal in several hostile/recovery cases.
    # Bind them to the exact guard object imported by the future core.
    guard = core.guard

    RunnerError = core.RunnerError
    RunnerHalt = core.RunnerHalt

    preflight_environment = staticmethod(
        core.preflight_environment
    )

    raw_lookup_has_evidence = staticmethod(
        core.raw_lookup_has_evidence
    )

    refreshed_state = staticmethod(
        core.refreshed_state
    )

    checkpoint_from_durable_evidence = staticmethod(
        core.checkpoint_from_durable_evidence
    )

    re_hex64 = staticmethod(
        core.re_hex64
    )

    reconstruct_and_checkpoint = staticmethod(
        core.reconstruct_and_checkpoint
    )


    @staticmethod
    def make_paced_executor(
        *,
        executor,
        pacer,
    ):

        return frozen_mock.make_paced_executor(
            executor=executor,
            pacer=pacer,
        )


    @staticmethod
    def run_one(
        *,
        context,
        executor,
        pacer,
        retry_sleeper,
        environ,
    ):

        paced_executor = (
            frozen_mock.make_paced_executor(
                executor=executor,
                pacer=pacer,
            )
        )

        return core.run_one(
            context=context,
            executor=paced_executor,
            retry_sleeper=retry_sleeper,
            environ=environ,
        )


def _find_test_case(
    module,
    required_method: str,
):

    matches = []

    for value in vars(
        module
    ).values():

        if (
            inspect.isclass(
                value
            )
            and issubclass(
                value,
                unittest.TestCase,
            )
            and hasattr(
                value,
                required_method,
            )
        ):

            matches.append(
                value
            )

    if len(
        matches
    ) != 1:
        raise RuntimeError(
            "expected one TestCase containing "
            + required_method
            + "; found "
            + str(
                len(
                    matches
                )
            )
        )

    return matches[
        0
    ]


GUARD_TEST_CASE = _find_test_case(
    guard_tests,
    "valid_authorization",
)


def future_make_authorization(
    self,
    *args,
    **kwargs,
):
    """Construct Amendment-001 authorization in the test temp root."""

    root = kwargs.get(
        "root"
    )

    if root is None:

        positional = list(
            args
        )

        if len(
            positional
        ) != 1:
            raise RuntimeError(
                "unexpected development make_authorization "
                "call signature"
            )

        root = positional[
            0
        ]

    root = Path(
        root
    )


    authorization_path = (
        root
        / "authorization.json"
    )

    execution_root = (
        root
        / "live_wave_a"
    )


    design = (
        guard.load_frozen_design()
    )


    authorization = {
        "schema_version":
            1,

        "authorization_type":
            guard.AUTHORIZATION_TYPE,

        "authorization_id":
            "SYNTHETIC-FUTURE-WAVE-A-AUTH",

        "status":
            "AUTHORIZED",

        "wave_id":
            guard.EXPECTED_WAVE_ID,

        "authorization_statement":
            guard.AUTHORIZATION_STATEMENT,

        "authorization_created_at_utc":
            "2026-09-30T00:00:00Z",

        "amendment_design_sha256":
            guard.EXPECTED_DESIGN_SHA256,

        "base_design_sha256":
            guard.EXPECTED_BASE_DESIGN_SHA256,

        "amended_wave_a_request_manifest_sha256":
            guard.EXPECTED_MANIFEST_SHA256,

        "design_parent_commit":
            guard.EXPECTED_DESIGN_PARENT_COMMIT,

        "authorized_execution_commit":
            guard.git_head(),

        "normalizer_sha256":
            guard.EXPECTED_NORMALIZER_SHA256,

        "transport_source_hashes":
            design[
                "transport_contract"
            ][
                "transport_sources"
            ],

        "maximum_request_count":
            guard.EXPECTED_MAXIMUM_REQUEST_COUNT,

        "execution_output_root":
            str(
                execution_root
            ),

        "one_use":
            True,

        "authorized_by":
            "human",
    }


    if (
        authorization[
            "execution_output_root"
        ]
        == guard.FROZEN_OUTPUT_ROOT
    ):
        raise RuntimeError(
            "focused test authorization attempted "
            "to use frozen production output root"
        )


    required = {
        "amendment_design_sha256",
        "base_design_sha256",
        "amended_wave_a_request_manifest_sha256",
        "design_parent_commit",
        "authorized_execution_commit",
        "normalizer_sha256",
        "transport_source_hashes",
        "maximum_request_count",
        "execution_output_root",
    }

    missing = (
        required
        - set(
            authorization
        )
    )

    if missing:
        raise RuntimeError(
            "future authorization fixture missing: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )


    if (
        authorization[
            "maximum_request_count"
        ]
        != EXPECTED_REQUEST_COUNT
    ):
        raise RuntimeError(
            "future authorization fixture has wrong request ceiling"
        )


    if (
        authorization[
            "amended_wave_a_request_manifest_sha256"
        ]
        != EXPECTED_MANIFEST_SHA256
    ):
        raise RuntimeError(
            "future authorization fixture has wrong manifest SHA"
        )


    authorization_path.write_text(
        json.dumps(
            authorization,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


    return (
        authorization_path,
        authorization,
    )


class FutureCoreStaticTests(
    unittest.TestCase
):

    def test_future_core_hash_and_guard_binding(
        self,
    ):

        self.assertEqual(
            sha256_file(
                FUTURE_CORE
            ),
            EXPECTED_FUTURE_CORE_SHA256,
        )

        self.assertEqual(
            sha256_file(
                Path(
                    guard.__file__
                )
            ),
            EXPECTED_GUARD_SHA256,
        )

        self.assertIs(
            core.guard,
            guard,
        )


    def test_future_core_is_semantic_copy_except_guard_module(
        self,
    ):

        development = (
            DEV_CORE.read_text(
                encoding="utf-8"
            )
        )

        future = (
            FUTURE_CORE.read_text(
                encoding="utf-8"
            )
        )

        normalized_development = (
            development.replace(
                "triage_pre_review_text_wave_a_guard_v1",
                "__WAVE_A_GUARD__",
            )
        )

        normalized_future = (
            future.replace(
                "pre_review_triage_future_text_wave_a_guard_v1",
                "__WAVE_A_GUARD__",
            )
        )

        self.assertEqual(
            normalized_development,
            normalized_future,
        )


    def test_future_core_has_no_default_executor(
        self,
    ):

        source = FUTURE_CORE.read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "default_http_executor",
            source,
        )

        signature = inspect.signature(
            core.run_one
        )

        self.assertIn(
            "executor",
            signature.parameters,
        )

        self.assertIs(
            signature.parameters[
                "executor"
            ].default,
            inspect.Parameter.empty,
        )

        self.assertNotIn(
            "pacer",
            signature.parameters,
        )


    def test_corrected_guard_manifest_bound_to_core(
        self,
    ):

        self.assertEqual(
            guard.EXPECTED_MAXIMUM_REQUEST_COUNT,
            EXPECTED_REQUEST_COUNT,
        )

        self.assertEqual(
            guard.EXPECTED_MANIFEST_SHA256,
            EXPECTED_MANIFEST_SHA256,
        )

        manifest = (
            guard.read_manifest()
        )

        self.assertEqual(
            len(
                manifest
            ),
            EXPECTED_REQUEST_COUNT,
        )

        design = (
            guard.load_frozen_design()
        )

        self.assertEqual(
            design[
                "_amendment"
            ][
                "offline_partition"
            ][
                "terminal_without_network"
            ],
            15,
        )


# Keep a hard fail-closed barrier around the exact transport default
# for this entire focused suite. Every selected behavior test supplies
# a synthetic executor.
_ORIGINAL_DEFAULT_HTTP_EXECUTOR = (
    development_tests.transport.default_http_executor
)


def _forbidden_default_http_executor(
    *args,
    **kwargs,
):

    raise AssertionError(
        "REAL/DEFAULT HTTP EXECUTOR IS FORBIDDEN "
        "IN FUTURE CORE TESTS"
    )


def setUpModule():

    development_tests.transport.default_http_executor = (
        _forbidden_default_http_executor
    )


def tearDownModule():

    development_tests.transport.default_http_executor = (
        _ORIGINAL_DEFAULT_HTTP_EXECUTOR
    )


def load_tests(
    loader,
    standard_tests,
    pattern,
):

    # Rebind the existing independently proven test fixture to the
    # corrected future guard and the unchanged future execution core.
    development_tests.guard = (
        guard
    )

    development_tests.runner = (
        FutureCoreRunnerShim
    )


    oracle_class = _find_test_case(
        development_tests,
        SELECTED_BEHAVIOR_TESTS[
            0
        ],
    )


    for name in SELECTED_BEHAVIOR_TESTS:

        if not hasattr(
            oracle_class,
            name,
        ):
            raise RuntimeError(
                "development runner oracle lost test: "
                + name
            )


    # Its historical helper creates the development authorization
    # vocabulary. Replace only that fixture constructor with the
    # already-passing Amendment-001 constructor.
    oracle_class.make_authorization = (
        future_make_authorization
    )


    suite = unittest.TestSuite()

    suite.addTests(
        loader.loadTestsFromTestCase(
            FutureCoreStaticTests
        )
    )


    for name in SELECTED_BEHAVIOR_TESTS:

        suite.addTest(
            oracle_class(
                name
            )
        )


    return suite


if __name__ == "__main__":
    unittest.main()
