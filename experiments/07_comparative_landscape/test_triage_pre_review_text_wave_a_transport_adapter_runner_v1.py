from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import retrieve_metadata_resolution_queue as transport
import triage_pre_review_text_wave_a_guard_v1 as guard
import triage_pre_review_text_wave_a_transport_evidence_adapter_v1 as adapter
import triage_pre_review_text_wave_a_mock_runner_v1 as runner


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

        value = float(
            seconds
        )

        self.sleeps.append(
            value
        )

        self.value += value


class WaveAAdapterRunnerTests(
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

        cls.openalex_work = next(
            row
            for row in cls.manifest
            if (
                row[
                    "provider"
                ]
                == "openalex"
                and row[
                    "transport_route"
                ]
                == "work_by_openalex_id"
            )
        )

        cls.openalex_doi = next(
            row
            for row in cls.manifest
            if (
                row[
                    "provider"
                ]
                == "openalex"
                and row[
                    "transport_route"
                ]
                == "work_by_doi"
            )
        )

        cls.pubmed = next(
            row
            for row in cls.manifest
            if (
                row[
                    "provider"
                ]
                == "pubmed"
            )
        )


    def synthetic_work_manifest(
        self,
        requested_work,
    ):

        row = dict(
            self.openalex_work
        )

        row[
            "identifier"
        ] = requested_work

        return row


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


    def transport_row(
        self,
        manifest_row,
    ):

        return (
            adapter.manifest_to_transport_row(
                manifest_row
            )
        )


    def test_contract_loads_base_and_amendment(
        self,
    ):

        base, amendment = (
            adapter.load_contract()
        )

        self.assertEqual(
            base[
                "status"
            ],
            "FROZEN_PRE_IMPLEMENTATION",
        )

        self.assertTrue(
            amendment[
                "raw_archive_integrity_extension"
            ][
                "required"
            ]
        )


    def test_openalex_direct_work_success(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            row = self.transport_row(
                self.openalex_work
            )

            transport.transport_lookup(
                row,
                archive_root=root,
                executor=
                    self.success_response,
                sleeper=lambda _: None,
                environ={},
            )

            evidence = (
                adapter.verified_evidence(
                    manifest_row=
                        self.openalex_work,
                    archive_root=root,
                    transport_module=
                        transport,
                )
            )

            self.assertEqual(
                evidence[
                    "provider_identity_status"
                ],
                "matched",
            )

            self.assertRegex(
                evidence[
                    "raw_archive_bundle_sha256"
                ],
                r"^[0-9a-f]{64}$",
            )


    def test_openalex_redirect_w1_to_w2_is_accepted(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            manifest = (
                self.synthetic_work_manifest(
                    "W1111111111"
                )
            )

            row = self.transport_row(
                manifest
            )

            calls = [0]

            def executor(
                request,
            ):

                calls[0] += 1

                if calls[0] == 1:

                    return transport.HTTPResponse(
                        status=302,
                        url=request.url,
                        headers=(
                            (
                                "Location",
                                "https://api.openalex.org/works/W2222222222",
                            ),
                        ),
                        body=b"",
                    )

                return transport.HTTPResponse(
                    status=200,
                    url=request.url,
                    headers=(),
                    body=json.dumps({
                        "id":
                            "https://openalex.org/W2222222222",

                        "ids": {
                            "openalex":
                                "https://openalex.org/W2222222222",
                        },
                    }).encode(
                        "utf-8"
                    ),
                )

            result = (
                transport.transport_lookup(
                    row,
                    archive_root=root,
                    executor=executor,
                    sleeper=lambda _: None,
                    environ={},
                )
            )

            self.assertEqual(
                result[
                    "terminal_status"
                ],
                "success",
            )

            evidence = (
                adapter.verified_evidence(
                    manifest_row=manifest,
                    archive_root=root,
                    transport_module=
                        transport,
                )
            )

            self.assertEqual(
                evidence[
                    "provider_identity_status"
                ],
                "matched_via_verified_openalex_redirect",
            )

            self.assertEqual(
                evidence[
                    "provider_record_id"
                ],
                "https://openalex.org/W2222222222",
            )


    def test_openalex_unredirected_w1_to_w2_rejected(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            manifest = (
                self.synthetic_work_manifest(
                    "W1111111111"
                )
            )

            row = self.transport_row(
                manifest
            )

            def executor(
                request,
            ):

                return transport.HTTPResponse(
                    status=200,
                    url=request.url,
                    headers=(),
                    body=json.dumps({
                        "id":
                            "https://openalex.org/W2222222222",

                        "ids": {
                            "openalex":
                                "https://openalex.org/W2222222222",
                        },
                    }).encode(
                        "utf-8"
                    ),
                )

            transport.transport_lookup(
                row,
                archive_root=root,
                executor=executor,
                sleeper=lambda _: None,
                environ={},
            )

            with self.assertRaises(
                adapter.ProviderIdentityMismatch
            ):

                adapter.verified_evidence(
                    manifest_row=manifest,
                    archive_root=root,
                    transport_module=
                        transport,
                )


    def test_openalex_redirect_w1_to_w2_returning_w3_rejected(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            manifest = (
                self.synthetic_work_manifest(
                    "W1111111111"
                )
            )

            row = self.transport_row(
                manifest
            )

            calls = [0]

            def executor(
                request,
            ):

                calls[0] += 1

                if calls[0] == 1:

                    return transport.HTTPResponse(
                        status=302,
                        url=request.url,
                        headers=(
                            (
                                "Location",
                                "https://api.openalex.org/works/W2222222222",
                            ),
                        ),
                        body=b"",
                    )

                return transport.HTTPResponse(
                    status=200,
                    url=request.url,
                    headers=(),
                    body=json.dumps({
                        "id":
                            "https://openalex.org/W3333333333",

                        "ids": {
                            "openalex":
                                "https://openalex.org/W3333333333",
                        },
                    }).encode(
                        "utf-8"
                    ),
                )

            transport.transport_lookup(
                row,
                archive_root=root,
                executor=executor,
                sleeper=lambda _: None,
                environ={},
            )

            with self.assertRaises(
                adapter.ProviderIdentityMismatch
            ):

                adapter.verified_evidence(
                    manifest_row=manifest,
                    archive_root=root,
                    transport_module=
                        transport,
                )


    def test_openalex_doi_identity_still_enforced(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            row = self.transport_row(
                self.openalex_doi
            )

            def mismatch(
                request,
            ):

                return transport.HTTPResponse(
                    status=200,
                    url=request.url,
                    headers=(),
                    body=json.dumps({
                        "id":
                            "https://openalex.org/W999999997",

                        "ids": {
                            "openalex":
                                "https://openalex.org/W999999997",

                            "doi":
                                "https://doi.org/10.9999/not-requested",
                        },
                    }).encode(
                        "utf-8"
                    ),
                )

            transport.transport_lookup(
                row,
                archive_root=root,
                executor=mismatch,
                sleeper=lambda _: None,
                environ={},
            )

            with self.assertRaises(
                adapter.ProviderIdentityMismatch
            ):

                adapter.verified_evidence(
                    manifest_row=
                        self.openalex_doi,
                    archive_root=root,
                    transport_module=
                        transport,
                )


    def test_not_found_verified(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            row = self.transport_row(
                self.openalex_work
            )

            def missing(
                request,
            ):

                return transport.HTTPResponse(
                    status=404,
                    url=request.url,
                    headers=(),
                    body=b'{"error":"not found"}',
                )

            transport.transport_lookup(
                row,
                archive_root=root,
                executor=missing,
                sleeper=lambda _: None,
                environ={},
            )

            evidence = (
                adapter.verified_evidence(
                    manifest_row=
                        self.openalex_work,
                    archive_root=root,
                    transport_module=
                        transport,
                )
            )

            self.assertEqual(
                evidence[
                    "adapter_status"
                ],
                "verified_not_found",
            )


    def test_pubmed_success_verified(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            row = self.transport_row(
                self.pubmed
            )

            transport.transport_lookup(
                row,
                archive_root=root,
                executor=
                    self.success_response,
                sleeper=lambda _: None,
                environ={
                    "NCBI_EMAIL":
                        "synthetic@example.invalid",
                },
            )

            evidence = (
                adapter.verified_evidence(
                    manifest_row=
                        self.pubmed,
                    archive_root=root,
                    transport_module=
                        transport,
                )
            )

            self.assertEqual(
                evidence[
                    "provider_identity_status"
                ],
                "matched",
            )


    def test_raw_archive_bundle_detects_nonbody_tamper(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            row = self.transport_row(
                self.openalex_work
            )

            transport.transport_lookup(
                row,
                archive_root=root,
                executor=
                    self.success_response,
                sleeper=lambda _: None,
                environ={},
            )

            lookup_root = (
                adapter.transport_lookup_root(
                    root,
                    row,
                )
            )

            before = (
                adapter.raw_archive_bundle_sha256(
                    lookup_root
                )
            )

            request_path = next(
                lookup_root.rglob(
                    "request.json"
                )
            )

            value = json.loads(
                request_path.read_text(
                    encoding="utf-8"
                )
            )

            value[
                "synthetic_tamper"
            ] = True

            request_path.write_text(
                json.dumps(
                    value,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            after = (
                adapter.raw_archive_bundle_sha256(
                    lookup_root
                )
            )

            self.assertNotEqual(
                before,
                after,
            )


    def test_archive_body_tamper_rejected(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            row = self.transport_row(
                self.openalex_work
            )

            transport.transport_lookup(
                row,
                archive_root=root,
                executor=
                    self.success_response,
                sleeper=lambda _: None,
                environ={},
            )

            lookup_root = (
                adapter.transport_lookup_root(
                    root,
                    row,
                )
            )

            body = next(
                lookup_root.rglob(
                    "hop_*_body.bin"
                )
            )

            body.write_bytes(
                b"TAMPERED"
            )

            with self.assertRaises(
                adapter.TransportEvidenceFault
            ):

                adapter.verified_evidence(
                    manifest_row=
                        self.openalex_work,
                    archive_root=root,
                    transport_module=
                        transport,
                )


    def make_authorization(
        self,
        root: Path,
    ):

        authorization_path = (
            root
            / "authorization.json"
        )

        authorization = {
            "schema_version":
                1,

            "authorization_type":
                guard.AUTHORIZATION_TYPE,

            "authorization_id":
                "SYNTHETIC-WAVE-A-AUTH",

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

            "wave_a_request_manifest_sha256":
                guard.EXPECTED_MANIFEST_SHA256,

            "design_parent_commit":
                guard.EXPECTED_DESIGN_PARENT_COMMIT,

            "authorized_execution_commit":
                guard.git_head(),

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
                    root
                    / "live_wave_a"
                ),

            "one_use":
                True,

            "authorized_by":
                "human",
        }

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


    def open_test_context(
        self,
        root: Path,
        execution_id: str,
    ):

        authorization_path, authorization = (
            self.make_authorization(
                root
            )
        )

        original = (
            guard.EXPECTED_OUTPUT_ROOT
        )

        guard.EXPECTED_OUTPUT_ROOT = (
            authorization[
                "execution_output_root"
            ]
        )

        context = (
            guard.open_execution(
                authorization_path=
                    authorization_path,
                execution_id=
                    execution_id,
            )
        )

        return (
            context,
            original,
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


    def test_cold_start_waits_before_first_request(
        self,
    ):

        clock = FakeClock()

        pacer = transport.ProviderPacer(
            interval_seconds=0.5,
            monotonic=
                clock.monotonic,
            sleeper=
                clock.sleep,
        )

        observed = []

        def executor(
            request,
        ):

            observed.append(
                clock.monotonic()
            )

            return transport.HTTPResponse(
                status=404,
                url=request.url,
                headers=(),
                body=b"",
            )

        wrapped = (
            runner.make_paced_executor(
                executor=executor,
                pacer=pacer,
            )
        )

        request = transport.build_request(
            self.transport_row(
                self.openalex_work
            ),
            environ={},
        )

        wrapped(
            request
        )

        self.assertEqual(
            observed,
            [
                0.5
            ],
        )

        self.assertEqual(
            clock.sleeps,
            [
                0.5
            ],
        )


    def test_redirect_is_paced_after_cold_start(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            manifest = (
                self.synthetic_work_manifest(
                    "W1111111111"
                )
            )

            row = self.transport_row(
                manifest
            )

            clock = FakeClock()

            pacer = transport.ProviderPacer(
                interval_seconds=0.5,
                monotonic=
                    clock.monotonic,
                sleeper=
                    clock.sleep,
            )

            call_times = []

            def executor(
                request,
            ):

                call_times.append(
                    clock.monotonic()
                )

                if len(
                    call_times
                ) == 1:

                    return transport.HTTPResponse(
                        status=302,
                        url=request.url,
                        headers=(
                            (
                                "Location",
                                "https://api.openalex.org/works/W2222222222",
                            ),
                        ),
                        body=b"",
                    )

                return transport.HTTPResponse(
                    status=200,
                    url=request.url,
                    headers=(),
                    body=json.dumps({
                        "id":
                            "https://openalex.org/W2222222222",

                        "ids": {
                            "openalex":
                                "https://openalex.org/W2222222222",
                        },
                    }).encode(
                        "utf-8"
                    ),
                )

            wrapped = (
                runner.make_paced_executor(
                    executor=executor,
                    pacer=pacer,
                )
            )

            transport.transport_lookup(
                row,
                archive_root=root,
                executor=wrapped,
                sleeper=lambda _: None,
                environ={},
            )

            self.assertEqual(
                call_times,
                [
                    0.5,
                    1.0,
                ],
            )

            self.assertEqual(
                clock.sleeps,
                [
                    0.5,
                    0.5,
                ],
            )


    def test_mock_runner_checkpoints_first_manifest_request(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            context, original = (
                self.open_test_context(
                    root,
                    "EXEC-MOCK-001",
                )
            )

            try:

                first = self.manifest[0]

                clock = FakeClock()

                pacer = transport.ProviderPacer(
                    interval_seconds=0.5,
                    monotonic=
                        clock.monotonic,
                    sleeper=
                        clock.sleep,
                )

                state = runner.run_one(
                    context=context,
                    executor=
                        self.success_response,
                    pacer=pacer,
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

                evidence = (
                    adapter.read_evidence(
                        execution_root=
                            context[
                                "execution_root"
                            ],
                        sequence=1,
                    )
                )

                self.assertTrue(
                    evidence[
                        "checkpoint_eligible"
                    ]
                )

                self.assertRegex(
                    evidence[
                        "raw_archive_bundle_sha256"
                    ],
                    r"^[0-9a-f]{64}$",
                )

            finally:

                guard.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_transport_failure_never_checkpoints(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            context, original = (
                self.open_test_context(
                    root,
                    "EXEC-FAULT-001",
                )
            )

            try:

                first = self.manifest[0]

                clock = FakeClock()

                pacer = transport.ProviderPacer(
                    interval_seconds=0.5,
                    monotonic=
                        clock.monotonic,
                    sleeper=
                        clock.sleep,
                )

                calls = [0]

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
                    runner.RunnerHalt
                ):

                    runner.run_one(
                        context=context,
                        executor=denied,
                        pacer=pacer,
                        retry_sleeper=
                            lambda _: None,
                        environ=
                            self.environment_for(
                                first
                            ),
                    )

                state = (
                    runner.refreshed_state(
                        context
                    )
                )

                self.assertEqual(
                    state[
                        "completed_request_count"
                    ],
                    0,
                )

                self.assertEqual(
                    calls[0],
                    1,
                )

            finally:

                guard.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_partial_raw_archive_halts_without_executor(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            context, original = (
                self.open_test_context(
                    root,
                    "EXEC-PARTIAL-001",
                )
            )

            try:

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
                    "synthetic crash\n",
                    encoding="utf-8",
                )

                calls = [0]

                def forbidden(
                    request,
                ):

                    calls[0] += 1

                    raise AssertionError(
                        "executor unexpectedly called"
                    )

                clock = FakeClock()

                pacer = transport.ProviderPacer(
                    interval_seconds=0.5,
                    monotonic=
                        clock.monotonic,
                    sleeper=
                        clock.sleep,
                )

                with self.assertRaises(
                    runner.RunnerHalt
                ):

                    runner.run_one(
                        context=context,
                        executor=forbidden,
                        pacer=pacer,
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

            finally:

                guard.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_durable_evidence_precedes_guard_checkpoint(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            context, original = (
                self.open_test_context(
                    root,
                    "EXEC-ORDER-001",
                )
            )

            try:

                first = self.manifest[0]

                clock = FakeClock()

                pacer = transport.ProviderPacer(
                    interval_seconds=0.5,
                    monotonic=
                        clock.monotonic,
                    sleeper=
                        clock.sleep,
                )

                original_checkpoint = (
                    guard.checkpoint_terminal
                )

                observed = [False]

                def checking_checkpoint(
                    **kwargs,
                ):

                    path = (
                        adapter.evidence_path(
                            context[
                                "execution_root"
                            ],
                            1,
                        )
                    )

                    self.assertTrue(
                        path.is_file()
                    )

                    adapter.read_evidence_path(
                        path
                    )

                    observed[0] = True

                    return original_checkpoint(
                        **kwargs
                    )

                with mock.patch.object(
                    runner.guard,
                    "checkpoint_terminal",
                    side_effect=
                        checking_checkpoint,
                ):

                    runner.run_one(
                        context=context,
                        executor=
                            self.success_response,
                        pacer=pacer,
                        retry_sleeper=
                            lambda _: None,
                        environ=
                            self.environment_for(
                                first
                            ),
                    )

                self.assertTrue(
                    observed[0]
                )

            finally:

                guard.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_raw_archive_tamper_blocks_evidence_recovery(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            context, original = (
                self.open_test_context(
                    root,
                    "EXEC-TAMPER-001",
                )
            )

            try:

                first = self.manifest[0]

                clock = FakeClock()

                pacer = transport.ProviderPacer(
                    interval_seconds=0.5,
                    monotonic=
                        clock.monotonic,
                    sleeper=
                        clock.sleep,
                )

                def crash(
                    **kwargs,
                ):

                    raise RuntimeError(
                        "synthetic crash"
                    )

                with mock.patch.object(
                    runner.guard,
                    "checkpoint_terminal",
                    side_effect=crash,
                ):

                    with self.assertRaises(
                        RuntimeError
                    ):

                        runner.run_one(
                            context=context,
                            executor=
                                self.success_response,
                            pacer=pacer,
                            retry_sleeper=
                                lambda _: None,
                            environ=
                                self.environment_for(
                                    first
                                ),
                        )

                evidence = (
                    adapter.read_evidence(
                        execution_root=
                            context[
                                "execution_root"
                            ],
                        sequence=1,
                    )
                )

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

                request_path = next(
                    lookup_root.rglob(
                        "request.json"
                    )
                )

                value = json.loads(
                    request_path.read_text(
                        encoding="utf-8"
                    )
                )

                value[
                    "tampered"
                ] = True

                request_path.write_text(
                    json.dumps(
                        value,
                        sort_keys=True,
                    ),
                    encoding="utf-8",
                )

                self.assertNotEqual(
                    evidence[
                        "raw_archive_bundle_sha256"
                    ],
                    adapter.raw_archive_bundle_sha256(
                        lookup_root
                    ),
                )

                calls = [0]

                def forbidden(
                    request,
                ):

                    calls[0] += 1

                    raise AssertionError(
                        "transport was reissued"
                    )

                with self.assertRaises(
                    runner.RunnerHalt
                ):

                    runner.run_one(
                        context=context,
                        executor=forbidden,
                        pacer=pacer,
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

            finally:

                guard.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_no_default_http_executor_path(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            context, original = (
                self.open_test_context(
                    root,
                    "EXEC-NETWORK-001",
                )
            )

            try:

                first = self.manifest[0]

                clock = FakeClock()

                pacer = transport.ProviderPacer(
                    interval_seconds=0.5,
                    monotonic=
                        clock.monotonic,
                    sleeper=
                        clock.sleep,
                )

                with mock.patch.object(
                    transport,
                    "default_http_executor",
                    side_effect=
                        AssertionError(
                            "default HTTP executor called"
                        ),
                ):

                    runner.run_one(
                        context=context,
                        executor=
                            self.success_response,
                        pacer=pacer,
                        retry_sleeper=
                            lambda _: None,
                        environ=
                            self.environment_for(
                                first
                            ),
                    )

            finally:

                guard.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_pubmed_live_preflight_requires_email(
        self,
    ):

        with self.assertRaises(
            runner.RunnerHalt
        ):

            runner.preflight_environment(
                manifest_row=
                    self.pubmed,
                environ={},
            )

        with self.assertRaises(
            runner.RunnerHalt
        ):

            runner.preflight_environment(
                manifest_row=
                    self.pubmed,
                environ={
                    "NCBI_EMAIL":
                        "synthetic@example.invalid",

                    "NCBI_API_KEY":
                        "forbidden",
                },
            )



    def test_pubmed_mismatch_remains_rejected(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            row = self.transport_row(
                self.pubmed
            )

            def mismatch(
                request,
            ):

                wrong = (
                    "99999999"
                    if request.identifier
                    != "99999999"
                    else "88888888"
                )

                body = (
                    "<PubmedArticleSet>"
                    "<PubmedArticle>"
                    "<MedlineCitation>"
                    f"<PMID Version=\"1\">{wrong}</PMID>"
                    "<Article>"
                    "<ArticleTitle>Synthetic mismatch</ArticleTitle>"
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

            result = (
                transport.transport_lookup(
                    row,
                    archive_root=root,
                    executor=mismatch,
                    sleeper=lambda _: None,
                    environ={
                        "NCBI_EMAIL":
                            "synthetic@example.invalid",
                    },
                )
            )

            self.assertEqual(
                result[
                    "terminal_status"
                ],
                "response_integrity_failure",
            )

            terminal = (
                adapter.terminal_json_path(
                    root,
                    row,
                )
            )

            self.assertFalse(
                terminal.exists()
            )


    def test_not_found_archive_tamper_rejected(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            row = self.transport_row(
                self.openalex_work
            )

            def missing(
                request,
            ):

                return transport.HTTPResponse(
                    status=404,
                    url=request.url,
                    headers=(),
                    body=b'{"error":"not found"}',
                )

            transport.transport_lookup(
                row,
                archive_root=root,
                executor=missing,
                sleeper=lambda _: None,
                environ={},
            )

            evidence = (
                adapter.verified_evidence(
                    manifest_row=
                        self.openalex_work,
                    archive_root=root,
                    transport_module=
                        transport,
                )
            )

            self.assertEqual(
                evidence[
                    "adapter_status"
                ],
                "verified_not_found",
            )

            lookup_root = (
                adapter.transport_lookup_root(
                    root,
                    row,
                )
            )

            body = next(
                lookup_root.rglob(
                    "hop_*_body.bin"
                )
            )

            body.write_bytes(
                b"TAMPERED-NOT-FOUND"
            )

            with self.assertRaises(
                adapter.TransportEvidenceFault
            ):

                adapter.verified_evidence(
                    manifest_row=
                        self.openalex_work,
                    archive_root=root,
                    transport_module=
                        transport,
                )


    def test_redirect_metadata_tamper_after_durable_evidence_rejected(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            manifest = (
                self.synthetic_work_manifest(
                    "W1111111111"
                )
            )

            row = self.transport_row(
                manifest
            )

            calls = [0]

            def executor(
                request,
            ):

                calls[0] += 1

                if calls[0] == 1:

                    return transport.HTTPResponse(
                        status=302,
                        url=request.url,
                        headers=(
                            (
                                "Location",
                                "https://api.openalex.org/works/W2222222222",
                            ),
                        ),
                        body=b"",
                    )

                return transport.HTTPResponse(
                    status=200,
                    url=request.url,
                    headers=(),
                    body=json.dumps({
                        "id":
                            "https://openalex.org/W2222222222",

                        "ids": {
                            "openalex":
                                "https://openalex.org/W2222222222",
                        },
                    }).encode(
                        "utf-8"
                    ),
                )

            transport.transport_lookup(
                row,
                archive_root=root,
                executor=executor,
                sleeper=lambda _: None,
                environ={},
            )

            evidence = (
                adapter.verified_evidence(
                    manifest_row=manifest,
                    archive_root=root,
                    transport_module=
                        transport,
                )
            )

            adapter.write_evidence(
                execution_root=root,
                evidence=evidence,
            )

            lookup_root = (
                adapter.transport_lookup_root(
                    root,
                    row,
                )
            )

            first_hop = (
                lookup_root
                / "attempt_01"
                / "hop_00_response.json"
            )

            value = json.loads(
                first_hop.read_text(
                    encoding="utf-8"
                )
            )

            value[
                "response_headers"
            ] = [
                [
                    "Location",
                    "https://example.com/works/W2222222222",
                ]
            ]

            first_hop.write_text(
                json.dumps(
                    value,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            durable = (
                adapter.read_evidence(
                    execution_root=root,
                    sequence=int(
                        manifest[
                            "request_sequence"
                        ]
                    ),
                )
            )

            self.assertNotEqual(
                durable[
                    "raw_archive_bundle_sha256"
                ],
                adapter.raw_archive_bundle_sha256(
                    lookup_root
                ),
            )

            with self.assertRaises(
                adapter.ProviderIdentityMismatch
            ):

                adapter.verified_evidence(
                    manifest_row=manifest,
                    archive_root=root,
                    transport_module=
                        transport,
                )


    def test_identity_mismatch_runner_never_checkpoints(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            context, original = (
                self.open_test_context(
                    root,
                    "EXEC-ID-MISMATCH-001",
                )
            )

            try:

                synthetic = dict(
                    self.openalex_work
                )

                synthetic[
                    "request_sequence"
                ] = "1"

                synthetic[
                    "request_identity_sha256"
                ] = self.manifest[0][
                    "request_identity_sha256"
                ]

                def mismatch(
                    request,
                ):

                    return transport.HTTPResponse(
                        status=200,
                        url=request.url,
                        headers=(),
                        body=json.dumps({
                            "id":
                                "https://openalex.org/W999999991",

                            "ids": {
                                "openalex":
                                    "https://openalex.org/W999999991",
                            },
                        }).encode(
                            "utf-8"
                        ),
                    )

                clock = FakeClock()

                pacer = transport.ProviderPacer(
                    interval_seconds=0.5,
                    monotonic=
                        clock.monotonic,
                    sleeper=
                        clock.sleep,
                )

                with mock.patch.object(
                    runner.guard,
                    "manifest_row_for_sequence",
                    return_value=synthetic,
                ):

                    with self.assertRaises(
                        runner.RunnerHalt
                    ):

                        runner.run_one(
                            context=context,
                            executor=mismatch,
                            pacer=pacer,
                            retry_sleeper=
                                lambda _: None,
                            environ={},
                        )

                state = (
                    runner.refreshed_state(
                        context
                    )
                )

                self.assertEqual(
                    state[
                        "completed_request_count"
                    ],
                    0,
                )

                checkpoint = (
                    guard.request_checkpoint_path(
                        context[
                            "execution_root"
                        ],
                        1,
                    )
                )

                self.assertFalse(
                    checkpoint.exists()
                )

            finally:

                guard.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_crash_after_durable_evidence_recovers_without_transport(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            context, original = (
                self.open_test_context(
                    root,
                    "EXEC-EVIDENCE-RECOVERY-001",
                )
            )

            try:

                first = self.manifest[0]

                clock = FakeClock()

                pacer = transport.ProviderPacer(
                    interval_seconds=0.5,
                    monotonic=
                        clock.monotonic,
                    sleeper=
                        clock.sleep,
                )

                with mock.patch.object(
                    runner.guard,
                    "checkpoint_terminal",
                    side_effect=
                        RuntimeError(
                            "synthetic crash after durable evidence"
                        ),
                ):

                    with self.assertRaises(
                        RuntimeError
                    ):

                        runner.run_one(
                            context=context,
                            executor=
                                self.success_response,
                            pacer=pacer,
                            retry_sleeper=
                                lambda _: None,
                            environ=
                                self.environment_for(
                                    first
                                ),
                        )

                state = (
                    runner.refreshed_state(
                        context
                    )
                )

                self.assertEqual(
                    state[
                        "completed_request_count"
                    ],
                    0,
                )

                adapter.read_evidence(
                    execution_root=
                        context[
                            "execution_root"
                        ],
                    sequence=1,
                )

                def forbidden(
                    request,
                ):

                    raise AssertionError(
                        "transport reissued during durable-evidence recovery"
                    )

                state = runner.run_one(
                    context=context,
                    executor=forbidden,
                    pacer=pacer,
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

            finally:

                guard.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_second_run_advances_without_duplicate(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            context, original = (
                self.open_test_context(
                    root,
                    "EXEC-SEQUENCE-001",
                )
            )

            try:

                clock = FakeClock()

                pacer = transport.ProviderPacer(
                    interval_seconds=0.5,
                    monotonic=
                        clock.monotonic,
                    sleeper=
                        clock.sleep,
                )

                seen = []

                def recording_success(
                    request,
                ):

                    seen.append(
                        request.logical_lookup_id
                    )

                    return self.success_response(
                        request
                    )

                first = self.manifest[0]

                runner.run_one(
                    context=context,
                    executor=
                        recording_success,
                    pacer=pacer,
                    retry_sleeper=
                        lambda _: None,
                    environ=
                        self.environment_for(
                            first
                        ),
                )

                second = self.manifest[1]

                runner.run_one(
                    context=context,
                    executor=
                        recording_success,
                    pacer=pacer,
                    retry_sleeper=
                        lambda _: None,
                    environ=
                        self.environment_for(
                            second
                        ),
                )

                expected = [
                    adapter.manifest_to_transport_row(
                        first
                    )[
                        "logical_lookup_id"
                    ],

                    adapter.manifest_to_transport_row(
                        second
                    )[
                        "logical_lookup_id"
                    ],
                ]

                self.assertEqual(
                    seen,
                    expected,
                )

                self.assertNotEqual(
                    seen[0],
                    seen[1],
                )

                state = (
                    runner.refreshed_state(
                        context
                    )
                )

                self.assertEqual(
                    state[
                        "completed_request_count"
                    ],
                    2,
                )

                self.assertEqual(
                    state[
                        "next_request_sequence"
                    ],
                    3,
                )

            finally:

                guard.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_mock_runner_rejects_default_http_executor(
        self,
    ):

        clock = FakeClock()

        pacer = transport.ProviderPacer(
            interval_seconds=0.5,
            monotonic=
                clock.monotonic,
            sleeper=
                clock.sleep,
        )

        with self.assertRaises(
            runner.RunnerHalt
        ):

            runner.make_paced_executor(
                executor=
                    transport.default_http_executor,
                pacer=pacer,
            )


if __name__ == "__main__":
    unittest.main()
