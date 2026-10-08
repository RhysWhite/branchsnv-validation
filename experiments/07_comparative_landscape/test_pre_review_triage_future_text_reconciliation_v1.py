from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pre_review_triage_future_text_reconciliation_v1 as r


class FutureReconciliationContractTests(
    unittest.TestCase
):

    def test_frozen_contract_validates(
        self,
    ):

        contract = (
            r.assert_frozen_contract()
        )

        self.assertEqual(
            contract[
                "design"
            ][
                "status"
            ],
            "FROZEN_PRE_IMPLEMENTATION",
        )


    def test_output_schemas_exact(
        self,
    ):

        self.assertEqual(
            r.normalized_text_columns(),
            r.NORMALIZED_TEXT_COLUMNS,
        )

        self.assertEqual(
            r.resolution_columns(),
            r.RESOLUTION_COLUMNS,
        )

        forbidden = {
            "include",
            "exclude",
            "decision",
            "label",
            "score",
            "threshold",
        }

        self.assertTrue(
            forbidden.isdisjoint(
                r.NORMALIZED_TEXT_COLUMNS
            )
        )

        self.assertTrue(
            forbidden.isdisjoint(
                r.RESOLUTION_COLUMNS
            )
        )


    def test_canonical_write_unconditionally_blocked(
        self,
    ):

        for confirmation in (
            None,
            "",
            "WRITE-FROZEN-FUTURE-RECONCILIATION-V1",
        ):

            with self.assertRaises(
                r.ReconciliationError
            ):
                r.validate_output_destination(
                    r.RROOT,
                    canonical_confirmation=
                        confirmation,
                )


    def test_temporary_output_root_allowed(
        self,
    ):

        with tempfile.TemporaryDirectory() as d:

            got = (
                r.validate_output_destination(
                    Path(
                        d
                    )
                )
            )

            self.assertEqual(
                got,
                Path(
                    d
                ).resolve(),
            )


    def test_output_names_exact(
        self,
    ):

        self.assertEqual(
            r.OUTPUT_FILENAMES,
            (
                "reconciled_resolution.tsv",
                "reconciled_normalized_text.tsv",
                "reconciliation_summary.json",
                "reconciliation_outputs.sha256",
            ),
        )


    def test_provider_identity_canonicalization(
        self,
    ):

        self.assertEqual(
            r.canonical_provider_id(
                "pubmed",
                "PMID:123",
            ),
            "123",
        )

        self.assertEqual(
            r.canonical_provider_id(
                "openalex",
                "https://openalex.org/W123",
            ),
            "W123",
        )


    def test_future_structural_population_bound(
        self,
    ):

        design = (
            r.assert_frozen_contract()[
                "design"
            ]
        )

        population = (
            design[
                "known_structural_population"
            ]
        )

        self.assertEqual(
            population[
                "future_input_rows"
            ],
            12162,
        )

        self.assertEqual(
            population[
                "future_wave_a_request_rows"
            ],
            12147,
        )

        self.assertEqual(
            population[
                "future_wave_b_fallback_rows"
            ],
            40,
        )

        self.assertEqual(
            population[
                "future_wave_b_primary_provider_counts"
            ],
            {
                "pubmed":
                    40,
            },
        )


class FutureReconciliationStaticTests(
    unittest.TestCase
):

    def test_no_network_client_import(
        self,
    ):

        source = (
            Path(
                r.__file__
            ).read_text(
                encoding="utf-8"
            )
        )

        forbidden = (
            "import requests",
            "from requests",
            "import httpx",
            "from httpx",
            "urllib.request",
            "aiohttp",
        )

        for token in forbidden:

            self.assertNotIn(
                token,
                source,
            )


    def test_future_guard_imports_exact(
        self,
    ):

        source = (
            Path(
                r.__file__
            ).read_text(
                encoding="utf-8"
            )
        )

        self.assertIn(
            "pre_review_triage_future_text_wave_a_guard_v1",
            source,
        )

        self.assertIn(
            "pre_review_triage_future_text_wave_b_guard_v1",
            source,
        )

        self.assertIn(
            "pre_review_triage_future_text_wave_b_transport_evidence_adapter_v1",
            source,
        )


if __name__ == "__main__":
    unittest.main()
