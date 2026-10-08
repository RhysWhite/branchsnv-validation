from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import triage_pre_review_text_wave_a_guard_v1 as g


class WaveAGuardTests(
    unittest.TestCase,
):

    @classmethod
    def setUpClass(
        cls,
    ):

        cls.design = g.load_frozen_design()

        cls.manifest = g.read_manifest()


    def valid_authorization(
        self,
        root: Path,
    ) -> tuple[Path, dict]:

        path = (
            root
            / "authorization.json"
        )

        authorization = {
            "schema_version":
                1,

            "authorization_type":
                g.AUTHORIZATION_TYPE,

            "authorization_id":
                "TEST-AUTH-WAVE-A-0001",

            "status":
                "AUTHORIZED",

            "wave_id":
                g.EXPECTED_WAVE_ID,

            "authorization_statement":
                g.AUTHORIZATION_STATEMENT,

            "authorization_created_at_utc":
                "2026-09-28T00:00:00Z",

            "design_sha256":
                g.EXPECTED_DESIGN_SHA256,

            "wave_a_request_manifest_sha256":
                g.EXPECTED_MANIFEST_SHA256,

            "design_parent_commit":
                g.EXPECTED_DESIGN_PARENT_COMMIT,

            "authorized_execution_commit":
                g.git_head(),

            "normalizer_sha256":
                g.EXPECTED_NORMALIZER_SHA256,

            "transport_source_hashes":
                self.design[
                    "transport_contract"
                ][
                    "transport_sources"
                ],

            "maximum_request_count":
                g.EXPECTED_MAXIMUM_REQUEST_COUNT,

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

        # The guard fixes the production output-root string.
        # Tests patch only after validating the static authorization
        # contract directly, then use a temporary execution root via
        # the helper below.
        authorization[
            "execution_output_root"
        ] = g.EXPECTED_OUTPUT_ROOT

        path.write_text(
            json.dumps(
                authorization,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        return path, authorization


    def write_authorization(
        self,
        path: Path,
        authorization: dict,
    ) -> None:

        path.write_text(
            json.dumps(
                authorization,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


    def test_missing_authorization_fails_closed(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            path = (
                Path(td)
                / "missing.json"
            )

            with self.assertRaises(
                g.AuthorizationGuardError
            ):
                g.validate_authorization(
                    path
                )


    def test_valid_authorization_contract(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            path, _ = (
                self.valid_authorization(
                    Path(td)
                )
            )

            result = (
                g.validate_authorization(
                    path
                )
            )

            self.assertEqual(
                result[
                    "authorization_type"
                ],
                g.AUTHORIZATION_TYPE,
            )


    def test_tampered_critical_authorization_fields_fail(
        self,
    ):

        mutations = {
            "design_sha256":
                "0" * 64,

            "wave_a_request_manifest_sha256":
                "1" * 64,

            "design_parent_commit":
                "deadbeef",

            "normalizer_sha256":
                "2" * 64,

            "maximum_request_count":
                4491,

            "execution_output_root":
                "wrong/root",

            "wave_id":
                "WRONG_WAVE",

            "one_use":
                False,

            "authorized_by":
                "software",

            "authorization_statement":
                "NOT_AUTHORIZED",

            "authorized_execution_commit":
                "deadbeef",
        }

        for field, bad_value in (
            mutations.items()
        ):

            with self.subTest(
                field=field
            ):

                with tempfile.TemporaryDirectory() as td:

                    path, authorization = (
                        self.valid_authorization(
                            Path(td)
                        )
                    )

                    authorization[
                        field
                    ] = bad_value

                    self.write_authorization(
                        path,
                        authorization,
                    )

                    with self.assertRaises(
                        g.AuthorizationGuardError
                    ):
                        g.validate_authorization(
                            path
                        )


    def test_transport_hash_tamper_fails(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            path, authorization = (
                self.valid_authorization(
                    Path(td)
                )
            )

            authorization[
                "transport_source_hashes"
            ] = copy.deepcopy(
                authorization[
                    "transport_source_hashes"
                ]
            )

            authorization[
                "transport_source_hashes"
            ][0][
                "sha256"
            ] = "f" * 64

            self.write_authorization(
                path,
                authorization,
            )

            with self.assertRaises(
                g.AuthorizationGuardError
            ):
                g.validate_authorization(
                    path
                )


    def test_request_outside_manifest_fails(
        self,
    ):

        expected = self.manifest[0]

        proposed = dict(
            expected
        )

        proposed[
            "identifier"
        ] = (
            proposed[
                "identifier"
            ]
            + "-tampered"
        )

        with self.assertRaises(
            g.AuthorizationGuardError
        ):
            g.validate_exact_request(
                expected_row=expected,
                proposed_request=proposed,
            )


    def test_secret_field_rejected_from_terminal_receipt(
        self,
    ):

        expected = self.manifest[0]

        receipt = {
            "wave_id":
                g.EXPECTED_WAVE_ID,

            "request_sequence":
                1,

            "request_identity_sha256":
                expected[
                    "request_identity_sha256"
                ],

            "provider":
                expected[
                    "provider"
                ],

            "transport_route":
                expected[
                    "transport_route"
                ],

            "terminal_status":
                "success",

            "archived_terminal_sha256":
                "a" * 64,

            "api_key":
                "DO-NOT-PERSIST",
        }

        with self.assertRaises(
            g.AuthorizationGuardError
        ):
            g.validate_terminal_receipt(
                expected_row=expected,
                terminal_receipt=receipt,
            )


    def test_claim_resume_and_second_execution_rejected(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            path, authorization = (
                self.valid_authorization(
                    root
                )
            )

            # For state-machine testing only, temporarily
            # replace the fixed output root after the static
            # authorization has already been validated.
            original = (
                g.EXPECTED_OUTPUT_ROOT
            )

            try:

                g.EXPECTED_OUTPUT_ROOT = str(
                    root
                    / "live_wave_a"
                )

                authorization[
                    "execution_output_root"
                ] = g.EXPECTED_OUTPUT_ROOT

                self.write_authorization(
                    path,
                    authorization,
                )

                first = g.open_execution(
                    authorization_path=path,
                    execution_id="EXEC-001",
                )

                self.assertFalse(
                    first[
                        "resumed"
                    ]
                )

                resumed = g.open_execution(
                    authorization_path=path,
                    execution_id="EXEC-001",
                )

                self.assertTrue(
                    resumed[
                        "resumed"
                    ]
                )

                with self.assertRaises(
                    g.AuthorizationGuardError
                ):
                    g.open_execution(
                        authorization_path=path,
                        execution_id="EXEC-002",
                    )

            finally:

                g.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_checkpoint_first_request_and_resume(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            path, authorization = (
                self.valid_authorization(
                    root
                )
            )

            original = (
                g.EXPECTED_OUTPUT_ROOT
            )

            try:

                g.EXPECTED_OUTPUT_ROOT = str(
                    root
                    / "live_wave_a"
                )

                authorization[
                    "execution_output_root"
                ] = g.EXPECTED_OUTPUT_ROOT

                self.write_authorization(
                    path,
                    authorization,
                )

                context = g.open_execution(
                    authorization_path=path,
                    execution_id="EXEC-001",
                )

                expected = self.manifest[0]

                receipt = {
                    "wave_id":
                        g.EXPECTED_WAVE_ID,

                    "request_sequence":
                        1,

                    "request_identity_sha256":
                        expected[
                            "request_identity_sha256"
                        ],

                    "provider":
                        expected[
                            "provider"
                        ],

                    "transport_route":
                        expected[
                            "transport_route"
                        ],

                    "terminal_status":
                        "success",

                    "archived_terminal_sha256":
                        "a" * 64,
                }

                state = g.checkpoint_terminal(
                    context=context,
                    proposed_request=expected,
                    terminal_receipt=receipt,
                )

                self.assertEqual(
                    state[
                        "completed_request_count"
                    ],
                    1,
                )

                self.assertEqual(
                    state[
                        "next_request_sequence"
                    ],
                    2,
                )

                resumed = g.open_execution(
                    authorization_path=path,
                    execution_id="EXEC-001",
                )

                self.assertEqual(
                    resumed[
                        "state"
                    ][
                        "next_request_sequence"
                    ],
                    2,
                )

            finally:

                g.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_corrupted_state_checksum_fails(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            path, authorization = (
                self.valid_authorization(
                    root
                )
            )

            original = (
                g.EXPECTED_OUTPUT_ROOT
            )

            try:

                g.EXPECTED_OUTPUT_ROOT = str(
                    root
                    / "live_wave_a"
                )

                authorization[
                    "execution_output_root"
                ] = g.EXPECTED_OUTPUT_ROOT

                self.write_authorization(
                    path,
                    authorization,
                )

                context = g.open_execution(
                    authorization_path=path,
                    execution_id="EXEC-001",
                )

                state_path = (
                    g.execution_state_path(
                        context[
                            "execution_root"
                        ]
                    )
                )

                state_path.write_text(
                    "{}\n",
                    encoding="utf-8",
                )

                with self.assertRaises(
                    g.AuthorizationGuardError
                ):
                    g.open_execution(
                        authorization_path=path,
                        execution_id="EXEC-001",
                    )

            finally:

                g.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_completed_claim_replay_rejected(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            path, authorization = (
                self.valid_authorization(
                    root
                )
            )

            original = (
                g.EXPECTED_OUTPUT_ROOT
            )

            try:

                g.EXPECTED_OUTPUT_ROOT = str(
                    root
                    / "live_wave_a"
                )

                authorization[
                    "execution_output_root"
                ] = g.EXPECTED_OUTPUT_ROOT

                self.write_authorization(
                    path,
                    authorization,
                )

                context = g.open_execution(
                    authorization_path=path,
                    execution_id="EXEC-001",
                )

                claim_path = (
                    g.claim_path_for_authorization(
                        path
                    )
                )

                claim = (
                    g.read_json_with_checksum(
                        claim_path
                    )
                )

                claim[
                    "status"
                ] = "COMPLETED"

                claim[
                    "completed_request_count"
                ] = (
                    g.EXPECTED_MAXIMUM_REQUEST_COUNT
                )

                claim[
                    "final_checkpoint_chain_sha256"
                ] = "b" * 64

                g.write_json_with_checksum(
                    claim_path,
                    claim,
                )

                with self.assertRaises(
                    g.AuthorizationGuardError
                ):
                    g.open_execution(
                        authorization_path=path,
                        execution_id="EXEC-001",
                    )

            finally:

                g.EXPECTED_OUTPUT_ROOT = (
                    original
                )



    def test_runtime_transport_source_hash_tamper_fails(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            path, _ = (
                self.valid_authorization(
                    Path(td)
                )
            )

            source_path = Path(
                self.design[
                    "transport_contract"
                ][
                    "transport_sources"
                ][0][
                    "path"
                ]
            )

            original_sha256_file = (
                g.sha256_file
            )

            def fake_sha256_file(
                candidate,
            ):

                candidate = Path(
                    candidate
                )

                if candidate == source_path:

                    return "0" * 64

                return original_sha256_file(
                    candidate
                )

            with mock.patch.object(
                g,
                "sha256_file",
                side_effect=fake_sha256_file,
            ):

                with self.assertRaises(
                    g.AuthorizationGuardError
                ):
                    g.validate_authorization(
                        path
                    )


    def test_crash_after_checkpoint_recovers_same_execution(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            path, authorization = (
                self.valid_authorization(
                    root
                )
            )

            original = (
                g.EXPECTED_OUTPUT_ROOT
            )

            try:

                g.EXPECTED_OUTPUT_ROOT = str(
                    root
                    / "live_wave_a"
                )

                authorization[
                    "execution_output_root"
                ] = g.EXPECTED_OUTPUT_ROOT

                self.write_authorization(
                    path,
                    authorization,
                )

                context = g.open_execution(
                    authorization_path=path,
                    execution_id="EXEC-CRASH-001",
                )

                state_path = (
                    g.execution_state_path(
                        context[
                            "execution_root"
                        ]
                    )
                )

                state_checksum_path = (
                    g.checksum_path(
                        state_path
                    )
                )

                pre_checkpoint_state = (
                    state_path.read_bytes()
                )

                pre_checkpoint_checksum = (
                    state_checksum_path.read_bytes()
                )

                expected = self.manifest[0]

                receipt = {
                    "wave_id":
                        g.EXPECTED_WAVE_ID,

                    "request_sequence":
                        1,

                    "request_identity_sha256":
                        expected[
                            "request_identity_sha256"
                        ],

                    "provider":
                        expected[
                            "provider"
                        ],

                    "transport_route":
                        expected[
                            "transport_route"
                        ],

                    "terminal_status":
                        "success",

                    "archived_terminal_sha256":
                        "a" * 64,
                }

                g.checkpoint_terminal(
                    context=context,
                    proposed_request=expected,
                    terminal_receipt=receipt,
                )

                # Simulate process death after the immutable
                # request checkpoint reached disk but before
                # execution_state.json was advanced.
                state_path.write_bytes(
                    pre_checkpoint_state
                )

                state_checksum_path.write_bytes(
                    pre_checkpoint_checksum
                )

                resumed = g.open_execution(
                    authorization_path=path,
                    execution_id="EXEC-CRASH-001",
                )

                self.assertTrue(
                    resumed[
                        "resumed"
                    ]
                )

                self.assertEqual(
                    resumed[
                        "state"
                    ][
                        "completed_request_count"
                    ],
                    1,
                )

                self.assertEqual(
                    resumed[
                        "state"
                    ][
                        "next_request_sequence"
                    ],
                    2,
                )

            finally:

                g.EXPECTED_OUTPUT_ROOT = (
                    original
                )


    def test_completion_receipt_created_before_claim_completion(
        self,
    ):

        with tempfile.TemporaryDirectory() as td:

            root = Path(td)

            path, authorization = (
                self.valid_authorization(
                    root
                )
            )

            original_output_root = (
                g.EXPECTED_OUTPUT_ROOT
            )

            try:

                g.EXPECTED_OUTPUT_ROOT = str(
                    root
                    / "live_wave_a"
                )

                authorization[
                    "execution_output_root"
                ] = g.EXPECTED_OUTPUT_ROOT

                self.write_authorization(
                    path,
                    authorization,
                )

                context = g.open_execution(
                    authorization_path=path,
                    execution_id="EXEC-COMPLETE-001",
                )

                expected = self.manifest[0]

                receipt = {
                    "wave_id":
                        g.EXPECTED_WAVE_ID,

                    "request_sequence":
                        1,

                    "request_identity_sha256":
                        expected[
                            "request_identity_sha256"
                        ],

                    "provider":
                        expected[
                            "provider"
                        ],

                    "transport_route":
                        expected[
                            "transport_route"
                        ],

                    "terminal_status":
                        "success",

                    "archived_terminal_sha256":
                        "c" * 64,
                }

                # Reduce only the in-memory test ceiling to
                # exercise the actual completion branch with
                # one mocked terminal lookup.
                with (
                    mock.patch.object(
                        g,
                        "EXPECTED_MAXIMUM_REQUEST_COUNT",
                        1,
                    ),
                    mock.patch.object(
                        g,
                        "read_manifest",
                        return_value=[
                            expected
                        ],
                    ),
                ):

                    state = (
                        g.checkpoint_terminal(
                            context=context,
                            proposed_request=expected,
                            terminal_receipt=receipt,
                        )
                    )

                    self.assertEqual(
                        state[
                            "status"
                        ],
                        "COMPLETED",
                    )

                    completion_path = (
                        g.completion_receipt_path(
                            context[
                                "execution_root"
                            ]
                        )
                    )

                    self.assertTrue(
                        completion_path.exists()
                    )

                    completion = (
                        g.read_json_with_checksum(
                            completion_path
                        )
                    )

                    self.assertEqual(
                        completion[
                            "status"
                        ],
                        "COMPLETED",
                    )

                    self.assertEqual(
                        completion[
                            "completed_request_count"
                        ],
                        1,
                    )

                    claim = (
                        g.read_json_with_checksum(
                            g.claim_path_for_authorization(
                                path
                            )
                        )
                    )

                    self.assertEqual(
                        claim[
                            "status"
                        ],
                        "COMPLETED",
                    )

                    self.assertEqual(
                        claim[
                            "completion_receipt_sha256"
                        ],
                        g.sha256_file(
                            completion_path
                        ),
                    )

            finally:

                g.EXPECTED_OUTPUT_ROOT = (
                    original_output_root
                )


if __name__ == "__main__":
    unittest.main()
