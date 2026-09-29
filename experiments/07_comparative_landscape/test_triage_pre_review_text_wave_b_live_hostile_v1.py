from __future__ import annotations

from contextlib import contextmanager
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import retrieve_metadata_resolution_queue as transport
import triage_pre_review_text_wave_b_guard_v1 as guard
import triage_pre_review_text_wave_b_live_entrypoint_v1 as live
import triage_pre_review_text_wave_b_runner_core_v1 as core
import triage_pre_review_text_wave_b_transport_evidence_adapter_v1 as adapter


class FakeClock:

    def __init__(
        self,
    ):

        self.value = 0.0
        self.sleeps = []


    def monotonic(
        self,
    ):

        return self.value


    def sleep(
        self,
        seconds,
    ):

        seconds = float(
            seconds
        )

        self.sleeps.append(
            seconds
        )

        self.value += seconds


class FakePacer:

    def __init__(
        self,
    ):

        self.sleeps = []
        self.waits = []

    def sleeper(
        self,
        seconds,
    ):

        self.sleeps.append(
            float(
                seconds
            )
        )

    def wait(
        self,
        provider,
    ):

        self.waits.append(
            provider
        )


class WaveBLiveEntrypointTests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(
        cls,
    ):

        cls.manifest = (
            guard.read_manifest()
        )

        cls.live_design = (
            guard.load_frozen_design()
        )


    def setUp(
        self,
    ):

        # Any accidental use of the real default executor in tests fails
        # immediately.  The one explicit live-binding test temporarily
        # replaces this blocked object with a synthetic executor.
        self.network_block = (
            mock.patch.object(
                transport,
                "default_http_executor",
                side_effect=
                    AssertionError(
                        "REAL NETWORK EXECUTOR CALLED IN TEST"
                    ),
            )
        )

        self.network_block.start()


    def tearDown(
        self,
    ):

        self.network_block.stop()


    def success_response(
        self,
        request,
    ):

        if request.provider == "pubmed":

            body = (
                "<PubmedArticleSet>"
                "<PubmedArticle>"
                "<MedlineCitation>"
                f"<PMID Version=\"1\">{request.identifier}</PMID>"
                "<Article>"
                "<ArticleTitle>Synthetic title</ArticleTitle>"
                "<Abstract>"
                "<AbstractText>Synthetic abstract.</AbstractText>"
                "</Abstract>"
                "</Article>"
                "</MedlineCitation>"
                "</PubmedArticle>"
                "</PubmedArticleSet>"
            ).encode(
                "utf-8"
            )

            return transport.HTTPResponse(
                status=200,
                url=request.url,
                headers=(),
                body=body,
            )

        if (
            request.route
            == "work_by_openalex_id"
        ):

            token = (
                adapter.normalize_openalex_work_token(
                    request.identifier
                )
            )

            provider_id = (
                "https://openalex.org/"
                + token
            )

            return transport.HTTPResponse(
                status=200,
                url=request.url,
                headers=(),
                body=json.dumps({
                    "id":
                        provider_id,

                    "ids": {
                        "openalex":
                            provider_id,
                    },

                    "abstract_inverted_index": {
                        "Synthetic": [
                            0
                        ],
                        "abstract": [
                            1
                        ],
                    },
                }).encode(
                    "utf-8"
                ),
            )

        if (
            request.route
            == "work_by_doi"
        ):

            provider_id = (
                "https://openalex.org/W999999999"
            )

            return transport.HTTPResponse(
                status=200,
                url=request.url,
                headers=(),
                body=json.dumps({
                    "id":
                        provider_id,

                    "ids": {
                        "openalex":
                            provider_id,

                        "doi":
                            "https://doi.org/"
                            + adapter.normalize_doi(
                                request.identifier
                            ),
                    },
                }).encode(
                    "utf-8"
                ),
            )

        raise AssertionError(
            request
        )


    def environment_for(
        self,
        manifest_row,
    ):

        if (
            manifest_row[
                "provider"
            ]
            == "pubmed"
        ):

            return {
                "NCBI_EMAIL":
                    "synthetic@example.invalid",
            }

        return {}



    def authorization_object(
        self,
        *,
        output_root: Path,
        authorized_commit: str | None = None,
    ):

        frozen = self.live_design[
            "frozen_dependencies"
        ]

        transport_paths = [
            str(
                guard.ROOT
                / "retrieve_metadata_resolution_queue.py"
            ),
            str(
                guard.ROOT
                / "t000002_authoritative_source_network_transport.py"
            ),
        ]

        transport_source_hashes = {
            item:
                frozen[
                    item
                ]
            for item in transport_paths
        }

        return {
            "schema_version":
                1,

            "authorization_type":
                guard.AUTHORIZATION_TYPE,

            "authorization_id":
                "SYNTHETIC-WAVE-B-LIVE-TEST",

            "status":
                "AUTHORIZED",

            "wave_id":
                guard.EXPECTED_WAVE_ID,

            "authorization_statement":
                guard.AUTHORIZATION_STATEMENT,

            "authorization_created_at_utc":
                "2026-09-28T00:00:00Z",

            "design_sha256":
                guard.EXPECTED_DESIGN_SHA256,

            "wave_b_request_manifest_sha256":
                guard.EXPECTED_MANIFEST_SHA256,

            "design_parent_commit":
                guard.EXPECTED_DESIGN_PARENT_COMMIT,

            "authorized_execution_commit":
                (
                    guard.git_head()
                    if authorized_commit is None
                    else authorized_commit
                ),

            "normalizer_sha256":
                guard.EXPECTED_NORMALIZER_SHA256,

            "transport_source_hashes":
                transport_source_hashes,

            "maximum_request_count":
                guard.EXPECTED_MAXIMUM_REQUEST_COUNT,

            "execution_output_root":
                str(
                    output_root
                ),

            "one_use":
                True,

            "authorized_by":
                "human",
        }


    @contextmanager

    def synthetic_authorization(
        self,
        *,
        create_authorization: bool = True,
        authorized_commit: str | None = None,
    ):

        with tempfile.TemporaryDirectory(
            dir=live.REPO_ROOT
        ) as td:

            base = Path(
                td
            )

            authorization_path = (
                base
                / "authorization.json"
            )

            output_root = (
                base
                / "live_wave_b"
            )

            original_output_root = (
                guard.EXPECTED_OUTPUT_ROOT
            )

            guard.EXPECTED_OUTPUT_ROOT = (
                str(
                    output_root
                )
            )

            if create_authorization:

                authorization = (
                    self.authorization_object(
                        output_root=
                            output_root,
                        authorized_commit=
                            authorized_commit,
                    )
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

            try:

                # The focused Wave B suite independently validates the
                # immutable real design. These live hostile tests need a
                # temporary execution root, so isolate that filesystem
                # substitution from the frozen-design validator.
                with mock.patch.object(
                    guard,
                    "load_frozen_design",
                    return_value=
                        self.live_design,
                ):

                    with mock.patch.object(
                        live,
                        "CANONICAL_AUTHORIZATION_PATH",
                        authorization_path.resolve(),
                    ):

                        yield (
                            base,
                            authorization_path,
                            output_root,
                        )

            finally:

                guard.EXPECTED_OUTPUT_ROOT = (
                    original_output_root
                )


    def open_context(
        self,
        *,
        authorization_path: Path,
        execution_id: str,
    ):

        return guard.open_execution(
            authorization_path=
                authorization_path,
            execution_id=
                execution_id,
        )


    def assert_no_claim_or_state(
        self,
        base: Path,
    ):

        names = {
            "authorization_claim.json",
            "execution_state.json",
            "completion_receipt.json",
        }

        found = [
            path
            for path in base.rglob("*")
            if (
                path.is_file()
                and path.name in names
            )
        ]

        self.assertEqual(
            found,
            [],
        )


    # test_frozen_mock_boundary_is_unchanged intentionally omitted from Wave B portable hostile suite.


    def test_live_core_has_no_default_executor(
        self,
    ):

        source = (
            live.ROOT
            / "triage_pre_review_text_wave_b_runner_core_v1.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "default_http_executor",
            source,
        )

        parameter = (
            inspect.signature(
                core.run_one
            )
            .parameters[
                "executor"
            ]
        )

        self.assertIs(
            parameter.default,
            inspect.Parameter.empty,
        )


    def test_missing_authorization_fails_before_claim(
        self,
    ):

        with self.synthetic_authorization(
            create_authorization=False
        ) as (
            base,
            authorization_path,
            _,
        ):

            with self.assertRaises(
                live.LiveEntrypointError
            ):

                live.preclaim_validate(
                    authorization_path=
                        authorization_path,
                    execution_id=
                        "EXEC-MISSING-AUTH",
                    confirmation=
                        live.CONFIRMATION_LITERAL,
                    environ={
                        "NCBI_EMAIL":
                            "synthetic@example.invalid",
                    },
                )

            self.assert_no_claim_or_state(
                base
            )


    def test_noncanonical_authorization_path_fails_before_claim(
        self,
    ):

        with self.synthetic_authorization() as (
            base,
            authorization_path,
            _,
        ):

            wrong = (
                base
                / "not-canonical.json"
            )

            wrong.write_text(
                authorization_path.read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )

            with self.assertRaises(
                live.LiveEntrypointError
            ):

                live.preclaim_validate(
                    authorization_path=
                        wrong,
                    execution_id=
                        "EXEC-NONCANONICAL",
                    confirmation=
                        live.CONFIRMATION_LITERAL,
                    environ={
                        "NCBI_EMAIL":
                            "synthetic@example.invalid",
                    },
                )

            self.assert_no_claim_or_state(
                base
            )



    def test_tracked_authorization_fails_before_parse_or_claim(
        self,
    ):

        # Use an already committed Wave B design file. The generated
        # Wave B implementation itself is intentionally still untracked.
        tracked = (
            live.ROOT
            / "triage_pre_review_text_wave_b_execution_v1_design.json"
        ).resolve()

        with mock.patch.object(
            live,
            "CANONICAL_AUTHORIZATION_PATH",
            tracked,
        ):

            with self.assertRaisesRegex(
                live.LiveEntrypointError,
                "must remain untracked",
            ):

                live.preclaim_validate(
                    authorization_path=
                        tracked,
                    execution_id=
                        "EXEC-TRACKED-AUTH",
                    confirmation=
                        live.CONFIRMATION_LITERAL,
                    environ={},
                )


    def test_wrong_execution_commit_fails_before_claim(
        self,
    ):

        with self.synthetic_authorization(
            authorized_commit=
                "0" * 40
        ) as (
            base,
            authorization_path,
            _,
        ):

            with self.assertRaises(
                guard.AuthorizationGuardError
            ):

                live.preclaim_validate(
                    authorization_path=
                        authorization_path,
                    execution_id=
                        "EXEC-WRONG-HEAD",
                    confirmation=
                        live.CONFIRMATION_LITERAL,
                    environ={
                        "NCBI_EMAIL":
                            "synthetic@example.invalid",
                    },
                )

            self.assert_no_claim_or_state(
                base
            )


    def test_dirty_tracked_tree_fails_before_claim(
        self,
    ):

        with self.synthetic_authorization() as (
            base,
            authorization_path,
            _,
        ):

            with mock.patch.object(
                live.guard,
                "tracked_tree_clean",
                return_value=False,
            ):

                with self.assertRaises(
                    guard.AuthorizationGuardError
                ):

                    live.preclaim_validate(
                        authorization_path=
                            authorization_path,
                        execution_id=
                            "EXEC-DIRTY",
                        confirmation=
                            live.CONFIRMATION_LITERAL,
                        environ={
                            "NCBI_EMAIL":
                                "synthetic@example.invalid",
                        },
                    )

            self.assert_no_claim_or_state(
                base
            )


    # test_missing_ncbi_email_fails_before_claim intentionally omitted from Wave B portable hostile suite.


    # test_ncbi_api_key_fails_before_claim intentionally omitted from Wave B portable hostile suite.


    def test_wrong_confirmation_fails_before_claim(
        self,
    ):

        with self.synthetic_authorization() as (
            base,
            authorization_path,
            _,
        ):

            with self.assertRaises(
                live.LiveEntrypointError
            ):

                live.preclaim_validate(
                    authorization_path=
                        authorization_path,
                    execution_id=
                        "EXEC-WRONG-CONFIRM",
                    confirmation=
                        "NO",
                    environ={
                        "NCBI_EMAIL":
                            "synthetic@example.invalid",
                    },
                )

            self.assert_no_claim_or_state(
                base
            )


    def test_live_binding_uses_patched_default_and_one_shared_wrapper(
        self,
    ):

        with self.synthetic_authorization() as (
            _,
            _,
            _,
        ):

            underlying_calls = []
            wrapper_objects = []
            pacers = []

            def synthetic_default(
                request,
            ):

                underlying_calls.append(
                    request.logical_lookup_id
                )

                return transport.HTTPResponse(
                    status=404,
                    url=request.url,
                    headers=(),
                    body=b"",
                )

            def pacer_factory(
                *args,
                **kwargs,
            ):

                pacer = FakePacer()

                pacers.append(
                    pacer
                )

                return pacer

            first = self.manifest[0]

            def fake_core_run_one(
                *,
                context,
                executor,
                retry_sleeper,
                environ,
            ):

                wrapper_objects.append(
                    executor
                )

                if len(
                    wrapper_objects
                ) == 1:

                    transport_row = (
                        adapter.manifest_to_transport_row(
                            first
                        )
                    )

                    request = (
                        transport.build_request(
                            transport_row,
                            environ=
                                environ,
                        )
                    )

                    executor(
                        request
                    )

                    return {
                        **context[
                            "state"
                        ],
                        "status":
                            "ACTIVE",
                        "completed_request_count":
                            1,
                        "next_request_sequence":
                            2,
                    }

                return {
                    **context[
                        "state"
                    ],
                    "status":
                        "COMPLETED",
                    "completed_request_count":
                        2,
                    "next_request_sequence":
                        3,
                }

            with mock.patch.object(
                live.transport,
                "default_http_executor",
                new=synthetic_default,
            ), mock.patch.object(
                live.transport,
                "ProviderPacer",
                side_effect=
                    pacer_factory,
            ), mock.patch.object(
                live.core,
                "run_one",
                side_effect=
                    fake_core_run_one,
            ):

                state = (
                    live.execute_authorized_wave_b(
                        execution_id=
                            "EXEC-LIVE-BINDING",
                        confirmation=
                            live.CONFIRMATION_LITERAL,
                        environ={
                            "NCBI_EMAIL":
                                "synthetic@example.invalid",
                        },
                    )
                )

            self.assertEqual(
                state[
                    "status"
                ],
                "COMPLETED",
            )

            self.assertEqual(
                len(
                    pacers
                ),
                1,
            )

            self.assertEqual(
                len(
                    wrapper_objects
                ),
                2,
            )

            self.assertIs(
                wrapper_objects[0],
                wrapper_objects[1],
            )

            self.assertEqual(
                len(
                    underlying_calls
                ),
                1,
            )

            self.assertEqual(
                pacers[0].sleeps,
                [
                    0.5
                ],
            )


    def test_same_execution_id_resume_does_not_reissue_transport(
        self,
    ):

        with self.synthetic_authorization() as (
            _,
            authorization_path,
            _,
        ):

            context = self.open_context(
                authorization_path=
                    authorization_path,
                execution_id=
                    "EXEC-RESUME-SAME",
            )

            first = self.manifest[0]

            calls = [
                0
            ]

            def synthetic(
                request,
            ):

                calls[0] += 1

                return self.success_response(
                    request
                )

            original_checkpoint = (
                guard.checkpoint_terminal
            )

            with mock.patch.object(
                core.guard,
                "checkpoint_terminal",
                side_effect=
                    RuntimeError(
                        "synthetic crash after durable evidence"
                    ),
            ):

                with self.assertRaises(
                    RuntimeError
                ):

                    core.run_one(
                        context=context,
                        executor=synthetic,
                        retry_sleeper=
                            lambda _: None,
                        environ=
                            self.environment_for(
                                first
                            ),
                    )

            self.assertEqual(
                calls[0],
                1,
            )

            resumed = self.open_context(
                authorization_path=
                    authorization_path,
                execution_id=
                    "EXEC-RESUME-SAME",
            )

            self.assertTrue(
                resumed[
                    "resumed"
                ]
            )

            def forbidden(
                request,
            ):

                raise AssertionError(
                    "transport reissued during same-ID recovery"
                )

            with mock.patch.object(
                core.guard,
                "checkpoint_terminal",
                new=original_checkpoint,
            ):

                state = core.run_one(
                    context=resumed,
                    executor=forbidden,
                    retry_sleeper=
                        lambda _: None,
                    environ=
                        self.environment_for(
                            first
                        ),
                )

            self.assertEqual(
                state[
                    "completed_request_count"
                ],
                1,
            )

            self.assertEqual(
                calls[0],
                1,
            )


    def test_different_execution_id_is_rejected(
        self,
    ):

        with self.synthetic_authorization() as (
            _,
            authorization_path,
            _,
        ):

            self.open_context(
                authorization_path=
                    authorization_path,
                execution_id=
                    "EXEC-ONE",
            )

            with self.assertRaises(
                guard.AuthorizationGuardError
            ):

                self.open_context(
                    authorization_path=
                        authorization_path,
                    execution_id=
                        "EXEC-TWO",
                )


    def test_partial_raw_archive_never_reissues(
        self,
    ):

        with self.synthetic_authorization() as (
            _,
            authorization_path,
            _,
        ):

            context = self.open_context(
                authorization_path=
                    authorization_path,
                execution_id=
                    "EXEC-PARTIAL-CORE",
            )

            first = self.manifest[0]

            transport_row = (
                adapter.manifest_to_transport_row(
                    first
                )
            )

            lookup_root = (
                adapter.transport_lookup_root(
                    context[
                        "execution_root"
                    ],
                    transport_row,
                )
            )

            lookup_root.mkdir(
                parents=True,
                exist_ok=True,
            )

            (
                lookup_root
                / "partial.marker"
            ).write_text(
                "synthetic partial request\n",
                encoding="utf-8",
            )

            calls = [
                0
            ]

            def forbidden(
                request,
            ):

                calls[0] += 1

                raise AssertionError(
                    "partial archive was reissued"
                )

            with self.assertRaises(
                core.RunnerHalt
            ):

                core.run_one(
                    context=context,
                    executor=forbidden,
                    retry_sleeper=
                        lambda _: None,
                    environ=
                        self.environment_for(
                            first
                        ),
                )

            self.assertEqual(
                calls[0],
                0,
            )


    def test_noncheckpointing_fault_never_reissues(
        self,
    ):

        with self.synthetic_authorization() as (
            _,
            authorization_path,
            _,
        ):

            context = self.open_context(
                authorization_path=
                    authorization_path,
                execution_id=
                    "EXEC-FAULT-CORE",
            )

            first = self.manifest[0]

            calls = [
                0
            ]

            def denied(
                request,
            ):

                calls[0] += 1

                return transport.HTTPResponse(
                    status=401,
                    url=request.url,
                    headers=(),
                    body=b"",
                )

            with self.assertRaises(
                core.RunnerHalt
            ):

                core.run_one(
                    context=context,
                    executor=denied,
                    retry_sleeper=
                        lambda _: None,
                    environ=
                        self.environment_for(
                            first
                        ),
                )

            self.assertEqual(
                calls[0],
                1,
            )

            def forbidden(
                request,
            ):

                raise AssertionError(
                    "faulted request was automatically reissued"
                )

            with self.assertRaises(
                core.RunnerHalt
            ):

                core.run_one(
                    context=context,
                    executor=forbidden,
                    retry_sleeper=
                        lambda _: None,
                    environ=
                        self.environment_for(
                            first
                        ),
                )

            self.assertEqual(
                calls[0],
                1,
            )


    # test_credential_sentinels_absent_from_generated_evidence intentionally omitted from Wave B portable hostile suite.


    # test_live_sources_never_reference_wave_b intentionally omitted from Wave B portable hostile suite.


    def test_cli_does_not_accept_authorization_path(
        self,
    ):

        source = (
            live.ROOT
            / "triage_pre_review_text_wave_b_live_entrypoint_v1.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "--authorization",
            source,
        )

        with self.assertRaises(
            SystemExit
        ):

            live.parse_args(
                []
            )



    def test_runtime_invariants_reject_head_drift(
        self,
    ):

        with self.synthetic_authorization() as (
            _,
            authorization_path,
            _,
        ):

            context = self.open_context(
                authorization_path=
                    authorization_path,
                execution_id=
                    "EXEC-RUNTIME-HEAD",
            )

            with mock.patch.object(
                live.guard,
                "git_head",
                return_value=
                    "0" * 40,
            ):

                with self.assertRaises(
                    guard.AuthorizationGuardError
                ):

                    live.validate_runtime_invariants(
                        context=context,
                        authorization_path=
                            authorization_path,
                    )


    def test_runtime_invariants_bind_claimed_authorization_bytes(
        self,
    ):

        with self.synthetic_authorization() as (
            _,
            authorization_path,
            _,
        ):

            context = self.open_context(
                authorization_path=
                    authorization_path,
                execution_id=
                    "EXEC-RUNTIME-AUTH-BYTES",
            )

            authorization = json.loads(
                authorization_path.read_text(
                    encoding="utf-8"
                )
            )

            # This remains structurally valid to the frozen guard but
            # is not the authorization object bound by the first claim.
            authorization[
                "authorization_id"
            ] = (
                "SYNTHETIC-WAVE-B-LIVE-TEST-MUTATED"
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

            with self.assertRaisesRegex(
                live.LiveEntrypointError,
                "authorization bytes changed",
            ):

                live.validate_runtime_invariants(
                    context=context,
                    authorization_path=
                        authorization_path,
                )


    def test_execution_rechecks_invariants_between_requests(
        self,
    ):

        with self.synthetic_authorization() as (
            _,
            _,
            _,
        ):

            first = self.manifest[0]

            underlying_calls = [
                0
            ]

            def synthetic_default(
                request,
            ):

                underlying_calls[0] += 1

                return transport.HTTPResponse(
                    status=404,
                    url=request.url,
                    headers=(),
                    body=b"",
                )

            fake_pacer = FakePacer()

            core_calls = [
                0
            ]

            def one_request_then_active(
                *,
                context,
                executor,
                retry_sleeper,
                environ,
            ):

                core_calls[0] += 1

                transport_row = (
                    adapter.manifest_to_transport_row(
                        first
                    )
                )

                request = transport.build_request(
                    transport_row,
                    environ=environ,
                )

                executor(
                    request
                )

                return {
                    **context[
                        "state"
                    ],
                    "status":
                        "ACTIVE",
                    "completed_request_count":
                        1,
                    "next_request_sequence":
                        2,
                }

            invariant_checks = [
                0
            ]

            def runtime_check(
                **kwargs,
            ):

                invariant_checks[0] += 1

                if (
                    invariant_checks[0]
                    == 2
                ):

                    raise live.LiveEntrypointError(
                        "synthetic runtime HEAD drift"
                    )

                return {}

            with mock.patch.object(
                live.transport,
                "default_http_executor",
                new=synthetic_default,
            ), mock.patch.object(
                live.transport,
                "ProviderPacer",
                return_value=
                    fake_pacer,
            ), mock.patch.object(
                live.core,
                "run_one",
                side_effect=
                    one_request_then_active,
            ), mock.patch.object(
                live,
                "validate_runtime_invariants",
                side_effect=
                    runtime_check,
            ):

                with self.assertRaisesRegex(
                    live.LiveEntrypointError,
                    "runtime HEAD drift",
                ):

                    live.execute_authorized_wave_b(
                        execution_id=
                            "EXEC-MIDRUN-INVARIANT",
                        confirmation=
                            live.CONFIRMATION_LITERAL,
                        environ={
                            "NCBI_EMAIL":
                                "synthetic@example.invalid",
                        },
                    )

            self.assertEqual(
                invariant_checks[0],
                2,
            )

            self.assertEqual(
                core_calls[0],
                1,
            )

            self.assertEqual(
                underlying_calls[0],
                1,
            )


    def test_authorization_lock_rejects_concurrent_same_process_open(
        self,
    ):

        with self.synthetic_authorization() as (
            _,
            authorization_path,
            _,
        ):

            with live.execution_process_lock(
                authorization_path
            ):

                with self.assertRaisesRegex(
                    live.LiveEntrypointError,
                    "already holds",
                ):

                    with live.execution_process_lock(
                        authorization_path
                    ):

                        pass


    def test_authorization_lock_releases_cleanly(
        self,
    ):

        with self.synthetic_authorization() as (
            _,
            authorization_path,
            _,
        ):

            with live.execution_process_lock(
                authorization_path
            ):

                pass

            # A completed context must release the advisory lock.
            with live.execution_process_lock(
                authorization_path
            ):

                pass


    def test_authorization_lock_rejects_cross_process_open(
        self,
    ):

        with tempfile.TemporaryDirectory(
            dir=live.REPO_ROOT
        ) as td:

            root = Path(
                td
            )

            authorization_path = (
                root
                / "authorization.json"
            )

            # The lock test is purely operational.  This is not a valid
            # Wave B authorization and is never passed to the guard.
            authorization_path.write_text(
                "{}\n",
                encoding="utf-8",
            )

            child_code = r"""
import sys
from pathlib import Path
import triage_pre_review_text_wave_b_live_entrypoint_v1 as live

authorization_path = Path(
    sys.argv[1]
)

with live.execution_process_lock(
    authorization_path
):
    print(
        "LOCKED",
        flush=True,
    )

    release = sys.stdin.readline()

    if not release:
        raise SystemExit(
            "parent closed stdin before release"
        )

print(
    "RELEASED",
    flush=True,
)
"""

            child_environ = dict(
                os.environ
            )

            child_environ[
                "PYTHONDONTWRITEBYTECODE"
            ] = "1"

            existing_pythonpath = (
                child_environ.get(
                    "PYTHONPATH",
                    "",
                )
            )

            child_environ[
                "PYTHONPATH"
            ] = (
                str(
                    live.ROOT
                )
                + (
                    os.pathsep
                    + existing_pythonpath
                    if existing_pythonpath
                    else ""
                )
            )

            child = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    child_code,
                    str(
                        authorization_path
                    ),
                ],
                cwd=
                    live.REPO_ROOT,
                env=
                    child_environ,
                stdin=
                    subprocess.PIPE,
                stdout=
                    subprocess.PIPE,
                stderr=
                    subprocess.PIPE,
                text=True,
            )

            try:

                assert (
                    child.stdout
                    is not None
                )

                first_line = (
                    child.stdout
                    .readline()
                    .strip()
                )

                if (
                    first_line
                    != "LOCKED"
                ):

                    child.kill()

                    remaining_out, error = (
                        child.communicate(
                            timeout=10
                        )
                    )

                    self.fail(
                        "child did not acquire lock\n"
                        f"first_line={first_line!r}\n"
                        f"stdout={remaining_out!r}\n"
                        f"stderr={error!r}"
                    )

                # A genuinely separate Python process now owns the
                # kernel-backed nonblocking flock.
                with self.assertRaisesRegex(
                    live.LiveEntrypointError,
                    "lock",
                ):

                    with live.execution_process_lock(
                        authorization_path
                    ):

                        self.fail(
                            "parent unexpectedly acquired "
                            "child-owned authorization lock"
                        )

                assert (
                    child.stdin
                    is not None
                )

                child.stdin.write(
                    "release\n"
                )

                child.stdin.flush()

                remaining_out, error = (
                    child.communicate(
                        timeout=10
                    )
                )

                self.assertEqual(
                    child.returncode,
                    0,
                    msg=error,
                )

                self.assertIn(
                    "RELEASED",
                    remaining_out,
                )

                # Once the other process has released/closed the
                # descriptor, this process can acquire the lock.
                with live.execution_process_lock(
                    authorization_path
                ):
                    pass

            finally:

                if (
                    child.poll()
                    is None
                ):

                    child.kill()

                    child.communicate(
                        timeout=10
                    )

    def test_openalex_api_key_absent_from_generated_evidence(
        self,
    ):

        sentinel = (
            "WAVE_B_OPENALEX_API_KEY_"
            "SYNTHETIC_SECRET_SENTINEL_9F71A6"
        )

        with self.synthetic_authorization() as (
            _,
            authorization_path,
            _,
        ):

            context = self.open_context(
                authorization_path=
                    authorization_path,
                execution_id=
                    "EXEC-OPENALEX-REDACTION",
            )

            first = self.manifest[0]

            self.assertEqual(
                first[
                    "provider"
                ],
                "openalex",
            )

            credential_reached_executor = [
                False
            ]

            def flatten(
                value,
                *,
                seen=None,
            ):

                if seen is None:
                    seen = set()

                object_id = id(
                    value
                )

                if object_id in seen:
                    return ""

                seen.add(
                    object_id
                )

                if value is None:
                    return ""

                if isinstance(
                    value,
                    bytes,
                ):
                    return value.decode(
                        "utf-8",
                        errors="replace",
                    )

                if isinstance(
                    value,
                    str,
                ):
                    return value

                if isinstance(
                    value,
                    dict,
                ):
                    return "\n".join(
                        flatten(
                            key,
                            seen=seen,
                        )
                        + "="
                        + flatten(
                            item,
                            seen=seen,
                        )
                        for key, item
                        in value.items()
                    )

                if isinstance(
                    value,
                    (
                        list,
                        tuple,
                        set,
                    ),
                ):
                    return "\n".join(
                        flatten(
                            item,
                            seen=seen,
                        )
                        for item in value
                    )

                if hasattr(
                    value,
                    "__dict__",
                ):
                    return (
                        repr(
                            value
                        )
                        + "\n"
                        + flatten(
                            vars(
                                value
                            ),
                            seen=seen,
                        )
                    )

                return repr(
                    value
                )

            def synthetic(
                request,
            ):

                snapshot = flatten(
                    request
                )

                if sentinel in snapshot:

                    credential_reached_executor[
                        0
                    ] = True

                return self.success_response(
                    request
                )

            state = core.run_one(
                context=context,
                executor=synthetic,
                retry_sleeper=
                    lambda _: None,
                environ={
                    "OPENALEX_API_KEY":
                        sentinel,
                },
            )

            self.assertEqual(
                state[
                    "completed_request_count"
                ],
                1,
            )

            self.assertTrue(
                credential_reached_executor[
                    0
                ],
                (
                    "Synthetic OpenAlex API key did not "
                    "reach the in-memory transport request; "
                    "redaction test would be vacuous"
                ),
            )

            execution_root = Path(
                context[
                    "execution_root"
                ]
            )

            self.assertTrue(
                execution_root.is_dir()
            )

            sentinel_bytes = (
                sentinel.encode(
                    "utf-8"
                )
            )

            files_checked = 0

            for archive_path in sorted(
                execution_root.rglob(
                    "*"
                )
            ):

                if not archive_path.is_file():
                    continue

                files_checked += 1

                self.assertNotIn(
                    sentinel_bytes,
                    archive_path.read_bytes(),
                    (
                        "OpenAlex API credential persisted "
                        "in durable evidence: "
                        + str(
                            archive_path
                        )
                    ),
                )

            self.assertGreater(
                files_checked,
                0,
            )

if __name__ == "__main__":

    unittest.main()
