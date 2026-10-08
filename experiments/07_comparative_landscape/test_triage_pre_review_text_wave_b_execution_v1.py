from __future__ import annotations

from collections import Counter
from pathlib import Path
import copy
import unittest

import triage_pre_review_text_wave_b_guard_v1 as guard
import triage_pre_review_text_wave_b_transport_evidence_adapter_v1 as adapter
import triage_pre_review_text_wave_b_runner_core_v1 as core
import triage_pre_review_text_wave_b_live_entrypoint_v1 as live


class WaveBExecutionTests(
    unittest.TestCase
):

    def test_frozen_design_validates(
        self,
    ):
        design = guard.load_frozen_design()

        self.assertEqual(
            design[
                "status"
            ],
            "FROZEN_PRE_IMPLEMENTATION",
        )

        self.assertEqual(
            design[
                "wave_id"
            ],
            "TRIAGE_TEXT_LIVE_WAVE_B",
        )


    def test_all_frozen_design_dependencies_validate(
        self,
    ):
        design = guard.load_frozen_design()

        guard.verify_transport_source_files(
            design
        )


    def test_manifest_is_exact_25_openalex_requests(
        self,
    ):
        rows = guard.read_manifest()

        self.assertEqual(
            len(rows),
            25,
        )

        self.assertEqual(
            {
                row[
                    "provider"
                ]
                for row in rows
            },
            {
                "openalex"
            },
        )

        self.assertEqual(
            Counter(
                row[
                    "frozen_route"
                ]
                for row in rows
            ),
            {
                "exact_work_id":
                    21,
                "exact_doi":
                    4,
            },
        )


    def test_request_identities_reproduce(
        self,
    ):
        for row in guard.read_manifest():

            self.assertEqual(
                guard.expected_request_identity(
                    row
                ),
                row[
                    "request_identity_sha256"
                ],
            )


    def test_guard_rejects_pubmed_route(
        self,
    ):
        row = copy.deepcopy(
            guard.read_manifest()[0]
        )

        row[
            "provider"
        ] = "pubmed"

        row[
            "frozen_route"
        ] = "exact_pmid_efetch"

        row[
            "transport_route"
        ] = "record_by_pmid"

        row[
            "identifier_namespace"
        ] = "pmid"

        row[
            "identifier"
        ] = "12345678"

        row[
            "request_identity_sha256"
        ] = guard.expected_request_identity(
            row
        )

        with self.assertRaises(
            guard.AuthorizationGuardError
        ):
            guard.validate_manifest_row(
                row
            )


    def test_adapter_uses_wave_b_namespace(
        self,
    ):
        row = guard.read_manifest()[0]

        mapped = adapter.manifest_to_transport_row(
            row
        )

        self.assertTrue(
            mapped[
                "logical_lookup_id"
            ].startswith(
                "triage_text_wave_b:"
            )
        )

        self.assertEqual(
            mapped[
                "provider"
            ],
            "openalex",
        )


    def test_adapter_rejects_pubmed(
        self,
    ):
        synthetic = {
            "request_sequence":
                "1",
            "request_identity_sha256":
                "a" * 64,
            "provider":
                "pubmed",
            "transport_route":
                "record_by_pmid",
            "identifier_namespace":
                "pmid",
            "identifier":
                "12345678",
        }

        with self.assertRaises(
            adapter.AdapterError
        ):
            adapter.manifest_to_transport_row(
                synthetic
            )


    def test_runner_preflight_allows_openalex_without_ncbi_environment(
        self,
    ):
        row = guard.read_manifest()[0]

        core.preflight_environment(
            manifest_row=row,
            environ={},
        )


    def test_runner_preflight_rejects_non_openalex(
        self,
    ):
        row = copy.deepcopy(
            guard.read_manifest()[0]
        )

        row[
            "provider"
        ] = "pubmed"

        with self.assertRaises(
            core.RunnerHalt
        ):
            core.preflight_environment(
                manifest_row=row,
                environ={},
            )


    def test_live_environment_requires_no_ncbi_credential(
        self,
    ):
        live.validate_live_environment(
            {}
        )


    def test_live_frozen_dependencies_validate(
        self,
    ):
        live.validate_frozen_dependencies()


    def test_live_confirmation_is_wave_b_specific(
        self,
    ):
        self.assertEqual(
            live.CONFIRMATION_LITERAL,
            "EXECUTE-AUTHORIZED-WAVE-B",
        )


    def test_authorization_path_is_wave_b_specific(
        self,
    ):
        self.assertTrue(
            str(
                live.CANONICAL_AUTHORIZATION_PATH
            ).endswith(
                (
                    "triage_pre_review_text_retrieval_v1/"
                    "live_wave_b/authorization.json"
                )
            )
        )


    def test_no_authorization_exists(
        self,
    ):
        self.assertFalse(
            live.CANONICAL_AUTHORIZATION_PATH.exists()
        )


    def test_runner_has_no_default_http_executor(
        self,
    ):
        source = Path(
            core.__file__
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "default_http_executor",
            source,
        )


    def test_live_entrypoint_is_only_b_execution_bridge(
        self,
    ):
        source = Path(
            live.__file__
        ).read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            source.count(
                "transport.default_http_executor"
            ),
            1,
        )


    def test_adapter_has_no_wave_a_lookup_namespace(
        self,
    ):
        source = Path(
            adapter.__file__
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            '"triage_text_wave_a:"',
            source,
        )


if __name__ == "__main__":
    unittest.main()
