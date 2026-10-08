from __future__ import annotations

import csv
import json
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

import pre_review_triage_future_review_queue_v1 as q


class FutureReviewQueueTests(
    unittest.TestCase
):

    def scored(
        self,
        index,
        entity,
        score,
    ):
        return q.ScoredRecord(
            retrieval_record_index=index,
            screening_entity_id=entity,
            selected_candidate_id=q.SELECTED_CANDIDATE,
            continuous_score=float(score),
            continuous_score_text=str(score),
        )

    def coverage(
        self,
        index,
        entity,
        status="scored",
        abstract_status="abstract_present",
    ):
        return q.CoverageRecord(
            retrieval_record_index=index,
            screening_entity_id=entity,
            abstract_status=abstract_status,
            coverage_status=status,
        )

    def test_rank_policy_and_tie_break(
        self,
    ):
        records = [
            self.scored(1, "b", 0.5),
            self.scored(2, "a", 0.5),
            self.scored(3, "c", 0.7),
        ]

        ranked = q.rank_scored(
            records
        )

        self.assertEqual(
            [
                x.screening_entity_id
                for x in ranked
            ],
            [
                "c",
                "a",
                "b",
            ],
        )

    def test_partition_exact(
        self,
    ):
        records = [
            self.scored(i, str(i), i)
            for i in range(5)
        ]

        priority, residual = (
            q.partition_ranked(
                records,
                2,
            )
        )

        self.assertEqual(
            len(priority),
            2,
        )

        self.assertEqual(
            len(residual),
            3,
        )

    def test_unscored_order(
        self,
    ):
        coverage = [
            self.coverage(
                9,
                "z",
                "no_normalized_text",
                "abstract_absent",
            ),
            self.coverage(
                2,
                "a",
                "no_normalized_text",
                "provider_not_found",
            ),
            self.coverage(
                1,
                "scored",
            ),
        ]

        ordered = q.order_unscored(
            coverage
        )

        self.assertEqual(
            [
                x.retrieval_record_index
                for x in ordered
            ],
            [
                2,
                9,
            ],
        )

    def test_ceil_rule_exact(
        self,
    ):
        self.assertEqual(
            q.ceil_fraction_times_n(
                35,
                76,
                11905,
            ),
            5483,
        )

    def test_authorization_payload_exact(
        self,
    ):
        value = (
            q.expected_authorization_payload()
        )

        self.assertEqual(
            value[
                "expected_priority_scored_rows"
            ],
            5483,
        )

        self.assertEqual(
            value[
                "expected_residual_scored_rows"
            ],
            6422,
        )

        self.assertFalse(
            value[
                "scientific_decision_authorized"
            ]
        )

    def test_authorization_round_trip(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:

            path = (
                Path(td)
                / "auth.json"
            )

            path.write_text(
                json.dumps(
                    q.expected_authorization_payload(),
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            q.validate_generation_authorization(
                path,
                q.GENERATION_CONFIRMATION,
            )

    def test_wrong_confirmation_fails(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:

            path = (
                Path(td)
                / "auth.json"
            )

            path.write_text(
                json.dumps(
                    q.expected_authorization_payload()
                ),
                encoding="utf-8",
            )

            with self.assertRaises(
                q.QueueError
            ):
                q.validate_generation_authorization(
                    path,
                    "WRONG",
                )

    def test_manifest_scientific_boundary(
        self,
    ):
        manifest = q.build_manifest(
            [],
            [],
            [],
        )

        boundary = manifest[
            "scientific_boundary"
        ]

        self.assertTrue(
            all(
                value is False
                for value in boundary.values()
            )
        )

        self.assertFalse(
            manifest[
                "cross_lane_priority_defined"
            ]
        )

    def test_write_outputs_exact_schema(
        self,
    ):
        priority = [
            self.scored(
                1,
                "p",
                0.9,
            )
        ]

        residual = [
            self.scored(
                2,
                "r",
                0.1,
            )
        ]

        manual = [
            self.coverage(
                3,
                "m",
                "no_normalized_text",
                "abstract_absent",
            )
        ]

        with tempfile.TemporaryDirectory() as td:

            root = (
                Path(td)
                / "out"
            )

            q.write_outputs(
                root,
                priority,
                residual,
                manual,
            )

            self.assertEqual(
                {
                    x.name
                    for x in root.iterdir()
                },
                {
                    q.PRIORITY_NAME,
                    q.RESIDUAL_NAME,
                    q.UNSCORED_NAME,
                    q.MANIFEST_NAME,
                },
            )

            with (
                root
                / q.PRIORITY_NAME
            ).open(
                "r",
                encoding="utf-8",
                newline="",
            ) as fh:
                reader = csv.DictReader(
                    fh,
                    delimiter="\t",
                )

                self.assertEqual(
                    reader.fieldnames,
                    [
                        "queue_position",
                        "retrieval_record_index",
                        "screening_entity_id",
                        "selected_candidate_id",
                        "continuous_score",
                    ],
                )

    def test_unauthorized_execution_creates_nothing(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:

            output = (
                Path(td)
                / "output"
            )

            missing_auth = (
                Path(td)
                / "missing.json"
            )

            with patch.object(
                q,
                "OUTPUT_ROOT",
                output,
            ):
                with self.assertRaises(
                    q.QueueError
                ):
                    q.execute_authorized(
                        missing_auth,
                        q.GENERATION_CONFIRMATION,
                    )

            self.assertFalse(
                output.exists()
            )


if __name__ == "__main__":
    unittest.main()
