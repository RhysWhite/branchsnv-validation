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
import pre_review_triage_future_text_wave_a_guard_v1 as guard
import pre_review_triage_future_text_wave_a_live_entrypoint_v1 as live
import pre_review_triage_future_text_wave_a_runner_core_v1 as core
import triage_pre_review_text_wave_a_transport_evidence_adapter_v1 as adapter


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


class WaveALiveEntrypointTests(
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

        return {
            "schema_version":
                1,

            "authorization_type":
                guard.AUTHORIZATION_TYPE,

            "authorization_id":
                "SYNTHETIC-WAVE-A-LIVE-TEST",

            "status":
                "AUTHORIZED",

            "wave_id":
                guard.EXPECTED_WAVE_ID,

            "authorization_statement":
                guard.AUTHORIZATION_STATEMENT,

            "authorization_created_at_utc":
                "2026-09-28T00:00:00Z",

            "amendment_design_sha256":
                guard.EXPECTED_DESIGN_SHA256,

            "base_design_sha256":
                guard.EXPECTED_BASE_DESIGN_SHA256,

            "amended_wave_a_request_manifest_sha256":
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
                self.live_design[
                    "transport_contract"
                ][
                    "transport_sources"
                ],

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
                / "live_wave_a"
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


    def test_frozen_mock_boundary_is_unchanged(
        self,
    ):

        path = (
            live.ROOT
            / "triage_pre_review_text_wave_a_mock_runner_v1.py"
        )

        self.assertEqual(
            live.sha256_file(
                path
            ),
            "21c67dd6791aac29d995ab33828ec6ff444fd4e52d911a10fd20809d30ca5242",
        )


    def test_live_core_has_no_default_executor(
        self,
    ):

        source = (
            live.ROOT
            / "pre_review_triage_future_text_wave_a_runner_core_v1.py"
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

        tracked = (
            live.ROOT
            / "pre_review_triage_future_text_wave_a_guard_v1.py"
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
                    environ={
                        "NCBI_EMAIL":
                            "synthetic@example.invalid",
                    },
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


    def test_missing_ncbi_email_fails_before_claim(
        self,
    ):

        with self.synthetic_authorization() as (
            base,
            authorization_path,
            _,
        ):

            with self.assertRaisesRegex(
                live.LiveEntrypointError,
                "NCBI_EMAIL",
            ):

                live.preclaim_validate(
                    authorization_path=
                        authorization_path,
                    execution_id=
                        "EXEC-NO-EMAIL",
                    confirmation=
                        live.CONFIRMATION_LITERAL,
                    environ={},
                )

            self.assert_no_claim_or_state(
                base
            )


    def test_ncbi_api_key_fails_before_claim(
        self,
    ):

        with self.synthetic_authorization() as (
            base,
            authorization_path,
            _,
        ):

            with self.assertRaisesRegex(
                live.LiveEntrypointError,
                "NCBI_API_KEY",
            ):

                live.preclaim_validate(
                    authorization_path=
                        authorization_path,
                    execution_id=
                        "EXEC-NCBI-KEY",
                    confirmation=
                        live.CONFIRMATION_LITERAL,
                    environ={
                        "NCBI_EMAIL":
                            "synthetic@example.invalid",

                        "NCBI_API_KEY":
                            "FORBIDDEN-SECRET",
                    },
                )

            self.assert_no_claim_or_state(
                base
            )


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
                    live.execute_authorized_wave_a(
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


    def test_credential_sentinels_absent_from_generated_evidence(
        self,
    ):

        with self.synthetic_authorization() as (
            base,
            authorization_path,
            _,
        ):

            context = self.open_context(
                authorization_path=
                    authorization_path,
                execution_id=
                    "EXEC-CREDENTIAL-SENTINEL",
            )

            first = self.manifest[0]

            email_secret = (
                "VERY-SECRET-NCBI-CONTACT@example.invalid"
            )

            openalex_secret = (
                "VERY-SECRET-OPENALEX-KEY"
            )

            environ = {
                "NCBI_EMAIL":
                    email_secret,

                "OPENALEX_API_KEY":
                    openalex_secret,
            }

            core.run_one(
                context=context,
                executor=
                    self.success_response,
                retry_sleeper=
                    lambda _: None,
                environ=environ,
            )

            prohibited = [
                email_secret.encode(
                    "utf-8"
                ),
                openalex_secret.encode(
                    "utf-8"
                ),
            ]

            for path in base.rglob("*"):

                if not path.is_file():

                    continue

                raw = path.read_bytes()

                for secret in prohibited:

                    self.assertNotIn(
                        secret,
                        raw,
                        msg=str(
                            path
                        ),
                    )


    def test_live_sources_never_reference_wave_b(
        self,
    ):

        for name in (
            "pre_review_triage_future_text_wave_a_runner_core_v1.py",
            "pre_review_triage_future_text_wave_a_live_entrypoint_v1.py",
        ):

            source = (
                live.ROOT
                / name
            ).read_text(
                encoding="utf-8"
            ).lower()

            self.assertNotIn(
                "wave_b",
                source,
            )


    def test_cli_does_not_accept_authorization_path(
        self,
    ):

        source = (
            live.ROOT
            / "pre_review_triage_future_text_wave_a_live_entrypoint_v1.py"
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
                "SYNTHETIC-WAVE-A-LIVE-TEST-MUTATED"
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

                    live.execute_authorized_wave_a(
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
            # Wave A authorization and is never passed to the guard.
            authorization_path.write_text(
                "{}\n",
                encoding="utf-8",
            )

            child_code = r"""
import sys
from pathlib import Path
import pre_review_triage_future_text_wave_a_live_entrypoint_v1 as live

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

class FutureAuthorityBindingTests(
    unittest.TestCase
):

    def test_future_amendment_001_authority_is_bound(
        self,
    ):

        self.assertEqual(
            guard.EXPECTED_DESIGN_SHA256,
            (
                "576c45e6294031980e56f63bd1f9c272"
                "701f11c89ec1afa7dd8aad999ddaf968"
            ),
        )

        self.assertEqual(
            guard.EXPECTED_BASE_DESIGN_SHA256,
            (
                "826e400faccf7481219cd04661a4e7e"
                "785903ec2876e1384ef5cfda3b10dd9e5"
            ),
        )

        self.assertEqual(
            guard.EXPECTED_MANIFEST_SHA256,
            (
                "9c5a1b7cda465f0f4a88fc06c612c979"
                "af3093f0cecabbe4d8b42576cac30e73"
            ),
        )

        self.assertEqual(
            guard.EXPECTED_MAXIMUM_REQUEST_COUNT,
            12147,
        )

        self.assertEqual(
            live.CANONICAL_AUTHORIZATION_PATH,
            (
                live.REPO_ROOT
                / (
                    "results/07_comparative_landscape/"
                    "pre_review_triage_future_text_retrieval_v1/"
                    "live_wave_a/authorization.json"
                )
            ).resolve(),
        )


    def test_entrypoint_dependencies_bind_committed_future_guard_and_core(
        self,
    ):

        live.validate_frozen_dependencies()

        guard_path, guard_sha = (
            live.FROZEN_DEPENDENCIES[
                "authorization_guard"
            ]
        )

        core_path, core_sha = (
            live.FROZEN_DEPENDENCIES[
                "future_runner_core"
            ]
        )

        amendment_path, amendment_sha = (
            live.FROZEN_DEPENDENCIES[
                "future_live_retrieval_amendment_001"
            ]
        )

        self.assertEqual(
            guard_path,
            live.ROOT
            / "pre_review_triage_future_text_wave_a_guard_v1.py",
        )

        self.assertEqual(
            guard_sha,
            (
                "79300875f7620afde503f70b27a78449"
                "d11fcda35c23b11dc44d2fe538bcb28c"
            ),
        )

        self.assertEqual(
            core_path,
            live.ROOT
            / "pre_review_triage_future_text_wave_a_runner_core_v1.py",
        )

        self.assertEqual(
            core_sha,
            (
                "c4775bfcef700ee7df35c32dafbeb97f5"
                "46ff6c14b935f675ae2f745ba8144cd"
            ),
        )

        self.assertEqual(
            amendment_path,
            live.ROOT
            / (
                "pre_review_triage_future_text_live_retrieval_v1_"
                "amendment_001_design.json"
            ),
        )

        self.assertEqual(
            amendment_sha,
            (
                "576c45e6294031980e56f63bd1f9c272"
                "701f11c89ec1afa7dd8aad999ddaf968"
            ),
        )

        self.assertIs(
            live.guard,
            guard,
        )

        self.assertIs(
            live.core.guard,
            guard,
        )



if __name__ == "__main__":

    unittest.main()
