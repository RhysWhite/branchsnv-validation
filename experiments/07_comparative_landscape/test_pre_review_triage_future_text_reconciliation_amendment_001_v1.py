from __future__ import annotations

import unittest

import pre_review_triage_future_text_reconciliation_v1 as r


EXPECTED_INDICES = {
    2421,
    2603,
    3092,
    3348,
    3492,
    3535,
    4738,
    4739,
    5283,
    11061,
}


class FutureReconciliationAmendment001Tests(
    unittest.TestCase
):

    @classmethod
    def setUpClass(cls):
        cls.result = (
            r.build_reconciliation()
        )

    def test_direct_openalex_not_found_population(
        self,
    ):
        rows = [
            row
            for row in self.result[
                "resolution_rows"
            ]
            if (
                row[
                    "abstract_status"
                ]
                == "provider_not_found"
            )
        ]

        self.assertEqual(
            {
                int(
                    row[
                        "retrieval_record_index"
                    ]
                )
                for row in rows
            },
            EXPECTED_INDICES,
        )

        self.assertEqual(
            len(rows),
            10,
        )

    def test_direct_openalex_not_found_semantics(
        self,
    ):
        rows = [
            row
            for row in self.result[
                "resolution_rows"
            ]
            if (
                row[
                    "abstract_status"
                ]
                == "provider_not_found"
            )
        ]

        for row in rows:

            self.assertEqual(
                row[
                    "resolution_lane"
                ],
                "wave_a_primary",
            )

            self.assertEqual(
                row[
                    "provider_used"
                ],
                "openalex",
            )

            self.assertEqual(
                row[
                    "provider_record_id"
                ],
                "",
            )

            self.assertEqual(
                row[
                    "provider_identity_status"
                ],
                "not_applicable",
            )

            self.assertEqual(
                row[
                    "parser_status"
                ],
                "not_applicable",
            )

            self.assertEqual(
                row[
                    "wave_b_request_sequence"
                ],
                "",
            )

            self.assertEqual(
                row[
                    "fallback_reason"
                ],
                "",
            )

            self.assertEqual(
                row[
                    "normalized_text_present"
                ],
                "0",
            )

    def test_not_found_rows_never_enter_text_output(
        self,
    ):
        text_indices = {
            int(
                row[
                    "retrieval_record_index"
                ]
            )
            for row in self.result[
                "normalized_text_rows"
            ]
        }

        self.assertTrue(
            EXPECTED_INDICES.isdisjoint(
                text_indices
            )
        )

    def test_amended_population_counts(
        self,
    ):
        self.assertEqual(
            self.result[
                "abstract_status_counts"
            ].get(
                "provider_not_found"
            ),
            10,
        )

        self.assertEqual(
            self.result[
                "terminal_source_counts"
            ].get(
                "wave_a_openalex_verified_not_found"
            ),
            10,
        )

        self.assertEqual(
            self.result[
                "parser_or_position_gap_count"
            ],
            1,
        )

        self.assertEqual(
            len(
                self.result[
                    "resolution_rows"
                ]
            ),
            12162,
        )


if __name__ == "__main__":
    unittest.main()
